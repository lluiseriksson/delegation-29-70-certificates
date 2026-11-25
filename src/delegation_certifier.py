"""Exact-Q four-mode certificate verifier for DC-DELEG-CERT-1.0.

Verifies downward-closed delegation certificates for Hamed Abdi, Kiarash Banihashem,
MohammadTaghi Hajiaghayi, and Danny Mittal, "Improved Downward-Closed Delegation
Bounds" (arXiv:2611.33095, Nov 2026).

Strictly zero floating-point operations (uses fractions.Fraction exclusively).
Author: Lluis Eriksson
License: MIT
"""

from __future__ import annotations

from fractions import Fraction
from math import gcd
import re
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

from src.delegation_exact import (
    LEMMA44_POLY_ASC,
    bernstein_coeffs_on_interval,
    evaluate_capped_menu_exact,
    exp_neg_taylor_bracket,
    exp_pos_taylor_sum,
    frac_to_canon_str,
    is_downward_closed,
)

SCHEMA_VERSION = "DC-DELEG-CERT-1.0"
MAX_BIT_LEN = 2048
MAX_JSON_DEPTH = 32
MAX_ID_LEN = 128

_CANON_INT_RE = re.compile(r"\A(?:0|-?[1-9][0-9]*)\Z")
_CANON_FRAC_RE = re.compile(r"\A(-?[1-9][0-9]*)/([1-9][0-9]*)\Z")

VALID_MODES = {
    "knapsack5_impossibility_cert",
    "lemma44_bernstein_3_10_cert",
    "capped_menu_score_cert",
    "appendix_a_taylor_beta_cert",
}


class CertError(ValueError):
    """Raised when a certificate violates schema, typing, or mathematical invariants."""


def _assert_strict_json_types(obj: Any, path: str = "root", depth: int = 0) -> None:
    if depth > MAX_JSON_DEPTH:
        raise CertError(f"{path}: JSON nesting depth exceeds {MAX_JSON_DEPTH}")
    if obj is None or type(obj) in (bool, int, str):
        return
    if type(obj) is list:
        for i, item in enumerate(obj):
            _assert_strict_json_types(item, f"{path}[{i}]", depth + 1)
        return
    if type(obj) is dict:
        for k, v in obj.items():
            if type(k) is not str:
                raise CertError(f"{path}: non-string dict key")
            _assert_strict_json_types(v, f"{path}.{k}", depth + 1)
        return
    raise CertError(f"{path}: disallowed type {type(obj).__name__} (non-exact types forbidden)")


def _require_exact_keys(d: Any, expected: set[str], label: str) -> Dict[str, Any]:
    if type(d) is not dict:
        raise CertError(f"{label}: expected dict")
    keys = set(d.keys())
    if keys != expected:
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise CertError(f"{label}: key mismatch (missing={missing}, extra={extra})")
    return d


def _parse_bool(v: Any, label: str) -> bool:
    if type(v) is not bool:
        raise CertError(f"{label}: expected bool, got {type(v).__name__}")
    return v


def _parse_int(v: Any, label: str, lo: Optional[int] = None, hi: Optional[int] = None) -> int:
    if type(v) is not int:
        raise CertError(f"{label}: expected int, got {type(v).__name__}")
    if v.bit_length() > MAX_BIT_LEN:
        raise CertError(f"{label}: integer exceeds {MAX_BIT_LEN} bits")
    if lo is not None and v < lo:
        raise CertError(f"{label}: {v} < {lo}")
    if hi is not None and v > hi:
        raise CertError(f"{label}: {v} > {hi}")
    return v


def _parse_id_str(v: Any, label: str) -> str:
    if type(v) is not str or not v or len(v) > MAX_ID_LEN:
        raise CertError(f"{label}: expected non-empty string of length <= {MAX_ID_LEN}")
    if any(ch in v for ch in ("\n", "\r", "\t")):
        raise CertError(f"{label}: control characters disallowed")
    return v


def _parse_canon_rational(v: Any, label: str) -> Fraction:
    if type(v) is not str:
        raise CertError(f"{label}: expected canonical rational string, got {type(v).__name__}")
    if len(v) > 2000:
        raise CertError(f"{label}: rational string too long")
    m_int = _CANON_INT_RE.match(v)
    if m_int:
        num = int(v)
        if num.bit_length() > MAX_BIT_LEN:
            raise CertError(f"{label}: numerator exceeds {MAX_BIT_LEN} bits")
        return Fraction(num, 1)
    m_frac = _CANON_FRAC_RE.match(v)
    if m_frac:
        num = int(m_frac.group(1))
        den = int(m_frac.group(2))
        if den < 2:
            raise CertError(f"{label}: non-canonical denominator {den} (integers must omit '/1')")
        if gcd(abs(num), den) != 1:
            raise CertError(f"{label}: non-reduced fraction {v}")
        if num.bit_length() > MAX_BIT_LEN or den.bit_length() > MAX_BIT_LEN:
            raise CertError(f"{label}: fraction exceeds {MAX_BIT_LEN} bits")
        return Fraction(num, den)
    raise CertError(f"{label}: invalid canonical rational string {v!r}")


def _parse_vector(v: Any, n: int, label: str) -> List[Fraction]:
    if type(v) is not list or len(v) != n:
        raise CertError(f"{label}: expected list of length {n}")
    return [_parse_canon_rational(x, f"{label}[{i}]") for i, x in enumerate(v)]


def _verify_mode1(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mode 1: Section 3 five-item knapsack impossibility below 1/2 (Prop 3.1, Thm 3.2, Prop 3.3)."""
    _require_exact_keys(
        payload,
        {
            "jackpot_prob",
            "jackpot_high_val",
            "eta",
            "claimed_offline_V",
            "claimed_rab_table",
            "claimed_det_payoff_ub",
            "claimed_det_ratio_ub",
            "claimed_rand_case1_ub",
            "claimed_rand_case2_ub",
            "claimed_rand_payoff_ub",
            "claimed_rand_ratio_ub",
        },
        "mode1.payload",
    )
    eps = _parse_canon_rational(payload["jackpot_prob"], "jackpot_prob")
    val_J = _parse_canon_rational(payload["jackpot_high_val"], "jackpot_high_val")
    eta = _parse_canon_rational(payload["eta"], "eta")
    if eps <= 0 or eps >= Fraction(1, 2):
        raise CertError("jackpot_prob must satisfy 0 < eps < 1/2 (Prop. 3.3)")
    if val_J * eps != Fraction(9):
        raise CertError("jackpot mean E[X_J] = val_J * eps must equal 9")
    if val_J <= Fraction(18):
        raise CertError("jackpot high value must exceed 18")
    if eta <= 0 or eta > Fraction(1):
        raise CertError("eta must satisfy 0 < eta <= 1")

    # Canonical 5-item knapsack: capacity 3; weights A=1, B=2, E=2, C=3, J=3
    weights = {"A": 1, "B": 2, "E": 2, "C": 3, "J": 3}
    agent_y = {
        "A": Fraction(3),
        "B": Fraction(2),
        "E": Fraction(4),
        "C": Fraction(8),
        "J": eta,
    }
    items = ["A", "B", "E", "C", "J"]
    feasible: List[FrozenSet[str]] = []
    for mask in range(1 << 5):
        sub = frozenset(items[i] for i in range(5) if (mask >> i) & 1)
        if sum(weights[it] for it in sub) <= 3:
            feasible.append(sub)
    # Verify exact 7 nonempty feasible sets and strict agent ranking C > AE > AB > E > A > B > J
    expected_nonempty = [
        frozenset({"C"}),
        frozenset({"A", "E"}),
        frozenset({"A", "B"}),
        frozenset({"E"}),
        frozenset({"A"}),
        frozenset({"B"}),
        frozenset({"J"}),
    ]
    if set(feasible) != set(expected_nonempty) | {frozenset()}:
        raise CertError("Internal knapsack feasibility mismatch")
    y_vals = [sum((agent_y[it] for it in s), Fraction(0)) for s in expected_nonempty]
    for i in range(len(y_vals) - 1):
        if not (y_vals[i] > y_vals[i + 1]):
            raise CertError("Strict agent preference ranking violated")

    # Exact offline optimum V over all 4 (X_A, X_B) states x 2 X_J states
    ab_states = [
        (Fraction(0), Fraction(0), Fraction(4, 9)),
        (Fraction(0), Fraction(9), Fraction(2, 9)),
        (Fraction(9), Fraction(0), Fraction(2, 9)),
        (Fraction(9), Fraction(9), Fraction(1, 9)),
    ]
    j_states = [(Fraction(0), Fraction(1) - eps), (val_J, eps)]
    V = Fraction(0)
    rab_list: List[Fraction] = []
    for xA, xB, pAB in ab_states:
        x_map_base = {"A": xA, "B": xB, "E": Fraction(3), "C": Fraction(10), "J": Fraction(0)}
        # Compute r_{ab} = max_{S != empty, J not in S} X(S)/Y(S)
        rab = max(
            sum((x_map_base[it] for it in s), Fraction(0)) / sum((agent_y[it] for it in s), Fraction(0))
            for s in expected_nonempty
            if "J" not in s
        )
        rab_list.append(rab)
        for xJ, pJ in j_states:
            xm = dict(x_map_base)
            xm["J"] = xJ
            opt_val = max(sum((xm[it] for it in s), Fraction(0)) for s in expected_nonempty)
            V += pAB * pJ * opt_val

    det_ub = Fraction(10)
    det_ratio = det_ub / V
    if det_ratio >= Fraction(1, 2):
        raise CertError(f"Deterministic ratio {det_ratio} is not strictly below 1/2")

    # Theorem 3.2 / Prop. 3.3 exact randomized Case 1 and Case 2 bounds
    # Case 1 (q <= 5/7): 10 + (1-eps)*eta * (4/9 * r00 + 2/9 * r09 + 2/9 * r90)
    case1_ub = Fraction(10) + (Fraction(1) - eps) * eta * (
        Fraction(4, 9) * rab_list[0] + Fraction(2, 9) * rab_list[1] + Fraction(2, 9) * rab_list[2]
    )
    # Case 2 (q > 5/7): 10 + (1-eps)*eta * (4/9 * r00 + 2/9 * r09)
    case2_ub = Fraction(10) + (Fraction(1) - eps) * eta * (
        Fraction(4, 9) * rab_list[0] + Fraction(2, 9) * rab_list[1]
    )
    rand_ub = max(case1_ub, case2_ub)
    rand_ratio = rand_ub / V
    if rand_ratio >= Fraction(1, 2):
        raise CertError(f"Randomized ratio {rand_ratio} is not strictly below 1/2")

    checks = [
        ("claimed_offline_V", V),
        ("claimed_det_payoff_ub", det_ub),
        ("claimed_det_ratio_ub", det_ratio),
        ("claimed_rand_case1_ub", case1_ub),
        ("claimed_rand_case2_ub", case2_ub),
        ("claimed_rand_payoff_ub", rand_ub),
        ("claimed_rand_ratio_ub", rand_ratio),
    ]
    for key, val in checks:
        if _parse_canon_rational(payload[key], key) != val:
            raise CertError(f"{key} mismatch: expected {frac_to_canon_str(val)}")
    if _parse_vector(payload["claimed_rab_table"], 4, "claimed_rab_table") != rab_list:
        raise CertError("claimed_rab_table mismatch")

    return {
        "V": frac_to_canon_str(V),
        "det_ratio_ub": frac_to_canon_str(det_ratio),
        "rand_ratio_ub": frac_to_canon_str(rand_ratio),
    }


def _verify_mode2(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mode 2: Section 4 Lemma 4.4 exact Bernstein positivity & 3/10 analytic warm-up."""
    _require_exact_keys(
        payload,
        {
            "interval_left",
            "interval_right",
            "mu_cantelli_test",
            "claimed_cantelli_lhs",
            "claimed_case1_gamma_lb",
            "claimed_exp_taylor7_gap",
            "claimed_bernstein_coeffs",
            "claimed_min_beta",
        },
        "mode2.payload",
    )
    left = _parse_canon_rational(payload["interval_left"], "interval_left")
    right = _parse_canon_rational(payload["interval_right"], "interval_right")
    if left < Fraction(2, 13) or right > Fraction(2, 3) or not (left < right):
        raise CertError("Interval [left, right] must be a non-empty subinterval of [2/13, 2/3]")

    mu_test = _parse_canon_rational(payload["mu_cantelli_test"], "mu_cantelli_test")
    if mu_test < Fraction(5):
        raise CertError("mu_cantelli_test must satisfy mu >= 5")
    cantelli_lhs = (mu_test * mu_test) / (Fraction(2) * mu_test + Fraction(12))
    if cantelli_lhs < Fraction(25, 22) or cantelli_lhs <= Fraction(1):
        raise CertError("Cantelli contradiction mu^2/(2*mu+12) >= 25/22 > 1 failed")

    case1_lb = (
        Fraction(52, 3)
        + Fraction(1)
        - Fraction(50, 13)
        - Fraction(80, 33) * Fraction(80, 33)
        - Fraction(40, 11)
        - Fraction(13, 5)
    )
    if case1_lb != Fraction(168034, 70785) or case1_lb <= 0:
        raise CertError("Case 1 Gamma lower bound check failed")

    exp_gap = exp_pos_taylor_sum(Fraction(15, 8), 7) - Fraction(13, 2)
    if exp_gap != Fraction(3772963, 234881024) or exp_gap <= 0:
        raise CertError("Degree-7 Taylor check for ln(13/2) < 15/8 failed")

    _, betas = bernstein_coeffs_on_interval(LEMMA44_POLY_ASC, left, right)
    if any(bk <= 0 for bk in betas):
        raise CertError("Non-positive Bernstein coefficient on [left, right]")
    min_beta = min(betas)

    if _parse_canon_rational(payload["claimed_cantelli_lhs"], "claimed_cantelli_lhs") != cantelli_lhs:
        raise CertError("claimed_cantelli_lhs mismatch")
    if _parse_canon_rational(payload["claimed_case1_gamma_lb"], "claimed_case1_gamma_lb") != case1_lb:
        raise CertError("claimed_case1_gamma_lb mismatch")
    if _parse_canon_rational(payload["claimed_exp_taylor7_gap"], "claimed_exp_taylor7_gap") != exp_gap:
        raise CertError("claimed_exp_taylor7_gap mismatch")
    if _parse_vector(payload["claimed_bernstein_coeffs"], 8, "claimed_bernstein_coeffs") != betas:
        raise CertError("claimed_bernstein_coeffs mismatch")
    if _parse_canon_rational(payload["claimed_min_beta"], "claimed_min_beta") != min_beta:
        raise CertError("claimed_min_beta mismatch")

    return {
        "interval": f"[{frac_to_canon_str(left)}, {frac_to_canon_str(right)}]",
        "min_beta": frac_to_canon_str(min_beta),
    }


def _verify_mode3(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mode 3: Exact Algorithm 2 capped-menu score & Lemma 2.2 normalization audit."""
    _require_exact_keys(
        payload,
        {
            "num_items",
            "feasible_sets",
            "item_laws",
            "cap_c",
            "singleton_cutoffs",
            "singleton_open_flags",
            "body_type",
            "level_t",
            "upper_u",
            "reserve_a",
            "is_safe_singleton_normalized",
            "claimed_V",
            "claimed_expected_score",
            "claimed_ratio",
            "claimed_beats_29_70",
            "claimed_min_seed_reserve_b",
        },
        "mode3.payload",
    )
    n = _parse_int(payload["num_items"], "num_items", 2, 5)
    raw_fam = payload["feasible_sets"]
    if type(raw_fam) is not list or not raw_fam or len(raw_fam) > (1 << n):
        raise CertError("feasible_sets: invalid list")
    family: set[FrozenSet[int]] = set()
    for idx, raw_s in enumerate(raw_fam):
        if type(raw_s) is not list:
            raise CertError(f"feasible_sets[{idx}]: expected list of item indices")
        elems = [_parse_int(e, f"feasible_sets[{idx}][{j}]", 0, n - 1) for j, e in enumerate(raw_s)]
        if len(set(elems)) != len(elems):
            raise CertError(f"feasible_sets[{idx}]: duplicate item index")
        fs = frozenset(elems)
        if fs in family:
            raise CertError(f"feasible_sets[{idx}]: duplicate feasible set")
        family.add(fs)
    if not is_downward_closed(family):
        raise CertError("feasible_sets: family is NOT downward closed")
    for i in range(n):
        if frozenset({i}) not in family:
            raise CertError(f"feasible_sets: singleton {{{i}}} must be feasible")

    raw_laws = payload["item_laws"]
    if type(raw_laws) is not list or len(raw_laws) != n:
        raise CertError(f"item_laws: expected {n} item distributions")
    item_laws: List[List[Tuple[Fraction, Fraction]]] = []
    total_outcomes = 1
    for i, raw_law in enumerate(raw_laws):
        if type(raw_law) is not list or not (1 <= len(raw_law) <= 4):
            raise CertError(f"item_laws[{i}]: expected 1..4 support points")
        pts: List[Tuple[Fraction, Fraction]] = []
        p_sum = Fraction(0)
        seen_vals: set[Fraction] = set()
        for j, pt in enumerate(raw_law):
            _require_exact_keys(pt, {"val", "prob"}, f"item_laws[{i}][{j}]")
            val = _parse_canon_rational(pt["val"], f"item_laws[{i}][{j}].val")
            prob = _parse_canon_rational(pt["prob"], f"item_laws[{i}][{j}].prob")
            if val < 0 or prob <= 0 or prob > 1:
                raise CertError(f"item_laws[{i}][{j}]: require val >= 0 and 0 < prob <= 1")
            if val in seen_vals:
                raise CertError(f"item_laws[{i}][{j}]: duplicate support value")
            seen_vals.add(val)
            p_sum += prob
            pts.append((val, prob))
        if p_sum != Fraction(1):
            raise CertError(f"item_laws[{i}]: probabilities sum to {p_sum} != 1")
        total_outcomes *= len(pts)
        item_laws.append(pts)
    if total_outcomes > 128:
        raise CertError(f"Joint support size {total_outcomes} exceeds cap 128")

    cap_c = _parse_canon_rational(payload["cap_c"], "cap_c")
    if cap_c <= 0:
        raise CertError("cap_c must be strictly positive")
    cutoffs = _parse_vector(payload["singleton_cutoffs"], n, "singleton_cutoffs")
    if any(d <= 0 for d in cutoffs):
        raise CertError("singleton_cutoffs must be strictly positive")
    raw_open = payload["singleton_open_flags"]
    if type(raw_open) is not list or len(raw_open) != n or not all(type(b) is bool for b in raw_open):
        raise CertError("singleton_open_flags must be a list of n strict booleans")

    body_type = _parse_id_str(payload["body_type"], "body_type")
    if body_type not in {"total_threshold", "seeds_upper", "seeds_reserve"}:
        raise CertError(f"invalid body_type {body_type!r}")
    level_t = _parse_canon_rational(payload["level_t"], "level_t")
    if level_t <= cap_c:
        raise CertError("Algorithm 2 requires level_t > cap_c")

    upper_u: Optional[Fraction] = None
    reserve_a: Optional[Fraction] = None
    if body_type == "total_threshold":
        if payload["upper_u"] is not None or payload["reserve_a"] is not None:
            raise CertError("upper_u and reserve_a must be null for total_threshold")
    elif body_type == "seeds_upper":
        upper_u = _parse_canon_rational(payload["upper_u"], "upper_u")
        if upper_u <= level_t:
            raise CertError("Algorithm 2 requires upper_u > level_t for seeds_upper")
        if payload["reserve_a"] is not None:
            raise CertError("reserve_a must be null for seeds_upper")
    else:
        reserve_a = _parse_canon_rational(payload["reserve_a"], "reserve_a")
        if reserve_a <= 0 or reserve_a > Fraction(1):
            raise CertError("Algorithm 2 requires 0 < reserve_a <= 1 for seeds_reserve")
        if payload["upper_u"] is not None:
            raise CertError("upper_u must be null for seeds_reserve")

    is_norm = _parse_bool(payload["is_safe_singleton_normalized"], "is_safe_singleton_normalized")
    if is_norm:
        # Lemma 2.2 check: item 0 is deterministic value 1 and {0} is maximal in F
        if item_laws[0] != [(Fraction(1), Fraction(1))]:
            raise CertError("Lemma 2.2: safe singleton item 0 must have X_0 = 1 surely")
        if any((0 in s and len(s) > 1) for s in family):
            raise CertError("Lemma 2.2: safe singleton {0} must be inclusion-maximal in F")

    res = evaluate_capped_menu_exact(
        num_items=n,
        family=family,
        item_laws=item_laws,
        cap_c=cap_c,
        cutoffs=cutoffs,
        open_flags=raw_open,
        body_type=body_type,
        level_t=level_t,
        upper_u=upper_u,
        reserve_a=reserve_a,
    )
    if res["V"] <= 0:
        raise CertError("V must be strictly positive")
    if is_norm and res["min_W"] < Fraction(1):
        raise CertError("Lemma 2.2: normalized instance must satisfy W >= 1 surely")

    if _parse_canon_rational(payload["claimed_V"], "claimed_V") != res["V"]:
        raise CertError(f"claimed_V mismatch: expected {frac_to_canon_str(res['V'])}")
    if _parse_canon_rational(payload["claimed_expected_score"], "claimed_expected_score") != res["expected_score"]:
        raise CertError(
            f"claimed_expected_score mismatch: expected {frac_to_canon_str(res['expected_score'])}"
        )
    if _parse_canon_rational(payload["claimed_ratio"], "claimed_ratio") != res["ratio"]:
        raise CertError(f"claimed_ratio mismatch: expected {frac_to_canon_str(res['ratio'])}")
    beats = res["ratio"] > Fraction(29, 70)
    if _parse_bool(payload["claimed_beats_29_70"], "claimed_beats_29_70") != beats:
        raise CertError("claimed_beats_29_70 mismatch")

    actual_min_b = res.get("min_seed_reserve_b")
    if actual_min_b is None:
        if payload["claimed_min_seed_reserve_b"] is not None:
            raise CertError("claimed_min_seed_reserve_b must be null when no seed occurs")
    else:
        if actual_min_b <= 0:
            raise CertError("Eq. (5.2) violated: seed reserve b_P <= 0")
        if _parse_canon_rational(payload["claimed_min_seed_reserve_b"], "claimed_min_seed_reserve_b") != actual_min_b:
            raise CertError(
                f"claimed_min_seed_reserve_b mismatch: expected {frac_to_canon_str(actual_min_b)}"
            )

    return {
        "body_type": body_type,
        "V": frac_to_canon_str(res["V"]),
        "expected_score": frac_to_canon_str(res["expected_score"]),
        "ratio": frac_to_canon_str(res["ratio"]),
        "beats_29_70": beats,
    }


def _verify_mode4(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Mode 4: Appendix A.5-A.6 exact alternating-Taylor bracket for beta < 9621/20000 = 0.48105."""
    _require_exact_keys(
        payload,
        {
            "a",
            "b",
            "d",
            "Delta",
            "eps_margin",
            "L0",
            "taylor_odd_deg",
            "target_cap",
            "claimed_z",
            "claimed_beta_hi_lt_target",
            "claimed_beta_hi_decimal_12",
            "claimed_beta_lo_decimal_12",
            "claimed_v_lo_plus_Delta_gt_1_plus_b",
            "claimed_bracket_lo_pos",
        },
        "mode4.payload",
    )
    a = _parse_canon_rational(payload["a"], "a")
    b = _parse_canon_rational(payload["b"], "b")
    d = _parse_canon_rational(payload["d"], "d")
    Delta = _parse_canon_rational(payload["Delta"], "Delta")
    eps_m = _parse_canon_rational(payload["eps_margin"], "eps_margin")
    L0 = _parse_canon_rational(payload["L0"], "L0")
    odd_deg = _parse_int(payload["taylor_odd_deg"], "taylor_odd_deg", 7, 25)
    if odd_deg % 2 != 1:
        raise CertError("taylor_odd_deg must be an odd integer")
    target_cap = _parse_canon_rational(payload["target_cap"], "target_cap")

    if a <= 0 or b <= 0 or d <= 0 or Delta <= 0 or eps_m <= 0 or L0 <= 0:
        raise CertError("Appendix A parameters must be strictly positive")
    z = a + b
    if z >= Fraction(1):
        raise CertError("Appendix A.6.2 requires z = a + b < 1 for alternating series bracket")
    if _parse_canon_rational(payload["claimed_z"], "claimed_z") != z:
        raise CertError("claimed_z mismatch")

    q_lo, q_hi = exp_neg_taylor_bracket(z, odd_deg)
    eb_lo, eb_hi = exp_neg_taylor_bracket(b, odd_deg)

    v_lo = z + q_lo
    v_hi = z + q_hi

    cond_v = (v_lo + Delta - Fraction(1)) > b
    if _parse_bool(payload["claimed_v_lo_plus_Delta_gt_1_plus_b"], "claimed_v_lo_plus_Delta_gt_1_plus_b") != cond_v:
        raise CertError("claimed_v_lo_plus_Delta_gt_1_plus_b mismatch")
    if not cond_v:
        raise CertError("Appendix A.5 condition v_lo + Delta - 1 > b failed")

    # Eq. (A.18) bracket: [v + Delta - b + b*(v + Delta - 1 - b/2) + a*L0 + a^2*d/2]
    # Note: strictly increasing in v!
    def _bracket(v_val: Fraction) -> Fraction:
        return (
            (v_val + Delta - b)
            + b * (v_val + Delta - Fraction(1) - b / Fraction(2))
            + a * L0
            + (a * a * d) / Fraction(2)
        )

    br_lo = _bracket(v_lo)
    br_hi = _bracket(v_hi)
    br_pos = br_lo > 0
    if _parse_bool(payload["claimed_bracket_lo_pos"], "claimed_bracket_lo_pos") != br_pos:
        raise CertError("claimed_bracket_lo_pos mismatch")
    if not br_pos:
        raise CertError("Appendix A.5 bracket lower bound is not positive")

    # W = z + 1 - exp(-b) + Q * bracket(v)
    W_lo = z + Fraction(1) - eb_hi + q_lo * br_lo
    W_hi = z + Fraction(1) - eb_lo + q_hi * br_hi
    if W_lo <= 0:
        raise CertError("W_lo must be positive")

    beta_hi = (v_hi + Delta + eps_m) / (Fraction(1) + W_lo)
    beta_lo = (v_lo + Delta + eps_m) / (Fraction(1) + W_hi)

    lt_target = beta_hi < target_cap
    if _parse_bool(payload["claimed_beta_hi_lt_target"], "claimed_beta_hi_lt_target") != lt_target:
        raise CertError("claimed_beta_hi_lt_target mismatch")
    if not lt_target:
        raise CertError(f"beta_hi does not strictly beat target_cap {target_cap}")

    # Exact rational 12-decimal ceiling/floor strings (zero floating-point!)
    scale = 10**12
    # Exact ceiling of beta_hi * 10^12:
    hi_scaled = (beta_hi.numerator * scale + beta_hi.denominator - 1) // beta_hi.denominator
    lo_scaled = (beta_lo.numerator * scale) // beta_lo.denominator
    hi_dec = f"{hi_scaled // scale}.{hi_scaled % scale:012d}"
    lo_dec = f"{lo_scaled // scale}.{lo_scaled % scale:012d}"

    if _parse_id_str(payload["claimed_beta_hi_decimal_12"], "claimed_beta_hi_decimal_12") != hi_dec:
        raise CertError(f"claimed_beta_hi_decimal_12 mismatch: expected {hi_dec}")
    if _parse_id_str(payload["claimed_beta_lo_decimal_12"], "claimed_beta_lo_decimal_12") != lo_dec:
        raise CertError(f"claimed_beta_lo_decimal_12 mismatch: expected {lo_dec}")

    return {
        "taylor_odd_deg": odd_deg,
        "beta_lo_12": lo_dec,
        "beta_hi_12": hi_dec,
        "strictly_below_target": lt_target,
    }


def verify_certificate(cert: Any) -> Tuple[bool, str, Dict[str, Any]]:
    """Verify a DC-DELEG-CERT-1.0 certificate payload over Q."""
    try:
        _assert_strict_json_types(cert)
        _require_exact_keys(
            cert,
            {"schema_version", "cert_id", "mode", "reference", "payload"},
            "certificate",
        )
        if cert["schema_version"] != SCHEMA_VERSION:
            raise CertError(
                f"schema_version mismatch: expected {SCHEMA_VERSION!r}, got {cert['schema_version']!r}"
            )
        cert_id = _parse_id_str(cert["cert_id"], "cert_id")
        mode = _parse_id_str(cert["mode"], "mode")
        if mode not in VALID_MODES:
            raise CertError(f"unknown mode {mode!r}")
        _parse_id_str(cert["reference"], "reference")
        payload = cert["payload"]
        if type(payload) is not dict:
            raise CertError("payload must be a dict")

        if mode == "knapsack5_impossibility_cert":
            summary = _verify_mode1(payload)
        elif mode == "lemma44_bernstein_3_10_cert":
            summary = _verify_mode2(payload)
        elif mode == "capped_menu_score_cert":
            summary = _verify_mode3(payload)
        else:
            summary = _verify_mode4(payload)

        summary["cert_id"] = cert_id
        summary["mode"] = mode
        return True, "OK", summary
    except CertError as exc:
        return False, str(exc), {}
