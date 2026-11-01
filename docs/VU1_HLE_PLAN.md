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
