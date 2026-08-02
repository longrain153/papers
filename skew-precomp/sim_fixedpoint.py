#!/usr/bin/env python3
"""
Bit-exact fixed-point verification of the final power-optimized datapath
(round 4b factored structure), to pin down every node width for the
block diagram.

Convention: FS = full-scale amplitude of x. Main path is s8
(8-bit signed, LSB = FS/128 = 2FS/2^8). All intermediate nodes are
quantized exactly as the hardware would:

  x_q                : s8,  LSB FS/128
  x_t  (top-5 trunc) : s5,  LSB FS/16      (correction path input)
  d_k = x_t - x_t    : s6,  LSB FS/16,  range +-2FS
  7/16*d2, 1/4*d3    : rounded to LSB FS/32
  v                  : s8,  LSB FS/32,  range +-3.375FS
  v>>a, v>>b (a,b in {4..7}) rounded to LSB FS/128 -> s6
  c = +-t1 +- t2     : s7,  LSB FS/128, range +-0.33FS
  y = sat(x_q + c)   : s9 pre-sat -> saturate/round to s8 out

Reference: ideal spectral delay of the SAME s8-quantized input (input
quantization is common-mode, not chargeable to the compensator).
"""

import itertools
import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db

BETAS = (0.05, 0.10, 0.125)
MU_MAX_CODE = 24


def spt2(target, exps=range(4, 8)):
    terms = [0.0] + [s * 2.0 ** -e for e in exps for s in (1, -1)]
    best, berr = 0.0, abs(target)
    for a, b in itertools.combinations_with_replacement(terms, 2):
        if abs(a + b - target) < berr:
            best, berr = a + b, abs(a + b - target)
    return best


def rnd(v, step):
    return np.round(v / step) * step


def datapath(xq, mu_hat, fs):
    xt = rnd(xq, fs / 16)                      # s5 truncation
    d = [np.roll(xt, k) - np.roll(xt, -k) for k in (1, 2, 3)]   # s6
    t2 = rnd(-7.0 / 16.0 * d[1], fs / 32)      # hardwired >>1 - >>4
    t3 = rnd(0.25 * d[2], fs / 32)             # hardwired >>2
    v = d[0] + t2 + t3                         # s8, LSB fs/32
    c = rnd(mu_hat * v, fs / 128)              # two 5:1-mux shifts, s7
    y = xq + c                                 # s9
    return np.clip(y, -fs, fs - fs / 128)      # saturate to s8


def main():
    worst, worst_at = -np.inf, None
    for beta in BETAS:
        x = gen_pam4(beta, nsym=1 << 15, seed=777)
        fs = np.max(np.abs(x)) * 1.0001
        xq = rnd(x, fs / 128)                  # s8 input
        for k in range(-MU_MAX_CODE, MU_MAX_CODE + 1):
            mu = k / 256.0
            y = datapath(xq, spt2(mu), fs)
            m = mse_db(y, ideal_delay(xq, mu))
            if m > worst:
                worst, worst_at = m, (beta, mu)
    print("bit-exact fixed-point chain (widths as in the block diagram):")
    print(f"  worst MSE = {worst:.2f} dB  at beta={worst_at[0]}, "
          f"mu={worst_at[1]:+.4f}")
    print("  spec -25 dB -> margin %.1f dB" % (-25 - worst))


if __name__ == "__main__":
    main()
