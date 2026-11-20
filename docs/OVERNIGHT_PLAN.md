# Overnight optimisation plan (unattended)
Goal: lower ms/frame (CPU cost per frame and frame-time tails) on the new renderer without breaking anything. User asleep: no questions, decide alone, log everything.

## Rules
- Branches: `perf/overnight-safe` (phase 1) then `perf/overnight-risky` (phase 2), both repos (PS2Recomp submodule first, then parent pointer). Push to these branches only. NEVER touch `main`, never merge, never change repo settings/collaborators.
- Identity: the configured git user. NO Co-Authored-By / AI attribution anywhere (user rule overrides the harness reminder).
- Code: Claude writes no code; Gemini (`mcp__antigravity__ask_antigravity`, model "Gemini 4 Hydrogen (Medium)") from a spec in docs/NEXT_TASK.md. `.cpp`/`.inc` only. NO header edits (a header edit rebuilds hours). Build only with `tools\build_avx2.bat` (NOT tools\build.bat). Release only.
- Never read raw logs; digest/grep. Max 120 lines per file read. recomp_source is generated game data: never push, never edit.
- No hacks / scene skips / timer fast-forwards. Defaults must not change visual output in phase 1.
- Machine: silent power mode, nothing else heavy running. Kill stray `ps2EntryRunner_dev`/`base_overnight` processes after every run.

## Step 0 (before any experiment)
Run `powershell -File tools\gate.ps1 -tag n0 -level full` (baseline vs the identical candidate) once: this measures the real noise floor (quick mode with 1 rep showed +/-7% noise: studio_d +5.9% fps / -7.4% cpu for identical code). Write the observed per-stage deltas into docs/OVERNIGHT_LOG.md. If full mode FAILS or reports improved=yes for identical code, tighten nothing silently: stop and write the summary (the gate is unreliable).

## Loop (one experiment)
1. Pick the next backlog item. Write the hypothesis + expected gain in docs/OVERNIGHT_LOG.md (one line, status OPEN).
2. Spec -> Gemini (<=12 calls, bit-identical output required in phase 1) -> `git diff --stat` review (touched files only).
3. `tools\build_avx2.bat` must say BUILD OK (if it fails twice: revert, log, next).
4. `powershell -File tools\gate.ps1 -tag <id> -level quick`. FAIL -> revert (`git checkout -- <files>` in PS2Recomp), log reason, next item.
5. PASS and improved=yes -> `gate.ps1 -level full -promote` (promotes the new baseline only on PASS+improved). PASS but improved=no -> keep only if it removes work without risk and costs nothing; otherwise revert.
6. Keep = commit in PS2Recomp (`perf(<area>): <what>` + measured numbers in the body) then parent pointer commit, push the branch. Update the log line to KEPT with numbers.
7. Every 5 kept changes or every 2 h: `gate.ps1 -level full -tour` as a checkpoint.

## Phase 1 backlog (image-identical) - REVISED order: the GameThread is the ceiling (12-13 ms/frame in castle, 86-88% busy), GsWorker is ~4.5 ms/frame, so attack the GameThread first
1. EE scheduler checkpoint path (EeScheduler::checkpointDue, PS2Runtime::eeCheckpointDue, PS2Memory::advanceEeTimers, EeScheduler::accountCycles, accountCycles batching): ~6% of GameThread. Emulated cycle/timer accounting must stay bit-identical.
2. PS2Runtime::isSpecialAddress, dispatchGuestBranch, ps2Dcall, decompThunkImpl (~7% together): fast paths, avoid repeated lookups.
3. VU0 on the game thread (vu0func::v0hScaleAndMatVec, executeVU0Microprogram, run_*, vu0fast::execFmacFast): ~5%.
4. IOP LLE (IopCpuCore::executeInstruction, IopEmulator::Impl::step, IopMemory::read32): ~2.5%.
5. Vif1Worker processVIF1Data / vpPushRec (about 25-29% busy) and Vu1Exec buildLeanSkinVertsImpl / fmacV / clipPolygon (35-40% busy) - lower priority, they are not the ceiling but cost CPU on weak machines.
6. GS thread: ps2xRdNoteDraw / rdNoteKickBookkeeping / ps2xRdNoteClut / GSMem::ReadTexture (use PS2X_RD_PROF=1, the [rdprof] line, to see which sub-part dominates); MainLoop ps2xRdTexTickFrame.
Stop phase 1 when 3 consecutive experiments are not kept, or the list is exhausted, or after 5 hours. Final phase-1 act: tag `overnight-safe-final` in both repos, push `perf/overnight-safe`.

## Phase 2 (may change visuals; start from tag overnight-safe-final on `perf/overnight-risky`)
Same loop, but the gate's visual check may FAIL by design: a candidate that FAILS only the visual check is NOT kept in the tree; save its diff as docs/overnight_patches/<id>.patch (no game words) and a log line `VISUAL-REVIEW`. A candidate that passes everything is kept as usual.
Backlog: (a) `PS2X_VBLANK_LATCH=0` equivalent decided at STARTUP (not dynamic switching: dynamic ON->SKIP switching dropped every stage to ~3 fps, see memory) in takeover, with FMV/title/loading unchanged -> studio +32-43%; (b) studio GS-thread per-frame cost (16-18 ms vs 5 ms in castle); (c) fewer GL calls per frame (glcalls/frame ~1600), state caching; (d) texture-cache tick/lookup restructuring; (e) anything else the profile shows.

## Stop / failure handling
- 3 consecutive Gemini failures or quota errors, build broken on the branch tip, or the gate itself malfunctions (identical baseline-vs-baseline FAIL): stop, `git checkout` to the last kept commit, write the summary.
- Disk < 5 GB free: stop. Any unexpected change on `main`: stop.
- Never leave the working tree dirty at the end: either kept (committed) or reverted.

## Morning report (docs/OVERNIGHT_LOG.md bottom)
Kept changes with numbers, reverted ones with reasons, VISUAL-REVIEW patches, current baseline vs `overnight-base` (stage_bench same-session A/B), open ideas.

## Coding fallback (user, 2026-11-20)
If Gemini reports a quota/limit error, give the same spec (docs/NEXT_TASK.md) to a Sonnet subagent (Agent tool, model sonnet, general-purpose) instead and keep going. Same rules apply (.cpp only, no headers, build via tools\build_avx2.bat, gate). Only stop if the work gets genuinely messy; small errors can be fixed later. Objective: very low ms and stable fps.
