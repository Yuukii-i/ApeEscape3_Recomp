# Audio plan (roadmap phase 2) - 2026-11-14

## Facts
- The game's sound driver is its own IOP module sg2iopm1.irx (in DATA.BIN; copy at tools/iop/sg2iopm1.irx). EE side
  binds SIF RPC server 0x11223344 (sub_003FC100) and sends N x 16-byte command packets (sub_0036FC28 -> sub_003FBFB0,
  NOWAIT, send 0x747080, recv 0x74B080 size 0x1C0). The driver queues them (ring, 1024 slots), its dispatcher runs a
  36-entry op table that calls libsd (sceSdSetParam / sceSdSetSwitch (key on/off) / sceSdSetAddr / voice transfers ...),
  and every call returns a 448-byte status block (voice states, stream positions) - docs/SG2_SPEC.md (op descriptions
  partly inferred).
- Today: RPC.cpp:488+ answers 0x11223344 with an HLE tracker that returns a ZEROED status block -> the game never advances
  its streams (HYPOTHESES C16, C26, C61, C103, C313); no PCM is produced. ps2_audio.cpp (raylib, 4-sample player, VAG
  decode in ps2_audio_vag.cpp) is unreachable for this game.
- The IOP R3000A interpreter (PS2Recomp/ps2xIOP, ~6k lines) IS compiled and linked; it advances with EE cycles
  (EeScheduler accountCycles -> IopSubsystem::runEeCycles), loads relocatable IRX (iop_module_loader.cpp), and HLEs
  sysmem/loadcore/intrman/thbase/thsemap/thevent/sifman/sifcmd/stdio/sysclib/timrman/vblank(partial)/cdvdman imports.
  Missing: libsd as an IMPORT library (only an RPC forwarder exists), any SPU2 model, vblank callback delivery.

## Approach: run the real driver (LLE) + HLE libsd onto a new software SPU2
Exact driver logic and status block by construction; only the hardware side is new code.
- AU1: load sg2iopm1.irx into the IOP emulator when the game loads it (or at the point the EE binds 0x11223344), route
  SID 0x11223344 calls to the IOP's registered server (env PS2X_SG2_LLE=1, default off; the HLE tracker stays as fallback),
  implement the libsd imports the IRX uses as HLE functions writing into an SPU2 register/RAM model (2 MB SPU RAM, 2 cores x
  24 voices: pitch, ADSR1/2, volumes, SSA/LSAX, key on/off, ENDX; core: master/effect volumes, reverb params stored),
  plus voice/block transfers EE->SPU RAM. Log every libsd call at first; status block must become non-zero/plausible.
- AU2: SPU2 voice synthesis + mixer: ADPCM decode from SPU RAM with loop flags, pitch (4.12), ADSR envelopes, per-voice and
  master volumes, ENDX/NAX status reads, 48 kHz output into a host audio stream (raylib AudioStream already linked), output
  thread decoupled from frame rate. Reverb later (store params, bypass first).
- AU3: streams (BGM / movie / voice): file3 CID1 VAG/stream reads (RPC.cpp ~2083) and the driver's stream ring buffers; the
  status block's stream positions then drive the EE-side refill naturally.
- AU4: timing/latency tuning, volume levels, A/B against PCSX2 recordings (user ears).
Each step default-off until verified; CPU budget: the IOP interpreter + mixer must stay within ~1-2 ms/frame of a core
(they run on their own thread where possible).

## Stream path (AU3 investigation)
- **SG2 ops starting/feeding streams (`tools/iop/sg2iopm1.irx`):**
  - **VAG ADPCM streams** (`sound/stream/*.x`, BGM / ambience / voices / movie VAG):
    - `op 0x18` (`0x2A90`): configures per-voice stream slot (`0x8EC8 + core*864 + voice*36`) with SPU2 ring `SSA` (`sceSdSetAddr(SD_VA_SSA)`), ring size in SPU2 RAM, and IOP RAM ring address (`pkt[3] & 0x00FFFFFF`, e.g. `0x177B00`); sets `ADSR1=0x8080`, `ADSR2=0x808A`.
    - `op 0x02` (`0x0870`) / `op 0x1C` (`0x31C0`): voice key-on and envelope updates.
    - `op 0x23` (`0x39A8`) / 60 Hz heartbeat (`0x3BB4 -> 0x3CB8`): drains command ring (`0x3A44`), updates the 448-byte (`0x1C0`) status block at `0x8D38` (`0x00..0xBF`: 48 x `u32` `SD_VP_ENVX`, `0xC0..0x17F`: 48 x `u32` stream positions, `0x180`: `BlockTrans` offset), polls `sceSdGetAddr(SD_VA_NAX)` in `0x20B8`, and when `NAX` crosses `SSA + size/2` enqueues `sceSdVoiceTrans` (IOP RAM -> SPU2 RAM) via `0x16EC` / `0x24D4` / `0x04C0`.
  - **AutoDMA PCM streams** (if used):
    - `op 0x20` (`0x373C`): copies 2 KB (`0x800`) from IOP RAM buffer (`arg1`) to `0xE5A0`, sets `SD_P_BVOLL`/`SD_P_BVOLR`, calls `sceSdBlockTrans(ch, SD_TRANS_LOOP /*0x10*/, 0xE5A0, 0x800)` and `sceSdSetTransIntrHandler(ch, 0x34BC, 0)`.
    - `0x34BC` (interrupt callback): calls `sceSdBlockTransStatus(ch, 0)`, checks bit 24 (`0x01000000`) for the inactive 1 KB (`0x400`) half-buffer, and `memcpy`s the next `0x400` bytes from the IOP ring (`0xE58C`).
    - `op 0x1F` (`0x36A4`) / `op 0x21` (`0x386C`): clears `sceSdSetTransIntrHandler(ch, 0, 0)` and stops `sceSdBlockTrans(ch, SD_TRANS_STOP /*2*/, 0, 0)`.
- **How stream data reaches the driver:**
  - EE -> IOP SIF DMA (`sceSifSetDma` in `SIF.cpp`) already lands in `runtime->writeIopMemory` (IOP emulator RAM).
  - CID1 (`file3.irx`) op `0x07` (`Seek` / stream read, `RPC.cpp`): disassembly of `tools/iop/file3.irx` (`0x0C94..0x0CA4`, `0x1E60..0x1EA8`) confirms that `flags & 1` (`src + 0x1C`) selects **IOP RAM** destination (`memcpy` into IOP RAM without SIF DMA) vs EE RAM (`flags & 1 == 0`, SIF DMA). Previously `RPC.cpp` ignored `flags` and always wrote to `rdram + dstAddr` (EE RAM), so `sg2iopm1.irx` on the IOP interpreter never received stream data at `0x177B00`.
- **What the EE waits for:**
  - The 448-byte (`0x1C0`) status block (`0x8D38` -> `0x74B080` on EE). The EE stream class (`0x3F7780 -> 0x402888 -> 0x3FBE78`, C61) polls stream positions (`0x8DF8`, i.e. `+0xC0..+0x17F`) to issue the next CID1 op `0x07` read into IOP RAM.

## AU3b diagnosis (2026-11-14, route levels_run to shop, PARKED: user chose performance first)
- The driver has no timer: imports only libsd/sifcmd/stdio/sysclib/thbase; its status/NAX/ENVX update (0x3BB4 -> 0x3CB8,
  0x20B8) runs once per RPC (hb=tick=naxPoll=rpc count). Module base 0x10000; server returns 0x18D38 (= base+0x8D38).
- The 0x1C0 status block in IOP RAM is ALL ZERO at every reply (iopNZ=0) -> EE gets zeros (statusNonZero=0).
- sceSdGetParam(ENVX) ~48 per RPC but only ~1% return a changed value; sceSdGetAddr(NAX) stopped at 500 calls total
  (early, during the first stream) -> the driver stops polling stream voices -> no refills (VoiceTrans stays ~82-89).
- Next: why the driver writes zeros (does 0x3CB8 store ENVX results? read the IRX at 0x3CB8/0x20B8 in Ghidra or PCSX2),
  why NAX polling stops (voice state flag in the per-voice stream slot 0x8EC8+...), FMV death with LLE on breaks replays.
- Uncommitted->committed as diagnostics only (all under PS2X_SG2_LLE=1). IOP vblank delivery added (vb=0/0: unused by sg2).
