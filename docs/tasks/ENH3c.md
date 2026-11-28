# ENH3c: read the stage name from the right place. Tiny task. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_enhance_profile.cpp, ps2xEnhanceProfileTick (~line 370-395).
Mark `// FEAT-ENH3`.
Instead of the name at 0x649650, read the NUL-terminated string at guest 0x649448 (max 63 chars), which holds
"/stage/<name>". Valid only if it starts with "/stage/" and the remainder (1..31 chars, stop at NUL) is all in
[a-z0-9_]; the stage name is that remainder. Otherwise "no stage".
Also: whenever the raw string differs from the previously seen raw string, log with ps2xSafeLog
`[enh] stagebuf "<first 48 printable chars, other bytes as '.'>"`.
Reply in 2 lines.
