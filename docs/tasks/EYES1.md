# EYES1: one-frame GS draw dump probe. Tiny task. Do NOT build/run/commit. No header edits.
File: PS2Recomp/ps2xRuntime/src/lib/gs/gs_frontend.cpp. Mark `// PROBE-EYES1`. No effect when env unset.
Env PS2X_GS_DRAWDUMP=<ms>: record every drawn primitive of ONE frame, the first whole frame starting at least <ms>
milliseconds after process start. Hook where rdGsDrawLogRecord is called (~line 576-660 shows it and the per-frame
hook rdGsDrawLogOnFrame); call yours from the same two places, independent of the PS2X_RD_GSDRAWLOG switch and of
its captured/geometry filters (record ALL primitives, any renderer setting).
Merge consecutive primitives with identical state into one line. State = prim register bits, tex0 (tbp0, psm, tw, th,
cbp, tfx, tcc; only if tme), ALPHA, TEST, FRAME fbmsk. Line format, written with fprintf to logs/gsdraws.txt:
`prim=%03x tbp=%04x psm=%02x %dx%d cbp=%04x tfx=%d al=%llx test=%llx msk=%x tris=%u rgba %u,%u,%u,%u..%u,%u,%u,%u bbox=%d,%d-%d,%d`
(untextured: tbp=0000 psm=00 0x0 cbp=0000 tfx=0). prim= type | iip<<3 | tme<<4 | fge<<5 | abe<<6.
bbox = screen pixels: vertex x/y minus xyoffset (as rdGsDrawLogRecord computes). rgba = per-channel min..max over
the vertices. Close the file after that frame and never record again. Reply in 2 lines.
