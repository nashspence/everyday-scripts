# run_normalize_pipeline.py Audio normalisation flow

## 1 Why run this pipeline?

Wraps the two-pass loudnorm process in a single command. Produces a normalised
copy of the input and logs the steps taken.

---

## 2 Inputs and options

`-i`/`--lufs` target integrated loudness.
`-t`/`--tp` target true peak.
Positional `input` and optional `output` file paths.

---

## 3 Example invocation

```bash
./run_normalize_pipeline.py input.wav
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Default targets** | 1 Run with only input.<br>2 Output file with `_R128` suffix created. |
| **2** | **Custom targets** | 1 Specify `-i` and `-t` values.<br>2 Resulting file matches requested loudness. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
