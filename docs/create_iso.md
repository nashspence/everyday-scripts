# **create\_iso.py — Build a Blu‑ray‑ready ISO**

---

## 1 Purpose
Package a **prepared build directory** (video masters, project assets, etc.) into a single **UDF + ISO‑9660 hybrid image** you can burn to BD‑R/RE or archive as a file.
Unless you say otherwise, the script stamps the ISO with the **current UTC timestamp** in ISO 8601 form (`YYYYMMDDThhmmssZ`) so every disc is self‑identifying and sortable.

---

## 2 Prerequisites

| Item                                                 | Why it matters                                                                                                           |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| **Build directory** (the files you want on the disc) | Source content.                                                                                                          |
| **Python ≥ 3.8**                                     | Script runtime.                                                                                                          |
| **Imaging utility**                                  | *macOS* → `hdiutil` (built‑in) • *Linux/WSL* → `xorriso` **or** `genisoimage` + `udftools` • *Windows* → run under WSL2. |
| ≥ 10 GB free space                                   | Working room for temp files + final ISO.                                                                                 |

If any required tool is missing, the script aborts early with a clear error.

---

## 3 Command‑line options

| Flag                  | Required | Example                       | Notes                                                                                      |
| --------------------- | :------: | ----------------------------- | ------------------------------------------------------------------------------------------ |
| `--build-dir DIR`     |     ✅    | `--build-dir build/`          | Directory is **recursively** archived.                                                     |
| `--iso-path PATH`     |     ✅    | `--iso-path out/project.iso`  | Parent folders auto‑created when possible.                                                 |
| `--logfile FILE`      |     ✅    | `--logfile create.log`        | All output echoed to *stderr* and `FILE`.                                                  |
| `--volume-label TEXT` |     ⃟    | `--volume-label “MASTER_001”` | Overrides the default timestamp label. **Constraints:** ≤ 32 chars; A‑Z a‑z 0‑9 \_ ‑ only. |
| `--force`             |     ⃟    | `--force`                     | Overwrite an existing ISO instead of aborting.                                             |

> *If `--volume-label` is omitted, the script uses the timestamp captured at start‑up.*

---

## 4 Workflow (high‑level)

1. **Validate inputs** — build dir exists & readable; iso path parent writable; `--volume-label` (if given) meets length/charset rules.
2. **Pick backend** — `hdiutil` on macOS, otherwise `xorriso` or the genisoimage + mkudffs pair.
3. **Create image** — hybrid UDF + ISO‑9660, volume label set to either the supplied string or the auto timestamp.
4. **Post‑build check** — ensure image exists and is > 0 bytes.
5. **Log & exit** — exit 0 on success; first failure returns non‑zero.

---

## 5 Quick‑start recipes

```bash
# 1. Timestamp‑labelled ISO (no custom label)
./scripts/create_iso/create_iso.py \
  --build-dir build/ \
  --iso-path out/footage.iso \
  --logfile create.log

# 2. Custom‑label ISO
./scripts/create_iso/create_iso.py \
  --build-dir build/ \
  --iso-path out/backup.iso \
  --volume-label MASTER_001 \
  --logfile create.log
```

The first command might generate a volume label like `20250718T194610Z`.

---

## 6 Acceptance criteria

| #      | Scenario & pre‑conditions        | Steps (user → expected result)                                                            |
| ------ | -------------------------------- | ----------------------------------------------------------------------------------------- |
| **1**  | **Happy path (timestamp label)** | Run script → ISO created, volume label matches start‑time UTC (±5 s), exit 0.             |
| **2**  | **Happy path (custom label)**    | Run with `--volume-label TESTDISC` → ISO created, volume label **TESTDISC**, exit 0.      |
| **3**  | **Invalid label (too long)**     | Run with label > 32 chars → abort; “Label too long”; exit 1.                              |
| **4**  | **Invalid label (bad chars)**    | Run with spaces or `!` → abort; “Label contains illegal characters”; exit 1.              |
| **5**  | **Non‑existent build dir**       | Bad `--build-dir` → abort; “Directory not found”; exit 1.                                 |
| **6**  | **Empty build dir**              | Empty folder → abort; “No input files”; exit 1.                                           |
| **7**  | **Unwritable iso path**          | Path without permission → abort; no partial file; exit 1.                                 |
| **8**  | **ISO exists, no --force**       | Second run → abort; “File exists”; exit 1.                                                |
| **9**  | **ISO exists, with --force**     | Second run with `--force` → file overwritten; exit 0.                                     |
| **10** | **Logfile unwritable**           | Read‑only logfile dir → abort; “Cannot write logfile”; exit 1.                            |
| **11** | **Toolchain missing**            | Rename `xorriso`/`hdiutil`; run → abort; “Required tool not found”; exit 1.               |
| **12** | **Large tree** (> 50 k files)    | Build completes within 2 × a plain copy; exit 0.                                          |
| **13** | **Cross‑platform parity**        | Scenario 1 passes on macOS (Intel & Apple Silicon), Ubuntu 22, CentOS 9, Windows 11 WSL2. |

All thirteen scenarios **must pass unmodified**; any failure must leave existing data untouched **and** exit with a non‑zero status.

---

**End of specification**
