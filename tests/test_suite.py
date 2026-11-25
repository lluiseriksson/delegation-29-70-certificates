"""Live 60-attack adversarial red-team test suite for DC-DELEG-CERT-1.0.

Tests 12 global schema/typing/rational/depth/newline/-0 attacks + 12 domain attacks per mode.
Author: Lluis Eriksson
License: MIT
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from typing import Any, Callable, List, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.delegation_certifier import verify_certificate


def _load(name: str) -> dict[str, Any]:
    return json.loads((ROOT / "certificates" / f"{name}.json").read_text(encoding="utf-8"))


def _mutate(cert: dict[str, Any], fn: Callable[[dict[str, Any]], None]) -> dict[str, Any]:
    c = copy.deepcopy(cert)
    fn(c)
    return c


def build_attacks() -> List[Tuple[str, str, Any]]:
    m1 = _load("m1_knapsack5_canonical_eta_1_100")
    m2 = _load("m2_lemma44_bernstein_left_2_13_to_2_5")
    m3_res = _load("m3_alg2_seeds_reserve_knap4")
    m3_norm = _load("m3_lemma22_safe_singleton_norm")
    m4 = _load("m4_appendix_a_taylor_deg19_paper")

    attacks: List[Tuple[str, str, Any]] = []

    # --- 12 Global Schema / Type / Rational / Depth Attacks ---
    attacks.append(("global", "g01_wrong_schema_version", _mutate(m1, lambda c: c.__setitem__("schema_version", "DC-DELEG-CERT-2.0"))))
    attacks.append(("global", "g02_unknown_mode", _mutate(m1, lambda c: c.__setitem__("mode", "unknown_mode"))))
    attacks.append(("global", "g03_extra_top_key", _mutate(m1, lambda c: c.__setitem__("extra", "bad"))))
    attacks.append(("global", "g04_missing_payload_key", _mutate(m1, lambda c: c["payload"].pop("eta"))))
    attacks.append(("global", "g05_raw_float_injected", _mutate(m1, lambda c: c["payload"].__setitem__("eta", 0.01))))
    attacks.append(("global", "g06_unreduced_fraction", _mutate(m1, lambda c: c["payload"].__setitem__("eta", "2/200"))))
    attacks.append(("global", "g07_denom_one_fraction", _mutate(m1, lambda c: c["payload"].__setitem__("jackpot_high_val", "900/1"))))
    attacks.append(("global", "g08_trailing_newline_rational", _mutate(m1, lambda c: c["payload"].__setitem__("eta", "1/100\n"))))
    attacks.append(("global", "g09_negative_zero_rational", _mutate(m3_res, lambda c: c["payload"]["item_laws"][0][0].__setitem__("val", "-0"))))
    attacks.append(("global", "g10_bool_as_int_num_items", _mutate(m3_res, lambda c: c["payload"].__setitem__("num_items", True))))
    attacks.append(("global", "g11_int_as_bool_open_flag", _mutate(m3_res, lambda c: c["payload"]["singleton_open_flags"].__setitem__(0, 1))))

    def _deep_nest(c: dict[str, Any]) -> None:
        node: Any = "leaf"
        for _ in range(40):
            node = [node]
        c["payload"]["eta"] = node

    attacks.append(("global", "g12_excess_json_depth", _mutate(m1, _deep_nest)))

    # --- 12 Mode 1 Domain Attacks ---
    attacks.append(("mode1", "m1_01_eps_ge_half", _mutate(m1, lambda c: c["payload"].__setitem__("jackpot_prob", "1/2"))))
    attacks.append(("mode1", "m1_02_eps_nonpositive", _mutate(m1, lambda c: c["payload"].__setitem__("jackpot_prob", "0"))))
    attacks.append(("mode1", "m1_03_jackpot_mean_not_9", _mutate(m1, lambda c: c["payload"].__setitem__("jackpot_high_val", "800"))))
    attacks.append(("mode1", "m1_04_eta_gt_one", _mutate(m1, lambda c: c["payload"].__setitem__("eta", "2"))))
    attacks.append(("mode1", "m1_05_eta_nonpositive", _mutate(m1, lambda c: c["payload"].__setitem__("eta", "0"))))
    attacks.append(("mode1", "m1_06_wrong_offline_V", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_offline_V", "20"))))
    attacks.append(("mode1", "m1_07_wrong_rab_table", _mutate(m1, lambda c: c["payload"]["claimed_rab_table"].__setitem__(0, "1"))))
    attacks.append(("mode1", "m1_08_wrong_det_payoff_ub", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_det_payoff_ub", "11"))))
    attacks.append(("mode1", "m1_09_wrong_det_ratio_ub", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_det_ratio_ub", "1/2"))))
    attacks.append(("mode1", "m1_10_wrong_case1_ub", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_rand_case1_ub", "10"))))
    attacks.append(("mode1", "m1_11_wrong_case2_ub", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_rand_case2_ub", "10"))))
    attacks.append(("mode1", "m1_12_wrong_rand_ratio_ub", _mutate(m1, lambda c: c["payload"].__setitem__("claimed_rand_ratio_ub", "1/2"))))

    # --- 12 Mode 2 Domain Attacks ---
    attacks.append(("mode2", "m2_01_left_below_2_13", _mutate(m2, lambda c: c["payload"].__setitem__("interval_left", "1/10"))))
    attacks.append(("mode2", "m2_02_right_above_2_3", _mutate(m2, lambda c: c["payload"].__setitem__("interval_right", "3/4"))))
    attacks.append(("mode2", "m2_03_empty_interval", _mutate(m2, lambda c: c["payload"].__setitem__("interval_left", "2/5"))))
    attacks.append(("mode2", "m2_04_mu_cantelli_below_5", _mutate(m2, lambda c: c["payload"].__setitem__("mu_cantelli_test", "4"))))
    attacks.append(("mode2", "m2_05_wrong_cantelli_lhs", _mutate(m2, lambda c: c["payload"].__setitem__("claimed_cantelli_lhs", "1"))))
    attacks.append(("mode2", "m2_06_wrong_case1_gamma_lb", _mutate(m2, lambda c: c["payload"].__setitem__("claimed_case1_gamma_lb", "2"))))
    attacks.append(("mode2", "m2_07_wrong_exp_taylor7_gap", _mutate(m2, lambda c: c["payload"].__setitem__("claimed_exp_taylor7_gap", "1/100"))))
    attacks.append(("mode2", "m2_08_wrong_bernstein_coeff", _mutate(m2, lambda c: c["payload"]["claimed_bernstein_coeffs"].__setitem__(0, "1"))))
    attacks.append(("mode2", "m2_09_wrong_bernstein_len", _mutate(m2, lambda c: c["payload"]["claimed_bernstein_coeffs"].pop())))
    attacks.append(("mode2", "m2_10_wrong_min_beta", _mutate(m2, lambda c: c["payload"].__setitem__("claimed_min_beta", "1"))))
    attacks.append(("mode2", "m2_11_full_interval_neg_bernstein", _mutate(m2, lambda c: c["payload"].__setitem__("interval_right", "2/3"))))
    attacks.append(("mode2", "m2_12_inverted_interval", _mutate(m2, lambda c: c["payload"].__setitem__("interval_left", "1/2") or c["payload"].__setitem__("interval_right", "2/5"))))

    # --- 12 Mode 3 Domain Attacks ---
    attacks.append(("mode3", "m3_01_not_downward_closed", _mutate(m3_res, lambda c: c["payload"]["feasible_sets"].remove([0, 1]))))
    attacks.append(("mode3", "m3_02_missing_singleton", _mutate(m3_res, lambda c: c["payload"].__setitem__("feasible_sets", [[], [0], [1], [2]]))))
    attacks.append(("mode3", "m3_03_law_probs_not_sum_one", _mutate(m3_res, lambda c: c["payload"]["item_laws"][0][0].__setitem__("prob", "1/3"))))
    attacks.append(("mode3", "m3_04_negative_item_val", _mutate(m3_res, lambda c: c["payload"]["item_laws"][0][0].__setitem__("val", "-1"))))
    attacks.append(("mode3", "m3_05_level_t_le_cap_c", _mutate(m3_res, lambda c: c["payload"].__setitem__("level_t", "2"))))
    attacks.append(("mode3", "m3_06_reserve_a_gt_one", _mutate(m3_res, lambda c: c["payload"].__setitem__("reserve_a", "3/2"))))
    attacks.append(("mode3", "m3_07_non_null_upper_u_in_reserve", _mutate(m3_res, lambda c: c["payload"].__setitem__("upper_u", "4"))))
    attacks.append(("mode3", "m3_08_broken_lemma22_safe_singleton_val", _mutate(m3_norm, lambda c: c["payload"]["item_laws"][0][0].__setitem__("val", "2"))))
    attacks.append(("mode3", "m3_09_broken_lemma22_not_maximal", _mutate(m3_norm, lambda c: c["payload"]["feasible_sets"].append([0, 1]))))
    attacks.append(("mode3", "m3_10_wrong_claimed_V", _mutate(m3_res, lambda c: c["payload"].__setitem__("claimed_V", "1"))))
    attacks.append(("mode3", "m3_11_wrong_claimed_ratio", _mutate(m3_res, lambda c: c["payload"].__setitem__("claimed_ratio", "1/2"))))
    attacks.append(("mode3", "m3_12_wrong_min_seed_reserve", _mutate(m3_res, lambda c: c["payload"].__setitem__("claimed_min_seed_reserve_b", "2"))))

    # --- 12 Mode 4 Domain Attacks ---
    attacks.append(("mode4", "m4_01_even_taylor_deg", _mutate(m4, lambda c: c["payload"].__setitem__("taylor_odd_deg", 18))))
    attacks.append(("mode4", "m4_02_deg_too_small", _mutate(m4, lambda c: c["payload"].__setitem__("taylor_odd_deg", 5))))
    attacks.append(("mode4", "m4_03_z_ge_one", _mutate(m4, lambda c: c["payload"].__setitem__("a", "1"))))
    attacks.append(("mode4", "m4_04_wrong_claimed_z", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_z", "7/10"))))
    attacks.append(("mode4", "m4_05_nonpositive_L0", _mutate(m4, lambda c: c["payload"].__setitem__("L0", "0"))))
    attacks.append(("mode4", "m4_06_target_cap_too_tight", _mutate(m4, lambda c: c["payload"].__setitem__("target_cap", "48/100"))))
    attacks.append(("mode4", "m4_07_wrong_beta_hi_dec12", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_beta_hi_decimal_12", "0.481040000000"))))
    attacks.append(("mode4", "m4_08_wrong_beta_lo_dec12", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_beta_lo_decimal_12", "0.481040000000"))))
    attacks.append(("mode4", "m4_09_false_lt_target_flag", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_beta_hi_lt_target", False))))
    attacks.append(("mode4", "m4_10_false_v_cond_flag", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_v_lo_plus_Delta_gt_1_plus_b", False))))
    attacks.append(("mode4", "m4_11_false_bracket_pos_flag", _mutate(m4, lambda c: c["payload"].__setitem__("claimed_bracket_lo_pos", False))))
    attacks.append(("mode4", "m4_12_negative_Delta", _mutate(m4, lambda c: c["payload"].__setitem__("Delta", "-1/400"))))

    assert len(attacks) == 60, f"Expected 60 attacks, got {len(attacks)}"
    return attacks


def run_red_team_suite() -> Tuple[int, int, List[str]]:
    attacks = build_attacks()
    rejected = 0
    failures: List[str] = []
    for cat, name, payload in attacks:
        ok, _, _ = verify_certificate(payload)
        if not ok:
            rejected += 1
        else:
            failures.append(f"[{cat}] {name} was UNEXPECTEDLY ACCEPTED!")
    return rejected, len(attacks), failures


def main() -> None:
    rejected, total, failures = run_red_team_suite()
    if failures:
        for f in failures:
            print("FAIL:", f)
        sys.exit(1)
    print(f"Adversarial red-team audit: {rejected}/{total} forged payloads REJECTED (100%).")


if __name__ == "__main__":
    main()
