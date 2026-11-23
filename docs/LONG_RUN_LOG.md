# Long run log (append one line per step)
04:11 | start | read LONG_RUN_PLAN.md, model = Gemini 4 Hydrogen (Medium) | ok
04:19 | P1 | mapping | PASS | docs/VU1_MAP.md (6 scenes, fallback=0 everywhere; decompile already covers gameplay)
04:20 | P4 | launcher plan + release checklist docs written | PASS
04:28 | P4 | L1 settings model | PASS (4/4 checks, tools/build_launcher.bat)
04:29 | P2A | hub: fogcol matches ref; lean skin path hard-codes fog=1.0 (vu1_func.inc:2546) -> spec E10a sent | OPEN
04:40 | P2A | E10a lean skin fog | PASS (leanfog mismatches=0; native hub/seaside screenshots ok; warp leaves stale fog = artifact) | tree haze + pale rectangle in hub still OPEN
