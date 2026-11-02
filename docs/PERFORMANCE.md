# Ape Escape 3 recomp: performance report

Date: 2026-11-02. Branch: `perf/aggressive`. Test machine: Ryzen 7 7435HS laptop (8 cores, 16 threads, 16 MB shared L3) [W7].

## 1. Summary

- **Where we are:** the shop, our worst scene, runs at about 43 FPS (23.2 ms per frame). The target is a locked 60 FPS (16.6 ms), then 144 FPS or more.
- **What limits us now:** the VIF1 worker thread, at 20.6 ms per frame. Most of that (about 16 ms) is running VU1 programs, which is about the same speed as the real console chip or a little slower.
- **What limits us next:** the GS thread, at about 16–18 ms per frame. Fixing only the worker would stop at about 55–62 FPS, so a locked 60 needs both threads to get cheaper.
- **Small fixes will not be enough for a locked 60.** The best case for the listed small fixes brings the worker to about 16 ms, with no headroom. History says these estimates tend to fall short.
- **The option we have been underrating:** stop sending most geometry through the emulated path (VU1 memory, then GIF packets, then GS parsing), and send it straight to the GPU. This is the only single change that cuts both limiting threads, and the same design is what makes real 3D rendering above 60 FPS possible. It was last on our roadmap. I now think it should come much sooner. It is also the largest and least proven item here.
- **Above 60 FPS there is no hidden trick.** A game that simulates 60 times a second produces 60 real states per second. Showing more frames takes one of two things: simulate more often, or draw estimated in-between states. Section 7 covers both, including an option that re-renders real geometry instead of generating images on the GPU.

How much to trust the numbers:

| Tag | Meaning |
|---|---|
| **[MEASURED]** | Read from a log of a real run |
| **[CODE]** | Read from the source, not observed running |
| **[ESTIMATE]** | My calculation from measured numbers; the result has not been tested |
| **[UNKNOWN]** | Nobody has measured this yet |

Bracketed references such as [L1] and [W1] point to section 10. Entries such as P369 are in [docs/HYPOTHESES.md](HYPOTHESES.md).

## 1b. Agreed plan (user decision, 2026-11-02)

1. **Locked 60 FPS with headroom.** Not "reaches 60 here": the cost of running the game must be lower than emulating it on PCSX2, otherwise the recomp has no point. Slower PCs and the phone port are the reason. Metrics (proposed, not yet agreed): 99% of frames finish in 14 ms or less in the shop and in a level, measured on a scripted route; total CPU-ms per frame (all threads, `tools/cpu_per_frame.ps1`) below PCSX2's on the same scene.
2. **Blend real geometry** between two real 60 Hz states (section 7, route B) to go above 60. Frame generation from images is ruled out.
3. **If blending adds too much input lag or looks bad:** push the game's own tick rate to 144 by changing its logic (route A).
4. Between 1 and 2: fix the existing crashes and visual glitches (open list in HYPOTHESES.md, plus the shop flicker P362).

Open: the PCSX2 CPU-per-frame number for the shop (needs PCSX2 sitting in the same scene) and the exact definition of "locked".

## 2. How a frame moves through the program

| Thread | Job |
|---|---|
| **EE** | Runs the recompiled game code, including VU0, and builds DMA lists for each frame |
| **VIF1 worker** | Parses the DMA stream, unpacks data into VU1 memory, runs VU1 programs, and sends the resulting GIF packets to the GS queue |
| **GS** | Parses GIF packets, assembles primitives, and records Vulkan draws and texture uploads |
| **Present** | Copies the finished image out of the emulated VRAM format and converts it |
| **Main** | Owns the window, polls input, and shows the image through raylib/OpenGL |

Terms used below:

- **MSCAL:** the VIF command that starts a VU1 program.
- **XGKICK:** the VU1 instruction that sends a packet to the GS.
- **Kernel:** a hand-written native replacement for a VU1 routine (`lbFull`, `lbVert`, `lbCopy`).
- **Hot block:** generated native code for a common stretch of VU1 code (`vuH_*`).
- **Fence:** a point where one thread waits for another to finish.

The threads overlap. The EE waits at one fence per frame, and the frame rate is set by whichever thread takes longest.

## 3. Where we are

### 3.1 Frame budget in the shop [MEASURED, L1]

All numbers come from the last sampler windows of one run (`logs/xp4.log`, 351 frames in 8.4 s). Sampler percentages are converted using 23.2 ms per frame.

| Thread | Busy per frame | Max FPS if nothing else limited it |
|---|---|---|
| VIF1 worker | 20.6 ms | about 48 |
| GS | 16.0 ms by sampler, 17.9 ms by its own timer (which includes GPU waits) | about 55–62 |
| EE | 11.4 ms by sampler, 13.4 ms by fence accounting | about 75–88 |
| Present | about 4.6–5.3 ms | not limiting |

This replaces the 62–70 FPS GS ceiling I gave earlier (P372), which was too high.

Total load is about 2.7 cores or more just for these four threads. That matters for the phone port.

### 3.2 Work per frame

| Quantity | Value | Basis |
|---|---|---|
| VU1 programs started | about 9,300 per frame, or about 400,000 per second at 43 FPS | [MEASURED, L3] in a slower run, assuming the count per frame does not depend on speed |
| GIF packets to GS | about 8,000 per frame | [MEASURED, L1] |
| GS draws | about 45,500 per frame | [MEASURED, L1] |
| Skinned vertices through `lbFull` | about 52,000 per frame | [MEASURED, L1] whole-run average, not shop only |
| Texture upload | about 2.7 MB per frame | [MEASURED, L1] whole-run average |
| Copied for present | about 3.9 MB per frame | [MEASURED, L1] whole-run average, almost all of the 4 MB VRAM |

### 3.3 VIF1 worker breakdown [MEASURED, L1]

| Item | % of wall time | ms per frame |
|---|---|---|
| **All worker work** (`processVIF1Data`) | 89.8 | 20.8 |
| Parsing and unpacking (everything outside `execute`) | 20.4 | 4.7 |
| VU1 entry, `execute` minus `run` | 4.4 | 1.0 |
| `run` minus native code, other than the flush | 4.1 | 1.0 |
| `flushPipelines`, which includes the final XGKICK and GIF submit | 8.3 | 1.9 |
| `lbFull` including `lbVertex8` | 18.5 | 4.3 |
| `lbVert` | 3.3 | 0.8 |
| `lbCopy` | 1.2 | 0.3 |
| `vu1NativeRun` own time (the dispatcher) | 6.2 | 1.4 |
| Everything else under native code, mostly hot blocks | 23.4 | 5.4 |
| Idle, waiting for the next job from the EE | 10.1 | 2.3 |

Details inside those rows:

- `lbVertex8` is 11.8% (2.7 ms) of the `lbFull` total.
- `vuH_14`, a single hot block, is 3.7% (0.9 ms). It is the largest single hot block.
- GIF submission totals about 7–9.5% depending on the window. `GifArbiter::submit` is 5.7%, and the copy into its buffer (`vector::assign`) is 3.0%.
- The largest single lines are the unpack loop at about 2.0% and `lb8Op` at 1.9%. Nothing else is above about 1.5%.

**Limits of this data:**

- The sampler has about 500 samples per window, so small entries are noisy.
- Each thread's list stops at 30 entries. Most hot blocks fall below the cut, and hot-block cost can only be found by subtraction.
- The inclusive numbers come from several ranked lists that do not always contain the same entries. I checked the GIF numbers against single windows, and they vary.

### 3.4 GS thread breakdown [MEASURED, L1]

| Item | % of wall time | ms per frame |
|---|---|---|
| `GS::vertexKick` | 13.1 | 3.0 |
| `GSCpuBackend::UploadImage` | 12.9 | 3.0 |
| `gpuDraw` | 9.8 | 2.3 |
| `processGIFPacket` | 6.7 | 1.6 |
| `flushPendingDraws` | 5.6 | 1.3 |
| `pagesForRect` + `rowsRange` | 3.8 | 0.9 |
| `writeRegisterPacked` | 2.0 | 0.5 |
| Waiting for the GPU (likely, `ZwWaitForMultipleObjects`) | 9.6 | 2.2 |
| Idle or waiting on locks (`ZwWaitForAlertByThreadId`) | 21.6 | 5.0 |

### 3.5 Other threads [MEASURED, L1]

- **EE:** the cost is spread thin. `dispatchGuestBranch` is 3.0%, `writeIORegister` 2.4%, and VU0-related items are a few percent. `_NLG_Return2` shows 5.2%, which is probably a symbol the sampler could not resolve [UNKNOWN]. No guest function is above 0.3%.
- **Present:** `CopyFrameToHostRgba` 6.9%, `PresentFromLocalMemory` 5.7%, and `memmove` 3.2%. It also allocates and frees virtual memory on every frame (about 1.3%).
- **Main:** about 41% of a logical core goes to `NtUserGetKeyState` and `NtUserGetProp2`. The loop polls input about 1,000 times per second [C10]. It does not limit the frame directly, but on a laptop it uses power and may share a physical core with busy threads.

### 3.6 Compared with the real console [ESTIMATE]

The real VU1 runs at 294.9 MHz. VU1 programs average 355–457 VU cycles per call in our captured corpora [L2], and we start about 9,300 per frame. On the console that is about 11–14 ms per frame. Ours takes 16.1 ms.

So **we are not beating the original chip at VU1 work, and may be up to about 1.4× slower.** The corpora are not shop-only, so this is a rough comparison. An earlier replay test measured us at 1.6–2.2× slower [D3].

This is the core of the problem. The VU1 path keeps most of the console's behaviour: timing state, flag state, and a packet round trip for each program.

### 3.7 What the current environment is

These are the switches for the normal test run, in PowerShell syntax:

```
$env:PS2X_GS_ASYNC="1"
$env:PS2X_VIF1_ASYNC="1"
$env:PS2X_GS_VULKAN="1"
$env:PS2X_VU1_KERNEL="1"
$env:PS2X_PRESENT_ASYNC="1"
```

The build flags are `/O2 /Ob2 /Oi /GL /fp:fast /arch:AVX2` for the runtime [C9]. Generated guest code has `/arch:AVX2` and other flags, but no `/GL` [C11].

## 4. What has been tried

| Attempt | Result | Reference |
|---|---|---|
| Async present (PERF-AP) | Kept. One sample showed 55 vs 51 FPS. Causes a small shop flicker, still unsolved | P361, P362, P368 |
| SIMD unpack (PERF-UV) | Kept. Exact: no mismatches live or in 400,000 offline cases | P360 |
| Packet buffer stash (PERF-XP) | Kept. No gain separable from noise | P366 |
| Skip movie scan outside movies (PERF-XS) | Kept. About 2.7% of the worker removed | P366 |
| Skinned-vertex kernel | Kept. Exact. Its first version was speed-neutral, and later rounds made it faster | P356–P359 |
| VU1 thread pipeline (PERF-VP2) | **Failed and reverted.** 9–11 FPS and broken geometry. The glitch cause was not found | P369 |
| VU1 "fast mode" without stalls | **Not exact.** GIF output differs in 42–47% of calls, because the programs read flags inside the timing window | D2 |
| Clang instead of MSVC for VU1 code | No gain: nearly the same instruction count | D2 |
| Clang build and clang PGO of guest code | No gain, per earlier notes | D3 |
| Larger GS queue | No gain; causes bursts and stalls | P355 |
| Running the EE ahead of VU1 | No gain; reset animations | D2 |
| Narrower present page set | No speed change | C270 |
| Parallel VU1 programs (simple form) | Not attempted. Calls are chained through registers and memory words 1022/1023 | D2 |

**Lesson from PERF-VP2:** the pipeline assumed each VU1 program only reads its own half of the buffer, and that was never tested. About 66% of programs had to wait for an unpack anyway, and the per-program hand-off cost more than it saved. Any future threading work needs its output checked against a serial run on the same data before anyone plays it.

**Measurement weakness:** we have no repeatable benchmark. Runs are played by hand, so comparisons depend on the route taken, and only the same stretch of play can be compared. Earlier notes also record about ±1 FPS of noise, plus drift from laptop power and heat [D3]. Gains under 3% cannot be trusted.

## 5. The options

Savings below are [ESTIMATE] unless marked. They are upper limits, not promises. Skinned-vertex work has already shown a 24% cut in one measurement with no visible FPS change, because another limit took over [D2].

### 5.1 Small worker trims (exact, low risk)

| Item | Evidence | Possible saving |
|---|---|---|
| Remove the clock read in the per-second probe, `checkDaProbeSecDump`, from the normal path | 1.4% plus part of the clock functions below it [L1, C1] | 0.3–0.5 ms |
| Force-inline `lb8Op` so unused results are removed | It shows as separate functions totalling about 5% [L1]. It returns a 320-byte struct, which goes through memory rather than registers [W5]. It computes MAC bits for every op, but only two ops use them [C2] | Up to 0.5 ms, [UNKNOWN] until compiled and counted. `__forceinline` is not guaranteed to inline [W6] |
| Cut per-program plumbing in `execute` and `run` | 8.5% (2 ms) spread over 9,300 calls, or about 215 ns per call [L1] | Up to 1 ms |
| Remove the double XGKICK copy | The copy into the GIF buffer is about 3% [L1] | Up to 0.7 ms. Needs a header change and one full rebuild |
| Find what is in the parser's own 10.5% | Unknown: no line stands out [L1] | [UNKNOWN] |

I earlier told you the `run()` setup cost was not an issue. That was wrong: section 3.3 shows about 2 ms around each frame's VU1 calls.

**Total for this group: about 2–3 ms.**

### 5.2 VU1 recompiler (register residency in hot blocks)

- Hot blocks and related code take up to 23.4% of wall time (5.4 ms), an upper bound found by subtraction.
- Keeping VU registers in host registers instead of in memory is estimated at 1.3–1.6× [D2]. That saves about 1.2–1.8 ms at most.
- My earlier "2.7%" figure was an undercount, because the lists are truncated (P371).
- A closed-form kernel for `vuH_14` (0.9 ms), and for the 24F8 clip loop mentioned in the roadmap, would be useful targets too.
- **It does not change the design:** timing still has to be tracked where the programs can observe it, because the fast-mode test shows flags are read inside the timing window [D2].

### 5.3 Combined result for the worker

Sections 5.1 and 5.2 together might save about 3–5 ms, taking the worker from 20.6 ms to about 16–17.5 ms. That is about 57–62 FPS in the best case if every estimate holds and the GS thread keeps up, and I would plan for less. **There would be no headroom, so this is not a locked 60.**

### 5.4 GS thread

| Item | Evidence | Possible saving |
|---|---|---|
| GIF-to-vertex fast path for common packets | `vertexKick` + `processGIFPacket` + `writeRegisterPacked` = 5.1 ms [L1]. Already step 1 of the roadmap [D2] | 2–3 ms |
| Merge draws | 45,500 draws per frame, `gpuDraw` + `flushPendingDraws` = 3.6 ms [L1] | 1–2 ms. Limited by ordering rules, [UNKNOWN] how far |
| Cheaper uploads | `UploadImage` 3.0 ms for about 2.7 MB [L1] | 1–2 ms. Could upload only changed data |
| Split the GS into two threads (parse, then record) | Packet batches are larger units than single VU1 programs, so hand-off should cost less [ESTIMATE] | Raises the ceiling, but uses the same or more total CPU |

### 5.5 Present directly from the GPU

Today each frame copies about 3.9 MB out of the GPU, converts it on the CPU, and uploads it again through OpenGL. Vulkan renders offscreen because the first plan avoided window-system work [D4].

- **Saves:** the present thread's work (about 5 ms of CPU, though not on the limiting thread), the large copy, and one frame of delay caused by async present.
- **Needed for:** resolution scaling and the phone port.
- **May help:** the flicker might also go away, because the present path would no longer use its own copy of VRAM. That is a guess, since the cause is unknown (P368).

### 5.6 Direct geometry path (the option we were underrating)

**Today:** each skinned vertex is computed by a kernel, written to VU1 memory, copied to a packet buffer by XGKICK, copied again to the GS queue, parsed by the GS thread, assembled into a primitive, and written to a Vulkan buffer.

**Proposal, in stages:**

1. **CPU direct path.** The kernels output finished vertices straight to the backend, skipping the VU memory, XGKICK, GIF and parse steps for that geometry. This can be exact: a check mode can compare the direct vertices with what the old path produces on the same frame.
2. **Extend coverage** to the clip/pack routines. Today only the skinned routine and a few others are kernels. About 12 program addresses cover about 70% of VU1 cycles [D5], so a fallback is always needed for the rest.
3. **GPU transform.** Send the source data and matrices, and do the vertex math in a compute shader. This is the same idea as RT64's deferred RSP, whose authors say it "effectively removes CPU bottlenecks that are critical for reaching very high target framerates" [W1].

**Possible savings [ESTIMATE]:**

| Stage | Worker | GS |
|---|---|---|
| Stage 1–2 (CPU direct) | Up to about 2–3 ms of XGKICK and submit costs, scaled by coverage | Up to about 3–5 ms of parse and `vertexKick` costs, scaled by coverage |
| Stage 3 (GPU transform) | Most of the 4.3+ ms of vertex math on top of that, and possibly more with wider coverage | Same as above |

**What could stop it [UNKNOWN unless noted]:**

- **Does anything read the results back?** If the game or a later program uses VU memory contents after the kernel, those writes must stay. The EE waits at only one fence per frame, which is a hopeful sign but not proof.
- **Draw order:** direct geometry must keep its exact position among state changes and other draws. Getting this wrong will show up as visual errors.
- **Bit-exact math on the GPU:** Vulkan can report round-toward-zero support for 32-bit floats [W3], which the VU uses in our runtime. That does not guarantee every result matches the CPU, so stage 3 would likely be checked by image comparison rather than exact bytes. It also needs a decision from you, since all our work so far has required exact output.
- **Clip logic on the GPU** is branch-heavy and may not suit a shader. Stage 3 may only cover part of the work.
- **Size:** this is weeks of work, not days, and the benefit depends on coverage.

**Why I would still move it up:** it is the only option that cuts both limiting threads and reduces total CPU use, which is what the phone port needs. It also gives us what mods, higher resolution and high frame rates all need: real geometry in a form we control.

### 5.7 Parallel VU1

Run chunks of a frame's job on several threads, each with its own VU1 copy, then join the GIF packets in order.

- **Possible gain:** on paper, about 16 ms of VU1 work spread over 3 threads, taking the worker to about 10–13 ms [ESTIMATE].
- **Problem:** VU1 calls are chained through registers and memory words 1022/1023 [D2], so chunks are not independent unless we track what each one reads and writes. I suggested this last turn without accounting for that note.
- **Can it be checked?** The existing corpus cannot answer it: it stores only sampled calls (1 in 200–400) [C8], so it has no consecutive calls to test. It needs a new live probe. Output can be compared byte for byte against a serial run, which PERF-VP2 lacked.
- **Downside:** it spreads CPU use rather than reducing it, so it does not help battery or heat on a phone [D6].

### 5.8 Doing less work

Some work may repeat from frame to frame: for example, the same object with the same matrices while the camera is still.

- **Reuse results:** hash a VU1 program's inputs, and reuse its output when they match. This is exact if every input is covered.
- **What I measured [L2]:** 18–21% of sampled runs had an output identical to an earlier one, but they are small: only about 3.6% of VU1 cycles. Because the corpus is sparse, that is a lower bound, and the true repeat rate is [UNKNOWN]. A live probe is cheap and would settle it.
- **Likely limit:** if matrices include the camera, any camera movement defeats it [ESTIMATE].
- **Skip what cannot be seen:** a recomp can change game code, so objects fully off-screen could be dropped before they reach VU1. How many are sent is [UNKNOWN].

### 5.9 Build and system settings (cheap to test)

| Item | Why | Status |
|---|---|---|
| MSVC profile-guided build of the runtime | The worker's cost is spread across branches and small functions. Earlier PGO tests were on guest code with clang, not this runtime [D3] | [UNKNOWN], one build to test |
| Input polling once per frame | About 41% of a logical core today [L1] | Easy. Saves power and may help boost clocks |
| Pin busy threads to separate physical cores | Avoids sharing a core between hyperthreads. All 8 cores share one L3 [W7] | [UNKNOWN], cheap test |
| Check plugged-in, high-performance power mode for every benchmark | Earlier notes show drift from power and heat [D3] | Do always |

### 5.10 EE code generation

EE is not limiting 60 FPS yet, but it decides what is possible above that.

- The plan is in [CODEGEN_PLAN.md](CODEGEN_PLAN.md): remove per-instruction `ctx->pc` stores, call known functions directly, and cache registers in locals.
- The `ctx->pc` stores are still there: one sampled generated file has 34 in 144 lines [C12].
- Earlier notes put EE code about 2.3× slower than the real chip at the title screen [D1].

## 6. Recommended order for a locked 60

1. **Measurement build first.** One build that answers several questions:
   - full sampler lists, without the 30-entry limit
   - per-program plumbing timers
   - a live input-repeat probe (5.8)
   - a read-and-write-set probe for VU1 calls, which answers 5.6 and 5.7
   - and a repeatable benchmark: a fixed input script from a fixed spot in the shop, so results stop depending on how the run is played
2. **Cheap trims from 5.1 and 5.9.** Low risk, and they raise the floor for everything else.
3. **Decide on the direct geometry path (5.6)** using the probe results. If nothing reads results back, start stage 1 on `lbFull`, which is the largest kernel and already exact.
4. **GS fast path and draw merging (5.4).** These may be partly replaced by the direct path, so decide after step 3.
5. **Hot-block register residency (5.2)** if the worker still needs it.
6. **Direct GPU present (5.5)** before the phone port or resolution work.

## 7. Above 60 FPS

### 7.1 What physically limits it

144 FPS allows 6.9 ms per frame. Today the EE alone uses 11–13 ms, the GS 16–18 ms, and the worker about 21 ms.

The game's logic is probably tied to vsync, so running it faster would make the game itself run faster. That is [UNKNOWN]: PCSX2 was not connected when I wrote this. Turbo mode in PCSX2 would answer it in a minute.

### 7.2 Routes that do not generate images on the GPU

**Route A: actually simulate more often.**

Because the code is recompiled, we can change the game's logic. Find everything that advances per tick (movement, animation, physics, timers), and scale it.

- This gives true high-rate game states with no estimation.
- It needs the EE near 6.9 ms, or about half today's cost, and at least as much from everything downstream unless rendering is also decoupled.
- Risk: per-tick values may be spread across hundreds of actors, and physics and game feel can change subtly. Each bug would be a gameplay bug, not a visual one.
- 120 FPS may be simpler than 144, since it is exactly double the tick rate [ESTIMATE].
- Size is [UNKNOWN] until the game's timing is studied.

**Route B: re-render real geometry at in-between states.**

Keep logic at 60, but draw the scene more often, with object and camera matrices blended between two real game states. Every extra frame is real 3D rendering, with correct depth and occlusion, and not an image warp.

This is how RT64 and Zelda64Recomp work:

- RT64 replays matching draw calls and creates "new 3D transformations ... via interpolation", uploading them to the GPU [W1].
- Zelda64Recomp states that "changing framerate has no effect on gameplay" [W2].
- RT64 also warns that draw call matching is "highly experimental" and "prone to errors", with "limited game support" [W1].

Our notes say an earlier probe found about 95% of draws line up between frames, with a median motion of 0.9 pixels, and that matrices in VU memory 978–1001 are a usable source [D5]. I could not find the original log, so this needs repeating.

Costs and honest limits:

- These are still in-between frames; they are just real renders. If you reject in-between states of any kind, only Route A remains.
- Blending between two states normally shows the scene up to one tick late [W4], so up to about 16.7 ms of added delay unless route C is added.
- It needs the direct geometry path (5.6). If each extra frame had to rerun VU1 on the CPU, 144 FPS would be impossible, because the worker alone takes 21 ms.
- Effects that read the framebuffer, UI and particles need special handling.

**Route C: run camera and input at the true high rate.** On top of B, sample input and update the camera at the display rate, while objects stay interpolated. This could reduce the perceived delay, but the camera code has to be separable from the game tick [UNKNOWN].

**Route D: extrapolate instead of interpolate.** Predict forward from the last state rather than blend. It adds no delay, but it is wrong whenever motion changes suddenly.

### 7.3 Recommendation

Decide between A and B only after a locked 60 exists and the timing question is answered. Both depend on work already recommended above. B is proven elsewhere on simpler hardware, and A gives the purest result at the highest risk. A combination is also possible: simulate the player and camera at a higher rate, and interpolate the rest.

## 8. Phone port

- **Total CPU matters more than the slowest thread.** Our load is 2.7 or more cores on a 4+ GHz laptop chip. Options that reduce work (5.6, 5.8) matter more than ones that spread it (5.7) [D6].
- **The Vulkan backend may not start on phones as written.** It requires fragment shader interlock and 64-bit floats in shaders, and refuses to run without them [C5]. I found no support data for Adreno or Mali [W8]; [gpuinfo.org](https://vulkan.gpuinfo.org) should be checked per device before committing to this design. The vendors being listed as contributors to the extension does not show that they ship it.
- **Storing the framebuffer in a storage buffer** with interlocked read-modify-write [D4] is also likely to be costly on tile-based phone GPUs [ESTIMATE]. Render targets for common cases are already listed as a later stage in the plan.
- **Direct present (5.5)** is needed in any case.

## 9. Open questions

| # | Question | How to answer it | Cost |
|---|---|---|---|
| 1 | Is game logic tied to vsync? | PCSX2 turbo mode | Minutes |
| 2 | Do later programs or the EE read kernel output in VU memory? | Live read-set probe | One build |
| 3 | How independent are consecutive VU1 calls? | Same probe, across calls | Same build |
| 4 | How much work repeats exactly between frames? | Live input-hash probe | Same build |
| 5 | What is in the parser's 10.5%? | Full line-level sampler output | Same build |
| 6 | What is the exact hot-block share? | Full sampler lists | Same build |
| 7 | Can the shop be benchmarked repeatably? | Fixed input script from a fixed spot | Small |
| 8 | Which GPU features exist on target phones? | gpuinfo.org | Minutes |
| 9 | Does MSVC PGO help the runtime? | Test build | One build |
| 10 | What causes the shop flicker? | Compare async and sync frames, as planned in P368's follow-up | Deferred by your decision |

## 10. Sources

### Logs (in `logs/`)

- **[L1]** `xp4.log`: shop run with PERF-XS. `[wait]`, `[gsq]`, `[gsq2]`, `[vk]`, `[present]` and `[prof2]` lines, windows t=60–80. Run from 2026-11-02.
- **[L2]** `vu1corpus.bin` (30,000 runs) and `vu1corpus_snow.bin` (6,000 runs), analysed with `tools/vu1gen/corpus.py`. Mean cycles 457 and 355. Identical outcomes: 18.4% and 21.4% of runs, 3.6% and 3.7% of cycles.
- **[L3]** `pp1.log`: PERF-VP2 run. `[pipe]` counters: about 9,300 MSCAL per frame, and 1,155,072 queued with waits of 261,076 absolute, 498,348 overlap, and 71,589 barrier.

### Code (under `PS2Recomp/ps2xRuntime/src/lib/` unless noted)

- **[C1]** `probe_ae.cpp:3099` `checkDaProbeSecDump`; called from `flushMovieBatch` (`probe_ae.cpp:3129`), which the MSCNT path calls (`ps2_vif1_interpreter.cpp`).
- **[C2]** `vu/generated/vu1_native_dispatch.cpp:4517` `lb8Op`; `:4612` `lbVertex8` (only `in.mac` and `r7.mac` are stored); `:4701` `lbFull`.
- **[C3]** `vu/ps2_vu1_core.cpp:2201` `progressXgkick`; `:2344` `finishXgkick`; `:4345` `run`.
- **[C4]** `gs/ps2_gif_arbiter.cpp:262` `GifArbiter::submit` and its `assign` copy.
- **[C5]** `gs/ps2_vk_gs_backend.cpp:360-369`: required Vulkan features check.
- **[C6]** `gs/ps2_vk_gs_backend.cpp` `startAsync`, `completeAsync`, `addPresentPages`: async present.
- **[C7]** `ps2_memory.cpp:512`: worker idle wait.
- **[C8]** `vu/ps2_vu1_core.cpp:3351-3355`: corpus capture keeps new dispatch addresses plus 1 in N runs.
- **[C9]** `ps2xRuntime/cmake/ReleaseMode.cmake`: runtime build flags.
- **[C10]** `ps2_runtime.cpp:6050-6056`: main loop polling, about 1 kHz.
- **[C11]** Root `CMakeLists.txt:62-64`: guest code flags.
- **[C12]** `recomp_source/sub_00101618_0x101618.cpp`: 34 `ctx->pc =` lines in 144.

### Project documents and notes

- **[D1]** [CODEGEN_PLAN.md](CODEGEN_PLAN.md): EE cost and code generation plan.
- **[D2]** [PERF_ROADMAP_60.md](PERF_ROADMAP_60.md): earlier budget, what was ruled out, fast-mode result.
- **[D3]** Project memory `project_perf_state.md` and `project_vu1_gs_design_diagnosis.md`: earlier measurements and noise levels. These are Claude's working notes, not in the repository.
- **[D4]** [VULKAN_PLAN.md](VULKAN_PLAN.md): backend design, offscreen rendering, interlock.
- **[D5]** Project memory `project_native_vu1_commitment.md`, and [VU1_HLE_PLAN.md](VU1_HLE_PLAN.md): program structure, cycle shares, and the interpolation probe. Same caveat as D3.
- **[D6]** Project memory `project_target_60fps_real_hw.md`: goals, phone port, and the preference for reducing work.
- [HYPOTHESES.md](HYPOTHESES.md): P355–P373, C270.

### External

- **[W1]** RT64 README: <https://github.com/rt64/rt64>
- **[W2]** Zelda64Recomp README: <https://github.com/Zelda64Recomp/Zelda64Recomp>
- **[W3]** Vulkan `VkPhysicalDeviceFloatControlsProperties`: <https://docs.vulkan.org/refpages/latest/refpages/source/VkPhysicalDeviceFloatControlsProperties.html>
- **[W4]** Fixed timestep and interpolation discussion, gamedev.net: <https://gamedev.net/forums/topic/691776-fix-your-timestep>
- **[W5]** Microsoft, `__vectorcall` return rules: <https://learn.microsoft.com/en-us/cpp/cpp/vectorcall?view=msvc-170>
- **[W6]** Microsoft, `inline`, `__inline`, `__forceinline`: <https://learn.microsoft.com/it-it/previous-versions/z8y1yy88(v=vs.120)>
- **[W7]** Ryzen 7 7435HS specifications, Notebookcheck: <https://www.notebookcheck.net/AMD-Ryzen-7-7435HS-Processor-Benchmarks-and-Specs.905778.0.html>
- **[W8]** Vulkan `VK_EXT_fragment_shader_interlock`: <https://docs.vulkan.org/refpages/latest/refpages/source/VK_EXT_fragment_shader_interlock.html>
- **[W9]** PCSX2, "Threading VU1", for comparison with our worker design and its limits ("This syncing is slow and if emulation needs to do it a lot it eliminates the speedup from threading"): <https://pcsx2.net/blog/2011/threading-vu1>
- **[W10]** VIF command reference (FLUSH, MSCALF and double-buffering behaviour), used for the PERF-VP2 design: <https://israpps.github.io/ps2tek/PS2/VIF/Commands.html>
