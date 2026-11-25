"""Exact rational polynomial, Bernstein, Taylor-bracket, and capped-menu helpers over Q.

Strictly zero floating-point operations (uses fractions.Fraction exclusively).
Author: Lluis Eriksson
License: MIT
"""

from __future__ import annotations

from fractions import Fraction
from itertools import product
from typing import Dict, FrozenSet, List, Sequence, Tuple


# Lemma 4.4 degree-7 polynomial coefficients in ascending powers of b:
# P(b) = -72 + 1345 b - 5459 b^2 + 7546 b^3 - 2948 b^4 + 1795 b^5 - 3593 b^6 + 1242 b^7
LEMMA44_POLY_ASC: List[Fraction] = [
    Fraction(-72),
    Fraction(1345),
    Fraction(-5459),
    Fraction(7546),
    Fraction(-2948),
    Fraction(1795),
    Fraction(-3593),
    Fraction(1242),
]


def frac_to_canon_str(x: Fraction) -> str:
    if not isinstance(x, Fraction):
        raise TypeError("Expected Fraction")
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def binom(n: int, k: int) -> int:
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    num = 1
    den = 1
    for i in range(1, k + 1):
        num *= n - k + i
        den *= i
    return num // den


def poly_add(p: Sequence[Fraction], q: Sequence[Fraction]) -> List[Fraction]:
    n = max(len(p), len(q))
    return [
        (p[i] if i < len(p) else Fraction(0)) + (q[i] if i < len(q) else Fraction(0))
        for i in range(n)
    ]


def poly_mul(p: Sequence[Fraction], q: Sequence[Fraction]) -> List[Fraction]:
    if not p or not q:
        return []
    out = [Fraction(0) for _ in range(len(p) + len(q) - 1)]
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            out[i + j] += a * b
    return out


def poly_scale(c: Fraction, p: Sequence[Fraction]) -> List[Fraction]:
    return [c * a for a in p]


def poly_pow(p: Sequence[Fraction], exp: int) -> List[Fraction]:
    res = [Fraction(1)]
    base = list(p)
    e = exp
    while e > 0:
        if e & 1:
            res = poly_mul(res, base)
        base = poly_mul(base, base)
        e >>= 1
    return res


def poly_eval(p: Sequence[Fraction], x: Fraction) -> Fraction:
    acc = Fraction(0)
    for coeff in reversed(p):
        acc = acc * x + coeff
    return acc


def bernstein_coeffs_on_interval(
    poly_asc: Sequence[Fraction], left: Fraction, right: Fraction
) -> Tuple[List[Fraction], List[Fraction]]:
    """Compute exact power-basis coefficients p_j of P(left + (right-left)v) and
    degree-n Bernstein coefficients beta_k = sum_{j=0}^k (C(k,j)/C(n,j)) * p_j.
    """
    n = len(poly_asc) - 1
    affine = [left, right - left]
    q_poly = [Fraction(0) for _ in range(n + 1)]
    for idx, coeff in enumerate(poly_asc):
        term = poly_scale(coeff, poly_pow(affine, idx))
        q_poly = poly_add(q_poly, term)
    betas: List[Fraction] = []
    for k in range(n + 1):
        acc = Fraction(0)
        for j in range(k + 1):
            acc += Fraction(binom(k, j), binom(n, j)) * q_poly[j]
        betas.append(acc)
    return q_poly, betas


def exp_neg_taylor_bracket(t: Fraction, odd_deg: int) -> Tuple[Fraction, Fraction]:
    """Exact rational alternating-series bracket [lo, hi] for exp(-t), 0 <= t <= 1.

    Uses odd_deg (odd >= 1) partial sum as lower bound and (odd_deg - 1) even partial sum
    as upper bound, valid by the alternating series theorem since t^k/k! decreases for k >= 1.
    """
    if t < 0 or t > 1:
        raise ValueError("exp_neg_taylor_bracket requires 0 <= t <= 1")
    if odd_deg < 1 or odd_deg % 2 != 1:
        raise ValueError("odd_deg must be an odd integer >= 1")
    s_even = Fraction(0)
    term = Fraction(1)
    for k in range(odd_deg):
        if k > 0:
            term = term * (-t) / Fraction(k)
        s_even += term
    last_term = term * (-t) / Fraction(odd_deg)
    s_odd = s_even + last_term
    return s_odd, s_even


def exp_pos_taylor_sum(t: Fraction, deg: int) -> Fraction:
    """Exact rational partial sum sum_{k=0}^deg t^k / k! for t >= 0."""
    if t < 0 or deg < 0:
        raise ValueError("Require t >= 0 and deg >= 0")
    total = Fraction(0)
    term = Fraction(1)
    for k in range(deg + 1):
        if k > 0:
            term = term * t / Fraction(k)
        total += term
    return total


def is_downward_closed(family: set[FrozenSet[int]]) -> bool:
    if frozenset() not in family:
        return False
    for s in family:
        for elem in s:
            if (s - {elem}) not in family:
                return False
    return True


def is_seed(s: FrozenSet[int], weights: Sequence[Fraction], level_t: Fraction) -> bool:
    """Section 5 Eq. (5.1): nonempty feasible set S is a seed at t iff w(S) >= t and
    w(S) - w_i < t for every i in S.
    """
    if not s:
        return False
    total = sum((weights[i] for i in s), Fraction(0))
    if total < level_t:
        return False
    for i in s:
        if total - weights[i] >= level_t:
            return False
    return True


def seed_reserve_b(s: FrozenSet[int], weights: Sequence[Fraction], level_t: Fraction) -> Fraction:
    """Section 5 Eq. (5.2): b_P = t + min_{i in P} w_i - w(P) > 0."""
    total = sum((weights[i] for i in s), Fraction(0))
    min_w = min(weights[i] for i in s)
    return level_t + min_w - total


def enumerate_sub_subsets(s: FrozenSet[int]) -> List[FrozenSet[int]]:
    elems = sorted(s)
    res: List[FrozenSet[int]] = []
    for mask in range(1, 1 << len(elems)):
        sub = frozenset(elems[bit] for bit in range(len(elems)) if (mask >> bit) & 1)
        res.append(sub)
    return res


def alg2_accepts(
    s: FrozenSet[int],
    x_vals: Sequence[Fraction],
    cap_c: Fraction,
    cutoffs: Sequence[Fraction],
    open_flags: Sequence[bool],
    body_type: str,
    level_t: Fraction,
    upper_u: Fraction | None,
    reserve_a: Fraction | None,
) -> bool:
    """Exact implementation of Algorithm 2 (Capped menu acceptance test, Sec. 5)."""
    if not s:
        return False
    if len(s) == 1:
        i = next(iter(s))
        if open_flags[i]:
            if x_vals[i] > cutoffs[i]:
                return True
        else:
            if x_vals[i] >= cutoffs[i]:
                return True
    w = [min(x_vals[i], cap_c) for i in range(len(x_vals))]
    w_s = sum((w[i] for i in s), Fraction(0))
    if body_type == "total_threshold":
        return w_s >= level_t
    if body_type == "seeds_upper":
        assert upper_u is not None
        return is_seed(s, w, level_t) or (w_s >= upper_u)
    if body_type == "seeds_reserve":
        assert reserve_a is not None
        for p_sub in enumerate_sub_subsets(s):
            if is_seed(p_sub, w, level_t):
                if p_sub == s:
                    return True
                b_p = seed_reserve_b(p_sub, w, level_t)
                ext_w = sum((w[i] for i in (s - p_sub)), Fraction(0))
                if ext_w >= reserve_a * b_p:
                    return True
        return False
    raise ValueError(f"Unknown body_type: {body_type}")


def evaluate_capped_menu_exact(
    num_items: int,
    family: set[FrozenSet[int]],
    item_laws: Sequence[Sequence[Tuple[Fraction, Fraction]]],
    cap_c: Fraction,
    cutoffs: Sequence[Fraction],
    open_flags: Sequence[bool],
    body_type: str,
    level_t: Fraction,
    upper_u: Fraction | None,
    reserve_a: Fraction | None,
) -> Dict[str, Fraction]:
    """Exact finite-support enumeration of V = E[W(X)], E[b_M(X)], ratio, and min seed reserve."""
    exp_V = Fraction(0)
    exp_score = Fraction(0)
    min_W = None
    min_b_p: Fraction | None = None

    nonempty_family = [s for s in family if len(s) > 0]
    for outcome in product(*item_laws):
        prob = Fraction(1)
        x_vals: List[Fraction] = []
        for val, pr in outcome:
            prob *= pr
            x_vals.append(val)
        if prob == 0:
            continue
        w_opt = max((sum((x_vals[i] for i in s), Fraction(0)) for s in family), default=Fraction(0))
        if min_W is None or w_opt < min_W:
            min_W = w_opt
        exp_V += prob * w_opt

        accepted = [
            s
            for s in nonempty_family
            if alg2_accepts(s, x_vals, cap_c, cutoffs, open_flags, body_type, level_t, upper_u, reserve_a)
        ]
        # Track min b_P across all seeds seen at this realization
        w_clipped = [min(x_vals[i], cap_c) for i in range(num_items)]
        for s in nonempty_family:
            if is_seed(s, w_clipped, level_t):
                bp = seed_reserve_b(s, w_clipped, level_t)
                if min_b_p is None or bp < min_b_p:
                    min_b_p = bp

        if not accepted:
            score = Fraction(0)
        else:
            acc_set = set(accepted)
            maximal = [
                s for s in acc_set if not any((s < other) for other in acc_set)
            ]
            score = min(sum((x_vals[i] for i in s), Fraction(0)) for s in maximal)
        exp_score += prob * score

    assert min_W is not None
    out: Dict[str, Fraction] = {
        "V": exp_V,
        "expected_score": exp_score,
        "ratio": exp_score / exp_V,
        "min_W": min_W,
    }
    if min_b_p is not None:
        out["min_seed_reserve_b"] = min_b_p
    return out
