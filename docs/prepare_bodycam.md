# prepare_bodycam.py Prepare footage for disc

## 1 Why prepare bodycam footage?

Copies or recompresses camera files into a working directory so the final image
fits on a single Blu-ray. Chooses AV1 settings based on total duration.

---

## 2 Inputs and options

`--build-dir` directory for processed clips.
`--logfile` output log.
Positional arguments are the source files.

---

## 3 Example invocation

```bash
./prepare_bodycam.py --logfile log.txt --build-dir work *.mp4
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Copy mode**<br>Total size fits on disc. | 1 Run script.<br>2 Files copied to build dir without re-encoding. |
| **2** | **Re-encode mode** | 1 Input too large.<br>2 Script re-encodes each file and logs bitrate used. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
