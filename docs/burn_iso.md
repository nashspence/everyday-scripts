# burn_iso.py Burn a Blu-ray ISO

## 1 Why burn an ISO?

Writes the prepared disc image to optical media and verifies the result. Used at
the end of the bodycam pipeline.

---

## 2 Inputs and options

`--iso-path` path to the `.iso` file.
`--logfile` file receiving progress output.

---

## 3 Example invocation

```bash
./burn_iso.py --logfile burn.log --iso-path footage.iso
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Successful burn**<br>Valid ISO present in drive. | 1 Run script with correct path.<br>2 hdiutil burns and verifies disc, logging success. |
| **2** | **Missing ISO** | 1 Provide nonexistent path.<br>2 Script fails and logs error. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
