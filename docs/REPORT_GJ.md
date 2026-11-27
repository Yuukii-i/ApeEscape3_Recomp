# Task GJ Report: Closed Forms of Clipper Setup & Plane Passes (2900..2CD0)

## Executive Summary
Task GJ derived, implemented, and verified independent closed forms for the clipper setup and the six view-frustum plane passes (`0x2900..0x2CD0`).

All 15 candidate region-0 entry PCs in this address range (each with 200 records in the capture) were evaluated using the closed-form engine [`tools/vu1gen/hclipa_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclipa_check.py). Across all tested records, the closed form achieved **zero mismatches and zero unverified fields** across 46,500 checked fields.

---

## Candidate Entry Points (Region 0, [0x2900, 0x2CD0])

| Entry PC | Role / Phase | Records in Capture | Records Tested | Mismatches | Unverified |
|---|---|---|---|---|---|
| `0x2908` | Clipper context save & register spill | 200 | 20 | 0 | 0 |
| `0x29D8` | Plane buffer & matrix constants setup | 200 | 20 | 0 | 0 |
| `0x2A50` | Plane 0 (+X Right) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2A60` | Plane 0 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2AB8` | Plane 1 (-X Left) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2AC8` | Plane 1 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2B28` | Plane 2 (+Y Top) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2B38` | Plane 2 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2B90` | Plane 3 (-Y Bottom) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2BA0` | Plane 3 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2C00` | Plane 4 (+Z Far) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2C10` | Plane 4 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2C68` | Plane 5 (-Z Near) test & BAL subroutine | 200 | 20 | 0 | 0 |
| `0x2C78` | Plane 5 post-pass & buffer flip | 200 | 20 | 0 | 0 |
| `0x2CB8` | Epilogue: strip emit & JR vi15 return | 200 | 20 | 0 | 0 |

**Totals**: 15 entries $\times$ 20 records $\times$ 155 fields = **46,500 fields compared, 0 mismatches, 0 unverified**.

---

## Verification Output (`python tools/vu1gen/hclipa_check.py 20`)

```text
=== Task GJ: Closed Forms of Clipper Setup & Plane Passes (2900..2CD0) ===
Candidate entries in [0x2900, 0x2CD0] (records >= 20):
  Entry 0x2908: 200 records in capture
  Entry 0x29D8: 200 records in capture
  Entry 0x2A50: 200 records in capture
  Entry 0x2A60: 200 records in capture
  Entry 0x2AB8: 200 records in capture
  Entry 0x2AC8: 200 records in capture
  Entry 0x2B28: 200 records in capture
  Entry 0x2B38: 200 records in capture
  Entry 0x2B90: 200 records in capture
  Entry 0x2BA0: 200 records in capture
  Entry 0x2C00: 200 records in capture
  Entry 0x2C10: 200 records in capture
  Entry 0x2C68: 200 records in capture
  Entry 0x2C78: 200 records in capture
  Entry 0x2CB8: 200 records in capture

Entry 0x2908: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x29D8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2A50: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2A60: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2AB8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2AC8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2B28: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2B38: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2B90: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2BA0: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2C00: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2C10: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2C68: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2C78: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2CB8: records 20, fields compared 3100, mismatches 0, unverified 0
```

---

## Verified Field Classes (Per Record)
Every tested record checks 155 fields across 10 distinct classes:
1. `vi`: 16 registers
2. `vf`: 32 registers $\times$ 4 lanes = 128 words
3. `acc`: 4 lanes
4. `q`: 1 word
5. `status`: 1 word
6. `mac`: 1 word
7. `clip`: 1 word
8. `mem diff`: full byte comparison of VU memory against record diff
9. `cycles`: total elapsed cycle count
10. `pc`: exit dispatcher return PC (`0x0028`)

---

## Deliverables
- [`tools/vu1gen/hclipa_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclipa_check.py): Self-contained closed-form verifier.
- [`docs/VU1_CLIP_FORMS_A.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_CLIP_FORMS_A.md): Closed-form mathematical specifications for setup, plane passes, and epilogue.
- [`docs/REPORT_GJ.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GJ.md): Acceptance and verification report.
