# ENH1c: verify that the pass-through changes no pixels. Small task. Do NOT build/run/commit.
Root c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime. Mark changes `// PROBE-ENH1`. Do not edit .h files.
File: src/lib/render/rd_enhance_vk.inc (from ENH1b), plus rd_gfx_vk.cpp only if a hook is needed.

Env PS2X_ENH_VERIFY=1: on every 60th applied frame, read the single-sample colour just BEFORE the composite and
just AFTER it (end the rendering after the composite so MSAA is resolved again, then resume with LOAD) into two
host-visible buffers. Compare them later, when that frame slot's fence has completed (no stall, no WaitIdle), and
log to stderr: `[enh] verify frame=<n> maxdiff=<largest per-channel difference> w=<w> h=<h>`.
With the variable unset there is no extra work. Reply with the line numbers touched.
