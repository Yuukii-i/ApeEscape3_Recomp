# VU1 Clipper Setup & Plane Passes Closed-Form Specification (2900..2CD0)

## 1. Overview and Architecture
The VU1 clipping subsystem in Ape Escape 3 implements the Sutherland-Hodgman polygon clipping algorithm against the six view frustum planes.

Code in `0x2900..0x2CD0` spans:
- **Clipper Initialization & Context Spill** (`0x2900..0x29D0`):
  Saves calling vertex pipeline integer state to VU memory quadwords `1020..1022`, spills transformation matrices and initial vertices to scratch quadwords `918..926`.
- **Plane Buffer Allocation & Constant Setup** (`0x29D8..0x2A48`):
  Initializes scratch buffer pointers for double-buffered polygon ping-pong (`vi8 = 952`, `vi9 = 918`), loads vertex count into `vi10`, sets plane constant matrices into memory (`919`, `922`, `928`).
- **The Six Frustum Plane Passes**:
  - Plane 0 (`0x2A50`, `0x2A60`): Right plane $+X$ (bitmask `1024` / `0x0400`)
  - Plane 1 (`0x2AB8`, `0x2AC8`): Left plane $-X$ (bitmask `2048` / `0x0800`)
  - Plane 2 (`0x2B28`, `0x2B38`): Top plane $+Y$ (bitmask `4096` / `0x1000`)
  - Plane 3 (`0x2B90`, `0x2BA0`): Bottom plane $-Y$ (bitmask `8192` / `0x2000`)
  - Plane 4 (`0x2C00`, `0x2C10`): Far plane $+Z$ (bitmask `16384` / `0x4000`)
  - Plane 5 (`0x2C68`, `0x2C78`): Near plane $-Z$ (bitmask `-32768` / `0x8000`)
- **Epilogue & Strip Assembly** (`0x2CB8`):
  Assembles the clipped polygon vertices into triangle strips / fans, emits them to the output stream, restores calling context from `1020..1022`, and returns via `JR vi15` to the dispatcher at `0x0028`.

---

## 2. Closed-Form Specifications by Entry PC

### Entry 0x2908: Context Save & Spill Entry
- **Semantics**:
  Stores `vi6..vi13, vi15` into quadwords `1020..1022`.
  Spills matrix rows `vf28, vf29, vf10` to `918, 921, 924`.
  Spills vertex 0 (`vf17..19`) and vertex 1 (`vf21..23`) to `919..926`.
  Sets `vi10 = 2`, stores to `1022.w`.
  Proceeds into `0x29D8` and the full 6-plane clipping sequence.
- **Exit State**:
  - `pc`: `0x0028` (40)
  - `vi[1]`: next command word loaded from `mem[vi13]`
  - `vi[2]`: updated vertex count / stride
  - `cycles`: baseline setup ($22 + 17 = 39$ cycles) + plane clipping iterations + epilogue.

### Entry 0x29D8: Buffer & Constants Setup Entry
- **Semantics**:
  Stores constant quadwords into `mem[919], mem[922], mem[928]`.
  Sets initial ping-pong pointers: `vi8 = 952`, `vi9 = 918`.
  Loads polygon vertex count `vi10 = mem[1022].w`.
  Loads first vertex quadwords into `vf21, vf22, vf23, vf17`.
  Falls directly into Plane 0 setup at `0x2A50`.
- **Exit State**:
  - `pc`: `0x0028` (40)
  - `cycles`: setup (17 cycles) + plane clipping iterations + epilogue.

### Entries 0x2A50 / 0x2A60: Plane 0 (+X Right Frustum Plane)
- **Semantics**:
  Tests vertices against $x \le +w$ plane limit via `CLIP.xyz ACC, vf17, vf17` and `CLIP.xyz ACC, vf21, vf21`.
  `BAL 108` invokes the edge-plane interpolation subroutine at `0x2DC0`.
  `0x2A60` continues post-pass: sets plane bitmask `1024` (`0x0400`), flips ping-pong buffers (`vi8, vi9 = 952, 918`), updates `vi10` to the new vertex count, and branches to Plane 1.
- **Exit Condition**: If `vi10 == 0` (polygon clipped out), exits early to epilogue.

### Entries 0x2AB8 / 0x2AC8: Plane 1 (-X Left Frustum Plane)
- **Semantics**:
  Tests vertices against $x \ge -w$ plane limit.
  `BAL 95` invokes edge interpolation subroutine.
  `0x2AC8` sets bitmask `2048` (`0x0800`), flips buffers (`vi8, vi9 = 918, 952`), updates vertex count, branches to Plane 2.

### Entries 0x2B28 / 0x2B38: Plane 2 (+Y Top Frustum Plane)
- **Semantics**:
  Tests vertices against $y \le +w$ plane limit.
  `BAL 81` invokes edge interpolation subroutine.
  `0x2B38` sets bitmask `4096` (`0x1000`), flips buffers (`vi8, vi9 = 952, 918`), updates vertex count, branches to Plane 3.

### Entries 0x2B90 / 0x2BA0: Plane 3 (-Y Bottom Frustum Plane)
- **Semantics**:
  Tests vertices against $y \ge -w$ plane limit.
  `BAL 68` invokes edge interpolation subroutine.
  `0x2BA0` sets bitmask `8192` (`0x2000`), flips buffers (`vi8, vi9 = 918, 952`), updates vertex count, branches to Plane 4.

### Entries 0x2C00 / 0x2C10: Plane 4 (+Z Far Frustum Plane)
- **Semantics**:
  Tests vertices against $z \le +w$ plane limit.
  `BAL 54` invokes edge interpolation subroutine.
  `0x2C10` sets bitmask `16384` (`0x4000`), flips buffers (`vi8, vi9 = 952, 918`), updates vertex count, branches to Plane 5.

### Entries 0x2C68 / 0x2C78: Plane 5 (-Z Near Frustum Plane)
- **Semantics**:
  Tests vertices against $z \ge -w$ plane limit.
  `BAL 41` invokes edge interpolation subroutine.
  `0x2C78` sets bitmask `-32768` (`0x8000`), stores final clipped vertex count into `mem[1022].x`, and branches to epilogue `0x2CB8`.

### Entry 0x2CB8: Epilogue & Strip Emit
- **Semantics**:
  Reads final vertex count $M$ from `mem[1022].x`.
  If $M \ge 3$: loads clipped vertices from scratch buffer and emits triangle strip quads to `vi9++` (`SQI.xyzw vf25..27`).
  Restores integer registers `vi5..vi13, vi15` from `1020..1022`.
  Executes `JR vi15` with delay slot `ILW.x vi1, 0(vi13)`, returning to dispatcher at `0x0028`.
- **Exit State**:
  - `pc`: `0x0028` (40)
  - `cycles`: $18 + 12 \times M$ cycles.

---

## 3. Mathematical Formula for Edge Interpolation
For each edge between vertex $V_1 = (P_1, ST_1, C_1)$ and $V_2 = (P_2, ST_2, C_2)$ crossing plane $k$:
1. **Parametric Weight**:
   $$\Delta = (P_{2, \text{coord}} - P_{1, \text{coord}}) \pm (P_{2, w} - P_{1, w})$$
   $$Q = \text{divq}(1.0, \Delta)$$
   $$t = (P_{1, w} \mp P_{1, \text{coord}}) \times Q$$
2. **Interpolated Attributes**:
   $$P_{\text{new}} = P_1 + t \times (P_2 - P_1)$$
   $$ST_{\text{new}} = ST_1 + t \times (ST_2 - ST_1)$$
   $$C_{\text{new}} = C_1 + t \times (C_2 - C_1)$$
3. **Hardware Latency**:
   - `DIV Q` reciprocal latency is 13 cycles.
   - Total interpolation cost is 34 cycles per edge.
