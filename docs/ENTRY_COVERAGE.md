# Capture Coverage Map: logs/vu1regions.bin

## 1. Overview and Summary Statistics
The `logs/vu1regions.bin` capture dataset contains **36,388 records** across two region configurations:
- **Region 0** (Command-stream & geometry processing): 35,388 records across 177 distinct entry PCs.
- **Region 1** (Dispatcher loop): 1,000 records across 5 distinct entry PCs (`0008`, `0010`, `0028`, `0030`, `0040`).

---

## 2. Top 15 Overall Capture Entries by Total Cycles

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

## 3. Disassembly of Top 15 Non-Verified Entries (First 6 Instructions)

### 1. Entry `0x24E0` (648,232 cycles, 200 recs)
```text
24E0: NOP                              | BAL 0
24E8: MINIi.xyzw vf13, vf13, vf0       | BAL 118
24F0: NOP                              | MOVE.w vf15, vf7
24F8: MULAz.w ACC, vf0, vf5            | ILW.x vi7, 1(vi4)
2500: MADDq.w vf9, vf5, vf0            | MOVE.xyzw vf28, vf29
2508: ADDz.xyzw vf30, vf31, vf0        | MOVE.xyzw vf29, vf10
```

### 2. Entry `0x29D8` (625,816 cycles, 200 recs)
```text
29D8: NOP                              | SQ.xyzw vf11, 919(vi0)
29E0: NOP                              | SQ.xyzw vf12, 922(vi0)
29E8: NOP                              | SQ.xyzw vf11, 928(vi0)
29F0: SUBw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 2048
29F8: NOP                              | IADDIU vi6, vi0, 32
2A00: NOP                              | IADDIU vi7, vi0, 2
```

### 3. Entry `0x2908` (593,126 cycles, 200 recs)
```text
2908: NOP                              | ISW.y vi6, 1022(vi0)
2910: NOP                              | ISW.z vi7, 1022(vi0)
2918: NOP                              | ISW.w vi8, 1022(vi0)
2920: NOP                              | ISW.x vi9, 1021(vi0)
2928: NOP                              | ISW.y vi10, 1021(vi0)
2930: NOP                              | ISW.z vi11, 1021(vi0)
```

### 4. Entry `0x2A50` (591,342 cycles, 200 recs)
```text
2A50: CLIP.xyz ACC, vf17, vf17         | BAL 108
2A58: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)
2A60: ADDw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 1024
2A68: NOP                              | IADDIU vi6, vi0, 16
2A70: NOP                              | IADDIU vi8, vi0, 952
2A78: NOP                              | IADDIU vi9, vi0, 918
```

### 5. Entry `0x2E00` (591,298 cycles, 200 recs)
```text
2E00: NOP                              | IBNE vi1, vi0, 14
2E08: NOP                              | IADDIU vi1, vi0, 1484
2E10: NOP                              | B 22
2E18: NOP                              | IADDIU vi11, vi11, 1
2E20: NOP                              | SQI.xyzw vf17, (vi9++)
2E28: NOP                              | SQI.xyzw vf18, (vi9++)
```

### 6. Entry `0x2E10` (589,230 cycles, 200 recs)
```text
2E10: NOP                              | B 22
2E18: NOP                              | IADDIU vi11, vi11, 1
2E20: NOP                              | SQI.xyzw vf17, (vi9++)
2E28: NOP                              | SQI.xyzw vf18, (vi9++)
2E30: NOP                              | IBNE vi1, vi0, 3
2E38: NOP                              | SQI.xyzw vf19, (vi9++)
```

### 7. Entry `0x2DE0` (588,722 cycles, 200 recs)
```text
2DE0: MULx.w vf25, vf17, vf20          | IAND vi13, vi1, vi5
2DE8: MULx.w vf26, vf21, vf20          | IAND vi1, vi1, vi6
2DF0: NOP                              | IBEQ vi13, vi0, 4
2DF8: NOP                              | LQI.xyzw vf23, (vi8++)
2E00: NOP                              | IBNE vi1, vi0, 14
2E08: NOP                              | IADDIU vi1, vi0, 1484
```

### 8. Entry `0x2E18` (588,603 cycles, 200 recs)
```text
2E18: NOP                              | IADDIU vi11, vi11, 1
2E20: NOP                              | SQI.xyzw vf17, (vi9++)
2E28: NOP                              | SQI.xyzw vf18, (vi9++)
2E30: NOP                              | IBNE vi1, vi0, 3
2E38: NOP                              | SQI.xyzw vf19, (vi9++)
2E40: ADDx.xyzw vf17, vf21, vf0        | JR vi15
```

### 9. Entry `0x2EC8` (579,636 cycles, 200 recs)
```text
2EC8: SUBw.xyzw vf25, vf17, vf25       | IBEQ vi7, vi0, 5
2ED0: SUBw.xyzw vf26, vf21, vf26       | IADD vi13, vi0, vi7
2ED8: NOP                              | ISUBIU vi13, vi13, 1
2EE0: NOP                              | MR32.xyzw vf25, vf25
2EE8: NOP                              | IBNE vi13, vi0, -3
2EF0: NOP                              | MR32.xyzw vf26, vf26
```

### 10. Entry `0x2DB8` (576,164 cycles, 200 recs)
```text
2DB8: ADDx.xyzw vf19, vf23, vf0        | ISUBIU vi10, vi10, 1
2DC0: NOP                              | ISUBIU vi15, vi12, 2
2DC8: NOP                              | IBNE vi10, vi0, 2
2DD0: NOP                              | FCGET vi1
2DD8: NOP                              | IADDIU vi15, vi0, 1489
2DE0: MULx.w vf25, vf17, vf20          | IAND vi13, vi1, vi5
```

### 11. Entry `0x2A60` (572,853 cycles, 200 recs)
```text
2A60: ADDw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 1024
2A68: NOP                              | IADDIU vi6, vi0, 16
2A70: NOP                              | IADDIU vi8, vi0, 952
2A78: NOP                              | IADDIU vi9, vi0, 918
2A80: NOP                              | IADD vi10, vi0, vi11
2A88: NOP                              | IADDIU vi11, vi0, 0
```

### 12. Entry `0x2EF8` (572,814 cycles, 200 recs)
```text
2EF8: SUB.x vf27, vf26, vf25           | MOVE.x vf24, vf25
2F00: ADDx.y vf24, vf0, vf26           | DIV Q, vf0.w, vf27.x
2F08: ABS.xy ACC, vf24, vf24           | MOVE.- vf0, vf0
2F10: ADDq.z vf24, vf0, vf0            | WAITQ
2F18: MULAy.xyzw ACC, vf17, vf24       | LQ.xyzw vf17, 1012(vi0)
2F20: MADDx.xyzw vf25, vf21, vf24      | MOVE.- vf0, vf0
```

### 13. Entry `0x2E88` (564,396 cycles, 200 recs)
```text
2E88: NOP                              | IBEQ vi11, vi0, -40
2E90: NOP                              | LQ.xyzw vf25, 0(vi14)
2E98: NOP                              | LQ.xyzw vf26, 1(vi14)
2EA0: NOP                              | LQ.xyzw vf27, 2(vi14)
2EA8: NOP                              | SQI.xyzw vf25, (vi9++)
2EB0: MULA.xyzw ACC, vf1, vf25         | SQI.xyzw vf26, (vi9++)
```

### 14. Entry `0x2DD8` (562,609 cycles, 200 recs)
```text
2DD8: NOP                              | IADDIU vi15, vi0, 1489
2DE0: MULx.w vf25, vf17, vf20          | IAND vi13, vi1, vi5
2DE8: MULx.w vf26, vf21, vf20          | IAND vi1, vi1, vi6
2DF0: NOP                              | IBEQ vi13, vi0, 4
2DF8: NOP                              | LQI.xyzw vf23, (vi8++)
2E00: NOP                              | IBNE vi1, vi0, 14
```

### 15. Entry `0x2E50` (551,354 cycles, 200 recs)
```text
2E50: NOP                              | BAL 14
2E58: NOP                              | IADDIU vi11, vi11, 1
2E60: NOP                              | SQI.xyzw vf25, (vi9++)
2E68: NOP                              | SQI.xyzw vf26, (vi9++)
2E70: NOP                              | SQI.xyzw vf27, (vi9++)
2E78: ADDx.xyzw vf17, vf21, vf0        | JR vi15
```
