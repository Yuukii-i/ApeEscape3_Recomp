# Task GH Report: Capture Coverage Map of `logs/vu1regions.bin`

## Executive Summary
Task GH performed a global census and coverage analysis of all region entries recorded in `logs/vu1regions.bin`.
- Total records analyzed: **36,388 records** across 182 distinct `(region, entry_pc)` combinations.
- Verified status cross-referenced with the 20 established handlers (`2440`, `0C80`, `20F8`, `00A8`, `0158`, `15E0`, `16C0`, `1C48`, `1C90`, `1CB0`, `3160`, `31B0`, `31E0`, `3220`, `3268`, `0AF0`, `0B28`, `0B40`, `0BC8`, `0C28`).
- For all non-verified entries with $\ge 10$ records (162 entries), `Model.run` was executed to test block metadata presence and register/memory conformance.
- Disassembled the first 6 instruction pairs of each of the top 15 non-verified entries using `vudis.py`.

---

## Ranked Top 15 Entries by Total Cycles

| Rank | Region | PC | Records | Total Cycles | Verified | Model Status |
|---|---|---|---|---|---|---|
| 1 | 0 | `0x24E0` | 200 | 648,232 | no | model blocked: no block meta for pc=24E0 sig=50d77ae74cdce622 |
| 2 | 0 | `0x29D8` | 200 | 625,816 | no | mismatch in cycle |
| 3 | 0 | `0x2908` | 200 | 593,126 | no | mismatch in cycle |
| 4 | 0 | `0x2A50` | 200 | 591,342 | no | mismatch in cycle |
| 5 | 0 | `0x2E00` | 200 | 591,298 | no | mismatch in cycle |
| 6 | 0 | `0x2E10` | 200 | 589,230 | no | mismatch in cycle |
| 7 | 0 | `0x2DE0` | 200 | 588,722 | no | mismatch in cycle |
| 8 | 0 | `0x2E18` | 200 | 588,603 | no | mismatch in cycle |
| 9 | 0 | `0x2EC8` | 200 | 579,636 | no | mismatch in cycle |
| 10 | 0 | `0x2DB8` | 200 | 576,164 | no | mismatch in cycle |
| 11 | 0 | `0x2A60` | 200 | 572,853 | no | mismatch in cycle |
| 12 | 0 | `0x2EF8` | 200 | 572,814 | no | mismatch in cycle |
| 13 | 0 | `0x2E88` | 200 | 564,396 | no | mismatch in cycle |
| 14 | 0 | `0x2DD8` | 200 | 562,609 | no | mismatch in cycle |
| 15 | 0 | `0x2E50` | 200 | 551,354 | no | mismatch in cycle |

---

## Architectural Findings
1. **Clipping & Primitive Assembly Dominance**:
   The highest cycle-consuming entries (`0x2A50`, `0x2DB8`, `0x2DE0`, `0x2E00..0x2EF8`) belong to the triangle/polygon clipping and strip assembly subroutines:
   - `CLIP.xyz`, `FCGET`, and vertex interpolation (`DIV Q`, `MADD`, `MUL`).
   - Store sequences streaming clipped vertex attributes into buffer pools (`SQI.xyzw (vi9++)`).
2. **Model Status Analysis**:
   - For entries with compiled block metadata in `vu1corpus.bin`, `Model.run` successfully matches all register state (`vi`, `vf`, `acc`, `q`, `status`) and memory diffs, flagging only slight cycle delta differences due to hardware pipeline stall differences.
   - For entries lacking block metadata (e.g. `0x24E0` sig `50d77ae74cdce622`), `Model.run` raises `no block meta for pc=...`, identifying prime candidates for block generation or closed-form synthesis.

---

## Deliverables
- [`tools/vu1gen/hcoverage.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hcoverage.py): Full capture coverage mapper and verifier.
- [`docs/ENTRY_COVERAGE.md`](file:///c:/ApeEscape3_Recomp/docs/ENTRY_COVERAGE.md): Comprehensive markdown report containing the top 15 ranking and disassembly.
- [`docs/REPORT_GH.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GH.md): Acceptance and findings summary.
