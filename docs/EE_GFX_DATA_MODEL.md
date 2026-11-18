# EE Graphics Engine Data Model

Data structures observed in [`ee_gfx_decomp.cpp`](file:///C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/decomp/ee_gfx_decomp.cpp).

---

## 1. Render Context (`RenderCtx`)

Top-level graphics/render state passed as `$a0` across packet-building, draw-list, and state-cache routines.

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0010` | `PktBufState*` | Active DMA/VIF packet buffer state | `sub_003B3CE0` (`pktAllocTailQwc`), `sub_003B3D80` (`pktGetWritePtr`), `sub_003B3D88` (`pktSetWritePtr`), `sub_003B8898` (`commitDrawNodePacketPtr`), `sub_003B40F8` |
| `0x0020` | `DrawListNode*` | Currently active draw list node | `sub_003B8898` (`commitDrawNodePacketPtr`) |
| `0x6868` | `DrawListHead` | Active draw list sentinel/head | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x6870` | `DrawListNode*` | Free draw list head | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x709C` | `int32_t` / `uint32_t` | Remaining free draw-node budget | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x70B8` | `uint32_t` | Cumulative requested node allocation size | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x70BC` | `uint32_t` | Cumulative reused node size | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x70D8` | `StateCache` | Cached DMA CALL target table (`+0x04` patchPtr, `+0x08` `uint32_t cachedTarget[]`) | `sub_003B9158` (`emitCachedDmaCallChain`) |

---

## 2. Packet Buffer State (`PktBufState`)

Pointed to by `RenderCtx + 0x10`. Tracks the current DMA/VIF packet write cursor and tail allocation cursor.

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0008` | `uint32_t` | Tail write cursor (decremented by `qwc * 16`) | `sub_003B3CE0` (`pktAllocTailQwc`) |
| `0x0014` | `uint32_t` | Current packet write pointer | `sub_003B3D80` (`pktGetWritePtr`), `sub_003B3D88` (`pktSetWritePtr`), `sub_003B8898` (`commitDrawNodePacketPtr`) |

---

## 3. Draw List Node (`DrawListNode`)

Intrusive doubly-linked list node with multi-channel link slots (`3` link pairs starting at `0x00`).

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0000` | `struct { uint32_t prev; uint32_t next; }[3]` | Link slots `0..2` (`+0x00/+0x04`, `+0x08/+0x0C`, `+0x10/+0x14`) | `sub_003AF9C8` (`resetDlistNodeState`), `sub_003AF9F8` (`unlinkDlistNode`), `sub_003AFA28` / `sub_003AFA50` (`insertDlistNodeAfter`), `sub_003B86A0` (`initDrawList`), `sub_003B8448` |
| `0x0018` | `uint32_t` | Node state / sort key (cleared to `0` on reset) | `sub_003AF9C8` (`resetDlistNodeState`), `sub_003B86A0` (`initDrawList`) |
| `0x001C` | `uint32_t` | Packet end / committed write pointer | `sub_003B8898` (`commitDrawNodePacketPtr`) |
| `0x0020` | `uint32_t` | Flags (`0x1` = free, `0x100` = active/pinned, `0x10000` = allocated) | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x0028` | `DrawNodeHandle*` | Back-pointer to owning handle | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x002C` | `uint32_t` | Node capacity / allocated size | `sub_003B8448` (`allocAndPinDrawNode`) |

---

## 4. Draw Node Handle (`DrawNodeHandle`)

Caller-side handle passed to `sub_003B8448` (`allocAndPinDrawNode`).

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0000` | `DrawListNode*` | Bound draw list node (or `0` if unallocated) | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x0008` | `uint32_t` | Requested node size | `sub_003B8448` (`allocAndPinDrawNode`) |
| `0x000C` | `uint32_t` | Disabled flag (`!= 0` skips allocation) | `sub_003B8448` (`allocAndPinDrawNode`) |

---

## 5. Draw Command (`DrawCmd`)

Command descriptor queued for cached DMA chain emission.

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0010` | `uint32_t` | Cache slot index in `RenderCtx + 0x70D8` | `sub_003B9158` (`emitCachedDmaCallChain`) |
| `0x0014` | `uint32_t` | DMA CALL target address (`0x50000000`) | `sub_003B9158` (`emitCachedDmaCallChain`) |
| `0x0018` | `uint32_t` | DMA NEXT target address (`0x20000000`, masked `& 0x0FFFFFFF`) | `sub_003B9158` (`emitCachedDmaCallChain`) |
| `0x001C` | `uint32_t` | Next DMA patch pointer stored to `StateCache + 0x04` | `sub_003B9158` (`emitCachedDmaCallChain`) |

---

## 6. DMA REF Descriptor (`DmaRefDesc`)

Descriptor used to emit a 128-bit DMA REF + VIF1 STCYCL/UNPACK (or NOP) tag.

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0000` | `uint32_t` | Source data address (`0` = skip, masked `& 0x0FFFFFFF`) | `sub_003BA7D8` |
| `0x0004` | `uint16_t` | Quadword count (`QWC`) | `sub_003BA7D8` |
| `0x0006` | `uint16_t` | Padding | `sub_003BA7D8` |
| `0x0008` | `uint32_t` | Unknown | `sub_003BA7D8` |
| `0x000C` | `int32_t` | Mode (`0` = VIF UNPACK V4-32 `0x6C`, `1` = VIF NOP, other = skip) | `sub_003BA7D8` |

---

## 7. Animation Track Header & Keyframes (`AnimTrackHeader`, `AnimTrackDesc`, `AnimKeyframe`)

Used by the animation sampling and keyframe lookup pipeline.

### `AnimTrackHeader`
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0010` | `uint16_t` | Channel flags (`0x1` packed rot, `0x2` unit scale, `0x4` interp mode adjust, `0x8` packed pos, `0x10` packed scale) | `sub_003ABBD0` (`sampleAnimKeyframePair`), `sub_003ABDB8`, `sub_003ABE60` (`evalAnimChannelTransform`), `sub_003ABF68` (`evalAnimChannelAtTime`) |
| `0x0012` | `uint16_t` | Keyframe stride in `uint16_t` units (`kf1 = kf0 + (stride << 1)`) | `sub_003ABBD0` (`sampleAnimKeyframePair`) |
| `0x0020` | `uint32_t` | Constant 128-bit `vec4` table base | `sub_003ABBD0` (`sampleAnimKeyframePair`) |
| `0x0024` | `uint32_t` | Float time table base | `sub_003ABF68` (`evalAnimChannelAtTime`) |
| `0x0028` | `uint32_t` | Packed `int16_t[4]` table base (8-byte entries) | `sub_003ABBD0` (`sampleAnimKeyframePair`) |
| `0x0030` | `vec4[2]` | Position unpack scale/offset (`+0x30`, `+0x40`) | `sub_003ABBD0` (`sampleAnimKeyframePair`), `sub_003AB950` (`unpackS16Vec4Scaled`) |
| `0x0050` | `vec4[2]` | Scale unpack scale/offset (`+0x50`, `+0x60`) | `sub_003ABBD0` (`sampleAnimKeyframePair`), `sub_003AB950` (`unpackS16Vec4Scaled`) |

### `AnimTrackDesc` & `AnimKeyframe`
| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `AnimTrackDesc` | `0x0004` | `uint8_t` | Keyframe stride in `uint16_t` units | `sub_003AC068` (`findKeyframeByTime`) |
| `AnimTrackDesc` | `0x0006` | `uint16_t` | Keyframe count | `sub_003AC068` (`findKeyframeByTime`) |
| `AnimTrackDesc` | `0x0008` | `uint32_t` | Keyframe array base pointer | `sub_003AC068` (`findKeyframeByTime`) |
| `AnimKeyframe` | `0x0000` | `uint16_t` | Start time index in `timeTable` | `sub_003AC068`, `sub_003ABF68` |
| `AnimKeyframe` | `0x0002` | `uint16_t` | Inverse duration index in `timeTable` | `sub_003ABF68` (`evalAnimChannelAtTime`) |
| `AnimKeyframe` | `0x0004` | `uint16_t` | Position value index | `sub_003ABBD0` (`sampleAnimKeyframePair`) |
| `AnimKeyframe` | `0x0006` | `uint16_t` | Rotation value index | `sub_003ABBD0` (`sampleAnimKeyframePair`) |
| `AnimKeyframe` | `0x0008` | `uint16_t` | Scale value index | `sub_003ABBD0` (`sampleAnimKeyframePair`) |

---

## 8. Object / Draw Entry (`GfxObject`)

Scene object descriptor with embedded DMA pointers and template fields.

| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0018` | `uint32_t` | Primary DMA tag address | `sub_003AFED8` |
| `0x03F8` | `uint32_t` | Secondary DMA tag address | `sub_003AFEA8` |
| `0x0830` | `uint32_t` | Primary DMA pointer | `sub_003AFED8` |
| `0x0834` | `uint32_t` | Secondary DMA pointer | `sub_003AFEA8`, `sub_003B7738` (`getObjSecondaryDmaPtr`) |
| `0x0840` | `uint32_t` | Object DMA end pointer | `sub_003A9280` (`getObjDmaEndPtr`) |

---

## 9. Render Context Free-Node & Coalescing Fields (`RenderCtx`, DECOMP-BT)

Additional fields in `RenderCtx` and `DrawListNode` used by free-node stack management and coalescing:

| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `RenderCtx` | `0x6884` | `DrawListNode*` | Channel 3 list head (pending coalesce list, `0x6868 + 0x1C`) | `sub_003B8220` (`clearPendingCoalesceList`) |
| `RenderCtx` | `0x689C` | `DrawListNode*[]` | Free draw-node pointer stack | `sub_003B7E88` (`popFreeDrawNode`), `sub_003B7EC0` (`pushFreeDrawNode`) |
| `RenderCtx` | `0x70A0` | `uint32_t` | Free draw-node stack top index | `sub_003B7E88` (`popFreeDrawNode`), `sub_003B7EC0` (`pushFreeDrawNode`) |
| `DrawListNode` | `0x0018` | `struct { uint32_t prev; uint32_t next; }` | Link slot 3 (`+0x18/+0x1C`, pending coalesce channel) | `sub_003AFA98` (`unlinkDlistNodeAll`), `sub_003B8220`, `sub_003B8380` |
| `DrawListNode` | `0x0020` | `uint32_t` | Additional flags (`0x10` = pinned/costed, `0x1000` = coalesceable) | `sub_003B7F18`, `sub_003B7FC0`, `sub_003B8220`, `sub_003B8380` |
| `DrawListNode` | `0x0024` | `uint32_t` | Node metadata (cleared to `0` on pop) | `sub_003B7E88` (`popFreeDrawNode`) |
| `DrawListNode` | `0x0030` | `uint32_t` | Node metadata (cleared to `0` on pop) | `sub_003B7E88` (`popFreeDrawNode`) |

---

## 10. Frustum & Bounds Structures (`FrustumCtx`, `PlaneMarginDesc`, DECOMP-BT)

| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `FrustumCtx` | `0x01A0` | `mat4` (`vec4[4]`) | Secondary frustum/cull matrix (tested via VU0 microprogram `0x348`) | `sub_003BA898` (`testFrustumAabb`) |
| `FrustumCtx` | `0x0260` | `mat4` (`vec4[4]`) | Primary frustum/cull matrix (tested via VU0 microprogram `0x4B0`) | `sub_003BA898` (`testFrustumAabb`) |
| `PlaneMarginDesc` | `0x000C` | `float` | Margin/radius added to AABB half-extents before `testAabbPlane` | `sub_003C2008` (`testAabbPlaneWithMargin`) |

---

## 11. Material & Render State Hash Caches (DECOMP-BU)

256-bucket circular-list hash tables used by `sub_003BBB50` (`lookupOrAllocMatState`) and `sub_003B7A00` (`lookupOrAllocRenderState`).

### `StateCacheCtx` (passed as `$a0` to `3BBB50` / `3B7A00`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x000C` | `SortNode*` | Tail of 1-QW sort node list | `sub_003B7A00` |
| `0x0010` | `uint32_t` | Sort node count | `sub_003B7A00` |
| `0x0014` | `RenderStateEntry*[256]` | 256-bucket hash table for `RenderStateEntry` | `sub_003B7A00` |
| `0x0414` | `MatStateEntry*[256]` | 256-bucket hash table for `MatStateEntry` | `sub_003BBB50` |
| `0x0814` | `PktBufState*` | Packet buffer state for tail QW allocation (`sub_003B3CE0`) | `sub_003BBB50`, `sub_003B7A00` |
| `0x082C` | `uint32_t` | Active render/material key 0 | `sub_003BBB50` |
| `0x0830` | `uint32_t` | Active render/material key 2 | `sub_003BBB50` |
| `0x0834` | `uint32_t` | Active render/material key 1 | `sub_003BBB50` |

### `MatStateEntry` (4 QWs / `0x40` bytes) & `MatDesc`
| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `MatDesc` | `0x0000` | `MatSubDesc*` | Sub-descriptor (`+0x08` `uint16_t` key, `+0x0A` `uint8_t` flag) | `sub_003BBB50` |
| `MatDesc` | `0x0008` | `void*` | Packet size descriptor (`+0x04` lower 24 bits = word count) | `sub_003BBB50` |
| `MatStateEntry` | `0x0000` | `uint32_t` | Full 32-bit hash | `sub_003BBB50` |
| `MatStateEntry` | `0x0004` / `0x0008` | `MatStateEntry*` | Circular list `next` / `prev` pointers | `sub_003BBB50` |
| `MatStateEntry` | `0x000C` / `0x0010` | `uint32_t` | State object pointer (`sub_003B7950`) & its `+0x0C` word | `sub_003BBB50` |
| `MatStateEntry` | `0x0014` | `uint32_t` | Non-zero `MatSubDesc+0x0A` flag (`0` or `1`) | `sub_003BBB50` |
| `MatStateEntry` | `0x0018` / `0x001C` | `uint32_t` | Word count (24-bit) & allocated packet buffer pointer | `sub_003BBB50` |
| `MatStateEntry` | `0x0024`..`0x0034` | `uint32_t` | Key tuple: `k82c`, `k834`, `k830`, `matDesc`, `subKey` | `sub_003BBB50` |

### `RenderStateEntry` (4 QWs / `0x40` bytes) & `RenderStateDesc`
| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `RenderStateDesc` | `0x0000` | `float` | Float key (also XOR-encoded into sort node `+0x00`) | `sub_003B7A00` |
| `RenderStateDesc` | `0x0004` | `uint32_t*` | Variable-length `uint32_t` key array | `sub_003B7A00` |
| `RenderStateDesc` | `0x0008` | `uint32_t` | Array element count | `sub_003B7A00` |
| `RenderStateDesc` | `0x000C`..`0x0014` | `uint32_t` | Scalar key words (`w0C`, `w10`, `w14`) | `sub_003B7A00` |
| `RenderStateEntry` | `0x0000` | `uint32_t` | Full 32-bit hash | `sub_003B7A00` |
| `RenderStateEntry` | `0x0004` | `RenderStateEntry*` | Circular list `next` pointer | `sub_003B7A00` |
| `RenderStateEntry` | `0x0020`..`0x0034` | `float`/`uint32_t` | Key fields: `f20`, `arrPtr`, `count`, `w0C`, `w10`, `w14` | `sub_003B7A00` |

---

## 12. GS Image Upload & VU1 Tiled-Pass Packet Builders (DECOMP-BV)

Used by `sub_003ADEC0` (`buildGfxPassPackets`), `sub_003AD0F8` (`emitGsImageUpload`), and `sub_003AD2B0` (`emitGsTexStripUpload`).

### `GfxPassDesc` (passed as `$a0` to `sub_003ADEC0`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0004` | `uint32_t` | Pass mode (`0..7`), dispatched via jump table `0x007204F8` | `sub_003ADEC0` |
| `0x0024` | `uint32_t` | Strip width (for `sub_003AD2B0` mode) | `sub_003ADEC0` |
| `0x0028` | `uint32_t` | GS pixel format (`psm`) | `sub_003ADEC0` |
| `0x002C` | `uint32_t` | Source RAM address (`srcAddr`) | `sub_003ADEC0` |
| `0x0038` | `GfxPassEntry[]` | Array of `0x20`-byte pass entries | `sub_003ADEC0` |
| `0x0118` | `uint32_t` | Entry count in `GfxPassEntry[]` | `sub_003ADEC0` |

### `GfxPassEntry` (`0x20` bytes per entry, starting at `GfxPassDesc+0x38`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0000` | `uint64_t` | Base `BITBLTBUF` value (combined with `(baseAddr << 32)`) | `sub_003ADEC0` |
| `0x0008` | `uint64_t` | Packed dimensions: bits `11:0` = width `w`, bits `63:32` = height `h` | `sub_003ADEC0` |
| `0x0010` | `uint32_t` | Source RAM base address for tile/image data | `sub_003ADEC0` |
| `0x0014` | `uint32_t` | QWC / upload count (direct upload mode) | `sub_003ADEC0` |

---

## 13. Render List, Batch & Frustum Cull Structures (DECOMP-BW)

Observed in `sub_003AFC28`, `sub_003B3680`, `sub_003B3740`, `sub_003B76D0`, `sub_003B7950`, `sub_003B8F78`, `sub_003B9270`, `sub_003B9310`, `sub_003BAAC0`.

### `RenderCtx` additional offsets (`$a0` in pass/list helpers)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x001C` | `EntryPair*` | Array of `0x10`-byte `{unk0, p4, p8, unkC}` sub-pass buffer pairs | `sub_003B3680`, `sub_003B3740` |
| `0x0020` | `uint32_t` | Capacity of `EntryPair[]` at `+0x1C` | `sub_003B3680`, `sub_003B3740` |
| `0x02E0` / `0x0320` / `0x0360` | `vec4[4]` | Frustum / cull plane matrices (4 QWs each) | `sub_003BAAC0` |
| `0x0814` | `void*` | Allocator / heap handle passed to `3B40F8` and `3B3CE0` | `sub_003AFC28` |
| `0x0818` | `void*` | Active sort-list pointer | `sub_003B76D0`, `sub_003B7740`, `sub_003B7798` |
| `0x0828` | `void*` | Current render-context descriptor | `sub_003B76D0` |
| `0x709C` | `uint32_t` | Remaining buffer budget checked by `sub_003B3680` | `sub_003B3680` |
| `0x70A4` | `RenderPassBatch*` | Head of linked `RenderPassBatch` list (`+0x1C` = next) | `sub_003B3740` |
| `0x70D8` | `DmaListState` | `{unk0, pktCursor (+0x04), slotFlags[] (+0x08..)}` | `sub_003B9270`, `sub_003B9310` |

### `RenderPassBatch` (`sub_003AFC28` / `sub_003B3680` / `sub_003B3740`)
| Offset | Type | Meaning |
|---|---|---|
| `0x0000` | `uint32_t` | Batch key / tag (`$a3` to `3AFC28`) |
| `0x0004` / `0x0008` | `void*` | Circular list `next` / `prev` (initialized to self) |
| `0x000C` | `void*` | Result of `sub_003B40F8` |
| `0x0010` / `0x0014` | `uint32_t*` | Sub-arrays allocated via `sub_003B3CE0` |
| `0x0018` | `void*` | Owning `RenderCtx*` |
| `0x001C` | `RenderPassBatch*` | Next batch in `RenderCtx+0x70A4` list |
| `0x0024` / `0x0028` | `uint32_t*` / `uint32_t` | Index array & element count |

### `RenderListNode` (`sub_003B8F78` / `sub_003B9270` / `sub_003B9310`)
| Offset | Type | Meaning |
|---|---|---|
| `0x0004` | `RenderListNode*` / `uint32_t` | Next node or packet pointer (updated by `3B8F78` callback) |
| `0x0008` | `uint32_t` | QWC (28-bit) for `0x20000000` DMA tag (`0` terminates tag loop) |
| `0x000C` | `uint32_t` | Callback function address (`sub_003B9310`) or sub-object (`sub_003B8F78`) |
| `0x0010` | `uint32_t` | Slot index into `DmaListState+0x08` (`sub_003B9270`) |
| `0x0014` | `uint32_t` | Callback table index into `0x007211D0` (`sub_003B8F78`) / QWC (`sub_003B9270`) |
| `0x0018`..`0x0024` | `uint32_t` | Mode (`+0x18 == 1` triggers `-1` arg to `3B94F0`) and callback args |

---

## 14. Mesh Descriptor & Draw List Pass Structures (DECOMP-BX)

Observed in `sub_003AF428`, `sub_003AF478`, `sub_003AF530`, `sub_003AF680`, `sub_003AF8A8`, `sub_003AF8B8`, `sub_003AF8F0`, `sub_003B89D0`, `sub_003B3D98`, `sub_003BE940`.

### `MeshDesc` (`0x3C` bytes, `sub_003AF8B8` / `sub_003AF8F0`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0000` | `vec4` | Header quadword | `sub_003AF8A8`, `sub_003AF8B8` |
| `0x0010` / `0x0014` | `uint32_t` / `void*` | Normal array count & allocated buffer (2 QWs/entry, normalized xyz) | `sub_003AF478`, `sub_003AF8F0` |
| `0x0018` / `0x001C` | `uint32_t` / `void*` | Vertex array count & allocated buffer (2 QWs/entry, raw memcpy) | `sub_003AF680`, `sub_003AF8F0` |
| `0x0020` / `0x0024` | `uint32_t` / `void*` | Sub-buffer 2 count & ptr (`sub_003AF6F8`) | `sub_003AF8F0` |
| `0x0028` / `0x002C` | `uint32_t` / `void*` | Anim key count & allocated buffer (3 QWs/entry, normalized xyz) | `sub_003AF530`, `sub_003AF8F0` |
| `0x0030` / `0x0034` | `uint32_t` / `void*` | Sub-buffer 4 count & ptr (`sub_003AF600`) | `sub_003AF8F0` |
| `0x0038` | `void*` | Owning `RenderCtx*` / allocator handle (passed to `sub_003B3CE0`) | `sub_003AF478`, `sub_003AF530`, `sub_003AF680`, `sub_003AF8F0` |

### `DrawList` splicing (`sub_003B89D0`) & `kickDmaListPass` (`sub_003B3D98`)
- `sub_003B89D0(dst, src)`: if `src->count (+0x24) != 0`, links `src->head (+0x04)` after `dst->tail (+0x0C)`, updates `dst->tail = src->tail`, adds `src->count` to `dst->count`, and resets `src`.
- `sub_003B3D98(renderCtx, passDesc)`: emits a `0x20000000` DMA NEXT tag to `sub_003B3D80(renderCtx)` at `renderCtx->dmaListState.pktCursor (+0x70DC)`, chains via `sub_003B3820`, advances `writePtr` by `0x10` (`sub_003B3D88`), and runs `sub_003B9310(renderCtx, *(passDesc+0x0C))`.
- `sub_003ACFB8`: jump-table dispatch (`0x007202C8[$a0]` for `$a0 < 0x2D`, else branches to `0x3AD008`, split piece).

---

## 15. VU1 Packet Builders & Material/Lighting Descriptors (DECOMP-BY)

Observed in `sub_003BC278`, `sub_003BC770`, `sub_003BCC50`, `sub_003BD048`, `sub_003C4230`.

### `MatDesc` (`sub_003BC278`, `sub_003BCC50`, `sub_003BD048`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `0x0010` | `float` | Blend/alpha scale factor (multiplied by `*0x7215C0`, clamped `[0, 255]`) | `sub_003BD048` |
| `0x002C` | `uint8_t` | Blend format ID (mapped via `sub_003BB878` when `+0x2D != 0`) | `sub_003BD048` |
| `0x002D` | `uint8_t` | Blend table index into `0x6AA4A0` (`!= 0` enables blend/alpha packing) | `sub_003BD048` |
| `0x002F` | `uint8_t` | Render mode index (`< 0x15` via jump table `0x7215C4` -> 2-bit state) | `sub_003BD048` |
| `0x0030` | `uint8_t` | Header VU1 pre-cmd mode (`1` = `0x168/-1.0f`, `2` = `0x168/+1.0f`, `3` = `0x690`) | `sub_003BCC50` |
| `0x0032` | `uint8_t` | Lighting packet mode (`0` = skip, `1` = direct, `2` = transformed) | `sub_003BC278` |
| `0x0033` | `uint8_t` | Texture/format ID (mapped via `sub_003BB878` when `!= 0`) | `sub_003BD048` |
| `0x0035` | `uint8_t` | Special shader/cull mode (`2`, `9`, `10` set bits 14..15 in `0x47` cmd) | `sub_003BD048` |

### `DrawObj` & `ObjMeshData` (`sub_003BC770`, `sub_003BCC50`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `DrawObj+0x00` | `MatDesc*` | Material descriptor | `sub_003BCC50` |
| `DrawObj+0x08` | `ObjMeshData*` | Mesh/animation/light-list data | `sub_003BC770`, `sub_003BCC50` |
| `ObjMeshData+0x00` | `uint32_t` | Morph/blend anim active flag (`!= 0` samples 2 tracks at `+0x08`) | `sub_003BCC50` |
| `ObjMeshData+0x08` | `AnimTrack*` | Track table (`+0x00`, `+0x10` for morph/blend) | `sub_003BCC50` |
| `ObjMeshData+0x10` | `uint32_t` | UV/tex matrix anim active flag (`!= 0` emits `0x389 = 1C48`) | `sub_003BCC50` |
| `ObjMeshData+0x18` | `AnimTrack*` | Track table (`+0x00`, `+0x10`, `+0x20` for UV/tex matrix) | `sub_003BCC50` |
| `ObjMeshData+0x34` | `uint32_t` | 24-bit light-item count (`& 0x00FFFFFF`) | `sub_003BC770` |
| `ObjMeshData+0x38` | `LightItem**` | Array of `0x10`-byte ptrs; item `+0x40` enabled, `+0x41` type (`1..4`) | `sub_003BC770` |

### `LightData` (`sub_003BC278`, `$a3`) & `BoneMtx` (`sub_003BCC50`, `$a3`)
| Offset | Type | Meaning | Used by |
|---|---|---|---|
| `LightData+0x10/+0x14` | `uint32_t` / `void*` | Array 0 count & `0x20`-stride entries (`0x39`/`0x66`, `MSCAL 8`) | `sub_003BC278` |
| `LightData+0x18/+0x1C` | `uint32_t` / `void*` | Array 1 count & `0x20`-stride entries (`0xC8`/`0x108`, `MSCAL 1`) | `sub_003BC278` |
| `LightData+0x20/+0x24` | `uint32_t` / `void*` | Array 2 count & `0x40`-stride entries (`0x19A`/`0x212`, `MSCAL 1`) | `sub_003BC278` |
| `LightData+0x28/+0x2C` | `uint32_t` / `void*` | Array 3 count & `0x30`-stride entries (`0x2BC`, `MSCAL 1`) | `sub_003BC278` |
| `LightData+0x30/+0x34` | `uint32_t` / `void*` | Array 4 count & `0x30`-stride entries (`0x2E4`, `MSCAL 1`) | `sub_003BC278` |
| `BoneMtx+0x24` | `uint8_t` | Transform active flag (`!= 0` applies `3BD3E0`/`3BD398` or emits `0xB6`) | `sub_003BCC50` |

---

## 16. Object VU1 Packet Dispatcher & Helpers (DECOMP-CA)

Observed in `sub_003BB8E8`, `sub_003BBDC8`, `sub_003BBF80`, `sub_003B8CC8`, `sub_003BE658`, `sub_003AF6F8`, `sub_003B94F0`.

### `sub_003BB8E8` (`buildDrawObjVu1Packet`) Pipeline

`sub_003BB8E8(drawObj, viewData, boneMtx)` allocates a packet buffer via `sub_003B3D80(viewData->renderCtx (+0x814))`, emits the camera/view block via `sub_003BBDC8`, and then iterates `s3 = 0 .. itemCount - 1` over `objDesc (+0x30) -> listHdr (+0x08) -> items (+0x08)` (`0x10` bytes per item). For every item, it runs the four packet builders in sequence:

| Stage | Builder | Input | Output / VU1 Role |
|---|---|---|---|
| Camera/View | `sub_003BBDC8` | `drawObj+0x28`, `drawObj+0x2C` | View/projection matrices & clip setup (`VIF UNPACK V4-32` at VU1 `0x60`) |
| Skin/Morph Pre-Header | `sub_003AFB68` + `3x sub_003AFD98` | `drawObj+0x0C`, `itemMat+0x1C >= 0` | Emitted only when `itemMat+0x1C >= 0` (VU1 `0x30`) |
| 1. Material & Pass | `sub_003BBF80` | `viewData`, `itemPtr`, `drawObj+0x2C`, `drawObj+0x24`, `hasSkin`, `s3 > 0` | Material GS/VIF (`3BD048` + `3BD238`), tex-anim patches (`3A94C0`), pass header (`0x190`/`0x3F7`/`0x3F8`/`0x3F4`, VU1 `0x10`) |
| 2. Lighting | `sub_003BC278` | `itemMat` (`*itemPtr`), `drawObj+0x28`, `drawObj+0x24` | Per-material lighting blocks (`0x39`/`0x66`, `0xC8`/`0x108`, `0x19A`/`0x212`, `0x2BC`, `0x2E4`) |
| 3. Light/Item List | `sub_003BC770` | `itemPtr`, `drawObj+0x28`, `&skinFlag` (`sp+0`) | Light-item list & matrix blocks (`0x320`/`0x321`/`0x398`/`0x39B`); writes `skinFlag` byte to `sp+0` |
| 4. Object Header | `sub_003BCC50` | `itemPtr`, `drawObj+0x28`, `boneMtx`, `hasSkin`, `skinFlag`, `0.0f` | Object header, morph/UV anim & trailer (`0x168`/`0x690`, `0xB6`, `0x389`, `0x3DC`/`0x3DE`) |

### Additional Structures
- **Scratchpad Sort (`sub_003B8CC8`)**: Uses scratchpad `0x70000000` (`8` bytes/entry: `+0x00` `uint32_t key`, `+0x04` `uint32_t nodePtr`) to cocktail-shaker sort singly-linked nodes (`mode 1` ascending, `mode 2` descending) and relink `node+0x04`.
- **Ray-Triangle (`sub_003BE658`)**: VU0-accelerated ray-triangle intersection against `uint16_t[3]` indexed `vec4` vertices (`+0x00` origin, `+0x10` dir).
- **Mesh Sub-Buffer 2 (`sub_003AF6F8`)**: `MeshDesc+0x20/+0x24` (`0x40` bytes/entry: QW1 normalized via `sub_003BDF08`, QW3 precomputed `sin`/`cos` cone terms).
- **DrawList Callback Node (`sub_003B94F0`)**: Appends a `16`-byte callback node (`+0x0C = 0x003B90A8`) to `DrawList` via `pktBufState->tail (+0x10->+0x18)`.

---

## 17. Scene Graph Relocation, Node Lists & Range Setters (DECOMP-CC)

Observed in `sub_003A7BB8`, `sub_003A8240`, `sub_003A85E0`, `sub_003AEB90`, `sub_003BBB28`, `sub_003C3D80`, `sub_003C6DA0`..`sub_003C6EE0`.

### Scene / Resource Relocation Nodes (`sub_003A7BB8`, `sub_003A85E0`)
| Struct | Offset | Type | Meaning | Used by |
|---|---|---|---|---|
| `RelocTreeNode` | `0x0000` | `uint16_t` | Child count (`0x8000` = leaf/skip flag) | `sub_003A7BB8` |
| `RelocTreeNode` | `0x0008` | `RelocTreeNode*` | Relocated child array (`-1` -> `0`; `< offset` -> `ptr + offset`; `0x0C` stride) | `sub_003A7BB8` |
| `RelocChunkNode` | `0x0000` / `0x0008` / `0x000C` | `void*` | Data, child array (`0x10` stride), and extra pointers (relocated by `+offset` when non-null) | `sub_003A85E0` |
| `RelocChunkNode` | `0x0004` | `uint32_t` | Packed header: bits `30:24` = type ID (`< 0x5A`, handler table `0x0069A310`), bit `31` = skip callback, bits `23:0` = child count | `sub_003A85E0` |

### Additional Structures
- **Doubly-Linked List Relink (`sub_003BBB28`)**: Unlinks `node` (`+0x04` next, `+0x08` prev) and inserts it before `target`.
- **VU0 AABB vs Edge-Cross (`sub_003C3D80`)**: Tests AABB half-extents (`$a0`) against triangle edge-cross extents (`$a1`, `$a2`, `$a3[0..2]`) via VU0 `vopmula`/`vopmsub` and returns `(vu0_status & 2) == 0`.
- **Range-Checked Globals (`sub_003C6DA0` / `sub_003C6E40` / `sub_003C6EE0`)**: Validate signed parameter against `[0, 1]` or `[0, 5]`, logging via `0x3C6F78`/`0x42B528` before storing to `0x00746D18`..`0x00746D20`.


---

## 18. Tree Relocation, OBB SAT, Callback Dispatch, SPR DMA & RenderCtx Init (DECOMP-CD)

Observed in `sub_003A7D08`, `sub_003C4360`, `sub_003C7D78`, `sub_003B3470`, `sub_003B4178`, `sub_003C5770`.

- **Tree Relocation Header (`sub_003A7D08`)**:
  - `node+0x10` (`uint8_t` active flag, cleared to `0` on completion)
  - `node+0x14` (`uint16_t` child0 count) / `node+0x18` (`0x0C`-byte child array; each child has `+0x00` ptr, `+0x04` `uint16_t` subCount, `+0x08` `0x30`-byte sub-array with `+0x24/+0x28/+0x2C` ptrs passed to `sub_003A7BB8`)
  - `node+0x16` (`uint16_t` ptr-table count) / `node+0x1C` (`uint32_t[]` ptr table); `-1` -> `0`, non-zero -> `+node`.
- **VU0 SAT OBB-vs-OBB (`sub_003C4360`)**: Tests 15 separating axes (3 A, 3 B, 9 cross) between two OBBs (`$a0/$a1` half-extents + 3x4 transform, `$a2/$a3` half-extents + 3x4 transform) using VU0 status bit 1.
- **Indexed Handler Dispatch (`sub_003C7D78`)**: Validates index `$a0` in `[0, 63]` and value `$a1` in `[0, 1]` (clamped on error), looks up `0x00746218 + idx * 44` (`+0x08` callback ptr), and invokes `fn(idx, clampedVal)`.
- **SPR DMA Test/Init (`sub_003B3470`)**: Enables `D_CTRL` bit 1 (`0x1000E000`), signals/waits on two `0x70000000` SPR descriptors via `0x412CB0`/`0x412FE0`, and kicks DMAC Ch8 (`0x1000D000`) & Ch9 (`0x1000D400`) with `QWC=1`.
- **RenderCtx Init (`sub_003B4178`)**: Zeroes `0x70F0` bytes at `$a0`, initializes `513` (`0x201`) `0x34`-byte pool entries backwards from `+0x6800` via `0x3AFAE8` with `+0x54 = 0x00100000`, builds `512`-entry pointer stack at `+0x7098` (count `+0x70A0 = 0x200`), and sets `+0x70A8 = 0x003B3640` and `+0x70B0 = *(float*)0x00720D30`.
- **IOP/RPC Load Request (`sub_003C5770`)**: Acquires lock (`0x0069A528`), polls `0x00746180` (`0x439848`) if `0x0069A54C < 0`, copies `<= 256`-byte name to `0x00746024`, submits RPC (`0x439A28`), copies `36` bytes from `0x20746000` to `$a0`, and returns `*(int32_t*)0x20746140`.


---

## 19. Frame Flush, GS Texture Block, Skinning & Model Dispatch (DECOMP-CE)

Observed in `sub_003B81A8`, `sub_003B9758`, `sub_003B4E80`, `sub_003B4818`, `sub_003B5508`, `sub_003BA2A0`, `sub_003B3820`.

- **Active Draw-List Unlink (`sub_003B81A8`)**: Unlinks all nodes from `RenderCtx+0x6868` (`+0x687C` head, slot `2`) via `sub_003AF9F8`, clearing `node+0x20` bits `0x111` and setting `0x10`, then resets `RenderCtx+0x709C = RenderCtx+0x28`.
- **GS Texture/Mip Register Block (`sub_003B9758`)**: Writes a 6-QW `A+D` GIFtag (`0x1000000000008005`, regs `0x06` `TEX0_1`, `0x14` `TEX1_1`, `0x16` `TEX2_1`, `0x34` `MIPTBP1_1`, `0x36` `MIPTBP2_1`) from optional template `$a1` and overlay `$a2`, computing TBP/TBW/CSA shifts via `sub_003AD018`.
- **Frame Flush & Pending Texture Upload (`sub_003B3820`)**: Emits `VIF FLUSH` (`0x11000000`), calls `sub_003B81A8` and `sub_003B85B8`, flushes `RenderCtx+0x70A4` texture/CLUT uploads via `sub_003B9758` / `sub_003B99B8`, and appends `FINISH` (`0x3F`) + `TEX0_1` (`0x06`, `0x00720C70`) DMA `CNT`+`CALL` blocks.
- **Channel Weight Sampler (`sub_003B4E80`)**: Samples up to `5` morph/anim channels (`0x44`-byte stride at `$a2`, results at `+0xF0` and counts at `+0x134`), evaluating `sub_003B9D38` for masked channels.
- **Object VU1 Matrix/Light Setup (`sub_003B4818`)**: Uploads matrix/light setup via `sub_003BD498`/`sub_003BD2F0`/`sub_003BD538`/`sub_003BD648` and SPR (`0x3AFD98`/`0x3B4290`), then dispatches mesh groups to `sub_003B5048`.
- **Model-Draw Dispatcher (`sub_003B5508`)**: Iterates mesh items (`0x10` stride), resolves `sub_003BBB50`, and routes to `sub_003B5900`, `sub_003B7220`, `sub_003B7460`, `sub_003B6FE0`, or inline DMA `CALL` + `sub_003B57C0`/`sub_003B5890`.
- **SPR/VU0 Skinning (`sub_003BA2A0`)**: DMAs bone/vertex buffers into SPR (`0x70000000`/`0x70000800`/`0x70001010`), executes VU0 microprograms `0xF0`, `0x88`, `0xCD0`, and DMAs output back via Ch8 (`0x1000D000`).

---

## 20. ViewData Init, DrawList Callbacks, Scene Pass & Anim Sampling (DECOMP-CF)

Observed in `sub_003B7CB0`, `sub_003B4088`, `sub_003B85B8`, `sub_003B45E8`, `sub_003B94A8`/`sub_003B9708`, `sub_003B9088`/`sub_003B92E0`, `sub_003B8FE0`, `sub_003ABAA8`, `sub_003A8360`, and leaf accessors (`3B1248`, `3B76F8`, `3BAF58`, `3B3C60`, `3A9660`/`3A9670`, `3A9430`/`3A9438`, `3A6D00`/`3A6D18`, `3AD050`, `3B8F58`, `3A8340`, `3B9E20`).

- **ViewData (`sub_003B7CB0` / `sub_003B4088` / `sub_003B76F8`)**:
  - `+0x0010`: `uint32_t` status/flag (cleared to `0`)
  - `+0x0014..0x0813`: two `256`-entry `uint32_t` tables (`+0x0014` and `+0x0414`)
  - `+0x0814`: `RenderCtx*`
  - `+0x0818`: `uint32_t` camera handle (`*(cam + 0x0C)`)
  - `+0x081C`: `PktBufState*` (from `sub_003B40F8`)
  - `+0x0824` / `+0x0828`: active camera/view node (`sub_003B7A00`)
  - `+0x0830`: `uint32_t` scene/pass parameter (`sub_003B76F8`)
  - `+0x0834`: `uint32_t` default clip/view descriptor (`sub_003B45E8`)
  - `+0x0838..0x0E57`: `98` (`0x62`) `16`-byte zeroed slots
- **DrawList 32-Byte Callback Nodes (`sub_003B94A8` / `sub_003B9708`)**:
  - Allocated from `PktBufState->tail (-= 0x20)`, linked into `DrawList` tail (`+0x0C`), incrementing `+0x24`.
  - `+0x0C = 0x003B9088` (dispatches `sub_003B9310(a0, *(node + 0x10))`) or `+0x0C = 0x003B92E0` (invokes `jalr *(node + 0x10)(*(node + 0x14), *(node + 0x18))`).
- **DrawList Node Commit (`sub_003B85B8`)**: Walks `RenderCtx+0x6868`, updates `node+0x24` offset, dispatches `sub_003ADEC0` (new, `+0x70C0`) or `sub_003AE708` (relocated, `+0x70C4`).
- **Scene/Model Pass (`sub_003B45E8`)**: Iterates mesh groups (`0x3B4E80`, `0x3B4818`, `0x3B4A60`), syncs DMAC Ch8 (`0x1000D000` via `0x413280`), returns `0` on any draw hit else `0xD`.
- **Sorted Item Lookup (`sub_003A8360`)**: Binary search over `16`-byte entries (`*(a0+8)`, count `*(a0+4) & 0xFFFFFF`) using `0x42C44C`.


## 21. Model-Draw Dispatchers, Mesh Group Pass, DrawList Node Alloc & VU0 Math (DECOMP-CG)

Observed in `sub_003B5048`, `sub_003B69D8`, `sub_003B4A60`, `sub_003B3E28`, `sub_003B8740`/`sub_003B8780`, `sub_003B0AA8`, `sub_003AF2D8`, `sub_003A7620`, `sub_003BD450`, `sub_003BE618`, and `sub_003BAF88`.

- **Model-Draw Dispatcher (`sub_003B5048`)**: Iterates mesh items `[$a1..$a2)`. When `$t0 == 2`, runs frustum cull (`3A9300` -> `3BD690` -> `3BA898`). Allocates draw node via `3BBB50`, then dispatches by `(flags & 3) && *(t2+0xAC)` -> `3B5900`, `*(node+0x14) != 0` -> `3B6508` (`$t0==1`) or `3B6740`, `$t0==1` -> inline `3A9270/3A9280/3B8840/3B57C0/3B5890/3B8898`, else `3B62C0`.
- **Batched Rigid-Mesh VU1 Builder (`sub_003B69D8`)**: Processes mesh nodes in batches of up to 16, builds transformed matrices in scratchpad (`3BA090`, `3BA2A0`), emits `3BA7D8` UNPACK pairs + `0x60000000` DMA RET, then emits `3AFD98` (`0x6C038000`) + `3BD2E0` + `3B5890` (`0x60028003`, `0x190`/`0x3F4`/`0x3F2`, `0x15`) bracketed by `sub_003B8740`/`sub_003B8780`.
- **Mesh-Group Pass (`sub_003B4A60`)**: Optional `3BA908` visibility test when `$a2 == 2`. Iterates sub-meshes; for `flag & 0x08` transforms bone+bbox via `vcallms 0` (`$vf4..$vf11`) and dispatches `3B5508`, else dispatches `3B5368`, uploading `3BD498`/`3BD2F0`/`3BD538`/`3BD648`/`3B4290` (`0x6C108000`, `0x190`/`0x3E1`/`0x3D2`).
- **Sorted Draw-Item Grouping (`sub_003B3E28`)**: Walks sorted list (`3B8FE0`), groups adjacent items with matching sort key (`+0x20`, `$f20`) and group id (`+0x2C`) via `3B3680`/`3B3740`/`3AFB90`/`3B89D0`/`3B3D98`.
- **DrawList Node Helpers (`sub_003B8740` / `sub_003B8780`)**: `3B8740` allocates a 16-byte node from `PktBufState->tail (-= 0x10)`, links it into `DrawList+0x0C`/`+0x20`, and increments `+0x24`; `3B8780` stores end packet ptr at `curNode+0x0C` and advances `PktBufState->cursor` to `$a1 + 0x10`.
- **VU0 & Scalar Math (`sub_003BD450`, `sub_003BE618`, `sub_003BAF88`)**: 3D cross product (`vopmula`/`vopmsub`), 4x4 matrix * (point + direction) pair, and scalar float lerp.

---

## 22. Sprite/Skin Mesh Builders, Bucket Sort, OBB Frustum Cull & Accessors (DECOMP-CH)

Observed in `sub_003B62C0`, `sub_003BA908`, `sub_003AE900`, `sub_003AEA18`, `sub_003B8A18`, `sub_003AEEA8`, `sub_003AF088`, `sub_003AF1B8`, `sub_003A7898`, `sub_003BD3F8`, `sub_003B2420`, `sub_003BFE60`, and accessors (`3A7028`, `3A7040`, `3A7088`, `3A70C0`, `3A9300`).

- **Skin/Mesh Batch Builder (`sub_003B62C0`)**: Iterates sub-meshes (`$s4..$fp`, `0x10` stride) after `3A9270`/`3A9280`/`3B8840`, optionally runs `3BD690` + `3BA898` frustum culling, emits `0x50000000` DMA `CALL` + `3AFD98` (`0x6C038000`) + `3BD2E0` + `0x60028003` (`0x190`/`0x3F4`/`0x3F2`, `0x15`) + per-bone `0x50000000` `CALL` tags, and commits via `3B8898`.
- **Bone-OBB Frustum Test (`sub_003BA908`)**: Transforms up to `*(uint16_t*)($a2+0x0E)` bone/box pairs (`0x40` stride at `*(a2+4)`) via VU0, computes world-space AABB center/half-extents, transforms by `*$a3` onto stack, and calls `sub_003BA898`.
- **Sprite/Quad Packet Emitter (`sub_003AE900`, `sub_003AEA18`)**: `3AE900` allocates 2 QWs (`3B3CE0`), packs clamped RGBA (`ppach`/`ppacb`), computes FPU UV/screen coords (`0x007205A8`/`0x007205AC`), emits packet via `3AEA18` (`0x60000000` DMA `RET` + `0x6C008000` VIF UNPACK + `0x14000001`), and commits via `3B3D88`.
- **256-Bucket Radix/Hash Insert (`sub_003B8A18`)**: Links nodes (`$a1`, next at `+0x04`) into 256 `16`-byte bucket tails (`$a0 + (((word0 >> $a2) & 0xFF) << 4) + 0x0C`).
- **64-Byte Entry Copy & Slot Ref-Increment (`sub_003AEEA8`, `sub_003AF088`)**: `3AEEA8` copies `(*(a0+0x18)->+0x34 & 0xFFFFFF)` `64`-byte blocks from `*(a0+0x10)->+0x10` to `$a1`; `3AF088` increments `uint16_t` `+0x08` on active (`+0x0C != 0`) slots in `($a0+0x10)->+0x08`.
- **Anim/Object Accessors & Math (`sub_003A7028`, `sub_003A7040`, `sub_003A7088`, `sub_003A70C0`, `sub_003A7898`, `sub_003A9300`, `sub_003AF1B8`, `sub_003BD3F8`)**: `3A7028`..`3A70C0` query `($a0+8)` table entries/counts via `3A8360`; `3A7898` indexes 12-byte track entries after `3A7620`; `3AF1B8` resolves `*(3A9430(3A9660(a0)))`; `3BD3F8` performs VU0 vec4 lerp.

---

## 23. Split Pieces, Sub-Entries, VIF/DMA Packet & Matrix Helpers (DECOMP-CJ)

Observed in `sub_003B1268` (sub-entry of `sub_003B1248`), `sub_003B88B8` (sub-entry of `sub_003B8898`), `sub_003AB9F0` (sub-entry of `sub_003AB980`), `sub_003BA680`/`sub_003BA71C` (split-piece loop), `sub_003B5368`, `sub_003AEF08`, `sub_003AB830`, `sub_003BAC40`, `sub_003AD018`, `sub_003BD238`, `sub_003ACFB8`, `sub_003AD09C`, `sub_003B2448`, `sub_003AFE00`, `sub_003BFED8`, `sub_003BBB10`, `sub_003B76E8`, `sub_003C0A48`, `sub_003A7650`, `sub_003B11D0`, `sub_003BAF48`/`sub_003BAF68`, `sub_003A87D8`.

- **Skinned/Instanced VU1 Packet Builder (`sub_003B1268`, `sub_003B2448`)**: Builds multi-pass DMA/VIF1 packets (`0x1000000B` CNT, `0x6C098000` UNPACK at `0x190`/`0x3F7`/`0x3F4`, `3BDC40` + `3BD2F0` header upload, optional `0x30000004` REF chunks in batches of up to 20, `0x6C028000` + `0x60028002` at `0x190`/`0x3F4`/`0x3F3`, and `0x65008050`/`0x66008050` index/flag streams). `3B2448` rotates `$t1..$t3` and tail-calls `3B1268`.
- **128-Byte Aligned DrawList Node Alloc (`sub_003B88B8`)**: Sub-entry of `3B8898` that allocates a 32-byte node from `PktBufState->tail (-= 0x20)`, aligns `PktBufState->writePtr` to 128 bytes (`& 0x0FFFFFFF`), sets callback `0x003B9270`, and links into `RenderCtx+0x0C`/`+0x24`.
- **Mesh/Skin Dispatch & Bone Transform Loops (`sub_003B5368`, `sub_003AEF08`, `sub_003AB830`)**: `3B5368` iterates `[$a1..$a2)` with `3BBB50`, branching to `3B5900`, `3B6CF0`, or `3B69D8`; `3AEF08` transforms active `64`-byte bone matrices via `vcallms 0` (`$vf4..$vf11`); `3AB830` iterates `uint16_t` index list (`0xFFFF` sentinel) calling `3ACA70` and `3BD338` for non-`$f20` channels.
- **VIF1 Tag Scanner (`sub_003BA680` / `sub_003BA71C`)**: Split-piece loop over DMA/VIF1 buffer (`*(a0+0) .. +(a0+4)*16`) patching `0x60` UNPACK tags and stepping over `0x20`/`0x30`/VIF commands via jump table `0x0072131C`.
- **Dispatch Tables & Leaf Helpers (`3AD018`, `3BD238`, `3ACFB8`, `3BAC40`, `3C0A48`, `3B11D0`, `3AB9F0`)**: Jump-table dispatchers at `0x0072037C` (`<45`), `0x00721618` (`<36`), `0x007202C8` (`<45`); `3BAC40` builds two 4x4 FPU matrices (`$t2`, `$t3`) using `0x007213E0`/`0x007213E4`; `3C0A48` computes VU0 squared xyz distance; `3B11D0` packs 64-bit `(f12<<32)|(a3<<24)|(a2<<16)|(a1<<8)|a0`.

- **DECOMP-CK Batch 16 (`3B7820`, `3BAE50`, `3BD398`, `3C6E30`, `3B7840`, `3B7890`, `3C2160`, `3A8960`, `3BFDE8`, `3B7708`, `3C6F78`, `3BE5F8`, `3BAF98`, `3BB838`, `3BD3C8`, `3AFB28`, `3B78B0`, `3A9468`, `3A9478`)**: `3B7820`/`3B7840`/`3B7890`/`3B78B0` tail-jump via `*($a0+0x81C)` to `3B88B8`/`3B8920`; `3BD398`/`3BD3C8` are VU0 4D add/neg; `3C6E30`/`3C6F78` read `0x746D18`/`0x746D20`; `3AFB28` inserts into intrusive doubly-linked list (`+4`/`+8`); `3BAE50` computes 4-row frustum matrix + vectors via `3BD450`/`3BD498`/`3BD690`; `3BAF98` builds full projection/clip/GS-tag packet into `3B3CE0` buffer and submits via `3B3D88`.
- **DECOMP-CN Batch 17 (`3BEE20`, `3BE9F0`, `3C17B0`, `3BD270`, `3AF3B8`, `3BAF78`, `3B7DF0`)**: `3BEE20` (ray/sphere-triangle hit test, `jalr *($a3+0x10)` + `3C17B0`) and `3BE9F0` (sphere-triangle hit test, `jalr *($a3+0x10)` + `3C0A48`/`3BD2E0`/`3BD398`); `3C17B0` (3D segment-segment closest-point / squared-distance with 9-case jump table `0x007217A0`); `3BD270` (multi-entry 16-byte DMA/VIF header QW writer with sub-entries `3BD280..3BD2A0`); `3AF3B8` (handle-to-slot setter via `3A9670`/`3A9660`/`3A9478`/`3A9468`); `3BAF78` (`$a0 + 0x3A0` accessor); `3B7DF0` (list flush + node alloc/link via `3B7EC0`/`3B7E88`/`3AFA28`, updating `$a0+0x709C`).
- **DECOMP-CO Batch 18 (`3AFF08`, `3AFFA0`, `3B3C58`, `3B4010`, `3B8288`, `3B93D8`, `3B8A98`, `3A74F0`, `3AF278`, `3A8858`, `3A8C90`, `3A6D68`, `3C3E00`, `3A83A0`, `3B85FC`, `3BD2B0`, `3B9B00`, `3B9AA0`, `3B0A48`, `3ACFA0`, `3A8C60`, `3AFAE8`, `3B50B8`, `3AFB40`)**: `3AFF08` (36-case jump table `0x007208C0`), `3AFFA0` (calls `3AFF08` then tail-jumps `3AFE58`), `3B4010` (resets `RenderCtx+0x70B4..+0x70C4`, calls `3BE5F8`/`3B8288`/`3B93D8`), `3B8288` (coalesces adjacent `DrawListNode`s matching mask `$a1` up to `$a2`), `3B93D8` (frame packet setup + `jalr *($s0+0x70A8)`), `3B8A98` (4-pass scratchpad `0x70000000`/`0x70002000` radix/bucket sort via `3B8A58`/`3B8A18`), `3B9B00` (6-case jump table `0x00721270`), `3B9AA0` (variable-stride table lookup), `3C3E00` (VU0 3x4 matrix * vec3), `3AFAE8` (4-slot link init + zero `+0x20..+0x30`), `3AFB40` (intrusive list splice `+4/+8`), `3BD2B0` (`$t4=0x58` tail to `3BD270`), and sub-entries `3A83A0`/`3B85FC`/`3B50B8`.

- **DECOMP-CP Batch 19 (`3B42D0`, `3BA5F8`, `3BAC00`, `3BD368`, `3C4008`, `3C41E8`, `3B9B50`, `3AD070`, `3B9B88`, `3ADCD8`, `3ADD08`, `3AE868`, `3B6FE0`, `3B9C20`, `3AD608`)**: `3B42D0` (mesh/primitive DMA packet builder over nested lists, calls `3BA090`/`3BA680`/`3BA7D8`), `3BA5F8` (VU0 centroid sum over `$t5` vec3s scaled by `0x721318 / count`), `3BAC00` (VU0 4x4 mat at `$a0+0x360` * vec4, returns `$vf4.x + $vf4.z` in `$f0`), `3BD368` (VU0 4x4 mat * vec4), `3C4008`/`3C41E8` (OBB/AABB overlap test + collision dispatch via `3BD338`/`3BD398`/`3BD3B0`/`3C3E00`/`3BD450`/`3C3D80`), `3B9B50` (multi-entry 16-byte alignment helper `*3/*4/(x/2)`), `3AD070` (45-case jump table `0x00720430` on `$a3`), `3B9B88` (vertex stream stride/offset sum), `3ADCD8` (linked-list head deref + tail-call `3AF9C8`), `3ADD08` (GS TEX0/CLAMP/etc. register packet builder), `3AE868` (0x30-byte zero-init via `42B320` + clear `+0..+0xC`), `3B6FE0` (skin/bone DMA packet builder calling `3A9270`/`3A9280`/`3B8840`/`3BD690`/`3BA898`/`3AFD98`/`3BD2E0`/`3B8898`), `3B9C20` (table offset lookup `a0 + lhu(a0+0xC) + lw(a0+8)`), `3AD608` (material/GS texture state packet builder with `3ADCA8`/`3B9AA0`/`3B9B00`/`3B9B88`/`3ACFB8`/`3AD070`/`3ACFA0`).

- **DECOMP-CQ Batch 20 (`3ADCA8`, `3AE808`, `3BD2A8`, `3A7668`, `3A7680`, `3A7860`, `3B6CF0`, `3A6CF8`, `3ACFF8`, `3B5574`, `3A7390`, `3A73E8`, `3A7498`, `3A9718`, `3AEFD0`, `3AEEC8`, `3BA928`, `3A98E0`, `3A8B70`, `3A94B8`, `3A70A0`, `3A70D0`, `3A9570`, `3A9140`, `3B81D4`, `3AF0A4`, `3A9428`, `3B4AC8`, `3B9098`, `3B3E74`, `3A95E0`, `3B97E8`, `3B3884`, `3B3C48`, `3BDAD8`, `3AC3F8`)**: `3B6CF0` (188-insn batched skinned/DMA-VIF1 emitter calling `3A9270`/`3A9280`/`3B3D80`/`3BA090`/`3BA2A0`/`3BA5F8`/`3BD368`/`3BAC00`/`3BA7D8`/`3B57C0`/`3B5890`/`3B8898`/`3B8840`), `3A7390`/`3A73E8`/`3A7498`/`3A7668`/`3A7680`/`3A7860` (object/stream tag validation & cleanup calling `42B0D8`/`3A7620`/`3A7650`/`3A85E0`/`3AEB90`/`3AED00`/`3A8490`), `3AE808` (0x128-byte zero-init via `42B320` + clear `+0..+0xC`), `3ADCA8` (linked-node tail-call `3AF9C8`), `3AEFD0` (16-byte + float copy with `0x720640`), `3A9718` (relative-offset pointer fixup), `3BD2A8` (`$t4=0x54` tail to `3BD270`), `3ACFF8` (`v0=8`), 1-insn `jr $ra` stubs (`3A6CF8`/`3A98E0`/`3A8B70`/`3A94B8`/`3A9570`/`3A9140`/`3A9428`/`3A95E0`/`3BDAD8`), and 14 sub-entries (`3B5574`, `3AEEC8`, `3BA928`, `3A70A0`, `3A70D0`, `3B81D4`, `3AF0A4`, `3B4AC8`, `3B9098`, `3B3E74`, `3B97E8`, `3B3884`, `3B3C48`, `3AC3F8`).
- **DECOMP-CR Batch 21 (`3B8920`, `3BA6C8`, `3BD280`, `3BA724`, `3B4AFC`, `3B0B78`, `3AB87C`, `3A7508`, `3B53DC`, `3B3890`, `3B3E7C`, `3A74A8`, `3B131C`, `3AFF44`, `3C6F88`)**: `3B8920` (13-insn leaf in `3B8898` setting `PktBufState` REF tag `0x30000000`), `3B0B78` (25-insn DMA/VIF1 packet builder calling `3AFDD8` with `0x6400000000008001` / `0x00F55510`), `3AFF44` (multi-entry `$a2` dispatch tail-jumping to `3AFE58`), `3C6F88` (62-insn init/table clear of `0x746218` x64 `44`-byte slots calling `3C6DA0`/`3C6E40`/`3C6EE0` and checking `3CDC50`/`3CC100`/`3CD418`), leaf sub-entries (`3BD280`, `3BA724`, `3A74A8`), and 8 resumable sub-entry wrappers (`3BA6C8`, `3B4AFC`, `3AB87C`, `3A7508`, `3B53DC`, `3B3890`, `3B3E7C`, `3B131C`).

- **DECOMP-CS Batch 22 (`3BA72C`, `3BA6F4`, `3BD288`, `3B3E8C`, `3B38A4`, `3B1338`, `3B4324`)**: 7 resumable sub-entry wrappers delegating to their already-decompiled parent switch-dispatch entries (`3BA71C`, `3BA680`, `3BD270`, `3B3E28`, `3B3820`, `3B1268`, `3B42D0`); `3BA72C` uses an internal `jr $t5` jump table (not a `jalr`, no `noCheck`).

- **DECOMP-CV Batch 23 (`3BD290`, `3BA718`, `3B38B8`, `3B8A24`, `3B7E14`, `3BA60C`)**: 6 resumable sub-entry wrappers delegating to their already-decompiled parent switch-dispatch entries (`3BD270`, `3BA680`, `3B3820`, `3B8A18`, `3B7DF0`, `3BA5F8`); all 6 parent switches already contained matching `case` labels.


- **DECOMP-CW Batch 24 (`3BD298`, `3C72E8`, `3C7FD0`)**: `3BD298` (resumable sub-entry wrapper delegating to `sub_003BD270` at `case 0x003BD298u`, sets `$t4 = 0x48` for 16-byte DMA/VIF header QW); `3C72E8` (driver open/create channel: validates `driverIdx` in `[0, 7]`, clamps params 1..4 & 6 to `[0, 0xFFFF]`, `[0, 0x7F]`, `[0, 0x1FFFF]`, `[0, 0x80]`, `[0, 0x80]`, wraps angle param5 into `[0, 360)`, invokes `drv->open` at `*(0x0069C0B8 + idx*4) + 0x00`, validates returned handle in `[0, 63]`, and stores `drv` into `0x00746218 + handle * 44`); `3C7FD0` (driver control/enable: validates `driverIdx` in `[0, 7]`, clamps `enableFlag` to `[0, 1]`, and invokes `drv->ctrl` at `*(0x0069C0B8 + idx*4) + 0x0C`).
- **DECOMP-CZ Batch 25 (`3B6508`, `3B6740`, `3B3D20`, `3B3D50`, `3BD470`, `3C22F0`, `3C0C00`, `3B8A58`, `3AE708`, `3B7220`, `3B0C50`, `3B1208`, `3AC4B0`, `3A6D88`, `3A7168`, `3A7238`, `3A6DA0`, `3A7250`, `3C28D8`, `3C18D4`, `3B8ADC`, `3A7C20`, `3A7D70`, `3AEF28`)**: `3A6D88` (leaf: reads `*(a0+8)+0x14` masked to 24 bits); `3A6DA0` (leaf: `*( *(a0+8)+0x18 ) + (a1<<4)`); `3A7168` (tail-jumps to `3A8360` with `*(a0+8)+0x20`); `3A7238` (leaf: reads `*(a0+8)+0x34` masked to 24 bits); `3A7250` (leaf: `*( *(a0+8)+0x38 ) + (a1<<4)`); `3AE708` (rearranges args `$a0=$a1, $a1=$a2, $a2=$a3, $a3=*(a0+8)` and tail-jumps to `3AD4E0`); `3B1208` (packs `($f13<<32)|$f12` into 64-bit `$v0`); `3B3D20` (calls `3B3D80` and 128-byte-aligns + 28-bit-masks `$v0`); `3B3D50` (128-byte-aligns `$a1`, sets `0x30000000` REF tag, tail-jumps to `3B3D88`); `3B8A58` (bucket-links list `$a1` into `$a0` using `(~*node >> a2) & 0xFF`); `3BD470` (VU0 3D dot product `$vf4.$vf5` -> `$v0`/`$f0`); `3C22F0` (sphere-segment squared distance <= `(r0+r1)^2` via `3C0C00`); `3C28D8` (capsule/sphere vs triangle/edge test via `3C0C00`/`3BD398`/`3BD498`/`3BD3B0`/`3BD470`); `3AC4B0` (VU0 quaternion slerp/nlerp via `41D628`/`41D490` and `vrsqrt`); `3B0C50` (5-qword GIF A+D packet builder calling `3AFDD8` + `$v0+0x50`); `3C0C00` (point-to-segment squared distance + optional clamped parameter `$a3` via `3BD3B0`/`3BD470`/`3BD338`); `3B6508`/`3B6740`/`3B7220` (skinned mesh/bone-palette DMA-VIF1 packet builders calling `3A9270`/`3A9280`/`3BD368`/`3BAC00`/`3B8840`/`3AFD98`/`3BD2E0`/`3B8898`, with `3B6740` adding frustum/vis test `3BD690`/`3BA898` and `3B7220` reading stack vertex-base arg); plus 5 resumable sub-entry wrappers (`3C18D4`->`3C17B0`, `3B8ADC`->`3B8A98`, `3A7C20`->`3A7BB8`, `3A7D70`->`3A7D08`, `3AEF28`->`3AEF08`).

- **DECOMP-DA Batch 26 (`3B9D38`, `3B9C48`, `3B9D78`, `3B9E60`, `3BA0C8`, `3A9760`, `3A9770`, `3A9490`, `3B5900`, `3B7460`, plus dispatch wrappers `3B8B0C`, `3A7C2C`, `3AEF30`)**:
  - `3A9490`: 1-insn `jr $ra` no-op stub.
  - `3A9760`: leaf accessor returning `*(*(a0+0x08)+0x08)`.
  - `3A9770`: leaf accessor returning `*(*(a0+0x08)+0x08) + ((*( *(a0+0x08)+0x04 ) & 0xFFFFFF) << 4)` (plus internal pointer-relocation sub-loops at `3A9790`/`3A9808`).
  - `3B9C48`: binary search over sorted float array `$a0[0..$a1)` for `$f12` (returning index in `$v0`), with sub-entry `3B9CB0` evaluating piecewise-linear float keyframes (`f0*t + f1` or endpoint fallback).
  - `3B9D38`: reads `*(*(a0+0x08))`; if non-null tail-jumps to `3B9CB0` (`sub_003B9C48`), else returns `*(float*)(*a0)`.
  - `3B9D78`: searches keyframe table via `3B9C48` and evaluates 128-bit VU0 linear interpolation (`vmulax`+`vmaddw` over `2*vec4` pair) into `*$a1` (with endpoint fallback at `a0+0x00`/`a0+0x10`).
  - `3B9E60`: iterates `(*(a0+0x08)+0x08)` entries (`0x10` stride) calling `3B9D78` to evaluate keyframed vec4 tracks into `$a1`.
  - `3BA0C8`: builds/evaluates bone-palette animation tracks into `$a1` (calling `3B9E60` or `3B9FA8`/`3B9ED8`/`3BA010` depending on `$t2 & 3`, then finalizing via `3BE5F8`).
  - `3B7460`: frustum-culled mesh/skin DMA-VIF1 builder (`3A9270`/`3A9280`, `3BD690`/`3BA898` cull, `3BAC00` sort key, `3B8840`/`3AFD98`/`3BD2E0`/`3B8898` with `0x50000000` CALL + `0x60028003`/`0x14000001` tags and per-bone `0x50000000` CALLs).
  - `3B5900`: batched mesh/skin/cull DMA-VIF1 packet builder (`$sp -= 0xF10`). Stack layout: `0x000..0x13F` = 16-entry `0x14`-byte batch item buffer; `0x140`/`0x160` = primary/secondary `3BA0C8`/`3BA090` track buffers; `0x180`/`0x190` = frustum/centroid scratch (`3BD368`/`3BA5F8`/`3BD690`/`3BA898`/`3BAC00`); `0x1C0..0x7FF` & `0x800..0xE3F` = bone-matrix A/B arrays (`0x14` stride); `0xE40..0xF0F` = spilled args/state (`extraPass`, `cullMode`, `meshFlags`, `curDrawNode`, `batchRefSlot`, saved `$s0-$s7/$fp/$ra`). Emits `3B8840`/`3B8898` (or `3B8740`/`3B8780` when `extraPass==0`) with `0x30000000` REF + `0x65008003` VIF UNPACK + `0x60000000` RET tags and `3B57C0`/`3B5890`/`3BA2A0`/`3BA7D8`.
  - `3B8B0C` (`-> 3B8A98`), `3A7C2C` (`-> 3A7BB8`), `3AEF30` (`-> 3AEF08`): resumable dispatch-label wrappers routed into their parent decomp's `switch (ctx->pc)`.

- **DECOMP-DB Batch 27 (`3A0028`, `3A0038`, `3A02D8`, `3A0328`, `3A05D0`, `3A0670`, `3A57F4`, `3A58E4`, `3A5988`, `3A59C0`, `3A5AD0`, `3A5EA8`, `3A5F8C`, `3A6070`, `3A60C8`, `3A61A4`, `3A6224`, `3A62AC`, `3A63D0`, `3A640C`, `3A66F4`, `3A6700`, `3A6A90`, `3A6AF0`, `3A6B24`)**:
  - `3A0028`: zeroes 32 bytes at `a0+0xE0..0xFF`.
  - `3A0038`: computes inertia/angular-momentum ellipsoid basis vectors into `a0+0x20..0x8F` via 5 calls to `0x44BD80`.
  - `3A02D8`: copies 3D vector `a0+0x0` via `0x359E74` into `a1`, and `a0+0x10` (with `w=1.0f`) into `a1+0x30`.
  - `3A0328`: integrates/clamps linear & angular velocity (`a0+0xA0..0xFF`), updates local/world transform matrices via `0x441F40`/`0x3A02D8`/`0x441F70`, and writes transformed velocity to `a0+0xD0`.
  - `3A05D0`: VU0 Euler-step integration of position (`a0+0x10`) and normalized quaternion (`a0+0x00`) from linear/angular velocities (`a0+0xB0`/`0xD0`) and `dt` (`$f12`).
  - `3A0670`: target-seeking velocity projection step adding `$a1` (or projected onto `a2 - *(a0+0x10)`) to `a0+0xE0`.
  - `3A57F4`: zeroes 42-byte header (`a0+0x0..0x29`) + 16-iter delay loop.
  - `3A58E4`: copies 42-byte header + `0x30` qword + 16×64-byte entries (`0x40..0x43F`) from `$a1` to `$a0`.
  - `3A5988`: appends a 64-byte entry (`$a1[0..31]`, `$a2[0..31]`) at `a0 + 0x40 + count*0x40` and increments `*(a0+0x24)`.
  - `3A59C0`: resolves 32-byte key via `0x271764`/`0x3714A0` and searches `a0+0x40` table for matching entry, returning `entry+0x60` (or `a0`).
  - `3A5AD0`: initializes `0x6B7428` vtable object (`0x20AE70`, `0x4432CC`, `0x3A58E4`, `0x3A61A4`, `0x3A63D0`, `0x3A66F4`), stores global ptr `0x69A070`.
  - `3A5EA8`: lazily creates/caches `a0+0x300` resource via `0x1D2814`/`0x246F88`/`0x1D27D0` selected by `*(a0+0x58)`.
  - `3A5F8C`: returns `$f12 * *(float*)0x71FE24u`.
  - `3A6070`: sets `*a0 = 0x006A2E98`.
  - `3A60C8`: maps `*(a0+0x60)/(*(a0+0x64))` against thresholds `0x71FED0..0x71FEE4` and tail-jumps to `0x3A61BC`.
  - `3A61A4`: zeroes 5 dwords at `a0+0x00..0x10`.
  - `3A6224`: advances timer `a0+0x8`/`0xC` when `*(a0+4)==1`, stepping slot `a0+0x10` across `0x69A080` table up to 9.
  - `3A62AC`: returns `0 < *(uint32_t*)(a0+4)`.
  - `3A63D0`: resets timer/state struct `a0+0x0..0xC` (`*(float*)(a0+8) = *(float*)0x71FEF8`).
  - `3A640C`: advances timed effect/interpolator at `a0` (`a0+0xC` active flag), firing `0x35AB88`/`0x165518`/`0x36252C`/`0x36F548` across thresholds `0x71FF50..0x71FF64`.
  - `3A66F4`: zeroes `*(u8*)(a0+4)` and `*(u32*)(a0+0)`.
  - `3A6700`: advances timed effect/interpolator at `a0` (`a0+0x4` active flag), firing `0x35AB88`/`0x165518`/`0x36252C` across thresholds `0x72000C..0x72001C`.
  - `3A6A90`: returns `*(uint8_t*)(a0+4)`.
  - `3A6AF0`: decrements/clamps global counter `0x69A074` into `[0, 60]`.
  - `3A6B24`: returns `*(int32_t*)0x69A074 < 1`.
