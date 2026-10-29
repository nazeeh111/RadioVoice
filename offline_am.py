#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0
"""Bounded offline AM experiment. Generates original IQ; never opens a device."""
import argparse
import hashlib
import json
from pathlib import Path
import time
import wave
import numpy as np

FS = 192000
DECIMATION = 4
CARRIER = 24000.0
MODULATION = 0.5


def lowpass_taps():
    n = np.arange(257) - 128
    taps = (2 * 5000 / FS) * np.sinc(2 * 5000 / FS * n) * np.hamming(len(n))
    return taps / taps.sum()


def demodulate(iq, backend='numpy'):
    iq = np.asarray(iq)
    if iq.ndim != 1 or not 1024 <= iq.size <= FS * 10 or not np.isfinite(iq).all():
        raise ValueError('IQ must be a finite 1D array of 1024 to 1920000 samples')
    taps = lowpass_taps()
    if backend == 'numpy':
        mixed = iq * np.exp(-2j * np.pi * CARRIER * np.arange(iq.size) / FS)
        channel = np.convolve(mixed, taps, mode='full')[:iq.size:DECIMATION]
        return (np.abs(channel) - 1) / MODULATION
    if backend != 'gnuradio':
        raise ValueError('unknown backend')
    from gnuradio import gr, blocks, filter
    graph = gr.top_block('RadioVoice offline AM')
    source = blocks.vector_source_c(iq.astype(np.complex64).tolist(), False)
    channel = filter.freq_xlating_fir_filter_ccf(DECIMATION, taps.tolist(), CARRIER, FS)
    envelope = blocks.complex_to_mag(1)
    dc = blocks.add_const_ff(-1.0)
    gain = blocks.multiply_const_ff(1 / MODULATION)
    sink = blocks.vector_sink_f()
    graph.connect(source, channel, envelope, dc, gain, sink)
    graph.run()
    return np.array(sink.data())


def evaluate(audio, tone):
    # Fit the known source frequency after FIR startup. Phase is reported, not hidden
    # by a lag search; GNU Radio and NumPy use different FIR history alignment.
    start = 1024
    if len(audio) <= start + 100:
        raise ValueError('experiment is too short for independent steady-state evaluation')
    t = np.arange(len(audio))[start:] / (FS / DECIMATION)
    design = np.column_stack((np.sin(2*np.pi*tone*t), np.cos(2*np.pi*tone*t), np.ones_like(t)))
    coeff, *_ = np.linalg.lstsq(design, audio[start:], rcond=None)
    error = audio[start:] - design @ coeff
    return {'amplitude': float(np.hypot(*coeff[:2])), 'dc': float(coeff[2]),
            'phase_rad': float(np.arctan2(coeff[1], coeff[0])),
            'residual_rms': float(np.sqrt(np.mean(error**2)))}


def experiment(destination, tone=997.0, duration=0.25, backend='numpy'):
    if not np.isfinite(tone) or not 100 <= tone <= 3000:
        raise ValueError('tone must be between 100 and 3000 Hz')
    if not np.isfinite(duration) or not 0.1 <= duration <= 10:
        raise ValueError('duration must be between 0.1 and 10 seconds')
    started = time.perf_counter()
    t = np.arange(round(FS * duration)) / FS
    message = np.sin(2*np.pi*tone*t)
    iq = ((1 + MODULATION * message) * np.exp(2j*np.pi*CARRIER*t)).astype('<c8')
    audio = demodulate(iq, backend)
    metrics = evaluate(audio, tone)
    # Independent known analytic message; after startup only amplitude and phase may
    # change through a linear FIR. A wrong carrier, decimation, or envelope fails.
    if abs(metrics['amplitude'] - 1) > 0.01 or metrics['residual_rms'] > 1e-4 or abs(metrics['dc']) > 1e-4:
        raise RuntimeError('demodulation failed independent tone reference: ' + str(metrics))
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    iq.tofile(destination / 'rf_iq.c64')
    audio.astype('<f4').tofile(destination / 'recovered.f32')
    with wave.open(str(destination / 'recovered.wav'), 'wb') as wav:
        wav.setparams((1, 2, FS // DECIMATION, 0, 'NONE', 'not compressed'))
        wav.writeframes((np.clip(audio, -1, 1) * 32767).astype('<i2').tobytes())
    result = {'evidence': 'original generated AM IQ, software DSP only', 'backend': backend,
              'rf_sample_rate_hz': FS, 'audio_sample_rate_hz': FS // DECIMATION,
              'carrier_offset_hz': CARRIER, 'modulation_index': MODULATION,
              'source_tone_hz': tone, 'duration_s': duration, 'samples': len(audio),
              'numpy_version': np.__version__, 'metrics': metrics,
              'elapsed_s': time.perf_counter() - started,
              'sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in destination.iterdir()}}
    (destination / 'measurements.json').write_text(json.dumps(result, indent=2) + '\n')
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='new directory; existing results are never overwritten')
    parser.add_argument('--tone', type=float, default=997)
    parser.add_argument('--duration', type=float, default=0.25)
    parser.add_argument('--backend', choices=['numpy', 'gnuradio'], default='numpy')
    args = parser.parse_args()
    print(json.dumps(experiment(args.output, args.tone, args.duration, args.backend), indent=2))


if __name__ == '__main__':
    main()
