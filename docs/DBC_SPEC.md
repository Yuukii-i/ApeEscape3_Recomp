# DBCMAN / DS1O Input Protocol Specification (Ape Escape 3)

## 1. Executive Summary
Ape Escape 3 uses a proprietary controller driver subsystem composed of four EE-side RPC services (`0x80001300`, `0x8000131C`, `0x8000131E`, `0x8000131F`) and two IOP modules (`dbcman.irx` and `ds1o.irx`).

Crucially, **pad data delivery is NOT an RPC pull**. The EE does not query button or stick state via `sceSifCallRpc`. Instead:
1. During initialization (`sceDbcInit` at `sub_00406CC0`), the EE sends the address of a 128-byte work buffer (`0x757D40`) to IOP via `sceSifCallRpc(0x80001300, fno=0x80001304)` (`sceDbcSetWorkAddr`).
2. On every VBlank, `ds1o.irx` samples the hardware controller state via SIO2, packages a 128-byte DualShock / DualShock 2 status packet, and invokes `dbcman` export #10 (`0x031c`).
3. `dbcman.irx` issues a direct **SIF DMA push transfer** (`sceSifSetDma`) targeting EE memory at `workAddr` (`0x757D40`).
4. In the EE main loop (`sub_001037E8`), each frame executes `sub_00279B84` -> `sub_0026ED90` -> `sub_00405E30` -> `sub_00407A60`, which reads the 128 bytes from `0x757D40`, double-buffers them into `0x757BC0` / `0x757C80`, and unpacks buttons and analog sticks via `sub_0051785C` and `sub_00517788`.

---

## 2. EE RPC Services and Functions

### 2.1 Bound Services in `sceDbcInit` (`sub_00406CC0`)
The EE binds four SIF RPC services using `sceSifBindRpc` (`func_439848`):

| Service ID (`sid`) | Name / Role | Client Struct EE Address | Size | Source Reference |
| :--- | :--- | :--- | :--- | :--- |
| `0x80001300` | `DBC_BASE` (Driver control & version) | `0x00755940` | 40 bytes | `recomp_source/sub_00406CC0_0x406cc0.cpp:202-211` `[CONFIRMED]` |
| `0x8000131C` | `DBC_PAD` (Pad management) | `0x00755990` | 40 bytes | `recomp_source/sub_00406CC0_0x406cc0.cpp:417-425` `[CONFIRMED]` |
| `0x8000131E` | `DBC_PORT0` (Port 0 controller) | `0x007559B8` | 40 bytes | `recomp_source/sub_00406CC0_0x406cc0.cpp:480-490` `[CONFIRMED]` |
| `0x8000131F` | `DBC_PORT1` (Port 1 controller) | `0x007559E0` | 40 bytes | `recomp_source/sub_00406CC0_0x406cc0.cpp:615-624` `[CONFIRMED]` |

A mutex semaphore is created at `sub_00406CC0:664` (`CreateSema` max=127, init=1) and stored at `*(u32*)0x00757E00`. All subsequent DBC RPC calls surround `sceSifCallRpc` with `WaitSema` (`0x435B20`) and `SignalSema` (`0x435B00`) on `*(u32*)0x00757E00`.

### 2.2 Complete EE Function Number (`fno`) Table
Every DBC RPC call uses a 144-byte (`0x90` bytes) send buffer at `0x00755A40` and receive buffer at `0x00755A40`.

| `fno` | Name / Purpose | Calling EE Function | Send Buffer Layout | Recv Buffer / Result | EE Behavior & Validation |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0x80001363` | `sceDbcGetModVersion` | `sub_00406C68:79` | `[+0x00..0x8F]`: zeroed | `[+0x00]`: version (`u32`) | Returns `0x0310`. `sub_00406CC0:279-282` checks `(version >> 4) == 0x31`. If false, returns error `-1` `[CONFIRMED recomp_source/sub_00406CC0_0x406cc0.cpp:279-282]`. Stored in `dbcman.irx:.data:0x2714` `[CONFIRMED dbcman.irx:0x2714]`. |
| `0x80001304` | `sceDbcSetWorkAddr` | `sub_00407008:83` | `[+0x04]`: EE work buffer address (`0x00757D40`) | `[+0x00]`: status (`0` = success) | Saves target address for SIF DMA to `dbcman.irx:.data:0x2774` `[CONFIRMED dbcman.irx:0x08DC]`. |
| `0x80001301` | Reset / Stop | `sub_00407078:242` | `[+0x00..0x8F]`: config | `[+0x00]`: status | Unregisters DMA buffers / resets controllers `[CONFIRMED dbcman.irx:0x1CD8]`. |
| `0x80001302` | Set Mode | `sub_004071A8:152` | `[+0x04]`: port, `[+0x08]`: mode | `[+0x00]`: status | Configures actuator / vibration motor settings `[CONFIRMED dbcman.irx:0x1CE8]`. |
| `0x80001303` | Actuator Set | `sub_00407268:334` | `[+0x04]`: port, `[+0x08..]`: motor speeds | `[+0x00]`: status | Sets small/large vibration motor levels `[CONFIRMED dbcman.irx:0x1CF8]`. |
| `0x80001315` | Read Port Status | `sub_00407268:769` | `[+0x04]`: port | `[+0x00]`: status (`1` = ready) | Queries controller connection state `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x80001316` | Read Device Capabilities | `sub_00407268:976` | `[+0x04]`: port | `[+0x00..0x0C]`: caps | Inquires whether analog/pressure mode is supported `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x80001317` | Read Button Mask | `sub_00407268:1183`| `[+0x00]`: port | `[+0x00..0x04]`: mask | Configures which button bits are active `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x8000131D` | Set Actuator Config | `sub_00407268:1405`| `[+0x10]`: align, `[+0x14]`: slot | `[+0x00]`: status | Binds rumble motors to DualShock 2 motor slots `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x80001318` | Set Pressure Mode | `sub_00407268:1744`| `[+0x04]`: port, `[+0x08]`: enable (1) | `[+0x00]`: status | Enables 12-byte pressure button reporting `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x80001319` | Query Config State | `sub_00407268:2173`| `[+0x04]`: port | `[+0x00]`: config state | Verifies controller is in configuration exit state `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x8000131A` | Exit Config Mode | `sub_00407D68:144` | `[+0x08]`: lock mode | `[+0x00]`: status | Locks DualShock 2 analog LED button `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |
| `0x8000131C` | Poll Status Callback | `sub_00407A60:851` | `[+0x00..0x208F]`: payload | `[+0x00]`: result | Infrequent status heartbeat / slot query `[CONFIRMED dbcman.irx:jump_table:0x2560]`. |

---

## 3. Data Delivery Architecture (SIF DMA Push)

### 3.1 IOP Side (`dbcman.irx` and `ds1o.irx`)
1. **Work Address Registration**:
   `sub_00407008` sends `0x00757D40`. IOP function `dbcman.irx:0x08DC` writes this pointer to `dbcman.irx:.data:0x2774`.
2. **Controller Polling on IOP VBlank**:
   `ds1o.irx` runs as a high-priority thread synced to VBlank interrupts. It polls controller port 0 using SIO2 hardware commands.
3. **Triggering Transfer**:
   `ds1o.irx:0x16F8` calls `dbcman` export #10 (`0x031C`), passing:
   - `$a0`: device handle (`*(u32*)0x1D40`)
   - `$a1`: port (`0`)
   - `$a2`: pointer to sampled controller buffer in IOP RAM
   - `$a3`: buffer length (`0x80` = 128 bytes)
4. **DMA Dispatch**:
   `dbcman.irx:0x00A4-0x0104` builds a `SifDmaTransfer_t` struct on stack:
   - `dest`: `*(u32*)0x2774` (`0x00757D40` in EE RDRAM)
   - `src`: `0x2778` (IOP local controller packet buffer)
   - `size`: `0x80` (128 bytes)
   - `attr`: `0`
   It calls `sceSifSetDma` (import stub `0x21DC`), with DMA completion callback `0x02F4` which signals semaphore `*(u32*)0x2770` via `iSignalSema`.

### 3.2 EE Consumer Execution Trace
On every frame:
1. `sub_001037E8` (Main loop) calls `sub_00279B84:293`.
2. `sub_00279B84:293` calls `sub_0026ED90:19`.
3. `sub_0026ED90:19` calls `sub_00405E30:203` with `$a0 = *(u32*)(*(u32*)0x00649728 + 4)`.
4. `sub_00405E30:203` calls `sub_00407A60:80-99` (`sceDbcRead`):
   - Reads packet size from `0x757D40 + 8`.
   - Verifies `size <= 128` (`0x407A94: slti $v0, $v1, 0x81`).
   - Copies 128 bytes into the EE double-buffer:
     - `buffer_index = *(u32*)0x0069E334 % 2` (`recomp_source/sub_00407A60_0x407a60.cpp:160-194`)
     - `dst_buffer = 0x00757BC0 + buffer_index * 192` (`0xC0` bytes)
     - `dst_buffer + 0x00`: copy status
     - `dst_buffer + 0x04`: port ID
     - `dst_buffer + 0x08`: packet size (`0x80`)
     - `dst_buffer + 0x0C..`: 128-byte raw controller packet data
5. `sub_0026EB34` consumes this data:
   - Calls `sub_0051785C` (`recomp_source/sub_0051785C_0x51785c.cpp:1-40`):
     - Unpacks 16-bit digital button mask at `dst_buffer + 0x0C`.
     - Inverts active-low bits (`nor $t6, $zero, $s2`).
     - Computes edge triggers (`pressed_this_frame`, `released_this_frame`).
   - Calls `sub_00517788` (`recomp_source/sub_00517788_0x517788.cpp:1-60`):
     - Unpacks Left/Right analog stick byte axes (`0..255`).
     - Subtracts 128 (`addiu $a1, $a1, -0x80`).
     - Converts to single-precision float (`cvt.s.w`).
     - Multiplies by scale factor `1.0f / 128.0f` (`lwc1 $f1, 0x6ED0AC`) to yield normalized `[-1.0f, +1.0f]`.
     - Computes vector magnitude squared (`mula.s $f6, $f6`) for deadzone filtering.

---

## 4. 128-Byte Controller Packet Layout (`0x00757D40`)

The 128-byte work buffer at `0x00757D40` has the following exact binary layout:

| Offset | Type | Field Name | Expected Connected Value | Description |
| :--- | :--- | :--- | :--- | :--- |
| `+0x00` | `uint8_t` | `status` | `0x00` | Connection status: `0x00` = SUCCESS / connected; `0xFF` = disconnected. |
| `+0x01` | `uint8_t` | `device_id` | `0x73` (analog) or `0x79` (pressure) | High nibble `0x7` = DualShock analog; low nibble = data halfwords count (`3` = 6 bytes, `9` = 18 bytes). |
| `+0x02` | `uint8_t` | `ack` | `0x5A` | Standard SPI acknowledge token. |
| `+0x03` | `uint8_t` | `buttons_lo` | Bitmask (active LOW) | `d_pad` and system buttons (see table below). |
| `+0x04` | `uint8_t` | `buttons_hi` | Bitmask (active LOW) | Action buttons and shoulder buttons (see table below). |
| `+0x05` | `uint8_t` | `rx` | `0x00..0xFF` (center `0x80`) | Right stick horizontal axis (0 = full left, 255 = full right). |
| `+0x06` | `uint8_t` | `ry` | `0x00..0xFF` (center `0x80`) | Right stick vertical axis (0 = full up, 255 = full down). |
| `+0x07` | `uint8_t` | `lx` | `0x00..0xFF` (center `0x80`) | Left stick horizontal axis (0 = full left, 255 = full right). |
| `+0x08` | `uint8_t` | `ly` | `0x00..0xFF` (center `0x80`) | Left stick vertical axis (0 = full up, 255 = full down). |
| `+0x09` | `uint8_t` | `press_right` | `0x00..0xFF` | D-Pad Right pressure level (0 = released, 255 = maximum). |
| `+0x0A` | `uint8_t` | `press_left` | `0x00..0xFF` | D-Pad Left pressure level. |
| `+0x0B` | `uint8_t` | `press_up` | `0x00..0xFF` | D-Pad Up pressure level. |
| `+0x0C` | `uint8_t` | `press_down` | `0x00..0xFF` | D-Pad Down pressure level. |
| `+0x0D` | `uint8_t` | `press_triangle`| `0x00..0xFF` | Triangle pressure level. |
| `+0x0E` | `uint8_t` | `press_circle` | `0x00..0xFF` | Circle pressure level. |
| `+0x0F` | `uint8_t` | `press_cross` | `0x00..0xFF` | Cross pressure level. |
| `+0x10` | `uint8_t` | `press_square` | `0x00..0xFF` | Square pressure level. |
| `+0x11` | `uint8_t` | `press_l1` | `0x00..0xFF` | L1 pressure level. |
| `+0x12` | `uint8_t` | `press_r1` | `0x00..0xFF` | R1 pressure level. |
| `+0x13` | `uint8_t` | `press_l2` | `0x00..0xFF` | L2 pressure level. |
| `+0x14` | `uint8_t` | `press_r2` | `0x00..0xFF` | R2 pressure level. |
| `+0x15..0x7F`| `uint8_t[107]` | `reserved` | `0x00` | Zero-padded to 128 bytes. |

### 4.1 Digital Buttons Bitmask Layout (`buttons_lo` / `buttons_hi`)
Buttons are **active LOW** (`0` = pressed, `1` = released). When no buttons are pressed, `buttons = 0xFFFF`.

| Bit | Byte | Mask | PS2 Button | Raylib Gamepad Button | Keyboard Fallback |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `0` | `lo` (`+0x03`) | `0x0001` | `SELECT` | `GAMEPAD_BUTTON_MIDDLE_LEFT` | `KEY_BACKSPACE` |
| `1` | `lo` (`+0x03`) | `0x0002` | `L3` (Left Thumb Click) | `GAMEPAD_BUTTON_LEFT_THUMB` | `KEY_V` |
| `2` | `lo` (`+0x03`) | `0x0004` | `R3` (Right Thumb Click)| `GAMEPAD_BUTTON_RIGHT_THUMB`| `KEY_B` |
| `3` | `lo` (`+0x03`) | `0x0008` | `START` | `GAMEPAD_BUTTON_MIDDLE_RIGHT`| `KEY_ENTER` |
| `4` | `lo` (`+0x03`) | `0x0010` | `D-PAD UP` | `GAMEPAD_BUTTON_LEFT_FACE_UP` | `KEY_UP` |
| `5` | `lo` (`+0x03`) | `0x0020` | `D-PAD RIGHT` | `GAMEPAD_BUTTON_LEFT_FACE_RIGHT`| `KEY_RIGHT` |
| `6` | `lo` (`+0x03`) | `0x0040` | `D-PAD DOWN` | `GAMEPAD_BUTTON_LEFT_FACE_DOWN` | `KEY_DOWN` |
| `7` | `lo` (`+0x03`) | `0x0080` | `D-PAD LEFT` | `GAMEPAD_BUTTON_LEFT_FACE_LEFT` | `KEY_LEFT` |
| `8` | `hi` (`+0x04`) | `0x0100` | `L2` | `GAMEPAD_BUTTON_LEFT_TRIGGER_1` | `KEY_Q` |
| `9` | `hi` (`+0x04`) | `0x0200` | `R2` | `GAMEPAD_BUTTON_RIGHT_TRIGGER_1`| `KEY_E` |
| `10`| `hi` (`+0x04`) | `0x0400` | `L1` | `GAMEPAD_BUTTON_LEFT_TRIGGER_2` | `KEY_1` |
| `11`| `hi` (`+0x04`) | `0x0800` | `R1` | `GAMEPAD_BUTTON_RIGHT_TRIGGER_2`| `KEY_3` |
| `12`| `hi` (`+0x04`) | `0x1000` | `TRIANGLE` | `GAMEPAD_BUTTON_RIGHT_FACE_UP` | `KEY_I` |
| `13`| `hi` (`+0x04`) | `0x2000` | `CIRCLE` | `GAMEPAD_BUTTON_RIGHT_FACE_RIGHT`| `KEY_L` |
| `14`| `hi` (`+0x04`) | `0x4000` | `CROSS` | `GAMEPAD_BUTTON_RIGHT_FACE_DOWN` | `KEY_K` |
| `15`| `hi` (`+0x04`) | `0x8000` | `SQUARE` | `GAMEPAD_BUTTON_RIGHT_FACE_LEFT` | `KEY_J` |

---

## 5. Device Present Conditions & Startup Bypass
To pass controller detection without errors:
1. `+0x00` (`status`) must be `0x00`.
2. `+0x01` (`device_id`) must be `0x73` (standard DualShock analog) or `0x79` (DualShock 2 pressure).
3. `+0x02` (`ack`) must be `0x5A`.
4. `+0x03..0x04` must be `0xFFFF` (no buttons pressed).
5. `+0x05..0x08` (analog sticks) must be `0x80` (128 = centered).
6. When `sub_00407008` is called (`fno=0x80001304`), the HLE must record the guest work address (`0x00757D40`).

---

## 6. Recommended Implementation Hook Point

### 6.1 Hook Location in `ps2_runtime.cpp`
- **File**: [`PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp`](file:///c:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp)
- **Function**: `void PS2Runtime::renderFrame(uint8_t* rdram)`
- **Timing**: Triggered once per frame immediately before or after `displayVramBuffer(...)`.

### 6.2 Implementation Logic
```cpp
void PS2Runtime::updateDbcPadState(uint8_t* rdram) {
    constexpr uint32_t kDbcWorkAddr = 0x00757D40u;
    uint8_t* pad = rdram + kDbcWorkAddr;

    // Header: Controller Connected & Ready
    pad[0] = 0x00; // Success
    pad[1] = 0x79; // DualShock 2 (Pressure Mode)
    pad[2] = 0x5A; // Acknowledge

    // Sample Digital Buttons (active LOW)
    uint16_t buttons = 0xFFFF;
    if (IsKeyDown(KEY_ENTER) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_MIDDLE_RIGHT))  buttons &= ~0x0008; // START
    if (IsKeyDown(KEY_BACKSPACE) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_MIDDLE_LEFT)) buttons &= ~0x0001; // SELECT
    if (IsKeyDown(KEY_UP) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_FACE_UP))       buttons &= ~0x0010; // UP
    if (IsKeyDown(KEY_RIGHT) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_FACE_RIGHT))  buttons &= ~0x0020; // RIGHT
    if (IsKeyDown(KEY_DOWN) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_FACE_DOWN))   buttons &= ~0x0040; // DOWN
    if (IsKeyDown(KEY_LEFT) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_FACE_LEFT))   buttons &= ~0x0080; // LEFT
    if (IsKeyDown(KEY_K) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_FACE_DOWN))     buttons &= ~0x4000; // CROSS
    if (IsKeyDown(KEY_L) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_FACE_RIGHT))    buttons &= ~0x2000; // CIRCLE
    if (IsKeyDown(KEY_J) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_FACE_LEFT))     buttons &= ~0x8000; // SQUARE
    if (IsKeyDown(KEY_I) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_FACE_UP))       buttons &= ~0x1000; // TRIANGLE
    if (IsKeyDown(KEY_1) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_TRIGGER_2))      buttons &= ~0x0400; // L1
    if (IsKeyDown(KEY_3) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_2))     buttons &= ~0x0800; // R1
    if (IsKeyDown(KEY_Q) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_TRIGGER_1))      buttons &= ~0x0100; // L2
    if (IsKeyDown(KEY_E) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_TRIGGER_1))     buttons &= ~0x0200; // R2
    if (IsKeyDown(KEY_V) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_LEFT_THUMB))          buttons &= ~0x0002; // L3
    if (IsKeyDown(KEY_B) || IsGamepadButtonDown(0, GAMEPAD_BUTTON_RIGHT_THUMB))         buttons &= ~0x0004; // R3

    pad[3] = static_cast<uint8_t>(buttons & 0xFF);
    pad[4] = static_cast<uint8_t>((buttons >> 8) & 0xFF);

    // Sample Analog Sticks (Centered at 128)
    float lx = GetGamepadAxisMovement(0, GAMEPAD_AXIS_LEFT_X);
    float ly = GetGamepadAxisMovement(0, GAMEPAD_AXIS_LEFT_Y);
    float rx = GetGamepadAxisMovement(0, GAMEPAD_AXIS_RIGHT_X);
    float ry = GetGamepadAxisMovement(0, GAMEPAD_AXIS_RIGHT_Y);

    // Keyboard stick simulation: WASD -> Left Stick, TFGH -> Right Stick
    if (IsKeyDown(KEY_A)) lx = -1.0f; else if (IsKeyDown(KEY_D)) lx = 1.0f;
    if (IsKeyDown(KEY_W)) ly = -1.0f; else if (IsKeyDown(KEY_S)) ly = 1.0f;
    if (IsKeyDown(KEY_F)) rx = -1.0f; else if (IsKeyDown(KEY_H)) rx = 1.0f;
    if (IsKeyDown(KEY_T)) ry = -1.0f; else if (IsKeyDown(KEY_G)) ry = 1.0f;

    pad[5] = static_cast<uint8_t>(std::clamp((rx + 1.0f) * 127.5f, 0.0f, 255.0f)); // RX
    pad[6] = static_cast<uint8_t>(std::clamp((ry + 1.0f) * 127.5f, 0.0f, 255.0f)); // RY
    pad[7] = static_cast<uint8_t>(std::clamp((lx + 1.0f) * 127.5f, 0.0f, 255.0f)); // LX
    pad[8] = static_cast<uint8_t>(std::clamp((ly + 1.0f) * 127.5f, 0.0f, 255.0f)); // LY

    // Pressure Bytes (0 or 255)
    for (int i = 9; i < 21; ++i) pad[i] = 0x00;
    if (!(buttons & 0x4000)) pad[0x0F] = 0xFF; // Cross
    if (!(buttons & 0x2000)) pad[0x0E] = 0xFF; // Circle
    if (!(buttons & 0x8000)) pad[0x10] = 0xFF; // Square
    if (!(buttons & 0x1000)) pad[0x0D] = 0xFF; // Triangle
}
```
