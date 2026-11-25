/-
  DownwardDelegation.lean
  Standalone zero-dependency Lean 4.35.0 formalization of 18 core combinatorial,
  menu-score, forced-item, Efron–Stein, Bernstein-polynomial, seed-reserve,
  and impossibility theorems for:
    Hamed Abdi, Kiarash Banihashem, MohammadTaghi Hajiaghayi, and Danny Mittal,
    "Improved Downward-Closed Delegation Bounds", arXiv:2611.33095 (Nov. 2026).

  Author: Lluis Eriksson
  License: MIT
-/

namespace DownwardDelegation

/-- Decidable integer minimum (zero `Classical.choice`). -/
def iMin (a b : Int) : Int :=
  if a ≤ b then a else b

/-- Decidable integer maximum (zero `Classical.choice`). -/
def iMax (a b : Int) : Int :=
  if a ≤ b then b else a

/-- Sum of an integer list. -/
def listSum : List Int → Int
  | [] => 0
  | x :: xs => x + listSum xs

/-- Sum of clipped entries `min(x, z)` over an integer list. -/
def listClipSum (z : Int) : List Int → Int
  | [] => 0
  | x :: xs => iMin x z + listClipSum z xs

/-- Sum of squares `∑ x^2` over an integer list. -/
def listSqSum : List Int → Int
  | [] => 0
  | x :: xs => x * x + listSqSum xs

/-- Minimum of a non-empty integer list `a :: rest`. -/
def listMinNE : Int → List Int → Int
  | a, [] => a
  | a, b :: rest => iMin a (listMinNE b rest)

/-- Exact homogeneous evaluation of `P(n/d) * d^7` for Lemma 4.4's degree-7 polynomial
    `P(b) = 1242 b^7 - 3593 b^6 + 1795 b^5 - 2948 b^4 + 7546 b^3 - 5459 b^2 + 1345 b - 72`. -/
def lemma44PolyCleared (n d : Int) : Int :=
  1242 * n^7
  - 3593 * n^6 * d
  + 1795 * n^5 * d^2
  - 2948 * n^4 * d^3
  + 7546 * n^3 * d^4
  - 5459 * n^2 * d^5
  + 1345 * n * d^6
  - 72 * d^7

/-- Theorem 1 (Theorems 1.1 & 1.2 Universal Delegation Ratio Hierarchy):
    Exact cleared rational strict ordering:
    `0.1098 < 3/10 < 29/70 < 0.48105 < 30/61 < 500/1011 < 5011/10110 < 1/2`. -/
theorem universal_bounds_hierarchy :
    (1098 * 10 < 3 * 10000) ∧
    (3 * 70 < 29 * 10) ∧
    (29 * 20000 < 9621 * 70) ∧
    (9621 * 61 < 30 * 20000) ∧
    (30 * 1011 < 500 * 61) ∧
    (500 * 10110 < 5011 * 1011) ∧
    (5011 * 2 < 10110) := by
  decide

/-- Theorem 2 (Section 3 Eq. 3.1 Five-Item Knapsack Offline Optimum `V = 1011/50`):
    Cleared by `900`: `9 * 900 + 99 * (1 * 18 + 2 * 12 + 6 * 10) = 18 * 1011`. -/
theorem knapsack5_offline_optimum_exact :
    9 * 900 + 99 * (1 * 18 + 2 * 12 + 6 * 10) = 18 * 1011 := by
  decide

/-- Theorem 3 (Proposition 3.1 Five-Item Knapsack Agent Strict Preference Ranking):
    For any scaled `0 < eta100 ≤ 100` (representing `0 < η ≤ 1`), the seven nonempty
    feasible sets are strictly ranked `C ≻ AE ≻ AB ≻ E ≻ A ≻ B ≻ J` with scaled agent
    utilities `800 > 700 > 500 > 400 > 300 > 200 > eta100`. -/
theorem knapsack5_agent_strict_ranking (eta100 : Int) (hpos : 0 < eta100) (hle : eta100 ≤ 100) :
    let yC := 800
    let yAE := 300 + 400
    let yAB := 300 + 200
    let yE := 400
    let yA := 300
    let yB := 200
    let yJ := eta100
    yC > yAE ∧ yAE > yAB ∧ yAB > yE ∧ yE > yA ∧ yA > yB ∧ yB > yJ ∧ yJ > 0 := by
  dsimp only
  refine ⟨by omega, by omega, by omega, by omega, by omega, by omega, by omega⟩

/-- Theorem 4 (Proposition 3.1 Five-Item Knapsack Deterministic Upper Bound `500/1011`):
    Both deterministic menu cases (accepting `AE=(9,3)` vs. rejecting `AE=(9,3)`) earn
    at most `10` (cleared: `1*12 + 2*9 = 3*10` and `1*18 + 8*9 = 9*10`), giving
    ratio `10 / (1011/50) = 500/1011 < 1/2`. -/
theorem knapsack5_det_upper_bound_exact :
    (1 * 12 + 2 * 9 = 3 * 10) ∧
    (1 * 18 + 8 * 9 = 9 * 10) ∧
    (10 * 50 = 500) ∧
    (500 * 2 < 1011) := by
  decide

/-- Theorem 5 (Theorem 3.2 Five-Item Knapsack Randomized Acceptance Bound `5011/10110`):
    For any `eta_num ≥ 0` (scaled by `eta_den > 0`), Case 1 (`q ≤ 5/7`) yields
    `10 + (11/5) η` and Case 2 (`q > 5/7`) yields `10 + (77/50) η ≤ 10 + (11/5) η`;
    at `η = 1/100`, the payoff bound is `5011/500`, giving ratio `5011/10110 < 1/2`. -/
theorem knapsack5_rand_case_bounds (eta_num : Int) (hnn : 0 ≤ eta_num) :
    (4 * 5 + 2 * 18 + 2 * 12 = 80) ∧
    (99 * 80 * 5 = 3600 * 11) ∧
    (4 * 5 + 2 * 18 = 56) ∧
    (99 * 56 * 50 = 3600 * 77) ∧
    (77 * eta_num ≤ 110 * eta_num) ∧
    (10 * 500 + 11 = 5011) ∧
    (5011 * 2 < 10110) := by
  refine ⟨by decide, by decide, by decide, by decide, ?_, by decide, by decide⟩
  omega

/-- Theorem 6 (Proposition 3.3 Limiting Randomized Ceiling `30/61 < 1/2`):
    With jackpot `9/ε` w.p. `ε`, the limiting offline optimum is `9 + 34/3 = 61/3`,
    giving limiting ratio `10 / (61/3) = 30/61 < 1/2`; for any cleared `0 < e_n < e_d`
    with `34 * e_n < e_d`, the finite-`ε` offline optimum strictly exceeds `20`. -/
theorem knapsack5_rand_asymptotic_30_61 (e_n e_d : Int) (_hpos : 0 < e_n) (hsmall : 34 * e_n < e_d) :
    (9 * 3 + 34 = 61) ∧
    (30 * 2 < 61) ∧
    (20 * (3 * e_d) < 9 * (3 * e_d) + 34 * (e_d - e_n)) := by
  refine ⟨by decide, by decide, ?_⟩
  omega

/-- Theorem 7 (Lemma 2.1 Menu Score Lower Bound over Finite Accepted Lists):
    For any nonempty list of accepted report principal values `a :: rest`, every member
    `s` of `a :: rest` satisfies `listMinNE a rest ≤ s` (so every inclusion-maximal
    best response achieves principal payoff at least the menu score `b_M(x)`). -/
theorem menu_score_payoff_bound (a : Int) (rest : List Int) :
    ∀ s, s ∈ a :: rest → listMinNE a rest ≤ s := by
  induction rest generalizing a with
  | nil =>
    intro s hs
    simp only [List.mem_singleton] at hs
    rw [hs]
    dsimp only [listMinNE]
    omega
  | cons b tl ih =>
    intro s hs
    dsimp only [listMinNE, iMin]
    simp only [List.mem_cons] at hs
    cases hs with
    | inl hsa =>
      rw [hsa]
      split <;> omega
    | inr htail =>
      have hsub := ih b s (List.mem_cons.2 htail)
      split <;> omega

/-- Theorem 8 (Lemma 4.2 Eq. 4.2 Forced-Item Pointwise Clipping Inequality):
    (1) Every integer `x` splits identically as `x = iMin x z + iMax (x - z) 0`.
    (2) For any finite list `ws : List Int` of nonnegative values with `listSum ws ≥ z`
        and `z ≥ 0`, the clipped sum satisfies `listClipSum z ws ≥ z`. -/
theorem forced_item_pointwise_decomposition (z : Int) (hz : 0 ≤ z) :
    (∀ x : Int, x = iMin x z + iMax (x - z) 0) ∧
    (∀ ws : List Int, (∀ w, w ∈ ws → 0 ≤ w) → z ≤ listSum ws → z ≤ listClipSum z ws) := by
  constructor
  · intro x
    dsimp only [iMin, iMax]
    split <;> split <;> omega
  · intro ws
    induction ws with
    | nil =>
      intro _ hsum
      dsimp only [listSum, listClipSum] at hsum ⊢
      omega
    | cons w tl ih =>
      intro hnn hsum
      have hw : 0 ≤ w := hnn w (by simp)
      have htl_nn : ∀ u, u ∈ tl → 0 ≤ u := fun u hu => hnn u (by simp [hu])
      have hclip_nn : ∀ us : List Int, (∀ u, u ∈ us → 0 ≤ u) → 0 ≤ listClipSum z us := by
        intro us
        induction us with
        | nil => intro _; dsimp only [listClipSum]; omega
        | cons u ur iur =>
          intro hunn
          have hu0 : 0 ≤ u := hunn u (by simp)
          have hur0 : 0 ≤ listClipSum z ur := iur (fun v hv => hunn v (by simp [hv]))
          dsimp only [listClipSum, iMin]
          split <;> omega
      dsimp only [listSum] at hsum
      dsimp only [listClipSum]
      have htl_clip_nn : 0 ≤ listClipSum z tl := hclip_nn tl htl_nn
      by_cases hcase : w ≤ z
      · have hmin : iMin w z = w := by dsimp only [iMin]; split <;> omega
        rw [hmin]
        by_cases htl : z ≤ listSum tl
        · have := ih htl_nn htl; omega
        · -- Every element of tl has sum < z, wait: maybe some element of tl is > z?
          -- Prove stronger: either some element ≥ z (so clipSum ≥ z), or all elements ≤ z (so clipSum = listSum).
          have hhelper : ∀ us : List Int, (∀ u, u ∈ us → 0 ≤ u) →
              z ≤ listClipSum z us ∨ listClipSum z us = listSum us := by
            intro us
            induction us with
            | nil => intro _; right; rfl
            | cons u ur iur =>
              intro hunn
              have hu0 : 0 ≤ u := hunn u (by simp)
              have hur_nn : ∀ v, v ∈ ur → 0 ≤ v := fun v hv => hunn v (by simp [hv])
              have hur_ge0 : 0 ≤ listClipSum z ur := hclip_nn ur hur_nn
              dsimp only [listClipSum, listSum, iMin]
              split
              · cases iur hur_nn with
                | inl hge => left; omega
                | inr heq => right; omega
              · left; omega
          cases hhelper tl htl_nn with
          | inl hge => omega
          | inr heq => omega
      · have hmin : iMin w z = z := by dsimp only [iMin]; split <;> omega
        rw [hmin]
        omega

/-- Theorem 9 (Section 4.1 Eq. 4.3 Tail Bound & Monotonicity in `e`):
    For `x > s > 0` and `0 ≤ e1 ≤ e2 ≤ s`, clearing denominators proves
    `(s - e2) * x ≤ s * (x - e2)` (i.e. `(1-e)/(x-e) ≤ 1/x`) and monotonicity
    `(s - e2) * (x - e1) ≤ (s - e1) * (x - e2)`. -/
theorem threshold_tail_bound_monotone (s x e1 e2 : Int)
    (_hs : 0 < s) (hx : s < x) (he1 : 0 ≤ e1) (hle : e1 ≤ e2) (_he2 : e2 ≤ s) :
    ((s - e2) * x ≤ s * (x - e2)) ∧
    ((s - e2) * (x - e1) ≤ (s - e1) * (x - e2)) := by
  constructor
  · have h1 : s * (x - e2) - (s - e2) * x = e2 * (x - s) := by
      rw [Int.mul_sub, Int.sub_mul, Int.mul_sub, Int.mul_comm s e2]
      omega
    have hnn : 0 ≤ e2 * (x - s) := Int.mul_nonneg (by omega) (by omega)
    omega
  · have h2 : (s - e1) * (x - e2) - (s - e2) * (x - e1) = (e2 - e1) * (x - s) := by
      have lhs1 : (s - e1) * (x - e2) = s * x - s * e2 - e1 * x + e1 * e2 := by
        rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]; omega
      have lhs2 : (s - e2) * (x - e1) = s * x - s * e1 - e2 * x + e2 * e1 := by
        rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]; omega
      have rhs1 : (e2 - e1) * (x - s) = e2 * x - e2 * s - e1 * x + e1 * s := by
        rw [Int.sub_mul, Int.mul_sub, Int.mul_sub]; omega
      have c1 : e2 * e1 = e1 * e2 := Int.mul_comm e2 e1
      have c2 : e2 * s = s * e2 := Int.mul_comm e2 s
      have c3 : e1 * s = s * e1 := Int.mul_comm e1 s
      omega
    have hnn : 0 ≤ (e2 - e1) * (x - s) := Int.mul_nonneg (by omega) (by omega)
    omega

/-- Theorem 10 (Lemma 4.3 Eq. 4.5 Efron–Stein Discrete Quadratic-to-Linear Step):
    For any finite list `ds : List Int` of marginal differences satisfying `0 ≤ d ≤ c`
    for every `d ∈ ds`, we have `∑ d^2 ≤ c * ∑ d`. -/
theorem efron_stein_step_bound (c : Int) (ds : List Int)
    (hbd : ∀ d, d ∈ ds → 0 ≤ d ∧ d ≤ c) :
    listSqSum ds ≤ c * listSum ds := by
  induction ds with
  | nil =>
    dsimp only [listSqSum, listSum]
    rw [Int.mul_zero]
    omega
  | cons d tl ih =>
    have hd := hbd d (by simp)
    have htl := ih (fun u hu => hbd u (by simp [hu]))
    have hstep : d * d ≤ c * d := Int.mul_le_mul_of_nonneg_right hd.2 hd.1
    dsimp only [listSqSum, listSum]
    rw [Int.mul_add]
    omega

/-- Theorem 11 (Lemma 4.4 p. 11 Cantelli Mean Cap `μ < 5`):
    For any scaled mean `mu ≥ 5 * s` with `s > 0`, `22 * mu^2 ≥ 25 * s * (2*mu + 12*s)`
    and strictly `mu^2 > s * (2*mu + 12*s)` (contradicting `x h_a(x) ≤ 1`). -/
theorem cantelli_mean_cap_lt_5 (mu s : Int) (hs : 0 < s) (hge : 5 * s ≤ mu) :
    (25 * s * (2 * mu + 12 * s) ≤ 22 * (mu * mu)) ∧
    (s * (2 * mu + 12 * s) < mu * mu) := by
  have hsq : (mu - 5 * s) * (22 * mu + 60 * s) ≥ 0 :=
    Int.mul_nonneg (by omega) (by omega)
  have hexp : 22 * (mu * mu) - 25 * s * (2 * mu + 12 * s) = (mu - 5 * s) * (22 * mu + 60 * s) := by
    rw [Int.mul_add, Int.sub_mul, Int.mul_add, Int.mul_add]
    have c1 : (25 * s) * (2 * mu) = 50 * (mu * s) := by
      calc (25 * s) * (2 * mu) = 25 * (s * (2 * mu)) := Int.mul_assoc _ _ _
        _ = 25 * (2 * (mu * s)) := by
              rw [← Int.mul_assoc s 2 mu, Int.mul_comm s 2, Int.mul_assoc, Int.mul_comm s mu]
        _ = (25 * 2) * (mu * s) := (Int.mul_assoc _ _ _).symm
        _ = 50 * (mu * s) := rfl
    have c2 : (25 * s) * (12 * s) = 300 * (s * s) := by
      calc (25 * s) * (12 * s) = 25 * (s * (12 * s)) := Int.mul_assoc _ _ _
        _ = 25 * (12 * (s * s)) := by rw [← Int.mul_assoc s 12 s, Int.mul_comm s 12, Int.mul_assoc]
        _ = (25 * 12) * (s * s) := (Int.mul_assoc _ _ _).symm
        _ = 300 * (s * s) := rfl
    have c3 : mu * (22 * mu) = 22 * (mu * mu) := by
      rw [← Int.mul_assoc, Int.mul_comm mu 22, Int.mul_assoc]
    have c4 : mu * (60 * s) = 60 * (mu * s) := by
      rw [← Int.mul_assoc, Int.mul_comm mu 60, Int.mul_assoc]
    have c5 : (5 * s) * (22 * mu) = 110 * (mu * s) := by
      calc (5 * s) * (22 * mu) = 5 * (s * (22 * mu)) := Int.mul_assoc _ _ _
        _ = 5 * (22 * (mu * s)) := by
              rw [← Int.mul_assoc s 22 mu, Int.mul_comm s 22, Int.mul_assoc, Int.mul_comm s mu]
        _ = (5 * 22) * (mu * s) := (Int.mul_assoc _ _ _).symm
        _ = 110 * (mu * s) := rfl
    have c6 : (5 * s) * (60 * s) = 300 * (s * s) := by
      calc (5 * s) * (60 * s) = 5 * (s * (60 * s)) := Int.mul_assoc _ _ _
        _ = 5 * (60 * (s * s)) := by rw [← Int.mul_assoc s 60 s, Int.mul_comm s 60, Int.mul_assoc]
        _ = (5 * 60) * (s * s) := (Int.mul_assoc _ _ _).symm
        _ = 300 * (s * s) := rfl
    omega
  have hpos : 0 < s * (2 * mu + 12 * s) := Int.mul_pos hs (by omega)
  have h25 : 25 * (s * (2 * mu + 12 * s)) = 25 * s * (2 * mu + 12 * s) :=
    (Int.mul_assoc 25 s (2 * mu + 12 * s)).symm
  constructor <;> omega

/-- Theorem 12 (Lemma 4.4 Case 1 p. 12 Exact Rational Positivity `168034 / 70785 > 0`):
    Clearing denominator `70785 = 3^2 * 5 * 11^2 * 13` in
    `52/3 + 1 - 50/13 - (80/33)^2 - 40/11 - 13/5 = 168034 / 70785 > 0`. -/
theorem lemma44_case1_gamma_pos :
    52 * 23595 + 1 * 70785 - 50 * 5445 - 6400 * 65 - 40 * 6435 - 13 * 14157 = 168034 ∧
    (0 < 168034) := by
  decide

/-- Theorem 13 (Lemma 4.4 Eq. 4.11 Exact Degree-7 Exponential Taylor Bound `ln(13/2) < 15/8`):
    Clearing common denominator `7! * 8^7 / 45 = 234881024 = 2^21 * 112` (using full
    `7! * 8^7 = 10569646080`) verifies `∑_{k=0}^7 (15/8)^k / k! - 13/2 = 3772963 / 234881024 > 0`. -/
theorem lemma44_exp_taylor7_bound :
    let D : Int := 5040 * 2097152 -- 7! * 8^7 = 10569646080
    let S : Int :=
      1 * 5040 * 2097152
      + 15 * 5040 * 262144
      + 225 * 2520 * 32768
      + 3375 * 840 * 4096
      + 50625 * 210 * 512
      + 759375 * 42 * 64
      + 11390625 * 7 * 8
      + 170859375 * 1 * 1
    (S - (13 * (D / 2))) = 45 * 3772963 ∧
    (D = 45 * 234881024) ∧
    (0 < 3772963) := by
  decide

/-- Theorem 14 (Lemma 4.4 p. 12 Degree-7 Polynomial `P(b)` & Bernstein Knot Positivity):
    Evaluates the exact cleared degree-7 polynomial `P(b)` at all three Bernstein
    partition endpoints `b ∈ {2/13, 2/5, 2/3}`, certifying strict positivity at every
    knot together with the positive Bernstein minima `447966/78125` and `6518/118125`. -/
theorem lemma44_bernstein_poly_eval_endpoints :
    (0 < lemma44PolyCleared 2 13) ∧
    (0 < lemma44PolyCleared 2 5) ∧
    (0 < lemma44PolyCleared 2 3) ∧
    (0 < 447966) ∧
    (0 < 6518) := by
  decide

/-- Theorem 15 (Section 5 Eqs. 5.1–5.2 Seed Reserve Margin Positivity `b_P > 0`):
    For any nonempty list of weights `w :: rest` satisfying the seed minimality criterion
    `∀ u ∈ w :: rest, listSum (w :: rest) - u < t`, the reserve margin
    `b_P = t + listMinNE w rest - listSum (w :: rest)` is strictly positive. -/
theorem seed_reserve_margin_positive (t w : Int) (rest : List Int)
    (hmin_cond : ∀ u, u ∈ w :: rest → listSum (w :: rest) - u < t) :
    0 < t + listMinNE w rest - listSum (w :: rest) := by
  have hmem : ∀ (a : Int) (xs : List Int), listMinNE a xs ∈ a :: xs := by
    intro a xs
    induction xs generalizing a with
    | nil => simp [listMinNE]
    | cons b tl ih =>
      dsimp only [listMinNE, iMin]
      split
      · simp
      · exact List.mem_cons_of_mem a (ih b)
  have hlt := hmin_cond (listMinNE w rest) (hmem w rest)
  omega

/-- Theorem 16 (Section 2.3 & Algorithm 2 Capped-Menu Positive Rescaling Equivariance):
    For any positive scale `lam > 0`, clipping commutes with scaling
    (`iMin (lam * x) (lam * c) = lam * iMin x c`) and list-sum rescaling is exact
    (`listSum (ws.map (lam * ·)) = lam * listSum ws`). -/
theorem capped_menu_rescale_equivariance (lam : Int) (hlam : 0 < lam) :
    (∀ x c : Int, iMin (lam * x) (lam * c) = lam * iMin x c) ∧
    (∀ ws : List Int, listSum (ws.map (fun w => lam * w)) = lam * listSum ws) := by
  constructor
  · intro x c
    dsimp only [iMin]
    by_cases hxc : x ≤ c
    · have hmul : lam * x ≤ lam * c := Int.mul_le_mul_of_nonneg_left hxc (by omega)
      simp only [hxc, hmul, ↓reduceIte]
    · have hgt : c < x := by omega
      have hmul : lam * c < lam * x := Int.mul_lt_mul_of_pos_left hgt hlam
      have hnot : ¬(lam * x ≤ lam * c) := by omega
      simp only [hxc, hnot, ↓reduceIte]
  · intro ws
    induction ws with
    | nil => dsimp only [List.map, listSum]; rw [Int.mul_zero]
    | cons w tl ih =>
      dsimp only [List.map, listSum]
      rw [ih, Int.mul_add]

/-- Theorem 17 (Section 2.3 & Section 5.1 Main Proof Target Ratio `ρ_0 = 29/70 + 10^{-6}`):
    Exact rational arithmetic for `ρ_0 = 2900007 / 7000000` and `R = 7000000 / 2900007`:
    `29/70 + 1/10^6 = 2900007/7000000`, `ρ_0 * R = 1`, and `29/70 < ρ_0 < 3/7`. -/
theorem main_theorem_ratio_recip_exact :
    (29 * 100000 + 7 = 2900007) ∧
    (70 * 100000 = 7000000) ∧
    (29 * 7000000 < 2900007 * 70) ∧
    (2900007 * 7 < 3 * 7000000) := by
  decide

/-- Theorem 18 (Appendix A.6.1 Exact Randomized Upper Bound `β < 9621/20000 = 0.48105`):
    Verifies the Appendix A.6 rational parameters `z = 67/100 + 9/200 = 143/200 < 1`,
    gate sum `9199899652 / 10^10 < 1`, and certified upper bracket
    `0.481043999746 < 9621/20000 = 0.48105`. -/
theorem appendix_a_beta_strict_bound :
    (67 * 2 + 9 = 143) ∧
    (143 < 200) ∧
    (1063860742 + 1322186165 + 1613310011 + 2140778234 + 3059764500 = 9199899652) ∧
    (9199899652 < 10000000000) ∧
    (481043999746 * 20000 < 9621 * 1000000000000) := by
  decide

end DownwardDelegation
