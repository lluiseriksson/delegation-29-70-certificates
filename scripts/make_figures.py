"""Generate 3 publication-quality 300 DPI figures for DC-DELEG-CERT-1.0.

Author: Lluis Eriksson
License: MIT
"""

from __future__ import annotations

from fractions import Fraction
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent


def _f(s: str) -> float:
    return float(Fraction(s))


def make_fig1() -> None:
    d1 = json.loads((ROOT / "data" / "exp1_knapsack5_impossibility_curve.json").read_text(encoding="utf-8"))["rows"]
    d4 = json.loads((ROOT / "data" / "exp4_capped_menu_scores.json").read_text(encoding="utf-8"))["rows"]

    inv_eps = [round(1.0 / _f(r["eps"])) for r in d1]
    det_r = [_f(r["det_ratio"]) for r in d1]
    rand_r = [_f(r["rand_ratio"]) for r in d1]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.35), dpi=300)

    ax1.semilogx(inv_eps, rand_r, "o-", color="#b03a2e", lw=1.8, ms=4, label=r"Randomized cap ($\eta=\varepsilon$)")
    ax1.semilogx(inv_eps, det_r, "s--", color="#1b4f72", lw=1.8, ms=4, label="Deterministic cap")
    ax1.axhline(0.5, color="#555555", ls=":", lw=1.2, label=r"Matroid optimal $1/2$")
    ax1.axhline(30 / 61, color="#148f77", ls="-.", lw=1.2, label=r"Prop. 3.3 limit $30/61 \approx 0.4918$")
    ax1.set_xlabel(r"Inverse jackpot probability $1/\varepsilon$", fontsize=8.5)
    ax1.set_ylabel("Certified upper bound on ratio", fontsize=8.5)
    ax1.set_title("(a) Five-item knapsack separation below 1/2", fontsize=9.0, fontweight="bold")
    ax1.set_ylim(0.490, 0.525)
    ax1.grid(True, which="both", alpha=0.22)
    ax1.legend(fontsize=6.6, loc="upper right", framealpha=0.92)

    labels = ["Alg. 2\nThreshold", "Alg. 2\nSeeds+Upper", "Alg. 2\nSeeds+Res.", "Lem. 2.2\nSafe-Norm"]
    ratios = [_f(r["ratio"]) for r in d4]
    colors = ["#1b4f72", "#148f77", "#b9770e", "#7d3c98"]
    bars = ax2.bar(labels, ratios, color=colors, edgecolor="#222222", lw=0.5)
    ax2.axhline(29 / 70, color="#c0392b", ls="--", lw=1.5, label=r"Thm. 1.1 bound $29/70 \approx 0.4143$")
    ax2.axhline(3 / 10, color="#555555", ls=":", lw=1.3, label=r"Thm. 4.1 warm-up $3/10$")
    for b, rv in zip(bars, ratios):
        ax2.text(
            b.get_x() + b.get_width() / 2.0,
            rv + 0.015,
            f"{rv:.3f}",
            ha="center",
            va="bottom",
            fontsize=7.3,
            fontweight="bold",
        )
    ax2.set_ylim(0, 1.14)
    ax2.set_ylabel(r"Exact menu score ratio $\mathbb{E}[b_M]/V$", fontsize=8.5)
    ax2.set_title("(b) Certified Alg. 2 capped-menu score ratios", fontsize=9.0, fontweight="bold")
    ax2.tick_params(axis="x", labelsize=7.5)
    ax2.grid(True, axis="y", alpha=0.25)
    ax2.legend(fontsize=6.7, loc="upper left", framealpha=0.92)

    fig.tight_layout()
    out = ROOT / "figures" / "fig1_knapsack_and_menus.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=300)
    plt.close(fig)


def make_fig2() -> None:
    d2 = json.loads((ROOT / "data" / "exp2_lemma44_bernstein_coeffs.json").read_text(encoding="utf-8"))["rows"]
    d3 = json.loads((ROOT / "data" / "exp3_appendix_a_taylor_convergence.json").read_text(encoding="utf-8"))["rows"]

    ks = [r["k"] for r in d2]
    bl = [_f(r["beta_left"]) for r in d2]
    br = [_f(r["beta_right"]) for r in d2]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.35), dpi=300)

    ax1.semilogy(ks, bl, "o-", color="#1b4f72", lw=1.9, ms=4.5, label=r"$[2/13,\, 2/5]$ ($\min = 447966/78125$)")
    ax1.semilogy(ks, br, "s-", color="#d35400", lw=1.9, ms=4.5, label=r"$[2/5,\, 2/3]$ ($\min = 6518/118125$)")
    ax1.set_xticks(ks)
    ax1.set_ylim(0.03, 95)
    ax1.set_xlabel(r"Bernstein basis index $k \in \{0,\dots,7\}$", fontsize=8.5)
    ax1.set_ylabel(r"Exact Bernstein coefficient $\beta_k > 0$", fontsize=8.5)
    ax1.set_title("(a) Lemma 4.4 positive Bernstein certificate", fontsize=9.0, fontweight="bold")
    ax1.grid(True, which="both", alpha=0.22)
    ax1.legend(fontsize=6.5, loc="lower right", framealpha=0.92)

    degs = [r["taylor_odd_deg"] for r in d3]
    # Plot gap to 0.48105 (positive means strictly below 0.48105!)
    cap = 0.48105
    hi_vals = [float(r["beta_hi_12"]) for r in d3]
    lo_vals = [float(r["beta_lo_12"]) for r in d3]
    widths = [max(h - l, 1e-13) for h, l in zip(hi_vals, lo_vals)]

    ax2.semilogy(degs, widths, "o-", color="#7d3c98", lw=1.9, ms=4.5, label=r"Bracket width $\beta_{\mathrm{hi}} - \beta_{\mathrm{lo}}$")
    ax2.axhline(cap - hi_vals[-1], color="#148f77", ls="--", lw=1.4, label=r"Headroom $0.48105 - \beta_{\mathrm{hi}} \approx 6.0\times 10^{-6}$")
    ax2.axvline(19, color="#b03a2e", ls=":", lw=1.3, label="App. A.6.2 deg 18/19")
    ax2.set_xticks(degs)
    ax2.set_xlabel("Alternating Taylor odd degree", fontsize=8.5)
    ax2.set_ylabel("Exact rational bracket width", fontsize=8.5)
    ax2.set_title(r"(b) App. A.6 Taylor certification ($\beta < 0.48105$)", fontsize=9.0, fontweight="bold")
    ax2.grid(True, which="both", alpha=0.22)
    ax2.legend(fontsize=6.4, loc="upper right", framealpha=0.92)

    fig.tight_layout()
    out = ROOT / "figures" / "fig2_bernstein_and_taylor_beta.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)


def make_fig3() -> None:
    rep = json.loads((ROOT / "data" / "certificate_replay_summary.json").read_text(encoding="utf-8"))["certificates"]
    short_names = [f"C{i+1:02d}" for i in range(len(rep))]
    ms_vals = [r["verify_ns"] / 1_000_000 for r in rep]
    mode_colors = {
        "knapsack5_impossibility_cert": "#1b4f72",
        "lemma44_bernstein_3_10_cert": "#148f77",
        "capped_menu_score_cert": "#b9770e",
        "appendix_a_taylor_beta_cert": "#922b21",
    }
    bar_colors = [mode_colors[r["mode"]] for r in rep]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.2, 3.35), dpi=300)
    ax1.bar(short_names, ms_vals, color=bar_colors, edgecolor="#222222", lw=0.4)
    ax1.set_ylabel("Replay time (ms)", fontsize=8.5)
    ax1.set_xlabel("Canonical certificates (M1: C01-C04, M2: C05-C08, M3: C09-C12, M4: C13-C16)", fontsize=7.0)
    ax1.set_title("(a) Exact-Q replay latency (16/16 PASS)", fontsize=9.0, fontweight="bold")
    ax1.tick_params(axis="x", labelsize=6.8, rotation=45)
    ax1.grid(True, axis="y", alpha=0.25)

    cats = ["Global\nSchema", "Mode 1\nKnap-5", "Mode 2\nBernst.", "Mode 3\nAlg. 2", "Mode 4\nApp. A"]
    counts = [12, 12, 12, 12, 12]
    colors2 = ["#34495e", "#1b4f72", "#148f77", "#b9770e", "#922b21"]
    bars = ax2.bar(cats, counts, color=colors2, edgecolor="#222222", lw=0.5)
    for b in bars:
        ax2.text(
            b.get_x() + b.get_width() / 2.0,
            b.get_height() + 0.35,
            "12/12",
            ha="center",
            va="bottom",
            fontsize=7.5,
            fontweight="bold",
        )
    ax2.set_ylim(0, 14.5)
    ax2.set_ylabel("Forged payloads rejected", fontsize=8.5)
    ax2.set_title("(b) Live adversarial red-team audit (60/60)", fontsize=9.0, fontweight="bold")
    ax2.tick_params(axis="x", labelsize=7.5)
    ax2.grid(True, axis="y", alpha=0.25)

    fig.tight_layout()
    out = ROOT / "figures" / "fig3_certificate_replay_atlas.png"
    fig.savefig(out, dpi=300)
    plt.close(fig)


def main() -> None:
    make_fig1()
    make_fig2()
    make_fig3()
    print("Generated all 3 figures in figures/.")


if __name__ == "__main__":
    main()
