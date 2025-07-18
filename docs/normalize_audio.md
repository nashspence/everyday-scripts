# **normalize\_audio.py — Broadcast‑ready loudness correction**

## 1 Purpose
Create a version of any A/V file that **meets EBU R128 (or your own) loudness and true‑peak targets** while staying sample‑accurate to the original video. It is **pass 2** of a two‑stage workflow: first run `analyse_loudness.py`, then feed its metrics to this script.

---

## 2 Prerequisites

| Item                                                 | Why it matters                                        |
| ---------------------------------------------------- | ----------------------------------------------------- |
| Metrics JSON from **analyse\_loudness.py**           | Supplies the measured loudness values this pass needs |
| **ffmpeg ≥ 4.3** in `$PATH`                          | All DSP work is delegated to FFmpeg                   |
| Python ≥ 3.8                                         | Script runtime                                        |
| Readable **input media** (`.wav`, `.mov`, `.mp4`, …) | Source to be normalised                               |
| Writable **output location**                         | Destination file                                      |
| macOS • Linux • Windows (WSL)                        | Fully supported                                       |

> `prepend_path()` automatically adds common Homebrew paths so FFmpeg is found on macOS/Linux.

---

## 3 CLI options

| Flag                   | Required | Example             | Notes                                     |
| ---------------------- | :------: | ------------------- | ----------------------------------------- |
| `--in-file PATH`       |     ✅    | `clip.mov`          | Source audio or A/V                       |
| `--out-file PATH`      |     ✅    | `clip_R128.mov`     | **Over‑written** if present               |
| `--analysis-json FILE` |     ✅    | `clip_metrics.json` | Output of pass 1                          |
| `--target-i N`         |     ☐    | `-19`               | Integrated loudness in LUFS (default −16) |
| `--target-tp N`        |     ☐    | `-2`                | True‑peak limit in dBTP (default −1.5)    |
| `--logfile FILE`       |     ✅    | `norm.log`          | Duplicates to stderr                      |

---

## 4 Under the hood (60 s)

1. **Validate JSON** – checks for keys `input_i / tp / lra / thresh / target_offset`; aborts if any are missing.
2. **Build filter chain** – `highpass=f=120, loudnorm=…, aresample=async=1` ensures clean low‑end, correct loudness, and audio/video sync.
3. **Encode** – copies video (`-c:v copy`), re‑encodes audio to AAC, sets `+faststart`, and forces overwrite (`-y`).
4. **Exit codes** – any FFmpeg error surfaces; success logs “✓ done” and returns **0**.

---

## 5 Quick‑start

```bash
# Pass 1 – measure
./analyse_loudness.py --in-file clip.mov --out-json clip_metrics.json

# Pass 2 – normalise
./normalize_audio.py \
  --logfile norm.log \
  --in-file clip.mov \
  --out-file clip_R128.mov \
  --analysis-json clip_metrics.json
```

---

## 6 Acceptance criteria (platform‑agnostic)

| #      | Scenario & pre‑conditions          | Steps (user → expected result)                                                                         |
| ------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **1**  | **Video, default targets**         | Run → output LUFS within ±0.5 LU, TP ≤ −1.5 dB; exit 0; log “✓ done”.                                  |
| **2**  | **Audio‑only WAV**                 | Same as #1; duration identical.                                                                        |
| **3**  | **Missing `--analysis-json` flag** | Omit flag → argparse error; exit 2; no processing.                                                     |
| **4**  | **Metrics file absent**            | Bad path → script aborts; exit 1; log “File not found”.                                                |
| **5**  | **Metrics missing key**            | Delete `input_tp` → RuntimeError; exit 1; log “Missing key in metrics”.                                |
| **6**  | **Input file absent**              | Bad `--in-file` → FFmpeg fails; exit 1; log relevant error.                                            |
| **7**  | **Output unwritable**              | Path in read‑only dir → FFmpeg fails; exit 1; OS error in log.                                         |
| **8**  | **FFmpeg not in PATH**             | Rename `ffmpeg` → subprocess error; exit 1; log instructs to install/restore.                          |
| **9**  | **Custom loudness**                | `--target-i -20 --target-tp -2` → output meets those limits.                                           |
| **10** | **Output file exists**             | Provide existing path → file replaced; new output passes #1 checks.                                    |
| **11** | **Windows WSL**                    | Run on same media as #1 → identical behaviour; no path issues.                                         |
| **12** | **Pipeline regression**            | Run pass 1 → pass 2 on ten clips → zero errors; video streams SHA‑256 match originals (audio differs). |

All twelve scenarios **must pass unchanged** on Linux, macOS, and Windows (WSL). Any failure must leave source media untouched or clearly report the error.
