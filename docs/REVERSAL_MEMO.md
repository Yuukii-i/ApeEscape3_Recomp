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
