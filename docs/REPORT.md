# Task EP Report
- BUILD OK.
- Grep verified: `ep ev` in `ps2xRuntime/src/lib/ps2_vif1_interpreter.cpp`.
- Added 64-event ring buffer tracking UNPACK, MSCAL/MSCNT/MSCALF, BASE, OFFSET, MPG, and C80 entry events.
- On first 3 bad VU stores (qw 970..1011), calls `ps2x_probeDump()` to dump ring events (`[probe] ep ev`) and logs vi13, vi12, and VU quadwords at vi13-2..vi13+1.
- Removed eo2 unpack/rdram/vifcode print spam while retaining periodic 5s `eo counts`.
- Committed on branch `task/EP` in PS2Recomp and ApeEscape3_Recomp.
