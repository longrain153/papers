#!/usr/bin/env python3
"""
Quantization-aware CSD (canonical signed digit) search for the 2-pair
antisymmetric skew pre-compensator:

    y[n] = x[n] + c1*(x[n-1] - x[n+1]) + c2*(x[n-2] - x[n+2])

If c1, c2 are sums of a few powers of two, each 'multiplier' is just
1-2 shift-adds -> a fully multiplierless compensator.

Search: enumerate all 1- and 2-term signed power-of-two values near the
LS optimum for (c1, c2) jointly, and report the best MSE (validated on an
independent signal realization). Also do the same for the 3-pair design.
"""

import itertools
import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db, MU
from sim_structured import pairs_design, pairs_apply


def spt_candidates(target, max_terms=2, shift_range=(2, 9)):
    """Signed-power-of-two sums with <= max_terms terms near target."""
    pows = [s * 2.0 ** -e for e in range(*shift_range) for s in (1, -1)]
    cands = {0.0: 0}
    for nt in range(1, max_terms + 1):
        for combo in itertools.combinations(pows, nt):
            v = sum(combo)
            if abs(v - target) < 0.35 * max(abs(target), 0.02):
                if v not in cands or nt < cands[v]:
                    cands[v] = nt
    return sorted(cands.items())


def main():
    results = {}
    for beta in (0.05, 0.10, 0.125):
        x = gen_pam4(beta, seed=1234)
        y = ideal_delay(x, MU)
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)

        c_ls, _ = pairs_design(x, y, [1, 2], unity_center=True)
        best = None
        for (v1, n1) in spt_candidates(c_ls[0]):
            for (v2, n2) in spt_candidates(c_ls[1]):
                m = mse_db(pairs_apply(xv, [1, 2], [v1, v2]), yv)
                adders = n1 + n2  # shift-adds inside the two "multipliers"
                key = (m, adders)
                if best is None or (m < best[0] and adders <= best[1] + 1) \
                   or (adders < best[1] and m < -25.5):
                    best = (m, adders, v1, v2)
        results[beta] = best
        m, na, v1, v2 = best
        print(f"beta={beta}: best 2-pair CSD  c1={v1:+.6f}  c2={v2:+.6f}  "
              f"-> {m:7.2f} dB  ({na} shift-add terms, 0 multipliers)")

    # cross-check one fixed CSD choice across all rolloffs
    print("\nFixed choice c1 = 3/32 = 0.09375, c2 = -5/128 = -0.0390625 "
          "(2+2 SPT terms):")
    for beta in (0.05, 0.10, 0.125):
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)
        m = mse_db(pairs_apply(xv, [1, 2], [3 / 32, -5 / 128]), yv)
        print(f"  beta={beta}: {m:7.2f} dB")

    print("\nSimpler fixed choice c1 = 3/32, c2 = -1/32 (2+1 SPT terms):")
    for beta in (0.05, 0.10, 0.125):
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)
        m = mse_db(pairs_apply(xv, [1, 2], [3 / 32, -1 / 32]), yv)
        print(f"  beta={beta}: {m:7.2f} dB")

    print("\nSimplest fixed choice c1 = 1/16+1/32, c2 = -1/32+... skipped; "
          "try c1=0.09375, c2=-0.046875 (=-3/64):")
    for beta in (0.05, 0.10, 0.125):
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)
        m = mse_db(pairs_apply(xv, [1, 2], [3 / 32, -3 / 64]), yv)
        print(f"  beta={beta}: {m:7.2f} dB")

    # 3-pair CSD for margin
    print("\n3-pair CSD (margin option):")
    for beta in (0.10, 0.125):
        x = gen_pam4(beta, seed=1234)
        y = ideal_delay(x, MU)
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)
        c_ls, _ = pairs_design(x, y, [1, 2, 3], unity_center=True)
        best = None
        for (v1, n1) in spt_candidates(c_ls[0]):
            for (v2, n2) in spt_candidates(c_ls[1]):
                for (v3, n3) in spt_candidates(c_ls[2]):
                    m = mse_db(pairs_apply(xv, [1, 2, 3], [v1, v2, v3]), yv)
                    adders = n1 + n2 + n3
                    if best is None or m < best[0]:
                        best = (m, adders, v1, v2, v3)
        m, na, v1, v2, v3 = best
        print(f"  beta={beta}: c=({v1:+.6f},{v2:+.6f},{v3:+.6f}) "
              f"-> {m:7.2f} dB  ({na} SPT terms)")


if __name__ == "__main__":
    main()
