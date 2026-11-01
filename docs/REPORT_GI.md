# Task GI Report: Real Clipping of the Vertex Routine (2900..2F00)

## Executive Summary
Task GI investigated and verified the execution of the real clipping subsystem in the VU1 vertex routine (`0x2900..0x2F08`) when trivial rejection at `0x28A0..0x28F8` fails.

All clipping records in the capture were identified, verified against `Model.run`, disassembled into block-by-block annotated assembly, and analyzed for memory store provenance and canonical expression diversity.

---

## Item 1: Record Selection and Counts
Clipping records were identified using two complementary selection criteria:
1. **Entry `0x2440` declining trivial reject**:
   Evaluated against the reference functional spec [`tools/vu1gen/vspec.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/vspec.py). Records where `vspec.Spec.run()` returns `None` (none of the six `FCOR` trivial-reject tests hit) invoke real clipping.
   - Total `0x2440` records: **200**
   - Non-clipping (handled by `vspec`): **145** (72.5%)
   - Real clipping (declined by `vspec`): **55** (27.5%)
2. **Region entries starting directly in `[0x2900, 0x2F00]`**:
   Scanned region 0 records for entries located inside the clipping routine.
   - Total records: **6,600**
   - Distinct entry PCs: **33** (200 records each: `0x2908`, `0x29D8`, `0x2A50`, `0x2DB8`, `0x2DE0`, `0x2E00`, `0x2E18`, `0x2E40`, `0x2EF8`, etc.).

**Total clipping records identified**: **6,655 records** ($55 + 6,600$).

---

## Item 2: Model Run Verification & Conformance

Tested with [`tools/vu1gen/hclip_prov.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclip_prov.py):
1. **Model compatibility on `0x2440` clipping records**:
   - Total records tested: **55**
   - Missing ops: **0**
   - Missing block metadata: **0**
   - Success rate: **100% (55 / 55)**
2. **Model compatibility on standalone clipping entries (`0x2900..0x2F00`)**:
   - Total distinct entry PCs: **33**
   - Runnable PCs: **33** (100%)
   - Blocked PCs: **0**
3. **Exit state comparison against record exit (`x`)**:
   Evaluated 153 fields per record across all 55 `0x2440` real clipping records:
   - `vi` (16 registers): 0 mismatches
   - `vf` (128 words): 0 mismatches
   - `acc` (4 lanes): 0 mismatches
   - `q` (1 word): 0 mismatches
   - `status` (1 word): 0 mismatches
   - `cycle` (1 field): 0 mismatches (exact cycle match to ground truth)
   - `mem diff` (1 field): 0 mismatches (exact byte match to ground truth)
   - `pc` (1 field): 0 mismatches (`0x0028`)

**Result**: **55 records, 8,415 fields compared, 0 mismatches, 0 unverified**.

---

## Item 3: Disassembly, Plane Clipping & Cycle Cost

The full block-by-block disassembly is documented in [`docs/VU1_CLIP_ASM.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_CLIP_ASM.md).

### Frustum Plane Architecture
The clipper executes Sutherland-Hodgman polygon clipping sequentially across 6 frustum planes:
- **Plane 0 (+X, Right)**: `0x2A50` (`BAL 108` to `0x2DC0`), plane bitmask `1024` (`0x0400`)
- **Plane 1 (-X, Left)**: `0x2AB8` (`BAL 95` to `0x2DC0`), plane bitmask `2048` (`0x0800`)
- **Plane 2 (+Y, Top)**: `0x2B28` (`BAL 81` to `0x2DC0`), plane bitmask `4096` (`0x1000`)
- **Plane 3 (-Y, Bottom)**: `0x2B90` (`BAL 68` to `0x2DC0`), plane bitmask `8192` (`0x2000`)
- **Plane 4 (+Z, Far)**: `0x2C00` (`BAL 54` to `0x2DC0`), plane bitmask `16384` (`0x4000`)
- **Plane 5 (-Z, Near)**: `0x2C68` (`BAL 41` to `0x2DC0`), plane bitmask `-32768` (`0x8000`)

### Per-Iteration Cycle Cost Breakdown
- **Edge intersection interpolation (`0x2CD8..0x2DA8`)**: **34 cycles / edge** (dominated by 13-cycle `DIV Q` and `WAITQ` reciprocal pipeline).
- **Preserved inside vertex**: **10 cycles / edge** (loads, formats, and stores XYZW, ST, RGBA to ping-pong buffer).
- **Discarded outside vertex**: **8 cycles / edge**.
- **Plane setup / ping-pong swap**: **14 cycles / plane**.
- **Strip output emission (`0x2E48..0x2EC0`)**: **12 cycles / emitted vertex** (3 quadwords via `SQI.xyzw (vi9++)`).

---

## Item 4: Clipper Memory Stores & Canonical Expression Table

The memory writes performed by the clipper belong to four distinct classes:
1. **Context & Header Save**: Integer stores at `0x2900..0x2950` saving registers to quadwords 1020..1022.
2. **Scratchpad Spill**: Float matrix and vertex scratchpad backup at `0x2968..0x29E8` to quadwords 918..928.
3. **Parametric Edge Interpolation**: Float stores at `0x2D20, 0x2D28, 0x2D30, 0x2D40` generating newly clipped intersection vertices.
4. **Vertex Output Stream Generation**: Float stores at `0x2E20` (XYZW position), `0x2E28` (ST coordinates), and `0x2E38` (RGBA color).

### Canonical Expression Table (`tools/vu1gen/hclip_prov.py`)

| Store PC | Lane | Kind | Total Stores | Distinct Canonical Expressions | Functional Role |
|---|---|---|---|---|---|
| `0x2900` | 0 | int | 253 | 18 | Save vertex counter `vi5` to 1022.x |
| `0x2908` | 1 | int | 172 | 36 | Save output pointer `vi6` to 1022.y |
| `0x2910` | 2 | int | 172 | 50 | Save vertex index `vi7` to 1022.z |
| `0x2918` | 3 | int | 172 | 3 | Save pointer `vi8` to 1022.w |
| `0x2920` | 0 | int | 172 | 2 | Save pointer `vi9` to 1021.x |
| `0x2928` | 1 | int | 172 | 2 | Save pointer `vi10` to 1021.y |
| `0x2930` | 2 | int | 172 | 1 | Save pointer `vi11` to 1021.z |
| `0x2940` | 3 | int | 172 | 1 | Save link `vi12` to 1021.w |
| `0x2948` | 0 | int | 172 | 4 | Save stream pointer `vi13` to 1020.x |
| `0x2950` | 1 | int | 172 | 1 | Save return address `vi15` to 1020.y |
| `0x2968` | 0..3 | float | 172 | 2 | Spill register `vf28` |
| `0x2970` | 0..3 | float | 172 | 1 | Spill register `vf29` |
| `0x2978` | 0..3 | float | 172 | 1 | Spill register `vf10` |
| `0x2980` | 0..3 | float | 172 | 2 | Spill initial vertex 0 pos |
| `0x2988` | 0..3 | float | 172 | 1..2 | Spill initial vertex 0 st |
| `0x2990` | 0..3 | float | 172 | 1 | Spill initial vertex 0 rgba |
| `0x2998` | 0..3 | float | 172 | 1 | Spill initial vertex 1 pos |
| `0x29A0` | 0..3 | float | 172 | 18 | Spill initial vertex 1 st |
| `0x29B0` | 0..3 | float | 172 | 1..2 | Spill initial vertex 1 rgba |
| `0x29D8` | 0..3 | float | 172 | 42 | Frustum plane constant quad 919 |
| `0x29E0` | 0..3 | float | 172 | 40 | Frustum plane constant quad 922 |
| `0x29E8` | 0..3 | float | 172 | 42 | Frustum plane constant quad 928 |
| `0x2C88` | 0 | int | 161 | 3 | Save final clipped vertex count |
| `0x2D20` | 0..3 | float | 583 | 249..303 | Interpolated vertex POS (XYZW) |
| `0x2D28` | 0..3 | float | 583 | 323 | Interpolated vertex ST coordinates |
| `0x2D30` | 0..3 | float | 583 | 303 | Interpolated vertex RGBA color |
| `0x2D40` | 3 | float | 583 | 303 | Interpolated W scalar |
| `0x2E20` | 0..3 | float | 2863 | 532 | Clipped strip vertex POS output |
| `0x2E28` | 0..3 | float | 2863 | 876 | Clipped strip vertex ST output |
| `0x2E38` | 0..3 | float | 2863 | 602..632 | Clipped strip vertex RGBA output |
| `0x2E60` | 0..3 | float | 482 | 287 | Fan vertex POS output |
| `0x2E68` | 0..3 | float | 482 | 295 | Fan vertex ST output |
| `0x2E70` | 0..3 | float | 482 | 280..287 | Fan vertex RGBA output |
| `0x2EA8` | 0..3 | float | 999 | 78 | Final strip POS emit |
| `0x2EB0` | 0..3 | float | 999 | 118 | Final strip ST emit |
| `0x2EC0` | 0..3 | float | 999 | 244..255 | Final strip RGBA emit |

---

## Deliverables
- [`tools/vu1gen/hclip_prov.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclip_prov.py): Verification tool and canonical provenance extractor.
- [`docs/VU1_CLIP_ASM.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_CLIP_ASM.md): Annotated disassembly and cycle cost analysis of `2900..2F08`.
- [`docs/REPORT_GI.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GI.md): Comprehensive findings and acceptance report.
