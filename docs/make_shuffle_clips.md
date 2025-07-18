````markdown
# make_shuffle_clips.py — build a 10‑min highlight reel from any set of videos

Generate a **chronological‑but‑shuffled** montage: every clip is taken from an equal‑sized “virtual partition” of the combined timeline, so the finished reel samples *the whole day* while still feeling random inside each slice.

---

## 1 Why use it?
* **Fast daily review** – skim hours of raw footage in minutes.  
* **Key‑frame safe** – cuts always begin on key‑frames, so the clips can later be concatenated losslessly.  
* **Platform‑agnostic** – pure Python + FFmpeg; runs on Linux, macOS, and Windows (WSL).

---

## 2 How it works (in 30 s)
1. **Scan durations** of every input file with `ffprobe`.
2. **Compute a clip plan** so that  
   * total length = `TARGET_SEC` (default 600 s)  
   * each clip length ∈ [`MIN_CLIP`, `MAX_CLIP`] (defaults 2–5 s)  
3. **Slice the combined timeline into `N` equal partitions.** (`N` ≈ `TARGET_SEC` / avg_clip_len)  
4. **Select one random offset inside each partition** (offset ≤ partition − clip_len).  
5. **Write**  
   * `TMP_DIR/clipNN.mkv` – key‑frame‑aligned segments  
   * `TMP_DIR/clip_list.txt` – *ffmpeg‑concat* manifest  

The result feels shuffled, yet always progresses forward in time.

---

## 3 Requirements
* Python 3.8+  
* FFmpeg & ffprobe available on `$PATH`  
* A writable temporary directory with ~2 × output size free space

---

## 4 Inputs & options
| Flag | Required | Description | Default |
|------|----------|-------------|---------|
| `--tmp-dir DIR` | ✔ | Scratch directory that will receive the clips & manifest | — |
| `--logfile FILE` | ✔ | Where progress messages are written | — |
| `--target-sec N` | ✖ | Total desired length (seconds) of the finished montage | `600` |
| `--min-clip N` | ✖ | Smallest allowed clip length (seconds) | `2` |
| `--max-clip N` | ✖ | Largest allowed clip length (seconds) | `5` |
| *positional* `FILES…` | ✔ | One or more source videos (any FFmpeg‑readable codec) | — |

**Rules**

* `1 ≤ MIN_CLIP ≤ MAX_CLIP < TARGET_SEC`  
* All numeric flags accept integers **or** `s`, `m`, `h` suffixes (e.g. `--target-sec 15m`).  
* If you supply only one of `--min-clip` or `--max-clip`, the other retains its default.

---

## 5 Quick start
```bash
# Ten‑minute reel, default 2–5 s clips
./make_shuffle_clips.py \
    --logfile shuffle.log \
    --tmp-dir /tmp/shuf \
    cam1.mp4 cam2.mp4 cam3.mp4

# Two‑minute super‑quick preview, 1–3 s clips
./make_shuffle_clips.py \
    --target-sec 120 \
    --min-clip 1 \
    --max-clip 3 \
    --logfile preview.log \
    --tmp-dir /tmp/preview \
    *.mp4
````

Resulting files live in the chosen `--tmp-dir`:

```text
clip001.mkv
…
clipNNN.mkv
clip_list.txt     # ready for: ffmpeg -f concat -safe 0 -i clip_list.txt -c copy montage.mkv
```

---

## 6 Tuning & reproducibility

* All numeric flags accept `s`, `m`, `h` suffixes for convenience (`--target-sec 10m`).
* For reproducible shuffles, pass `--seed N` (not shown in table; any int).
* Internally the script uses `random.Random(seed)`; if no seed is provided, it falls back to current time.

---

## 7 Acceptance criteria

| #     | Scenario & pre‑conditions                                  | Steps (user → expected behaviour)                                                                                                                                        |
| ----- | ---------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **1** | **Happy path (defaults)** – valid videos, writable tmp dir | 1 Run script with no target/min/max flags.<br>2 Process exits `0`.<br>3 `clip_list.txt` duration **600 ± 0.1 s**.                                                        |
| **2** | **Custom lengths** – user overrides                        | 1 Run with `--target-sec 120 --min-clip 1 --max-clip 3`.<br>2 Exit `0`.<br>3 `clip_list.txt` duration **120 ± 0.1 s** and every clip’s duration ∈ \[1 s, 3 s].           |
| **3** | **Even coverage**                                          | 1 Inspect timestamps of successive clips.<br>2 They strictly increase and lie within their respective equal‑width partitions (partition width ≈ combined\_duration / N). |
| **4** | **Key‑frame integrity**                                    | 1 Concatenate with `ffmpeg -f concat -safe 0 -i clip_list.txt -c copy out.mkv`.<br>2 `ffmpeg` shows “Stream copy”, zero re‑encode.                                       |
| **5** | **Invalid numeric combo**                                  | 1 Run `--min-clip 8 --max-clip 5`.<br>2 Script aborts non‑zero; stderr explains “MIN\_CLIP must be ≤ MAX\_CLIP”.                                                         |
| **6** | **Total footage shorter than TARGET\_SEC**                 | 1 Provide sources totaling < TARGET\_SEC.<br>2 Script exits non‑zero; message “source shorter than requested target”.                                                    |
| **7** | **Missing ffmpeg / ffprobe**                               | 1 Temporarily remove them from `$PATH`.<br>2 Exit non‑zero; log prints failing command.                                                                                  |
| **8** | **Unwritable tmp‑dir**                                     | 1 Pass `--tmp-dir` pointing to read‑only path.<br>2 Exit non‑zero; log: “permission denied”.                                                                             |

All scenarios must pass unchanged on Linux, macOS, and Windows (WSL).

---

**End of specification**
