# **run\_bodycam\_pipeline.py — One‑click body‑cam archive**

## 1  Purpose

End‑to‑end **automation**: drop your raw `.mp4` clips on the command‑line and walk away. The script:

1. **Pre‑processes** footage so everything fits a single 25 GB BD‑R (delegates to `prepare_bodycam.py`).
2. **Masters** a UDF/ISO‑9660 image (`create_iso.py`).
3. **Burns & verifies** the disc (`burn_iso.py`).
4. **Cleans up** all temp artefacts (via the `cleanup` helper).

A single, timestamped log captures every sub‑step.

---

## 2  Before you start

| Requirement                                | Notes                                                                                                                                         |
| ------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Python ≥ 3.8**                           | Same version used by all sub‑scripts.                                                                                                         |
| **Platform utilities**                     | Whatever each sub‑script needs (see their docs).                                                                                              |
| **Mounted workspace drive**                | By default the script writes to `"/Volumes/Sabrent Rocket XTRM‑Q 2TB"`; edit the `ROOT` constant at the top of the file if your path differs. |
| **Writable optical drive + blank BD‑R/RE** | Needed only when `burn_iso.py` runs (stage 3).                                                                                                |
| **Free disk space ≈ ISO size × 2**         | Working dir + final image.                                                                                                                    |

---

## 3  CLI usage

```bash
# minimal
./scripts/run_bodycam_pipeline/run_bodycam_pipeline.py *.mp4
```

\### 3.1  Pass‑through flags — expose every useful option from the stages

For any flag that exists in a stage script you may supply the **same flag name** but with the stage‑prefix listed below. The pipeline validates it, then relays it unchanged to the right sub‑process. If you omit the prefix by mistake, the parser throws “unknown option”.

| Stage                | Prefix     | Examples                                                          |
| -------------------- | ---------- | ----------------------------------------------------------------- |
| `prepare_bodycam.py` | `--prep-`  | `--prep-disc-bytes 50_000_000_000`, `--prep-delete-originals yes` |
| `create_iso.py`      | `--iso-`   | `--iso-volume-label SHIFT_001`, `--iso-force`                     |
| `burn_iso.py`        | `--burn-`  | `--burn-skip-verify`, `--burn-speed 4`, `--burn-device /dev/sr0`  |
| `cleanup`         | `--clean-` | `--clean-build-dir /tmp/work`                                     |

* Flags keep **identical semantics, defaults, and mutually-exclusive rules** as documented in each script.
* Unknown or misspelled flags abort before stage ① so nothing is written to disk.
* Global `FILE …` positionals (the raw clips) always come last.

```bash
# full custom run (50 GB disc, custom label, no verify, 4× burn)
./scripts/run_bodycam_pipeline/run_bodycam_pipeline.py shift1/*.mp4 \
   --prep-disc-bytes 50_000_000_000 --prep-safety-bytes 0 \
   --iso-volume-label SHIFT1_20250718 --iso-force \
   --burn-skip-verify --burn-speed 4
```

---

## 4  What happens under the hood (30 sec overview)

| Stage      | Tool                 | Key action                                                         | Output                |
| ---------- | -------------------- | ------------------------------------------------------------------ | --------------------- |
|  ① Prepare | `prepare_bodycam.py` | Copy or re‑encode clips into a temp *build dir* sized to fit disc. | ready‑to‑master files |
|  ② Image   | `create_iso.py`      | Make `YYYYMMDDTHHMMSSZ.iso` (UTC stamp in volume name).            | ISO file              |
|  ③ Burn    | `burn_iso.py`        | Write + SHA‑256 verify.                                            | Final Blu‑ray         |
|  ④ Clean   | `cleanup`         | Delete build dir.                                                  | —                     |

See each tool’s doc for exact flags and edge‑cases — the pipeline merely orchestrates them.

---

## 5  Quick‑start checklist

1. **Insert blank disc** (if burning).
2. **Mount external SSD** (or adjust `ROOT`).
3. `cd` to folder containing your raw clips.
4. Run the command in § 3 and relax — the terminal will print the ISO path and log location when done.

---

## 6  Acceptance criteria (platform‑agnostic)

|    #   | Scenario & pre‑conditions                                     | Steps (user → expected result)                                                                                                                                     |
| :----: | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
|  **1** | **Happy path (copy only)** — Total size ≤ disc.               | 1 Run script → build dir created, files copied → ISO built → disc burned & verified → build dir deleted → exit 0; final message prints ISO+log paths.              |
|  **2** | **Happy path (re‑encode)** — Size > disc so re‑encode needed. | Same as #1 but prepare stage transcodes and reports bitrate; pipeline still exits 0.                                                                               |
|  **3** | **Missing workspace drive** — `ROOT` not mounted.             | 1 Run → script aborts before stage ①; clear error *“No such path… (check ROOT)”*; exit 1; nothing written.                                                         |
|  **4** | **Bad input file** — One source file does not exist.          | 1 Run → prepare stage fails → pipeline exits 1; log pinpoints missing file; ISO/BD not created; build dir auto‑deleted.                                            |
|  **5** | **Sub‑step failure propagates** (e.g. burner missing).        | 1 Disconnect BD writer → run → burn stage fails → pipeline exits with non‑zero code from `burn_iso.py`; log states failing stage; build dir retained for analysis. |
|  **6** | **User abort (Ctrl‑C)** during any stage.                     | Signal forwarded → current sub‑script stops → pipeline exits 130; no further stages run; partial ISO not burned; temp dir left intact.                             |
|  **7** | **Repeat runs** — Execute twice within 1 s.                   | Each run generates unique build dir, ISO, log names (timestamped) with no collisions.                                                                              |
|  **8** | **Cross‑platform** — macOS, Linux, Windows (WSL 2).           | Scenarios 1, 2, 5 & 6 behave identically; all logs show correct paths (POSIX or Windows as applicable).                                                            |
|  **9** | **Pass‑through flag honoured** — e.g. skip verification.      | 1 Run with `--burn-skip-verify` → pipeline passes flag to burn stage; log confirms verification skipped; exit 0.                                                   |
| **10** | **Invalid pass‑through flag** — typo.                         | 1 Run with `--iso-volumelabel ABC` → parser aborts at start; meaningful “unknown option” message; exit 1; no files created.                                        |

> **All ten scenarios must pass unchanged on every supported OS.** Any failure stops the pipeline immediately and surfaces the root cause.

---

**End of specification**
