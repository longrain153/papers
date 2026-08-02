#!/usr/bin/env python3
"""
FINAL frozen design (round 3): tunable skew compensation, |skew| <= 0.35 ps
(mu in [-0.093, +0.093] samples), 236G PAM4 @ 265.5 GSa/s.

    d1[n] = x[n-1] - x[n+1]
    d2[n] = x[n-2] - x[n+2]
    d3[n] = x[n-3] - x[n+3]                      (option B only)

    A (minimal):  y[n] = x[n] + mu * ( d1[n] - (7/16)*d2[n] )
    B (margin) :  y[n] = x[n] + mu * ( d1[n] - (7/16)*d2[n] + (1/4)*d3[n] )

Hardware per output sample:
    A: 1 programmable multiplier (mu, 6-bit signed suffices) + 5 adders
    B: 1 programmable multiplier + 7 adders
(7/16 = 1/2 - 1/16 -> 2 shift-adds; 1/4 -> pure shift.)

This script validates worst-case MSE vs the ideal (spectral) delay over a
dense mu grid and all feasible RRC roll-offs, on signals independent of any
design data (the coefficients are hard-coded constants).
"""

import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db, TS

C_A = [1.0, -7.0 / 16.0]
C_B = [1.0, -7.0 / 16.0, 1.0 / 4.0]
MU_MAX = 0.35e-12 / TS


def compensate(x, mu, coeffs):
    v = np.zeros_like(x)
    for k, ck in enumerate(coeffs, start=1):
        v += ck * (np.roll(x, k) - np.roll(x, -k))
    return x + mu * v


def main():
    print(f"|mu| <= {MU_MAX:.4f} samples  (0.35 ps @ {1/TS/1e9:.1f} GSa/s)\n")
    for name, coeffs in (("A: 2-pair, 1 mult + 5 add", C_A),
                         ("B: 3-pair, 1 mult + 7 add", C_B)):
        print(f"design {name}")
        worst = -np.inf
        for beta in (0.05, 0.10, 0.125):
            xv = gen_pam4(beta, nsym=1 << 15, seed=777)
            row = []
            for mu in np.linspace(-MU_MAX, MU_MAX, 15):
                m = mse_db(compensate(xv, mu, coeffs), ideal_delay(xv, mu))
                row.append(m)
                worst = max(worst, m)
            print(f"  beta={beta:5}: worst over mu grid = {max(row):7.2f} dB, "
                  f"at nominal +0.35 ps = {row[-1]:7.2f} dB")
        margin = -25 - worst
        print(f"  ==> WORST CASE {worst:7.2f} dB  "
              f"(margin {margin:.1f} dB vs -25 dB spec)\n")

    # mu register resolution
    xv = gen_pam4(0.125, nsym=1 << 15, seed=777)
    for bits in (5, 6, 8):
        worst = -np.inf
        for mu in np.linspace(-MU_MAX, MU_MAX, 31):
            muq = np.round(mu * 2 ** bits) / 2 ** bits
            m = mse_db(compensate(xv, muq, C_B), ideal_delay(xv, mu))
            worst = max(worst, m)
        print(f"design B with {bits}-bit signed-fractional mu register: "
              f"{worst:7.2f} dB")


if __name__ == "__main__":
    main()
