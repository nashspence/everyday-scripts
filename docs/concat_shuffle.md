# concat_shuffle.py Join shuffle clips

## 1 Why concatenate clips?

Takes the list produced by `make_shuffle_clips.py` and stream-copies each clip
into a single montage file. This step is lossless and quick.

---

## 2 Inputs and options

`--clip-list` path to the ffmpeg concat list.
`--out-file` name of the final montage.
`--logfile` log destination.

---

## 3 Example invocation

```bash
./concat_shuffle.py --logfile log.txt --clip-list clip_list.txt \
  --out-file montage.mkv
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Montage created**<br>List references existing clips. | 1 Run script.<br>2 Output file written and log reports success. |
| **2** | **Bad list** | 1 List references missing clip.<br>2 FFmpeg fails and script exits non-zero. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
