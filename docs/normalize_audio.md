# normalize_audio.py Apply loudness correction

## 1 Why normalise audio?

Uses metrics gathered by `analyse_loudness.py` to produce an audio track that
meets broadcast loudness targets while preserving sync with video.

---

## 2 Inputs and options

`--in-file` source media.
`--out-file` destination path.
`--analysis-json` metrics from pass one.
`--target-i` desired LUFS (default -16).
`--target-tp` desired true peak (default -1.5).
`--logfile` log location.

---

## 3 Example invocation

```bash
./normalize_audio.py --logfile log.txt --in-file a.mov --out-file a_R128.mov \
  --analysis-json metrics.json
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **File normalised** | 1 Run with valid inputs.<br>2 Output file plays back at target loudness. |
| **2** | **Missing metrics** | 1 Omit `--analysis-json`.<br>2 Script errors and exits non-zero. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
