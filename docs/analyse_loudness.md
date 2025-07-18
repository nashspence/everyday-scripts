# **analyse\_loudness.py** – *Loudness analysis (pass 1)*

---

## 1  Why analyse loudness?

Runs FFmpeg’s first `loudnorm` pass to pull the loudness statistics (LUFS, true‑peak, etc.) that will drive the later normalisation pass. Storing the JSON makes the second pass completely deterministic and avoids repeated re‑analysis.

---

## 2  Prerequisites

* **FFmpeg ≥ 4.3** in `PATH` (build with `loudnorm` filter).
* **Python 3.8+** plus the helper module `utils` shipped in the repo.
* Read/write access to the directories you pass in.

---

## 3  Inputs & options

| Flag              | Required | Default | Meaning                                       |
| ----------------- | -------- | ------- | --------------------------------------------- |
| `--in-file PATH`  | ✔        |  –      | Source media (any container FFmpeg can read). |
| `--target-i NUM`  | ✖        |  `‑16`  | Integrated LUFS target.                       |
| `--target-tp NUM` | ✖        |  `‑1.5` | True‑peak target in dBTP.                     |
| `--out-json PATH` | ✔        |  –      | Destination file for the captured metrics.    |
| `--logfile PATH`  | ✔        |  –      | Where progress & errors are logged.           |

*Exit codes*: **0** success · **≠0** failure.

---

## 4  Outputs

A UTF‑8 JSON file containing at minimum the keys FFmpeg prints:
`input_i`, `input_tp`, `input_lra`, `input_thresh`, `target_offset`, `measured_I`, … (full set depends on FFmpeg version). ([GitHub][2])

---

## 5  Example

```bash
./analyse_loudness.py \
  --logfile loudness.log \
  --in-file clip.mov \
  --out-json metrics.json
```

`metrics.json` can then be fed straight into the normalisation (pass 2) script.

---

## 6  Acceptance criteria (platform‑agnostic)

| #     | Scenario (pre‑conditions)                                     | Steps → Expected behaviour                                                                                                                                                                                  |
| ----- | ------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1** | **Happy path** ‑ valid media, writable destination.           | 1 Run script with all required flags.<br>2 Process exits 0.<br>3 `metrics.json` exists and includes **all** FFmpeg keys listed in §4.<br>4 `loudness.log` records command line and “Metrics saved” message. |
| **2** | **Missing input file**.                                       | 1 Pass a non‑existent `--in-file`.<br>2 Process exits ≠0.<br>3 `loudness.log` contains “No such file” (or FFmpeg equivalent).<br>4 No `metrics.json` is written.                                            |
| **3** | **Unwritable output path** (e.g. read‑only dir).              | 1 Provide a path in an unwritable location.<br>2 Process exits ≠0.<br>3 `loudness.log` shows a “Permission denied” or similar filesystem error.                                                             |
| **4** | **Invalid numeric target** (`--target-i 0` or extreme value). | 1 Run with an out‑of‑range value.<br>2 Process exits ≠0.<br>3 Log records FFmpeg validation error.                                                                                                          |
| **5** | **FFmpeg not in PATH**.                                       | 1 Run with PATH cleared of FFmpeg.<br>2 Process exits ≠0.<br>3 Log shows “ffmpeg: command not found” (or Windows equivalent).                                                                               |

All scenarios must pass without modifying this spec on **Linux**, **macOS**, and **Windows (WSL)**.

---

**End of specification**
