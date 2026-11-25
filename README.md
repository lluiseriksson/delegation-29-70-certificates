# Certified Verification of Improved Downward-Closed Delegation Bounds

[![License: MIT](https://img.shields.io/badge/Code%20%26%20Lean-MIT-blue.svg)](LICENSE)
[![Paper License: CC-BY-4.0](https://img.shields.io/badge/Paper-CC--BY--4.0-green.svg)](paper/main.tex)

**Author:** Lluis Eriksson

Machine-checked **Lean 4.35.0** formalization and zero-floating-point exact-$\mathbb{Q}$ certificate audit (`DC-DELEG-CERT-1.0`) for **Hamed Abdi, Kiarash Banihashem, MohammadTaghi Hajiaghayi, & Danny Mittal** ([arXiv:2611.33095](https://arxiv.org/abs/2611.33095), Nov 2026), *"Improved Downward-Closed Delegation Bounds"*.

---

## Key Verified Artifacts

| Artifact | Verification Metric | Result |
| :--- | :--- | :--- |
| **Lean 4.35.0 Kernel** (`lean/DownwardDelegation.lean`) | 18 theorems, zero `sorry`, zero warnings, zero `Classical.choice` | **18 / 18 PASS** (`8` `none`, `10` `[propext, Quot.sound]`) |
| **Exact-$\mathbb{Q}$ Verifier** (`src/delegation_certifier.py`) | Zero `float()`, `math`, or `numpy`; 4-mode `DC-DELEG-CERT-1.0` | **16 / 16 PASS** (`0.185–2.611 ms`, total `9.21 ms`) |
| **Adversarial Red-Team Suite** (`tests/test_suite.py`) | 60 live forged payloads (12 global + 12/mode) | **60 / 60 REJECTED** |
| **SHA-256 Integrity Manifest** (`SHA256_MANIFEST.json`) | Full deterministic replay check (`scripts/verify_all.py`) | **40 / 40 MATCH** |
| **Manuscript** (`paper/main.pdf`) | 3 pages, 3 publication figures (`300 DPI`) | **0 warnings, 0 overfulls** |

---

## Four Certificate Modes (`DC-DELEG-CERT-1.0`)

1. **`knapsack5_impossibility_cert` (Mode 1 — Section 3 Prop. 3.1, Thm. 3.2, Prop. 3.3):** Enumerates all $2^5$ subsets of the five-item capacity-3 knapsack, verifies downward closure, strict agent preference ranking, exact offline optimum $V$, $r_{ab}$ table, deterministic ceiling $500/1011 < 1/2$, and randomized ceilings $5011/10110 < 1/2$ approaching $30/61$.
2. **`lemma44_bernstein_3_10_cert` (Mode 2 — Section 4 Lemma 4.4 & Theorem 4.1):** Independently expands $P(\ell + (r-\ell)v)$ in $\mathbb{Q}[v]$, verifies all 8 positive degree-7 Bernstein coefficients on $[2/13, 2/5]$ (exact min `447966/78125`) and $[2/5, 2/3]$ (exact min `6518/118125`), plus exact Cantelli, Case 1 (`168034/70785`), and degree-7 Taylor (`ln(13/2) < 15/8`) checks.
3. **`capped_menu_score_cert` (Mode 3 — Section 2 & Section 5 Algorithm 2):** Verifies downward closure, executes exact Algorithm 2 acceptance across all three body types (`total_threshold`, `seeds_upper`, `seeds_reserve`) over all joint realizations, verifies Lemma 2.2 safe-singleton normalization, seed reserve positivity $b_P > 0$, and exact score ratio $\mathbb{E}[b_M(X)]/V$.
4. **`appendix_a_taylor_beta_cert` (Mode 4 — Appendix A.5–A.6):** Computes exact rational alternating-Taylor brackets for $e^{-(a+b)}$ and $e^{-b}$, verifies Eq. (A.18) positivity conditions, and certifies exact 12-decimal brackets `[0.481043999745, 0.481043999746] < 9621/20000 = 0.48105`.

---

## Quick Reproduction

```bash
cd lean && lake build && lake env lean AuditAxioms.lean && cd ..
python scripts/run_all_experiments.py
python scripts/make_figures.py
python scripts/verify_all.py
```

---

## Licenses & Transparency Disclosure

- **Code, Lean proofs, certificates, and scripts:** [MIT License](LICENSE).
- **Manuscript (`paper/main.tex`, `paper/main.pdf`) and figures:** CC-BY-4.0.
- **AI Assistance Disclosure:** Prepared by sole author Lluis Eriksson with AI coding, formalization, and drafting assistance from Google Antigravity; all Lean proofs, exact-$\mathbb{Q}$ certificates, and adversarial tests were independently compiled and machine-verified locally.
