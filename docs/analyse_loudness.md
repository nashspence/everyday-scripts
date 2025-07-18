# analyse_loudness.py Measure audio loudness

## 1 Why analyse loudness?

Runs the first FFmpeg loudnorm pass to gather metrics used in later normalisation.
The script records values in a JSON file for the second pass.

---

## 2 Inputs and options

`--in-file` path to the source media.
`--target-i` integrated LUFS target (default -16).
`--target-tp` true peak target (default -1.5).
`--out-json` destination for metrics.
`--logfile` where progress is logged.

---

## 3 Example invocation

```bash
./analyse_loudness.py --logfile log.txt --in-file clip.mov \
  --out-json metrics.json
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Metrics saved**<br>Input media exists. | 1 Run script with valid arguments.<br>2 `metrics.json` contains loudnorm JSON. |
| **2** | **Missing input** | 1 Specify nonexistent file.<br>2 Script exits non-zero with an error logged. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
