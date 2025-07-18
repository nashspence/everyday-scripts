# open_console.zsh Tail logs in Terminal

## 1 Why open a console?

Opens macOS Terminal and starts `tail -f` on the given logfile so the user can
watch pipeline output in real time.

---

## 2 Inputs and options

Single argument: path to the logfile.

---

## 3 Example invocation

```bash
./scripts/open_console/open_console.zsh ~/logs/pipeline.log
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Window opens** | 1 Run script with writable log path.<br>2 Terminal launches and tails the file. |
| **2** | **Bad path** | 1 Pass unwritable path.<br>2 Script prints error and exits non-zero. |

All scenarios must pass when invoked via Docker on any host OS without altering this spec.

---

**End of specification**
