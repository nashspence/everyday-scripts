# **prepare\_bodycam.py — Fit a batch of MP4 clips on one disc, every time**

---

## 1 Purpose

Copy **or** re‑encode a folder of body‑camera clips so their combined size never exceeds a user‑defined disc capacity.

* Chooses **COPY** when everything already fits.
* Otherwise re‑encodes to AV1 + Opus at one calculated constant bitrate for uniform quality.
* Writes all outputs to a *build directory* that is ready for ISO creation and burning.

---

## 2 Prerequisites

| Requirement                                         | Reason                          |
| --------------------------------------------------- | ------------------------------- |
| Python ≥ 3.8                                        | Script runtime                  |
| FFmpeg ≥ 6.0 with `ffprobe`, `libsvtav1`, `libopus` | Media probing and (re)encoding  |
| Free disk space ≥ (total input size + 1 GB)         | Working files and logs          |
| Linux, macOS, or Windows WSL                        | Run the Docker image on any platform |

Missing tools or versions abort execution with a clear error message.

---

## 3 Command‑line interface

| Flag                           |        Required       | Default          | Example                       | Description                                                             |
| ------------------------------ | :-------------------: | ---------------- | ----------------------------- | ----------------------------------------------------------------------- |
| `--build-dir DIR`              |           ✅           | —                | `--build-dir work`            | Destination for processed clips and progress file (auto‑created).       |
| `--logfile FILE`               |           ✅           | —                | `--logfile prep.log`          | Full run log (also echoed to stdout).                                   |
| `--disc-bytes N`               |           ❌           | `25_000_000_000` | `--disc-bytes 50_000_000_000` | Target medium capacity **in bytes**.                                    |
| `--safety-bytes N`             |           ❌           | `500_000_000`    | `--safety-bytes 200_000_000`  | Reserved head‑room to guarantee no overflow.                            |
| `--delete-originals {yes\|no}` |           ❌           | `no`             | `--delete-originals yes`      | Remove source clips **only after the job finishes successfully**.       |
| `--resume FILE`                |           ❌           | —                | `--resume work/progress.json` | Resume an interrupted job; processes only files still marked *pending*. |
| *positional* `FILE …`          | ✅ (unless `--resume`) | —                | `*.mp4`                       | One or more input videos. Ignored when `--resume` is used.              |

All numeric arguments must be positive integers.

---

## 4 Progress tracking & resume design

* A JSON progress file is created in the build directory (or the path given to `--resume`).
* Example structure:

```json
{
  "disc_bytes": 25000000000,
  "safety_bytes": 500000000,
  "mode": "COPY",
  "kbps": null,                // populated only when mode == "ENCODE"
  "files": {
    "cam1_001.mp4": "done",
    "cam1_002.mp4": "pending"
  }
}
```

* Each clip switches from `"pending"` → `"done"` immediately after a successful copy or encode; the file is flushed to disk.
* When `--resume` is provided, clips already marked `"done"` are skipped and untouched.
* If the progress file is missing, unreadable, or malformed, the script exits with a specific error code (see §6).

---

## 5 Processing logic (high‑level)

1. **Parse arguments** and validate.
2. **Create or load progress**

   * No `--resume` ➜ create fresh progress file and record chosen parameters.
   * `--resume` ➜ load existing progress file and validate consistency with CLI arguments (`disc‑bytes`, `safety‑bytes`, `mode`).
3. **Mode decision**

   * Compute `usable_bytes = disc_bytes – safety_bytes`.
   * If total size of *pending* clips ≤ `usable_bytes` ➜ `mode = COPY`.
   * Else ➜ `mode = ENCODE`:

     * Sum durations of *pending* clips (via `ffprobe`).

     * Calculate constant video bitrate:

       $$
       \text{kbps} = \frac{(\text{usable bytes} \times 8)}{\text{total seconds}} / 1000
       $$

     * Store `kbps` in progress file so resumed runs keep the same bitrate.
4. **Clip loop**

   * For each *pending* clip:

     * **COPY** ➜ `shutil.copy2`.
     * **ENCODE** ➜ `ffmpeg -y -i input -c:v libsvtav1 -b:v {kbps}k -c:a libopus -b:a 64k -ac 1 -ar 24000 output`.
     * On success mark `"done"` and flush progress file.
     * On any exception write error to log, keep `"pending"`, and exit with code 4.
5. **Completion**

   * Verify combined size of outputs ≤ `usable_bytes`.
   * Rename progress file to `progress.completed.json`.
   * If `--delete-originals yes` ➜ delete source clips.

---

## 6 Exit codes

| Code | Meaning                                                               |
| :--: | --------------------------------------------------------------------- |
|  `0` | Success — all clips processed, size within limit.                     |
|  `1` | Usage error or missing dependency.                                    |
|  `2` | Finished processing but outputs still exceed limit.                   |
|  `3` | Progress file missing, corrupted, or inconsistent with CLI arguments. |
|  `4` | Runtime error during copy/encode (progress saved, safe to resume).    |

---

## 7 Quick examples

```bash
# Standard 25 GB disc, keep originals
./scripts/prepare_bodycam/prepare_bodycam.py --logfile prep.log --build-dir work shift1/*.mp4

# Double‑layer BD‑R, smaller safety margin
./scripts/prepare_bodycam/prepare_bodycam.py --logfile prep.log --build-dir work \
  --disc-bytes 50_000_000_000 --safety-bytes 200_000_000 *.mp4

# Resume a previously interrupted job
./scripts/prepare_bodycam/prepare_bodycam.py --logfile prep.log --resume work/progress.json

# After a clean run, delete source files
./scripts/prepare_bodycam/prepare_bodycam.py --logfile prep.log --build-dir work \
  --delete-originals yes shift2/*.mp4
```

---

## 8 Acceptance criteria

The script **must pass** every scenario when executed through Docker on any host OS.

| #      | Scenario                    | Preconditions                                                      | Expected outcome                                                       |
| ------ | --------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------- |
| **1**  | Custom disc size            | `--disc-bytes 50_000_000_000`, total input ≤ 49.5 GB               | COPY mode, exit 0, log shows capacity 50 GB.                           |
| **2**  | Custom safety margin        | `--safety-bytes 0`, total input = 24.9 GB                          | COPY mode, exit 0, final size ≤ 25 GB.                                 |
| **3**  | Delete originals            | `--delete-originals yes`, inputs fit without encode                | After exit 0, originals are gone; copies exist.                        |
| **4**  | Resume mid‑copy             | Kill script after 1 of 3 copies; run with `--resume progress.json` | Second run skips finished file, processes remaining 2, exit 0.         |
| **5**  | Resume mid‑encode           | Same as 4 but mode = ENCODE                                        | Remaining clips encoded; bitrate identical to first run.               |
| **6**  | Corrupt progress file       | Truncate `progress.json`; run with `--resume`                      | Abort, exit 3, originals untouched.                                    |
| **7**  | Resume omitted              | Progress file exists but run started without `--resume`            | New progress file overwrites old; warning logged; processing restarts. |
| **8**  | Overflow after encode       | Job finishes but outputs > usable\_bytes                           | Exit 2; outputs retained for inspection.                               |
| **9**  | Safety for delete‑originals | `--delete-originals yes`; kill job mid‑run                         | Originals remain until a run exits 0.                                  |
| **10** | Basic copy fit              | Defaults, total input ≤ 24.5 GB                                    | COPY mode, exit 0, SHA‑256 of each copy matches original.              |
| **11** | Basic encode fit            | Defaults, total input > 24.5 GB                                    | ENCODE mode, exit 0, total outputs ≤ 24.5 GB.                          |

---

**End of specification**
