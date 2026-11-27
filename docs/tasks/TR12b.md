# Task TR12b: fix gifCarriesFog. One file, small edit. No header edits. Do NOT build/run/commit.
File: c:\ApeEscape3_Recomp\PS2Recomp\ps2xRuntime\src\lib\vu\vu1_func.inc, helper gifCarriesFog (~2818-2856).
Observed: it returns false for 100% of calls, so it is not finding the geometry tag. A kick can hold several GIF
tags (setup A+D tag first). Rewrite the helper to take (gif, off, len) and walk all tags in [off, off+len):
 tag: lo,hi u64; nloop = lo & 0x7FFF; flg=(lo>>58)&3; nreg=(lo>>60)&0xF (0->16);
 data bytes: flg0 -> nloop*nreg*16; flg1 -> ((nloop*nreg+1)&~1)*8; else nloop*16. Stop at EOP (lo bit 15) or end.
 (The lean copy may hold only the 16-byte tag with NLOOP zeroed: that works, the loop just ends.)
 For each tag: if flg<2 and any of the nreg nibbles of hi is 0x4 or 0xC -> return true. If any nibble is 0x5 or
 0xD and none was 4/C -> remember sawXyz2. After the walk: return !sawXyz2 (i.e. unknown packets keep their fog).
 Update the three callers to pass gifLen.
 Also, when PS2X_RD_FOGSRC=1: print each distinct (lo & ~0x7FFFull, hi) pair of the walked tags once, at most 24
 pairs: "[fogtag] lo=%016llx hi=%016llx\n".
Reply in <=2 lines.
