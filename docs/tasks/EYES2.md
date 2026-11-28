# EYES2: add palette contents to the EYES1 dump. Tiny task. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp, the PROBE-EYES1 code (~line 575-800). Mark `// PROBE-EYES1`.
When a NEW merged state line is started for a textured draw with psm == 0x14 (4-bit), also remember, and print
after that line in eyes1FlushLineLocked:
  `  clut csa=<csa> cld=<cld> cbp0=<n/a ok to omit>: <16 entries as RRGGBBAA hex>`
The palette is the active CLUT buffer returned by ps2xRdActiveClut() (const uint16_t[512]): for CT32 palettes
entry i = lo word clut[(csa*16+i)] | hi word clut[256+(csa*16+i)] << 16, little-endian R,G,B,A.
Copy the 16 values at record time (not at flush time).
Also print once per such line the first 16 bytes of the texture in GS local memory if easily reachable at that
point; otherwise skip that part. Reply in 2 lines.
