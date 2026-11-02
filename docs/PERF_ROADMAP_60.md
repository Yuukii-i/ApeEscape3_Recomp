# Road to a locked 60 fps (shop = worst scene) — measured 2026-11-02

Shop scene, 30 fps => ~33 ms/frame. Per frame:

| thread | cost/frame | share | what it is |
|---|---|---|---|
| VIF1 worker | ~30 ms (10.5 s busy / 352 frames) | 93% busy | ~12k VU1 programs x ~2.5 us (replay: 2.5 us/call avg). Kernels (skinFull, vert, copy) ~45% of it, ~200 hot blocks the rest |
| GS thread | ~23 ms (77% busy at 30 fps) | | ~45k prims/frame (15.6M draws per 11.5 s window), ~500 ns/prim all-in |
| EE | ~5.5 ms + waits | idle ~55% in the fence | not the limiter |

60 fps needs every pipeline stage <= ~15 ms: VU1 worker 2x, GS thread 1.5-2x. Single-thread exact micro-optimisations give ~5-10% each
(PERF-FT/SV: skinFull -24% on the snow corpus, live fps unchanged). They are worth doing but cannot reach 60 alone.

## What was ruled out
- clang-cl instead of MSVC for the VU1 TUs: same instruction count and memory ops per block (vuH_14: 583 vs 572 ins, 233 vs 200 mem). No gain.
- Parallel VU1 programs: calls are chained through registers and memory words 1022/1023; needs read/write-set tracking, not blind-safe.
- Run-ahead EE (sb3): bounded lag gave nothing and reset animations.

## Plan (in order)
1. GS front-end fast path (target GS 23 -> ~10 ms): GIF packet -> vertex buffer directly for the common PACKED/REGLIST prims, one state compare per run
   (PERF-GR already removed the per-prim state copy and lock: GS thread went from queue-bound to 77% busy), then merge runs in the Vulkan backend into
   one draw. Exact by construction; verify with the GS dump compare.
2. VU1 functional mode for the dominant programs (skinFull 1FE0, vert 2440/1CC0, copy 0C80): compute outputs only, skip per-op flag/ready-time bookkeeping
   where the microcode never reads it (STATUS never read; MAC ring only at KEEPMAC pairs). Verifier = existing corpus replay VERIFY=3, cycle count modelled in closed form.
   lbVert next: 3.5 us/call, same SoA treatment as PERF-SV (8 vertices per step).
3. Hot blocks: vf/vi register residency per block (locals instead of st.vf[]), generator patch; expected 1.3-1.6x on the ~55% that is not kernels.
4. Only then: native draw-list path (VU1 output -> GPU vertex data without GIF round trip): needed anyway for widescreen, resolution scaling, 144 fps, phone.

Rule: every step exact (replay 0 mismatches) or behind an env switch with the old path as fallback; measure with [wait] vif1_worker_busy and [gsq] busy.
