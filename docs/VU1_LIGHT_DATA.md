# VU1 Light, Material, and Skinning Data Layout

Analysis of VU1 data-memory (1024 quadwords = 16 KiB, byte offset = `qword * 16`) inputs/outputs for the matrix, light, skinning, and rigid geometry handlers in [vu1_func.inc](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/vu/vu1_func.inc), cross-referenced with [VU1_HANDLER_FORMS.md](file:///c:/ApeEscape3_Recomp/docs/VU1_HANDLER_FORMS.md), [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md), and [VU1_MAP.md](file:///c:/ApeEscape3_Recomp/docs/VU1_MAP.md).

Every statement is tagged `[CODE file:line]` or `[INFERRED]`.

---

## Global Per-Frame & Per-Batch Data

| Qword (dec) | Byte Offset | Lanes | Meaning | Source |
|---|---|---|---|---|
| `978..981` | `0x3D20..0x3D50` (`15648..15696`) | `.xyzw` | Object / local-to-world 4x4 matrix rows (`978`=R0, `979`=R1, `980`=R2, `981`=R3) | `[CODE vu1_func.inc:1160,1170-1171]` |
| `982..985` | `0x3D60..0x3D90` (`15712..15760`) | `.xyz` | 4x3 affine matrix transforming world light position to local/model space (`985` = translation) | `[CODE vu1_func.inc:3237,3451,3490]` |
| `986..988` | `0x3DA0..0x3DC0` (`15776..15808`) | `.xyz` | 3x3 model-space rotation/transform matrix for directional light vectors | `[CODE vu1_func.inc:3400,3575]` |
| `989..991` | `0x3DD0..0x3DF0` (`15824..15856`) | `.xyz` | 3x3 rotation/transform matrix for spotlight position/direction and half-vector offset `1017` | `[CODE vu1_func.inc:3239,3283,3345]` |
| `998..1001` | `0x3E60..0x3E90` (`15968..16016`) | `.xyzw` | Camera / view-projection 4x4 matrix rows (`998..1000` `.xyz` rows, `1001` translation row) | `[CODE vu1_func.inc:1160]` `[CODE VU1_HANDLER_FORMS.md:23-24]` |
| `1002` | `0x3EA0` (`16032`) | `.xyzw` | Viewport scale (`vpScale`, `c1v`) applied to projected position | `[CODE vu1_func.inc:2339,2366,2681]` `[INFERRED]` |
| `1003` | `0x3EB0` (`16048`) | `.xyzw` | Viewport offset (`vpOffset`, `c2v`) added to `c1v * pos` | `[CODE vu1_func.inc:2339,2367,2681]` `[INFERRED]` |
| `1010` | `0x3F20` (`16160`) | `.xyzw` | Bounding-sphere center (`.xyz`) and radius (`.w`) for spotlight cone cull (`0CC0`) | `[CODE vu1_func.inc:3283,3286]` `[CODE VU1_HANDLER_FORMS.md:297]` |
| `1011` | `0x3F30` (`16176`) | `.x,.y,.w` | Batch control: `.x` = `base` vertex offset, `.y` = rigid/skin flag (`<0` = rigid), `.w` = vertex count `n` | `[CODE vu1_func.inc:1165,2603,3227]` |
| `1012` | `0x3F40` (`16192`) | `.z,.w` | GIFTAG upper words (`m1012z`, `m1012w`) copied into output GIF header | `[CODE vu1_func.inc:2340,2716]` |
| `1013` | `0x3F50` (`16208`) | `.xyzw` | Material/lighting colour scale (`vf16`) multiplied with vertex colour `Cs` | `[CODE vu1_func.inc:2339,2368,2681]` `[INFERRED]` |
| `1014` | `0x3F60` (`16224`) | `.xyzw` | Ambient colour (`c14v`) added to accumulated light colour `As` (`vf2` in `1EE0`) | `[CODE vu1_func.inc:2339,2369-2370,2681]` `[INFERRED]` |
| `1015` | `0x3F70` (`16240`) | `.xyzw` | 4-term specular polynomial coefficients `(c0, c1, c2, c3)` for `c0*d + c1*d^2 + c2*d^4 + c3*d^8` | `[CODE vu1_func.inc:3212,3241,3350,3404]` |
| `1016` | `0x3F80` (`16256`) | `.z,.w` | Fog constants (`c5v`): `fog = clamp(c5v.z + c5v.w * Q, 0, 255)` | `[CODE vu1_func.inc:2339,2412-2413,2681]` `[INFERRED]` |
| `1017` | `0x3F90` (`16272`) | `.xyz` | Camera/view half-vector offset transformed by `989..991` to `hOff` | `[CODE vu1_func.inc:3239-3240,3345,3349]` `[CODE VU1_HANDLER_FORMS.md:275]` |
| `1018` | `0x3FA0` (`16288`) | `.x,.y,.z,.w` | Stream bases relative to `vi12` (`.x`=S2, `.y`=S3, `.z`=I4) and `.w` = vertex count `N` (`1EE0`/`1C48`) | `[CODE vu1_func.inc:2605-2608,3135]` |
| `1023` | `0x3FF0` (`16368`) | `.z,.w` | Output GIF buffer base `ubase` (`.z`) and double-buffer swap state (`.w`) | `[CODE vu1_func.inc:2609,2717]` |

---

## Handler Details

### 1. Handler `0x00A8` (Object Matrix Setup & Vertex/Normal Transform)

- **(a) Reads**:
  - `978..981` (`0x3D20..0x3D50`, bytes `15648..15696`): Object matrix rows R0..R3 `[CODE vu1_func.inc:1160,1170-1171]`.
  - `998..1001` (`0x3E60..0x3E90`, bytes `15968..16016`): Camera / view-projection matrix rows `[CODE vu1_func.inc:1160]`.
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `vi3` (base) and `vi2` (trip count `n`) `[CODE vu1_func.inc:1165]`.
  - `vi3 + 476 .. vi3 + 476 + n - 1` (base `0x1DC0`, bytes `7616+`): Input vertex/normal stream `[CODE vu1_func.inc:1180-1196]`.
- **(b) Writes**:
  - `vi3 + 636 .. vi3 + 636 + n - 1` (base `0x27C0`, bytes `10176+`): Transformed positions/vectors (`M * v`) `[CODE vu1_func.inc:1180,1243-1245]`.
  - `vi3 + 716 .. vi3 + 716 + n - 1` (base `0x2CC0`, bytes `11456+`): Zeroed vertex colour accumulator stream (`vf31 = 0`) `[CODE vu1_func.inc:1161,1188,1240-1241]`.
  - Calls `scene::setObjMatrix(vf1, vf2, vf3, vf4)` `[CODE vu1_func.inc:1178-1179]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 2. Handler `0x1C48` (Light Matrix Block)

- **(a) Reads**:
  - `1018` (`0x3FA0`, byte `16288`) `.x,.w`: `vi1_0` (stream offset) and `n` (vector count) `[CODE vu1_func.inc:3135]`.
  - `vi13 .. vi13 + 3` (advances `vi13 += 4`): 4x3+translation transform matrix (`vf1..vf4`) `[CODE vu1_func.inc:3138-3142]`.
  - `base .. base + n - 1` where `base = vi1_0 + R.vi[12]`: Input vectors `[CODE vu1_func.inc:3143,3151]`.
- **(b) Writes**:
  - `base .. base + n - 1`: Transformed vectors in place (`vf1*v.x + vf2*v.y + vf3*v.z + vf4`) `[CODE vu1_func.inc:3152-3156]`.
- **(c) EE routine**: `emitVu1LightMatrixBlock` referenced in [VU1_MAP.md](file:///c:/ApeEscape3_Recomp/docs/VU1_MAP.md#L29) (DECOMP_LOG BY3; handler ids `0x3F2`/`0x321`/`0x39B`...); `sub_003BC770` emits `VU1CMD 0x320, 0x398, 0x39B` in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md#L566) `[CODE EE_RENDER_MAP.md:566,795]`.

### 3. Handler `0x0198` (4-Directional Diffuse Light)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3560]`.
  - `vi13 .. vi13 + 2` (advances `vi13 += 7`): 3x4 light-direction rows `d0..d2` (4 lights across `.xyzw`) `[CODE vu1_func.inc:3567-3569]`.
  - `vi13 + 3 .. vi13 + 6`: 4x4 light RGBA colour matrix `c0..c3` (one RGBA per light) `[CODE vu1_func.inc:3570-3574]`.
  - `986..988` (`0x3DA0..0x3DC0`, bytes `15776..15808`): 3x3 model-space transform matrix `[CODE vu1_func.inc:3575]`.
  - `base + 556 .. base + 556 + n + 2` (base `0x22C0`, bytes `8896+`): Vertex normal stream `Nrm` (plus `n+1`, `n+2` for exit `vf11..vf12`) `[CODE vu1_func.inc:3583,3593-3595]`.
  - `base + 716 .. base + 716 + n` (base `0x2CC0`, bytes `11456+`): Existing vertex colour accumulator `Col` `[CODE vu1_func.inc:3584,3596]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += sum_i(c[i] * max(0, dot(L_i, Nrm)))` in place `[CODE vu1_func.inc:3585-3589]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 4. Handler `0x02E0` (4-Directional Specular Light)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3385]`.
  - `vi13 .. vi13 + 2` (advances `vi13 += 7`): 3x4 light-direction/half-vector rows `d0..d2` `[CODE vu1_func.inc:3392-3394]`.
  - `vi13 + 3 .. vi13 + 6`: 4x4 light RGBA colour matrix `c0..c3` `[CODE vu1_func.inc:3395-3399]`.
  - `986..988` (`0x3DA0..0x3DC0`, bytes `15776..15808`): 3x3 model-space transform matrix `[CODE vu1_func.inc:3400]`.
  - `1015` (`0x3F70`, byte `16240`): 4-term specular polynomial coefficients `(c0, c1, c2, c3)` `[CODE vu1_func.inc:3404]`.
  - `base + 556 .. base + 556 + n + 2` (base `0x22C0`, bytes `8896+`): Vertex normal stream `Nrm` `[CODE vu1_func.inc:3408,3416-3418]`.
  - `base + 716 .. base + 716 + n - 1` (base `0x2CC0`, bytes `11456+`): Existing vertex colour accumulator `Col` `[CODE vu1_func.inc:3409]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += sum_i(c[i] * max(0, poly4Spec(dot(L_i, Nrm))))` in place `[CODE vu1_func.inc:3410-3413]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 5. Handler `0x0628` (Point Diffuse Light)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3441]`.
  - `vi13` (advances `vi13 += 2`): `cmd0.xyz` = light position `[CODE vu1_func.inc:3448,3450]`.
  - `vi13 + 1`: `cmd1.xyzw` = light RGBA colour `[CODE vu1_func.inc:3449]`.
  - `982..985` (`0x3D60..0x3D90`, bytes `15712..15760`): 4x3 affine matrix transforming `cmd0.xyz` to local light position `L` `[CODE vu1_func.inc:3451-3452]`.
  - `base + 476 .. base + 476 + n - 1` (base `0x1DC0`, bytes `7616+`): Vertex position stream `P` `[CODE vu1_func.inc:3456]`.
  - `base + 556 .. base + 556 + n - 1` (base `0x22C0`, bytes `8896+`): Vertex normal stream `Nrm` `[CODE vu1_func.inc:3457]`.
  - `base + 716 .. base + 716 + n - 1` (base `0x2CC0`, bytes `11456+`): Existing vertex colour accumulator `Col` `[CODE vu1_func.inc:3458]`.
- **(b) Writes**:
  - If `prologue`: stores live-in `R.vf[11..13]` to `R.vi[4] + 17`, `+ 19`, `+ 21` `[CODE vu1_func.inc:3437-3439]`.
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += cmd1 * (max(0, dot(L - P, Nrm)) / ||L - P||^2)` in place `[CODE vu1_func.inc:3459-3469]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 6. Handler `0x0840` (Point Specular Light)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3227]`.
  - `vi13` (advances `vi13 += 2`): `cmdPos.xyz` = light position `[CODE vu1_func.inc:3234,3236]`.
  - `vi13 + 1`: `cmdCol.xyzw` = light RGBA colour `[CODE vu1_func.inc:3235]`.
  - `982..985` (`0x3D60..0x3D90`, bytes `15712..15760`): 4x3 affine matrix transforming `cmdPos.xyz` to `L` `[CODE vu1_func.inc:3237-3238]`.
  - `989..991` (`0x3DD0..0x3DF0`, bytes `15824..15856`) and `1017` (`0x3F90`, byte `16272`): 3x3 matrix * `1017.xyz` -> half-vector offset `hOff` `[CODE vu1_func.inc:3239-3240]`.
  - `1015` (`0x3F70`, byte `16240`): 4-term specular polynomial coefficients `[CODE vu1_func.inc:3241]`.
  - `base + 476 .. base + 476 + n - 1`, `base + 556 .. base + 556 + n - 1`, `base + 716 .. base + 716 + n - 1`: `P`, `Nrm`, `Col` `[CODE vu1_func.inc:3245-3247]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += cmdCol * (max(0, poly4Spec(dot(Nrm, normalize(hOff + dir)))) / d)` in place `[CODE vu1_func.inc:3248-3261]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 7. Handler `0x0CC0` (Diffuse Spotlight with Cone Cull)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3271]`.
  - `vi13 .. vi13 + 3` (advances `vi13 += 4`): `cmd0.xyz` = light position, `cmd1.xyzw` = light RGBA colour, `cmd2.xyz` = spotlight direction (negated), `cmd3.xyzw` = `(.x=cos_cutoff, .y=falloff_scale, .z=cos2_bound_cone, .w=bound_sphere_offset)` `[CODE vu1_func.inc:3278-3282]` `[CODE VU1_HANDLER_FORMS.md:293-296]`.
  - `989..991` (`0x3DD0..0x3DF0`, bytes `15824..15856`) and `985` (`0x3D90`, byte `15760`): 3x3 matrix + translation -> `L` and `D` `[CODE vu1_func.inc:3283-3289]`.
  - `1010` (`0x3F20`, byte `16160`): Bounding-sphere center/radius for early-out cone cull `[CODE vu1_func.inc:3283,3286-3302]`.
  - `base + 476 .. base + 476 + n - 1`, `base + 556 .. base + 556 + n - 1`, `base + 716 .. base + 716 + n - 1`: `P`, `Nrm`, `Col` `[CODE vu1_func.inc:3306-3308]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: If not cone-culled, accumulates `Col += cmd1 * (spotClamp * nlClamp / d)` in place `[CODE vu1_func.inc:3309-3323]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 8. Handler `0x1090` (Specular Spotlight)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3333]`.
  - `vi13 .. vi13 + 3` (advances `vi13 += 4`): `cmd0.xyz` = light position, `cmd1.xyzw` = light RGBA colour, `cmd2.xyz` = spotlight direction (negated), `cmd3.xy` = cone cutoff & falloff scale `[CODE vu1_func.inc:3340-3344]` `[CODE VU1_HANDLER_FORMS.md:316]`.
  - `989..991` (`0x3DD0..0x3DF0`), `985` (`0x3D90`), `1017` (`0x3F90`): 3x3 matrix + translation -> `L`, `D`, `hOff` `[CODE vu1_func.inc:3345-3349]`.
  - `1015` (`0x3F70`, byte `16240`): 4-term specular polynomial coefficients `[CODE vu1_func.inc:3350]`.
  - `base + 476 .. base + 476 + n - 1`, `base + 556 .. base + 556 + n - 1`, `base + 716 .. base + 716 + n - 1`: `P`, `Nrm`, `Col` `[CODE vu1_func.inc:3354-3356]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += cmd1 * (max(0, poly4Spec(dot(Nrm, hNorm) * spotClamp)) / d)` in place `[CODE vu1_func.inc:3357-3375]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 9. Handler `0x1720` (Quadratic-Falloff Point Light)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.x,.w`: `base` and vertex count `n` `[CODE vu1_func.inc:3479]`.
  - `vi13 .. vi13 + 2` (advances `vi13 += 3`): `cmd0.xyz` = light position, `cmd1.xyzw` = light RGBA colour, `cmd2.xyzw` = `(a, b, c, cap)` quadratic falloff coefficients and clamp ceiling `[CODE vu1_func.inc:3486-3489]` `[CODE VU1_HANDLER_FORMS.md:367]`.
  - `982..985` (`0x3D60..0x3D90`, bytes `15712..15760`): 4x3 affine matrix transforming `cmd0.xyz` to `L` `[CODE vu1_func.inc:3490-3491]`.
  - `base + 476 .. base + 476 + n - 1`, `base + 716 .. base + 716 + n - 1`: `P` and `Col` `[CODE vu1_func.inc:3495-3496]`.
- **(b) Writes**:
  - `base + 716 .. base + 716 + n - 1`: Accumulates `Col += cmd1 * clamp(a*d^2 + b*d + c, 0, cap)` in place `[CODE vu1_func.inc:3497-3507]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 10. Handler `0x1EE0` / `0x1EF0` + `buildLeanSkinVertsImpl` (Skinned Mesh Path)

- **(a) Reads**:
  - `1011` (`0x3F30`, byte `16176`) `.y`: Rigid vs skinned selector (`>= 0` = skinned) `[CODE vu1_func.inc:2603]`.
  - `1018` (`0x3FA0`, byte `16288`) `.x,.y,.z,.w`: `s2base` (`+vi12`), `s3base` (`+vi12`), `i4base` (`+vi12`), vertex count `N` `[CODE vu1_func.inc:2605-2608]`.
  - `1023` (`0x3FF0`, byte `16368`) `.z,.w`: `ubase` (output GIF buffer) and `ctlOld` `[CODE vu1_func.inc:2609,2717]`.
  - `1012` (`0x3F40`, byte `16192`) `.z,.w`: GIFTAG upper words `[CODE vu1_func.inc:2716]`.
  - `vi13` (`.y`, advances `vi13 += 1`): `vf27y` GIFTAG/pass word `[CODE vu1_func.inc:2612,2635]`.
  - `1002` (`vpScale`), `1003` (`vpOffset`), `1013` (`vf16` colour scale), `1014` (`vf2` ambient), `1016` (`vf1` fog) `[CODE vu1_func.inc:2681]`.
  - `i4base + t`: Index stream `idx` (int16 `.x`) `[CODE vu1_func.inc:2649]`.
  - `636 + idx` (base `0x27C0`, bytes `10176+`): Pre-transformed vertex positions `gA` (bone-weighted positions written earlier by `00A8` / `0088`) `[CODE vu1_func.inc:2489]`.
  - `716 + idx` (base `0x2CC0`, bytes `11456+`): Accumulated vertex lighting colours `gB` `[CODE vu1_func.inc:2490]`.
  - `s3base + s`: Per-vertex material/diffuse colour stream `gS3` `[CODE vu1_func.inc:2491]`.
  - `796 + idx` (`0x1EF0`, `VI10=true`) or `s2base + s` (`0x1EE0`, `VI10=false`): STQ UV stream `gS2` `[CODE vu1_func.inc:2492]`.
  - Note: Bone matrices are **not** read inside `1EE0`/`buildLeanSkinVertsImpl` itself; bone-matrix blending/transforms into `636+idx` happen in preceding `00A8`/`0088` passes `[CODE VU1_MAP.md:28]` `[INFERRED]`.
- **(b) Writes**:
  - `ubase .. ubase + 4*N`: Output GIF packet (header at `ubase`, then STQ, RGBA, XYZF2 per vertex) and `1023` `.z/.w` swap `[CODE vu1_func.inc:2724-2726,2773-2774]`.
  - In lean path: writes `RdVert` (`pos`, `rgba`, `uv`, `fog`) and `rdIndices` directly `[CODE vu1_func.inc:2567-2582]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

### 11. Handler `0x2440` (`rigid2440`, Rigid Mesh Path)

- **(a) Reads**:
  - Invoked from `1EE0` when `mem[1011].y < 0` `[CODE vu1_func.inc:2603,2613,2618]`.
  - `1002` (`c1v` `vpScale`), `1003` (`c2v` `vpOffset`), `1013` (`vf16` colour scale), `1014` (`c14v` ambient), `1016` (`c5v` fog), `1012.zw` (GIFTAG upper words) `[CODE vu1_func.inc:2339-2340]`.
  - `i4base + it`: Index + ADC flag word (`Wd[it]`, bit 15 = ADC) `[CODE vu1_func.inc:2351,2416]`.
  - `636 + ix` (base `0x27C0`, bytes `10176+`): Pre-transformed vertex positions `Ps` `[CODE vu1_func.inc:2353,2418]`.
  - `716 + ix` (base `0x2CC0`, bytes `11456+`): Accumulated vertex lighting colours `As` `[CODE vu1_func.inc:2359,2424]`.
  - `796 + ix` (if `copyS`) or `s2base + pS`: STQ UV stream `Ss` `[CODE vu1_func.inc:2360,2425]`.
  - `s3base + pC`: Per-vertex material/diffuse colour stream `Cs` `[CODE vu1_func.inc:2357,2428]`.
- **(b) Writes**:
  - `ubase .. ubase + 4*N`: Output GIF packet (header at `ubase`, STQ at `+1`, RGBA `clampI(Lit)` at `+2`, XYZF2 at `+3/+4`), plus `1022.x` if `hit == 5` `[CODE vu1_func.inc:2354-2355,2408-2409,2421-2446]`.
- **(c) EE routine**: Unknown (not mapped per-handler in [EE_RENDER_MAP.md](file:///c:/ApeEscape3_Recomp/docs/EE_RENDER_MAP.md)).

---

## Proposed `SceneDraw` Additions

To let a lighting/shadow renderer rebuild lighting at `MSCAL` time without extra VU1 cost:

1. **Per-light capture at light-handler `MSCAL` time** (in `handler0198`, `handler02E0`, `handler0628`, `handler0840`, `handler0CC0`, `handler1090`, `handler1720`):
   - `struct SceneLight`:
     - `uint32_t type;` (enum: `DIR4_DIFF` `0x0198`, `DIR4_SPEC` `0x02E0`, `POINT_DIFF` `0x0628`, `POINT_SPEC` `0x0840`, `SPOT_DIFF` `0x0CC0`, `SPOT_SPEC` `0x1090`, `POINT_FALLOFF` `0x1720`)
     - `float dirOrPos[4][4];` (4-dir: `Lx, Ly, Lz` or `cmd[0..2]` transformed by `986..988`; point/spot: `L` in `dirOrPos[0]` and `D` in `dirOrPos[1]`)
     - `float colour[4][4];` (4-dir: `cmd[3..6]` from `vi13+3..6`; point/spot: `cmd[1]` from `vi13+1`)
     - `float params[4];` (`1015` specular poly for `02E0`/`0840`/`1090`; `cmd[3]` cone params for `0CC0`/`1090`; `cmd[2]` quadratic falloff for `1720`; `hOff` from `989..991 * 1017` if needed)
   - `uint32_t lightCount;` and `uint32_t firstLight;` (or inline `SceneLight lights[MAX_LIGHTS]`) on `SceneDraw`: append to a per-frame `std::vector<SceneLight>` as each light handler runs, and snapshot `(firstLight, lightCount)` when `pushDraw` / `beginLeanDraw` is called (resetting or scoping per object/material batch).
2. **Ambient, Material Scale, and Fog** (already loaded at `1EE0`/`2440` `MSCAL` time):
   - `float ambient[4];` — source: VU qword `1014` (`0x3F60`) `[CODE vu1_func.inc:2339,2681]`.
   - `float lightScale[4];` — source: VU qword `1013` (`0x3F50`) `[CODE vu1_func.inc:2339,2681]`.
   - `float fogParams[4];` — source: VU qword `1016` (`0x3F80`, `.zw`) `[CODE vu1_func.inc:2339,2681]`.
3. **Camera / View-Projection Matrix** (already loaded in `handler00A8`):
   - `float viewProjMatrix[16];` — source: VU qwords `998..1001` (`0x3E60..0x3E90`) `[CODE vu1_func.inc:1160]`.
4. **Bone Matrices** (`float boneMatrices[][16]` indexed by `firstBone`, `boneCount`):
   - `00A8` (and `1C48` if used for bone transforms) already computes `M` from `978..981` and `998..1001` `[CODE vu1_func.inc:1160-1179]` or reads `vi13..vi13+3` `[CODE vu1_func.inc:3138-3141]`. Capture each bone's `978..981` object/bone matrix in `handler00A8` (already hooked at `scene::setObjMatrix` `:1179`) into a per-frame bone palette and attach `(firstBone, boneCount)` to `SceneDraw` at `1EE0` `MSCAL` time.
