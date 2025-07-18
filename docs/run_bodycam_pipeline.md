# run_bodycam_pipeline.py Full bodycam workflow

## 1 Why run the pipeline?

Automates preparing clips, creating an ISO, burning it and cleaning up. Produces
a timestamped log and disc image without manual intervention.

---

## 2 Inputs and options

Positional arguments: one or more source files.
No optional flags besides those passed to sub-scripts via environment.

---

## 3 Example invocation

```bash
./run_bodycam_pipeline.py *.mp4
```

---

## 4 Acceptance criteria (platform-agnostic)

| # | Scenario & pre-conditions | Steps (user actions -> expected behaviour) |
| --- | ------------------------------------------------------------ | ------------------------------------------------------ |
| **1** | **End-to-end success** | 1 Run script with camera files.<br>2 ISO burned and log summarises each step. |
| **2** | **Sub-step failure** | 1 Force an error (e.g. missing FFmpeg).<br>2 Pipeline stops and reports which stage failed. |

All scenarios must pass on Linux, macOS, and Windows (WSL) without altering this spec.

---

**End of specification**
