#!/usr/bin/env python3
"""Summary figures: MSE-vs-complexity Pareto and error spectrum."""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sim_skew_precomp import (gen_pam4, ideal_delay, fir_apply, mse_db,
                              taps_linear, taps_lagrange, taps_ls,
                              rrc_freq, MU, FS, RS)
from sim_structured import pairs_design, pairs_apply

BETA = 0.10
x = gen_pam4(BETA, seed=1234)
y = ideal_delay(x, MU)
xv = gen_pam4(BETA, seed=999)
yv = ideal_delay(xv, MU)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))

# ---- (a) Pareto: MSE vs real multipliers per sample ----
pts = []
h, c = taps_linear(MU)
pts.append(("linear (2-tap)", 2, mse_db(fir_apply(xv, h, c), yv), "tab:gray"))
h, c = taps_lagrange(MU, 3)
pts.append(("Lagrange-3", 3, mse_db(fir_apply(xv, h, c), yv), "tab:gray"))
h, c = taps_lagrange(MU, 4)
pts.append(("Lagrange-4", 4, mse_db(fir_apply(xv, h, c), yv), "tab:gray"))
for n in (3, 4, 5, 6, 7):
    h, c = taps_ls(x, y, n)
    pts.append((f"LS FIR-{n}", n, mse_db(fir_apply(xv, h, c), yv),
                "tab:blue"))
for ks, lbl in (([1], "1-pair"), ([1, 2], "2-pair"), ([1, 2, 3], "3-pair")):
    cc, _ = pairs_design(x, y, ks, unity_center=True)
    pts.append((f"antisym {lbl}", len(ks),
                mse_db(pairs_apply(xv, ks, cc), yv), "tab:red"))
m_csd = mse_db(pairs_apply(xv, [1, 2], [3 / 32, -5 / 128]), yv)
pts.append(("2-pair CSD\n(0 mult, 4 SPT)", 0, m_csd, "tab:green"))

for lbl, nm, m, col in pts:
    ax1.scatter(nm, m, c=col, s=45, zorder=3)
    ax1.annotate(lbl, (nm, m), textcoords="offset points",
                 xytext=(6, 4), fontsize=7.5)
ax1.axhline(-25, color="k", ls="--", lw=1)
ax1.text(5.5, -24.6, "spec  -25 dB", fontsize=8)
ax1.set_xlabel("real multipliers per output sample")
ax1.set_ylabel("MSE vs ideal compensation (dB)")
ax1.set_title(f"236G PAM4, 1.125 sps, skew 0.35 ps (μ={MU:.3f}), "
              f"β={BETA}")
ax1.grid(alpha=0.3)
ax1.set_xlim(-0.6, 8)

# ---- (b) frequency-domain error of the recommended designs ----
f = np.linspace(0, FS / 2, 2000)
w = 2 * np.pi * f / FS
H_id = np.exp(-1j * w * MU)


def H_pairs(cs, ks):
    H = np.ones_like(w, dtype=complex)
    for ck, k in zip(cs, ks):
        H += ck * (np.exp(-1j * w * k) - np.exp(1j * w * k))
    return H


for cs, ks, lbl, col in (
        ([3 / 32, -5 / 128], [1, 2], "2-pair CSD (0 mult)", "tab:green"),
        (pairs_design(x, y, [1, 2, 3], True)[0], [1, 2, 3],
         "3-pair LS (3 mult)", "tab:red")):
    err = 20 * np.log10(np.abs(H_pairs(cs, ks) - H_id) + 1e-12)
    ax2.plot(f / 1e9, err, color=col, label=lbl)
h2, c2 = taps_linear(MU)
Hlin = h2[0] + h2[1] * np.exp(-1j * w)
ax2.plot(f / 1e9, 20 * np.log10(np.abs(Hlin - H_id) + 1e-12),
         color="tab:gray", label="linear interp (2 mult)")
psd = rrc_freq(f, RS, BETA) ** 2
ax2.plot(f / 1e9, 10 * np.log10(psd + 1e-12), "k:", lw=1,
         label="signal PSD (norm.)")
ax2.axvline((1 + BETA) * RS / 2 / 1e9, color="k", lw=0.6, alpha=0.5)
ax2.set_xlabel("frequency (GHz)")
ax2.set_ylabel("|H - H_ideal|  (dB)")
ax2.set_title("error response vs. signal spectrum")
ax2.set_ylim(-80, 5)
ax2.grid(alpha=0.3)
ax2.legend(fontsize=8, loc="lower right")

fig.tight_layout()
fig.savefig("results.png", dpi=160)
print("saved results.png")
