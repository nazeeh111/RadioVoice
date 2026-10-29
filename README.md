# RadioVoice

![RadioVoice](docs/identity.svg)

GNU Radio flowgraphs for RF-modulated optical audio and recorded-signal demodulation.

## Run the offline AM example

No SDR, Qt, audio playback or recording is used. With Python 3.10 or later:

```sh
python3 -m venv .venv
.venv/bin/pip install -r requirements-offline.txt
.venv/bin/python offline_am.py --output result-997
.venv/bin/python offline_am.py --tone 1733 --output result-1733
```

Each new directory contains original complex64 little-endian IQ, recovered float32
samples, a 48 kHz WAV and `measurements.json` with parameters, SHA-256 digests and
an independent fit to the known source tone. Existing results are refused.
The input is 192 kHz AM IQ at a 24 kHz carrier offset and modulation index 0.5.
This demonstrates generated-signal DSP, not captured optical/RF performance.

For an actual GNU Radio production-core run, install GNU Radio 3.10 and use
`--backend gnuradio` with its Python interpreter. CI executes both tones through
GNU Radio blocks and separately checks the NumPy path against SciPy filtering.
No hardware driver is used by the offline example. [Verification](COMPATIBILITY.md).

## Choose a retained flowgraph

- **`laser_mf_demod.grc`** → `laser_mf_demod.py`: reads a live `osmosdr`
  source, translates and AM-demodulates the signal, and writes a unique `audio.wav` per run.
- **`laser_zmod.grc`** → `laser_zmod.py`: reads a live `osmosdr` source,
  translates it, takes a real-valued channel and sends it to an audio sink.
  This graph has no WAV writer.
- **`saleae_demod.grc`** → `saleae_demod.py`: reads a float sample file from
  `RADIOVOICE_INPUT`, then provides audio playback and
  a unique `audio.wav` output. The input file is not included here.
- **`usrp_laser_demod2.grc`** → `usrp_laser_demod2.py`: reads a live UHD/USRP
  source, translates and AM-demodulates it, then provides audio playback and
  a unique `audio.wav` output.

These are GNU Radio/Qt applications that may open hardware or audio playback.
Run them only with authorized signals and devices. Their DSP connections, filters,
gains and rates are retained. The recorded-file graph requires an explicit,
nonempty native float32 sample file through `RADIOVOICE_INPUT`; it is not the
complex IQ format from the offline example. The capture rate remains 781250 Hz.

Three enabled WAV writers allocate separate run directories and print their output
paths. Set `RADIOVOICE_OUTPUT_DIR` to an existing directory to choose their parent.
This prevents shared temporary-file collisions. Keep `radiovoice_paths.py` beside
both the generated Python and `.grc` source when regenerating or running. No
external captured-signal performance is established by these changes.

## Environment

The generated files target GNU Radio 3.10.10.0 and use Qt. Individual graphs also import SDR-specific modules such as `osmosdr`. Hardware sources need compatible devices and drivers; recorded-data sources need their expected input files. This repository does not bundle a runnable Python environment.

[Preservation and verification](COMPATIBILITY.md) records the offline checks and their limits.

## License

New repository presentation and documentation are under [MIT](LICENSE-MIT). The generated Python flowgraphs retain their existing [GPL-3.0 terms](LICENSE-GPL-3.0) and SPDX notices. GNU Radio and device modules retain their separate terms. [Source details](NOTICE.md).
