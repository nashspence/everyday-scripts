# create_iso.py Build a disc image

## 1 Why create an ISO?

Turns the prepared directory into a UDF/ISO hybrid file suitable for Blu-ray
burning. Encodes metadata such as the timestamp into the volume name.

---

## 2 Inputs and options

`--build-dir` directory of video files.
`--iso-path` output path for the `.iso`.
`--iso-ts` timestamp string used as the volume name.
`--logfile` write progress here.

---

## 3 Example invocation

```bash
./create_iso.py --logfile log.txt --build-dir work --iso-path out.iso \
  --iso-ts 20250101T120000Z
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **ISO created**<br>Build dir exists. | 1 Run script.<br>2 File `out.iso` appears and log notes success. |
| **2** | **Invalid dir** | 1 Pass nonexistent build dir.<br>2 Script exits with error. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
