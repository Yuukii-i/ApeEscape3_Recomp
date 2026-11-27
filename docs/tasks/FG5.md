# Task FG5: where do the 9 ms of ps2xRdDraw go? (instrumentation only, env PS2X_RD_DRAWPROF=1)
Budget: "[call N/12]", stop at 12. Edit ONLY PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, and PS2Recomp/ps2xRuntime/src/lib/render/rdgfx_vk.cpp (or whichever .cpp implements rdgfx_vk::beginFrame/endFrame and the draw/bind wrappers; find it with Grep, do not edit headers). Mark `// PROBE-FG5`. DO NOT BUILD/RUN/COMMIT.
Why: frame interpolation repeats ps2xRdDraw for every extra present. FG4c measured drawRealMs 9.2-9.6 ms in woods_a (~3500 batches/frame, 60k verts) and 3.4-4.1 ms in the hub; extras are skipped when the draw does not fit. To make extras cheap we need to know whether the time is state/descriptor/uniform changes, per-batch draw calls, texture lookups/uploads, or buffer uploads.
Do (static bool read once; unset => one bool test per section):
1. Accumulate wall time (QPC) per frame into named buckets inside ps2xRdDraw and its callees, printed once per second as `[drawprof] frames=%u total=%.2f upload=%.2f texLookup=%.2f stateBind=%.2f uniforms=%.2f drawCalls=%.2f other2D=%.2f submit=%.2f nBatches=%.0f nDraws=%.0f nTexBinds=%.0f nStateChanges=%.0f nUniformUpdates=%.0f` (milliseconds per frame, counts per frame).
   - upload: vertex/index buffer upload for slots
   - texLookup: ps2xRdTex* lookups/decodes per batch
   - stateBind: pipeline/blend/depth/scissor/descriptor set changes
   - uniforms: push constants / UBO updates
   - drawCalls: the draw/drawIndexed recording itself
   - other2D: 2D batches
   - submit: queue submit/present inside this function if any
2. Also print the top 5 consecutive-batch state change reasons (e.g. tex0 changed, alpha changed, test changed, prim changed, scissor changed) as counts per frame in the same line: `chg=tex:%u alpha:%u test:%u prim:%u zbuf:%u fog:%u`.
3. No behaviour change.
Accept: compiles; reply <=4 lines with file/line ranges.
