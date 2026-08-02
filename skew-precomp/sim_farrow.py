#!/usr/bin/env python3
"""
Round 2: ONLINE-TUNABLE skew compensation (standalone, no TX-FIR reuse).

Skew is a slowly-varying calibration parameter -> the cost that matters is
the number of PROGRAMMABLE multipliers per output sample (fixed-coefficient
subfilters reduce to shift-adds via CSD).

Structure: parity-constrained Farrow with exact identity at mu = 0:

    y[n] = x[n] + sum_{p=1..P} mu^p * (C_p * x)[n]

  - odd  p: C_p antisymmetric -> pairs (x[n-k] - x[n+k]), zero center
  - even p: C_p symmetric     -> pairs (x[n-k] + x[n+k]) + center tap
  - subfilter coefficients are FIXED (designed once, CSD-able)
  - firmware precomputes mu, mu^2, ..., mu^P  (updated only on calibration)
  - hardware per sample: P programmable multipliers + adders

Baseline for comparison: N-tap programmable-coefficient FIR whose taps are
recomputed by firmware for each mu (cost: N programmable multipliers).

Integer part of the skew is assumed handled by a mux-select delay line, so
the fractional range to cover is mu in [-1/2, +1/2] samples (+-1.88 ps).
Smaller calibration ranges are also swept.

All designs are fit on beta = 0.125 (widest PSD, worst case) and validated
on independent signals at beta in {0.05, 0.10, 0.125}; reported MSE is the
WORST case over the mu range and over beta.
"""

import numpy as np
from sim_skew_precomp import gen_pam4, ideal_delay, fir_apply, mse_db, TS

BETAS = (0.05, 0.10, 0.125)
NSYM_FIT = 1 << 14


def farrow_design(x, P, K, mus):
    """Parity-constrained LS Farrow fit. Returns coeff dict."""
    # basis columns (per mu they get scaled by mu^p)
    odd_cols = [np.roll(x, k) - np.roll(x, -k) for k in range(1, K + 1)]
    even_cols = [x] + [np.roll(x, k) + np.roll(x, -k) for k in range(1, K + 1)]
    blocks, targets = [], []
    for mu in mus:
        cols = []
        for p in range(1, P + 1):
            base = odd_cols if p % 2 == 1 else even_cols
            cols += [(mu ** p) * col for col in base]
        blocks.append(np.stack(cols, axis=1))
        targets.append(ideal_delay(x, mu) - x)
    A = np.concatenate(blocks, axis=0)
    b = np.concatenate(targets)
    theta, *_ = np.linalg.lstsq(A, b, rcond=None)
    # unpack per order
    coeffs, i = {}, 0
    for p in range(1, P + 1):
        n = K if p % 2 == 1 else K + 1
        coeffs[p] = theta[i:i + n].copy()
        i += n
    return coeffs


def farrow_apply(x, coeffs, mu, K):
    y = x.copy()
    odd_cols = [np.roll(x, k) - np.roll(x, -k) for k in range(1, K + 1)]
    even_cols = [x] + [np.roll(x, k) + np.roll(x, -k) for k in range(1, K + 1)]
    for p, c in coeffs.items():
        base = odd_cols if p % 2 == 1 else even_cols
        v = np.zeros_like(x)
        for ck, col in zip(c, base):
            v += ck * col
        y += (mu ** p) * v
    return y


def worst_mse(coeffs, K, mu_range, xv_by_beta, n_mu=13):
    worst = -np.inf
    mus = np.linspace(-mu_range, mu_range, n_mu)
    for beta, xv in xv_by_beta.items():
        for mu in mus:
            m = mse_db(farrow_apply(xv, coeffs, mu, K), ideal_delay(xv, mu))
            worst = max(worst, m)
    return worst


def prog_fir_worst(x, xv_by_beta, n_taps, mu_range, n_mu=13):
    """Baseline: per-mu LS-redesigned programmable N-tap FIR."""
    worst = -np.inf
    c = (n_taps - 1) // 2
    for mu in np.linspace(-mu_range, mu_range, n_mu):
        y = ideal_delay(x, mu)
        cols = [np.roll(x, k - c) for k in range(n_taps)]
        h, *_ = np.linalg.lstsq(np.stack(cols, axis=1), y, rcond=None)
        for beta, xv in xv_by_beta.items():
            m = mse_db(fir_apply(xv, h, c), ideal_delay(xv, mu))
            worst = max(worst, m)
    return worst


def quantize_coeffs(coeffs, bits):
    out = {}
    for p, c in coeffs.items():
        m = np.max(np.abs(c))
        step = 2.0 ** np.ceil(np.log2(m)) / 2.0 ** (bits - 1)
        out[p] = np.round(c / step) * step
    return out


def main():
    x = gen_pam4(0.125, nsym=NSYM_FIT, seed=1234)
    xv_by_beta = {b: gen_pam4(b, nsym=NSYM_FIT, seed=999) for b in BETAS}

    ranges = {
        "±0.50 ps  (mu ±0.133)": 0.50e-12 / TS,
        "±1.00 ps  (mu ±0.266)": 1.00e-12 / TS,
        "±1.88 ps  (mu ±0.500, full)": 0.5,
    }

    print("Worst-case MSE (dB) over the mu range and beta in {0.05,0.1,0.125}")
    print("Farrow: P = polynomial order = programmable mults, "
          "K = correction pairs\n")

    results = {}
    for label, R in ranges.items():
        print(f"===== calibration range {label} =====")
        mus_fit = np.linspace(-R, R, 9)
        for P in (1, 2, 3, 4):
            row = f"  P={P} ({P} mult): "
            for K in (2, 3, 4, 5, 6):
                coeffs = farrow_design(x, P, K, mus_fit)
                w = worst_mse(coeffs, K, R, xv_by_beta)
                results[(label, P, K)] = (w, coeffs)
                row += f" K={K}:{w:7.2f}"
            print(row)
        for n in (5, 7, 9, 11, 13):
            w = prog_fir_worst(x, xv_by_beta, n, R)
            print(f"  baseline prog-FIR {n:2d} taps ({n} mult): {w:7.2f} dB")
        print()

    # ---- detail the minimal designs ----
    print("===== minimal designs meeting -25 dB =====")
    for label, R in ranges.items():
        best = None
        for P in (1, 2, 3, 4):
            for K in (2, 3, 4, 5, 6):
                w, coeffs = results[(label, P, K)]
                if w < -25 and (best is None or (P, K) < (best[0], best[1])):
                    best = (P, K, w, coeffs)
            if best:
                break
        if best is None:
            print(f"  {label}: none up to P=4,K=6")
            continue
        P, K, w, coeffs = best
        print(f"  {label}: P={P}, K={K}  ->  {w:.2f} dB   "
              f"({P} programmable mult)")
        for p, c in coeffs.items():
            print(f"      C{p} ({'anti' if p % 2 else 'sym'}): "
                  f"{np.array2string(c, precision=5)}")
        for bits in (6, 8, 10):
            cq = quantize_coeffs(coeffs, bits)
            wq = worst_mse(cq, K, R, xv_by_beta)
            print(f"      subfilter coeffs quantized to {bits:2d} bit: "
                  f"{wq:7.2f} dB")
        # mu resolution
        print("      (mu register resolution check, 8-bit mu, worst case): "
              f"{worst_mse_mu_quant(best, R, xv_by_beta):7.2f} dB")
        print()


def worst_mse_mu_quant(best, R, xv_by_beta, bits=8):
    P, K, _, coeffs = best
    worst = -np.inf
    for beta, xv in xv_by_beta.items():
        for mu in np.linspace(-R, R, 13):
            muq = np.round(mu * 2 ** bits) / 2 ** bits   # 8-bit fractional
            y = farrow_apply(xv, coeffs, muq, K)
            worst = max(worst, mse_db(y, ideal_delay(xv, mu)))
    return worst


if __name__ == "__main__":
    main()
