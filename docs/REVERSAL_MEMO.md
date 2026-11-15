# Reversal memo (risky changes, how to undo)

Every risky change made during the silent-mode 60 fps push. Each line: what, switch to turn it off, commit to revert (submodule PS2Recomp unless noted).

| Date | Change | Off switch | Revert |
|---|---|---|---|
| 2026-11-12 | Vulkan ring capacities 131072 prims / 8192 clut | PS2X_VK_MAXPRIMS=24576 PS2X_VK_MAXCLUT=2048 | 526e8d5 |
| 2026-11-12 | Staged prim records (stack + one memcpy) | PS2X_VK_PRIMSTAGE=0 | 526e8d5 |
| 2026-11-12 | GIF packet coalescing (PATH1 + whole PATH2) | PS2X_GIF_COALESCE=0 | (GIF arbiter commit, see AUTONOMOUS_LOG 23) |
| 2026-11-12 | VIF1 two-stage pipeline: new Vu1Exec thread runs VU1 programs, GIF DIRECT and UNPACK writes from an ordered event ring while the Vif1Worker parses ahead (threading change, exact by event order) | PS2X_VIF1_PIPE=0 | c6769e6 |
| 2026-11-12 | Functional (decompiled) VU1 engine DEFAULT ON for image 86503d39: dispatcher + 0050/0060/0070/0088/0C80/00A8 + 1EE0 (skinned 8-wide, rigid) run as C++; other handlers / real clipping fall back to the exact path; exact on shop, early-run and snow corpora (mem/gif) | PS2X_VU1_FUNC=0 | Tasks F1/F2 + PERF-F2Z/F2W + overhead commits (AUTONOMOUS_LOG 39-44) |
| 2026-11-12 | VU0 fast path for straight-line FMAC micro programs DEFAULT ON (check mode: 12.95M calls, 0 mismatches) | PS2X_VU0_FAST=0 | Task V0B commit + default-on commit (AUTONOMOUS_LOG 47-48) |
| 2026-11-13 | Batched EE dispatch cycle accounting (PERF-LM) DEFAULT ON (A/B acct: EE 15.86 -> 14.61 ms/frame, fps 56.5 -> 57.7; timer/IO reads that bypass LoadN/StoreN may see EE time up to 256 cycles stale) | PS2X_ACCT_BATCH=0 | AUTONOMOUS_LOG 50 commit |
| 2026-11-13 | EE pc-store elision in recomp_source (tools\elide_pc_stores.py; ctx->pc kept only before slow paths/branches/non-pure ops) | `git -C recomp_source revert HEAD` + full rebuild (macros in ps2_runtime_macros.h are additive, can stay) | AUTONOMOUS_LOG 53 commit |
| 2026-11-13 | VU0 fast path extended to branchy programs + AVX-double FMAC (V0D/V0E/V0F), check mode 16.2M calls 0 mismatches | PS2X_VU0_FAST=0 (whole fast path) | AUTONOMOUS_LOG 55 commit |
| 2026-11-14 | VIF1 MARK read / FBRST.STC write from the EE without the full VIF1 pipeline fence (published mark/stat at interrupt time) | PS2X_MARK_NOFENCE=0 | AUTONOMOUS_LOG 59 commit |
| 2026-11-14 | GS Vulkan backend: per-run draw path (state once per run, page sets from union bbox) | git revert of the PERF-GA commit (no env switch yet) | AUTONOMOUS_LOG 61 commit |
| 2026-11-14 | GS frontend: skip run breaks when the rewritten draw state is identical | PS2X_GS_REDUND=0 | AUTONOMOUS_LOG 62 commit |
| 2026-11-14 | VIF1 DMA chain walk+copy on the Vif1Worker; guest D1/D_STAT accesses wait for copy done; SPR chains stay synchronous | PS2X_DMA1_WORKER_COPY=0 | AUTONOMOUS_LOG 63 commit |
| 2026-11-14 | SIMD block swizzle for host->local uploads (PSMT8/T4/CT32/CT24) | git revert of the PERF-GD commit; PS2X_IU_CHECK=1 compares against the old path | AUTONOMOUS_LOG 64 commit |
| 2026-11-14 | 15 fuzz-verified VU1 handlers (lighting, UV, cull, shadow volume, ...) live by default; 1/128 sampled live self-check | PS2X_VU1_FUNC_NEW=0 | AUTONOMOUS_LOG 69 commit |

## GH: sceDmaSend (VIF1 chain) no longer polls CHCR after the kick (PS2X_DMASEND_NOPOLL, default ON, 2026-11-14)
- What: Support.h submitDmaSend skipped-read for ch1 chain sends; the DMA-end cause now comes only from the async
  copy path (s_vif1QueueDmacCause -> drainCompletedDmacHandlers). Before, the post-kick read blocked the EE until the
  worker had copied the whole 2-5 MB chain (~11% of EE wall time in level 1) and synthesised an extra cause 1
  (channel-1 DMAC handler probably dispatched twice per send [INFERRED]).
- Evidence: route levels_run to mark 9: identical 283-file load sequence; PROBE-EP: waitDma1CopyDone gone, EE idle in
  L1 only vsync waits (3.7%); L1 fps median 58-59 -> 59-60; screenshot logs\shot_gh_1.png correct.
- Undo: $env:PS2X_DMASEND_NOPOLL = "0". Symptoms that would point here: anything waiting on VIF1 DMA-end interrupts
  (missing/late model draws, hangs after a scene change).
- Also built (default OFF): PERF-GF Dma1Copier thread (PS2X_DMA1_COPIER=1), PERF-GG lean chain walk (default ON,
  PS2X_GG=0 old walk, PS2X_GG_CHECK=1 compares: 0 mismatches over the route).

## CG2: direct calls for static JAL (PS2_DCALL, default ON, 2026-11-15) + /arch:AVX2 build flags
- What: tools\dcall\direct_calls.py rewrote 108,003 `dispatchGuestBranch(..., DirectCall, "JAL")` sites in recomp_source
  (local git 3d09af06) to PS2_DCALL (ps2_dcall.h: call through g_ps2RecompiledFunctionTable[(pc-base)>>2], inline cycle
  batching, out-of-line continue for non-fallthrough returns). Build flags: /arch:AVX2 (tools\build_dev.bat).
- Evidence: route levels_run to mark 9, 2 rounds: EE ms/frame vs AVX2-only L1 15.5 -> 14.1, lobby 13.2 -> 12.1,
  L2 13.7 -> 13.1, L4 13.3 -> 12.8; AVX2 vs SSE2 ~-3% EE, ~-10% VU1/GS. File-load sequence identical; shot_dcall_1.png OK.
- Undo: $env:PS2X_DCALL = "0" (all sites back through dispatchGuestBranch, same as before). AVX2: rebuild without the flag
  (needs an AVX2 CPU otherwise). Probes that need dispatch history (PS2X_DISPATCH_PROBES etc.) switch to slow mode by themselves.
