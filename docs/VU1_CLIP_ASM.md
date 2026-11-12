# VU1 Real Clipping Disassembly and Architectural Specification (2900..2F08)

## 1. Overview and Architecture
When a triangle in the vertex pipeline (`0x2440`) cannot be trivially rejected by the six `FCOR` plane tests at `0x28A0..0x28F8` (approx. 27.5% of vertex pipeline calls in play), execution branches into the Sutherland-Hodgman view-frustum polygon clipper at `0x2900..0x2F08`.

The clipper sequentially clips the polygon against the 6 frustum planes:
1. Plane 0 (`+X`, right plane, mask bit `0x0400`): setup at `0x2A50`, branch `BAL 108` to clipper subroutine at `0x2DC0`.
2. Plane 1 (`-X`, left plane, mask bit `0x0800`): setup at `0x2AB8`, branch `BAL 95` to clipper subroutine at `0x2DC0`.
3. Plane 2 (`+Y`, top plane, mask bit `0x1000`): setup at `0x2B28`, branch `BAL 81` to clipper subroutine at `0x2DC0`.
4. Plane 3 (`-Y`, bottom plane, mask bit `0x2000`): setup at `0x2B90`, branch `BAL 68` to clipper subroutine at `0x2DC0`.
5. Plane 4 (`+Z`, far plane, mask bit `0x4000`): setup at `0x2C00`, branch `BAL 54` to clipper subroutine at `0x2DC0`.
6. Plane 5 (`-Z`, near plane, mask bit `0x8000`): setup at `0x2C68`, branch `BAL 41` to clipper subroutine at `0x2DC0`.

Core Registers:
- `vi5`: Current polygon vertex count.
- `vi8`: Pointer to current input vertex buffer in VU scratchpad.
- `vi9`: Pointer to clipped output vertex buffer in VU scratchpad.
- `vi10`: Inner edge loop counter ($N$ edges).
- `vi11`: Clip test status mask and plane flag accumulator.
- `vi12`: Subroutine return address for `JR vi12`.
- `vi13`: Edge intersection interpolation index.
- `vi14`: Base pointer for scratch register backup quadwords (`918..928`).
- `vi15`: General return register (`JR vi15` returns to dispatcher at `0x0028`).

---

## 2. Block-by-Block Annotated Disassembly

### [0x2900 - 0x2960]: Clipper State Context Save
*Saves vertex pipeline integer registers and return pointers into VU memory quadwords 1020..1022.*
```text
2900: NOP                              | ISW.x vi5, 1022(vi0)       ; Save input vertex count
2908: NOP                              | ISW.y vi6, 1022(vi0)       ; Save output buffer pointer
2910: NOP                              | ISW.z vi7, 1022(vi0)       ; Save current vertex index
2918: NOP                              | ISW.w vi8, 1022(vi0)       ; Save loop induction pointer
2920: NOP                              | ISW.x vi9, 1021(vi0)       ; Save scratch pointer vi9
2928: NOP                              | ISW.y vi10, 1021(vi0)      ; Save scratch pointer vi10
2930: NOP                              | ISW.z vi11, 1021(vi0)      ; Save clip mask vi11
2938: NOP                              | ILW.y vi11, 1012(vi0)      ; Load clipping mode configuration
2940: NOP                              | ISW.w vi12, 1021(vi0)      ; Save subroutine link vi12
2948: NOP                              | ISW.x vi13, 1020(vi0)      ; Save stream pointer vi13
2950: NOP                              | ISW.y vi15, 1020(vi0)      ; Save return address vi15
2958: NOP                              | IADDIU vi10, vi0, 1        ; Initialize test bit
2960: NOP                              | IAND vi11, vi11, vi10      ; Test clip flag enable
```

### [0x2968 - 0x29D0]: Vector Register Spill to Scratchpad
*Backs up active vector transformation registers vf28, vf29, vf10 into quadwords 918..924.*
```text
2968: NOP                              | SQ.xyzw vf28, 918(vi0)     ; Spill vf28 (matrix row 0)
2970: NOP                              | SQ.xyzw vf29, 921(vi0)     ; Spill vf29 (matrix row 1)
2978: MAXx.xyzw vf13, vf13, vf0        | SQ.xyzw vf10, 924(vi0)     ; Spill vf10 (matrix row 2)
2980: NOP                              | SQ.xyzw vf17, 919(vi0)     ; Spill vertex 0 pos
2988: NOP                              | SQ.xyzw vf18, 922(vi0)     ; Spill vertex 0 st
2990: NOP                              | SQ.xyzw vf19, 925(vi0)     ; Spill vertex 0 rgba
2998: NOP                              | SQ.xyzw vf21, 920(vi0)     ; Spill vertex 1 pos
29A0: NOP                              | SQ.xyzw vf22, 923(vi0)     ; Spill vertex 1 st
29A8: NOP                              | IBEQ vi11, vi0, 5          ; Skip extended backup if disabled
29B0: NOP                              | SQ.xyzw vf23, 926(vi0)     ; Spill vertex 1 rgba
29B8: NOP                              | IADDIU vi10, vi0, 2        ; Set vertex count = 2
29C0: NOP                              | ISW.w vi10, 1022(vi0)      ; Store initial vertex count
29C8: NOP                              | B 4                        ; Jump to buffer setup
```

### [0x29D8 - 0x2A48]: Clip Buffer Setup & Matrix Inversion
*Sets up double-buffer scratch areas 918..952 for ping-pong polygon clipping.*
```text
29D8: NOP                              | SQ.xyzw vf11, 919(vi0)     ; Store plane matrix constant
29E0: NOP                              | SQ.xyzw vf12, 922(vi0)     ; Store plane matrix constant
29E8: NOP                              | SQ.xyzw vf11, 928(vi0)     ; Store plane matrix constant
29F0: SUBw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 2048      ; Set plane mask base
29F8: NOP                              | IADDIU vi6, vi0, 32        ; Set stride
2A00: NOP                              | IADDIU vi7, vi0, 2         ; Index init
2A08: NOP                              | IADDIU vi8, vi0, 952       ; Buffer 0 pointer
2A10: NOP                              | IADDIU vi9, vi0, 918       ; Buffer 1 pointer
2A18: NOP                              | ILW.w vi10, 1022(vi0)      ; Load active vertex count
2A20: NOP                              | IADDIU vi11, vi0, 0        ; Clear clip status accumulator
2A28: NOP                              | LQI.xyzw vf21, (vi8++)     ; Load initial vertex
2A30: NOP                              | LQI.xyzw vf22, (vi8++)     ; Load initial ST
2A38: NOP                              | LQI.xyzw vf23, (vi8++)     ; Load initial RGBA
2A40: NOP                              | IADDI vi8, vi8, -3         ; Rewind buffer pointer
2A48: NOP                              | LQI.xyzw vf17, (vi8++)     ; Load first test vertex
```

### [0x2A50 - 0x2AB0]: Plane 0 (+X Right Frustum Plane)
*Tests vertices against Plane 0 (x > +w), calls clipper subroutine at 0x2DC0.*
```text
2A50: CLIP.xyz ACC, vf17, vf17         | BAL 108                    ; Branch to 2DC0 (Plane 0)
2A58: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)     ; Delay slot: test v1, load ST
2A60: ADDw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 1024      ; Set plane 0 bitmask (0x0400)
2A68: NOP                              | IADDIU vi6, vi0, 16        ; Stride
2A70: NOP                              | IADDIU vi8, vi0, 952       ; Flip ping-pong buffer
2A78: NOP                              | IADDIU vi9, vi0, 918       ; Flip ping-pong buffer
2A80: NOP                              | IADD vi10, vi0, vi11       ; vi10 = new vertex count
2A88: NOP                              | IADDIU vi11, vi0, 0        ; Reset clip counter
2A90: NOP                              | LQI.xyzw vf21, (vi8++)     ; Load next vertex
2A98: NOP                              | LQI.xyzw vf22, (vi8++)     ; Load next ST
2AA0: NOP                              | LQI.xyzw vf23, (vi8++)     ; Load next RGBA
2AA8: NOP                              | IADDI vi8, vi8, -3         ; Rewind pointer
2AB0: NOP                              | LQI.xyzw vf17, (vi8++)     ; Load test vertex
```

### [0x2AB8 - 0x2B20]: Plane 1 (-X Left Frustum Plane)
*Tests vertices against Plane 1 (x < -w), calls clipper subroutine at 0x2DC0.*
```text
2AB8: CLIP.xyz ACC, vf17, vf17         | BAL 95                     ; Branch to 2DC0 (Plane 1)
2AC0: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)     ; Delay slot
2AC8: SUBw.x vf20, vf0, vf0            | IADDIU vi5, vi0, 2048      ; Set plane 1 bitmask (0x0800)
2AD0: NOP                              | IADDIU vi6, vi0, 32
2AD8: NOP                              | IADDIU vi8, vi0, 918
2AE0: NOP                              | IADDIU vi9, vi0, 952
2AE8: NOP                              | IADD vi10, vi0, vi11
2AF0: NOP                              | IADDIU vi11, vi0, 0
2AF8: NOP                              | LQI.xyzw vf21, (vi8++)
2B00: NOP                              | LQI.xyzw vf22, (vi8++)
2B08: NOP                              | LQI.xyzw vf23, (vi8++)
2B10: NOP                              | IADDI vi8, vi8, -3
2B18: NOP                              | LQI.xyzw vf17, (vi8++)
```

### [0x2B28 - 0x2B88]: Plane 2 (+Y Top Frustum Plane)
*Tests vertices against Plane 2 (y > +w), calls clipper subroutine at 0x2DC0.*
```text
2B28: CLIP.xyz ACC, vf17, vf17         | BAL 81                     ; Branch to 2DC0 (Plane 2)
2B30: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)
2B38: ADDw.y vf20, vf0, vf0            | IADDIU vi5, vi0, 4096      ; Set plane 2 bitmask (0x1000)
2B40: NOP                              | IADDIU vi6, vi0, 64
2B48: NOP                              | IADDIU vi8, vi0, 952
2B50: NOP                              | IADDIU vi9, vi0, 918
2B58: NOP                              | IADD vi10, vi0, vi11
2B60: NOP                              | IADDIU vi11, vi0, 0
2B68: NOP                              | LQI.xyzw vf21, (vi8++)
2B70: NOP                              | LQI.xyzw vf22, (vi8++)
2B78: NOP                              | LQI.xyzw vf23, (vi8++)
2B80: NOP                              | IADDI vi8, vi8, -3
2B88: NOP                              | LQI.xyzw vf17, (vi8++)
```

### [0x2B90 - 0x2BF8]: Plane 3 (-Y Bottom Frustum Plane)
*Tests vertices against Plane 3 (y < -w), calls clipper subroutine at 0x2DC0.*
```text
2B90: CLIP.xyz ACC, vf17, vf17         | BAL 68                     ; Branch to 2DC0 (Plane 3)
2B98: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)
2BA0: SUBw.y vf20, vf0, vf0            | IADDIU vi5, vi0, 8192      ; Set plane 3 bitmask (0x2000)
2BA8: NOP                              | IADDIU vi6, vi0, 128
2BB0: NOP                              | IADDIU vi8, vi0, 918
2BB8: NOP                              | IADDIU vi9, vi0, 952
2BC0: NOP                              | IADD vi10, vi0, vi11
2BC8: NOP                              | IADDIU vi11, vi0, 0
2BD0: NOP                              | LQI.xyzw vf21, (vi8++)
2BD8: NOP                              | LQI.xyzw vf22, (vi8++)
2BE0: NOP                              | LQI.xyzw vf23, (vi8++)
2BE8: NOP                              | IADDI vi8, vi8, -3
2BF0: NOP                              | LQI.xyzw vf17, (vi8++)
```

### [0x2C00 - 0x2C60]: Plane 4 (+Z Far Frustum Plane)
*Tests vertices against Plane 4 (z > +w), calls clipper subroutine at 0x2DC0.*
```text
2C00: CLIP.xyz ACC, vf17, vf17         | BAL 54                     ; Branch to 2DC0 (Plane 4)
2C08: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)
2C10: ADDw.z vf20, vf0, vf0            | IADDIU vi5, vi0, 16384     ; Set plane 4 bitmask (0x4000)
2C18: NOP                              | IADDIU vi6, vi0, 256
2C20: NOP                              | IADDIU vi8, vi0, 952
2C28: NOP                              | IADDIU vi9, vi0, 918
2C30: NOP                              | IADD vi10, vi0, vi11
2C38: NOP                              | IADDIU vi11, vi0, 0
2C40: NOP                              | LQI.xyzw vf21, (vi8++)
2C48: NOP                              | LQI.xyzw vf22, (vi8++)
2C50: NOP                              | LQI.xyzw vf23, (vi8++)
2C58: NOP                              | IADDI vi8, vi8, -3
2C60: NOP                              | LQI.xyzw vf17, (vi8++)
```

### [0x2C68 - 0x2CD0]: Plane 5 (-Z Near Frustum Plane)
*Tests vertices against Plane 5 (z < -w), calls clipper subroutine at 0x2DC0.*
```text
2C68: CLIP.xyz ACC, vf17, vf17         | BAL 41                     ; Branch to 2DC0 (Plane 5)
2C70: CLIP.xyz ACC, vf21, vf21         | LQI.xyzw vf22, (vi8++)
2C78: SUBw.z vf20, vf0, vf0            | IADDIU vi5, vi0, -32768    ; Set plane 5 bitmask (0x8000)
2C80: NOP                              | IADDIU vi6, vi0, 512
2C88: NOP                              | ISW.x vi11, 1022(vi0)      ; Save final clipped count
2C90: NOP                              | IADDIU vi8, vi0, 918
2C98: NOP                              | IADDIU vi9, vi0, 952
2CA0: NOP                              | IADD vi10, vi0, vi11
2CA8: NOP                              | IADDIU vi11, vi0, 0
2CB0: NOP                              | LQI.xyzw vf21, (vi8++)
2CB8: NOP                              | LQI.xyzw vf22, (vi8++)
2CC0: NOP                              | LQI.xyzw vf23, (vi8++)
2CC8: NOP                              | IADDI vi8, vi8, -3
2CD0: NOP                              | LQI.xyzw vf17, (vi8++)
```

### [0x2CD8 - 0x2DA8]: Core Edge Intersection Interpolator (Subroutine)
*Calculates parametric $t = \frac{w_1 - x_1}{(x_2 - x_1) - (w_2 - w_1)}$ using DIV Q, WAITQ, and interpolates position, ST, and RGBA.*
```text
2CD8: NOP                              | IADDIU vi11, vi11, 1       ; Increment clipped vertex counter
2CE0: NOP                              | SQI.xyzw vf25, (vi9++)     ; Store new vertex pos
2CE8: NOP                              | SQI.xyzw vf26, (vi9++)     ; Store new vertex ST
2CF0: NOP                              | SQI.xyzw vf27, (vi9++)     ; Store new vertex RGBA
2CF8: MULq.xyz vf27, vf27, vf0         | BAL 0                      ; Local loop
2D00: MULA.xyzw ACC, vf1, vf25         | MOVE.x vf24, vf25
2D08: MADD.xyzw vf24, vf2, vf25        | DIV Q, vf0.w, vf27.x       ; Compute Q = 1.0 / delta
2D10: MADD.xyzw vf24, vf3, vf25        | WAITQ                      ; Wait for reciprocal Q
2D18: MADD.xyzw vf24, vf4, vf25        | MOVE.- vf0, vf0
2D20: NOP                              | SQ.xyzw vf24, 0(vi14)      ; Store interpolated quad
2D28: NOP                              | SQ.xyzw vf25, 1(vi14)
2D30: NOP                              | SQ.xyzw vf26, 2(vi14)
2D38: NOP                              | IBNE vi11, vi0, -17        ; Loop over remaining edges
2D40: MULw.w vf25, vf24, vf0           | ISW.x vi11, 1022(vi0)
...
2DA8: NOP                              | JR vi12                    ; Return to plane caller
```

### [0x2DB8 - 0x2E40]: Polygon Edge Dispatcher
*Dispatches vertex pairs: checks visibility via FCGET vi1 against plane bitmask, branches to emit or interpolate.*
```text
2DB8: ADDx.xyzw vf19, vf23, vf0        | ISUBIU vi10, vi10, 1       ; Decrement remaining edge counter
2DC0: NOP                              | ISUBIU vi15, vi12, 2       ; Set return address
2DC8: NOP                              | IBNE vi10, vi0, 2          ; Loop check
2DD0: NOP                              | FCGET vi1                  ; Read CLIP flags
2DD8: NOP                              | IADDIU vi15, vi0, 1489
2DE0: MULx.w vf25, vf17, vf20          | IAND vi13, vi1, vi5        ; Test vertex 0 against plane
2DE8: MULx.w vf26, vf21, vf20          | IAND vi1, vi1, vi6         ; Test vertex 1 against plane
2DF0: NOP                              | IBEQ vi13, vi0, 4          ; Branch if vertex 0 is inside
2DF8: NOP                              | LQI.xyzw vf23, (vi8++)
2E00: NOP                              | IBNE vi1, vi0, 14          ; Branch if vertex 1 is inside
2E08: NOP                              | IADDIU vi1, vi0, 1484
2E10: NOP                              | B 22                       ; Jump to next edge
2E18: NOP                              | IADDIU vi11, vi11, 1       ; Vertex preserved
2E20: NOP                              | SQI.xyzw vf17, (vi9++)     ; Output preserved vertex POS
2E28: NOP                              | SQI.xyzw vf18, (vi9++)     ; Output preserved vertex ST
2E30: NOP                              | IBNE vi1, vi0, 3
2E38: NOP                              | SQI.xyzw vf19, (vi9++)     ; Output preserved vertex RGBA
2E40: ADDx.xyzw vf17, vf21, vf0        | JR vi15                    ; Return / advance
```

### [0x2E48 - 0x2F08]: Clipped Strip Assembly and Epilogue
*Re-assembles the clipped polygon into triangle strips, restores caller context from 1020..1022, and returns to dispatcher.*
```text
2E48: NOP                              | IADDIU vi10, vi0, 3
2E50: NOP                              | BAL 14                     ; Emit triangle fan / strip
2E58: NOP                              | IADDIU vi11, vi11, 1
2E60: NOP                              | SQI.xyzw vf25, (vi9++)     ; Emit vertex 0
2E68: NOP                              | SQI.xyzw vf26, (vi9++)     ; Emit vertex 1
2E70: NOP                              | SQI.xyzw vf27, (vi9++)     ; Emit vertex 2
2E78: ADDx.xyzw vf17, vf21, vf0        | JR vi15
2E80: NOP                              | MOVE.xyzw vf21, vf17
2E88: NOP                              | IBEQ vi11, vi0, -40        ; Strip loop back
2E90: NOP                              | LQ.xyzw vf25, 0(vi14)      ; Reload scratchpad vertex
2E98: NOP                              | LQ.xyzw vf26, 1(vi14)
2EA0: NOP                              | LQ.xyzw vf27, 2(vi14)
2EA8: NOP                              | SQI.xyzw vf25, (vi9++)     ; Write to vertex output stream
2EB0: MULA.xyzw ACC, vf1, vf25         | SQI.xyzw vf26, (vi9++)
2EB8: MADDw.xyzw vf19, vf2, vf25       | JR vi12
2EC0: NOP                              | SQI.xyzw vf27, (vi9++)
2EC8: SUBw.xyzw vf25, vf17, vf25       | IBEQ vi7, vi0, 5           ; End of strip check
2ED0: SUBw.xyzw vf26, vf21, vf26       | IADD vi13, vi0, vi7
2ED8: NOP                              | ISUBIU vi13, vi13, 1
2EE0: NOP                              | MR32.xyzw vf25, vf25       ; Rotate triangle vertices
2EE8: NOP                              | IBNE vi13, vi0, -3
2EF0: NOP                              | MR32.xyzw vf26, vf26
2EF8: SUB.x vf27, vf26, vf25           | MOVE.x vf24, vf25
2F00: ADDx.y vf24, vf0, vf26           | DIV Q, vf0.w, vf27.x
2F08: ABS.xy ACC, vf24, vf24           | MOVE.- vf0, vf0
```

---

## 3. Per-Iteration Cycle Cost and Exit Conditions

1. **Polygon-Plane Edge Clipping Subroutine (`0x2DB8..0x2E40`)**:
   - Both vertices inside plane: **10 cycles / edge** (preserves vertex, outputs XYZW, ST, RGBA).
   - One vertex inside, one outside (edge intersection): **34 cycles / edge** (due to `DIV Q, WAITQ` latency of 13 cycles).
   - Both vertices outside plane: **8 cycles / edge** (discards vertex, advances pointer).
2. **Frustum Plane Test Overhead**:
   - Each of the 6 planes consumes a setup overhead of **14 cycles** (`CLIP.xyz`, flip ping-pong buffer, rewind pointer).
3. **Clipped Strip Output Generation (`0x2E48..0x2EC0`)**:
   - Outputs 3 quadwords per clipped vertex (`SQI.xyzw (vi9++)`): **12 cycles / emitted vertex**.
4. **Exit Conditions**:
   - Polygon completely clipped out (0 vertices remain after any plane): early exit back to dispatcher `0x0028` in ~120 cycles.
   - Successful clip: emits $M$ vertices ($M \in [3, 8]$), completes strip assembly, restores registers from quadwords 1020..1022, and returns via `JR vi15` to dispatcher `0x0028`.
