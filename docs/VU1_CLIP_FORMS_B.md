# VU1 Clipper Edge Interpolator & Strip Assembly Closed-Form Specification (2CD8..2F08)

## 1. Overview and Scope
Task GK covers the inner execution core of the Sutherland-Hodgman clipper:
1. **Edge Interpolator (`0x2CD8..0x2DA8`)**:
   Calculates edge intersections against the active clipping plane using `DIV Q, vf0.w, vf27.x` followed by `WAITQ`, performs linear attribute interpolation (`MADD`, `MULA`, `MULq`), and writes newly generated vertices into scratch memory.
2. **Edge Dispatcher (`0x2DB8..0x2E40`)**:
   Loops through the $N$ polygon edges, queries plane clipping flags via `FCGET vi1`, tests visibility against plane bitmasks (`vi5` for vertex 0, `vi6` for vertex 1), and directs control to emit, interpolate, or discard.
3. **Strip Assembly & Epilogue (`0x2E48..0x2F08`)**:
   Transforms the clipped polygon into triangle strips / fans, emits 3 quadwords per vertex (`SQI.xyzw (vi9++)`), restores calling pipeline registers from quadwords `1020..1022`, and returns via `JR vi15` to the dispatcher at `0x0028`.

---

## 2. Hardware Divide & Flag Mechanics (`DIV Q`, `WAITQ`)

### Divide Pipeline Timing
At `0x2D08`, reciprocal division is issued:
```text
2D08: MADD.xyzw vf24, vf2, vf25        | DIV Q, vf0.w, vf27.x
```
- Operands: Numerator = `vf0.w` ($1.0$), Denominator = `vf27.x` ($\Delta = (P_{2, \text{coord}} - P_{1, \text{coord}}) \pm (P_{2, w} - P_{1, w})$).
- Latency: Exactly 13 cycles.
- At `0x2D10`, `WAITQ` halts upper and lower pipelines until the quotient is ready:
  $$Q = \text{divq}(1.0, \Delta)$$
- Div-by-zero flag: If denominator is zero, STATUS bit `0x010` (D flag) is asserted.
- Upon landing at cycle $C_{\text{div}} + 13$, STATUS bit `0x020` (I flag) is updated if the quotient is inexact/valid.
- Because `WAITQ` is issued immediately prior to reading Q (`MULq.xyz` at `0x2CF8` / `0x2D18`), no divide is in-flight at block exit ($fdiv = (0, -\text{readyCycle}, 0, 0)$).

---

## 3. Closed-Form Specifications by Entry PC

### 1. `0x2D48` & `0x2D50`: Interpolator Loop Continuation
- **Semantics**:
  Continues the Sutherland-Hodgman intersection loop for remaining polygon edges.
  Decrements loop induction counter `vi11`.
  If `vi11 != 0`: loops back to `0x2CF8` (`BAL 0`) to compute next intersection.
  If `vi11 == 0`: branches to `0x2DA8` (`JR vi12`) to return to plane caller.
- **Cycles**: $13 + 34 \times vi_{11}$ cycles.
- **Exit State**: `pc = 0x0028` (via plane return and epilogue).

### 2. `0x2DA8`: Subroutine Return
- **Semantics**:
  Executes `JR vi12` with delay slot, returning control to the caller block of the active plane (`0x2A60`, `0x2AC8`, `0x2B38`, `0x2BA0`, `0x2C10`, or `0x2C78`).
- **Cycles**: 2 cycles + remaining plane passes.

### 3. `0x2DB8`, `0x2DD8`, `0x2DE0`: Edge Dispatcher
- **Semantics**:
  Loads next vertex attributes from input buffer `(vi8++)`.
  Decrements remaining edges `vi10 = vi10 - 1`.
  `FCGET vi1` fetches clipping flags.
  Tests vertex 0: `(vi1 & vi5) == 0` (inside).
  Tests vertex 1: `(vi1 & vi6) == 0` (inside).
  Branches to:
  - Inside-Inside: `0x2E18` (outputs preserved vertex to `vi9++`).
  - Outside-Inside / Inside-Outside: `0x2D00` (interpolates edge).
  - Outside-Outside: skips vertex, advances `vi8`.
- **Cycles**: $10$ cycles (inside) / $34$ cycles (intersect) / $8$ cycles (outside) per edge.

### 4. `0x2E00`, `0x2E10`, `0x2E18`, `0x2E40`: Preserved Vertex Emission
- **Semantics**:
  Emits preserved vertex attributes directly to output ping-pong buffer:
  - `SQI.xyzw vf17, (vi9++)` (Position XYZW)
  - `SQI.xyzw vf18, (vi9++)` (Texture coordinates ST)
  - `SQI.xyzw vf19, (vi9++)` (Color RGBA)
  Increments output vertex count `vi11 = vi11 + 1`.
  Branches to next edge in loop.
- **Cycles**: 5 cycles.

### 5. `0x2E50`, `0x2E60`, `0x2E78`: Strip Fan Assembly
- **Semantics**:
  Emits triangle fan / strip header vertices.
  Writes 3 quadwords to output stream via `SQI.xyzw (vi9++)`.
  Proceeds to strip epilogue `0x2EA8`.
- **Cycles**: $7$ cycles / emitted vertex.

### 6. `0x2E88`, `0x2E98`, `0x2EC8`, `0x2ED8`, `0x2EF8`: Strip Assembly & Vertex Rotation
- **Semantics**:
  Loads clipped vertices from scratchpad (`LQ.xyzw vf25..27, 0..2(vi14)`).
  Rotates triangle vertices using `MR32.xyzw vf25, vf25` to maintain correct triangle winding order.
  Emits final vertex stream (`SQI.xyzw vf25..27, (vi9++)`).
  Restores integer registers `vi5..vi13, vi15` from quadwords `1020..1022`.
  Executes `JR vi15` (delay slot `ILW.x vi1, 0(vi13)`), returning to dispatcher at `0x0028`.
- **Cycles**: $18 + 12 \times M$ cycles, where $M$ is the number of emitted vertices.

---

## 4. Mathematical Model for Vertex Stores
For every emitted vertex $k \in \{0, \dots, M-1\}$ at address $A_k = vi_{9, \text{init}} + 3k$:

1. **Position (XYZW)** at $A_k + 0$:
   $$X = \text{ftoi}(vf_{25}.x, 16)$$
   $$Y = \text{ftoi}(vf_{25}.y, 16)$$
   $$Z = \text{ftoi}(vf_{25}.z, 16)$$
   $$W = \text{ftoi}(vf_{25}.w, 16)$$
2. **Texture (ST)** at $A_k + 1$:
   $$S = \text{fmac}(\text{MUL}, vf_{26}.x, Q, 0)$$
   $$T = \text{fmac}(\text{MUL}, vf_{26}.y, Q, 0)$$
3. **Color (RGBA)** at $A_k + 2$:
   $$C_c = \text{ftoi}(\text{maxmini}(\text{True}, \text{maxmini}(\text{False}, vf_{27}[c], 255.0), 0.0), 1) \quad \forall c \in \{0, 1, 2, 3\}$$
