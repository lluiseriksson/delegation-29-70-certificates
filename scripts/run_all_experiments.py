"""Generate all 16 canonical DC-DELEG-CERT-1.0 certificates and 4 exact-Q datasets.

Author: Lluis Eriksson
License: MIT
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path
import sys
import time
from typing import Any, Dict, FrozenSet, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.delegation_certifier import SCHEMA_VERSION, verify_certificate
from src.delegation_exact import (
    LEMMA44_POLY_ASC,
    bernstein_coeffs_on_interval,
    evaluate_capped_menu_exact,
    exp_neg_taylor_bracket,
    exp_pos_taylor_sum,
    frac_to_canon_str,
)


def _write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def _make_m1(cert_id: str, ref: str, eps: Fraction, eta: Fraction) -> Dict[str, Any]:
    val_J = Fraction(9) / eps
    # Exact V = eps * val_J + (1 - eps) * (1/9*18 + 2/9*12 + 2/3*10) = 9 + (1-eps)*34/3
    V = Fraction(9) + (Fraction(1) - eps) * Fraction(34, 3)
    rab = [Fraction(5, 4), Fraction(9, 2), Fraction(3), Fraction(9, 2)]
    det_ub = Fraction(10)
    case1 = Fraction(10) + (Fraction(1) - eps) * eta * Fraction(20, 9)
    case2 = Fraction(10) + (Fraction(1) - eps) * eta * Fraction(14, 9)
    rand_ub = max(case1, case2)
    return {
        "schema_version": SCHEMA_VERSION,
        "cert_id": cert_id,
        "mode": "knapsack5_impossibility_cert",
        "reference": ref,
        "payload": {
            "jackpot_prob": frac_to_canon_str(eps),
            "jackpot_high_val": frac_to_canon_str(val_J),
            "eta": frac_to_canon_str(eta),
            "claimed_offline_V": frac_to_canon_str(V),
            "claimed_rab_table": [frac_to_canon_str(x) for x in rab],
            "claimed_det_payoff_ub": frac_to_canon_str(det_ub),
            "claimed_det_ratio_ub": frac_to_canon_str(det_ub / V),
            "claimed_rand_case1_ub": frac_to_canon_str(case1),
            "claimed_rand_case2_ub": frac_to_canon_str(case2),
            "claimed_rand_payoff_ub": frac_to_canon_str(rand_ub),
            "claimed_rand_ratio_ub": frac_to_canon_str(rand_ub / V),
        },
    }


def _make_m2(cert_id: str, ref: str, left: Fraction, right: Fraction, mu_test: Fraction) -> Dict[str, Any]:
    cantelli = (mu_test * mu_test) / (Fraction(2) * mu_test + Fraction(12))
    case1_lb = Fraction(168034, 70785)
    exp_gap = exp_pos_taylor_sum(Fraction(15, 8), 7) - Fraction(13, 2)
    _, betas = bernstein_coeffs_on_interval(LEMMA44_POLY_ASC, left, right)
    return {
        "schema_version": SCHEMA_VERSION,
        "cert_id": cert_id,
        "mode": "lemma44_bernstein_3_10_cert",
        "reference": ref,
        "payload": {
            "interval_left": frac_to_canon_str(left),
            "interval_right": frac_to_canon_str(right),
            "mu_cantelli_test": frac_to_canon_str(mu_test),
            "claimed_cantelli_lhs": frac_to_canon_str(cantelli),
            "claimed_case1_gamma_lb": frac_to_canon_str(case1_lb),
            "claimed_exp_taylor7_gap": frac_to_canon_str(exp_gap),
            "claimed_bernstein_coeffs": [frac_to_canon_str(b) for b in betas],
            "claimed_min_beta": frac_to_canon_str(min(betas)),
        },
    }


def _make_m3(
    cert_id: str,
    ref: str,
    num_items: int,
    feasible_lists: List[List[int]],
    item_laws: List[List[Tuple[Fraction, Fraction]]],
    cap_c: Fraction,
    cutoffs: List[Fraction],
    open_flags: List[bool],
    body_type: str,
    level_t: Fraction,
    upper_u: Optional[Fraction],
    reserve_a: Optional[Fraction],
    is_norm: bool,
) -> Dict[str, Any]:
    family: set[FrozenSet[int]] = {frozenset(s) for s in feasible_lists}
    res = evaluate_capped_menu_exact(
        num_items=num_items,
        family=family,
        item_laws=item_laws,
        cap_c=cap_c,
        cutoffs=cutoffs,
        open_flags=open_flags,
        body_type=body_type,
        level_t=level_t,
        upper_u=upper_u,
        reserve_a=reserve_a,
    )
    min_b = res.get("min_seed_reserve_b")
    return {
        "schema_version": SCHEMA_VERSION,
        "cert_id": cert_id,
        "mode": "capped_menu_score_cert",
        "reference": ref,
        "payload": {
            "num_items": num_items,
            "feasible_sets": feasible_lists,
            "item_laws": [
                [{"val": frac_to_canon_str(v), "prob": frac_to_canon_str(pr)} for v, pr in law]
                for law in item_laws
            ],
            "cap_c": frac_to_canon_str(cap_c),
            "singleton_cutoffs": [frac_to_canon_str(d) for d in cutoffs],
            "singleton_open_flags": open_flags,
            "body_type": body_type,
            "level_t": frac_to_canon_str(level_t),
            "upper_u": frac_to_canon_str(upper_u) if upper_u is not None else None,
            "reserve_a": frac_to_canon_str(reserve_a) if reserve_a is not None else None,
            "is_safe_singleton_normalized": is_norm,
            "claimed_V": frac_to_canon_str(res["V"]),
            "claimed_expected_score": frac_to_canon_str(res["expected_score"]),
            "claimed_ratio": frac_to_canon_str(res["ratio"]),
            "claimed_beats_29_70": res["ratio"] > Fraction(29, 70),
            "claimed_min_seed_reserve_b": frac_to_canon_str(min_b) if min_b is not None else None,
        },
    }


def _make_m4(cert_id: str, ref: str, odd_deg: int) -> Dict[str, Any]:
    a = Fraction(67, 100)
    b = Fraction(9, 200)
    d = Fraction(9, 50)
    Delta = Fraction(1, 400)
    eps_m = Fraction(1, 1000000)
    L0 = Fraction(15733850124938532977, 32768000000000000000)
    target_cap = Fraction(9621, 20000)
    z = a + b

    q_lo, q_hi = exp_neg_taylor_bracket(z, odd_deg)
    eb_lo, eb_hi = exp_neg_taylor_bracket(b, odd_deg)
    v_lo, v_hi = z + q_lo, z + q_hi

    def _br(v: Fraction) -> Fraction:
        return (v + Delta - b) + b * (v + Delta - Fraction(1) - b / Fraction(2)) + a * L0 + (a * a * d) / Fraction(2)

    W_lo = z + Fraction(1) - eb_hi + q_lo * _br(v_lo)
    W_hi = z + Fraction(1) - eb_lo + q_hi * _br(v_hi)
    beta_hi = (v_hi + Delta + eps_m) / (Fraction(1) + W_lo)
    beta_lo = (v_lo + Delta + eps_m) / (Fraction(1) + W_hi)

    scale = 10**12
    hi_s = (beta_hi.numerator * scale + beta_hi.denominator - 1) // beta_hi.denominator
    lo_s = (beta_lo.numerator * scale) // beta_lo.denominator
    hi_dec = f"{hi_s // scale}.{hi_s % scale:012d}"
    lo_dec = f"{lo_s // scale}.{lo_s % scale:012d}"

    return {
        "schema_version": SCHEMA_VERSION,
        "cert_id": cert_id,
        "mode": "appendix_a_taylor_beta_cert",
        "reference": ref,
        "payload": {
            "a": frac_to_canon_str(a),
            "b": frac_to_canon_str(b),
            "d": frac_to_canon_str(d),
            "Delta": frac_to_canon_str(Delta),
            "eps_margin": frac_to_canon_str(eps_m),
            "L0": frac_to_canon_str(L0),
            "taylor_odd_deg": odd_deg,
            "target_cap": frac_to_canon_str(target_cap),
            "claimed_z": frac_to_canon_str(z),
            "claimed_beta_hi_lt_target": beta_hi < target_cap,
            "claimed_beta_hi_decimal_12": hi_dec,
            "claimed_beta_lo_decimal_12": lo_dec,
            "claimed_v_lo_plus_Delta_gt_1_plus_b": (v_lo + Delta - Fraction(1)) > b,
            "claimed_bracket_lo_pos": _br(v_lo) > 0,
        },
    }


def build_canonical_certificates() -> List[Dict[str, Any]]:
    certs: List[Dict[str, Any]] = []

    # Mode 1: Five-item knapsack impossibility (Sec. 3 Prop. 3.1, Thm. 3.2, Prop. 3.3)
    certs.append(_make_m1("m1_knapsack5_canonical_eta_1_100", "Abdi et al. (2026) Prop. 3.1 & Thm. 3.2 (eps=1/100, eta=1/100)", Fraction(1, 100), Fraction(1, 100)))
    certs.append(_make_m1("m1_knapsack5_tight_eta_1_1000", "Abdi et al. (2026) Thm. 3.2 tight eta=1/1000", Fraction(1, 100), Fraction(1, 1000)))
    certs.append(_make_m1("m1_knapsack5_prop33_eps_1_1000", "Abdi et al. (2026) Prop. 3.3 limiting ceiling (eps=1/1000)", Fraction(1, 1000), Fraction(1, 1000)))
    certs.append(_make_m1("m1_knapsack5_prop33_eps_1_10000", "Abdi et al. (2026) Prop. 3.3 limiting ceiling (eps=1/10000 -> 30/61)", Fraction(1, 10000), Fraction(1, 10000)))

    # Mode 2: Lemma 4.4 Bernstein positivity & 3/10 analytic warm-up
    certs.append(_make_m2("m2_lemma44_bernstein_left_2_13_to_2_5", "Abdi et al. (2026) Lemma 4.4 Bernstein cert on [2/13, 2/5]", Fraction(2, 13), Fraction(2, 5), Fraction(5)))
    certs.append(_make_m2("m2_lemma44_bernstein_right_2_5_to_2_3", "Abdi et al. (2026) Lemma 4.4 Bernstein cert on [2/5, 2/3]", Fraction(2, 5), Fraction(2, 3), Fraction(6)))
    certs.append(_make_m2("m2_lemma44_bernstein_sub_2_13_to_1_4", "Abdi et al. (2026) Lemma 4.4 refined subinterval [2/13, 1/4]", Fraction(2, 13), Fraction(1, 4), Fraction(11, 2)))
    certs.append(_make_m2("m2_lemma44_bernstein_sub_1_2_to_2_3", "Abdi et al. (2026) Lemma 4.4 refined subinterval [1/2, 2/3]", Fraction(1, 2), Fraction(2, 3), Fraction(7)))

    # Mode 3: Algorithm 2 Capped-Menu Score & Lemma 2.2 Normalization (4 certs)
    fam_knap3 = [[], [0], [1], [2], [0, 1], [0, 2]]
    laws_3 = [
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
        [(Fraction(0), Fraction(1, 2)), (Fraction(3), Fraction(1, 2))],
        [(Fraction(0), Fraction(2, 3)), (Fraction(5), Fraction(1, 3))],
    ]
    certs.append(
        _make_m3(
            "m3_alg2_total_threshold_knap3",
            "Abdi et al. (2026) Alg. 2 total-threshold capped menu",
            num_items=3,
            feasible_lists=fam_knap3,
            item_laws=laws_3,
            cap_c=Fraction(2),
            cutoffs=[Fraction(5), Fraction(5), Fraction(4)],
            open_flags=[False, False, False],
            body_type="total_threshold",
            level_t=Fraction(3),
            upper_u=None,
            reserve_a=None,
            is_norm=False,
        )
    )
    certs.append(
        _make_m3(
            "m3_alg2_seeds_upper_knap3",
            "Abdi et al. (2026) Alg. 2 seeds + upper-threshold menu",
            num_items=3,
            feasible_lists=fam_knap3,
            item_laws=laws_3,
            cap_c=Fraction(2),
            cutoffs=[Fraction(4), Fraction(3), Fraction(4)],
            open_flags=[True, False, False],
            body_type="seeds_upper",
            level_t=Fraction(3),
            upper_u=Fraction(4),
            reserve_a=None,
            is_norm=False,
        )
    )
    fam_knap4 = [[], [0], [1], [2], [3], [0, 1], [0, 2], [1, 2], [0, 1, 2], [0, 3]]
    laws_4 = [
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
        [(Fraction(0), Fraction(3, 4)), (Fraction(6), Fraction(1, 4))],
    ]
    certs.append(
        _make_m3(
            "m3_alg2_seeds_reserve_knap4",
            "Abdi et al. (2026) Alg. 2 seeds + reserve-extension menu (Eq. 5.2)",
            num_items=4,
            feasible_lists=fam_knap4,
            item_laws=laws_4,
            cap_c=Fraction(2),
            cutoffs=[Fraction(5), Fraction(5), Fraction(5), Fraction(5)],
            open_flags=[True, True, True, False],
            body_type="seeds_reserve",
            level_t=Fraction(3),
            upper_u=None,
            reserve_a=Fraction(1, 2),
            is_norm=False,
        )
    )
    # Safe-singleton normalized instance (Lemma 2.2: item 0 is X_0 = 1 surely, {0} maximal!)
    fam_norm = [[], [0], [1], [2], [1, 2]]
    laws_norm = [
        [(Fraction(1), Fraction(1))],
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
        [(Fraction(0), Fraction(1, 2)), (Fraction(2), Fraction(1, 2))],
    ]
    certs.append(
        _make_m3(
            "m3_lemma22_safe_singleton_norm",
            "Abdi et al. (2026) Lemma 2.2 safe-singleton normalized instance",
            num_items=3,
            feasible_lists=fam_norm,
            item_laws=laws_norm,
            cap_c=Fraction(3, 2),
            cutoffs=[Fraction(2), Fraction(3, 2), Fraction(3, 2)],
            open_flags=[False, False, False],
            body_type="total_threshold",
            level_t=Fraction(2),
            upper_u=None,
            reserve_a=None,
            is_norm=True,
        )
    )

    # Mode 4: Appendix A.6 exact alternating-Taylor bracket for beta < 9621/20000 = 0.48105
    certs.append(_make_m4("m4_appendix_a_taylor_deg11", "Abdi et al. (2026) App. A.6 Taylor bracket deg 10/11", 11))
    certs.append(_make_m4("m4_appendix_a_taylor_deg15", "Abdi et al. (2026) App. A.6 Taylor bracket deg 14/15", 15))
    certs.append(_make_m4("m4_appendix_a_taylor_deg19_paper", "Abdi et al. (2026) App. A.6.2 canonical Taylor bracket deg 18/19", 19))
    certs.append(_make_m4("m4_appendix_a_taylor_deg21", "Abdi et al. (2026) App. A.6 tightened Taylor bracket deg 20/21", 21))

    return certs


def main() -> None:
    cert_dir = ROOT / "certificates"
    data_dir = ROOT / "data"
    cert_dir.mkdir(parents=True, exist_ok=True)
    data_dir.mkdir(parents=True, exist_ok=True)

    certs = build_canonical_certificates()
    replay_rows: List[Dict[str, Any]] = []
    for cert in certs:
        _write_json(cert_dir / f"{cert['cert_id']}.json", cert)
        t0 = time.perf_counter_ns()
        ok, msg, summary = verify_certificate(cert)
        dt_ns = time.perf_counter_ns() - t0
        if not ok:
            raise RuntimeError(f"Canonical cert {cert['cert_id']} FAILED: {msg}")
        replay_rows.append(
            {
                "cert_id": cert["cert_id"],
                "mode": cert["mode"],
                "verified": ok,
                "verify_ns": dt_ns,
                "summary": summary,
            }
        )
    _write_json(data_dir / "certificate_replay_summary.json", {"certificates": replay_rows})

    # Dataset 1: Five-item knapsack deterministic & randomized ratio curve as eps -> 0 (eta = eps)
    exp1_rows = []
    for den in [10, 20, 50, 100, 250, 500, 1000, 5000, 10000]:
        eps = Fraction(1, den)
        V = Fraction(9) + (Fraction(1) - eps) * Fraction(34, 3)
        det_r = Fraction(10) / V
        rand_r = (Fraction(10) + (Fraction(1) - eps) * eps * Fraction(20, 9)) / V
        exp1_rows.append(
            {
                "eps": frac_to_canon_str(eps),
                "V": frac_to_canon_str(V),
                "det_ratio": frac_to_canon_str(det_r),
                "rand_ratio": frac_to_canon_str(rand_r),
            }
        )
    _write_json(data_dir / "exp1_knapsack5_impossibility_curve.json", {"rows": exp1_rows})

    # Dataset 2: Lemma 4.4 degree-7 Bernstein coefficients on [2/13, 2/5] and [2/5, 2/3]
    _, b_left = bernstein_coeffs_on_interval(LEMMA44_POLY_ASC, Fraction(2, 13), Fraction(2, 5))
    _, b_right = bernstein_coeffs_on_interval(LEMMA44_POLY_ASC, Fraction(2, 5), Fraction(2, 3))
    exp2_rows = [
        {
            "k": k,
            "beta_left": frac_to_canon_str(b_left[k]),
            "beta_right": frac_to_canon_str(b_right[k]),
        }
        for k in range(8)
    ]
    _write_json(data_dir / "exp2_lemma44_bernstein_coeffs.json", {"rows": exp2_rows})

    # Dataset 3: Appendix A.6 alternating Taylor bracket convergence across odd degrees 7..21
    exp3_rows = []
    for deg in [7, 9, 11, 13, 15, 17, 19, 21]:
        c = _make_m4(f"deg_{deg}", "sweep", deg)
        p = c["payload"]
        exp3_rows.append(
            {
                "taylor_odd_deg": deg,
                "beta_lo_12": p["claimed_beta_lo_decimal_12"],
                "beta_hi_12": p["claimed_beta_hi_decimal_12"],
                "beats_048105": p["claimed_beta_hi_lt_target"],
            }
        )
    _write_json(data_dir / "exp3_appendix_a_taylor_convergence.json", {"rows": exp3_rows})

    # Dataset 4: Mode 3 capped-menu exact score ratio summary
    exp4_rows = [r["summary"] for r in replay_rows if r["mode"] == "capped_menu_score_cert"]
    _write_json(data_dir / "exp4_capped_menu_scores.json", {"rows": exp4_rows})

    total_ms = sum(r["verify_ns"] for r in replay_rows) / 1_000_000
    min_ms = min(r["verify_ns"] for r in replay_rows) / 1_000_000
    max_ms = max(r["verify_ns"] for r in replay_rows) / 1_000_000
    print(f"Generated and verified {len(certs)}/16 canonical certificates.")
    print(f"Latency: min={min_ms:.3f} ms, max={max_ms:.3f} ms, total={total_ms:.2f} ms")


if __name__ == "__main__":
    main()
