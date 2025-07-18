# run_shuffle_pipeline.py Create video montage

## 1 Why run the shuffle pipeline?

Chains clip extraction, concatenation and cleanup to produce a ten-minute
highlight reel from the provided videos.

---

## 2 Inputs and options

Positional arguments are the source video files. No optional flags.

---

## 3 Example invocation

```bash
./run_shuffle_pipeline.py clip1.mkv clip2.mkv
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Montage produced** | 1 Run script with several clips.<br>2 Montage file appears on Desktop and log records steps. |
| **2** | **Missing input** | 1 Run without files.<br>2 Script exits and prints error. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
