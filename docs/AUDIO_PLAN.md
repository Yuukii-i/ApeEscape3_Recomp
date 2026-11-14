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
