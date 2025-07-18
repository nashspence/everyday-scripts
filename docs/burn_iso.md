# **burn\_iso.py — Burn a Blu‑ray ISO**

## 1 Purpose

Write a prepared `.iso` image to blank Blu‑ray media **and (optionally) confirm byte‑perfect integrity**.
Typical use‑case: the final stage of the body‑cam archiving pipeline where a cold‑storage disc is required.

---

## 2 Prerequisites

| Item                              | Why it matters                                                                       |
| --------------------------------- | ------------------------------------------------------------------------------------ |
| **Blu‑ray writer** (BD‑R / BD‑RE) | Physical drive that supports 25 GB+ discs.                                           |
| **Blank disc**                    | ISO → disc must fit entirely.                                                        |
| **ISO path**                      | Absolute/relative path to the image you intend to burn.                              |
| Python ≥ 3.8                      | Script runtime.                                                                      |
| OS utilities                      | *macOS*: `hdiutil` • *Linux*: `growisofs` + `readom` • *Windows/WSL*: same as Linux. |

> The script autodetects your platform and aborts early if required tools are missing.

---

## 3 CLI options

| Flag                       | Required | Example                  | Notes                                                              |
| -------------------------- | :------: | ------------------------ | ------------------------------------------------------------------ |
| `--iso-path PATH`          |     ✅    | `--iso-path footage.iso` | Path to the source image.                                          |
| `--verify / --skip-verify` |     ☐    | `--skip-verify`          | Verification **on by default**. Disable to save time.              |
| `--logfile FILE`           |     ☐    | `--logfile burn.log`     | Redirect console output to `FILE` **and** keep a copy on `stdout`. |
| `--device DEV`             |     ☐    | `--device /dev/sr0`      | Override auto‑detected burner (Linux/WSL only).                    |
| `--speed X`                |     ☐    | `--speed 4`              | Limit write speed; lower = safer.                                  |
| `--dry-run`                |     ☐    | (no args)                | Parse arguments & show the command that *would* run, then exit 0.  |

---

## 4 Workflow (internal overview)

1. **Input validation** — confirm ISO exists and is readable.
2. **Drive discovery** — pick first optical drive unless `--device` overrides.
3. **Disc‑present check** —

   * If the drive tray is empty the script logs
     *“💿  No disc detected in `<DEV>`. Please insert a blank BD‑R/RE… (press Ctrl‑C to cancel)”*
     and polls every 3 s until a disc appears. No timeout.
4. **Pre‑flight checks** — verify disc is blank and capacity ≥ ISO size.
5. **Burn** —

   * macOS → `hdiutil burn …`
   * Linux/WSL → `growisofs -dvd-compat -speed=X -Z DEV=ISO`
6. **(Optional) Verification** — skipped when `--skip-verify` supplied. Otherwise read disc back (`hdiutil verify` | `readom --verify`) and compare SHA‑256 to the original.
7. **Log summary** — success or first encountered failure.

The script exits **0** only when every executed stage succeeds.

---

## 5 Quick‑start

```bash
# Minimal (burn + verify)
./burn_iso.py --iso-path footage.iso

# No verification, verbose log, 4× speed, explicit drive
./burn_iso.py --iso-path footage.iso --skip-verify --logfile burn.log --speed 4 --device /dev/sr0
```

---

## 6 Acceptance criteria (platform‑agnostic)

| #      | Scenario & pre‑conditions                                       | Steps (user → expected result)                                                                                       |
| ------ | --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **1**  | **Successful burn + verify** — ISO exists; blank disc inserted. | 1 Run script with default args → wait if needed → burn completes; SHA‑256 matches; exit 0; log contains **SUCCESS**. |
| **2**  | **Drive present, no disc**                                      | 1 Run script with tray empty → friendly “No disc” message appears; insert blank disc → burn proceeds automatically.  |
| **3**  | **Skip verification**                                           | 1 Run with `--skip-verify` → burn completes; SHA not computed; exit 0; log notes “Verification skipped”.             |
| **4**  | **Missing ISO**                                                 | 1 Give non‑existent path → script aborts before waiting for disc; exit 1; log “File not found”.                      |
| **5**  | **Disc already written**                                        | 1 Insert used disc; run burn → script aborts before writing; exit 1; log “medium not blank”.                         |
| **6**  | **No optical drive**                                            | 1 Run on machine without BD writer → aborts; exit 1; log “No drive detected”.                                        |
| **7**  | **Verify mismatch** (flip one byte after burn)                  | 1 Run default → verification fails; exit 2; log “Checksum mismatch”.                                                 |
| **8**  | **Permission denied for logfile**                               | 1 Point `--logfile` to unwritable location → meaningful error; exit 1; no burn starts.                               |
| **9**  | **Linux path override**                                         | 1 Specify `--device /dev/sr1` with disc → script uses that drive successfully.                                       |
| **10** | **Dry‑run safety**                                              | 1 Run with `--dry-run` → no hardware interaction; exit 0; printed command matches selected options.                  |
| **11** | **macOS utility absence**                                       | 1 Rename `hdiutil`; run script → aborts; exit 1; message instructs to restore tool.                                  |
| **12** | **Windows WSL**                                                 | 1 Run inside WSL with `/dev/sr0` accessible → scenarios 1 & 3 pass identically to Linux.                             |

All twelve scenarios **must pass unmodified** on Linux, macOS, and Windows (WSL).
If any step fails, the script must **leave the disc untouched** or clearly indicate failure.

---

**End of specification**
