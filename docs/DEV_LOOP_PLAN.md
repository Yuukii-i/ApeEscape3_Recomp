# Faster development loop

Written 2026-11-09. Goal: make each change-and-measure cycle take seconds to about a minute, not about 12 minutes of your time, while the project works toward a locked 60 FPS with headroom ([LOCKED60_PLAN.md](LOCKED60_PLAN.md)).

## Where the time goes today

**One cycle** is one build plus three runs (A/B/C) of about 3 minutes each. Each run means: boot, intro, title, load the save, walk to the shop, start `cpu_per_frame.ps1`, wait, close, paste. That is about 12 minutes of your attention per cycle, and some cycles have needed a second round because of a wrong env block or exe.

**Build** [MEASURED, `build/.ninja_log`, last incremental build]:

| Step | Time |
|---|---|
| Compiling the changed file | 2.5 s |
| `ps2_runtime.lib` | 21 s |
| Exe link | about 60 s |

The link dominates because the runtime is built with whole-program optimisation (`/GL` + `/LTCG`): every change re-generates the code for the whole runtime at link time.

## The plan, in order

### 1. Fast dev build (small change; target: edit to runnable exe in about 20-30 s)

- New CMake switch `PS2X_DEV_BUILD=ON`: the runtime and the exe are built at the same `/O2` optimisation, but without `/GL` / `/LTCG`, and are linked incrementally. Release and PGO builds stay as they are for acceptance tests (LOCKED60_PLAN steps 6 and 10).
- `tools\build.bat` gets a `dev` mode that uses all cores at normal priority (today it uses half the cores at below-normal priority, so the machine stays usable during the long builds).
- **Check once:** how much slower a dev build runs than a release build. A/B comparisons stay valid as long as both sides use the same build type. The real number counts only at acceptance builds.

### 2. One-command benchmark (target: one command, nothing to paste)

- **In-game bench mode** `PS2X_BENCH=<seconds>`. On a hotkey (F9), or automatically once the input script below reaches the shop, the game measures for that many seconds:
  - per-thread CPU time (the same numbers as `cpu_per_frame.ps1`, measured inside the process)
  - frame-time percentiles
  - VIF and GS counters

  It writes `logs/bench_<tag>.json` and closes itself.
- **`tools\ab.ps1`** runs exe A and exe B alternately (A B A B), with the env block built in, so no more forgotten variables. It prints the comparison table, including how much the two A runs differ (the noise). I read the JSON files directly, so you paste nothing.
- **Getting to the shop:** extend the existing `PS2X_INJECT_PAD` (time-based button presses) into a script file that goes from boot through the menus to the shop on its own. This only works if the game is deterministic enough on the same timeline, which must be tested. The fallback is that you walk to the shop and press F9, which still removes everything else.

### 3. Offline replay benchmarks (target: most performance work without starting the game; I can run these myself)

Record a few seconds of the shop once, then replay the recording through the same runtime code in a small tool, without the game.

- **VIF1/VU1 replay.** Record the VIF1 jobs of about 300 frames plus the starting VU state (memory, registers, microcode). `vif_replay.exe` runs the real worker code on them and reports:
  - ms per frame for the worker
  - a hash of the GIF packets it produced, which is the correctness check
- **GS replay.** Record the GIF packet stream; a GS dump writer already exists (`[probe] fv gsdump`). `gs_replay.exe` feeds it through the Vulkan backend with no window and reports:
  - ms per frame for the GS thread
  - a hash of the final framebuffer
- **Why this helps:** deterministic, so no noise from playing; seconds per run; and I can measure, find a mistake and fix it in one sitting without you. Every change to the two limiting threads (LOCKED60_PLAN steps 3 and 4) can be tested this way first. The in-game bench (2) then only confirms the result at the end of a batch.
- **Limit:** a recording covers what the recorded scene does. A level and the shop need separate recordings, and the in-game run stays the final word.

### 4. How we work with it

- I iterate on the replay tools until a change is correct (same hashes) and faster. You then do one dev build and one `ab.ps1` run per batch. Acceptance builds (PGO) only at the plan's acceptance steps.
- Typical cycle afterwards: under 1 minute for me per offline iteration, and about 5 minutes per batch for you (one build plus one unattended script).

## Your decision needed

**One rule changes.** Today the project rule (CLAUDE.md, token rule 1) is that I never build or run anything; you do. Step 3 only pays off fully if I may build and run the **replay tools** myself (small console programs, not the game; output is a few lines). The game exe itself would stay yours to run.

## Order and size

| Part | Size | Payoff |
|---|---|---|
| 1. Fast dev build | Small (CMake + `build.bat`) | Build drops from about 1.5-3 min to about 20-30 s (estimate, to be measured) |
| 2. Bench mode + `ab.ps1` (+ F9 start) | Medium | Runs become unattended; no pasting, no wrong env |
| 2b. Scripted path to the shop | Medium, uncertain (determinism) | Fully hands-off runs |
| 3. VIF1/VU1 and GS replay tools | Large | Most iterations in seconds, without you |

I would do 1 and 2 first, because they help immediately, then 3.
