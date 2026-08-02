#!/usr/bin/env python3
"""
Round 4: power-oriented variants of the frozen design (|skew| <= 0.35 ps).

Dynamic power ~ switching activity x bit-width, and mu is quasi-static
(changes only at calibration). Three questions, all quantitative:

Q1  How coarsely can the CORRECTION path be quantized?
    y = x + mu*v: correction-path quantization noise is attenuated by
    mu^2 (~ -21 dB) before reaching the output, so d_k and the product
    can run at far fewer bits than the main path.

Q2  Can the multiplier be removed entirely by folding mu into the taps?
    Effective taps t1 = mu, t2 = -(7/16)mu, t3 = (1/4)mu are quasi-static;
    approximate each online by <= 2 signed-power-of-two terms
    (programmable barrel shifts whose SELECT lines are static -> only
    data toggles). Zero multipliers, zero coefficient switching.

Q3  Analog alternative: what residual delay error delta keeps MSE < -25 dB
    if the 0.35 ps shift is done in the DAC clock (phase interpolator)?
    -> sets the required PI resolution.
"""

import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, mse_db, TS, FS

MU_MAX = 0.35e-12 / TS
C_B = [1.0, -7.0 / 16.0, 1.0 / 4.0]
BETAS = (0.05, 0.10, 0.125)


def q(v, step):
    return np.round(v / step) * step if step > 0 else v


def compensate_quant(x, mu, coeffs, d_step=0, p_step=0):
    """Design B with quantized difference terms and quantized product."""
    v = np.zeros_like(x)
    for k, ck in enumerate(coeffs, start=1):
        v += ck * q(np.roll(x, k) - np.roll(x, -k), d_step)
    return x + q(mu * v, p_step)


def best_spt(target, n_terms, emin=2, emax=14):
    pows = [s * 2.0 ** -e for e in range(emin, emax + 1) for s in (1, -1)]
    best, berr = 0.0, abs(target)
    import itertools
    for nt in range(1, n_terms + 1):
        for combo in itertools.combinations(pows, nt):
            v = sum(combo)
            if abs(v - target) < berr:
                best, berr = v, abs(v - target)
    return best


def main():
    xv = {b: gen_pam4(b, nsym=1 << 15, seed=777) for b in BETAS}
    fs_amp = max(np.max(np.abs(x)) for x in xv.values())
    mus = np.linspace(-MU_MAX, MU_MAX, 15)

    # ---------- Q1: correction-path bit widths ----------
    print("Q1: correction-path truncation (design B, float mu)")
    print("    d-bits = bits for d_k (range +-2FS), p-bits for the product")
    for d_bits, p_bits in ((None, None), (6, None), (5, None), (4, None),
                           (6, 8), (5, 8), (5, 7), (4, 7), (4, 6)):
        d_step = 0 if d_bits is None else 4 * fs_amp / 2 ** d_bits
        p_step = 0 if p_bits is None else 2 * fs_amp / 2 ** p_bits
        worst = -np.inf
        for b, x in xv.items():
            for mu in mus:
                m = mse_db(compensate_quant(x, mu, C_B, d_step, p_step),
                           ideal_delay(x, mu))
                worst = max(worst, m)
        lbl = (f"d={d_bits if d_bits else 'inf'}b, "
               f"p={p_bits if p_bits else 'inf'}b")
        print(f"    {lbl:16s}: worst {worst:7.2f} dB")
    print()

    # ---------- Q2: multiplierless programmable-shift taps ----------
    print("Q2: fold mu into taps, each tap -> best <=T SPT terms "
          "(programmable static shifts, 0 multipliers)")
    for terms in (1, 2, 3):
        worst = -np.inf
        worst_mu = None
        for mu_reg in np.round(mus * 256) / 256:     # 8-bit mu register
            th = [best_spt(c * mu_reg, terms) for c in C_B]
            for b, x in xv.items():
                v = np.zeros_like(x)
                for k, tk in enumerate(th, start=1):
                    v += tk * (np.roll(x, k) - np.roll(x, -k))
                for mu_true in (mu_reg,):
                    m = mse_db(x + v, ideal_delay(x, mu_true))
                    if m > worst:
                        worst, worst_mu = m, mu_reg
        print(f"    <= {terms} SPT terms/tap: worst {worst:7.2f} dB "
              f"(at mu = {worst_mu:+.4f})")

    # combined: 2-SPT taps + 5-bit d_k truncation
    print("    combined: <=2 SPT/tap + d_k truncated to 5 bits:")
    worst = -np.inf
    d_step = 4 * fs_amp / 2 ** 5
    for mu_reg in np.round(mus * 256) / 256:
        th = [best_spt(c * mu_reg, 2) for c in C_B]
        for b, x in xv.items():
            v = np.zeros_like(x)
            for k, tk in enumerate(th, start=1):
                v += tk * q(np.roll(x, k) - np.roll(x, -k), d_step)
            worst = max(worst, mse_db(x + v, ideal_delay(x, mu_reg)))
    print(f"      worst {worst:7.2f} dB")
    print()

    # ---------- Q3: analog clock-shift residual tolerance ----------
    print("Q3: pure delay residual delta -> MSE (sets analog PI resolution)")
    for delta_ps in (0.05, 0.10, 0.15, 0.20, 0.30):
        worst = -np.inf
        for b, x in xv.items():
            m = mse_db(x, ideal_delay(x, delta_ps * 1e-12 / TS))
            worst = max(worst, m)
        print(f"    residual {delta_ps:.2f} ps: {worst:7.2f} dB")


if __name__ == "__main__":
    main()
