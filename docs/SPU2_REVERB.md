# SPU2 reverb reference (for Task BD)

Sources: ps2sdk FREESD libsd `iop/sound/libsd/src/effect.c` (Academic Free License 2.0, TyRaNiD / Lukasz Bruun) for the
preset tables and sceSdSetEffectAttr behaviour; psx-spx (nocash) "SPU Reverb Formula" for the algorithm (SPU2 reverb uses
the same register set and formula as the PS1 SPU, per core).

## Preset tables (verbatim from effect.c). Mode index = SD_EFFECT_MODE (0 OFF,1 ROOM,2 STUDIO_A,3 STUDIO_B,4 STUDIO_C,
5 HALL,6 SPACE,7 ECHO,8 DELAY,9 PIPE). memcpy into u16 mode_data[32] (little endian: [2k]=low half of word k, [2k+1]=high).

```c
u16 EffectSizes[10] = { 0x1, 0x26C, 0x1F4, 0x484, 0x6FE, 0xADE, 0xF6C, 0x1804, 0x1804, 0x3C0 };
u32 EffectParams[160] = {
 0x00000000,0x00000000,0x00000000,0x00000000,0x00000000,0x00010001,0x00000000,0x00000000,0x00000000,0x00010001,0x00000000,0x00000000,0x00000000,0x00000000,0x00000000,0x00000000,
 0x005B007D,0x54B86D80,0x0000BED0,0xBA800000,0x53005800,0x033304D6,0x022703F0,0x01EF0374,0x01B70336,0x01B60335,0x01B50334,0x01B50334,0x01B50334,0x013601B4,0x005C00B8,0x80008000,
 0x00250033,0x4FA870F0,0x4410BCE0,0x9C00C0F0,0x4EC05280,0x031B03E4,0x02AF03A4,0x02660372,0x025D031C,0x018E025C,0x0135022F,0x00B701D2,0x00B5018F,0x008000B4,0x0026004C,0x80008000,
 0x007F00B1,0x4FA870F0,0x4510BCE0,0xB4C0BEF0,0x4EC05280,0x076B0904,0x065F0824,0x061607A2,0x05ED076C,0x042E05EC,0x0305050F,0x02B70462,0x0265042F,0x01B20264,0x00800100,0x80008000,
 0x00A900E3,0x4FA86F60,0x4510BCE0,0xA680BEF0,0x52C05680,0x0B580DFB,0x0A3C0D09,0x09730BD9,0x08DA0B59,0x05E908D9,0x04B007EC,0x03D206EF,0x031D05EA,0x0238031C,0x00AA0154,0x80008000,
 0x013901A5,0x50006000,0xB8004C00,0xC000BC00,0x5C006000,0x11BB15BA,0x10BD14C2,0x0DC111BC,0x0DC311C0,0x09C10DC0,0x07C10BC4,0x06CD0A00,0x05C109C2,0x041A05C0,0x013A0274,0x80008000,
 0x0231033D,0x50007E00,0xB000B400,0xB0004C00,0x54006000,0x1A311ED6,0x183B1D14,0x16B21BC2,0x15EF1A32,0x105515EE,0x0F2D1334,0x0C5D11F6,0x0AE11056,0x07A20AE0,0x02320464,0x80008000,
 0x00030003,0x7FFF7FFF,0x00000000,0x81000000,0x00000000,0x0FFD1FFD,0x00091009,0x00000000,0x00091009,0x1FFF1FFF,0x1FFE1FFE,0x1FFE1FFE,0x1FFE1FFE,0x10041008,0x00040008,0x80008000,
 0x00030003,0x7FFF7FFF,0x00000000,0x00000000,0x00000000,0x0FFD1FFD,0x00091009,0x00000000,0x00091009,0x1FFF1FFF,0x1FFE1FFE,0x1FFE1FFE,0x1FFE1FFE,0x10041008,0x00040008,0x80008000,
 0x00130017,0x4FA870F0,0x4510BCE0,0x8500BEF0,0x54C05F80,0x02AF0371,0x01DF02E5,0x01D702B0,0x026A0358,0x011E01D6,0x00B1012D,0x0059011F,0x00E301A0,0x00400058,0x00140028,0x80008000,
};
```
mode_data index -> PS1 name: 0 dAPF1, 1 dAPF2, 2 vIIR, 3 vCOMB1, 4 vCOMB2, 5 vCOMB3, 6 vCOMB4, 7 vWALL, 8 vAPF1, 9 vAPF2,
10 mLSAME, 11 mRSAME, 12 mLCOMB1, 13 mRCOMB1, 14 mLCOMB2, 15 mRCOMB2, 16 dLSAME, 17 dRSAME, 18 mLDIFF, 19 mRDIFF,
20 mLCOMB3, 21 mRCOMB3, 22 mLCOMB4, 23 mRCOMB4, 24 dLDIFF, 25 dRDIFF, 26 mLAPF1, 27 mRAPF1, 28 mLAPF2, 29 mRAPF2, 30 vLIN, 31 vRIN.
Address entries (0,1,10..29) are in units of 8 bytes = 4 samples (16-bit). Volumes (2..9,30,31) are signed 1.15 (0x8000 = -1.0
as int16; vLIN/vRIN 0x8000 used as gain 1.0 -> treat 0x8000 as magnitude 1.0 for vLIN/vRIN, i.e. use (int16)value with abs for
-32768, or simply 0x7FFF). Work area: EffectSizes[mode] << 4 bytes = EffectSizes[mode] * 8 samples (per channel pair buffer).

## ECHO (7) / DELAY (8): sceSdSetEffectAttr overrides (attr = caller's delay/feedback, 0..127)
```c
u16 delay = ((attr->delay+1) << 5);  u16 feedback = ((attr->feedback << 7) + attr->feedback) << 1;
mode_data[7] = feedback; mode_data[10] = (delay << 1) - mode_data[0]; mode_data[11] = delay - mode_data[1];
mode_data[16] = mode_data[17] + delay; mode_data[12] = mode_data[13] + delay;
mode_data[27] = mode_data[29] + delay; mode_data[26] = mode_data[28] + delay;
```
Depth: EVOLL = depth_L, EVOLR = depth_R (raw signed 1.15).

## Algorithm (psx-spx), one step per 2 output samples (reverb runs at half rate, 24 kHz):
[x] = buffer sample at (pos + x*4) mod size (address entries in samples after *4); [x-2 bytes] = previous sample (x*4 - 1).
```
Lin = in_L*vLIN ; Rin = in_R*vRIN     (in = average of the two 48 kHz wet-input samples)
[mLSAME] = (Lin + [dLSAME]*vWALL - [mLSAME-1])*vIIR + [mLSAME-1]
[mRSAME] = (Rin + [dRSAME]*vWALL - [mRSAME-1])*vIIR + [mRSAME-1]
[mLDIFF] = (Lin + [dRDIFF]*vWALL - [mLDIFF-1])*vIIR + [mLDIFF-1]
[mRDIFF] = (Rin + [dLDIFF]*vWALL - [mRDIFF-1])*vIIR + [mRDIFF-1]
Lout = vCOMB1*[mLCOMB1] + vCOMB2*[mLCOMB2] + vCOMB3*[mLCOMB3] + vCOMB4*[mLCOMB4]   (R likewise with mRCOMBn)
Lout = Lout - vAPF1*[mLAPF1 - dAPF1];  [mLAPF1] = Lout;  Lout = Lout*vAPF1 + [mLAPF1 - dAPF1]
Lout = Lout - vAPF2*[mLAPF2 - dAPF2];  [mLAPF2] = Lout;  Lout = Lout*vAPF2 + [mLAPF2 - dAPF2]   (R likewise)
out_L = Lout*EVOLL ; out_R = Rout*EVOLR ; pos = (pos + 1) mod size
```
All products are (a*b)>>15; every buffer write saturates to int16. Output held for both 48 kHz samples (or linearly
interpolated between steps).
