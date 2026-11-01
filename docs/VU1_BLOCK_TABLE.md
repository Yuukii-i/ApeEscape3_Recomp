# VU1 hot-block table: how it is built and rebuilt

The hot blocks (`generated/vu1_hot_blocks.cpp`) are compiled from timing records of the exact interpreter: one record per (pc, entry timing hash).
Everything is regenerable; nothing in the file is hand-edited.

## Hash and the XGKICK-active token
The runtime timing hash (`blkStateScan` in `ps2_vu1_core.cpp`) is `H = 0x1234ABCD; for each token: H = mix(H ^ mix(token))`. Until 2026-11-01 a running XGKICK transfer
added a final `x` token, so a block recorded with a transfer in flight had a different key and could never be reached by the optimised blocks (they decline while a
transfer runs). Now (`PS2X_VU1_XG_HOT`, default on, `=0` restores the old behaviour) the hash ignores the transfer, and two block families share the keys:

| family | symbol | form | used when |
|---|---|---|---|
| fast | `vuH_N`, `vu1HotLookup` | all patches (loop fusion, ADV, RG, NR); declines (`return -1`) if a transfer is running | no transfer running |
| transfer-aware | `vuX_N`, `vu1HotLookupXg` | stages xg / lean / inline / inline2 only; every cycle steps the transfer (`op.xgProgress`) | a transfer is running |

The dispatcher keeps one slot cache per family (`s_hotSlot`, `s_hotSlotX`).

## Rebuild loop (about 10 minutes, no gameplay)
1. Record blocks over the corpus with the interpreter (4 s for 30k runs):
   `PS2X_VU1_NATIVE=0 PS2X_VU_BLK=1 PS2X_VU1_REPLAY=1 PS2X_VU1_REPLAY_REPS=1` -> `logs/vublk2_u1_<image>.txt` (also `PS2X_VU1_XG_HOT` default on, so new dumps are already transfer-free).
2. Merge dumps, recompute every hash from the token text, drop the transfer token, dedupe:
   `python tools/vu1gen/hotgen_norm.py logs/hotgen_blocks_xl.txt logs/vublk2_u1_<image>.txt <older dumps...>` (the first dump wins; every hash is verified against its tokens).
3. Generate both families and assemble the file:
   `python tools/vu1gen/regen_hot.py logs/hotgen_blocks_xl.txt` (`--dry --work <dir>` writes to the work dir instead).
   Pipeline per family: `gen_vu1_hot.py` -> `patch_xg` -> `patch_lean` -> [`patch_loop`] -> `patch_inline` -> `patch_inline2` -> [`patch_adv` -> `patch_regs` -> `patch_nrm`] (brackets: fast family only).
4. `tools\build.bat` (only `vu1_hot_blocks.cpp` + the link), then check:
   `PS2X_VU1_REPLAY=1 PS2X_VU_BLK_CHECK=1` (hash tables exact: no `exit-hash MISMATCH` lines) and `PS2X_VU1_VERIFY=3`.

## Notes
- Records whose entry has a transfer token and records without are merged: they have equal timing (the transfer does not change VU pipeline timing outside XGKICK pairs).
- `next=` in a record is the observed successor pc and is not used by the generator, so duplicates that differ only there are not conflicts.
- The previous table (109 blocks, committed) is reproducible except for two tiny blocks (pc 0000/0028 variants) that the old pipeline left in the transfer-aware form.
