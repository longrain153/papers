#!/usr/bin/env python3
"""
Round 5: extend the multiplierless tunable compensator to |skew| <= 1 ps
(mu in [-0.2655, +0.2655] samples).

First order is insufficient here (round 2: ~-18 dB): the even error term
cos(w*mu)-1 ~ -(w*mu)^2/2 matters now. Structure = 2nd-order parity Farrow
with BOTH quasi-static scalars realized as SPT shift stages:

    v1[n] = sum_k a_k (x[n-k] - x[n+k])      k = 1..K1  (antisymmetric)
    v2[n] = b_0 x[n] + sum_k b_k (x[n-k] + x[n+k])  k = 1..K2 (symmetric)
    y[n]  = x[n] + s1 * v1[n] + s2 * v2[n]

s1 ~ mu (<= n1 SPT terms), s2 ~ mu^2 (<= n2 SPT terms) -> 0 multipliers.
Questions answered numerically:
  Q1  minimal (K1, K2) at float scalars (C2 should be much shorter than C1)
  Q2  SPT terms needed for s1 / s2 (mu register 8 bit, |code| <= 68)
  Q3  correction-path truncation budget (attenuation now only mu^2 ~ -11 dB)
Worst case over dense mu grid x roll-offs {0.05, 0.10, 0.125}.
"""

import itertools
import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db, TS

BETAS = (0.05, 0.10, 0.125)
MU_MAX = 1.0e-12 / TS                 # 0.2655
MU_MAX_CODE = int(round(MU_MAX * 256))  # 68


def design(x, K1, K2, mus):
    odd = [np.roll(x, k) - np.roll(x, -k) for k in range(1, K1 + 1)]
    even = [x] + [np.roll(x, k) + np.roll(x, -k) for k in range(1, K2 + 1)]
    blocks, targets = [], []
    for mu in mus:
        cols = [mu * c for c in odd] + [mu * mu * c for c in even]
        blocks.append(np.stack(cols, axis=1))
        targets.append(ideal_delay(x, mu) - x)
    th, *_ = np.linalg.lstsq(np.concatenate(blocks),
                             np.concatenate(targets), rcond=None)
    return th[:K1], th[K1:]


def q(v, step):
    return np.round(v / step) * step if step > 0 else v


def apply_c(x, a, b, s1, s2, d_step=0):
    v1 = np.zeros_like(x)
    for k, ak in enumerate(a, start=1):
        v1 += ak * q(np.roll(x, k) - np.roll(x, -k), d_step)
    v2 = b[0] * q(x, d_step / 2 if d_step else 0)
    for k, bk in enumerate(b[1:], start=1):
        v2 += bk * q(np.roll(x, k) + np.roll(x, -k), d_step)
    return x + s1 * v1 + s2 * v2


def best_spt(t, n_terms, emin=1, emax=12):
    pows = [s * 2.0 ** -e for e in range(emin, emax + 1) for s in (1, -1)]
    best, berr = 0.0, abs(t)
    for nt in range(1, n_terms + 1):
        for combo in itertools.combinations(pows, nt):
            v = sum(combo)
            if abs(v - t) < berr:
                best, berr = v, abs(v - t)
    return best


def worst(a, b, xv, spt=None, d_step=0, n_mu=17):
    w = -np.inf
    for k in np.linspace(-MU_MAX_CODE, MU_MAX_CODE, n_mu):
        mu = round(k) / 256.0
        s1, s2 = mu, mu * mu
        if spt:
            s1 = best_spt(s1, spt[0])
            s2 = best_spt(np.sign(s2) * s2, spt[1])
        for beta, x in xv.items():
            m = mse_db(apply_c(x, a, b, s1, s2, d_step), ideal_delay(x, mu))
            w = max(w, m)
    return w


def main():
    x = gen_pam4(0.125, nsym=1 << 14, seed=1234)
    xv = {b: gen_pam4(b, nsym=1 << 14, seed=999) for b in BETAS}
    mus_fit = np.linspace(-MU_MAX, MU_MAX, 11)
    fs_amp = max(np.max(np.abs(v)) for v in xv.values())

    print(f"|mu| <= {MU_MAX:.4f} (1 ps), mu code <= {MU_MAX_CODE}\n")
    print("Q1: minimal (K1, K2), float scalars:")
    designs = {}
    for K1 in (4, 5, 6):
        for K2 in (1, 2, 3):
            a, b = design(x, K1, K2, mus_fit)
            designs[(K1, K2)] = (a, b)
            print(f"  K1={K1} K2={K2}: {worst(a, b, xv):7.2f} dB")
    print()

    print("Q2: SPT-quantized scalars (winner candidates):")
    for K1, K2 in ((5, 2), (5, 3), (6, 2), (6, 3)):
        a, b = designs[(K1, K2)]
        for spt in ((2, 1), (2, 2), (3, 2)):
            print(f"  K1={K1} K2={K2}, s1<={spt[0]} SPT, s2<={spt[1]} SPT: "
                  f"{worst(a, b, xv, spt=spt):7.2f} dB")
    print()

    print("Q3: + correction-path truncation (d_k bits over +-2FS):")
    K1, K2 = 6, 2
    a, b = designs[(K1, K2)]
    for d_bits in (8, 7, 6, 5):
        d_step = 4 * fs_amp / 2 ** d_bits
        print(f"  K1=6 K2=2, s1<=3,s2<=2 SPT, d_k {d_bits}bit: "
              f"{worst(a, b, xv, spt=(3, 2), d_step=d_step):7.2f} dB")
    print()
    print(f"  winning subfilters  a (C1) = {np.array2string(a, precision=5)}")
    print(f"                      b (C2) = {np.array2string(b, precision=5)}")


if __name__ == "__main__":
    main()
