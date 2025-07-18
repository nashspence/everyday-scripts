# check.sh Run project checks

## 1 Why run check.sh?

Executes formatting, linting and tests in one step. Used locally and by CI to
ensure all scripts compile and follow style guidelines.

---

## 2 Inputs and options

No arguments. Activates `venv/bin/activate` if present before running tools.

---

## 3 Example invocation

```bash
./check.sh
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **Clean repo** | 1 Run script.<br>2 black, ruff, mypy and pytest all succeed. |
| **2** | **Failing test** | 1 Introduce an error.<br>2 Script exits non-zero and reports failure. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
