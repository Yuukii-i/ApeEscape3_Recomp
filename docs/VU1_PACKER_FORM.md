# VU1 Packer Loop Closed Form Specification (0B40 / 0BC8)

## 1. Overview and Context
- **Handler 0BC8**: High-frequency packer inner loop (12 cycles/iteration, hot block hash `fb8ef27e9dfd2579`, ~95,000 it/s). It packs quaternions/vectors and performs cross products, dot products, vector transformations, and integer bit packing into vertex output streams.
- **Handler 0B40**: Prologue to the packer loop (block hash `cd057af54d65447f`, 29 instruction pairs: 17 prologue pairs + 12 loop iteration pairs). It initializes constants (`vf1`, `vf4`, `vf11`), sets up pointer addresses and bounds (`vi1`, `vi2`, `vi3`, `vi4`, `vi5`, `vi6`), performs initial vector loads (`vf2`, `vf12`, `vf3`), pushes an initial zero MAC flag at 0BB0, and falls through into the 0BC8 loop.
- **Exit Stub 0C28 / 0C30**: Epilogue returning control to the dispatcher:
  ```text
  0C28: JR vi15
  0C30: ILW.x vi1, 0(vi13)  (delay slot)
  ```

---

## 2. Derivation of 0BC8 Loop State Transitions

Let $n = (vi_2 - vi_1) \ \& \ \text{0xFFFF}$ be the iteration count.
For iteration $k \in \{0, \dots, n-1\}$, let $S_k = \text{cycle}_0 + 12k$.

### Instruction Pair Breakdown & Cycle Timing

1. **Cycle $S_k + 0$ (0BC8)**:
   - Upper: `ADDw.xyzw vf5, vf0, vf3` $\implies vf_5 = \text{copy}(vf_3)$
   - Lower: `IADDIU vi1, vi1, 1` $\implies vi_1 = (vi_1 + 1) \ \& \ \text{0xFFFF}$

2. **Cycle $S_k + 1$ (0BD0)**:
   - Upper: `ADDw.xyzw vf3, vf0, vf2` $\implies vf_3 = \text{copy}(vf_2)$
   - Lower: `FMAND vi9, vi3`: Reads MAC flags visible at cycle $S_k + 1$ (newest push with $\text{push\_cycle} + 4 \le S_k + 1$).
     $$\text{vis} = \text{MAC visible at } S_k + 1$$
     $$vi_9 = (\text{vis} \ \& \ \text{0xFFFF}) \ \& \ (vi_3 \ \& \ \text{0xFFFF})$$
     - When $k = 0$: reads from entry MAC ring buffer (or prologue push from 0BB0).
     - When $k > 0$: reads the push from $S_{k-1} + 9$ (`MULy.x vf0, vf4, vf1`), because $(S_{k-1} + 9) + 4 = S_k + 1 \le S_k + 1$.

3. **Cycle $S_k + 2$ (0BD8)**:
   - Upper: `NOP`
   - Lower: `LQ vf2, 636(vi7)`: Loads quadword at VU address $(636 + vi_7) \pmod{1024}$.

4. **Cycle $S_k + 3$ (0BE0)**:
   - Upper: `ADDAy.x ACC, vf4, vf4`:
     $$acc[0] = fmac(\text{ADD}, vf_4[0], vf_4[1], 0)$$
     Pushes MAC to ring buffer at $S_k + 3$. Updates `status` sticky bits.
   - Lower: `IADDIU vi9, vi9, 32767` $\implies vi_9 = (vi_9 + 32767) \ \& \ \text{0xFFFF}$

5. **Cycle $S_k + 4$ (0BE8)**:
   - Upper: `MADDz.x vf4, vf11, vf4`:
     $$vf_4[0] = fmac(\text{MADD}, vf_{11}[0], vf_4[2], acc[0])$$
     Pushes MAC to ring buffer at $S_k + 4$. Updates `status` sticky bits.
   - Lower: `IADD vi8, vi8, vi9` $\implies vi_8 = (vi_8 + vi_9) \ \& \ \text{0xFFFF}$

6. **Cycle $S_k + 5$ (0BF0)**:
   - Upper: `OPMULA.xyz ACC, vf5, vf3`:
     $$acc[0] = fmac(\text{MUL}, vf_5[1], vf_3[2], 0)$$
     $$acc[1] = fmac(\text{MUL}, vf_5[2], vf_3[0], 0)$$
     $$acc[2] = fmac(\text{MUL}, vf_5[0], vf_3[1], 0)$$
     Pushes MAC to ring buffer at $S_k + 5$. Updates `status` sticky bits.
   - Lower: `IAND vi8, vi8, vi4` $\implies vi_8 = (vi_8 \ \& \ vi_4) \ \& \ \text{0xFFFF}$

7. **Cycle $S_k + 6$ (0BF8)**:
   - Upper: `OPMSUB.xyz vf5, vf3, vf5`:
     $$vf_5'[0] = fmac(\text{MSUB}, vf_3[1], vf_5[2], acc[0])$$
     $$vf_5'[1] = fmac(\text{MSUB}, vf_3[2], vf_5[0], acc[1])$$
     $$vf_5'[2] = fmac(\text{MSUB}, vf_3[0], vf_5[1], acc[2])$$
     *(Calculated simultaneously to prevent in-place overwrite).*
     Pushes MAC to ring buffer at $S_k + 6$. Updates `status` sticky bits.
   - Lower: `IOR vi6, vi6, vi8` $\implies vi_6 = (vi_6 \ | \ vi_8) \ \& \ \text{0xFFFF}$

8. **Cycle $S_k + 7$ (0C00)**:
   - Upper: `ADDw.z vf2, vf0, vf2`:
     $$vf_2[2] = fmac(\text{ADD}, 0, vf_2[3], 0) = vf_2[3]$$
     Pushes MAC to ring buffer at $S_k + 7$. Updates `status` sticky bits.
   - Lower: `ISW.x vi6, -3(vi1)`: Writes 32-bit integer $(vi_6 \ \& \ \text{0xFFFF})$ into lane X of quadword $(vi_1 - 3) \pmod{1024}$.

9. **Cycle $S_k + 8$ (0C08)**:
   - Upper: `NOP`
   - Lower: `ILW.x vi6, -2(vi1)`: Loads signed 16-bit integer from lane X of quadword $(vi_1 - 2)$.

10. **Cycle $S_k + 9$ (0C10)**:
    - Upper: `MULy.x vf0, vf4, vf1`:
      $$r = fmac(\text{MUL}, vf_4[0], vf_1[1], 0)$$
      Result written to `vf0` (discarded). Pushes MAC to ring buffer at $S_k + 9$. Updates `status` sticky bits.
    - Lower: `ILW.x vi7, 0(vi1)`: Loads signed 16-bit integer from lane X of quadword $vi_1$.

11. **Cycle $S_k + 10$ (0C18)**:
    - Upper: `NOP`
    - Lower: `IBNE vi1, vi2, -11`: Branches back to 0BC8 if $vi_1 \ne vi_2$.

12. **Cycle $S_k + 11$ (0C20)** (Branch Delay Slot):
    - Upper: `MUL.xyzw vf4, vf5, vf2`:
      $$vf_4[c] = fmac(\text{MUL}, vf_5[c], vf_2[c], 0) \quad \forall c \in \{0, 1, 2, 3\}$$
      Pushes MAC to ring buffer at $S_k + 11$. Updates `status` sticky bits.
    - Lower: `ILW.y vi8, -2(vi1)`: Loads signed 16-bit integer from lane Y of quadword $(vi_1 - 2)$.

---

## 3. Exit State & Epilogue

When the loop terminates ($vi_1 = vi_2$ after $n$ iterations):
- Execution jumps to epilogue `0C28` (`JR vi15`), with delay slot `0C30` (`ILW.x vi1, 0(vi13)`).
- **Registers**:
  - $vi_1 = \text{sign\_extend}_{16}(mem[vi_{13}].x)$
  - $vi_2 = vi_{2, \text{init}}$
  - $vi_3, vi_4, vi_6, vi_7, vi_8, vi_9$ hold their final loop values (sign-extended 16-bit).
  - $vf_2, vf_3, vf_4, vf_5$ hold their exact values from the final loop iteration.
  - $acc$ holds the final accumulator state from $S_{n-1} + 5$.
  - $pc = 0\text{x}0028$.
  - $\text{cycle} = \text{cycle}_0 + 2 + 12n$.
- **Flags and State Visibility**:
  - In VU1 hardware / interpreter architecture, `VU1State::mac` is updated when a reader instruction (`FMAND`, `FMOR`, `FMEQ`) executes.
  - No reader instruction executes after the final iteration's `FMAND` at $S_{n-1} + 1$.
  - Thus, exit $st.mac$ exactly equals the MAC value read during the last iteration's `FMAND`!
  - $st.clip$ is untouched throughout the loop ($st.clip = st.clip_0$).

---

## 4. Prologue 0B40 Derivation

Block 0B40 executes 17 pairs (0B40..0BC0) taking 21 cycles before entering 0BC8 at cycle $\text{cycle}_0 + 21$:
1. $vi_1 = \text{s16}(mem[1018].z + vi_{12})$
2. $vi_2 = \text{s16}(vi_1 + mem[1018].w + 2)$
3. $vi_3 = 128$
4. $vi_4 = -32768$ (`0x8000`)
5. $vi_6 = \text{s16}(mem[vi_1].x)$
6. $vi_5 = \text{s16}(mem[vi_1 + 1].x)$
7. $vf_1 = [0.0, mem[vi_{13} - 1].y, 0.0, 1.0]$
8. $vf_4 = [0.0, 0.0, 0.0, 1.0]$
9. $vf_{11} = [1.0, 1.0, 1.0, 1.0]$
10. $vf_{12} = mem[636 + vi_6]$, with $vf_{12}.z = vf_{12}.w$
11. $vf_2 = mem[636 + vi_5]$, with $vf_2.z = vf_2.w$
12. $vf_3 = \text{copy}(vf_{12})$
13. `MUL.x vf0, vf0, vf0` pushes zero MAC to ring buffer at cycle $\text{cycle}_0 + 18$.
14. $vi_7 = \text{s16}(mem[vi_1].x)$, $vi_8 = \text{s16}(mem[vi_1 - 2].y)$
15. Falls through into 0BC8 loop with $n = mem[1018].w$, starting at cycle $\text{cycle}_0 + 21$.
16. Total execution cycles: $21 + 2 + 12n = 23 + 12n$.
