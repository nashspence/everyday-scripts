# make_shuffle_clips.py Extract random segments

## 1 Why make shuffle clips?

Chooses short segments from multiple videos so that the total length equals ten
minutes. Ensures cuts land on key frames to allow lossless concatenation.

---

## 2 Inputs and options

`--tmp-dir` directory for output clips and list.
`--logfile` records progress messages.
Positional arguments are the source video files.

---

## 3 Example invocation

```bash
./make_shuffle_clips.py --logfile log.txt --tmp-dir /tmp/shuf video1.mp4 video2.mp4
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Clip list produced** | 1 Run with valid inputs.<br>2 `clip_list.txt` and numbered clips appear in tmp dir. |
| **2** | **Insufficient space** | 1 Provide unwritable tmp dir.<br>2 Script exits with error. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
