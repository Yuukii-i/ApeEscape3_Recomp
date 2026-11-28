# EYESFIX: correct palette-blend function at guest 0x00100400. Small task. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp. Add a runtime override of guest function 0x00100400 the same
way the existing override of 0x0051E198 is installed (~line 3470, "FIX-BLUR1"). Mark `// FIX-EYES1`.
Env PS2X_CLUTBLEND_FIX=0 leaves the generated function in place; default is override ON.

The guest function blends two palettes. Arguments (EE o32/n32 registers): a0=$4 dst, a1=$5 src1, a2=$6 src2,
a3=$7 byte count (multiple of 16), t0=$8 weights (low 32 bits: halfword0 = f, halfword1 = g = 256 - f),
t1=$9 mask (0x00FF00FF..., not needed by us). Behaviour to implement, for each byte i in 0..a3-1 (at least 16
bytes, i.e. do-while in 16-byte steps):
    dst[i] = (uint8_t)(((int)src1[i] * (int16_t)f + (int)src2[i] * (int16_t)g) >> 8);
Read all 16 source bytes of a step before writing that step (dst may alias a source). Use the runtime's guest
memory access helpers (scratchpad addresses must work), not raw rdram indexing. Finish like other overrides:
return to ra ($31). Reply in 2 lines.
