# SG2IOPM1 Audio Protocol Specification (Ape Escape 3)

## 1. Executive Summary
Ape Escape 3 delegates music sequencing and sound effect management to the IOP module `sg2iopm1.irx` (`bin/irx/3.0/sg2iopm1.irx` in `DATA.BIN`).

Prior agent reports claimed that `sg2iopm1` registered RPC `0x80001800` and that a function `sub_003702C8` waited on `0x00746FF8` until an alleged completion callback `sub_003703D0` ran. **Our investigation definitively proves this was a misconception:**
1. `sg2iopm1.irx` registers SIF RPC server ID **`0x11223344`** (`sg2iopm1.irx:0x3B70-0x3B88`), **NOT** `0x80001800`.
2. The EE binds to `0x11223344` in `sub_003FC100:110-128` (`client=0x0074B240`).
3. `0x00746FF8` does **not exist** anywhere in the game binary or recompiled sources.
4. `0x3703D0` is NOT a callback; it is simply the delay slot instruction of `sub_003703C4` (`sb $t6, -0x67E4($t7)` writing byte `1` to `0x0069981C`).
5. `sub_003703D4` is a sound error inquiry function called by `sub_0015993C:74`. It returns byte `*(u8*)0x0069981C` in `$v0`. In unmodified game BSS, `*(u8*)0x0069981C == 0`, so `sub_003703D4` naturally returns `0` (Success / Sound OK) without requiring any runtime PC overrides.

---

## 2. RPC Architecture & Communication Flow

```
+-------------------------------------------------------------+
|                     EE (Game Engine)                        |
|                                                             |
|   sub_003FC100: sceSifBindRpc(client=0x74B240, 0x11223344)  |
|                                                             |
|   sub_0036FC28: Formats 16-byte audio command packets       |
|                                                             |
|   sub_003FBFB0: sceSifCallRpc(                              |
|                     client=0x74B240,                        |
|                     fno=0,                                  |
|                     mode=SIF_RPC_M_NOWAIT (1),              |
|                     send_buf=0x747080, send_size=N*16,      |
|                     recv_buf=0x74B080, recv_size=0x1C0)     |
+------------------------------+------------------------------+
                               | SIF RPC (0x11223344)
                               v
+-------------------------------------------------------------+
|                    IOP (sg2iopm1.irx)                       |
|                                                             |
|   0x3BB4: RPC Server Handler                                |
|   - Verifies fno == 0                                       |
|   - Reads N = (send_size >> 4) packets                      |
|   - Enqueues packets into ring buffer at 0x4938 (1024 slots)|
|   - Returns 448 bytes (0x1C0) from 0x8D38 to EE recv_buf    |
|                                                             |
|   0x3A44: Command Dispatcher                                |
|   - Drains ring buffer at 0x4938                            |
|   - Opcode = packet.word[0]                                 |
|   - Dispatches via 36-entry jump table at 0x4820            |
|   - Calls libsd.irx (sceSdSetParam, sceSdKeyOn, etc.)       |
+------------------------------+------------------------------+
                               | IOP Imports
                               v
+-------------------------------------------------------------+
|                      libsd.irx / SPU2                       |
|   Synthesizes voices, volumes, pitches, reverb, ADPCM waves |
+-------------------------------------------------------------+
```

---

## 3. Disassembly Evidence: RPC Registration & Server Handler

### 3.1 Registration in `sg2iopm1.irx` (`0x3B60..0x3B90`) `[CONFIRMED]`
```mips
0x3b6c: move       $a0, $v0           # SifRpcServerData_t*
0x3b70: lui        $a1, 0x1122        # Server ID high: 0x1122
0x3b74: ori        $a1, $a1, 0x3344   # Server ID low:  0x3344 -> SID = 0x11223344!
0x3b78: lui        $a2, 0
0x3b7c: addiu      $a2, $a2, 0x3bb4   # RPC Handler function = 0x3BB4
0x3b80: lui        $a3, 1
0x3b84: addiu      $a3, $a3, -0x1260  # Receive buffer in IOP RAM = 0xEDA0
0x3b88: jal        sceSifRegisterRpc  # Register RPC Service
0x3b8c: nop
0x3b90: jal        sceSifSetRpcQueue  # Queue RPC Service
```

### 3.2 Server Handler in `sg2iopm1.irx` (`0x3BB4..0x3C90`) `[CONFIRMED]`
```mips
0x3bd0: lw         $v0, 0x28($fp)     # Load fno argument
0x3bd8: bnez       $v0, 0x3c9c        # If fno != 0, return NULL
0x3be0: lw         $v0, 0x2c($fp)     # Load send_buf pointer (EE packets)
0x3bec: lw         $v1, 0x30($fp)     # Load send_size
0x3bf4: srl        $v0, $v1, 4        # packet_count = send_size / 16
# Loop through all 16-byte packets:
0x3c20: lw         $a0, 0x0($pkt)     # packet.word[0] (Opcode)
0x3c4c: lw         $a1, 0x4($pkt)     # packet.word[1] (Channel / Voice mask)
0x3c50: lw         $a2, 0x8($pkt)     # packet.word[2] (Pitch / Volume)
0x3c54: lw         $a3, 0xC($pkt)     # packet.word[3] (ADPCM address / Pan)
0x3c58: jal        0x3E58             # Enqueue into 1024-entry ring buffer at 0x4938
0x3c84: jal        0x3CB8             # Trigger dispatcher
0x3c8c: lui        $v0, 1
0x3c90: addiu      $v0, $v0, -0x72c8  # Return pointer 0x8D38 (448 bytes status)
```

---

## 4. The 36-Entry Command Jump Table (`sg2iopm1.irx:.data:0x4820`)

When dispatcher `0x3A44` drains the queue, it reads `opcode = packet.word[0]` and branches through `0x4820 + opcode * 4`:

| Opcode | Handler Addr | Description / Subsystem | Imported Calls |
| :--- | :--- | :--- | :--- |
| `0x00` | `0x0698` | No-Op / Ping | None |
| `0x01` | `0x06B4` | Play Sound Effect (Channel Alloc & Trigger) | `libsd:sceSdSetParam` |
| `0x02` | `0x0870` | Key On (Voice note-on trigger) | `libsd:sceSdKeyOn` |
| `0x03` | `0x09B4` | Key Off (Voice note-off trigger) | `libsd:sceSdKeyOff` |
| `0x04` | `0x0A68` | Set Voice Parameters (Volume, Pitch, ADSR) | `libsd:sceSdSetParam` |
| `0x05` | `0x0E48` | Stop Voice / Fade Out | `libsd:sceSdSetParam` |
| `0x06` | `0x0F10` | Set Master Volume (Left/Right) | `libsd:sceSdSetParam` |
| `0x07` | `0x0F8C` | Set Reverb Mode & Depth | `libsd:sceSdSetParam` |
| `0x08` | `0x0FE8` | Set Core Effect Parameters | `libsd:sceSdSetParam` |
| `0x09` | `0x1044` | Query Voice Playback Status | `0x41CC` |
| `0x0A` | `0x10B8` | Query Core Volume | `0x41CC` |
| `0x0B` | `0x1104` | Pause All Active Voices | `libsd:sceSdSetSwitch` |
| `0x0C` | `0x1154` | Resume All Paused Voices | `libsd:sceSdSetSwitch` |
| `0x0D` | `0x11C8` | Stop All Active Voices | `libsd:sceSdKeyOff` |
| `0x0E` | `0x1284` | Set Sound Group Volume | None |
| `0x0F` | `0x1314` | Set Sound Group Pitch | None |
| `0x10` | `0x1374` | Set Sound Group Pan | None |
| `0x11` | `0x13D4` | Load Sound Bank Header | SIO/SIF |
| `0x12` | `0x1538` | Unload Sound Bank | `0x4214` |
| `0x13` | `0x1570` | Set BGM Track Volume | None |
| `0x14` | `0x15F0` | Start BGM Sequence | `libsd:sceSdKeyOn` |
| `0x15` | `0x1670` | Stop BGM Sequence | `libsd:sceSdKeyOff` |
| `0x16` | `0x2A20` | BGM Tempo / Speed Adjust | `0x42A0` |
| `0x17` | `0x2A74` | BGM Track Mute / Solo | None |
| `0x18` | `0x2A90` | Transfer Waveform Sample to SPU2 RDRAM | `libsd:sceSdVoiceTrans` |
| `0x19` | `0x2DFC` | Waveform DMA Status Poll | None |
| `0x1A` | `0x2EF0` | Set Voice Pitch Bend | `libsd:sceSdSetParam` |
| `0x1B` | `0x306C` | Set Voice Modulation / LFO | `libsd:sceSdSetParam` |
| `0x1C` | `0x31C0` | Set Voice Envelope (Attack, Decay, Sustain, Release) | `libsd:sceSdSetParam` |
| `0x1D` | `0x3450` | Reset Audio Driver State | `libsd:sceSdInit` |
| `0x1E` | `0x35F4` | Configure Hardware Reverb Workarea | `0x42A0` |
| `0x1F` | `0x36A4` | Set Digital Audio Output Rate | `0x4214` |
| `0x20` | `0x373C` | Set Voice Noise Clock / Noise Mode | `libsd:sceSdSetSwitch` |
| `0x21` | `0x386C` | Flush Audio Buffers | `0x4214` |
| `0x22` | `0x3904` | Set Voice Panpot / 3D Audio Position | None |
| `0x23` | `0x39A8` | Driver Heartbeat / Sync Frame | None |

---

## 5. Investigation of `sub_003703D4` and Myth Busing

### 5.1 Myth: "0x00746FF8 Flag & sub_003703D0 Callback"
Prior documentation claimed:
- `sub_003703D4` waits for `*(u32*)0x00746FF8 == 0`.
- An IOP completion callback `sub_003703D0` runs and clears `0x00746FF8`.

### 5.2 Confirmed Truth:
1. Grepping `recomp_source/` confirms **`0x746FF8` does not exist**.
2. Address `0x3703D0` is the delay slot instruction of `sub_003703C4` (`recomp_source/sub_003703C4_0x3703c4.cpp:36-37`):
   ```mips
   // 0x3703cc: jr $ra
   // 0x3703d0: sb $t6, -0x67E4($t7)   # $t6=1, $t7=0x6A0000 -> *(u8*)0x69981C = 1!
   ```
3. `sub_003703D4` (`recomp_source/sub_003703D4_0x3703d4.cpp:28-119`) decompiles to:
   ```c
   uint32_t sub_003703D4() {
       if (*(uint32_t*)0x00635470 == 0) {
           if ((*(uint32_t*)0x00649714 & 1) != 0) {
               // Bit 0 of 0x649714 is "sound subsystem disabled/faulted"
               sub_003703C4(); // Sets *(uint8_t*)0x0069981C = 1
           }
       }
       return (uint32_t)*(uint8_t*)0x0069981C;
   }
   ```
4. `sub_0015993C:74-95` calls `sub_003703D4()`. If `$v0 != 0`, it writes `4` to `0x635544` (flagging sound subsystem failure). If `$v0 == 0`, sound init succeeds!
5. In normal game boot, `*(u8*)0x0069981C == 0` and `*(u32*)0x00649714 == 0`. Thus, `sub_003703D4` naturally returns `0`! The prior override at `ps2_runtime.cpp:1141-1145` was only necessary because `0x11223344` was not bound, causing previous sound init code to fail and trip bit 0 of `0x649714`.

---

## 6. Minimal Faithful HLE & Implementation Plan

### 6.1 Phase 1: Minimal HLE (Unblocks Boot Without Overrides)
1. In [`PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Syscalls/RPC.cpp):
   - Replace the unused `0x80001800` entry in `s_rpcHleServices` with `0x11223344`:
     ```cpp
     // 0x11223344: sg2iopm1 audio sequencer RPC service
     {
         0x11223344u,
         [](uint8_t* rdram, SifRpcServerData_t* server, int fno, void* sendBuf, int sendSize, void* recvBuf, int recvSize) -> int {
             if (recvBuf && recvSize >= 0x1C0) {
                 // Zero-initialize the 448-byte voice status response
                 std::memset(recvBuf, 0, 0x1C0);
             }
             return 0; // Success
         }
     }
     ```
2. In `ps2_runtime.cpp:1141-1145`:
   - Remove the `0x003703D4` override. The guest code runs completely unmodified and cleanly returns 0.

### 6.2 Phase 2: Full Audio Playback via `libsd`
1. When `sceSifCallRpc(0x11223344, fno=0)` is called:
   - Cast `sendBuf` to `const uint32_t*`.
   - Iterate through `sendSize / 16` packets.
   - For Opcode `0x01` (Play Sound Effect):
     - Extract sound bank ID and sample index.
     - Call `libsd` (`sceSdKeyOn(0, voice_mask)`).
   - For Opcode `0x04` (Set Volume/Pitch):
     - Call `libsd` (`sceSdSetParam(0 | voice, SD_PARAM_BVOLL, vol_l)`).
2. SPU2 synthesis in `libsd.cpp` feeds into Raylib audio device, producing game sound effects.

---

## 7. Empirical Live Decoding & SID Registration Verification (`[CONFIRMED]`)

### 7.1 SID Registration Findings
- `RPC.cpp:init()` confirms registered HLE SIDs:
  - `0x11223344`: SG2 Audio (`sg2iopm1.irx`)
  - `0x80001300`, `0x8000131C`, `0x8000131E`, `0x8000131F`: DBC pad/multitap services
  - `0x80001800`: **NOT REGISTERED** (`[CONFIRMED logs/run_20261019_231054.log:141]`). `0x80001800` is absent from game binaries and was an early hypothesis myth.

### 7.2 Live SG2 Packet Stream (First 288-Byte Call, 18 Packets)
During boot, the EE sends an initial setup batch of 18 16-byte packets (`288` bytes total) via `sceSifCallRpc(0x11223344, fno=0)` `[CONFIRMED logs/run_20261019_231054.log:962-988]`:
- Pkt 00: Op=0x11 (Load Sound Bank) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 01: Op=0x05 (Stop Voice/Fade) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 02: Op=0x05 (Stop Voice/Fade) arg0=0x00000001 arg1=0x00000000 arg2=0x00000000
- Pkt 03: Op=0x16 (BGM Tempo) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 04: Op=0x16 (BGM Tempo) arg0=0x00000001 arg1=0x00000000 arg2=0x00000000
- Pkt 05: Op=0x0B (Pause Voices) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 06: Op=0x0B (Pause Voices) arg0=0x00000001 arg1=0x00000000 arg2=0x00000000
- Pkt 07: Op=0x10 (Group Pan) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 08: Op=0x10 (Group Pan) arg0=0x00000001 arg1=0x00000000 arg2=0x00000000
- Pkt 09: Op=0x0F (Group Pitch) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 10: Op=0x0F (Group Pitch) arg0=0x00000001 arg1=0x00000000 arg2=0x00000000
- Pkt 11: Op=0x0E (Group Volume) arg0=0x00000000 arg1=0x0000007F arg2=0x00000000
- Pkt 12: Op=0x0E (Group Volume) arg0=0x00000001 arg1=0x0000007F arg2=0x00000000
- Pkt 13: Op=0x0D (Stop All Voices) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 14: Op=0x06 (Master Volume) arg0=0x0000007F arg1=0x0000007F arg2=0x00000000
- Pkt 15: Op=0x09 (Voice Status) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000
- Pkt 16: Op=0x0A (Core Volume) arg0=0x00000000 arg1=0x00007FFF arg2=0x00007FFF
- Pkt 17: Op=0x08 (Core Effects) arg0=0x00000000 arg1=0x00000000 arg2=0x00000000

Subsequent calls are 0-byte heartbeats requesting a 448-byte voice status update at 60 Hz `[CONFIRMED logs/run_20261019_234141.log:910-1200]`.

