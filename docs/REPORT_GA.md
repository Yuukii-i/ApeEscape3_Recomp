# Task GA Report: Add Missing VU1 Ops to Python Model

## Overview
Added missing VU1 operations and flag ring handling to `tools/vu1gen/lbmodel.py` to enable modelling the 0AF0..0BC8 handler family and other VU1 microprograms without raising `ValueError`.

## Source Line References
Every added operation follows ground-truth semantics copied directly from the PS2Recomp VU1 interpreter:

### Flag & Ring Management
- **MAC Ring Visibility**: Initialized `self.macring` at `Model.run` entry from `rings["mac"]` (or fallback `st["mac"]`), pushed entries on every active FMAC (`self.macring.append((t, mac))`), and checked visibility using the rule `tc + 4 <= t` matching `vu1_hot_ops.h` / `vu1_flag_ring.h` and `clipring`.

### Lower Operations
- **`FCSET` (0x11)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:183-187`
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp:1572-1585` (`queueFcset`, `flgPushOrReplace`)
  Updates `self.wclip = lo & 0xFFFFFF` and replaces/appends to `self.clipring` at cycle `t`.
- **`FSEQ` (0x14)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:202-209`
  `res = 1 if ((self.status & 0xFFF) == imm12) else 0`, writes to `vi[ft]`.
- **`FSSET` (0x15)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:210-215`
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp:1501-1517` (`queueFsset`)
  Updates sticky status flags: `self.status = (self.status & 0x03F) | (imm12 & 0xFC0)`.
- **`FSAND` (0x16)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:216-223`
  `res = (self.status & 0xFFF) & imm12`, writes to `vi[ft]`.
- **`FSOR` (0x17)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:224-231`
  `res = (self.status & 0xFFF) | imm12`, writes to `vi[ft]`.
- **`FMEQ` (0x18)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:232-239`
  Compares visible `mac` word with `vi[fs] & 0xFFFF`; writes `1` if equal else `0` to `vi[ft]`.
- **`FMAND` (0x1A)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:240-247`
  Bitwise AND of visible `mac` word with `vi[fs] & 0xFFFF`; writes to `vi[ft]`.
- **`FMOR` (0x1B)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:248-255`
  Bitwise OR of visible `mac` word with `vi[fs] & 0xFFFF`; writes to `vi[ft]`.

### Lower Specials (Op 0x40)
- **`LQD` (0x36)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:471-484`
  Pre-decrements `vi[fs]`, loads quadword from `(vi[fs] * 16) & (dsz - 1)` into `vf[ft]` under `dest`.
- **`SQD` (0x37)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:485-498`
  Pre-decrements `vi[ft]`, stores quadword from `vf[fs]` into `(vi[ft] * 16) & (dsz - 1)` under `dest`.
- **`SQRT` (0x39)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:523-530`
  Computes `sqrt(abs(vf[ft][ftf]))`, sets `statusDi = 0x10` if operand is negative, queues to Q with latency 7 (`fdiv = (t + 7, val, di)`).
- **`RSQRT` (0x3A)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:531-553`
  Computes `vf[fs][fsf] / sqrt(abs(vf[ft][ftf]))`, handles divide-by-zero / clamp, queues to Q with latency 13 (`fdiv = (t + 13, val, di)`).
- **`WAITQ` (0x3B)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:554-555`
  No-op (`pass`), matching interpreter.
- **`ILWR` (0x3E)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:578-599`
  Loads integer word from `(vi[fs] * 16) & (dsz - 1)` with component selected by `dest` into `vi[ft]`.
- **`ISWR` (0x3F)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_lower.cpp:600-612`
  Stores integer word from `vi[ft]` into `(vi[fs] * 16) & (dsz - 1)` under `dest`.

### Upper Operations
- **`OPMULA` (SP 0x2E)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_upper.cpp:482-488`
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp:1283-1290`, `1493-1499`
  Cross product multiply into ACC: `ACC.x = vs.y * vt.z`, `ACC.y = vs.z * vt.x`, `ACC.z = vs.x * vt.y`, `ACC.w = 0.0f`.
- **`OPMSUB` (UP 0x2E)**:
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_upper.cpp:220-226`
  `PS2Recomp/ps2xRuntime/src/lib/vu/ps2_vu1_core.cpp:1208-1216`, `1338`, `1351-1371`, `1485-1491`
  Cross product subtract into VF: `res.x = ACC.x - vs.y * vt.z`, `res.y = ACC.y - vs.z * vt.x`, `res.z = ACC.z - vs.x * vt.y`, `res.w = 0.0f`.

---

## Verification Outputs

### 1. `python tools/vu1gen/lbmodel.py logs/vu1region.bin 50`
```
records=50 bad=0
model warnings: {}
```

### 2. `python tools/vu1gen/vspec.py 200`
```
records 200 exact(mem+vi) 145 declined 55 bad {}
```

### 3. `python tools/vu1gen/vregions_check.py 12`
#### Before Changes:
```
TOTAL records 2124 exact 1056 exceptions 1020 mismatched 48
```
Exceptions list included:
```
('lower op 1A at 0BD0', 24)
```

#### After Changes:
```
0050 n=12 exact=0 exc=0 bad=12 {'pc': 12, 'vi1': 12, 'cycle': 12} {}
0070 n=12 exact=0 exc=0 bad=12 {'vi13': 12, 'pc': 12, 'vi1': 12, 'cycle': 12} {}
0088 n=12 exact=0 exc=0 bad=12 {'vi13': 12, 'pc': 12, 'vi1': 12, 'cycle': 12} {}
0098 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0098 sig=13eefc24f37234d9': 12}
00A8 n=12 exact=0 exc=0 bad=12 {'vi6': 12, 'vi2': 12, 'vf': 12, 'mem': 12, 'pc': 12, 'vi7': 12, 'cycle': 12, 'status': 12, 'vi3': 12, 'vi1': 12, 'vi5': 12, 'acc': 11} {}
0AF8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0AF8 sig=e2f38a47daada9de': 12}
0B00 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0B00 sig=4a86e41804423013': 12}
0B08 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0B08 sig=ae31827f3e66ea7a': 12}
0B10 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0B10 sig=e2f79deeeeeea47b': 12}
0B18 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0B18 sig=a76c692e0f6a1f59': 12}
0B20 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=0B20 sig=000000001234abcd': 12}
24E0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=24E0 sig=50d77ae74cdce622': 12}
2500 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2500 sig=98ff0e9577ce0d49': 12}
2508 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2508 sig=01f2c48ae3e4b215': 12}
2510 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2510 sig=c264f017d56a109a': 12}
2518 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2518 sig=ea7e2a68d10a670f': 12}
2520 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2520 sig=2b6dacb6de9c74ab': 12}
2528 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2528 sig=678efd659f19d37d': 12}
2530 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2530 sig=cac6869e7276334d': 12}
2538 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2538 sig=cc99762d828e72f4': 12}
2540 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2540 sig=1f286a216a49bfcf': 12}
2548 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2548 sig=20b4efb27225b90a': 12}
2550 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2550 sig=6aedb02e4d0257a6': 12}
2558 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2558 sig=5ad955525ff1a0b5': 12}
2560 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2560 sig=5695808e451a0812': 12}
2568 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2568 sig=c2e610af5d3170da': 12}
2570 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2570 sig=abf5de403d6d47fe': 12}
2578 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2578 sig=854ac3adc4ff2fd9': 12}
2580 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2580 sig=3132d7a8a4ec5be9': 12}
2588 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2588 sig=4b9d87865572abd1': 12}
2590 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2590 sig=28c2234ef4b85a8d': 12}
2598 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2598 sig=513e2859dc4c8f27': 12}
25A0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25A0 sig=bb8fd945a66c7335': 12}
25A8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25A8 sig=59456ec07f308e2d': 12}
25B0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25B0 sig=2c9b4f00024e86e4': 12}
25D0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25D0 sig=b5e73323b9720663': 12}
25D8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25D8 sig=38c74bde9f14644a': 12}
25E0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25E0 sig=35e2a783be8f8b4a': 12}
25E8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=25E8 sig=86ce8bc7326769af': 12}
2678 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2678 sig=dbbeb51571a5c830': 12}
2680 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2680 sig=6efb28630aa541a1': 12}
2688 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2688 sig=f3e3eba09c001202': 12}
2690 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2690 sig=af156d4194246147': 12}
2698 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2698 sig=f118a1dd7af533c2': 12}
26A0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26A0 sig=d95d4a21124e0989': 12}
26A8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26A8 sig=81f2aa4d7da024f7': 12}
26B0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26B0 sig=6dd8318d6ef7731c': 12}
26B8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26B8 sig=3fe41f2331223e9d': 12}
26C0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26C0 sig=55ccbef9c1521741': 12}
26C8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26C8 sig=db1264c3382faae7': 12}
26D0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26D0 sig=1e74547dc00b1c9b': 12}
26D8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26D8 sig=18e69b16ece79dff': 12}
26E0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26E0 sig=d859f8f3d3e75a4f': 12}
26E8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26E8 sig=5f1b419b8444eb80': 12}
26F0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26F0 sig=8f7f0524a512e081': 12}
26F8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=26F8 sig=33e986e4072fccfa': 12}
2708 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2708 sig=50d77ae74cdce622': 12}
2720 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2720 sig=218480e4368572e8': 12}
2728 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2728 sig=98ff0e9577ce0d49': 12}
2730 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2730 sig=01f2c48ae3e4b215': 12}
2738 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2738 sig=c264f017d56a109a': 12}
2740 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2740 sig=ea7e2a68d10a670f': 12}
2748 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2748 sig=2b6dacb6de9c74ab': 12}
2750 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2750 sig=678efd659f19d37d': 12}
2758 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2758 sig=cac6869e7276334d': 12}
2760 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2760 sig=cc99762d828e72f4': 12}
2768 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2768 sig=1f286a216a49bfcf': 12}
2770 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2770 sig=20b4efb27225b90a': 12}
2778 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2778 sig=6aedb02e4d0257a6': 12}
2780 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2780 sig=933657478a298847': 12}
2788 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2788 sig=5695808e451a0812': 12}
2790 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2790 sig=c2e610af5d3170da': 12}
2798 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2798 sig=abf5de403d6d47fe': 12}
27A0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27A0 sig=854ac3adc4ff2fd9': 12}
27A8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27A8 sig=3132d7a8a4ec5be9': 12}
27B0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27B0 sig=4b9d87865572abd1': 12}
27B8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27B8 sig=28c2234ef4b85a8d': 12}
27C0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27C0 sig=513e2859dc4c8f27': 12}
27C8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27C8 sig=bb8fd945a66c7335': 12}
27D0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27D0 sig=59456ec07f308e2d': 12}
27D8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27D8 sig=2c9b4f00024e86e4': 12}
27E8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27E8 sig=f9696d956aea1536': 12}
27F0 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27F0 sig=979eb71a91ba9d33': 12}
27F8 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=27F8 sig=b5e73323b9720663': 12}
2800 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2800 sig=38c74bde9f14644a': 12}
2808 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2808 sig=35e2a783be8f8b4a': 12}
2810 n=12 exact=0 exc=12 bad=0 {} {'no block meta for pc=2810 sig=86ce8bc7326769af': 12}
TOTAL records 2124 exact 1080 exceptions 996 mismatched 48
[('no block meta for pc=0098 sig=13eefc24f37234d9', 12), ('no block meta for pc=0AF8 sig=e2f38a47daada9de', 12), ('no block meta for pc=0B00 sig=4a86e41804423013', 12), ('no block meta for pc=0B08 sig=ae31827f3e66ea7a', 12), ('no block meta for pc=0B10 sig=e2f79deeeeeea47b', 12), ('no block meta for pc=0B18 sig=a76c692e0f6a1f59', 12), ('no block meta for pc=0B20 sig=000000001234abcd', 12), ('no block meta for pc=24E0 sig=50d77ae74cdce622', 12)]
[('pc', 48), ('vi1', 48), ('cycle', 48), ('vi13', 24), ('vi6', 12), ('vi2', 12), ('vf', 12), ('mem', 12)]
```

The exception `('lower op 1A at 0BD0', 24)` no longer appears. Exact increased from 1056 to 1080, and mismatched count remained at 48.
