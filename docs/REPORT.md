# Task LC Report: Bench Marker + A/B Script

- `Pad.cpp`: Replaced all `std::fprintf(stderr, ...)` in record/replay code with `::ps2xSafeLog(...)` followed by `std::fflush(stderr)`.
- `Pad.cpp`: Added `[bench] START poll=N` marker via `::ps2xSafeLog` + `fflush` when replay first reaches the end of records.
- `tools/ab.ps1`: Implemented PowerShell 7 A/B benchmarking runner supporting `-ExeA`, `-ExeB`, `-EnvA`, `-EnvB`, `-Pad`, `-Seconds`, `-Rounds`, `-Tag`, `-Fps`.
- Clean slate environment: captures and clears existing `PS2X_*` vars, applies standard async/vulkan/pad settings, applies side envs, and restores on exit.
- Process lifecycle: launches exe in repo root with output redirected to `logs/ab_<Tag>_<side><round>.out/.err`, polls for `[bench] START` (max 300s).
- Settle and CPU snapshot: waits 3s after marker, records per-thread CPU time over `-Seconds` using Win32 `GetThreadDescription` (same as `cpu_per_frame.ps1`), forces process exit.
- Metrics parsing & aggregation: extracts post-START `[ft]` p50/p99 medians, maps named threads (GameThread, Vif1Worker, GsWorker, PresentLatch, MainLoop, other, TOTAL).
- Output: prints compact comparison table with side means, diffs (ms & %), and noise `|A1-A2|` (p50, vif, gs), saves to `logs/ab_<Tag>.txt`, and outputs copy-friendly one-line summary.
