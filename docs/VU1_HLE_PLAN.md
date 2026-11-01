# VU1 native HLE: plan and state (2026-10-31)

Main image 86503d3905e35276 = command interpreter in threaded code. Dispatcher 0000-0048 (TOP -> first command, JR vi1, vi15 = 5 loop / 0 end).

## Done (exact, checked by replay + verifier + block-hash checks)
- Skinned-vertex routine 1FE0 (lbFull, lbLoop): ~34.6% of cycles.
- Copy handler 0C80/0C88/0CB0 (lbCopy): replay MISMATCHED=0 (2999 recs), verifier mismatches=0.

## Tooling (tools/vu1gen)
- lbmodel.py: functional + timing model driven by block tables (logs/vublk2_u1_*.txt, first file wins, needs cyc= from the current dump). Now runs any entry (pc, entry hash), supports CLIP/ABS/SQI/MFIR/MTIR/XTOP/IAND/IOR/IADDI/IBxx/BAL/FC* (+ clip ring 4-cycle visibility). FC* write vi1 directly (a branch right after sees the new value).
- regions.py: reader for logs/vu1regions.bin (probe v3 adds flag rings + working clip). vudis.py: fixed operand printing.
- clip4.py (scratchpad): per-entry exactness over the region capture. Result: 1056/2124 exact, 0 mismatches in the clip machine; rest = block variants not in the table.

## Decisions
- No Python port of the cycle scheduler: kernels hook on known entry hashes and decline others, so unknown timing variants are harmless (they fall back to blocks).
- Block-table variants only appear in live play (entry hash carries leftover pipeline state); the corpus replay and PS2X_VU1_NATIVE=0 (6 fps) do not add them usefully.

## Structure of the clip/assembly machine (~31% of cycles)
- 2440-25B0 and 2670-27D8 are the same per-vertex routine (variant reads LQ.xyz vf7,796(vi7)): transform -> DIV (Q) -> CLIP x3 -> FCAND/ADC bits -> FTOI -> SQ to GIF buffer (vi6). 23 pairs per vertex. BAL leaves to the 28xx clip subroutines (FCOR/IBNE chains) when a vertex fails the test.
- Entered by computed jumps at 8-byte steps (26F0..27D8, 24C8..25A8 one-pair blocks); tails 2DA8-2E18 (JR vi12, FCGET) and 27E0-2818 (XTOP, ISW, XGKICK).
- Next: Python closed form of the per-vertex routine (model first), then C++ kernel per iteration batch with fallback; then the 28xx subroutines.

## Open
- Model lacks FMAND/FSAND (0AF0-0BC8 family, 'lower op 1A'), OPMULA/OPMSUB, SQRT/RSQRT.
- Handlers entered while an XGKICK is active run on the slow path (~60-75 ms/s) and must be covered by the full HLE.

## Per-vertex routine closed form (derived 2026-10-31 with tools/vu1gen/vprov.py, 60 records, entry 2440)
Per vertex (software-pipelined: the stores at iteration k belong to the vertex loaded at k-1). Inputs: idx = vi7 & 0x7FFF where vi7 = index word (ILW.x vi7, 1(vi4)); P = quad 636+idx, A = quad 716+idx, constants vf1/vf2 (1002/1003), vf5.zw (1016), vf14 (1014), vf16 (scale, live from the caller), ST stream S (LQI via vi2), colour stream C (LQI via vi3). Copy at 2670 reads the S vector from quad 796+idx instead of the stream.
- W = vf2.w*P.w + (vf1.w*P.w)  (MULA then MADD, exact FMAC order); Q = 1/W (DIV vf0.w / W)
- XYZ out (SQ at 25A0 and 25B0, lanes 0..2): ftoi4( (vf2.c*P.w + vf1.c*P.c) * Q )
- Out w lane: ftoi4( clamp(vf5.w*Q + vf5.z*1.0, 0, 255) + adc ), adc = 2048.0 if the index word has the skip bit (vi7 sign) else 0.0 (this gives the ADC bit 0x8000 in the GS word)
- ST out (SQ.xyz at 2538): S.c * Q
- RGBA out (SQ at 2598): ftoi0( clamp( A.c*col + vf14.c*col , 0, 255) ), col = C.c * vf16.c
- All the min/max chains seen (min,max,min,max / min,min,max / min,max) are the same clamp.
- Control: IBLTZ vi7 skips the clip call, IBLEZ vi8 skips it, else BAL to the 28xx clip subroutines (kernel declines those iterations). Loop end IBNE vi5. Prologue 2440-24C0, epilogue 25B8-2818 (XTOP, ISW vi6/vi7 at 1023, XGKICK vi7).
Next: Python check of this per-vertex function against the model's stores (all lanes, all classes), then the full-routine spec (prologue and epilogue states, flags, clip ring pushes), then C++.

## Exit state is closed form (2026-10-31, tools/vu1gen/vexit.py)
76 records of entry 2440 without a clip subroutine: every vf lane (31 regs x 4), ACC (4) and Q has exactly ONE canonical expression relative to the last iteration. So the full exit state is a fixed function of the last vertices and the entry state (same situation as lbFull for the skinned routine).
Plan: generate the kernel's FP code from the canonical trees (emit C++ per register/store from the hash-consed nodes) instead of transcribing pairs; hand-write only the integer/control part (vi2..vi13 pointers, vi8/vi9/vi10 clip window, trip count, BAL decline), the cycle formula (a + b*n, from records) and the flag/ring/status effects (clip ring pushes, STATUS, MAC ring). Then check: model -> kernel spec (Python) -> replay/verifier/exit-hash in C++.

## Per-vertex stores verified (vcheck1.py, 40 records, 725 stores per lane, 0 mismatches)
ADC rule (w lane): adc = 2048.0 when the vertex index word is negative (IBLTZ vi7 path, MOVE.w vf15,vf7 in 24F0) or when the clip call (BAL) was taken; 0.0 only on the IBLEZ path (index >= 0 and window sum vi8 <= 0), where SUB.w vf15 = 0 at 24D8 stays.
Control per iteration (loop head 24C8): IBLTZ vi7 -> 24F0 (skips 24D8..24E8 completely, including their upper ops and the I=255 IMM); else IBLEZ vi8 -> 24F8 (delay slot 24E0 sets I=255); else BAL -> 28A0 clip chain, which returns with JR vi12 at 2DA8. vi8 = vi9+vi10+vi1 is a 3-vertex window of the FCAND 3F outside flags (initial -2).
IMPORTANT: the BAL path is the COMMON path (sample: 28A0 visited 4301 times vs 24F8 2557), so the kernel must include the 28A0..28E8 FCOR/IBNE trivial-test chain and the 2DA8 return; only real clipping (28F8+) can be declined.

## Trivial-reject chain 28A0..28F8 (checked on model traces, fcor.py)
Six FCOR tests, each in the delay slot of the previous IBNE: FCOR FDF7DF/FEFBEF/FF7DF7/FFBEFB/FFDF7D/FFEFBE at 28A0/28B0/28C0/28D0/28E0/28F0, IBNE vi1,vi0 at 28A8..28F8 jumping to 2DA8 (JR vi12 back to 24F8, delay slot 2DB0 a NOP). Each mask has zeros at one plane's bit in the three newest CLIP results (bits p, p+6, p+12), so a hit means all three vertices lie outside that plane = triangle trivially rejected. If none hits, control falls through to 2900+ (real clipping: the only part to decline).
Details that matter for exactness: (1) the FCOR in the delay slot of the taken IBNE still executes, so vi1 on return = the NEXT test's result; (2) all six tests read the same visible clip value (no CLIP issues inside the chain; ring visibility = newest push at least 4 cycles old); (3) a BAL iteration costs 41 cycles versus 27 for a plain one in the traced steady state, so the cycle model is per-path constants.
