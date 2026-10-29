# SPDX-License-Identifier: GPL-3.0
"""Portable paths shared by the retained GRC and generated Python graphs."""
import os
from pathlib import Path
import tempfile


def output_file(graph):
    """Allocate an exclusive run directory; a graph never replaces another WAV."""
    if graph not in {'laser_mf_demod', 'laser_zmod', 'saleae_demod', 'usrp_laser_demod2'}:
        raise ValueError('unknown RadioVoice flowgraph')
    root = os.environ.get('RADIOVOICE_OUTPUT_DIR')
    if root is not None and not Path(root).is_dir():
        raise ValueError('RADIOVOICE_OUTPUT_DIR must be an existing directory')
    result = str(Path(tempfile.mkdtemp(prefix=graph + '-', dir=root)) / 'audio.wav')
    print('RadioVoice WAV output:', result, flush=True)
    return result


def input_file():
    """The legacy Saleae graph expects native float32 samples, never IQ pairs."""
    value = os.environ.get('RADIOVOICE_INPUT')
    if not value:
        raise ValueError('Set RADIOVOICE_INPUT to an authorized float32 sample file')
    path = Path(value).expanduser().resolve(strict=True)
    if not path.is_file() or path.stat().st_size == 0 or path.stat().st_size % 4:
        raise ValueError('RADIOVOICE_INPUT must be a nonempty float32 sample file (4-byte alignment)')
    return str(path)
