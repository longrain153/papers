#!/usr/bin/env python3
"""
Skew pre-compensation algorithm search for 236 GBaud PAM4 @ 236*1.125 GSa/s.

Goal: compensate (pre-delay) a fixed skew of 0.35 ps with MSE < -25 dB
relative to ideal compensation (long-FIR / exact spectral delay), at the
lowest implementation complexity (real multipliers per output sample).

Method
------
1. Generate a PAM4 signal at 1.125 samples/symbol (rate 9/8):
   upsample symbols x9 -> RRC shaping (freq domain) -> decimate x8.
2. Ideal reference: exact fractional delay applied as a spectral phase ramp
   exp(-j*2*pi*f*tau) (equivalent to an infinitely long sinc FIR).
3. Candidate low-complexity compensators, all evaluated as
   MSE = mean|y - y_ideal|^2 / mean|y_ideal|^2 (dB):
     - 2-tap linear interpolation
     - 3-tap parabolic (Lagrange) interpolation
     - 4-tap cubic Lagrange interpolation
     - N-tap least-squares FIR (signal-spectrum-weighted, N = 2..7)
     - N-tap windowed-sinc FIR
     - 1st-order Thiran all-pass IIR (for reference; IIR is impractical at
       265.5 GSa/s parallel hardware)
4. Coefficient quantization sweep for the winning design.
5. Robustness: MSE vs. actual skew value and vs. RRC roll-off.
"""

import numpy as np

rng = np.random.default_rng(20260802)

# ----------------------------------------------------------------------
# System parameters
# ----------------------------------------------------------------------
RS = 236e9                    # baud rate
OSR_NUM, OSR_DEN = 9, 8       # 1.125 = 9/8 samples per symbol
FS = RS * OSR_NUM / OSR_DEN   # 265.5 GSa/s
TS = 1.0 / FS                 # 3.7665 ps
TAU = 0.35e-12                # skew to pre-compensate
MU = TAU / TS                 # fractional delay in samples

NSYM = 1 << 16                # symbols per run


def gen_pam4(beta, nsym=NSYM, seed=None):
    """PAM4 @ 9/8 samples/symbol, RRC roll-off beta (must be <= 0.125)."""
    r = np.random.default_rng(seed) if seed is not None else rng
    syms = r.choice([-3.0, -1.0, 1.0, 3.0], nsym)
    n_hi = nsym * OSR_NUM                      # rate 9*RS
    up = np.zeros(n_hi)
    up[::OSR_NUM] = syms
    f = np.fft.fftfreq(n_hi, d=1.0 / (OSR_NUM * RS))
    up_f = np.fft.fft(up) * rrc_freq(f, RS, beta)
    x_hi = np.fft.ifft(up_f).real
    return x_hi[::OSR_DEN]                     # rate 9/8*RS = FS


def rrc_freq(f, rs, beta):
    """Root-raised-cosine frequency response."""
    af = np.abs(f)
    f1 = (1 - beta) * rs / 2
    f2 = (1 + beta) * rs / 2
    h = np.zeros_like(af)
    h[af <= f1] = 1.0
    tb = (af > f1) & (af < f2)
    if beta > 0:
        h[tb] = np.sqrt(0.5 * (1 + np.cos(np.pi / (beta * rs) * (af[tb] - f1))))
    return h


def ideal_delay(x, delay_samp):
    """Exact (spectral) fractional delay; the 'ideal long-FIR' reference."""
    n = len(x)
    f = np.fft.fftfreq(n)
    y = np.fft.ifft(np.fft.fft(x) * np.exp(-2j * np.pi * f * delay_samp))
    return y.real


def fir_apply(x, h, center):
    """Circular FIR with integer group-delay 'center' removed."""
    y = np.zeros_like(x)
    for k, hk in enumerate(h):
        y += hk * np.roll(x, k - center)
    return y


def mse_db(y, ref):
    return 10 * np.log10(np.mean((y - ref) ** 2) / np.mean(ref ** 2))


# ----------------------------------------------------------------------
# Candidate designs
# ----------------------------------------------------------------------
def taps_linear(mu):
    return np.array([1 - mu, mu]), 0          # h[0]=x[n], h[1]=x[n-1]


def taps_lagrange(mu, n_taps):
    """Lagrange interpolator of length n_taps, delay = center + mu."""
    center = (n_taps - 1) // 2
    d = center + mu
    k = np.arange(n_taps)
    h = np.ones(n_taps)
    for i in range(n_taps):
        for j in range(n_taps):
            if j != i:
                h[i] *= (d - j) / (i - j)
    return h, center


def taps_sinc_win(mu, n_taps):
    center = (n_taps - 1) // 2
    k = np.arange(n_taps)
    h = np.sinc(k - center - mu) * np.hamming(n_taps)
    return h / np.sum(h), center


def taps_ls(x, y_ref, n_taps):
    """Least-squares FIR on the actual signal (auto PSD-weighted)."""
    center = (n_taps - 1) // 2
    cols = [np.roll(x, k - center) for k in range(n_taps)]
    A = np.stack(cols, axis=1)
    h, *_ = np.linalg.lstsq(A, y_ref, rcond=None)
    return h, center


def thiran_ap1(x, mu):
    """1st-order Thiran all-pass, total delay mu (reference only)."""
    a = (1 - mu) / (1 + mu)
    from scipy.signal import lfilter
    return lfilter([a, 1.0], [1.0, a], x)


def quantize(h, bits):
    scale = 2.0 ** (bits - 1)
    m = np.max(np.abs(h))
    step = np.ceil(m) / scale   # keep a power-of-two-friendly full scale
    return np.round(h / step) * step


# ----------------------------------------------------------------------
# Main evaluation
# ----------------------------------------------------------------------
def main():
    print(f"Fs = {FS/1e9:.1f} GSa/s, Ts = {TS*1e12:.4f} ps, "
          f"tau = {TAU*1e12} ps -> mu = {MU:.6f} samples\n")

    for beta in (0.05, 0.10, 0.125):
        x = gen_pam4(beta, seed=1234)
        y_ref = ideal_delay(x, MU)
        print(f"===== RRC roll-off beta = {beta} "
              f"(band edge {(1+beta)*RS/2/1e9:.1f} GHz, "
              f"Nyquist {FS/2/1e9:.2f} GHz) =====")

        h, c = taps_linear(MU)
        print(f"  2-tap linear interp        : "
              f"{mse_db(fir_apply(x, h, c), y_ref):7.2f} dB   (2 mult)")

        for n in (3, 4):
            h, c = taps_lagrange(MU, n)
            print(f"  {n}-tap Lagrange            : "
                  f"{mse_db(fir_apply(x, h, c), y_ref):7.2f} dB   ({n} mult)")

        for n in (3, 5, 7):
            h, c = taps_sinc_win(MU, n)
            print(f"  {n}-tap windowed sinc       : "
                  f"{mse_db(fir_apply(x, h, c), y_ref):7.2f} dB   ({n} mult)")

        ls_taps = {}
        for n in range(2, 8):
            h, c = taps_ls(x, y_ref, n)
            ls_taps[n] = (h, c)
            # validate on an independent realization
            xv = gen_pam4(beta, seed=999)
            yv = ideal_delay(xv, MU)
            print(f"  {n}-tap LS FIR              : "
                  f"{mse_db(fir_apply(xv, h, c), yv):7.2f} dB   ({n} mult)")

        y = thiran_ap1(x, MU)
        # discard IIR transient
        s = slice(64, None)
        m = 10 * np.log10(np.mean((y[s] - y_ref[s]) ** 2)
                          / np.mean(y_ref[s] ** 2))
        print(f"  Thiran AP1 (IIR, ref only) : {m:7.2f} dB   (1 mult, IIR)")
        print()

        if beta == 0.10:
            # ---- winner detail: smallest LS FIR meeting -25 dB ----
            xv = gen_pam4(beta, seed=999)
            yv = ideal_delay(xv, MU)
            for n in range(2, 8):
                h, c = ls_taps[n]
                if mse_db(fir_apply(xv, h, c), yv) < -25:
                    break
            print(f"  --> smallest LS FIR meeting -25 dB @ beta=0.1: "
                  f"{n} taps")
            print(f"      taps = {np.array2string(h, precision=6)}")
            print(f"      (integer group delay = {c} samples)\n")

            print("  Coefficient quantization of the winner:")
            for bits in (6, 8, 10, 12):
                hq = quantize(h, bits)
                print(f"    {bits:2d}-bit taps: "
                      f"{mse_db(fir_apply(xv, hq, c), yv):7.2f} dB")
            print()

            # also quantize the next size up for margin comparison
            h5, c5 = ls_taps[min(n + 2, 7)]
            print(f"  {len(h5)}-tap LS quantized (margin option):")
            for bits in (6, 8, 10):
                hq = quantize(h5, bits)
                print(f"    {bits:2d}-bit taps: "
                      f"{mse_db(fir_apply(xv, hq, c5), yv):7.2f} dB")
            print()

            # ---- robustness: MSE vs actual skew for fixed designs ----
            print("  Robustness (beta=0.1): MSE vs skew for LS designs "
                  "(designed at 0.35 ps):")
            print("    skew(ps) " + "".join(f"  {n}-tap " for n in (2, 3, 4, 5)))
            for tau_ps in (0.1, 0.2, 0.35, 0.5, 0.7, 1.0, 1.88):
                mu2 = tau_ps * 1e-12 / TS
                row = f"    {tau_ps:7.2f} "
                for n in (2, 3, 4, 5):
                    h, c = taps_ls(x, ideal_delay(x, mu2), n)
                    row += f"{mse_db(fir_apply(xv, h, c), ideal_delay(xv, mu2)):7.2f} "
                print(row + "  (re-designed per skew)")
            print()


if __name__ == "__main__":
    main()
