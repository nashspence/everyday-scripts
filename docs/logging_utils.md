# logging_utils.py Shared logging helpers

## 1 Why provide logging utilities?

Centralises logger setup so all scripts emit timestamps and messages in the same
format. Also amends `PATH` for bundled FFmpeg binaries.

---

## 2 Functions

`setup_logging(logfile, name=None)` writes to both the logfile and stderr.
`prepend_path()` adds common binary paths to `PATH`.

---

## 3 Example usage

```python
from logging_utils import setup_logging, prepend_path
logger = setup_logging("tool.log")
prepend_path()
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Logger writes** | 1 Call `setup_logging` with a path.<br>2 File and stderr both receive formatted messages. |
| **2** | **PATH updated** | 1 Call `prepend_path`.<br>2 `ffmpeg` binaries in `/usr/local/bin` become discoverable. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
