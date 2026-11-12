# Reversal memo (risky changes, how to undo)

Every risky change made during the silent-mode 60 fps push. Each line: what, switch to turn it off, commit to revert (submodule PS2Recomp unless noted).

| Date | Change | Off switch | Revert |
|---|---|---|---|
| 2026-11-12 | Vulkan ring capacities 131072 prims / 8192 clut | PS2X_VK_MAXPRIMS=24576 PS2X_VK_MAXCLUT=2048 | 526e8d5 |
| 2026-11-12 | Staged prim records (stack + one memcpy) | PS2X_VK_PRIMSTAGE=0 | 526e8d5 |
| 2026-11-12 | GIF packet coalescing (PATH1 + whole PATH2) | PS2X_GIF_COALESCE=0 | (GIF arbiter commit, see AUTONOMOUS_LOG 23) |
| 2026-11-12 | VIF1 two-stage pipeline: new Vu1Exec thread runs VU1 programs, GIF DIRECT and UNPACK writes from an ordered event ring while the Vif1Worker parses ahead (threading change, exact by event order) | PS2X_VIF1_PIPE=0 | c6769e6 |
| 2026-11-12 | Functional (decompiled) VU1 engine DEFAULT ON for image 86503d39: dispatcher + 0050/0060/0070/0088/0C80/00A8 + 1EE0 (skinned 8-wide, rigid) run as C++; other handlers / real clipping fall back to the exact path; exact on shop, early-run and snow corpora (mem/gif) | PS2X_VU1_FUNC=0 | Tasks F1/F2 + PERF-F2Z/F2W + overhead commits (AUTONOMOUS_LOG 39-44) |
