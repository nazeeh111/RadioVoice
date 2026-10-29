# SPDX-License-Identifier: GPL-3.0
import ast
import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
import offline_am
from radiovoice_paths import input_file, output_file


class OfflineTests(unittest.TestCase):
    def test_changed_tone_and_reference(self):
        with tempfile.TemporaryDirectory() as temp:
            hashes = []
            for frequency in (997, 1733):
                result = offline_am.experiment(Path(temp) / str(frequency), frequency)
                self.assertAlmostEqual(result['metrics']['amplitude'], 1, delta=.01)
                self.assertLess(result['metrics']['residual_rms'], 1e-4)
                hashes.append(result['sha256']['recovered.f32'])
            self.assertNotEqual(*hashes)
            with self.assertRaises(FileExistsError):
                offline_am.experiment(Path(temp) / '997')

    def test_fir_against_independent_scipy_lfilter(self):
        from scipy.signal import lfilter
        rng = np.random.default_rng(17)
        iq = rng.normal(size=4096) + 1j*rng.normal(size=4096)
        mixed = iq * np.exp(-2j*np.pi*offline_am.CARRIER*np.arange(len(iq))/offline_am.FS)
        ref = (abs(lfilter(offline_am.lowpass_taps(), [1], mixed)[::4])-1)/.5
        np.testing.assert_allclose(offline_am.demodulate(iq), ref, atol=2e-14, rtol=2e-14)

    def test_input_limits(self):
        for iq in (np.ones(10), np.ones((1024, 1)), np.full(1024, np.nan)):
            with self.assertRaises(ValueError): offline_am.demodulate(iq)
        with self.assertRaises(ValueError): offline_am.demodulate(np.ones(1024), 'invalid')
        for tone, duration in ((float('nan'), .25), (4000, .25), (997, .001), (997, float('inf'))):
            with self.assertRaises(ValueError): offline_am.experiment('unused', tone, duration)

    def test_safe_legacy_paths(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'RADIOVOICE_OUTPUT_DIR': temp}, clear=True):
            first = Path(output_file('saleae_demod')); second = Path(output_file('saleae_demod'))
            self.assertNotEqual(first, second)
            first.write_bytes(b'preserve')
            self.assertEqual(first.read_bytes(), b'preserve')
            with self.assertRaises(ValueError): input_file()
            source = Path(temp) / 'samples.f32'; source.write_bytes(np.ones(10, dtype='<f4').tobytes())
            os.environ['RADIOVOICE_INPUT'] = str(source)
            self.assertEqual(input_file(), str(source.resolve()))
            source.write_bytes(b'bad')
            with self.assertRaises(ValueError): input_file()

    def test_grc_and_python_paths_agree(self):
        import yaml
        for name in ('laser_mf_demod', 'saleae_demod', 'usrp_laser_demod2', 'laser_zmod'):
            source = Path(name + '.py').read_text(); graph = yaml.safe_load(Path(name + '.grc').read_text())
            ast.parse(source)
            self.assertNotIn('/tmp/sdr.wav', source)
            self.assertNotIn('/Users/samy/', source)
            fields = {b['name']: b for b in graph['blocks']}
            self.assertEqual(fields['radiovoice_imports']['parameters']['imports'], 'from radiovoice_paths import output_file, input_file')
            self.assertEqual(fields['blocks_wavfile_sink_0']['parameters']['file'], 'output_path')
            if name == 'saleae_demod':
                self.assertEqual(fields['blocks_file_source_0']['parameters']['file'], 'input_path')
                self.assertIn('input_path = input_file()', source)

    @unittest.skipUnless(importlib.util.find_spec('gnuradio'), 'GNU Radio not installed; explicit separate gate')
    def test_gnuradio_actual_core(self):
        for tone in (997, 1733):
            with tempfile.TemporaryDirectory() as temp:
                result = offline_am.experiment(Path(temp)/'run', tone, backend='gnuradio')
                self.assertLess(result['metrics']['residual_rms'], 1e-4)


if __name__ == '__main__': unittest.main()
