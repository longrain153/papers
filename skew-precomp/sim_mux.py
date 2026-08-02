#!/usr/bin/env python3
"""
Round 4b: how wide do the programmable-shift muxes actually need to be?

Refinement of the round-4 multiplierless design. Instead of folding mu into
all three taps (6 programmable shifters), FACTOR the datapath:

    v[n] = d1 - (7/16) d2 + (1/4) d3     <- 7/16, 1/4 HARDWIRED shifts
    y[n] = x[n] + (+-2^-a +- 2^-b) * v[n] <- ONE programmable 2-term SPT stage

Only TWO programmable shifters (on v), each a small mux; term signs are
static add/sub selects (no mux). mu register is 8-bit (step 2^-8), and
|mu| <= 0.0938 = 24/256, so mu_hat = (+-2^p +- 2^q)/256 with p,q in {0..4}
-> shift exponents in {4..8}: FIVE positions + "off" = 6:1 mux per shifter.

This script verifies, over ALL 8-bit mu codes in range and all roll-offs:
  - exact-ratio property: sharing one mu_hat across taps keeps tap ratios
    exact, so accuracy tracks the float-mu design;
  - worst-case MSE with the {4..8} exponent window (6:1 muxes);
  - same with the correction path truncated to 5 bits;
  - how much a narrower window ({4..7}, 5:1 mux) loses.
"""

import itertools
import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db, TS

C_B = [1.0, -7.0 / 16.0, 1.0 / 4.0]
BETAS = (0.05, 0.10, 0.125)
MU_MAX_CODE = 24                      # 0.0938 * 256


def spt2_in_window(target, exps):
    """Best <=2-term signed-power-of-two approx with exponents in exps."""
    terms = [0.0] + [s * 2.0 ** -e for e in exps for s in (1, -1)]
    best, berr = 0.0, abs(target)
    for a, b in itertools.combinations_with_replacement(terms, 2):
        v = a + b
        if abs(v - target) < berr:
            best, berr = v, abs(v - target)
    return best


def q(v, step):
    return np.round(v / step) * step if step > 0 else v


def run(exps, d_bits=None, label=""):
    xv = {b: gen_pam4(b, nsym=1 << 15, seed=777) for b in BETAS}
    fs_amp = max(np.max(np.abs(x)) for x in xv.values())
    d_step = 0 if d_bits is None else 4 * fs_amp / 2 ** d_bits
    worst, worst_mu = -np.inf, 0
    for k in range(-MU_MAX_CODE, MU_MAX_CODE + 1):
        mu = k / 256.0
        mu_hat = spt2_in_window(mu, exps)
        for b, x in xv.items():
            v = np.zeros_like(x)
            for i, ci in enumerate(C_B, start=1):
                v += ci * q(np.roll(x, i) - np.roll(x, -i), d_step)
            m = mse_db(x + mu_hat * v, ideal_delay(x, mu))
            if m > worst:
                worst, worst_mu = m, mu
    print(f"  {label:42s}: worst {worst:7.2f} dB  (at mu={worst_mu:+.4f})")


def main():
    print("Factored structure: v fixed (hardwired 7/16, 1/4), "
          "y = x + mu_hat * v\n")
    run(range(2, 13), None, "exps {2..12} (ref, unconstrained)")
    run(range(4, 9), None, "exps {4..8}  (5 pos + off = 6:1 mux)")
    run(range(4, 9), 5,    "exps {4..8}  + d_k truncated to 5 bit")
    run(range(4, 8), None, "exps {4..7}  (4 pos + off = 5:1 mux)")
    run(range(5, 9), None, "exps {5..8}  (missing 2^-4: expect fail)")
    print("""
Per-sample datapath (recommended):
  3 narrow subtractions (d1,d2,d3, 5-6 bit)
  2 hardwired shift-adds            -> v  (7/16 = 1/2-1/16, 1/4)
  2 programmable shifts of v        -> two 6:1 muxes, static selects
  1 add (combine SPT terms) + 1 full-width output add
Firmware per calibration: decompose 8-bit mu code (<=24/256) into
(+-2^p +- 2^q)/256, p,q in {0..4}; write 2 x (sign, 3-bit select).""")


if __name__ == "__main__":
    main()
