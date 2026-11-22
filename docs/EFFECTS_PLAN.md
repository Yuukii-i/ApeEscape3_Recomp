# Missing effects plan (2026-11-22): fog, god rays, particles, blur, fades/transitions
User priority: effects come before more widescreen/resolution work (transitions and blur are full-screen effects; R4 audit parked).

## Census (PS2X_RD_CENSUS=1, `[census]` line per second, PROBE-E0 in gs_frontend.cpp; stages castle_a, studio_b, toyhouse_a, arabian_a, woods_a, woods_c, snowfesta_c, boss1_a, space_b, hub)
- Render-to-texture draws (frame reg FBP != display fbp): rt={} in ALL gameplay stages. Only 1 fb-read per frame (the display copy, tbp0=0 psm0). So gameplay effects are NOT render-to-texture.
- line=0 point=0 everywhere (no skipped point/line particles). sprites: ~360/s (UI) except snowfesta_c ~108000/s (snow = sprites, drawn).
- FOG IS USED: fge (fog-enabled draws/s) woods_a 15.6k/36k prims fogcol=0xFFD6B2, toyhouse_a 31k fogcol=0xBFB2B2, arabian_a 7.5k fogcol=0xFFD8CC, space_b 51k, boss1_a 22k, snowfesta_c 14k; castle_a/studio_b 0. The new renderer has NO fog code at all (grep fog in src/lib/render = 0 hits; RdVert = pos[4], rgba[4], uv[2], no fog value; the GS backend vertex has vtx.fog). => forest shows no fog.
- Blend modes seen (alpha reg & 0xFF000000FF): 0x44 std alpha, 0x48 additive (Cs*As+Cd), 0x46 multiplicative darken, 0x21/0x28 constant-FIX blends, 0x5a. masked draws (fbmsk!=0): 1/frame.
- Transitions: in a hub->shop door transition the census shows textured draws reading tbp0=0xE00 (scratch fbp 0xE0) 28-34/s for ~3 s = screen copied to a scratch area and sampled (snapshot substitution mechanism, RD81, which misrenders in Vulkan: V3A could not reproduce because only stages were tested, not transitions).

## Plan (one hypothesis per build)
E1 FOG: (a) probe: fog coefficient distribution for FGE draws (GS vtx.fog min/max/mean) to confirm F varies with distance; locate where the 3D path (vu1_func.inc, t_rdTris/rdVerts) reads the XYZF qword and can carry F; (b) carry F per vertex (RdVert gets fog; keep the three copies of the struct in sync: rd_view.cpp, vu1_func.inc, gs_frontend.cpp/others), per-batch FGE flag + FOGCOL in RdBatch/state, shader: rgb = mix(fogcol, rgb, F/255) after texture/lighting and before blending (GS: Cout = F*Cs + (255-F)*FOGCOL >> 8), uniform fogcol; env PS2X_RD_FOG default ON once verified, with A/B vs PCSX2 forest screenshot.
E2 TRANSITIONS/BLUR (snapshots): reproduce SNAP=1 misrender at a real transition (hub door, level start), compare GL vs VK, fix snapshot copy/sampling in rdgfx_vk, then fades/blur that read the scratch buffer.
E3 GOD RAYS / PARTICLES: find what the guest draws for the forest light shafts (additive 0x48 polys? masked draws? dropped draws: use [rd78] why= logs on woods_a) and compare with the PCSX2 forest frame; fix the drop/state handling.
E4 SWIRL (radial wipe with depth-mask sectors) after E2.
E5 then resume R4 audit (without transitions) and widescreen culling.
