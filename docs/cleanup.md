# cleanup.py Remove build artefacts

## 1 Why cleanup?

Deletes the temporary working directory created during pipeline runs. Keeps the
system tidy and frees disk space.

---

## 2 Inputs and options

`--build-dir` path to the directory to delete.
`--logfile` file that records the action.

---

## 3 Example invocation

```bash
./cleanup.py --logfile run.log --build-dir /tmp/bodycam_123
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Directory removed**<br>Path exists. | 1 Run script.<br>2 Directory is deleted and log notes removal. |
| **2** | **Nothing to remove** | 1 Run script on missing path.<br>2 Warning logged but exit 0. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
