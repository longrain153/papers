#!/usr/bin/env python3
"""Round-2 figure: tunable compensator — worst-case MSE vs programmable
multipliers, Farrow vs programmable-FIR baseline (numbers from
sim_farrow.py output)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# (label, farrow[(P mults, mse)], progfir[(taps, mse)])
data = [
    ("±0.5 ps  (μ ≤ 0.133)",
     [(1, -26.89), (2, -29.56)],            # P=1 K=4 ; P=2 K=4
     [(5, -24.02), (7, -27.13), (9, -29.56), (11, -31.60)]),
    ("±1.0 ps  (μ ≤ 0.266)",
     [(2, -26.27), (3, -26.34)],            # P=2 K=5
     [(7, -21.86), (9, -24.30), (11, -26.34), (13, -28.10)]),
    ("±1.88 ps (μ ≤ 0.5, full range)",
     [(3, -25.38), (3.15, -26.88)],         # P=3 K=6 ; P=3 K=7 (offset x)
     [(9, -21.62), (11, -23.68), (13, -25.46)]),
]

fig, axes = plt.subplots(1, 3, figsize=(12, 3.8), sharey=True)
for ax, (lbl, farrow, prog) in zip(axes, data):
    xs, ys = zip(*prog)
    ax.plot(xs, ys, "o-", color="tab:blue", label="programmable FIR\n(N mult)")
    xs, ys = zip(*farrow)
    ax.plot(xs, ys, "s", color="tab:red", ms=8,
            label="Farrow (P mult +\nfixed CSD subfilters)")
    ax.axhline(-25, color="k", ls="--", lw=1)
    ax.set_title(lbl, fontsize=10)
    ax.set_xlabel("programmable multipliers / sample")
    ax.grid(alpha=0.3)
    ax.set_xlim(0, 14)
axes[0].set_ylabel("worst-case MSE vs ideal (dB)")
axes[0].legend(fontsize=8, loc="upper right")
fig.suptitle("Tunable skew compensation, 236G PAM4 @ 1.125 sps "
             "(worst case over μ range and β ∈ {0.05, 0.1, 0.125})",
             fontsize=10)
fig.tight_layout(rect=[0, 0, 1, 0.93])
fig.savefig("results_tunable.png", dpi=160)
print("saved results_tunable.png")
