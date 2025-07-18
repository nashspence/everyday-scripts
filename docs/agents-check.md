# agents-check.sh CI helper script

## 1 Why run agents-check?

Installs linters and test tools before executing `check.sh`. Useful in clean
containers to mirror CI behaviour.

---

## 2 Inputs and options

No arguments. Requires an internet connection to fetch Python packages.

---

## 3 Example invocation

```bash
./agents-check.sh
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **All checks pass**<br>Required tools install successfully. | 1 Run script -> dependencies install.<br>2 `check.sh` completes with exit 0. |
| **2** | **Checks fail** | 1 Introduce a failing test.<br>2 Run script -> `check.sh` exits non-zero and prints errors. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
