#!/usr/bin/env python3
"""
Structured low-multiplier skew pre-compensators for mu = 0.0929 samples.

Idea: for small fractional delay, e^{-j*w*mu} = cos(w*mu) - j*sin(w*mu),
with cos(w*mu) ~ 1 in-band. Constrain the FIR to

    h = unity center tap + antisymmetric correction pairs
    y[n] = x[n-c] + sum_k c_k * ( x[n-c-k] - x[n-c+k] )

Each pair costs ONE multiplier (pre-subtract then multiply), the center tap
costs none. So K pairs -> K multipliers total.

Variants tested:
  A) K pairs, unity center            -> K mult
  B) K pairs, free center tap         -> K+1 mult
  C) unconstrained N-tap LS, all integer center offsets (baseline recheck)
Plus coefficient quantization of the winners.
"""

import numpy as np
from sim_skew_precomp import (gen_pam4, ideal_delay, fir_apply, mse_db,
                              taps_ls, quantize, MU, TS, FS, RS)


def pairs_design(x, y_ref, ks, unity_center=True):
    """LS fit of antisymmetric-pair correction; returns callable + coeffs."""
    d_cols = [np.roll(x, k) - np.roll(x, -k) for k in ks]   # x[n-k]-x[n+k]
    A = np.stack(d_cols, axis=1)
    if unity_center:
        target = y_ref - x
        c, *_ = np.linalg.lstsq(A, target, rcond=None)
        g = None
    else:
        A = np.concatenate([x[:, None], A], axis=1)
        c_all, *_ = np.linalg.lstsq(A, y_ref, rcond=None)
        g, c = c_all[0], c_all[1:]
    return c, g


def pairs_apply(x, ks, c, g=None):
    y = x.copy() if g is None else g * x
    for k, ck in zip(ks, c):
        y += ck * (np.roll(x, k) - np.roll(x, -k))
    return y


def pairs_quantize(x, ks, c, g, bits):
    cq = quantize(np.asarray(c), bits)
    gq = None if g is None else quantize(np.asarray([g]), bits)[0]
    return pairs_apply(x, ks, cq, gq)


def ls_best_center(x, y_ref, xv, yv, n_taps):
    """Unconstrained N-tap LS, searching all integer center offsets."""
    best = (0, None, 0)
    for c in range(n_taps):
        cols = [np.roll(x, k - c) for k in range(n_taps)]
        A = np.stack(cols, axis=1)
        h, *_ = np.linalg.lstsq(A, y_ref, rcond=None)
        m = mse_db(fir_apply(xv, h, c), yv)
        if best[1] is None or m < best[0]:
            best = (m, h, c)
    return best


def main():
    print(f"mu = {MU:.6f} samples ({MU*TS*1e15:.0f} fs)\n")
    for beta in (0.05, 0.10, 0.125):
        x = gen_pam4(beta, seed=1234)
        y = ideal_delay(x, MU)
        xv = gen_pam4(beta, seed=999)
        yv = ideal_delay(xv, MU)
        print(f"===== beta = {beta} =====")

        for ks in ([1], [1, 2], [1, 2, 3], [1, 2, 3, 4]):
            c, _ = pairs_design(x, y, ks, unity_center=True)
            m = mse_db(pairs_apply(xv, ks, c), yv)
            print(f"  A) {len(ks)} pair(s) k={ks}, unity center : "
                  f"{m:7.2f} dB   ({len(ks)} mult)")

        for ks in ([1], [1, 2], [1, 2, 3]):
            c, g = pairs_design(x, y, ks, unity_center=False)
            m = mse_db(pairs_apply(xv, ks, c, g), yv)
            print(f"  B) {len(ks)} pair(s) k={ks}, free center  : "
                  f"{m:7.2f} dB   ({len(ks)+1} mult)")

        for n in (3, 4, 5):
            m, h, cc = ls_best_center(x, y, xv, yv, n)
            print(f"  C) {n}-tap LS best center (c={cc})    : "
                  f"{m:7.2f} dB   ({n} mult)")
        print()

        if beta == 0.10:
            print("  ---- winners @ beta=0.1, quantized ----")
            for ks, unity in (([1, 2], True), ([1, 2, 3], True),
                              ([1, 2], False)):
                c, g = pairs_design(x, y, ks, unity_center=unity)
                tag = "unity" if unity else "free "
                nm = len(ks) + (0 if unity else 1)
                print(f"  pairs k={ks} ({tag} center, {nm} mult), "
                      f"c = {np.array2string(np.asarray(c), precision=6)}"
                      + ("" if unity else f", g = {g:.6f}"))
                for bits in (5, 6, 8, 10):
                    m = mse_db(pairs_quantize(xv, ks, c, g, bits), yv)
                    print(f"      {bits:2d}-bit: {m:7.2f} dB")
            print()


if __name__ == "__main__":
    main()
