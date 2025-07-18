# concat\_shuffle.py — Concatenate & Shuffle Clips

A tiny helper that **losslessly stitches together a list of pre‑trimmed video snippets into one shuffled “montage” file**.
Typical use‑case: you first run `make_shuffle_clips.py` to cut highlights, then run this script to merge them into a single share‑ready video.

---

## 1  Prerequisites

| Requirement                    | Why it’s needed                   |
| ------------------------------ | --------------------------------- |
| **Python ≥ 3.8**               | Runs the wrapper script           |
| **FFmpeg (4.0 +) in PATH**     | Performs the actual concatenation |
| Disk space ≥ size of all clips | Output is a direct copy           |

---

## 2  Inputs & options

| Option               | Required | Description                                                              |
| -------------------- | -------- | ------------------------------------------------------------------------ |
| `--clip-list <path>` | ✔        | Text file in FFmpeg “concat” format produced by `make_shuffle_clips.py`. |
| `--out-file  <name>` | ✔        | Target video file (e.g., `montage.mkv`). Overwritten if already present. |
| `--logfile   <path>` | ✖        | Where to write verbose progress output (defaults to STDOUT).             |

---

## 3  Quick start

```bash
./concat_shuffle.py \
  --clip-list clip_list.txt \
  --out-file  montage.mkv \
  --logfile   concat.log
```

The script prints a running FFmpeg command, then exits with **0** on success. ([GitHub][1])

---

## 4  Exit codes

| Code | Meaning                                                   |
| ---- | --------------------------------------------------------- |
| 0    | All clips concatenated; output file verified to exist.    |
| 1    | Invalid arguments (missing / unreadable list, bad paths). |
| 2    | One + clips missing or unreadable; FFmpeg aborted.        |
| 3    | FFmpeg returned a non‑zero status for any other reason.   |

---

## 5  Acceptance criteria (cross‑platform)

All scenarios must pass on Linux, macOS, and Windows (WSL) **without altering this spec**.

| #     | Scenario & Pre‑conditions                                              | Steps (user → expected behaviour)                                                                      |
| ----- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **1** | **Happy path** — list references existing clips.                       | 1 Run script ➜ 2 Progress logged ➜ 3 `montage.mkv` created; exit 0.                                    |
| **2** | **Missing clip** — list contains a path that does not exist.           | 1 Run script ➜ 2 FFmpeg error surfaced in log ➜ 3 Exit 2 and no output file.                           |
| **3** | **Unreadable list file** — wrong path or no permissions.               | 1 Run script ➜ 2 Script prints clear error ➜ 3 Exit 1.                                                 |
| **4** | **Output already exists & is locked** (e.g., open in another program). | 1 Run script ➜ 2 OS blocks write ➜ 3 Script aborts, exit 3.                                            |
| **5** | **Interrupted run** (Ctrl‑C mid‑process).                              | 1 Interrupt ➜ 2 Partial file removed to avoid corruption ➜ 3 Exit 3.                                   |
| **6** | **Large montage** (> 4 GB).                                            | 1 Run script ➜ 2 Completes within expected time, log reports success ➜ 3 File plays from start to end. |
