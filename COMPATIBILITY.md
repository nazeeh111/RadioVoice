# RadioVoice preservation record

## Change boundary

The repository presentation, documentation entry points and source comments were updated. Existing executable entry points, algorithms, defaults, filenames, formats and numerical operations remain unchanged. First-party presentation changes are MIT; generated-source GPL notices and separate dependency terms remain. Flowgraph author fields are presentation metadata.

## Verified locally

GNU Radio, Qt, SDR drivers and optical/radio hardware were not available for end-to-end execution. No flowgraph was started. The four Python files passed parsing and their executable syntax trees match the baseline exactly; all four companion flowgraphs preserve every operational field; only author metadata differs.

The source comparison checks Python syntax trees without comments or source locations, so changes in documentation do not obscure computational changes. This is an equivalence check against the supplied source, not a claim that every experiment is correct or portable. Existing invalid-escape warnings in legacy Python strings also occur in the baseline and were not changed.

## Execution boundary

No RF transmission, signal acquisition, connected-device commands, firmware changes or live-target experiments were performed. No external experimental datasets were downloaded. Build and reproduction requirements remain those documented by the source; absent dependencies have not been silently replaced with new algorithms.
