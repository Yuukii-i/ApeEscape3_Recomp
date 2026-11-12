# VU1 Command-Stream Handlers and Dispatcher Closed Forms Specification

## 1. Overview and Architecture

The VU1 microprogram in Ape Escape 3 uses a stream-driven command dispatch loop located at `0x0008..0x0048`.
- The initialization code at `0x0008..0x0020` sets the return register $vi_{15} = 5$ (so that returning via `JR vi15` executes jump target $(5 \times 8) = 0\text{x}0028$), reads the VIF double-buffer top pointer $vi_{12} = \text{XTOP}$, initializes stream pointer $vi_{13} = vi_{12}$, and fetches the first command word into $vi_1$.
- The dispatcher loop at `0x0028..0x0038` advances the stream pointer $vi_{13}$, reads the quadword count/argument into $vi_2$, and branches to the command handler via `JR vi1`.
- Individual command handlers process geometry, lighting, matrix manipulation, or data copying, and conclude with `JR vi15` (delay slot `ILW.x vi1, 0(vi13)`), returning directly to `0x0028` with the next handler command already loaded in $vi_1$.

---

## 2. Microcode Disassembly

### Dispatcher Loop (0x0008..0x0048)
```text
0008: IADDIU vi15, vi0, 5        ; vi15 = 5 -> return address 0x0028
0010: XTOP vi12                  ; vi12 = VIF TOP (double-buffer base)
0018: ILW.x vi1, 0(vi12)         ; vi1 = initial command word
0020: IADDI vi13, vi12, 0        ; vi13 = vi12 (stream pointer)
0028: IADDIU vi13, vi13, 1       ; stream pointer advance
0030: JR vi1                     ; dispatch to handler at (vi1 * 8)
0038: ILW.y vi2, -1(vi13)        ; delay slot: load argument into vi2
0040: B -7                       ; loop back
0048: IADDIU vi15, vi0, 0
```

### Handler 0x0050 (Final Kick)
```text
0050: IADDIU vi1, vi0, 1023      ; vi1 = 1023 (0x3FF)
0058: XGKICK vi1                 ; Kick quadword 1023 to GIF
0060: JR vi15                    ; Return to dispatcher at 0x0028
0068: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

### Handler 0x0060 (Return)
```text
0060: JR vi15                    ; Return to dispatcher at 0x0028
0068: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

### Handler 0x0070 (Pointer Adjust & Jump to 0188)
```text
0070: ISUB vi2, vi2, vi12        ; vi2 = vi2 - vi12
0078: B 33                       ; Branch to 0x0188
0080: IADD vi13, vi2, vi12       ; Delay slot: vi13 = (vi2 - vi12) + vi12 = old vi2
0188: JR vi15                    ; Return to dispatcher at 0x0028
0190: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

### Handler 0x0088 (XGKICK and Pointer Advance)
```text
0088: XGKICK vi13                ; Kick quadword vi13 to GIF
0090: IADD vi13, vi13, vi2       ; vi13 = vi13 + vi2
0098: JR vi15                    ; Return to dispatcher at 0x0028
00A0: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

### Handler 0x0098 (Return)
```text
0098: JR vi15                    ; Return to dispatcher at 0x0028
00A0: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

### Handler 0x0188 (Return)
```text
0188: JR vi15                    ; Return to dispatcher at 0x0028
0190: ILW.x vi1, 0(vi13)         ; Delay slot: load next command into vi1
```

---

## 3. Mathematical Closed-Form Formulas

For each handler entered at cycle $C_0$ with state $st$:

| Entry PC | Next $vi_1$ | Register Mutations | Target Exit PC | Total Cycles | Side Effects |
|---|---|---|---|---|---|
| `0x0050` | $\text{s16}(mem[vi_{13}].x)$ | $vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 4 | `XGKICK 1023` (flush final packet) |
| `0x0060` | $\text{s16}(mem[vi_{13}].x)$ | $vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 2 | None |
| `0x0070` | $\text{s16}(mem[\text{old\_vi2}].x)$ | $vi_2 = \text{s16}(vi_2 - vi_{12})$<br>$vi_{13} = \text{s16}(\text{old\_vi2})$<br>$vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 8 | None |
| `0x0088` | $\text{s16}(mem[vi_{13} + vi_2].x)$ | $vi_{13} = \text{s16}(vi_{13} + vi_2)$<br>$vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 6 | `XGKICK vi13` (geometry kick to GIF) |
| `0x0098` | $\text{s16}(mem[vi_{13}].x)$ | $vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 2 | None |
| `0x0188` | $\text{s16}(mem[vi_{13}].x)$ | $vi_1 = \text{next\_vi1}$ | $0\text{x}0028$ (40) | 2 | None |
| `0x0028` | $vi_{1, \text{entry}}$ | $vi_{13} = \text{s16}(vi_{13} + 1)$<br>$vi_2 = \text{s16}(mem[vi_{13}].y)$ | $(vi_1 \times 8) \ \& \ 0\text{x}3\text{FFF}$ | 2 | Dispatches to next handler |

All other state variables ($vf_{0..31}$, $acc$, $q$, $status$, $mac$, $clip$, memory) are preserved without modification across these handlers.
