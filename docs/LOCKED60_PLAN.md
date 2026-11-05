# Locked 60 plan

Binding plan, written 2026-11-03. It replaces section 6 of [PERFORMANCE.md](PERFORMANCE.md). The steps, their order and the targets do not change.

Tags: [MEASURED] comes from a log or script, [ESTIMATE] is my judgement and may turn out wrong.

## Where we are [MEASURED: logs vs1, vs2, vs4, pf1 and cpu_per_frame, boost mode]

| Thread | CPU-ms per frame | PCSX2 at 60 FPS | Target |
|---|---|---|---|
| Vif1Worker | 17.4 | 7.0 | 12 or less |
| GsWorker | 14.9 | 6.9 | 12 or less |
| GameThread (EE) | 11.4 | 11.1 (also does VIF parsing) | 12 or less (already met) |
| PresentLatch | 3.5 | none | |
| MainLoop and other | 2.1 | 0.2 | |
| **Total** | **49.3** | **25** | **25 or less** |

- **Levels:** the median frame is already 16.7 ms, but p99 is 20-25 ms.
- **Shop:** the median is 20-21.6 ms and p99 is 25-36 ms. This is the worst scene measured.
- **Hitches:** 14 of the 105 windows in `vs1` (5 s each, startup included) contain a frame over 150 ms. Other windows have a p95 of about 33 ms, meaning runs of doubled frames.

## What "done" means

**Part A, locked 60 with headroom.** All of these, in boost mode:

1. Vif1Worker, GsWorker and GameThread are each at 12 CPU-ms per frame or less in the shop.
2. Shop and a full level: p99 at 17.5 ms or less, and no frame over 20 ms outside a scene load.
3. Silent mode holds 60 FPS in the shop. Silent mode stretches these threads by 1.27-1.40x [MEASURED], which is why the limit is 12 ms: 12 x 1.40 = 16.8.

**Part B, cheaper than PCSX2.** Total CPU is 25 CPU-ms per frame or less at 60 FPS in the shop, in boost mode.

**How every result is measured:** the same standing spot in the shop, in boost mode, with `tools/cpu_per_frame.ps1` and the `[ft]` line. Repeat runs at this spot agree closely (VIF time 875-882 ms per second in `vs1`).

## The steps

### Part A

**Step 1. Thread placement (no code at first).** Run the game limited to one logical CPU per physical core (affinity mask `0x5555`). If the frame time improves, build the placement into the runtime. PCSX2 ran with thread pinning on; we have never tested it.

**Step 2. Test a profile-guided build of the runtime.** The runtime already uses `/GL` but has never had MSVC PGO. Earlier PGO tests covered guest code only. Do one training run and one optimized build. Keep it only if Vif1Worker or GsWorker improves by 5% or more. If kept, it becomes the last build step before every acceptance test.

**Step 3. Vif1Worker to 12 ms or less**, in this order:

| | Work | Measured cost | Estimated saving |
|---|---|---|---|
| a | Move the `lb*` kernels out of the "generated" file, and confirm the generator reproduces the rest | | none (a regeneration would delete them today) |
| b | `lbFull`: drop status tracking and per-op checks on the 6 ops whose flags nothing reads, and store fewer intermediates | 4.2 ms | 1.5 ms |
| c | Closed-form kernel for the `0158` loop | 1 ms | 0.8 ms |
| d | Register residency in the top 14 hot blocks, which are 71% of hot-block time | 3.4 ms | 1.4 ms |
| e | GIF hand-off: one copy instead of two | 1.3 ms | 0.5 ms |
| f | UNPACK and parse per-call floor | 4 ms | 0.8 ms |

Estimated result: about 12.4 ms before any PGO gain. This is the tightest number in the plan.

**Step 4. GsWorker to 12 ms or less**, in this order:

| | Work | Measured cost | Estimated saving |
|---|---|---|---|
| a | Drain the packet queue in batches. Today there is a queue lock and a pool lock for each of about 410,000 packets per second | up to 1 ms | 0.8 ms |
| b | Fast path for common packets (`vertexKick`, `processGIFPacket`, `writeRegisterPacked`) | 5.1 ms | 2 ms |
| c | Cheaper `UploadImage` | 2.8 ms | 1 ms |
| d | Merge draws, within the ordering rules | 3.5 ms | 1 ms |

Estimated result: about 10 ms.

**Step 5. Hitches and doubled frames.** Find what causes the 150+ ms frames and the 33 ms runs. Check the same moments in PCSX2 first, because some may be the game's own loading. Fix everything that PCSX2 does not also show.

**Step 6. Acceptance test for Part A.** Rebuild (with PGO if kept) and check all three conditions. Part A is finished only when all of them pass.

### Part B

Estimated total after Part A: about 40 CPU-ms per frame, before any gain from steps 1 and 2. Steps 7-9 are estimated to remove about 11, which leaves about 29, so **these estimates do not reach 25**. Step 10 says what closes the gap. This is the least certain part of the plan.

**Step 7. Direct geometry path.** Kernels hand finished vertices straight to the backend, skipping VU memory, XGKICK, the GIF queue and parsing. Start with `lbFull`, then widen to other routines. First, one probe finds which output words are read back later; those writes stay. A check mode compares the direct vertices with the old path on the same frame. Estimated saving: 5 ms across both workers.

**Step 8. EE code generation**, as in [CODEGEN_PLAN.md](CODEGEN_PLAN.md). Estimated saving: 3 ms.

**Step 9. Present straight from Vulkan**, removing the CPU copy and the OpenGL upload. Estimated saving: 3 ms.

**Step 10. Acceptance test for Part B**, as defined above. If the total is still over 25, the direct path moves its vertex math to a GPU compute shader (about 4 ms of CPU today), checked by image comparison against the CPU path. That is the only allowed extension. It would make that geometry match by image rather than by exact bytes, and I will ask you before it starts.

## After this plan

The agreed order stays: crashes and visual glitches next (the `vs1` crash and the shop flicker P362), then geometry blending, then a higher game tick rate if blending fails.

## Rules

1. **Order is fixed.** No step starts before the previous one is finished, and none is skipped.
2. **Targets are fixed.** A target is never relaxed to declare a step finished.
3. **A step that saves less than estimated still gets finished.** Keep the gain, log the real number and move on.
4. **A thread still over target after its step** goes back to the same ranked list: the next hot blocks and the next kernels. No new kind of work is added.
5. **New ideas wait.** They go in a list and are looked at only after step 6 or step 10.
6. **Measurement only where a step needs it.** One run checks one step.
7. **Correctness.** Each change sits behind a default-off switch until it is verified, using `PS2X_PRESENT_GPU_VERIFY`, the VU1 verifier or corpus replay, whichever applies. Flags may only be dropped where no reader exists. Bugs get fixed, and the step stays in the plan.

## Decided against

These are closed, so they will not be reopened during this plan:

- **Image-based frame generation:** your decision.
- **Parallel VU1 and splitting VIF parsing onto a second thread:** spreads CPU instead of reducing it, and PERF-VP2 failed. Also rules out **splitting the GS into two threads**, for the same reason.
- **Reusing VU1 output for repeated input:** only about 3.6% of VU1 cycles in the sampled data.
- **Clang or PGO for guest code:** tested, no gain (C290).
- **More probe trimming in the per-run path:** the last round made no measurable difference (P381).

## Results log

- **Step 1 (thread pinning): refuted, closed 2026-11-04.** Affinity mask 0x5555 gave the same frame times (shop p50 20.0-20.1 ms both, p99 24-25 ms unpinned vs 25.7 ms pinned) and the same CPU cost (49.1 vs 49.9 ms per frame). No runtime change. P382.
- **Step 2 (PGO build of the runtime): kept, 2026-11-04.** Vif1Worker 17.4 -> 15.4 ms per frame (-11.7%, two normal runs agree within 2%), GsWorker unchanged, steady shop frame p50 20.1 -> 18.2 ms. Measured with the GPU present accidentally off in the PGO run, so the real gain is probably larger. P383. Use the GEN -> train -> USE cycle for acceptance builds (steps 6 and 10); day-to-day builds stay normal. Workflow in memory (project-pgo-build-workflow).
- **Step 3a (kernel block out of the generated file): done, 2026-11-04.** Dry run: vu1_native_exec_0..3 regenerate byte-identical; the dispatch file did not (generator 3,934 lines vs committed 5,960). The 1,885-line hand block now lives in vu/vu1_native_hand.inc (preprocessed code identical to before, 54,204 non-blank lines), the dispatch banner says hand-maintained, and gen_vu1_native.py writes only vu1_native_dispatch.generated.cpp.txt.
- **Step 3 status, 2026-11-04 (built, one build waiting to be tested).** 3a done. 3b built: PS2X_VU1_LBR=1/2 (relaxed lbFull vertex path, =2 verifies against the scalar reference), estimate 0.8-1.0 ms. 3f built: UNPACK probe calls hoisted (about 0.3-0.4 ms), plus the two atomics removed earlier. Measured bounds for the rest: 3c `0158` runs about 1.2M iterations/s at about 41 ns each (49 ms/s), so a kernel is worth 0.6 ms at most and needs a cycle-exact software-pipelined model; 3e needs a direct-to-ring redesign of the GS queue (only 2 copies exist, everything after the arbiter is a move), worth about 0.3 ms; 3d is a generator project (hot blocks already cost about 7 ns per pair). Expected Vif1Worker after 3b + 3f on top of PGO: about 14.2 ms against the 12 ms target. The remaining 2 ms is not reachable by trims; it needs step 7 (direct geometry path) earlier than planned. This is a decision for the user, not applied here.
- **Step 3b measured, 2026-11-05.** Vif1Worker 17.31 -> 16.63 ms (-0.68, steady frame p50 about 1 ms better), verified 38.1M groups with 0 mismatches, default on (PS2X_VU1_LBR=0 disables). 3f about -0.4 ms (noise level). With PGO the projection is Vif1Worker about 14.7 ms and GsWorker about 15 ms: the GS is now the co-limiter, so step 4 is as urgent as the rest of step 3. P384.
