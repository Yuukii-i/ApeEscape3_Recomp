# Task GK Report: Closed Forms of Clipper Edge Interpolator & Strip Assembly (2CD8..2F08)

## Executive Summary
Task GK derived, implemented, and verified independent closed forms for the clipper's edge interpolator, polygon edge dispatcher, and strip assembly routines (`0x2CD8..0x2F08`).

All 18 candidate region-0 entry PCs in this address range (each with 200 records in the capture) were evaluated using the closed-form verification tool [`tools/vu1gen/hclipb_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclipb_check.py). Across all tested records, the closed form achieved **zero mismatches and zero unverified fields** across 55,800 checked fields.

---

## Candidate Entry Points (Region 0, [0x2CD8, 0x2F08])

| Entry PC | Role / Subsystem | Records in Capture | Records Tested | Mismatches | Unverified |
|---|---|---|---|---|---|
| `0x2D48` | Interpolator loop continuation check | 200 | 20 | 0 | 0 |
| `0x2D50` | Interpolator inner edge setup | 200 | 20 | 0 | 0 |
| `0x2DA8` | Interpolator subroutine return (`JR vi12`) | 200 | 20 | 0 | 0 |
| `0x2DB8` | Edge dispatcher loop head | 200 | 20 | 0 | 0 |
| `0x2DD8` | Edge dispatcher return address setup | 200 | 20 | 0 | 0 |
| `0x2DE0` | Edge dispatcher plane mask test | 200 | 20 | 0 | 0 |
| `0x2E00` | Inside edge check branch | 200 | 20 | 0 | 0 |
| `0x2E10` | Next edge jump | 200 | 20 | 0 | 0 |
| `0x2E18` | Preserved vertex output setup | 200 | 20 | 0 | 0 |
| `0x2E40` | Preserved vertex return (`JR vi15`) | 200 | 20 | 0 | 0 |
| `0x2E50` | Strip fan header emit branch | 200 | 20 | 0 | 0 |
| `0x2E60` | Strip fan vertex emit | 200 | 20 | 0 | 0 |
| `0x2E78` | Strip fan return (`JR vi15`) | 200 | 20 | 0 | 0 |
| `0x2E88` | Strip assembly loop head | 200 | 20 | 0 | 0 |
| `0x2E98` | Strip quadword reload | 200 | 20 | 0 | 0 |
| `0x2EC8` | Strip winding rotation check | 200 | 20 | 0 | 0 |
| `0x2ED8` | Triangle winding vertex rotate (`MR32`) | 200 | 20 | 0 | 0 |
| `0x2EF8` | Parametric intersection calculation | 200 | 20 | 0 | 0 |

**Totals**: 18 entries $\times$ 20 records $\times$ 155 fields = **55,800 fields compared, 0 mismatches, 0 unverified**.

---

## Verification Output (`python tools/vu1gen/hclipb_check.py 20`)

```text
=== Task GK: Closed Forms of Edge Interpolator & Strip Assembly (2CD8..2F08) ===
Candidate entries in [0x2CD8, 0x2F08] (records >= 20):
  Entry 0x2D48: 200 records in capture
  Entry 0x2D50: 200 records in capture
  Entry 0x2DA8: 200 records in capture
  Entry 0x2DB8: 200 records in capture
  Entry 0x2DD8: 200 records in capture
  Entry 0x2DE0: 200 records in capture
  Entry 0x2E00: 200 records in capture
  Entry 0x2E10: 200 records in capture
  Entry 0x2E18: 200 records in capture
  Entry 0x2E40: 200 records in capture
  Entry 0x2E50: 200 records in capture
  Entry 0x2E60: 200 records in capture
  Entry 0x2E78: 200 records in capture
  Entry 0x2E88: 200 records in capture
  Entry 0x2E98: 200 records in capture
  Entry 0x2EC8: 200 records in capture
  Entry 0x2ED8: 200 records in capture
  Entry 0x2EF8: 200 records in capture

Entry 0x2D48: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2D50: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2DA8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2DB8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2DD8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2DE0: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E00: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E10: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E18: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E40: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E50: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E60: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E78: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E88: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2E98: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2EC8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2ED8: records 20, fields compared 3100, mismatches 0, unverified 0
Entry 0x2EF8: records 20, fields compared 3100, mismatches 0, unverified 0
```

---

## Special Care Requirements Addressed
1. **Divide Landing & Q Pipeline Mechanics**:
   `DIV Q, vf0.w, vf27.x` has a 13-cycle latency and is followed immediately by `WAITQ`. The quotient $Q = \text{divq}(1.0, \Delta)$ lands before subsequent `MULq` instructions execute. No divide remains pending at region exit ($fdiv = (0, -\text{readyCycle}, 0, 0)$).
2. **Strip Assembly Vertex Output (`SQI.xyzw (vi9++)`)**:
   Emits 3 quadwords per vertex: Position XYZW (`ftoi(..., 16)`), Texture ST (`fmac(MUL, S, Q, 0)`), and Color RGBA (`ftoi(clamp(C, 0, 255), 1)`).
3. **Cycle Cost & Data Dependencies**:
   - Edge intersection: 34 cycles / edge (dominated by 13-cycle `DIV Q` and `WAITQ`).
   - Preserved inside edge: 10 cycles / edge.
   - Discarded edge: 8 cycles / edge.
   - Emitted vertex output: 12 cycles / vertex.

---

## Deliverables
- [`tools/vu1gen/hclipb_check.py`](file:///c:/ApeEscape3_Recomp/tools/vu1gen/hclipb_check.py): Self-contained closed-form verifier.
- [`docs/VU1_CLIP_FORMS_B.md`](file:///c:/ApeEscape3_Recomp/docs/VU1_CLIP_FORMS_B.md): Mathematical closed-form specifications for edge interpolation, edge dispatching, and strip assembly.
- [`docs/REPORT_GK.md`](file:///c:/ApeEscape3_Recomp/docs/REPORT_GK.md): Acceptance and verification report.
