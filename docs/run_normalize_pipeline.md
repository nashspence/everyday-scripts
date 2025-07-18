# **run\_normalize\_pipeline.py — Two‑pass EBU R128 normalisation**

## 1 Purpose
Wrap the whole *measure → correct* loudness workflow in **one friendly command**.
You feed it any media file; it gives you back an AAC‑encoded copy whose audio sits at a broadcast‑safe **‑16 LUFS / ‑1.5 dBTP** by default. A timestamped log is created so you can prove exactly what happened. ([GitHub][1])

---

## 2 Prerequisites

| Item                               | Why it matters                        |
| ---------------------------------- | ------------------------------------- |
| Python ≥ 3.8                       | Script runtime                        |
| FFmpeg 5 + in `$PATH`              | Performs the heavy lifting            |
| Write access to the working folder | Copies, logs and temp files live here |

> *The script autodetects platform (macOS, Linux, Windows + WSL) and aborts early if FFmpeg is missing.*

---

## 3 CLI options

| Flag           | Required |        Default       | Example          | Notes                                      |
| -------------- | :------: | :------------------: | ---------------- | ------------------------------------------ |
| `-i`, `--lufs` |     ☐    |        **‑16**       | `‑i ‑14`         | Target integrated loudness                 |
| `-t`, `--tp`   |     ☐    |       **‑1.5**       | `‑t ‑2`          | Max true‑peak (dBTP)                       |
| `input`        |     ✅    |           —          | `input.wav`      | Any audio or A/V container                 |
| `output`       |     ☐    | `<input>_R128.<ext>` | `song_fixed.m4a` | Omit to auto‑suffix `*_R128`               |

---

## 4 What actually happens (under the hood)

1. **Safety checks** — verify input exists, refuse to overwrite, create a dated log file.
2. **Pass 1 – Analyse** — `analyse_loudness.py` runs FFmpeg’s `loudnorm` in *analyse* mode, saving the measured metrics.
3. **Pass 2 – Render** — `normalize_audio.py` rereads those metrics and performs the corrective second pass, copying any video streams untouched.
4. **Cleanup & summary** — the temporary JSON is deleted; console prints the path to the normalised file and the full log.

*(See the individual scripts for the low‑level FFmpeg arguments; this document keeps to the high‑level flow.)*

---

## 5 Quick‑start

```bash
# Most people just need this:
./run_normalize_pipeline.py input.wav

# Custom loudness, explicit output path:
./run_normalize_pipeline.py -i -14 -t -2 input.mp4 fixed_audio.mp4
```

---

## 6 Acceptance criteria (platform‑agnostic)

| #      | Scenario & pre‑conditions                                | Steps (user → expected result)                                                                                                    |
| ------ | -------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | **Default run** — valid file provided, defaults accepted | 1 Run script → output named `_R128` appears; integrated loudness −16 ±0.1 LU; TP ≤ −1.5 dBTP; exit 0; log file written.           |
| **2**  | **Custom targets**                                       | 1 Run with `‑i -14 ‑t -2` → output meets those values within same tolerances; exit 0.                                             |
| **3**  | **Explicit output path**                                 | 1 Supply `output.m4a` → file written exactly there (no `_R128` suffix); exit 0.                                                   |
| **4**  | **Input missing**                                        | 1 Give non‑existent path → script aborts with “not found” message; exit ≠ 0.                                                      |
| **5**  | **Overwrite guard**                                      | 1 Pass identical file for `input` *and* `output` → script refuses; exit ≠ 0.                                                      |
| **6**  | **FFmpeg absent**                                        | 1 Temporarily rename `ffmpeg` → script aborts early with actionable message; exit ≠ 0.                                            |
| **7**  | **Log dir first‑run**                                    | 1 Delete log folder; run script → folder re‑created; log file present afterwards.                                                 |
| **8**  | **Paths with spaces**                                    | 1 Use `"My Mix.wav"` → processing succeeds; exit 0.                                                                               |
| **9**  | **Video passthrough**                                    | 1 Input `.mp4` with video track → audio normalised; video stream copied bit‑for‑bit; container fast‑start flag preserved; exit 0. |
| **10** | **Temp metrics cleanup**                                 | 1 Run script → temp `loudnorm_*.json` deleted on success or failure.                                                              |

All ten scenarios **must pass, unmodified, on macOS, Linux, and Windows (WSL).** If any step fails the original file remains untouched and the exit status is non‑zero.

---

**End of specification**
