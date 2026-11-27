# Task UI2: tag every game UI quad with its layer number inside the PRIM register's unused upper bits
Files: PS2Recomp/ps2xRuntime/src/lib/decomp/ee_gfx_decomp.cpp, src/lib/ps2_runtime.cpp, src/lib/gs/gs_frontend.cpp.
No header edits. No recomp_source edits. DO NOT BUILD/RUN/COMMIT. Mark `// FIX-UI2`. Apply exactly this.
All of it is active only when env `PS2X_UI_LAYER_LOG` is "1" (otherwise nothing is installed or changed).

Facts (from PCSX2): guest sub_0050897C writes one UI quad as a GIF REGLIST packet whose first datum is PRIM (0x14C or 0x15C),
then calls sub_003B7798 with return address 0x508D94. At that call: a1 (reg 5) = packet end address,
s3 (reg 19) = layer queue entry = *(u32*)0x006AF340 + layer*0x20, s2 (reg 18) = quad struct.

1. ee_gfx_decomp.cpp: add global function `void ps2xUiTagInstall(PS2Runtime &rt)` (outside the anonymous namespace).
   - return unless env PS2X_UI_LAYER_LOG == "1".
   - static RecompiledFunction orig = rt.lookupFunction(0x003B7798u); return if null.
   - rt.registerFunction(0x003B7798u, wrapper). wrapper(rdram, ctx, runtime):
     if GPR_U32(ctx,31) == 0x00508D94u:
       base = guest u32 at 0x006AF340; s3 = GPR_U32(ctx,19); s2 = GPR_U32(ctx,18); end = GPR_U32(ctx,5);
       layer = (s3 - base) / 0x20; trailers = (guest u8 at s2+1 != 0 ? 1:0) + (guest u8 at s2 & 1 ? 1:0);
       prim = end - 0x70u - 0x30u*trailers; v = guest u64 at prim;
       if (layer < 35 && (v == 0x14Cu || v == 0x15Cu)) write guest u64 prim = v | (uint64(0xA500u | layer) << 32);
     then ALWAYS `orig(rdram, ctx, runtime);`.
     Guest address -> host: mask with 0x1FFFFFFF and bounds-check against PS2_RAM_SIZE (use the helpers this file already uses).
     Keep a counter; ps2xSafeLog("[uitag] tagged=%u missed=%u\n") every 2000 calls from 0x508D94.
2. ps2_runtime.cpp: next to line 10 declare `extern void ps2xUiTagInstall(PS2Runtime &);` and call
   `ps2xUiTagInstall(*this);` directly AFTER `ps2xEeGfxDecompInstall(*this);` (about line 2923).
3. gs_frontend.cpp:
   - file static `static uint32_t s_uiCurLayer = 0xFFu;`
   - in `case GS_REG_PRIM:` of writeRegisterUnlocked (about line 5309):
     `s_uiCurLayer = (((value >> 40) & 0xFFu) == 0xA5u) ? uint32_t((value >> 32) & 0xFFu) : 0xFFu;`
     (check decodePrimRegister ignores bits above 10; report if not).
   - PROBE-UI1 block: put the layer into the map key (`| (uint64_t(s_uiCurLayer) << 56)`), and print
     `layer=%d` (-1 when 0xFF) in the [uilayer] line, after fbp. Raise the key cap from 64 to 160.
Reply in <=5 lines with line ranges touched.
