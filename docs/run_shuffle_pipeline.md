# **run\_shuffle\_pipeline.py — One‑stop “Shuffle Montage” builder**

## 1 Purpose

Wraps **three helpers**—`make_shuffle_clips.py → concat_shuffle.py → cleanup`—so you can cut, merge, and tidy a random highlight reel in a single command. Default output is a **10‑minute (600 s) montage** on your Desktop plus a full log, but every parameter of the underlying tools is exposed for power‑users.

---

## 2 Prerequisites

| Requirement                   | Why needed                         |
| ----------------------------- | ---------------------------------- |
| Python ≥ 3.8                  | Runs the wrapper & helpers.        |
| FFmpeg 4.x (+ ffprobe)        | All trimming / concatenation.      |
| ≈ 2 × final size free disk    | Scratch clips live in `--tmp-dir`. |
| macOS / Linux / Windows (WSL) | Run inside Docker on any host OS.   |
| Helper scripts co‑located     | Wrapper execs them directly.       |

The wrapper previously adjusted `PATH` for Homebrew. Docker images now provide FFmpeg, so no adjustment is required.

---

## 3 Inputs & options

Every flag of **all three helpers** can be supplied here; the wrapper validates, wires, and forwards them.

| Flag                   | Default                              | Forwarded to                    | Notes                                                               |
| ---------------------- | ------------------------------------ | ------------------------------- | ------------------------------------------------------------------- |
| `--tmp-dir DIR`        | `/tmp/shuffle_<ts>`                  | `make_shuffle_clips`, `cleanup` | Scratch workspace.                                                  |
| `--logfile FILE`       | `~/Desktop/Montage‑Shuffle‑<ts>.log` | *all*                           | One shared log.                                                     |
| `--target-sec N`       | **600**                              | `make_shuffle_clips`            | Total montage length; accepts `s`, `m`, `h` suffixes.  |
| `--min-clip N`         | 2                                    | `make_shuffle_clips`            | Smallest clip length.                                               |
| `--max-clip N`         | 5                                    | `make_shuffle_clips`            | Largest clip length.                                                |
| `--seed N`             | none                                 | `make_shuffle_clips`            | Reproducible shuffles.                                 |
| `--clip-list FILE`     | auto‑generated                       | `concat_shuffle`                | Advanced: reuse a pre‑made list.                    |
| `--out-file FILE`      | `montage_<ts>.mkv` (Desktop)         | `concat_shuffle`                | Final video name.                                    |
| `--build-dir DIR`      | same as `--tmp-dir`                  | `cleanup`                       | Directory to delete.                                  |
| *positional* `VIDEOS…` | —                                    | `make_shuffle_clips`            | One or more FFmpeg‑readable files.                                  |

> **Tip** You may combine any subset of the above; unspecified flags revert to their defaults.

---

## 4 Workflow (under the hood)

1. **Prepare** — create timestamped log, resolve defaults, make `--tmp-dir`.
2. **Extract** — run `make_shuffle_clips.py` with all relevant args.
3. **Concatenate** — call `concat_shuffle.py` (auto‑generates `--clip-list` unless you supplied one).
4. **Clean** — call the `cleanup` helper to delete `--build-dir`.
5. **Finish** — print absolute paths of final video & log; exit 0 only if every step succeeded. ([GitHub][1], [GitHub][3], [GitHub][4])

---

## 5 Examples

```bash
# Default 10‑min montage
./scripts/run_shuffle_pipeline/run_shuffle_pipeline.py vacation/*.mp4

# Two‑minute teaser, 1–3 s clips, reproducible shuffle
./scripts/run_shuffle_pipeline/run_shuffle_pipeline.py --target-sec 120 --min-clip 1 --max-clip 3 --seed 42 *.mp4

# Power‑user: supply your own temp dir & output name
./scripts/run_shuffle_pipeline/run_shuffle_pipeline.py --tmp-dir /var/tmp/shuf \
                          --out-file wow.mkv      \
                          cam?.mov
```

---

## 6 Acceptance criteria

| #      | Scenario                                                | Expected behaviour                                                                    |
| ------ | ------------------------------------------------------- | ------------------------------------------------------------------------------------- |
| **1**  | **Happy path (defaults)** — ≥ 2 videos                  | Montage on Desktop; duration 600 ±1 s; log ends with **SUCCESS**; exit 0.             |
| **2**  | **Custom target length** — `--target-sec 120`           | Output length 120 ±1 s.                                                               |
| **3**  | **Custom clip bounds** — `--min-clip 3 --max-clip 7`    | Every snippet duration ∈ \[3 s, 7 s].                                                 |
| **4**  | **Reproducible seed** — run twice with `--seed 7`       | Byte‑identical `montage.mkv`.                                                         |
| **5**  | **User tmp dir** — `--tmp-dir /var/tmp/shuf`            | All artefacts appear there; dir removed after success.                                |
| **6**  | **User clip list** — `--clip-list my.txt`               | Wrapper skips extraction; concatenates supplied list.                                 |
| **7**  | **Custom out file** — `--out-file mix.mkv`              | File is exactly that name on Desktop (or absolute path if given).                     |
| **8**  | **Custom logfile**                                      | All three helpers append to the same file.                                            |
| **9**  | **No args**                                             | Prints “❌ No input files”, exits 1; no tmp dir made.                                  |
| **10** | **Invalid numeric combo** — `--min-clip 8 --max-clip 5` | Wrapper forwards, helper rejects; exit 1.                             |
| **11** | **Disk full in tmp dir**                                | Graceful abort; tmp cleaned; exit 1.                                                  |
| **12** | **Large batch (≥ 50 files)**                            | Runtime scales linearly; length correct; exit 0.                                      |
| **13** | **Log integrity**                                       | Log contains clearly delimited sections *extract / concat / cleanup* and final paths. |
| **14** | **Cleanup**                                             | After any success `--build-dir` no longer exists.                                     |

All scenarios **must pass unchanged** when executed via Docker. At no time may the pipeline alter or delete the user’s original media.

---

**End of specification**
