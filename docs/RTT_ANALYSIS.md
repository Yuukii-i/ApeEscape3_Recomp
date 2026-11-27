# Off-Screen Render-Target & Feedback Analysis (RT1)

## 1. FLOW: Off-Screen `FRAME.FBP` Draw Path (Default Config)

Default run configuration (`PS2X_GS_ASYNC=1`, `PS2X_GS_VULKAN=1`, `PS2X_SDL_RD=1`, `PS2X_RD_VIEW=1`, takeover active):

1. **GS Frontend capture & batching (`gs_frontend.cpp`)**:
   - **3D/geom kicks**: `ps2xRdNoteState`, `ps2xRdNoteXyoff`, `ps2xRdNoteScissor` (`gs_frontend.cpp:5969-5981`) and `ps2xRdNoteDraw` (`gs_frontend.cpp:5998`) record state and texture content.
   - **2D/non-geom draws**: `ps2xRdNoteDraw(texSerial, rawTex0, rawTexa, m_localMemoryStorage, ps2xRdActiveClut())` (`gs_frontend.cpp:6252`) records the texture into the content map, and an `Rd2DBatch` (`b2d`) is appended to `s_rd2dBatches` (`gs_frontend.cpp:6255-6404`).
   - **Backend submission (`GS::flushPendingDraws`)**: `g_rdCurDrawIsGeom` is computed as `ps2xRdActive() && s_rdRunIsGeom && (!ps2xRdHasDisplayFbp() || ps2xRdIsDisplayFbp(m_runState.context.frame.fbp)) && rdScissorQualifies(...) && ps2xRdIsMainPass(...)` (`gs_frontend.cpp:6567-6569`). For an off-screen `FRAME.FBP` (`!ps2xRdIsDisplayFbp`), `g_rdCurDrawIsGeom` is **`false`**. It then calls `m_backend->SubmitRun(m_runState, m_runPrims.data(), m_runPrims.size())` (`gs_frontend.cpp:6571`).

2. **GS Backend rasterization (`ps2_vk_gs_backend.cpp` / `gs_cpu_backend.cpp`)**:
   - With `PS2X_GS_VULKAN=1`, `m_backend` is the Vulkan GS backend (`ps2_vk_gs_backend.cpp`).
   - In `SubmitRun` (`ps2_vk_gs_backend.cpp:796-814`), it only early-returns (skips rasterization) when `ps2xRdTakeoverOn() && g_rdCurDrawIsGeom` (`ps2_vk_gs_backend.cpp:805`).
   - Because `g_rdCurDrawIsGeom` is `false` for non-display FBPs, **the Vulkan GS backend DOES rasterize off-screen `FRAME.FBP` draws** into its GPU-side VRAM buffer (`ps2_vk_gs_backend.cpp:815-877`) `[CODE ps2_vk_gs_backend.cpp:805-877]`. (If it falls back to `submitRunPerPrim` / `GSCpuBackend::DrawPrimitive`, the CPU backend rasterizes into `m_localMemoryStorage` `[INFERRED]`.)

3. **Direct-Renderer 2D publish filter (where it is dropped from the screen)**:
   - During frame publish in `gs_frontend.cpp:3534-3800`, every `Rd2DBatch` in `s_pubBatches` is filtered:
     - `keepBatch` is set to `true` only if `s_rd2dKeepAll`, `bFbp == filterFbp` (`kept-main`), `s_rd2dFeedback` matches `s_copySrcFbps` (`kept-feedback`), or `s_rd2dKeepSmall` (`kept-small`) (`gs_frontend.cpp:3541-3603`).
     - Any other off-screen `bFbp != filterFbp` batch has `keepBatch == false` and is labeled `dropped-offscreen-fbp` (or `dropped-feedback` if its `tex0` overlaps `rd78FbFirst/Last` or `ps2xRdIsFbFeedback(b.texSerial)` is true) (`gs_frontend.cpp:3658-3665`, `3742-3752`).
     - Only `keepBatch == true` batches are compacted and forwarded to `rd_view.cpp` (`gs_frontend.cpp:3797-3800`); all `dropped-offscreen-fbp` / `dropped-feedback` batches are **dropped before `rd_view.cpp` ever draws them**.

---

## 2. VRAM: What `ps2xRdGetTexture` Decodes From & Why `0x2e40`/`0x3240` Are All Zero

- **Memory decoded**: `ps2xRdGetTexture` (`rd_texture.cpp:1383-1388`) reads from `g_rdVram` (`ps2xRdSetVram`, `rd_texture.cpp:1222-1225`), which points to the CPU-side 4 MB PS2 VRAM buffer (`m_localMemoryStorage` in `gs_frontend.cpp:6252`). `decodeTextureRaw` / `bulkReadTextureRaw` (`rd_texture.cpp:618-689`) decodes directly from that CPU `vram` pointer.
- **Who writes CPU `g_rdVram`**:
  1. Host-to-local texture uploads: `UploadImage` (`ps2_vk_gs_backend.cpp:971-977` forwards to `cpu_->UploadImage` at `gs_cpu_backend.cpp:4571`).
  2. CPU rasterizer `GSCpuBackend::DrawPrimitive` (`gs_cpu_backend.cpp:1139`) when CPU fallback is used `[INFERRED]`.
  3. Explicit GPU->CPU page readback: `ps2xVkSyncPagesForCpu(fpFirst, fpLast, &syncedBytes)` (`ps2_vk_gs_backend.cpp:1363`, `3196-3204`), called by `ps2xRdNoteDraw` (`rd_texture.cpp:1743`).
- **Are off-screen draws updating `g_rdVram` / why `0x2e40` and `0x3240` are all zero**:
  - **The Vulkan GS backend is NOT disabled for off-screen FBPs**: `g_rdCurDrawIsGeom` is `false` for `fbp=0x172` (`0x2e40/32`) and `fbp=0x192` (`0x3240/32`), so `SubmitRun` executes them on the Vulkan GS GPU VRAM (`ps2_vk_gs_backend.cpp:805-877`).
  - **Why `0x2e40`/`0x3240` end up all zero in `g_rdVram` / decoded textures**:
    1. **Main-pass draws are skipped on the Vulkan GS**: Any 3D/main-pass draw targeting display FBP has `g_rdCurDrawIsGeom == true` and is skipped by `ps2_vk_gs_backend.cpp:805`. Thus the Vulkan GS's GPU VRAM for display/scene FBPs is empty/black; any off-screen pass that copies from display FBP into `0x172`/`0x192` copies black pixels `[INFERRED]`.
    2. **Async RT sync staleness/skip (`PS2X_RD_ASYNCRT` default ON)**: `ps2xRdNoteDraw` calls `ps2xVkSyncPagesForCpu` (`rd_texture.cpp:1743`). In `syncPageRangeForCpu` (`ps2_vk_gs_backend.cpp:1407`, `2947-2949`, `3050-3070`), `asyncRtWanted()` defaults to `true`, so readbacks are asynchronous and `handleRtAsyncNotReady` skips up to 3 consecutive frames before forcing a blocking sync.
    3. **Fallback path skips sync**: If `ps2xRdGetTextureForBatch` (`rd_texture.cpp:2072`) misses `ps2xRdLookupContentId(serial)` (e.g., `serial == 0` or ring overwrite) and falls back to `ps2xRdGetTexture(tex0, texa)` (`rd_texture.cpp:2190`), `ps2xRdGetTexture` reads `g_rdVram` directly **without** calling `ps2xVkSyncPagesForCpu`.
    4. **Feedback early-out**: If the sampled pages overlap `ps2xRdFbPageRanges` (display/geom FB ranges), `ps2xRdNoteDraw` marks `g_fbFeedbackRing` and returns early at `rd_texture.cpp:1715-1720` without syncing or decoding.

---

## 3. The Display Buffer as a Texture & What Is Missing for Pause

- **What the renderer currently provides (`rd_view.cpp`)**:
  - **`s_prevTexId` / `ps2xRdGetPrevFrame` (`FXC1`, `rd_view.cpp:340`, `475-482`)**: Captures the previous frame's direct-rendered backbuffer (`copyToFbTarget` at `rd_view.cpp:7624`). Used by:
    - `isRdFbTexDisplayBatch` (`rd_view.cpp:2780-2835`, `FIX-RD80/82`): Substitutes `s_prevTexId` when a batch has `ps2xRdIsFbFeedback(b.texSerial)` and `tex0` points into a display FBP page range (`ps2xRdIsDisplayFbp`).
    - `rdGetDisplayBlend` (`gs_frontend.cpp:3605-3634`, `rd_view.cpp:7560-7572`, `FIX-RD80`): Full-screen `alpha=0x64` (`FIX` blend) feedback quads are approximated as a single post-frame overlay blend of `s_prevTexId`.
  - **`FIX-RD81` Snapshots (`findRdSnapTex`, `rd_view.cpp:2837-2861`, `7471-7558`)**: When `gs_frontend.cpp:3563-3593` sees a non-display, non-geom FBP batch (`bFbp != displayFbp && bFbp != frameGeomFbp`) that samples a display/FB page (`fbOverlap || ps2xRdIsFbFeedback`), it calls `ps2xRdNoteSnapshot(bFbp, snapW, snapH)`. `rd_view.cpp:7508-7554` copies the current backbuffer into an `RdSnapSlot` keyed by `slot.destFbp = req.destFbp`. Later draws sampling `tbp0/32 == slot.destFbp` can bind `slot.texId` via `findRdSnapTex` (`rd_view.cpp:5059`, `5333`).
- **What is missing for the pause pipeline (copy `0x0 -> fb 0x70`, shrink `0x70 -> fb 0xe0`, blend `0x1c00` back to `fb 0x0`)**:
  1. **Multi-hop scratch chain**: `FIX-RD81` only snapshots the *backbuffer* into `slot.destFbp` (`0x70`) at end-of-frame (`rd_view.cpp:7471-7555`), **not** mid-frame when the copy happens, and it does **not** execute the second off-screen pass (`fb 0x70 -> fb 0xe0` shrunk/blurred).
  2. **Dropped intermediate passes**: Both the `fb=0x70` copy and the `fb=0xe0` shrink/blur pass have `bFbp != filterFbp` and are dropped as `dropped-offscreen-fbp` / `dropped-feedback` (`gs_frontend.cpp:3663-3664`), so `fb 0xe0` (`tbp 0x1c00`) is never rendered on the direct-render GPU.
  3. **No `s_snapSlots` entry for `0xe0` / `FIX` blend mismatch**: Because `0xe0` is never registered as a direct snapshot of the display buffer (its source is `0x70`, not `0x0`), `findRdSnapTex` misses `tbp 0x1c00`, and `rd_view.cpp` samples black VRAM (or skips it).

---

## 4. Options to Make Off-Screen Targets Work

| Option | Design | Files Changed | How Texture Decoder Finds Target | What Breaks / Risks | Effort (Lines) |
|---|---|---|---|---|---|
| **(A) CPU Rasterizer + Coherent VRAM** | Route off-screen `FRAME.FBP` draws to `GSCpuBackend::DrawPrimitive` (bypassing Vulkan GS) and copy GPU display frame into CPU `g_rdVram` whenever an off-screen pass reads display FBP. | `gs_frontend.cpp`, `ps2_vk_gs_backend.cpp`, `rd_texture.cpp`, `rd_view.cpp` | `ps2xRdNoteDraw` / `ps2xRdGetTexture` already decode from `g_rdVram` (`m_localMemoryStorage`), so they find it automatically once `g_rdPageGen` is bumped. | GPU->CPU readback of display buffer stalls pipeline & drops FPS; CPU rasterizer is slow at full-screen blur; `PS2X_RD_ASYNCRT` must be bypassed for same-frame RT reads. | Medium (~250–400 lines) |
| **(B) GPU Render-Target Pool in `rd_view`** | Keep a pool of GPU FBOs/textures in `rd_view.cpp` keyed by `(fbp, fbw, psm)` (or page range). Don't drop `dropped-offscreen-fbp` / `dropped-feedback` batches; execute them in submission order into their FBO, and bind the FBO's texture when a later batch's `tex0` (`tbp0/32`) matches an active RT. Lazy-copy current RT on self-read (`dstFbp == srcFbp`). | `gs_frontend.cpp`, `rd_view.cpp`, `rd_texture.cpp` | `rd_view.cpp` checks an RT-pool lookup (`findRdTargetTex(tbp0, psm)`) before calling `ps2xRdGetTextureForBatch`, similar to `findRdSnapTex` (`rd_view.cpp:5059`). | Requires preserving exact draw order across 2D/3D (`afterSerial`) and handling partial-page/PSM aliasing (e.g., `PSMCT32` write vs `PSMT8` read) and `UploadImage` invalidation of RT pages. | High (~500–800 lines) |
| **(C) Hybrid (GPU RT Pool for `PSMCT32/16` + CPU/VRAM fallback)** | Execute `PSMCT32`/`CT24`/`CT16` off-screen passes (level-select TV `0x172`/`0x192`, pause `0x70`/`0xe0`) in a GPU RT pool inside `rd_view.cpp`, seeded by `s_prevTexId` / backbuffer copy on display-FBP reads; leave exotic format-aliasing or CPU-readback passes on `GSCpuBackend` + `g_rdVram`. | `gs_frontend.cpp`, `rd_view.cpp`, `rd_texture.cpp` | `rd_view.cpp` resolves `tbp0` against the GPU RT pool first, falling back to `ps2xRdGetTextureForBatch` (`g_rdVram`) if no GPU RT owns those pages. | Must invalidate/evict a GPU RT if `UploadImage` or CPU GS writes to its pages; `g_rdVram` and GPU RT pool must not fight over the same `fbp`. | Medium-High (~350–550 lines) |

---

## 5. Recommendation & Minimal First Experiment

- **Recommendation**: **Option (C) Hybrid** (converging toward **(B)** for all `PSMCT32`/`CT16` off-screen RTs). It avoids GPU->CPU readback stalls for display-buffer feedback (like pause `0x0 -> 0x70 -> 0xe0 -> 0x0`) and keeps blur/CRT passes at full GPU speed, while avoiding immediate reimplementation of exotic PS2 format-reinterpretation RTs.
- **Minimal First Experiment (Level-Select TV Picture `0x2e40` / `0x3240`)**:
  - In `rd_texture.cpp:1743`, force synchronous `ps2xVkSyncPagesForCpu` (bypass `PS2X_RD_ASYNCRT` skip) when `bFbp` or `tbp0` is a non-display RT (`0x172`/`0x192`, i.e., `tbp0 == 0x2e40 || tbp0 == 0x3240`), **or** temporarily route `fbp == 0x172 || fbp == 0x192` in `ps2_vk_gs_backend.cpp:805` to `cpu_->DrawPrimitive` (after ensuring `0x3640` is in `m_localMemoryStorage`, which it already is) and bump `g_rdPageGen` / `g_rdVramGen` after the draw.
  - Because `0x3640` already holds the real preview picture in CPU VRAM, executing the `0x172`/`0x192` draws synchronously into `m_localMemoryStorage` (or forcing a synchronous `ps2xVkSyncPagesForCpu` before `ps2xRdNoteDraw` hashes `0x2e40`/`0x3240`) is a ~15-line test that should immediately make `0x2e40`/`0x3240` non-black and display the level-select TV picture.
