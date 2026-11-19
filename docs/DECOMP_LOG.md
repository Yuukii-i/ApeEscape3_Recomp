# Graphics decomp log (started 2026-11-17)

Objective (user): every graphics call as readable C++ we can build on (lighting overhaul later). Bosses, second half of the
last level and minigames are deferred (not in the corpus).

## Corpus
logs/vu1corpus_full.bin (2.87 GB, 139,074 runs, ~1 h of all levels; inputs logs/capture_full.padrec).
| image (FNV, runtime) | sha1 (corpus.py) | startPCs (runs) | role |
|---|---|---|---|
| 86503d3905e35276 | f3402d53ddebf8af | 0008 36635, 0040 1707 | hub/shop/menus; vu1_func.inc engine, ~99.9% functional (fb 01C8 only) |
| 38aed21fa6906cf0 | 8a7c544d94a1866a | 0008 96353, 0040 4339 | in-level; = 86503d39 except 8 handlers (C453) |
| 4020410124328442 | e36760f92ee290c5 | 0000 11, 04A0 5, 0A18 22 | rare full-screen jobs (36k cycles each at 0000) |
| d6b2281aa7efd05a / 4279fa213443af76 | 5e5df851 / bb8db7f0 | 1 run each | one-offs |
Note: runtime image hash = FNV-1a64 with the non-standard basis 1469598103934665603.

## Plan
1. BE: per-handler code signatures -> functional engine runs on 38aed21f for the shared handlers; per-image coverage line.
2. Measure live coverage on level replays (slow1..5) -> list of fallback handlers by count.
3. Decompile the 38aed21f variants of 0198 02E0 0560 0628 0AE0 0B38 0C38 0CC0 (only those used), then 01C8, 3480, 3890, then
   image 40204101 (0000/04A0/0A18). Verify each: PERF-VNC live self-check + corpus replay.
4. Readability pass: every handler as a named C++ function with semantic inputs/outputs (docs/VU1_HANDLER_FORMS.md), then the
   EE packet builders that feed them (data model).

## Progress
- 2026-11-17: corpus checked; image map above; BE spec written (docs/NEXT_TASK.md, sigs docs/BE_sigs.txt).
- BE built: per-handler code signatures (vu1_func.inc kHandlerSigs). slow1 replay (logs/be_slow1.err): 38aed21f 6.72M programs
  all functional, 0 fallback; 86503d39 3.27M all functional; d6b2281a 267 functional. The 8 differing level handlers are not used there.
- BF built: entry 01C8 (= 0198 body without its dead prologue) + 0198 prologue live-out valid bits. Hub replay fb now only 0640 (8).
- Corpus replay needs files < 2 GB (runtime uses 32-bit ftell): split per image (scratchpad split_corpus.py) ->
  logs/vu1c_level.bin (98519 runs, 1.8 GB) and logs/vu1c_hub.bin (38342 runs).
- FINDING: REPLAY_FUNC mismatches mem on ~70% and GIF on ~50% of records (both images; also on the pre-BE exe, so old),
  exact interpreter 0 mismatches. PROBE-BG (mismatch detail + handler trace) in progress.
- C454: replay mismatches = rounding mode (functional engine on the async VIF1 worker runs round-to-nearest). Fix BH in progress. Lesson: every functional/native VU path must set MXCSR RZ itself.
- BH built: replay mismatches 70% -> hub 3/38342, level 33/98519. BI built (entry 0640 = 0628 body): 0 fallbacks on both corpora.
  => every VU1 program of the hub and in-level images in the 1 h corpus runs as C++ (vu1_func.inc).
- C455 traced to clipPolygon spill of vf13 (colour) z lane at the rigid2440 call (~1458); can give alpha 0x100 -> transparent
  vertex. Task BJ in progress.
- The 43 'differing' pairs of image 38aed21f are leftovers of the full-screen program (image 40204101, 0000-0E00) in dead
  prologue slots. 40204101 = particle/billboard program (RINIT/RNEXT jitter, I=0.01, 9 XGKICKs), entries 0000/04A0/0A18,
  38 runs/h; corpus logs/vu1c_fx.bin; listing docs/vu1_image_40204101.txt (git-ignored). Next after BJ.
- BJ built: clipPolygon vf13 = clampI(Lit[j]). REPLAY_FUNC: hub 0/38342, level 0/98519 mismatches, 0 fallbacks. MILESTONE: main VU1 images fully functional + bit-exact on the corpus.

## EE side (graphics engine) - started 2026-11-17
- VU1 command words (handler pc/8) are written by EE code: e.g. sub_003BCC50 (0x3BCC50-0x3BD044) stores 0x389 (1C48), then
  0x3DC/0x3DE (1EE0 skinned / 1EF0 UV variant, chosen by movz) next to VIF UNPACK words (lui 0x6003). 0x3DC appears in 18
  functions (cluster 0x176xxx-0x17Bxxx + 0x32A00C/0x32A28C/0x32ABCC + 0x22EFF0 + 0x13395C).
- PS2X_PROF_EE=1 on slow1 (logs/prof_slow1.err, [eeprof] owner): hot guest fns 3BA2A0 (VU0 matrix/skin setup, top), 3BF9A0,
  3BA898, 3B4290, 3BBB50, 3B45E8, 3ABBD0, 3AEF08, 3B4A60, 3AC370, 3B7A00, 3B3820, 3BD690, 3BBF80, 3BCC50 ...
  => graphics engine library = 0x3A0000-0x3C8000 (719 recomp files, 8.8 MB generated source).
- Task BL: tools/ee_render_map.py (static call graph + VIF/VU1CMD/VU0/DMA flags) -> docs/EE_RENDER_MAP.md.
- docs/EE_RENDER_MAP.md generated (tools/ee_render_map.py 3A0000 3C8000). Structure: model-draw dispatchers 3B5048/3B5508 ->
  per-format builders 3B57C0 3B62C0 3B6508 3B6740 3B69D8 3B6CF0 3B6FE0 3B7220 3B7460 (VU1CMD 0x15/0x190 = 00A8/0C80);
  dispatcher 3BB8E8 -> 3BBDC8 3BBF80 3BC278 3BC770 3BCC50; small shared leaves 3BA7D8 (UNPACK header), 3B5890 (DIRECT),
  3AFDD8/3AFE58 (command helpers). ~27 roots called from game code.
- EE decomp method (Task BM): readable C++ replacements via rt.replaceFunction in src/lib/decomp/ee_gfx_decomp.cpp, installed
  after the generated functions; PS2X_EEDC=1 enables, PS2X_EEDC_CHECK=N dual-run check (snapshot ctx+RDRAM+scratch, run
  original, restore, run decomp, compare). Pilot: 3BA7D8, 3B5890.
- BK: fx programs P0/P1/P2 written; BK2 (ilw arg order) -> P0/P1 exact except epilogue Q of the last vertex; P2 declines. BK3 running.
- BK4 built: fx image P2 count 0 + I=6.0 (LOI at 0AA0). REPLAY_FUNC fx 38/38 exact.
  MILESTONE 2026-11-17: ALL VU1 programs in the 1 h corpus (images 86503d39, 38aed21f, 40204101; 136,899 runs) run as C++ in
  vu1_func.inc with bit-exact VU memory + GIF output. (d6b2281a/4279fa21 one-offs: d6b2281a functional; 4279fa21 = exact path.)
- BM built (EE harness, PS2X_EEDC=1, PS2X_EEDC_CHECK=N): pilots 3BA7D8 (DMA REF tag + STCYCL + UNPACK V4-32 header) and
  3B5890 (DMA CALL tag pairs). First check run: every check flagged 'delay' (ctx bookkeeping field, not ABI-visible) -> BN
  restricts the comparison to ABI-visible state (v0,v1,s0-s8,gp,sp,ra,f20-f31,pc,RAM,scratchpad) + per-category counts.
- BN built: checker on ABI-visible state -> 3BA7D8/3B5890 exact (10k checks). BO built: census (PS2X_EEDC_CENSUS=1, top-60 every
  10 s) + batch 1 (9 fns live-exact; 3AFED8/3B2D30 not called in slow1). Census top (150 s level): 3AFD98 1.6M, 3AB950 310k,
  3B3CE0 299k, 3ABA20 273k, 3AB930 236k, 3AF9F8 197k, 3BD498 186k, 3AFDD8 177k, 3BD2F0 174k, 3BDDE0 155k ...
  Workflow per batch: spec -> Gemini (ee_gfx_decomp.cpp only) -> build -> slow1 with PS2X_EEDC=1 PS2X_EEDC_CHECK=50
  PS2X_EEDC_CENSUS=1 (logs/<task>_slow1.err) -> commit when every entry ok == checked.
- BP (batch 2a, 17 tiny helpers + VU0 state in the checker) in progress; 2b next: 3ABDB8 3C1E70 3A9280 3BA090 3AF9C8 3AFA28
  3B9FA8 3BA268 3B1230 3AFE00 3B86A0 3BDC30 3BDC40 3AD018 3B40F8 3B9018 3B2448. Then mid-size (3ABBD0.. 3ACA70, 3BBB50, 3B5508,
  3B7A00, 3B1248) and the per-format model builders.
- BP built (+BP2 noCheck for jalr callers, BP3 time-budget checks: PS2X_EEDC_CHECK=N = N checks/s/function, first 20 always).
  slow1 checked run (logs/bp_slow1.err): replay reaches both marks; 26/27 exact; 3BDDE0 leaves different VU0 scratch regs
  (fix in BQ). Lesson: never check every Nth call of a hot function (32 MB snapshot per check -> 3 fps -> replay desync).
- Run command for checks: PS2X_EEDC=1 PS2X_EEDC_CHECK=5 PS2X_EEDC_CENSUS=1 + standard env + slow1 padrec, 160 s.
- BQ built: batch 2b (14 fns) + 3BDDE0 VU0 fix -> 38/40 entries exact in level play (logs/bq_slow1.err).
  CLOSED EE-1 (harness bug, see BS2): 3B40F8 (allocAndInitDrawCmd, calls 3B3CE0/3B9018) returns v0 0x30 lower than the original (82/83 checks) and
  writes 0x80 at 0xb854b0; 3B9018 writes 0x80 where the original keeps 0 on its first 2 calls. Not a resume-point issue (BQ2
  added resume labels, no change). Suspect: original's direct (CG2) calls into generated callees vs decomp calls through the
  dispatch table, or a counter outside RAM. Both disabled (BQ3) until investigated.
- BR built: batch 3 (10 mid-size: anim sampling 3ABBD0/3ABE60/3ABF68/3AC068, quatSlerp 3AC370, draw-node alloc 3B8448,
  3B8898, 3B9158 cached DMA CALL chain, mat4InvertAffine 3BD538, mat4MulVu0 3BD690) + docs/EE_GFX_DATA_MODEL.md.
  BR2: quatSlerp fixed (qmtc2 keeps all 128 bits of the GPR source). 3B8448 still differs -> disabled (BR3), EE-1 family.
  Active: 47 entries. BS (full diff dump, experimental entries via PS2X_EEDC_EXPERIMENTAL=1) in progress.
- BS/BS2: EE-1 was a CHECKER bug: per-template in-check flag + shared snapshot buffers -> nested checks inside the original run overwrote the outer snapshot. Fixed (single thread_local flag). 50/50 entries exact (1654 checks). 3B40F8/3B9018/3B8448 still gated by PS2X_EEDC_EXPERIMENTAL=1 -> un-gate in the next batch.
- BT built (+BT2 goto/init compile fix, BT3 full-width v0/v1 writes): 63 EE entries exact (1657 checks). Lesson: final ABI regs must use the original's exact write semantics (movn copies 128 bits; v1 leftovers count).
- BU built (+BU2 helper params, BU3 checker ignores [entry sp-64K, entry sp) = dead stack): 66 EE entries exact (1648 checks).
- BV built: census coverage/todo lines + 3ADEC0/3AD0F8/3AD2B0 (GS image/texture upload builders). With them installed the
  game stalls (3 fps) after the level start although their check passed. Cause under investigation (BV2): decompThunk sends
  every resume (ctx->pc != entry) to the ORIGINAL; a decomp whose call-site state differs from the original's breaks when a
  callee yields. BV2: 'resumable' entries resume in the decomp; yield propagation after every PS2_DCALL.
  RULE for all future entries: after each guest call mirror the generated code's yield check (return if ctx->pc != ret addr)
  and support resume at that address.
- BV2 (resumable entries resume in the decomp) + BV3 (PS2X_EEDC_DISABLE=hex,list) built. Bisect: the stall is 3ADEC0 only
  (disable 3ADEC0 -> 60 fps, kicks 3846/s; 3AD2B0/3AD0F8 fine). CLOSED EE-2 (BV6 swapped args): 3ADEC0 (GS image upload builder, 29 guest calls)
  stalls rendering although its one dual-run check passed -> made experimental (BV4). Next for EE-2: force many checks of it
  (it runs ~2/s) with PS2X_EEDC_EXPERIMENTAL=1 + full diff dump, and compare its call sequence (census deltas).
- Final fps of a correct run at the end of slow1 (after mark 2) is 46-61; 3-4 fps / ~268 kicks means broken drawing.
  ALWAYS check the last [fps] line of each verification run, not only the eedc summary.
- BV5: 3AD2B0 fixed (16-QW special case tests width, not remaining qwc; v1 = psm<<56). Normal set 68/68 exact. Coverage (slow1): 325 engine functions called, 68 decomp, 76% of engine calls. EE-2 clue: with decomp 3ADEC0, 3AD2B0 is called 159x instead of ~177k -> 3ADEC0 decomp exits early (suspect PS2_DCALL false 'yield' from ra/fallthrough mismatch).

## 2026-11-18 BW (batch 6a)
- 18 functions + 3ADEC0 promoted to a normal entry. Split piece skipped: 3BD238 (jumps past its end and has a jump table at 0x721618).
- EE-3: 3BAAC0 v0 upper 64 bits: the original returns v0 through movn v0,$t7, and $t7 got all 128 bits from qmfc2 $vf9 in the delay slot at 0x3bab74. Fixed in BW2/BW3. Rule added to the spec: 128-bit moves.
- slow1 checked run: 87 entries, 1747 checks ok, 0 mismatches, 46 fps, 3840 kicks.

## 2026-11-18 BX (batch 6b)
- 17 functions. Split piece skipped: 3ACFB8 (jump table 0x7202C8). noCheck: 3BE940 (jalr).
- Checker fix BX2: the global 20/s cap starved about 20 hot entries (0 checks ever). Entries with fewer than 20 checks now bypass the cap (at most one per 50 ms).
- slow1 checked run: 104 entries, 4146 checks ok, 0 mismatches, 45 fps, 3833 kicks. All entries checked except the 5 noCheck ones.
- OPEN EE-4: the noCheck entries (3ABA20, 3ABE60, 3B8F78, 3B9310, 3BE940) are not verified yet. They need a jalr-safe method, e.g. a call-trace comparison or a stub for the callback.

## 2026-11-18 BY (batch 7: VU1 packet builders)
- 3BC278, 3BC770, 3BCC50, 3BD048, 3C4230, with the helpers emitVu1CmdQwc2/3/4Swapped and emitVu1LightMatrixBlock.
- Fixes:
  - BY2: 3BC278 never wrote v1 (the last write is lui 0x6C00 at 0x3bc50c, plus ori 0x8000 when the count is non-zero). 3BD048 read the byte table at 0x6AA4A0 instead of 0x69A4A0.
  - BY3: 3BC770 type-3/4 items read from the wrong pointer and had their handler IDs swapped (type 3 = 0x321/0x39B, type 4 = 0x320/0x398). emitVu1LightMatrixBlock had 0x3F2 in the wrong half of its header word.
- EE-5 LESSON: 3BC770 passed all 20 sampled checks but broke the replay (about 1000 kicks), because the type-3/4 items are rare and no sampled call hit them. The kicks/fps gate caught it. A replay reaching about 3800 kicks is a mandatory acceptance gate. TODO: a per-entry exhaustive check mode (PS2X_EEDC_ONLY=addr, check every call) for the big builders.
- slow1 checked run: 109 entries, 4230 checks ok, 0 mismatches, 46 fps, 3840 kicks.

## 2026-11-18 BZ/CA/CB (exhaustive mode, batch 8, EE-6)
- BZ: PS2X_EEDC_ONLY=addr,... checks every call of the listed entries; nothing else is checked. It is slow (about 4 fps) and only covers the early game.
- CA2: in 3BC770 the movn $s4,$s6 copies all 128 bits and the ld restores only the low 64, so $s4's upper half leaked to the caller (265/12202 calls; found by exhaustive mode).
- CA: 3BB8E8 (dispatcher), 3BBF80, 3BBDC8, 3B8CC8, 3BE658, 3AF6F8, 3B94F0.
- CA3: 3BBF80 is missing its back-edge checkpoints (eCheckpointDue); loop state moved into guest registers; mult LO/HI.
- CB = EE-6: the replay crashed at 0x3abf58 because the 3ABE60 decomp left a different s-reg state at its jalr call sites, and the original code resumed on it after a callback yielded. Rule: at every guest call, live guest state == the original's. 3ABE60 is now resumable. Audited 3ABA20, 3B8F78, 3B9310, 3BE940, 3BBF80, 3BB8E8: they match.
- slow1 checked run: 116 entries, 4472 checks ok, 0 mismatches, 45 fps, 3839 kicks, mark 2 reached.

## 2026-11-18 CC (batch 9)
- 27 functions. Skipped: 3AD09C (split piece that falls into 3AD0AC) and eight one-instruction jr-$ra stubs (3A8B70 3A94B8 3A98E0 3A9570 3A9140 3A9428 3A95E0 3BDAD8). noCheck: 3A85E0.
- CC2: 3C6DA0, 3C6E40 and 3C6EE0 leave v0 = 0x740000 (a leftover lui base).
- slow1 checked run: 143 entries, 4821 checks ok, 0 mismatches, mark 2 reached, 46 fps, 3831 kicks. The exhaustive run of the new entries was exact apart from CC2 and reached mark 2.

## 2026-11-18 CD (batch 10)
- 3A7D08, 3C4360, 3C7D78 (noCheck), 3B3470, 3B4178, plus 3C5770 (gated).
- OPEN EE-7: the 3C5770 decomp (boot-time busy-wait loop at 0x3c5810 with a checkpoint back-edge; writes 0x69a51c and the uncached 0x20000000 address) stops the game from starting. On its first check it returns pc=0x3c5810 instead of the caller's 0x3c5a80. CD2 fixed some v1 differences but it still fails. Gated experimental (CD3). Not a draw path.
- slow1 checked run: 147 entries, 4834 checks ok, 0 mismatches, mark 2 reached, 44 fps, 3849 kicks.

## 2026-11-18 CE (batch 11)
- 3B9758, 3B5508, 3B4E80, 3B4818, 3BA2A0, 3B3820, 3B81A8 (all resumable).
- CE2: 3B3820 never set v1 (lui 0x1000 at 0x3b3954). 3BA2A0 kept v1 in C++ locals instead of writing it back (0x3ba444/46c/4a8).
- slow1 checked run: 154 entries, 4952 checks ok, mark 2 reached, 46 fps. Exhaustive run of the 7 new entries: 12592 checks ok.

## 2026-11-18 CF (batch 12)
- 26 functions (3B1248 3B76F8 3BAF58 3B3C60 3A9660 3A9670 3A9430 3A9438 3A6D00 3A6D18 3AD050 3B8F58 3A8340 3B8F60 3B9E20 3B94A8 3B9708 3B8FE0 3B9088 3B92E0(noCheck) 3B4088 3A8360 3B85B8 3B7CB0 3ABAA8 3B45E8). Skipped: 3BA71C (split piece).
- CF2: 3B45E8's v0 comes from movz v0,t7 (a 128-bit copy). Checker: a decomp run that ends with pc != entry ra (a yield) now counts as skipped, not compared, because the two runs share the checkpoint budget. The skipped counts have to be watched, since this rule could hide a real wrong-pc bug.
- slow1 checked run: 180 entries, 5623 checks ok, 30 skipped, mark 2 reached, 47 fps. Exhaustive run of the new entries: 12851 checks ok.

## 2026-11-18 CG (batch 13)
- 3BAF88 3BD450 3BE618 3A7620 3B8740 3B8780 3B0AA8 3AF2D8 3B3E28 3B69D8 3B5048 3B4A60.
- CG2: 3B4A60 and 3B69D8 stored the DMA tag address without the 28-bit mask (sll 4 / srl 4), which leaked 0x30 into the tag's top byte (the ID field). The exhaustive run (early game only) missed it; the sampled run caught it.
- slow1 checked run: 192 entries, 5850 checks ok, 48 skipped, mark 2 reached, 45 fps.

## 2026-11-18 CH (batch 14)
- 17 functions (3A7028 3A7040 3A9300 3B2420 3BFE60 3BD3F8 3AEA18 3A7088 3A70C0 3A7898 3AF1B8 3B8A18 3AEEA8 3AF088 3AE900 3BA908 3B62C0). Skipped: 3BA680 (split piece into 3BA71C).
- NOTE: many generated files contain SEVERAL functions (e.g. 3A7898 has entries up to 3A7B88). The census only counts per-file entries, so the true todo list is larger; a sub-entry census is needed.
- CH2: 3B62C0 rewritten one-to-one (its call-site registers and constants were wrong; at 20 fps the replay derailed). 3AEA18's DMA tag had QWC shifted into the upper half. Skip rule: skip only when the decomp and original runs end at different pcs (3BFE60 tail-jumps and had been skipped 1119 times).
- slow1 checked run: 209 entries, 6383 checks ok, 17 skipped, mark 2 reached, 46 fps. Exhaustive run of the new entries: 11545 ok.
- OPEN EE-8: 3B45E8 (batch 12) has 1 of 44 checks differing in v0, VU0, RAM and scratchpad at once (call 53779): a rare path.
- CH3 (EE-8): 3B45E8 now sets the temporary registers t4-t7, a0 and a2 at each guest call exactly as the original. The next run was 44/44 exact (EE-8 likely fixed; it is rare, so keep watching).

## 2026-11-18 CI (full census)
- The function table holds one slot per function plus one per resume/branch label (6895 slots in range). The census now wraps the lowest address of each distinct host function: 816 functions in the engine range, 336 called in slow1, 209 decomped, 127 todo (docs/EE_TODO.md). The hottest remaining are the split pieces, which are now decompiled as entries (CJ rule).

## 2026-11-18 CJ (batch 15: split pieces)
- 24 entries, including the split pieces and sub-entries 3AD018 3B1268 3B2448 3B88B8 3AFE00 3BD238 3AB9F0 3ACFB8 3BA71C 3BA680 3AD09C, which are now decompiled as entries.
- slow1: 233 entries, 6973 checks ok, exhaustive run 12349 ok. A checks-off run reached mark 2 at 60 fps in 70 s.
- OPEN EE-9: one checked run got stuck in a scene (no mark 2). In that run 3AEB90 (batch 9) mismatched once (call 31: v0 is a different pointer, RAM 0x15fbaa0 exp 5 got 0), and the checker keeps the decomp's result. It is intermittent; the next two runs were fine.
- CJ2 (EE-9): 3AEB90 now writes the temp registers (t5-t7, a0) at its call sites like the original. No control-flow difference was found. Next run: 7006 checks ok, mark 2 reached. EE-9 stays watch-only (possibly a checkpoint-timing artifact).

## 2026-11-18 CK (batch 16)
- 19 functions incl. 3BAF98 (552), 3C6F78, 3A8960. Exhaustive run 11983 ok; sampled run 7528 ok. Checks-off runs (full and both halves) reach mark 2 at 52-61 fps.
- EE-9 UPDATE: the 3AEB90 mismatch is DETERMINISTIC (call 31 in every checked run; decomp v0=0x15fba90 every time, the original returns a different block). Checked runs stall in a scene intermittently (1 of 2 here); checks-off runs never do. Next: dump the entry state on mismatch (CL).

## 2026-11-18 CL/CM (checker hardening, EE-9 CLOSED)
- CL: on a mismatch the checker now dumps the entry state (args, pointed-to memory, up to 16 differing bytes with their pre-call snapshot, final pc/v0/v1).
- EE-9 root cause (from the dump): both runs of 3AEB90 call 31 ended at the same loop checkpoint (pc 0x3b4444, inside callee 3B42D0) after a different number of iterations. A checker artifact, not a decomp bug.
- CM (suppress checkpoints during checks) was REJECTED: it made a loading scene crawl at 3-7 fps (a checked function waits on another thread). It is disabled in CM2.
- CM2: if either run ends with pc != ra, the check is skipped. CM3: entries that always end pc != ra (tail jumps 3BFE60 3BA680 3BA71C 3BFED8 3BFDE8) become noCheck after 20 tries; the starved bypass is capped at 20 attempts. Without that cap the game fell to 24 fps.
- Two checked runs: 252 entries, about 7370 checks ok, 137 skipped, 0 mismatches, mark 2 reached both times, 44-46 fps.
- GAP: the tail-jump entries are covered only by the mark-2 gate; they need a tail-aware check later.

## 2026-11-18 CN (batch 17)
- 3BEE20 (noCheck), 3BE9F0 (noCheck), 3C17B0, 3BD270, 3AF3B8, 3BAF78, 3B7DF0.
- slow1: 259 entries, 7493 checks ok, 149 skipped, mark 2 reached, 46 fps. Exhaustive run of the checkable new entries: 11671 ok.

## 2026-11-18 CO (batch 18)
- 24 entries incl. sub-entries 3A83A0, 3B85FC, 3B50B8. noCheck: 3AFF08 and 3B9B00 (Gemini flagged their jr $t5 internal jump tables; these could be checked, TODO), 3B93D8 (jalr).
- slow1: 282 entries, 7881 checks ok, 0 mismatches; mark 2 reached at 170 s (41 fps; checked runs need a 200 s window now). Exhaustive run of the new entries: 11714 ok.

## 2026-11-18 CP (batch 19)
- 3B42D0 3BA5F8 3BAC00 3BD368 3C4008 3C41E8 3B9B50 3AD070 (noCheck: jr jump table, TODO make checkable) 3B9B88 3ADCD8 3ADD08 3AE868 3B6FE0 3B9C20 3AD608.
- slow1: 297 entries, 8241 checks ok, 0 mismatches, mark 2 reached, 46 fps. Exhaustive run of the new entries: 6985 ok, and it reached mark 2.

## 2026-11-18 CQ (batch 20, census tail)
- 36 entries incl. sub-entries and 1-insn stubs.
- slow1: 331 entries, 8861 checks ok, 0 mismatches, mark 2 reached, 46 fps. Exhaustive run: 4870 ok, mark 2 reached. Census: 348 called, 331 decomped, 17 todo: sub-entries that the earlier decomps branch or dispatch into (3B8920 3BA6C8 3BD280 3BA724 3B4AFC 3B0B78 3AB87C 3A7508 3B53DC 3B3890 3B3E7C 3A74A8 3B131C 3AFF44 3C6F88) plus 3C72E8 and 3C7FD0.

## 2026-11-18 CR (batch 21)
- 15 sub-entries. slow1: 342 entries, 8914 checks ok, 0 mismatches, mark 2 reached, 44 fps. Exhaustive run: 12452 ok.
- Census: 351 called, 342 decomped, todo 9 = further dispatch labels (3BA72C 3BA6F4 3BD288 3B3E8C 3B38A4 3B1338 3B4324; the decomps end by dispatching to the generated code's next label) + 3C72E8 + 3C7FD0.

## 2026-11-18 CS + CT/CU (batch 22, precise checker)
- CS: 7 dispatch-label wrappers (3BA72C 3BA6F4 3BD288 3B3E8C 3B38A4 3B1338 3B4324) that route into their parent decomp's resume switch.
- CT: a thread_local g_ps2xCheckpointYields counter (ps2_runtime.cpp, incremented when eeCheckpointDue returns true). A check is skipped only if a run actually yielded (or the thread changed); otherwise everything is compared, including pc. The CM2 pc!=ra skip and the CM3 auto-noCheck are removed. This immediately exposed 3A7BB8.
- CU: run-to-return. After each run the checker dispatches continuation entries until pc == entry ra (cap 256; CU2: hitting the cap or a null slot = skipped). Decomps may now merge the generated code's fall-through or dispatch continuations (3A7BB8 does, and passes).
- CU2: 3AFF08, 3B9B00 and 3AD070 are checkable again (jr jump tables are not calls).
- slow1: 350 entries, 9190 checks ok, 0 mismatches, mark 2 reached, 44 fps.

## 2026-11-18 CV (batch 23)
- Dispatch labels 3BD290 3BA718 3B38B8 3B8A24 3B7E14 3BA60C routed into the parents' resume switches (all cases already present). slow1: 353 entries, 9351 checks ok, 0 mismatches, mark 2 reached, 45 fps. Census: 356 called, 353 decomped; todo = 3BD298, 3C72E8, 3C7FD0.

## 2026-11-18 CW (batch 24) - MILESTONE: slow1 fully decompiled
- 3BD298 (label, routed into 3BD270), 3C72E8 and 3C7FD0 (driver-table dispatchers: validate the driver index 0-7, clamp params, call drv->open / drv->ctrl via the table at 0x69C0B8; noCheck because of jalr).
- Census on slow1: 356 engine functions called, 356 decompiled, todo 0. 9264 checks ok, 0 mismatches, mark 2 reached, 41 fps.
- Verification gaps: 37 called entries have 0 comparisons (15 jalr noCheck; the rest are rare sub-entries whose checks were skipped because of a yield or the run-to-return cap). They are covered only by the mark-2 gate.
- Next: coverage of the other replays (slow2-5), a jalr-safe check, and the gaps.

## 2026-11-18 - full-capture census, CX..DC
- Full 1 h capture (decomps on, checks off): 60 fps, no crash; census todo=59 functions not reached by slow1 (~4k insns).
- CX: PS2X_EEDC_CHECK_JALR=1 checks the 13 jalr entries (opt-in: slows slow1 past the window). 11/13 exact first try.
- CY: 3C72E8 v1 = 44*handle on success path (real bug). 3A85E0: generated code inlines the self-call as goto, so nested
  checked calls (ra in [3A85E0,3A8708)) are cut at the inner jr; checker now skips those (artifact, top-level calls exact).
- CZ (batch 25): 19 functions + 5 sub-entries; slow1 checked exact, mark 2 (186 s; slow1 checked window is now 300 s).
- DA (batch 26): 10 functions incl. 3B5900 + labels 3B8B0C/3A7C2C/3AEF30. DB (batch 27): 25 functions of 0x3A0000 group.
  DC: 3A6B34 is the real body after the 3-insn leaf 3A6B24 (standalone entry, verbatim - readability pass later).
- slow1 checked with DB+DC: exact, mark 2. Pending: full-capture PS2X_EEDC_ONLY runs (logs/czfull_*, logs/dbfull_*).

## 2026-11-18 - checked warp run verA (toyhouse a-c, arabian a-c, snowfesta_c, studio_a, castle_a; ONLY batches 25-27 leftovers)
- 25 exact (3B9D38 2516 checks, 3A0670 557, 3A02D8 410, 0x3A0000 group 102 each, 3B5900 5 ...). 19 not reached here.
- MISMATCH 3A0038 (DB): at a0+0x30 (0x8FA720) original stores 0, decomp stores 0x01FFD560 (= sp-0x100, a stack ptr)
  -> wrong source register in one store. Entry a0=0x8FA6F0 sp=0x1FFD660 ra=0x39FFD8.
- MISMATCH 3A7C20 (CZ label wrapper into 3A7BB8): original returns with s1 = entry s1 (0x1AA4EF8), s0 = 1; decomp
  s1 = entry-0x40, s0 = 2 -> resume case at 0x3A7C20 runs one loop step (s0++, s1-=0x40) too many. ra=0x3A7C2C.
- Exhaustive checks drop fps to ~5 in toyhouse_c/arabian_a (3B9D38 is hot); fine for verification runs.
- verB (batch 28 + DH2 fixes, 15 stages): 15 exact (3A06F8 3361, 3BD26C 876, 3C2A68 685, 3BD2A0 677, 3A7C20 17 fixed ...).
  3A0038 still differs on one path: call from ra=0x391CD8, a0=0x8B48A0 a1=0x71E458 a2=0x1FFD650 t0=0x3E2AAAAA, s0=0
  s3=0x8B40E0 s4=0x3F800000 s5=0x8B48A0: decomp writes word 0x41324000 at a0+0x28, original leaves 0.
  Not verified (not reached or all skipped by yields): 3B9E9C 3B9DB4 3B82C0 3BA154 3B8498 3AEF90 3C2AA8 3C2B88 3C3588
  3C36C8 3C3910 3A5C60 3A1AEC 3A4384 (179 calls, 0 checked: jalr noCheck).
- verC (batch 29, snowfesta e/f/g): 3A3BA8 562/562, 3A1ED4 561/561, 3A07C8 1/1 exact, first try.
- verD (batch 30 + 3A0038 recheck): 3A0038 2/2 exact (DH3 fix). 3A13B4 off-by-one: original writes words 3,4,5 at
  0x8DD270.., decomp writes 3,4 and leaves the third (v0=5 both; entry a0=0x8DC7F0 a1=0x1FFF630 a2=0x72D890 ra=0x3A4630).
  3A2D98 (1448 calls) and 3A2558 (3) never checkable: every call yields at a checkpoint -> needs targeted no-yield checks
  (PS2X_EEDC_NOYIELD, uses the CM g_ps2xSuppressCheckpoint hook only for listed entries; CM rejected only as global).
- verE (sampled, all entries, 5 stages): 398 entries 10945 checks 0 mismatches (confirms DK thunk refactor). 3A4750/3A47F8 exact. verF/G/H/I: 3A13B4 fixed (DL) exact; 3A2D98 needs NOYIELD + CONTMAX=200000 + IGNORE_RAM=0x772720:48 (timer words, EE-10) -> 1271/1271 exact.

## 2026-11-18 - direct render path started (docs/RENDER_DIRECT_PLAN.md)
- Baseline bench (logs/base_on_bench.txt): 60 fps everywhere, 24-46 ms CPU/frame, emulation side ~2/3. PRESENT_GPU: no gain.
- FEAT-BGWIN (PS2Recomp PR #3): PS2X_WINDOW_BACKGROUND=1, test runs open unfocused at the bottom of the z-order.
- R0 already existed (PERF-SA scene buffer). RD1 (recomp/render-direct-r1a, 61de155): PS2X_RD_VIEW=1 draws the scene
  buffer with an own OpenGL pass at window resolution (vertex colour + depth), F11 toggles. Needs PS2X_RD_FLIP=1 (y).
  travel_a/toyhouse_a: ~28-33k tris/frame, geometry matches the GS shots (logs/shots/rd1f1_*, rd1ref_*), 58-60 fps.
  Missing: textures, GS state (blend/alpha test, invisible helper draws show as grey), clipped polys (~210 draws/frame), sky, HUD.
- Next: RD2 = GS state join per scene draw (kick serial), RD3 = textures from VRAM (decode + cache = texture-replacement hook).
- RD2 (22321c3): shadow A+D parser on the VU1 kick path -> per-draw GS state; blend/alpha test/depth applied. Bug found:
  rlSetBlendMode flushes raylib's batch and unbinds our program -> rebind after blend changes.
- RD3 (5d1ae71): textures decoded from the CPU VRAM copy, cached by content hash (future replacement key). This game draws
  with TEX0 CLD=0/CBP=0 (palette pre-loaded into the CLUT cache by other TEX0 writes), so the Vulkan backend notes the active
  CLUT per indexed texture (ps2xRdNoteClut). travel_a/toyhouse_a render textured at window res (logs/shots/rd3c_*).
  Open: sky + near geometry (clip polygons, RD4 in progress), HUD (prebuilt GIF packets, not in scene buffer), some floor
  textures wrong, cost (toyhouse 47 fps with view on, 245 texture decodes/s).
- RD4 (0f970e5): VU1-clipped polygons drawn as fans -> sky and near geometry; hub matches the GS shot.
- RD5 (b82042a): exact per-draw textures. woods_a streams several textures through one VRAM slot per frame -> kick serial
  carried in the GIF stream as a GS NOP (0x7F) write; GS thread notes texture content + active CLUT per kick. Cost fixes
  (PROBE-RDP): CLUT pointer from the instance that loads it (black textures), fast cache by VRAM page generation + CLUT
  generation, CRC32C of raw pages before any texel decode (game re-uploads ~2.7 MB/frame of identical textures):
  noteDraw 18.5 -> 0.45 ms/frame. View ON: toyhouse 41 fps / woods 55 (Vu1Exec +7 ms = scene recording); OFF: 59/59
  unchanged. Visuals match GS shots in woods_a, toyhouse_a, castle_a, snowfesta_f; open: white drop-shadow quads, HUD.
- RD6 in progress: texture replacement by content hash (mods/textures/<hash>.png, any resolution).
- RD6 (17adf4e): texture replacement by content hash (mods/textures/<id>.png, any size; tested 90 x 512^2 in travel_a, 59 fps).
- RD7 (1e3aaad): general PS2 blend formula -> GL blend equations; RD8/9 (8aa1367): 2D capture of non-VU1 GS draws on the
  main colour buffer (game double-buffers: use the FBP of the 3D kick draws), FBMSK colour mask (alpha-only draws blacked
  the frame), real dest alpha for Ad. RD10 (95d6257): VU1 non-geometry kicks (HUD, labels, some scenery) flagged via
  serial bit 30 -> 2D path: travel_a HUD + trees appear. RD11: 2D draws depth-tested via inverse VU1 viewport Z (woods
  canopy silhouettes gone). Open: drop shadows still white, gadget net dark, one intermittent all-black frame
  (rd11_travel_a, not reproduced in 2 reruns), HUD auto-hide makes HUD checks timing-dependent.
- RD12 (fbbd094): PS2X_RD_TAKEOVER=1 skips GS raster + frame readback (PresentLatch gone). RD13 (47be42f): 3D/2D frames
  aligned by GS-thread kick-serial ranges (fixed all-black frames: next frame's clear sorted after this frame's 3D).
  RD14 (2568485): lean capture (28-byte verts + strip indices, vector swap, 4 GPU slots, indexed draws); RD14b fixed stale
  VAO base offset (>64k-vertex frames garbled).
- Same-time A/B 22:01-22:09 (logs/rd14b_bench.txt vs rd14off_bench.txt), CPU ms/frame takeover vs off: travel_a 34.2/37.2,
  travel_b 42.9/43.2, woods 41.9/46.0, castle 37.8/41.3, studio 23.3/29.8, snowfesta_f 26.1/31.1, toyhouse 57.5/54.6
  (54 vs 59 fps), arabian 33.7/39.3, hong 29.8/37.0, space 25.0/29.7 -> ~-4 ms (-11%) avg at window resolution;
  toyhouse regresses (GL driver thread ~9 ms) -> RD15 GL state caching. Cross-session numbers are not comparable (the
  same view-off toyhouse measured 46.5 at 18:16 and 54.6 at 22:09).
- RD15: GL state cache (tex params/binds/uniforms/depth/colour mask only on change): 338 GL calls/frame, driver thread 8.9 -> 3.9 ms. Same-time A/B takeover vs off: toyhouse 52.2/58.4 ms (fps 53.7/56.5, pacing limited elsewhere), woods 34.6/46.1 (-25%).
- RD16 (cac9dfd): PS2X_ASPECT=fill Hor+ (VU1 VP x lane, decomp EE frustum widen, renderer layout): 16:9 and 21:9 fill the window, 60/57 fps, same CPU as 4:3. RD17: GS-thread state per kick (gsState 99.8%): white drop-shadow squares gone; the dark blob shadow (two-pass dest-alpha) still missing.
- RD18 (+18b): flip-time 2D filter by the frame's geometry FBP; classic present for frames without geometry kicks (raster skipped only for geometry draws). Boot with takeover: Now Loading, SCEA card, fades OK; title logo/menu missing (render-target composite?), FMV unverified (very dark frames). tools/boot_shots.ps1 added.
- RD19-21 (user report: 'FOV too far, mesh glitches, flicker'): 2D Z-writing clears now write our depth (black silhouettes from pre-clear passes gone), exact PS2 viewport mapping (guard band: clip +-1 was mapped to the window edges = zoomed out; framing now identical to GS in studio_e/toyhouse_g/hong_g/space_c). Open: near-camera objects the GS hides (scissor? camera-occluder fade?), render-target textures (TV screen).
- RD26/27: camera timeline probe showed one camera per frame; root cause of the 'walls in front of the camera': skinned/clip recorders read ADC from the FOG qword, so VU1-culled back faces were drawn. Fixed; studio_e/hong_g/space_c match GS. Open: render-target screen contents (TV/robot screens), missing props in toyhouse_g, drop shadows, title logo.
- RD28 RT page sync (live robot screens), RD29-31 AFAIL modes + unblended dest alpha + DATE/ABE (drop shadows back), RD32 recording realloc fix (toyhouse takeover 58 fps, 53.8 vs 56.1 ms off; castle 35.1 vs 40.4; space 21.8 vs 27.9).
- FEAT-CFG: ps2x.ini (renderer classic|new, aspect, msaa, window, texture_pack, background_window); env vars override; PS2X_NO_CONFIG=1 for tests. Verified ini-only launch: new renderer + fill at 1600x900. Boot sequence with the new renderer: loading, SCEA card, FMV (classic fallback), title logo/menu all render.

## 2026-11-19 flicker RD33-RD37
RD33-34b composition by main-pass serial set + slot pinning; RD35 black-frame probe found space_c black = next frame's full-screen clear drawn in the 2D tail (RD36 drops it); RD37 rejects partial compositions (<0.6x average main serials). 6-stage burst: travel/woods/castle/arabian clean, space_c clean, toyhouse_a 3/30 sky-only frames left.
