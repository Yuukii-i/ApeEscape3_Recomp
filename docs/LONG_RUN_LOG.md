# Long run log (append one line per step)
04:11 | start | read LONG_RUN_PLAN.md, model = Gemini 4 Hydrogen (Medium) | ok
04:19 | P1 | mapping | PASS | docs/VU1_MAP.md (6 scenes, fallback=0 everywhere; decompile already covers gameplay)
04:20 | P4 | launcher plan + release checklist docs written | PASS
04:28 | P4 | L1 settings model | PASS (4/4 checks, tools/build_launcher.bat)
04:29 | P2A | hub: fogcol matches ref; lean skin path hard-codes fog=1.0 (vu1_func.inc:2546) -> spec E10a sent | OPEN
04:40 | P2A | E10a lean skin fog | PASS (leanfog mismatches=0; native hub/seaside screenshots ok; warp leaves stale fog = artifact) | tree haze + pale rectangle in hub still OPEN
04:43 | P2C | pause ball | BLOCKED: logs/pause_test.padrec desyncs (black after hub); needs a new recording through a level + pause (user)
04:44 | P4 | L2+L3 launcher window, pages, process start, headless modes | PASS (builds, window screenshot ok, --print-launch ok, --play boots runtime). Known: runtime reads ps2x.ini from its own cwd, launcher --ini path may differ (env block carries all settings so behaviour is identical)
04:46 | P2B | title-screen fog glitch | NOT REPRODUCED in current build (title ground green and normal with fog on; shots logs/shots/titA_14.png) | closed unless user still sees it
04:48 | P2A | hub pale rectangle | OPEN: removing the panorama texture (PS2X_RD_TEXFILTER=5e1313300 INV=1) removes the rectangle but also the hills; with-panorama colours are close to ref at the horizon; texture alpha plane is a checker/dither (avg ~50%); needs a pixel-exact comparison of draw #8690 (blend factors / checker alpha handling) - not solved
04:49 | P3 | V1 light data analysis | PASS docs/VU1_LIGHT_DATA.md (all 11 handlers, addresses with CODE refs) ; V2 export spec sent (gated by PS2X_SCENE)
