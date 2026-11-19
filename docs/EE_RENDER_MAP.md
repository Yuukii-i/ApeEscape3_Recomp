# EE Render Map (`0x3A0000` - `0x3C8000`)

Scanned **719** functions in `[0x3A0000, 0x3C8000)`.

## 1. Functions

| Function | Start | Last | Insns | Callees (max 12) | Callers (in set) | Flags |
| --- | --- | --- | ---: | --- | --- | --- |
| sub_003A0028 | 0x3A0028 | 0x3A0034 | 4 | - | sub_003A2D98 | - |
| sub_003A0038 | 0x3A0038 | 0x3A02D4 | 168 | 0x44BD80 | sub_003A07C8, sub_003A13B4 | - |
| sub_003A02D8 | 0x3A02D8 | 0x3A0324 | 20 | 0x359E74 | sub_003A0328, sub_003A2D98, sub_003A3BA8 | - |
| sub_003A0328 | 0x3A0328 | 0x3A05CC | 170 | 0x441F40, sub_003A02D8, 0x441F70 | sub_003A2D98 | - |
| sub_003A05D0 | 0x3A05D0 | 0x3A066C | 40 | - | sub_003A2D98 | - |
| sub_003A0670 | 0x3A0670 | 0x3A06F4 | 34 | - | sub_003A1ED4, sub_003A2558, sub_003A2D98 | - |
| sub_003A06F8 | 0x3A06F8 | 0x3A07C4 | 51 | - | sub_003A1ED4, sub_003A2558, sub_003A2D98 | - |
| sub_003A07C8 | 0x3A07C8 | 0x3A13B0 | 763 | 0x28A31C, 0x28A53C, sub_003AFC08, sub_003B7A00, sub_003B76D0, sub_003B7740, sub_003AFE58, sub_003AFB68, 0x423B08, sub_003AFE00, sub_003B0AA8, sub_003AFD98 ... (+25) | sub_003A3BA8 | VU1CMD 0x15C; VIF 0x0400,0x5000,0x7A60,0x7B20,0x7CC0,0x7F00,0x7F80 |
| sub_003A13B4 | 0x3A13B4 | 0x3A1944 | 356 | sub_003A5AD0, 0x39FF78, 0x441F40, 0x35AB88, sub_003A0038, 0x281870, 0x281994, 0x27F8CC, 0x2410F8, 0x241200, 0x23F4A0, 0x23F6C4 ... (+17) | sub_003A4604 | - |
| sub_003A1948 | 0x3A1948 | 0x3A19C0 | 30 | 0x281870, 0x281994, 0x2801EC, 0x20B944, 0x1651E4, 0x16525C, sub_003A6070 | - | - |
| sub_003A19C4 | 0x3A19C4 | 0x3A1A40 | 31 | 0x281870, 0x281994, 0x2801EC, 0x20B944, 0x1651E4, 0x16525C, sub_003A6070 | - | - |
| sub_003A1A44 | 0x3A1A44 | 0x3A1AC4 | 38 | 0x221644 | - | - |
| sub_003A1AC8 | 0x3A1AC8 | 0x3A1AE8 | 9 | - | - | - |
| sub_003A1AEC | 0x3A1AEC | 0x3A1BE4 | 63 | sub_003A5C60, 0x362178, sub_003A5D04, sub_003A61BC, 0x28FA34 | - | - |
| sub_003A1BE8 | 0x3A1BE8 | 0x3A1C6C | 34 | sub_003A5FA0, sub_003A6A98, 0x362178 | - | - |
| sub_003A1C70 | 0x3A1C70 | 0x3A1DDC | 91 | sub_003A5FF4, 0x441F40, 0x441F70, sub_003A6A98, 0x3622A8 | - | - |
| sub_003A1DE0 | 0x3A1DE0 | 0x3A1ED0 | 60 | 0x20BA94, 0x20BD78, 0x35AB88, 0x362178 | - | - |
| sub_003A1ED4 | 0x3A1ED4 | 0x3A2554 | 415 | 0x29045C, 0x101584, 0x44E280, 0x4FE6DC, 0x46327C, 0x4632AC, 0x4FEA78, 0x462EF0, 0x41A3D8, 0x4748AC, 0x44C3C8, sub_003A0670 ... (+5) | sub_003A2D98 | VU1CMD 0x0A |
| sub_003A2558 | 0x3A2558 | 0x3A2D94 | 524 | 0x29023C, sub_003A06F8, sub_003A0670, 0x2716BC, 0x35AB88, 0x3713F8, 0x362730 | sub_003A2D98 | - |
| sub_003A2D98 | 0x3A2D98 | 0x3A3BA4 | 898 | sub_003A6AF0, sub_003A6224, sub_003A640C, sub_003A6700, sub_003A60C8, sub_003A0028, sub_003A02D8, 0x441F40, 0x44C3C8, 0x359E74, sub_003A5AC4, 0x238F04 ... (+39) | - | - |
| sub_003A3BA8 | 0x3A3BA8 | 0x3A4380 | 501 | 0x441F40, sub_003A02D8, 0x441F70, 0x267F8C, 0x35AB88, 0x26B1E0, 0x1651E4, 0x1652A8, 0x15DF6C, 0x268A50, 0x2460A0, 0x2689F8 ... (+12) | - | - |
| sub_003A4384 | 0x3A4384 | 0x3A4600 | 183 | 0x29023C, 0x441F40, 0x28552C, 0x238BF8, 0x221644, 0x44BE94 | - | - |
| sub_003A4604 | 0x3A4604 | 0x3A4748 | 82 | 0x41B800, sub_003A13B4, 0x619970, 0x42B21C, 0x4EBE68 | sub_003A2D98 | - |
| sub_003A4750 | 0x3A4750 | 0x3A5530 | 887 | 0x619D80, 0x619E94, 0x284178, sub_003AFC08, sub_003B7A00, sub_003B76D0, sub_003B7740, sub_003AFEA8, sub_003AFE58, 0x441F40, 0x41B8B0, 0x44BD80 ... (+7) | sub_003A4750, sub_003A5534 | - |
| sub_003A5534 | 0x3A5534 | 0x3A55EC | 46 | 0x41B800, sub_003A4750, 0x5B7468, 0x619D70, 0x619D2C | - | - |
| sub_003A55F0 | 0x3A55F0 | 0x3A5658 | 26 | 0x5B7468, 0x619D70, 0x619D2C | - | - |
| sub_003A565C | 0x3A565C | 0x3A56BC | 25 | - | - | - |
| sub_003A56C0 | 0x3A56C0 | 0x3A5774 | 42 | - | - | - |
| sub_003A5778 | 0x3A5778 | 0x3A57EC | 30 | - | - | - |
| sub_003A57F4 | 0x3A57F4 | 0x3A58DC | 58 | - | - | - |
| sub_003A58E4 | 0x3A58E4 | 0x3A5980 | 40 | - | sub_003A2D98, sub_003A5AD0 | - |
| sub_003A5988 | 0x3A5988 | 0x3A59BC | 14 | - | - | - |
| sub_003A59C0 | 0x3A59C0 | 0x3A5AB4 | 62 | 0x271764, 0x3714A0 | sub_003A07C8, sub_003A13B4 | - |
| sub_003A5AB8 | 0x3A5AB8 | 0x3A5AC0 | 3 | - | sub_003A2D98 | - |
| sub_003A5AC4 | 0x3A5AC4 | 0x3A5ACC | 3 | - | sub_003A2D98 | - |
| sub_003A5AD0 | 0x3A5AD0 | 0x3A5C24 | 86 | 0x20AE70, 0x4432CC, sub_003A58E4, sub_003A61A4, sub_003A63D0, sub_003A66F4 | sub_003A07C8, sub_003A13B4 | - |
| sub_003A5C28 | 0x3A5C28 | 0x3A5C30 | 3 | - | - | - |
| sub_003A5C34 | 0x3A5C34 | 0x3A5C5C | 11 | - | - | - |
| sub_003A5C60 | 0x3A5C60 | 0x3A5D00 | 41 | 0x44BE58 | sub_003A1AEC | - |
| sub_003A5D04 | 0x3A5D04 | 0x3A5D40 | 17 | sub_003A5EA8 | sub_003A1AEC | - |
| sub_003A5D48 | 0x3A5D48 | 0x3A5D74 | 12 | - | - | - |
| sub_003A5D78 | 0x3A5D78 | 0x3A5DCC | 25 | sub_003A5EA8 | - | - |
| sub_003A5DD4 | 0x3A5DD4 | 0x3A5E00 | 12 | - | - | - |
| sub_003A5E04 | 0x3A5E04 | 0x3A5E18 | 6 | - | - | - |
| sub_003A5E1C | 0x3A5E1C | 0x3A5E58 | 17 | sub_003A5EA8 | sub_003A2D98 | - |
| sub_003A5E60 | 0x3A5E60 | 0x3A5EA4 | 18 | - | - | - |
| sub_003A5EA8 | 0x3A5EA8 | 0x3A5F88 | 56 | 0x1D2814, 0x246F88, 0x1D27D0 | sub_003A07C8, sub_003A13B4, sub_003A5D04, sub_003A5D78, sub_003A5E1C | - |
| sub_003A5F8C | 0x3A5F8C | 0x3A5F9C | 5 | - | sub_003A07C8, sub_003A13B4, sub_003A2D98 | - |
| sub_003A5FA0 | 0x3A5FA0 | 0x3A5FF0 | 21 | 0x362178 | sub_003A1BE8 | - |
| sub_003A5FF4 | 0x3A5FF4 | 0x3A606C | 31 | 0x362178, sub_003A6AE4 | sub_003A1C70 | - |
| sub_003A6070 | 0x3A6070 | 0x3A607C | 4 | - | sub_003A13B4, sub_003A1948, sub_003A19C4 | - |
| sub_003A6080 | 0x3A6080 | 0x3A608C | 4 | - | - | - |
| sub_003A6090 | 0x3A6090 | 0x3A60AC | 8 | - | - | - |
| sub_003A60B0 | 0x3A60B0 | 0x3A60B0 | 1 | - | - | - |
| sub_003A60B8 | 0x3A60B8 | 0x3A60B8 | 1 | - | - | - |
| sub_003A60C0 | 0x3A60C0 | 0x3A60C0 | 1 | - | - | - |
| sub_003A60C8 | 0x3A60C8 | 0x3A61A0 | 55 | - | sub_003A2D98 | - |
| sub_003A61A4 | 0x3A61A4 | 0x3A61B8 | 6 | - | sub_003A5AD0 | - |
| sub_003A61BC | 0x3A61BC | 0x3A6220 | 24 | - | sub_003A1AEC | - |
| sub_003A6224 | 0x3A6224 | 0x3A62A4 | 31 | - | sub_003A2D98 | - |
| sub_003A62AC | 0x3A62AC | 0x3A62B4 | 3 | - | sub_003A3BA8 | - |
| sub_003A62B8 | 0x3A62B8 | 0x3A63CC | 70 | 0x36DA14 | sub_003A3BA8 | - |
| sub_003A63D0 | 0x3A63D0 | 0x3A63EC | 8 | - | sub_003A5AD0 | - |
| sub_003A63F0 | 0x3A63F0 | 0x3A6408 | 7 | - | sub_003A2D98 | - |
| sub_003A640C | 0x3A640C | 0x3A6688 | 160 | 0x35AB88, 0x165518, 0x36252C, 0x36F548 | sub_003A2D98 | - |
| sub_003A668C | 0x3A668C | 0x3A6690 | 2 | - | sub_003A2D98 | - |
| sub_003A6694 | 0x3A6694 | 0x3A66F0 | 24 | - | sub_003A2D98 | - |
| sub_003A66F4 | 0x3A66F4 | 0x3A66FC | 3 | - | sub_003A5AD0 | - |
| sub_003A6700 | 0x3A6700 | 0x3A69E0 | 185 | 0x35AB88, 0x165518, 0x36252C | sub_003A2D98 | - |
| sub_003A69E4 | 0x3A69E4 | 0x3A69F0 | 4 | - | sub_003A07C8, sub_003A13B4 | - |
| sub_003A69F4 | 0x3A69F4 | 0x3A6A30 | 15 | - | sub_003A2D98 | - |
| sub_003A6A38 | 0x3A6A38 | 0x3A6A8C | 22 | - | - | - |
| sub_003A6A90 | 0x3A6A90 | 0x3A6A94 | 2 | - | sub_003A2D98 | - |
| sub_003A6A98 | 0x3A6A98 | 0x3A6AE0 | 19 | 0x35AB88, 0x165578 | sub_003A1BE8, sub_003A1C70 | - |
| sub_003A6AE4 | 0x3A6AE4 | 0x3A6AEC | 3 | - | sub_003A5FF4 | - |
| sub_003A6AF0 | 0x3A6AF0 | 0x3A6B20 | 12 | - | sub_003A2D98 | - |
| sub_003A6B24 | 0x3A6B24 | 0x3A6CCC | 107 | - | sub_003A3BA8 | - |
| sub_003A6CD0 | 0x3A6CD0 | 0x3A6CEC | 8 | - | - | - |
| sub_003A6CF0 | 0x3A6CF0 | 0x3A6CF0 | 1 | - | - | - |
| sub_003A6CF8 | 0x3A6CF8 | 0x3A6CF8 | 1 | - | - | - |
| sub_003A6D00 | 0x3A6D00 | 0x3A6D14 | 6 | - | - | - |
| sub_003A6D18 | 0x3A6D18 | 0x3A6D5C | 18 | - | - | - |
| sub_003A6D60 | 0x3A6D60 | 0x3A6D60 | 1 | - | - | - |
| sub_003A6D68 | 0x3A6D68 | 0x3A6D68 | 1 | - | - | - |
| sub_003A6D70 | 0x3A6D70 | 0x3A6D84 | 6 | - | - | - |
| sub_003A6D88 | 0x3A6D88 | 0x3A6D9C | 6 | - | - | - |
| sub_003A6DA0 | 0x3A6DA0 | 0x3A7020 | 160 | sub_003A8360 | - | - |
| sub_003A7028 | 0x3A7028 | 0x3A703C | 6 | - | - | - |
| sub_003A7040 | 0x3A7040 | 0x3A7084 | 18 | - | - | - |
| sub_003A7088 | 0x3A7088 | 0x3A70BC | 14 | sub_003A8360 | - | - |
| sub_003A70C0 | 0x3A70C0 | 0x3A7164 | 42 | sub_003A8360 | - | - |
| sub_003A7168 | 0x3A7168 | 0x3A7234 | 52 | sub_003A8360 | - | - |
| sub_003A7238 | 0x3A7238 | 0x3A724C | 6 | - | - | - |
| sub_003A7250 | 0x3A7250 | 0x3A72D4 | 34 | - | - | - |
| sub_003A72D8 | 0x3A72D8 | 0x3A7314 | 16 | - | sub_003AEB90, sub_003AED00 | - |
| sub_003A7318 | 0x3A7318 | 0x3A738C | 30 | 0x42C44C | sub_003A7540 | - |
| sub_003A7390 | 0x3A7390 | 0x3A73E4 | 22 | 0x42B0D8 | sub_003A73E8 | - |
| sub_003A73E8 | 0x3A73E8 | 0x3A7494 | 44 | sub_003A7390, sub_003A85E0, sub_003AEB90, sub_003AED00, sub_003A8490 | sub_003A7498 | - |
| sub_003A7498 | 0x3A7498 | 0x3A74D4 | 16 | sub_003A73E8 | - | - |
| sub_003A74D8 | 0x3A74D8 | 0x3A74EC | 6 | - | - | - |
| sub_003A74F0 | 0x3A74F0 | 0x3A753C | 20 | - | - | - |
| sub_003A7540 | 0x3A7540 | 0x3A758C | 20 | sub_003A7318 | - | - |
| sub_003A7590 | 0x3A7590 | 0x3A759C | 4 | - | - | - |
| sub_003A75A0 | 0x3A75A0 | 0x3A761C | 32 | - | - | - |
| sub_003A7620 | 0x3A7620 | 0x3A764C | 12 | 0x42B0D8 | sub_003A7680, sub_003A7860, sub_003A7898 | - |
| sub_003A7650 | 0x3A7650 | 0x3A7660 | 5 | - | sub_003A7680 | - |
| sub_003A7668 | 0x3A7668 | 0x3A767C | 6 | - | sub_003A7680 | - |
| sub_003A7680 | 0x3A7680 | 0x3A785C | 120 | sub_003A7620, sub_003A7668, sub_003A7650 | - | - |
| sub_003A7860 | 0x3A7860 | 0x3A7894 | 14 | sub_003A7620 | - | - |
| sub_003A7898 | 0x3A7898 | 0x3A7BB4 | 200 | sub_003A7620, 0x42C44C, 0x42B0D8 | - | - |
| sub_003A7BB8 | 0x3A7BB8 | 0x3A7C4C | 37 | sub_003A7BB8 | sub_003A7BB8, sub_003A7D08 | - |
| sub_003A7C50 | 0x3A7C50 | 0x3A7D04 | 46 | sub_003A7C50 | sub_003A7C50, sub_003A7D08 | - |
| sub_003A7D08 | 0x3A7D08 | 0x3A813C | 260 | sub_003A7BB8, sub_003A7C50 | - | - |
| sub_003A8140 | 0x3A8140 | 0x3A8144 | 2 | - | - | - |
| sub_003A8148 | 0x3A8148 | 0x3A823C | 60 | 0x42C44C | - | - |
| sub_003A8240 | 0x3A8240 | 0x3A833C | 62 | 0x42C44C | - | - |
| sub_003A8340 | 0x3A8340 | 0x3A835C | 8 | - | - | - |
| sub_003A8360 | 0x3A8360 | 0x3A8404 | 41 | 0x42C44C | sub_003A6DA0, sub_003A7088, sub_003A70C0, sub_003A7168, sub_003A8960, sub_003A8C90, sub_003AA608, sub_003AA8E8, sub_003AAB38 | - |
| sub_003A8408 | 0x3A8408 | 0x3A8478 | 29 | - | sub_003A8490, sub_003A85E0 | - |
| sub_003A8480 | 0x3A8480 | 0x3A8480 | 1 | - | - | - |
| sub_003A8488 | 0x3A8488 | 0x3A8488 | 1 | - | - | - |
| sub_003A8490 | 0x3A8490 | 0x3A85DC | 94 | sub_003A8408, sub_003A8490 | sub_003A73E8, sub_003A8490 | - |
| sub_003A85E0 | 0x3A85E0 | 0x3A8704 | 86 | sub_003A8408, sub_003A85E0 | sub_003A73E8, sub_003A85E0 | - |
| sub_003A8708 | 0x3A8708 | 0x3A8708 | 1 | - | - | - |
| sub_003A8710 | 0x3A8710 | 0x3A8710 | 1 | - | - | - |
| sub_003A8718 | 0x3A8718 | 0x3A8718 | 1 | - | - | - |
| sub_003A8720 | 0x3A8720 | 0x3A8720 | 1 | - | - | - |
| sub_003A8728 | 0x3A8728 | 0x3A8728 | 1 | - | - | - |
| sub_003A8730 | 0x3A8730 | 0x3A87BC | 33 | - | - | - |
| sub_003A87C0 | 0x3A87C0 | 0x3A87D0 | 5 | - | - | - |
| sub_003A87D8 | 0x3A87D8 | 0x3A884C | 29 | - | - | - |
| sub_003A8850 | 0x3A8850 | 0x3A8850 | 1 | - | - | - |
| sub_003A8858 | 0x3A8858 | 0x3A8944 | 57 | - | - | - |
| sub_003A8948 | 0x3A8948 | 0x3A8958 | 5 | - | - | - |
| sub_003A8960 | 0x3A8960 | 0x3A8B64 | 129 | sub_003A8360 | - | - |
| sub_003A8B68 | 0x3A8B68 | 0x3A8B68 | 1 | - | - | - |
| sub_003A8B70 | 0x3A8B70 | 0x3A8BD4 | 25 | - | - | - |
| sub_003A8BD8 | 0x3A8BD8 | 0x3A8BD8 | 1 | - | - | - |
| sub_003A8BE0 | 0x3A8BE0 | 0x3A8C44 | 25 | - | - | - |
| sub_003A8C48 | 0x3A8C48 | 0x3A8C58 | 5 | - | - | - |
| sub_003A8C60 | 0x3A8C60 | 0x3A8C70 | 5 | - | - | - |
| sub_003A8C78 | 0x3A8C78 | 0x3A8C88 | 5 | - | - | - |
| sub_003A8C90 | 0x3A8C90 | 0x3A9084 | 253 | sub_003A8360 | - | - |
| sub_003A9088 | 0x3A9088 | 0x3A9098 | 5 | - | - | - |
| sub_003A90A0 | 0x3A90A0 | 0x3A9134 | 37 | - | - | - |
| sub_003A9138 | 0x3A9138 | 0x3A9138 | 1 | - | - | - |
| sub_003A9140 | 0x3A9140 | 0x3A9140 | 1 | - | - | - |
| sub_003A9148 | 0x3A9148 | 0x3A926C | 72 | - | - | - |
| sub_003A9270 | 0x3A9270 | 0x3A927C | 4 | - | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740, sub_003B69D8, sub_003B6CF0, sub_003B6FE0, sub_003B7220, sub_003B7460 | - |
| sub_003A9280 | 0x3A9280 | 0x3A92FC | 32 | - | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740, sub_003B69D8, sub_003B6CF0, sub_003B6FE0, sub_003B7220, sub_003B7460 | - |
| sub_003A9300 | 0x3A9300 | 0x3A93A4 | 40 | - | sub_003B5048 | - |
| sub_003A93A8 | 0x3A93A8 | 0x3A93B8 | 5 | - | - | - |
| sub_003A93C0 | 0x3A93C0 | 0x3A93D0 | 5 | - | - | - |
| sub_003A93D8 | 0x3A93D8 | 0x3A93D8 | 1 | - | - | - |
| sub_003A93E0 | 0x3A93E0 | 0x3A93E0 | 1 | - | - | - |
| sub_003A93E8 | 0x3A93E8 | 0x3A941C | 14 | - | - | - |
| sub_003A9420 | 0x3A9420 | 0x3A9420 | 1 | - | - | - |
| sub_003A9428 | 0x3A9428 | 0x3A9428 | 1 | - | - | - |
| sub_003A9430 | 0x3A9430 | 0x3A9434 | 2 | - | sub_003AF1B8, sub_003AF2D8 | - |
| sub_003A9438 | 0x3A9438 | 0x3A9444 | 4 | - | sub_003AF1B8, sub_003AF2D8 | - |
| sub_003A9448 | 0x3A9448 | 0x3A9454 | 4 | - | sub_003AF1B8, sub_003AF2D8 | - |
| sub_003A9458 | 0x3A9458 | 0x3A9464 | 4 | - | sub_003AF1B8, sub_003AF2D8 | - |
| sub_003A9468 | 0x3A9468 | 0x3A9474 | 4 | - | sub_003AF278, sub_003AF3B8 | - |
| sub_003A9478 | 0x3A9478 | 0x3A9484 | 4 | - | sub_003AF278, sub_003AF3B8 | - |
| sub_003A9488 | 0x3A9488 | 0x3A9488 | 1 | - | - | - |
| sub_003A9490 | 0x3A9490 | 0x3A9490 | 1 | - | - | - |
| sub_003A9498 | 0x3A9498 | 0x3A94AC | 6 | - | - | - |
| sub_003A94B0 | 0x3A94B0 | 0x3A94B0 | 1 | - | - | - |
| sub_003A94B8 | 0x3A94B8 | 0x3A94B8 | 1 | - | - | - |
| sub_003A94C0 | 0x3A94C0 | 0x3A94C4 | 2 | - | sub_003BBF80 | - |
| sub_003A94C8 | 0x3A94C8 | 0x3A94D4 | 4 | - | sub_003BBF80 | - |
| sub_003A94D8 | 0x3A94D8 | 0x3A94E8 | 5 | - | - | - |
| sub_003A94F0 | 0x3A94F0 | 0x3A9564 | 29 | - | - | - |
| sub_003A9568 | 0x3A9568 | 0x3A9568 | 1 | - | - | - |
| sub_003A9570 | 0x3A9570 | 0x3A95D4 | 25 | - | - | - |
| sub_003A95D8 | 0x3A95D8 | 0x3A95D8 | 1 | - | - | - |
| sub_003A95E0 | 0x3A95E0 | 0x3A95E0 | 1 | - | - | - |
| sub_003A95E8 | 0x3A95E8 | 0x3A95E8 | 1 | - | - | - |
| sub_003A95F0 | 0x3A95F0 | 0x3A965C | 25 | - | - | - |
| sub_003A9660 | 0x3A9660 | 0x3A966C | 4 | - | sub_003AF1B8, sub_003AF278, sub_003AF2D8, sub_003AF3B8 | - |
| sub_003A9670 | 0x3A9670 | 0x3A967C | 4 | - | sub_003AF1B8, sub_003AF278, sub_003AF2D8, sub_003AF3B8 | - |
| sub_003A9680 | 0x3A9680 | 0x3A968C | 4 | - | sub_003BBF80 | - |
| sub_003A9690 | 0x3A9690 | 0x3A96FC | 28 | - | sub_003BBF80 | - |
| sub_003A9700 | 0x3A9700 | 0x3A9710 | 5 | - | - | - |
| sub_003A9718 | 0x3A9718 | 0x3A9728 | 5 | - | - | - |
| sub_003A9730 | 0x3A9730 | 0x3A975C | 12 | - | sub_003B4E80 | - |
| sub_003A9760 | 0x3A9760 | 0x3A976C | 4 | - | sub_003B4E80 | - |
| sub_003A9770 | 0x3A9770 | 0x3A98D4 | 88 | - | sub_003B4E80 | - |
| sub_003A98D8 | 0x3A98D8 | 0x3A98D8 | 1 | - | - | - |
| sub_003A98E0 | 0x3A98E0 | 0x3A98E0 | 1 | - | - | - |
| sub_003A98E8 | 0x3A98E8 | 0x3A9A00 | 70 | - | - | - |
| sub_003A9A08 | 0x3A9A08 | 0x3A9A0C | 2 | - | sub_003AEB90 | - |
| sub_003A9A10 | 0x3A9A10 | 0x3A9A1C | 4 | - | sub_003AEB90 | - |
| sub_003A9A20 | 0x3A9A20 | 0x3A9A2C | 4 | - | sub_003AEB90 | - |
| sub_003A9A30 | 0x3A9A30 | 0x3A9A3C | 4 | - | sub_003AEB90 | - |
| sub_003A9A40 | 0x3A9A40 | 0x3A9A50 | 5 | - | - | - |
| sub_003A9A58 | 0x3A9A58 | 0x3A9A68 | 5 | - | - | - |
| sub_003A9A70 | 0x3A9A70 | 0x3A9A80 | 5 | - | - | - |
| sub_003A9A88 | 0x3A9A88 | 0x3A9A98 | 5 | - | - | - |
| sub_003A9AA0 | 0x3A9AA0 | 0x3A9AA0 | 1 | - | - | - |
| sub_003A9AA8 | 0x3A9AA8 | 0x3A9AA8 | 1 | - | - | - |
| sub_003A9AB0 | 0x3A9AB0 | 0x3A9AB0 | 1 | - | - | - |
| sub_003A9AB8 | 0x3A9AB8 | 0x3A9AB8 | 1 | - | - | - |
| sub_003A9AC0 | 0x3A9AC0 | 0x3A9AC0 | 1 | - | - | - |
| sub_003A9AC8 | 0x3A9AC8 | 0x3A9B4C | 33 | - | - | - |
| sub_003A9B50 | 0x3A9B50 | 0x3A9B60 | 5 | - | - | - |
| sub_003A9B68 | 0x3A9B68 | 0x3A9B78 | 5 | - | - | - |
| sub_003A9B80 | 0x3A9B80 | 0x3A9B90 | 5 | - | - | - |
| sub_003A9B98 | 0x3A9B98 | 0x3A9C2C | 37 | - | - | - |
| sub_003A9C30 | 0x3A9C30 | 0x3A9C30 | 1 | - | - | - |
| sub_003A9C38 | 0x3A9C38 | 0x3A9C38 | 1 | - | - | - |
| sub_003A9C40 | 0x3A9C40 | 0x3A9C40 | 1 | - | - | - |
| sub_003A9C48 | 0x3A9C48 | 0x3A9CCC | 33 | - | - | - |
| sub_003A9CD0 | 0x3A9CD0 | 0x3A9CD0 | 1 | - | - | - |
| sub_003A9CD8 | 0x3A9CD8 | 0x3A9E34 | 85 | - | - | - |
| sub_003A9E38 | 0x3A9E38 | 0x3A9E38 | 1 | - | - | - |
| sub_003A9E40 | 0x3A9E40 | 0x3A9E40 | 1 | - | - | - |
| sub_003A9E48 | 0x3A9E48 | 0x3A9E48 | 1 | - | - | - |
| sub_003A9E50 | 0x3A9E50 | 0x3A9EB4 | 25 | - | - | - |
| sub_003A9EB8 | 0x3A9EB8 | 0x3A9EB8 | 1 | - | - | - |
| sub_003A9EC0 | 0x3A9EC0 | 0x3A9EC0 | 1 | - | - | - |
| sub_003A9EC8 | 0x3A9EC8 | 0x3A9EC8 | 1 | - | - | - |
| sub_003A9ED0 | 0x3A9ED0 | 0x3A9ED0 | 1 | - | - | - |
| sub_003A9ED8 | 0x3A9ED8 | 0x3A9ED8 | 1 | - | - | - |
| sub_003A9EE0 | 0x3A9EE0 | 0x3A9EE0 | 1 | - | - | - |
| sub_003A9EE8 | 0x3A9EE8 | 0x3A9F1C | 14 | - | - | - |
| sub_003A9F20 | 0x3A9F20 | 0x3A9F20 | 1 | - | - | - |
| sub_003A9F28 | 0x3A9F28 | 0x3A9F28 | 1 | - | - | - |
| sub_003A9F30 | 0x3A9F30 | 0x3A9F84 | 22 | - | - | - |
| sub_003A9F88 | 0x3A9F88 | 0x3A9F88 | 1 | - | - | - |
| sub_003A9F90 | 0x3A9F90 | 0x3A9F90 | 1 | - | - | - |
| sub_003A9F98 | 0x3A9F98 | 0x3A9FAC | 6 | - | - | - |
| sub_003A9FB0 | 0x3A9FB0 | 0x3A9FB0 | 1 | - | - | - |
| sub_003A9FB8 | 0x3A9FB8 | 0x3AA03C | 33 | - | - | - |
| sub_003AA040 | 0x3AA040 | 0x3AA040 | 1 | - | - | - |
| sub_003AA048 | 0x3AA048 | 0x3AA0AC | 25 | - | - | - |
| sub_003AA0B0 | 0x3AA0B0 | 0x3AA0B0 | 1 | - | - | - |
| sub_003AA0B8 | 0x3AA0B8 | 0x3AA0B8 | 1 | - | - | - |
| sub_003AA0C0 | 0x3AA0C0 | 0x3AA0D4 | 6 | - | - | - |
| sub_003AA0D8 | 0x3AA0D8 | 0x3AA0D8 | 1 | - | - | - |
| sub_003AA0E0 | 0x3AA0E0 | 0x3AA0E0 | 1 | - | - | - |
| sub_003AA0E8 | 0x3AA0E8 | 0x3AA0FC | 6 | - | - | - |
| sub_003AA100 | 0x3AA100 | 0x3AA100 | 1 | - | - | - |
| sub_003AA108 | 0x3AA108 | 0x3AA108 | 1 | - | - | - |
| sub_003AA110 | 0x3AA110 | 0x3AA110 | 1 | - | - | - |
| sub_003AA118 | 0x3AA118 | 0x3AA118 | 1 | - | - | - |
| sub_003AA120 | 0x3AA120 | 0x3AA120 | 1 | - | - | - |
| sub_003AA128 | 0x3AA128 | 0x3AA128 | 1 | - | - | - |
| sub_003AA130 | 0x3AA130 | 0x3AA144 | 6 | - | - | - |
| sub_003AA148 | 0x3AA148 | 0x3AA148 | 1 | - | - | - |
| sub_003AA150 | 0x3AA150 | 0x3AA150 | 1 | - | - | - |
| sub_003AA158 | 0x3AA158 | 0x3AA158 | 1 | - | - | - |
| sub_003AA160 | 0x3AA160 | 0x3AA160 | 1 | - | - | - |
| sub_003AA168 | 0x3AA168 | 0x3AA168 | 1 | - | - | - |
| sub_003AA170 | 0x3AA170 | 0x3AA170 | 1 | - | - | - |
| sub_003AA178 | 0x3AA178 | 0x3AA1CC | 22 | - | - | - |
| sub_003AA1D0 | 0x3AA1D0 | 0x3AA1D0 | 1 | - | - | - |
| sub_003AA1D8 | 0x3AA1D8 | 0x3AA1D8 | 1 | - | - | - |
| sub_003AA1E0 | 0x3AA1E0 | 0x3AA1F4 | 6 | - | - | - |
| sub_003AA1F8 | 0x3AA1F8 | 0x3AA1F8 | 1 | - | - | - |
| sub_003AA200 | 0x3AA200 | 0x3AA200 | 1 | - | - | - |
| sub_003AA208 | 0x3AA208 | 0x3AA23C | 14 | - | - | - |
| sub_003AA240 | 0x3AA240 | 0x3AA240 | 1 | - | - | - |
| sub_003AA248 | 0x3AA248 | 0x3AA248 | 1 | - | - | - |
| sub_003AA250 | 0x3AA250 | 0x3AA284 | 14 | - | - | - |
| sub_003AA288 | 0x3AA288 | 0x3AA288 | 1 | - | - | - |
| sub_003AA290 | 0x3AA290 | 0x3AA290 | 1 | - | - | - |
| sub_003AA298 | 0x3AA298 | 0x3AA5F4 | 214 | - | - | - |
| sub_003AA5F8 | 0x3AA5F8 | 0x3AA5F8 | 1 | - | - | - |
| sub_003AA600 | 0x3AA600 | 0x3AA600 | 1 | - | - | - |
| sub_003AA608 | 0x3AA608 | 0x3AA71C | 70 | sub_003A8360 | - | - |
| sub_003AA720 | 0x3AA720 | 0x3AA720 | 1 | - | - | - |
| sub_003AA728 | 0x3AA728 | 0x3AA728 | 1 | - | - | - |
| sub_003AA730 | 0x3AA730 | 0x3AA730 | 1 | - | - | - |
| sub_003AA738 | 0x3AA738 | 0x3AA738 | 1 | - | - | - |
| sub_003AA740 | 0x3AA740 | 0x3AA740 | 1 | - | - | - |
| sub_003AA748 | 0x3AA748 | 0x3AA8CC | 95 | - | - | - |
| sub_003AA8D0 | 0x3AA8D0 | 0x3AA8E0 | 5 | - | - | - |
| sub_003AA8E8 | 0x3AA8E8 | 0x3AAA0C | 73 | sub_003A8360 | - | - |
| sub_003AAA10 | 0x3AAA10 | 0x3AAA10 | 1 | - | - | - |
| sub_003AAA18 | 0x3AAA18 | 0x3AAA9C | 33 | - | - | - |
| sub_003AAAA0 | 0x3AAAA0 | 0x3AAAA0 | 1 | - | - | - |
| sub_003AAAA8 | 0x3AAAA8 | 0x3AAB2C | 33 | - | - | - |
| sub_003AAB30 | 0x3AAB30 | 0x3AAB30 | 1 | - | - | - |
| sub_003AAB38 | 0x3AAB38 | 0x3AAE6C | 205 | sub_003A8360 | - | - |
| sub_003AAE70 | 0x3AAE70 | 0x3AB7A4 | 587 | sub_003AC068, sub_003ABF68, sub_003AB7A8, sub_003AAE70 | sub_003AAE70 | - |
| sub_003AB7A8 | 0x3AB7A8 | 0x3AB82C | 34 | sub_003AC370, sub_003BD3F8 | sub_003AAE70 | - |
| sub_003AB830 | 0x3AB830 | 0x3AB92C | 63 | sub_003ACA70, sub_003BD338 | - | - |
| sub_003AB930 | 0x3AB930 | 0x3AB94C | 8 | - | sub_003ABAA8, sub_003ABBD0 | - |
| sub_003AB950 | 0x3AB950 | 0x3AB97C | 12 | - | sub_003ABAA8, sub_003ABBD0 | - |
| sub_003AB980 | 0x3AB980 | 0x3ABA1C | 39 | - | - | - |
| sub_003ABA20 | 0x3ABA20 | 0x3ABA5C | 18 | - | - | - |
| sub_003ABA60 | 0x3ABA60 | 0x3ABAA4 | 20 | - | - | - |
| sub_003ABAA8 | 0x3ABAA8 | 0x3ABBCC | 74 | sub_003AB950, sub_003AB930 | sub_003ABDB8, sub_003ABF68 | - |
| sub_003ABBD0 | 0x3ABBD0 | 0x3ABDB4 | 122 | sub_003AB950, sub_003AB930 | sub_003ABDB8 | - |
| sub_003ABDB8 | 0x3ABDB8 | 0x3ABE5C | 42 | sub_003ABBD0, sub_003ABAA8 | sub_003ABE60 | - |
| sub_003ABE60 | 0x3ABE60 | 0x3ABF64 | 71 | sub_003ABDB8 | sub_003ABF68 | - |
| sub_003ABF68 | 0x3ABF68 | 0x3AC064 | 64 | sub_003ABAA8, sub_003ABE60 | sub_003AAE70 | - |
| sub_003AC068 | 0x3AC068 | 0x3AC150 | 57 | - | sub_003AAE70 | - |
| sub_003AC158 | 0x3AC158 | 0x3AC1CC | 30 | - | sub_003ACA70 | - |
| sub_003AC1D0 | 0x3AC1D0 | 0x3AC254 | 33 | 0x41D628, 0x41D490 | sub_003ACA70 | - |
| sub_003AC258 | 0x3AC258 | 0x3AC2F4 | 39 | sub_003BDEB0, 0x41D490, 0x41D3D8 | sub_003ACA70 | - |
| sub_003AC2F8 | 0x3AC2F8 | 0x3AC340 | 18 | - | sub_003AC4B0, sub_003AC690 | - |
| sub_003AC348 | 0x3AC348 | 0x3AC36C | 10 | - | sub_003AC690, sub_003ACA70 | - |
| sub_003AC370 | 0x3AC370 | 0x3AC4AC | 80 | 0x41D628, 0x41D490 | sub_003AB7A8 | - |
| sub_003AC4B0 | 0x3AC4B0 | 0x3AC68C | 118 | 0x41D628, 0x41D490, sub_003AC2F8, sub_003BDCC0, sub_003BDDE0 | - | - |
| sub_003AC690 | 0x3AC690 | 0x3AC7DC | 83 | sub_003AC2F8, sub_003BDDE0, sub_003AC348, 0x41D628, 0x41D490, sub_003BDCC0, sub_003BDD38 | sub_003AC910 | - |
| sub_003AC7E0 | 0x3AC7E0 | 0x3AC90C | 76 | 0x41D628, 0x41D490 | sub_003AC910 | - |
| sub_003AC910 | 0x3AC910 | 0x3ACA6C | 86 | sub_003AC690, sub_003AC7E0 | - | - |
| sub_003ACA70 | 0x3ACA70 | 0x3ACF9C | 332 | sub_003BDDC8, sub_003AC348, sub_003AC158, sub_003AC1D0, sub_003BDD38, sub_003BDCC0, sub_003AC258, 0x41D490, 0x41D3D8 | sub_003AB830 | - |
| sub_003ACFA0 | 0x3ACFA0 | 0x3ACFB4 | 6 | - | sub_003AD608 | - |
| sub_003ACFB8 | 0x3ACFB8 | 0x3ACFD8 | 10 | - | sub_003AD2B0, sub_003AD608 | - |
| sub_003ACFE0 | 0x3ACFE0 | 0x3ACFE4 | 2 | - | - | - |
| sub_003ACFE8 | 0x3ACFE8 | 0x3ACFEC | 2 | - | - | - |
| sub_003ACFF0 | 0x3ACFF0 | 0x3ACFF4 | 2 | - | - | - |
| sub_003ACFF8 | 0x3ACFF8 | 0x3ACFFC | 2 | - | - | - |
| sub_003AD000 | 0x3AD000 | 0x3AD004 | 2 | - | - | - |
| sub_003AD008 | 0x3AD008 | 0x3AD008 | 1 | - | - | - |
| sub_003AD010 | 0x3AD010 | 0x3AD014 | 2 | - | - | - |
| sub_003AD018 | 0x3AD018 | 0x3AD038 | 10 | - | sub_003AD2B0, sub_003ADD08, sub_003B9758 | - |
| sub_003AD040 | 0x3AD040 | 0x3AD044 | 2 | - | - | - |
| sub_003AD048 | 0x3AD048 | 0x3AD04C | 2 | - | - | - |
| sub_003AD050 | 0x3AD050 | 0x3AD054 | 2 | - | - | - |
| sub_003AD058 | 0x3AD058 | 0x3AD05C | 2 | - | - | - |
| sub_003AD060 | 0x3AD060 | 0x3AD060 | 1 | - | - | - |
| sub_003AD068 | 0x3AD068 | 0x3AD06C | 2 | - | - | - |
| sub_003AD070 | 0x3AD070 | 0x3AD094 | 11 | - | sub_003AD608 | - |
| sub_003AD09C | 0x3AD09C | 0x3AD0A8 | 4 | - | - | - |
| sub_003AD0AC | 0x3AD0AC | 0x3AD0F4 | 19 | - | - | - |
| sub_003AD0F8 | 0x3AD0F8 | 0x3AD2AC | 110 | - | sub_003ADEC0 | VU1CMD 0x0E; VIF 0x1000,0x5000; DMA |
| sub_003AD2B0 | 0x3AD2B0 | 0x3AD604 | 214 | sub_003ACFB8, sub_003AD018 | sub_003ADEC0 | VU1CMD 0x0E; VIF 0x1000,0x5000; DMA |
| sub_003AD608 | 0x3AD608 | 0x3ADCA4 | 424 | sub_003ADCA8, sub_003B9AA0, sub_003B9B00, sub_003B9B88, sub_003ACFB8, sub_003AD070, sub_003ACFA0 | - | VU1CMD 0x0A |
| sub_003ADCA8 | 0x3ADCA8 | 0x3ADCD4 | 12 | - | sub_003AD608, sub_003AE808 | - |
| sub_003ADCD8 | 0x3ADCD8 | 0x3ADD04 | 12 | - | sub_003ADD08, sub_003AE868 | - |
| sub_003ADD08 | 0x3ADD08 | 0x3ADEBC | 110 | sub_003ADCD8, sub_003B9AA0, sub_003B9C20, sub_003AD018 | - | VU1CMD 0x0A |
| sub_003ADEC0 | 0x3ADEC0 | 0x3AE704 | 528 | sub_003AD0F8, sub_003AD2B0, sub_003AFD98, sub_003AFE58, sub_003B3B40 | sub_003B85B8 | VIF 0x1400,0x6C01,0x7200,0x7210,0x7240 |
| sub_003AE708 | 0x3AE708 | 0x3AE72C | 10 | - | sub_003B85B8 | - |
| sub_003AE730 | 0x3AE730 | 0x3AE804 | 54 | - | - | - |
| sub_003AE808 | 0x3AE808 | 0x3AE864 | 23 | 0x42B320, sub_003ADCA8 | - | - |
| sub_003AE868 | 0x3AE868 | 0x3AE8FC | 37 | 0x42B320, sub_003ADCD8, sub_003BD2C0 | - | - |
| sub_003AE900 | 0x3AE900 | 0x3AEA14 | 70 | sub_003B3CE0, sub_003B3D80, sub_003AEA18, sub_003B3D88 | - | - |
| sub_003AEA18 | 0x3AEA18 | 0x3AEB8C | 94 | - | sub_003AE900 | VU1CMD 0x0A,0x0E; VIF 0x0100,0x1400,0x6000 |
| sub_003AEB90 | 0x3AEB90 | 0x3AECFC | 90 | sub_003A72D8, sub_003A9A10, sub_003A9A08, sub_003B42D0, sub_003A9A30, sub_003A9A20 | sub_003A73E8 | - |
| sub_003AED00 | 0x3AED00 | 0x3AEEA4 | 106 | sub_003A72D8, 0x42C44C | sub_003A73E8 | - |
| sub_003AEEA8 | 0x3AEEA8 | 0x3AEF04 | 24 | - | - | - |
| sub_003AEF08 | 0x3AEF08 | 0x3AEFCC | 50 | - | - | VU0 |
| sub_003AEFD0 | 0x3AEFD0 | 0x3AF084 | 45 | - | - | - |
| sub_003AF088 | 0x3AF088 | 0x3AF1B4 | 76 | - | - | - |
| sub_003AF1B8 | 0x3AF1B8 | 0x3AF274 | 44 | sub_003A9670, sub_003A9660, sub_003A9438, sub_003A9430, sub_003A9458, sub_003A9448 | - | - |
| sub_003AF278 | 0x3AF278 | 0x3AF2D4 | 22 | sub_003A9670, sub_003A9660, sub_003A9478, sub_003A9468 | - | - |
| sub_003AF2D8 | 0x3AF2D8 | 0x3AF3B4 | 52 | sub_003A9670, sub_003A9660, sub_003A9438, sub_003A9430, sub_003A9458, sub_003A9448 | - | - |
| sub_003AF3B8 | 0x3AF3B8 | 0x3AF424 | 26 | sub_003A9670, sub_003A9660, sub_003A9478, sub_003A9468 | - | - |
| sub_003AF428 | 0x3AF428 | 0x3AF474 | 20 | sub_003BD2C0 | - | - |
| sub_003AF478 | 0x3AF478 | 0x3AF52C | 46 | sub_003B3CE0, sub_003BDF08 | sub_003AF8F0 | - |
| sub_003AF530 | 0x3AF530 | 0x3AF5FC | 52 | sub_003B3CE0, sub_003BDF08 | sub_003AF8F0 | - |
| sub_003AF600 | 0x3AF600 | 0x3AF67C | 32 | sub_003B3CE0, 0x42B16C | sub_003AF8F0 | - |
| sub_003AF680 | 0x3AF680 | 0x3AF6F4 | 30 | sub_003B3CE0, 0x42B16C | sub_003AF8F0 | - |
| sub_003AF6F8 | 0x3AF6F8 | 0x3AF8A4 | 108 | sub_003B3CE0, sub_003BDF08, 0x41D3D8, 0x41D490 | sub_003AF8F0 | - |
| sub_003AF8A8 | 0x3AF8A8 | 0x3AF8B4 | 4 | - | sub_003AF8F0 | - |
| sub_003AF8B8 | 0x3AF8B8 | 0x3AF8EC | 14 | - | sub_003AF8F0 | - |
| sub_003AF8F0 | 0x3AF8F0 | 0x3AF9C4 | 54 | sub_003B3CE0, sub_003AF8B8, sub_003AF8A8, sub_003AF478, sub_003AF680, sub_003AF6F8, sub_003AF530, sub_003AF600 | - | - |
| sub_003AF9C8 | 0x3AF9C8 | 0x3AF9F4 | 12 | - | sub_003B7EC0, sub_003B80F0, sub_003B8288 | - |
| sub_003AF9F8 | 0x3AF9F8 | 0x3AFA24 | 12 | - | sub_003AFA98, sub_003B81A8, sub_003B8220 | - |
| sub_003AFA28 | 0x3AFA28 | 0x3AFA4C | 10 | - | sub_003B7DF0, sub_003B8448 | - |
| sub_003AFA50 | 0x3AFA50 | 0x3AFA94 | 18 | - | sub_003B8288, sub_003B8380, sub_003B8448 | - |
| sub_003AFA98 | 0x3AFA98 | 0x3AFAE4 | 20 | sub_003AF9F8 | sub_003B7EC0 | - |
| sub_003AFAE8 | 0x3AFAE8 | 0x3AFB24 | 16 | - | sub_003B4178 | - |
| sub_003AFB28 | 0x3AFB28 | 0x3AFB3C | 6 | - | sub_003B7A00 | - |
| sub_003AFB40 | 0x3AFB40 | 0x3AFB64 | 10 | - | sub_003B7A00 | - |
| sub_003AFB68 | 0x3AFB68 | 0x3AFB8C | 10 | - | sub_003A07C8, sub_003AFE00, sub_003BB8E8 | - |
| sub_003AFB90 | 0x3AFB90 | 0x3AFC04 | 30 | sub_003B99B8 | sub_003B3E28 | - |
| sub_003AFC08 | 0x3AFC08 | 0x3AFC24 | 8 | - | sub_003A07C8, sub_003A4750, sub_003B7CB0 | - |
| sub_003AFC28 | 0x3AFC28 | 0x3AFD94 | 92 | sub_003B40F8, sub_003B3CE0 | sub_003B7A00 | - |
| sub_003AFD98 | 0x3AFD98 | 0x3AFDD4 | 16 | - | sub_003A07C8, sub_003ADEC0, sub_003B2D30, sub_003B2D90, sub_003B2EA8, sub_003B4818, sub_003B4A60, sub_003B57C0, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740 ... (+10) | - |
| sub_003AFDD8 | 0x3AFDD8 | 0x3AFDFC | 10 | - | sub_003AFE58, sub_003AFFA0, sub_003B0098, sub_003B0800, sub_003B0A48, sub_003B0AA8, sub_003B0B78, sub_003B0C50, sub_003B0E40, sub_003B0F70, sub_003B1048 | VIF 0x1100,0x5000 |
| sub_003AFE00 | 0x3AFE00 | 0x3AFE54 | 22 | sub_003AFB68 | sub_003A07C8 | - |
| sub_003AFE58 | 0x3AFE58 | 0x3AFEA4 | 20 | sub_003AFDD8 | sub_003A07C8, sub_003A4750, sub_003ADEC0, sub_003AFFA0 | VU1CMD 0x0E |
| sub_003AFEA8 | 0x3AFEA8 | 0x3AFED4 | 12 | - | sub_003A4750, sub_003B2EA8 | VIF 0x5000 |
| sub_003AFED8 | 0x3AFED8 | 0x3AFF04 | 12 | - | sub_003B2EA8 | VIF 0x5000 |
| sub_003AFF08 | 0x3AFF08 | 0x3AFF38 | 15 | - | sub_003AFFA0 | - |
| sub_003AFF40 | 0x3AFF40 | 0x3AFF40 | 1 | - | - | - |
| sub_003AFF44 | 0x3AFF44 | 0x3AFF74 | 13 | - | - | - |
| sub_003AFF78 | 0x3AFF78 | 0x3AFF7C | 2 | - | - | - |
| sub_003AFF80 | 0x3AFF80 | 0x3AFF84 | 2 | - | - | - |
| sub_003AFF88 | 0x3AFF88 | 0x3AFF9C | 6 | - | - | - |
| sub_003AFFA0 | 0x3AFFA0 | 0x3B0044 | 42 | sub_003AFF08, sub_003AFE58, sub_003AFDD8 | sub_003B93D8 | VU1CMD 0x11 |
| sub_003B0048 | 0x3B0048 | 0x3B0094 | 20 | sub_003BDD98, sub_003BDD38, sub_003BDF40 | sub_003B0098, sub_003B0800 | - |
| sub_003B0098 | 0x3B0098 | 0x3B07FC | 474 | sub_003BDDB0, sub_003BDF30, sub_003B0098, sub_003B0048, sub_003AFDD8, sub_003BDF40 | sub_003B0098, sub_003B0800 | VU1CMD 0x0A; VIF 0x0535 |
| sub_003B0800 | 0x3B0800 | 0x3B0A44 | 146 | sub_003BDF40, sub_003B0098, sub_003B0048, sub_003AFDD8, sub_003BDC30 | - | - |
| sub_003B0A48 | 0x3B0A48 | 0x3B0AA4 | 24 | sub_003AFDD8 | - | VU1CMD 0x11 |
| sub_003B0AA8 | 0x3B0AA8 | 0x3B0B74 | 52 | sub_003AFDD8 | sub_003A07C8 | - |
| sub_003B0B78 | 0x3B0B78 | 0x3B0C4C | 54 | sub_003AFDD8 | - | - |
| sub_003B0C50 | 0x3B0C50 | 0x3B0E3C | 124 | sub_003AFDD8 | - | VIF 0x5151 |
| sub_003B0E40 | 0x3B0E40 | 0x3B0F6C | 76 | sub_003AFDD8 | sub_003B2618, sub_003B2AE0 | VU1CMD 0x11 |
| sub_003B0F70 | 0x3B0F70 | 0x3B1044 | 54 | sub_003AFDD8 | sub_003B2618 | - |
| sub_003B1048 | 0x3B1048 | 0x3B11CC | 98 | sub_003AFDD8 | sub_003B2618 | VU1CMD 0x11 |
| sub_003B11D0 | 0x3B11D0 | 0x3B1204 | 14 | - | sub_003B2618, sub_003B2AE0 | - |
| sub_003B1208 | 0x3B1208 | 0x3B122C | 10 | - | sub_003B2618 | - |
| sub_003B1230 | 0x3B1230 | 0x3B1244 | 6 | - | - | - |
| sub_003B1248 | 0x3B1248 | 0x3B18B4 | 411 | sub_003BDC40, sub_003BD2F0 | sub_003B2618, sub_003B2AE0 | VU1CMD 0x15,0x190; VIF 0x0100,0x0320,0x1000,0x1400,0x6001,0x6002,0x6500,0x6600,0x6C00,0x6C02,0x6C09,0x7C50; DMA |
| sub_003B18B8 | 0x3B18B8 | 0x3B1C14 | 216 | sub_003B18B8, sub_003BDC50, sub_003B1C18 | sub_003B18B8, sub_003B1C18 | VIF 0x0100,0x0320,0x1000,0x1400,0x5000,0x6000,0x6500,0x6600,0x6C00; DMA |
| sub_003B1C18 | 0x3B1C18 | 0x3B241C | 513 | sub_003B18B8, sub_003BDC50, sub_003B1C18 | sub_003B18B8, sub_003B1C18 | VIF 0x0100,0x0320,0x1000,0x1400,0x6000,0x6500,0x6600,0x6C00,0x7C00; DMA |
| sub_003B2420 | 0x3B2420 | 0x3B2444 | 10 | - | sub_003A4750 | - |
| sub_003B2448 | 0x3B2448 | 0x3B2464 | 8 | - | - | - |
| sub_003B2468 | 0x3B2468 | 0x3B2490 | 11 | - | sub_003B2498 | - |
| sub_003B2498 | 0x3B2498 | 0x3B2614 | 96 | sub_003B2468, sub_003BD3F8 | sub_003B2618, sub_003B2AE0 | - |
| sub_003B2618 | 0x3B2618 | 0x3B2ADC | 306 | sub_003B7738, sub_003BAF48, sub_003BAF58, sub_003BAF68, sub_003BD690, sub_003BD368, sub_003BD2E0, sub_003B2498, sub_003BD930, sub_003B1248, sub_003B1208, sub_003B11D0 ... (+3) | - | - |
| sub_003B2AE0 | 0x3B2AE0 | 0x3B2D2C | 146 | sub_003B11D0, sub_003B7738, sub_003BAF48, sub_003BAF58, sub_003BAF68, sub_003BD690, sub_003BD368, sub_003B2498, sub_003BD930, sub_003B1248, sub_003B0E40 | sub_003B2F98 | - |
| sub_003B2D30 | 0x3B2D30 | 0x3B2D8C | 24 | sub_003AFD98, sub_003BDC50 | sub_003B2E28 | VIF 0x1000,0x6C03; DMA |
| sub_003B2D90 | 0x3B2D90 | 0x3B2E24 | 38 | sub_003AFD98, sub_003BDC30, sub_003B7738, sub_003BAF78 | - | VIF 0x1000,0x6C01; DMA |
| sub_003B2E28 | 0x3B2E28 | 0x3B2EA4 | 32 | sub_003B7738, sub_003BAF78, sub_003BDC50, sub_003BDCC0, sub_003B2D30 | - | - |
| sub_003B2EA8 | 0x3B2EA8 | 0x3B2F8C | 57 | sub_003B7730, sub_003AFEA8, sub_003AFED8, sub_003AFD98 | - | VIF 0x0100,0x6C02 |
| sub_003B2F90 | 0x3B2F90 | 0x3B2F94 | 2 | - | - | - |
| sub_003B2F98 | 0x3B2F98 | 0x3B346C | 310 | sub_003BD2E0, 0x41D3D8, 0x41D490, sub_003B2AE0, sub_003BD690, sub_003BD2F0, 0x404230 | - | VU1CMD 0x0A,0x0E; VIF 0x0100,0x1000,0x1400,0x6001,0x6C02; DMA |
| sub_003B3470 | 0x3B3470 | 0x3B363C | 116 | sub_003BDAD8, sub_003B3B40, sub_003BE5F8, 0x404230, 0x412CB0, 0x413280, 0x412FE0, sub_003B3B00 | - | VIF 0x1000,0x7000; DMA |
| sub_003B3640 | 0x3B3640 | 0x3B3654 | 6 | - | - | VIF 0x7000 |
| sub_003B3658 | 0x3B3658 | 0x3B367C | 10 | sub_003B7DF0 | - | - |
| sub_003B3680 | 0x3B3680 | 0x3B373C | 48 | - | sub_003B3E28 | - |
| sub_003B3740 | 0x3B3740 | 0x3B381C | 56 | sub_003B8448 | sub_003B3E28 | - |
| sub_003B3820 | 0x3B3820 | 0x3B3AFC | 183 | sub_003B81A8, sub_003B85B8, sub_003B9758, sub_003B99B8, sub_003B3C58, 0x412CB0, 0x413280, 0x412FE0 | sub_003B3D98 | VU1CMD 0x0E; VIF 0x1000,0x1100,0x5000; DMA |
| sub_003B3B00 | 0x3B3B00 | 0x3B3B3C | 16 | - | sub_003B3470 | - |
| sub_003B3B40 | 0x3B3B40 | 0x3B3C0C | 52 | - | sub_003ADEC0, sub_003B3470 | VIF 0x1000; DMA |
| sub_003B3C10 | 0x3B3C10 | 0x3B3C54 | 17 | - | - | - |
| sub_003B3C58 | 0x3B3C58 | 0x3B3C5C | 2 | - | sub_003B3820 | - |
| sub_003B3C60 | 0x3B3C60 | 0x3B3CDC | 32 | - | - | - |
| sub_003B3CE0 | 0x3B3CE0 | 0x3B3D1C | 16 | - | sub_003AE900, sub_003AF478, sub_003AF530, sub_003AF600, sub_003AF680, sub_003AF6F8, sub_003AF8F0, sub_003AFC28, sub_003B4088, sub_003B40F8, sub_003B7A00, sub_003BAF98 ... (+1) | - |
| sub_003B3D20 | 0x3B3D20 | 0x3B3D4C | 11 | sub_003B3D80 | - | - |
| sub_003B3D50 | 0x3B3D50 | 0x3B3D7C | 12 | - | - | - |
| sub_003B3D80 | 0x3B3D80 | 0x3B3D84 | 2 | - | sub_003AE900, sub_003B3D20, sub_003B3D98, sub_003B4818, sub_003B4A60, sub_003B5900, sub_003B69D8, sub_003B6CF0, sub_003B90B0, sub_003B9158, sub_003B93D8, sub_003BAF98 ... (+1) | - |
| sub_003B3D88 | 0x3B3D88 | 0x3B3D94 | 4 | - | sub_003AE900, sub_003B3D98, sub_003B4818, sub_003B4A60, sub_003B5900, sub_003B69D8, sub_003B6CF0, sub_003B90B0, sub_003B9158, sub_003B93D8, sub_003BAF98, sub_003BB8E8 | - |
| sub_003B3D98 | 0x3B3D98 | 0x3B3E24 | 36 | sub_003B3D80, sub_003B3820, sub_003B3D88, sub_003B9310 | sub_003B3E28 | - |
| sub_003B3E28 | 0x3B3E28 | 0x3B400C | 121 | sub_003B8FE0, sub_003B3680, sub_003AFB90, sub_003B89D0, sub_003B3D98, sub_003B3740, sub_003B40F8 | - | - |
| sub_003B4010 | 0x3B4010 | 0x3B4084 | 29 | sub_003BE5F8, sub_003B8288, sub_003B93D8 | - | - |
| sub_003B4088 | 0x3B4088 | 0x3B40F4 | 28 | sub_003B3CE0, sub_003B7CB0, sub_003B94A8 | - | GIF |
| sub_003B40F8 | 0x3B40F8 | 0x3B416C | 30 | sub_003B3CE0, sub_003B9018 | sub_003AFC28, sub_003B3E28, sub_003B7A00, sub_003B7CB0 | - |
| sub_003B4170 | 0x3B4170 | 0x3B4174 | 2 | - | - | - |
| sub_003B4178 | 0x3B4178 | 0x3B428C | 70 | 0x42B320, sub_003AFAE8 | - | - |
| sub_003B4290 | 0x3B4290 | 0x3B42CC | 15 | - | sub_003B4818, sub_003B4A60 | VIF 0x1001 |
| sub_003B42D0 | 0x3B42D0 | 0x3B45E4 | 196 | sub_003BA090, sub_003BA680, sub_003BA7D8 | sub_003AEB90 | VIF 0x0100,0x6000,0x6500 |
| sub_003B45E8 | 0x3B45E8 | 0x3B4814 | 139 | sub_003BD690, sub_003BA898, sub_003B4E80, sub_003B4818, sub_003B4A60, 0x413280 | - | VIF 0x1000; DMA |
| sub_003B4818 | 0x3B4818 | 0x3B4A5C | 145 | sub_003BD690, sub_003BA898, sub_003B3D80, sub_003AFD98, sub_003BD498, sub_003BD2F0, sub_003BD538, sub_003BD648, sub_003B4290, sub_003B3D88, sub_003B5048 | sub_003B45E8 | VU1CMD 0x11,0x190; VIF 0x0100,0x1400,0x6C10,0x7000 |
| sub_003B4A60 | 0x3B4A60 | 0x3B4E7C | 261 | sub_003BA908, sub_003B3D80, sub_003AFD98, sub_003BD498, sub_003BD2F0, sub_003BD538, sub_003BD648, sub_003B4290, sub_003B3D88, sub_003B5508, sub_003B5368 | sub_003B45E8 | VU1CMD 0x11,0x190; VIF 0x0100,0x1400,0x6C10,0x7000; VU0 |
| sub_003B4E80 | 0x3B4E80 | 0x3B5044 | 113 | sub_003A9730, sub_003A9760, sub_003A9770, sub_003B9D38 | sub_003B45E8 | - |
| sub_003B5048 | 0x3B5048 | 0x3B5364 | 200 | sub_003A9300, sub_003BD690, sub_003BA898, sub_003BBB50, sub_003A9270, sub_003A9280, sub_003B8840, sub_003B57C0, sub_003B5890, sub_003B8898, sub_003B62C0, sub_003B6508 ... (+2) | sub_003B4818 | VIF 0x5000 |
| sub_003B5368 | 0x3B5368 | 0x3B5504 | 104 | sub_003BBB50, sub_003B69D8, sub_003B6CF0, sub_003B5900 | sub_003B4A60 | - |
| sub_003B5508 | 0x3B5508 | 0x3B57BC | 174 | sub_003BBB50, sub_003A9270, sub_003A9280, sub_003B8840, sub_003B57C0, sub_003B5890, sub_003B8898, sub_003B6FE0, sub_003B7220, sub_003B7460, sub_003B5900 | sub_003B4A60 | VIF 0x5000 |
| sub_003B57C0 | 0x3B57C0 | 0x3B588C | 52 | sub_003AFD98, sub_003BD2E0 | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B6CF0 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x6002,0x6C03 |
| sub_003B5890 | 0x3B5890 | 0x3B58F8 | 27 | - | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B69D8, sub_003B6CF0 | VIF 0x5000 |
| sub_003B5900 | 0x3B5900 | 0x3B62BC | 621 | sub_003A9270, sub_003A9280, sub_003B8840, sub_003B8898, sub_003B3D80, sub_003B3D88, sub_003B57C0, sub_003B5890, sub_003B8740, sub_003AFD98, sub_003BD2E0, sub_003B8780 ... (+9) | sub_003B5048, sub_003B5368, sub_003B5508 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6000,0x6002,0x6500,0x6C03; GIF |
| sub_003B62C0 | 0x3B62C0 | 0x3B6504 | 146 | sub_003A9270, sub_003A9280, sub_003B8840, sub_003BD690, sub_003BA898, sub_003AFD98, sub_003BD2E0, sub_003B8898 | sub_003B5048 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03 |
| sub_003B6508 | 0x3B6508 | 0x3B673C | 142 | sub_003A9270, sub_003A9280, sub_003BD368, sub_003BAC00, sub_003B8840, sub_003AFD98, sub_003BD2E0, sub_003B8898 | sub_003B5048 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF |
| sub_003B6740 | 0x3B6740 | 0x3B69D4 | 166 | sub_003A9270, sub_003A9280, sub_003BD690, sub_003BA898, sub_003BAC00, sub_003B8840, sub_003AFD98, sub_003BD2E0, sub_003B8898, sub_003BD368 | sub_003B5048 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF |
| sub_003B69D8 | 0x3B69D8 | 0x3B6CEC | 198 | sub_003A9270, sub_003A9280, sub_003B8840, sub_003B8898, sub_003B3D80, sub_003BA090, sub_003BA2A0, sub_003BA7D8, sub_003B3D88, sub_003B8740, sub_003AFD98, sub_003BD2E0 ... (+2) | sub_003B5368 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6000,0x6002,0x6C03 |
| sub_003B6CF0 | 0x3B6CF0 | 0x3B6FDC | 188 | sub_003A9270, sub_003A9280, sub_003B3D80, sub_003BA090, sub_003BA2A0, sub_003BA5F8, sub_003BD368, sub_003BAC00, sub_003BA7D8, sub_003B3D88, sub_003B8840, sub_003B57C0 ... (+2) | sub_003B5368 | VIF 0x5000,0x6000; GIF |
| sub_003B6FE0 | 0x3B6FE0 | 0x3B721C | 144 | sub_003A9270, sub_003A9280, sub_003B8840, sub_003BD690, sub_003BA898, sub_003AFD98, sub_003BD2E0, sub_003B8898 | sub_003B5508 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03 |
| sub_003B7220 | 0x3B7220 | 0x3B745C | 144 | sub_003A9270, sub_003A9280, sub_003BD368, sub_003BAC00, sub_003B8840, sub_003AFD98, sub_003BD2E0, sub_003B8898 | sub_003B5508 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF |
| sub_003B7460 | 0x3B7460 | 0x3B76CC | 156 | sub_003A9270, sub_003A9280, sub_003BD690, sub_003BA898, sub_003BAC00, sub_003B8840, sub_003AFD98, sub_003BD2E0, sub_003B8898 | sub_003B5508 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF |
| sub_003B76D0 | 0x3B76D0 | 0x3B76E4 | 6 | - | sub_003A07C8, sub_003A4750 | - |
| sub_003B76E8 | 0x3B76E8 | 0x3B76F4 | 4 | - | - | - |
| sub_003B76F8 | 0x3B76F8 | 0x3B7704 | 4 | - | - | - |
| sub_003B7708 | 0x3B7708 | 0x3B772C | 10 | - | - | - |
| sub_003B7730 | 0x3B7730 | 0x3B7734 | 2 | - | sub_003B2EA8 | - |
| sub_003B7738 | 0x3B7738 | 0x3B773C | 2 | - | sub_003B2618, sub_003B2AE0, sub_003B2D90, sub_003B2E28 | - |
| sub_003B7740 | 0x3B7740 | 0x3B7794 | 22 | - | sub_003A07C8, sub_003A4750 | GIF |
| sub_003B7798 | 0x3B7798 | 0x3B781C | 34 | - | sub_003A07C8, sub_003A4750 | GIF |
| sub_003B7820 | 0x3B7820 | 0x3B783C | 8 | - | - | - |
| sub_003B7840 | 0x3B7840 | 0x3B788C | 20 | - | - | - |
| sub_003B7890 | 0x3B7890 | 0x3B78AC | 8 | - | - | - |
| sub_003B78B0 | 0x3B78B0 | 0x3B794C | 40 | - | - | - |
| sub_003B7950 | 0x3B7950 | 0x3B79FC | 44 | sub_003B7A00 | sub_003BBB50 | - |
| sub_003B7A00 | 0x3B7A00 | 0x3B7CAC | 172 | sub_003AFB40, sub_003B3CE0, sub_003AFC28, sub_003AFB28, sub_003B40F8, sub_003B94A8, sub_003B7CB0 | sub_003A07C8, sub_003A4750, sub_003B7950, sub_003B7CB0 | GIF |
| sub_003B7CB0 | 0x3B7CB0 | 0x3B7DEC | 80 | sub_003B40F8, sub_003B86A0, sub_003B9708, sub_003AFC08, sub_003B7A00 | sub_003B4088, sub_003B7A00 | - |
| sub_003B7DF0 | 0x3B7DF0 | 0x3B7E84 | 38 | sub_003B7EC0, sub_003B7E88, sub_003AFA28 | sub_003B3658 | - |
| sub_003B7E88 | 0x3B7E88 | 0x3B7EBC | 14 | - | sub_003B7DF0, sub_003B8448 | - |
| sub_003B7EC0 | 0x3B7EC0 | 0x3B7F14 | 22 | sub_003AF9C8, sub_003AFA98 | sub_003B7DF0, sub_003B80F0, sub_003B8288 | - |
| sub_003B7F18 | 0x3B7F18 | 0x3B7FB8 | 40 | - | sub_003B80F0 | - |
| sub_003B7FC0 | 0x3B7FC0 | 0x3B80E8 | 70 | - | sub_003B80F0 | VIF 0x7FFF |
| sub_003B80F0 | 0x3B80F0 | 0x3B81A4 | 45 | sub_003B7F18, sub_003B7FC0, sub_003B7EC0, sub_003AF9C8 | sub_003B8380 | - |
| sub_003B81A8 | 0x3B81A8 | 0x3B821C | 30 | sub_003AF9F8 | sub_003B3820 | - |
| sub_003B8220 | 0x3B8220 | 0x3B8284 | 26 | sub_003AF9F8 | sub_003B8380 | - |
| sub_003B8288 | 0x3B8288 | 0x3B837C | 62 | sub_003AF9C8, sub_003AFA50, sub_003B7EC0 | sub_003B4010, sub_003B8380 | - |
| sub_003B8380 | 0x3B8380 | 0x3B8444 | 50 | sub_003B8220, sub_003AFA50, sub_003B80F0, sub_003B8288 | sub_003B8448 | VU1CMD 0x11 |
| sub_003B8448 | 0x3B8448 | 0x3B85B4 | 90 | sub_003B8380, sub_003AFA50, sub_003B7E88, sub_003AFA28 | sub_003B3740 | - |
| sub_003B85B8 | 0x3B85B8 | 0x3B869C | 58 | sub_003ADEC0, sub_003AE708 | sub_003B3820 | - |
| sub_003B86A0 | 0x3B86A0 | 0x3B873C | 40 | - | sub_003B7CB0, sub_003B9018 | - |
| sub_003B8740 | 0x3B8740 | 0x3B877C | 16 | - | sub_003B5900, sub_003B69D8 | - |
| sub_003B8780 | 0x3B8780 | 0x3B883C | 48 | - | sub_003B5900, sub_003B69D8 | - |
| sub_003B8840 | 0x3B8840 | 0x3B8894 | 22 | - | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740, sub_003B69D8, sub_003B6CF0, sub_003B6FE0, sub_003B7220, sub_003B7460 | - |
| sub_003B8898 | 0x3B8898 | 0x3B89CC | 78 | - | sub_003B5048, sub_003B5508, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740, sub_003B69D8, sub_003B6CF0, sub_003B6FE0, sub_003B7220, sub_003B7460 | - |
| sub_003B89D0 | 0x3B89D0 | 0x3B8A14 | 17 | - | sub_003B3E28 | - |
| sub_003B8A18 | 0x3B8A18 | 0x3B8A54 | 14 | - | sub_003B8A98 | - |
| sub_003B8A58 | 0x3B8A58 | 0x3B8A90 | 14 | - | sub_003B8A98 | - |
| sub_003B8A98 | 0x3B8A98 | 0x3B8CC4 | 138 | sub_003B8A58, sub_003B8A18 | sub_003B8FE0 | VIF 0x7000 |
| sub_003B8CC8 | 0x3B8CC8 | 0x3B8F54 | 164 | - | sub_003B8FE0 | VIF 0x7000 |
| sub_003B8F58 | 0x3B8F58 | 0x3B8F5C | 2 | - | - | - |
| sub_003B8F60 | 0x3B8F60 | 0x3B8F74 | 6 | - | - | - |
| sub_003B8F78 | 0x3B8F78 | 0x3B8FDC | 29 | - | sub_003B9310 | - |
| sub_003B8FE0 | 0x3B8FE0 | 0x3B9014 | 12 | sub_003B8CC8, sub_003B8A98 | sub_003B3E28 | - |
| sub_003B9018 | 0x3B9018 | 0x3B9084 | 28 | sub_003B86A0 | sub_003B40F8 | - |
| sub_003B9088 | 0x3B9088 | 0x3B90A4 | 8 | sub_003B9310 | - | - |
| sub_003B90A8 | 0x3B90A8 | 0x3B90AC | 2 | - | - | - |
| sub_003B90B0 | 0x3B90B0 | 0x3B9154 | 42 | sub_003B3D80, sub_003B3D88 | - | VIF 0x5000 |
| sub_003B9158 | 0x3B9158 | 0x3B9254 | 64 | sub_003B3D80, sub_003B3D88 | - | VIF 0x5000 |
| sub_003B9258 | 0x3B9258 | 0x3B926C | 6 | - | - | - |
| sub_003B9270 | 0x3B9270 | 0x3B92B4 | 18 | - | - | - |
| sub_003B92B8 | 0x3B92B8 | 0x3B92DC | 9 | sub_003BE598 | - | - |
| sub_003B92E0 | 0x3B92E0 | 0x3B930C | 14 | - | - | - |
| sub_003B9310 | 0x3B9310 | 0x3B93D4 | 57 | sub_003B94F0, sub_003B8F78 | sub_003B3D98, sub_003B9088, sub_003B93D8 | - |
| sub_003B93D8 | 0x3B93D8 | 0x3B94A4 | 61 | sub_003B3D80, sub_003AFFA0, sub_003B3D88, sub_003B9310 | sub_003B4010 | - |
| sub_003B94A8 | 0x3B94A8 | 0x3B94EC | 18 | - | sub_003B4088, sub_003B7A00 | - |
| sub_003B94F0 | 0x3B94F0 | 0x3B9704 | 134 | 0x42CE60, 0x42C5A8 | sub_003B9310 | - |
| sub_003B9708 | 0x3B9708 | 0x3B9754 | 20 | - | sub_003B7CB0 | - |
| sub_003B9758 | 0x3B9758 | 0x3B99B4 | 149 | sub_003AD018 | sub_003B3820 | VU1CMD 0x0E |
| sub_003B99B8 | 0x3B99B8 | 0x3B9A9C | 57 | - | sub_003AFB90, sub_003B3820 | VU1CMD 0x0E |
| sub_003B9AA0 | 0x3B9AA0 | 0x3B9AFC | 23 | - | sub_003AD608, sub_003ADD08 | - |
| sub_003B9B00 | 0x3B9B00 | 0x3B9B44 | 21 | - | sub_003AD608 | - |
| sub_003B9B4C | 0x3B9B4C | 0x3B9B4C | 1 | - | - | - |
| sub_003B9B50 | 0x3B9B50 | 0x3B9B84 | 14 | - | - | - |
| sub_003B9B88 | 0x3B9B88 | 0x3B9C1C | 35 | - | sub_003AD608 | - |
| sub_003B9C20 | 0x3B9C20 | 0x3B9C44 | 9 | - | sub_003ADD08 | - |
| sub_003B9C48 | 0x3B9C48 | 0x3B9D34 | 58 | sub_003B9C48 | sub_003B9C48, sub_003B9D78 | - |
| sub_003B9D38 | 0x3B9D38 | 0x3B9D74 | 16 | - | sub_003B4E80 | - |
| sub_003B9D78 | 0x3B9D78 | 0x3B9E1C | 41 | sub_003B9C48 | sub_003B9E60, sub_003B9ED8 | - |
| sub_003B9E20 | 0x3B9E20 | 0x3B9E5C | 16 | - | sub_003BCC50 | - |
| sub_003B9E60 | 0x3B9E60 | 0x3B9ED4 | 30 | sub_003B9D78 | sub_003BA0C8 | - |
| sub_003B9ED8 | 0x3B9ED8 | 0x3B9FA4 | 52 | sub_003B9D78 | sub_003BA0C8 | - |
| sub_003B9FA8 | 0x3B9FA8 | 0x3BA008 | 23 | - | sub_003BA0C8, sub_003BA2A0 | - |
| sub_003BA010 | 0x3BA010 | 0x3BA08C | 31 | - | sub_003BA0C8 | - |
| sub_003BA090 | 0x3BA090 | 0x3BA0C4 | 14 | - | sub_003B42D0, sub_003B5900, sub_003B69D8, sub_003B6CF0 | - |
| sub_003BA0C8 | 0x3BA0C8 | 0x3BA264 | 102 | sub_003BE5F8, sub_003B9E60, sub_003B9FA8, sub_003BA010, sub_003B9ED8 | sub_003B5900 | - |
| sub_003BA268 | 0x3BA268 | 0x3BA29C | 13 | - | sub_003BA2A0 | - |
| sub_003BA2A0 | 0x3BA2A0 | 0x3BA5F4 | 210 | sub_003B9FA8, sub_003BA268 | sub_003B5900, sub_003B69D8, sub_003B6CF0 | VIF 0x1001,0x7000; VU0 |
| sub_003BA5F8 | 0x3BA5F8 | 0x3BA67C | 33 | - | sub_003B5900, sub_003B6CF0 | - |
| sub_003BA680 | 0x3BA680 | 0x3BA718 | 37 | - | sub_003B42D0 | - |
| sub_003BA71C | 0x3BA71C | 0x3BA7D4 | 46 | - | - | - |
| sub_003BA7D8 | 0x3BA7D8 | 0x3BA894 | 47 | - | sub_003B42D0, sub_003B5900, sub_003B69D8, sub_003B6CF0 | VIF 0x0100,0x6C00 |
| sub_003BA898 | 0x3BA898 | 0x3BA904 | 27 | - | sub_003B45E8, sub_003B4818, sub_003B5048, sub_003B5900, sub_003B62C0, sub_003B6740, sub_003B6FE0, sub_003B7460, sub_003BA908 | VU0 |
| sub_003BA908 | 0x3BA908 | 0x3BAABC | 110 | sub_003BA898 | sub_003B4A60 | - |
| sub_003BAAC0 | 0x3BAAC0 | 0x3BABF8 | 78 | - | - | - |
| sub_003BAC00 | 0x3BAC00 | 0x3BAC3C | 15 | - | sub_003B5900, sub_003B6508, sub_003B6740, sub_003B6CF0, sub_003B7220, sub_003B7460 | - |
| sub_003BAC40 | 0x3BAC40 | 0x3BAE4C | 131 | - | sub_003BAF98 | - |
| sub_003BAE50 | 0x3BAE50 | 0x3BAF44 | 62 | sub_003BD450, sub_003BD498, sub_003BD690 | sub_003BAF98 | - |
| sub_003BAF48 | 0x3BAF48 | 0x3BAF54 | 4 | - | sub_003B2618, sub_003B2AE0 | - |
| sub_003BAF58 | 0x3BAF58 | 0x3BAF64 | 4 | - | sub_003B2618, sub_003B2AE0 | - |
| sub_003BAF68 | 0x3BAF68 | 0x3BAF74 | 4 | - | sub_003B2618, sub_003B2AE0 | - |
| sub_003BAF78 | 0x3BAF78 | 0x3BAF84 | 4 | - | sub_003B2D90, sub_003B2E28 | - |
| sub_003BAF88 | 0x3BAF88 | 0x3BAF94 | 4 | - | sub_003BAF98 | - |
| sub_003BAF98 | 0x3BAF98 | 0x3BB834 | 552 | sub_003B3CE0, sub_003BD2F0, sub_003BAC40, sub_003BD690, sub_003BAF88, sub_003BB838, sub_003BAE50, sub_003BD538, sub_003BD498, sub_003BD3C8, sub_003B3D80, sub_003AFD98 ... (+3) | - | VU1CMD 0x0A,0x0E,0x11,0x190; VIF 0x0100,0x1400,0x6002,0x6C06,0x6C0A |
| sub_003BB838 | 0x3BB838 | 0x3BB874 | 16 | - | sub_003BAF98 | - |
| sub_003BB878 | 0x3BB878 | 0x3BB8E4 | 24 | - | sub_003BD048 | - |
| sub_003BB8E8 | 0x3BB8E8 | 0x3BBB0C | 138 | sub_003B3D80, sub_003BBDC8, sub_003B3D88, sub_003AFB68, sub_003AFD98, sub_003BBF80, sub_003BC278, sub_003BC770, sub_003BCC50 | sub_003BBB50 | VU1CMD 0x11; VIF 0x0100,0x6002,0x6401,0x6C06 |
| sub_003BBB10 | 0x3BBB10 | 0x3BBB24 | 6 | - | sub_003BBB50 | - |
| sub_003BBB28 | 0x3BBB28 | 0x3BBB4C | 10 | - | sub_003BBB50 | - |
| sub_003BBB50 | 0x3BBB50 | 0x3BBDC4 | 158 | sub_003BBB28, sub_003B3CE0, sub_003B7950, sub_003BB8E8, sub_003BBB10 | sub_003B5048, sub_003B5368, sub_003B5508 | - |
| sub_003BBDC8 | 0x3BBDC8 | 0x3BBF7C | 110 | sub_003BD2F0, sub_003BDC30, sub_003AFD98 | sub_003BB8E8 | VU1CMD 0x0A,0x0E,0x190; VIF 0x0100,0x1400,0x6002,0x6C00 |
| sub_003BBF80 | 0x3BBF80 | 0x3BC274 | 190 | sub_003BD048, sub_003BD238, sub_003A9690, sub_003A9680, sub_003A94C8, sub_003A94C0, sub_003AFD98 | sub_003BB8E8 | VU1CMD 0x0A,0x0E,0x11,0x190; VIF 0x0100,0x1400,0x6002,0x6C00 |
| sub_003BC278 | 0x3BC278 | 0x3BC76C | 318 | sub_003AFD98, sub_003BD398, sub_003BD498 | sub_003BB8E8 | VU1CMD 0x39,0xC8,0x108,0x212,0x2BC,0x2E4; VIF 0x0100,0x1400,0x6001,0x6C00,0x6C08 |
| sub_003BC770 | 0x3BC770 | 0x3BCC4C | 312 | sub_003BD690 | sub_003BB8E8 | VU1CMD 0x320,0x398,0x39B; VIF 0x0100,0x1000,0x1400,0x6000; DMA |
| sub_003BCC50 | 0x3BCC50 | 0x3BD044 | 254 | sub_003B9E20, sub_003BD3E0, sub_003BD398, 0x41D490, 0x41D3D8, 0x42B320, sub_003BD690, sub_003AFD98 | sub_003BB8E8 | VU1CMD 0x389,0x3DC,0x3DE; VIF 0x0100,0x6003,0x6C00 |
| sub_003BD048 | 0x3BD048 | 0x3BD234 | 123 | sub_003BB878 | sub_003BBF80 | VU1CMD 0x0A |
| sub_003BD238 | 0x3BD238 | 0x3BD264 | 14 | - | sub_003BBF80 | - |
| sub_003BD26C | 0x3BD26C | 0x3BD26C | 1 | - | - | - |
| sub_003BD270 | 0x3BD270 | 0x3BD2A4 | 13 | - | - | - |
| sub_003BD2A8 | 0x3BD2A8 | 0x3BD2AC | 2 | - | - | - |
| sub_003BD2B0 | 0x3BD2B0 | 0x3BD2B4 | 2 | - | - | - |
| sub_003BD2B8 | 0x3BD2B8 | 0x3BD2BC | 2 | - | - | - |
| sub_003BD2C0 | 0x3BD2C0 | 0x3BD2DC | 8 | - | sub_003AE868, sub_003AF428 | - |
| sub_003BD2E0 | 0x3BD2E0 | 0x3BD2EC | 4 | - | sub_003B2618, sub_003B2F98, sub_003B57C0, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740, sub_003B69D8, sub_003B6FE0, sub_003B7220, sub_003B7460, sub_003BAF98 ... (+3) | - |
| sub_003BD2F0 | 0x3BD2F0 | 0x3BD314 | 10 | - | sub_003B1248, sub_003B2F98, sub_003B4818, sub_003B4A60, sub_003BAF98, sub_003BBDC8 | - |
| sub_003BD318 | 0x3BD318 | 0x3BD334 | 8 | - | sub_003BD690, sub_003BD760, sub_003BD7E8, sub_003BD930 | - |
| sub_003BD338 | 0x3BD338 | 0x3BD364 | 12 | - | sub_003AB830, sub_003BFF00, sub_003C0488, sub_003C0A70, sub_003C0B38, sub_003C0C00, sub_003C2B88, sub_003C3008, sub_003C3588, sub_003C36C8, sub_003C3910, sub_003C4008 | - |
| sub_003BD368 | 0x3BD368 | 0x3BD394 | 12 | - | sub_003B2618, sub_003B2AE0, sub_003B5900, sub_003B6508, sub_003B6740, sub_003B6CF0, sub_003B7220, sub_003BD930 | - |
| sub_003BD398 | 0x3BD398 | 0x3BD3AC | 6 | - | sub_003BC278, sub_003BCC50, sub_003BE9F0, sub_003C28D8, sub_003C3588, sub_003C36C8, sub_003C3910, sub_003C4008 | - |
| sub_003BD3B0 | 0x3BD3B0 | 0x3BD3C4 | 6 | - | sub_003BF9A0, sub_003BFF00, sub_003C0488, sub_003C0A70, sub_003C0B38, sub_003C0C00, sub_003C1030, sub_003C1470, sub_003C1D18, sub_003C2548, sub_003C28D8, sub_003C2B88 ... (+5) | - |
| sub_003BD3C8 | 0x3BD3C8 | 0x3BD3DC | 6 | - | sub_003BAF98 | - |
| sub_003BD3E0 | 0x3BD3E0 | 0x3BD3F4 | 6 | - | sub_003BCC50 | - |
| sub_003BD3F8 | 0x3BD3F8 | 0x3BD44C | 22 | - | sub_003AB7A8, sub_003B2498 | - |
| sub_003BD450 | 0x3BD450 | 0x3BD46C | 8 | - | sub_003BAE50, sub_003BD930, sub_003C3E40, sub_003C3EC8, sub_003C4008 | - |
| sub_003BD470 | 0x3BD470 | 0x3BD494 | 9 | - | sub_003BFF00, sub_003C0488, sub_003C0A70, sub_003C0B38, sub_003C0C00, sub_003C1030, sub_003C1470, sub_003C2548, sub_003C28D8, sub_003C2B88, sub_003C3008, sub_003C3588 ... (+2) | - |
| sub_003BD498 | 0x3BD498 | 0x3BD4FC | 26 | - | sub_003B4818, sub_003B4A60, sub_003BAE50, sub_003BAF98, sub_003BC278, sub_003BD930, sub_003C28D8, sub_003C2B88, sub_003C3008 | - |
| sub_003BD500 | 0x3BD500 | 0x3BD534 | 13 | - | sub_003BD930 | - |
| sub_003BD538 | 0x3BD538 | 0x3BD644 | 68 | - | sub_003B4818, sub_003B4A60, sub_003BAF98, sub_003BD930, sub_003BF9A0 | - |
| sub_003BD648 | 0x3BD648 | - | 0 | - | sub_003B4818, sub_003B4A60 | - |
| sub_003BD690 | 0x3BD690 | 0x3BD75C | 51 | sub_003BD318, 0x41D3D8, 0x41D490, sub_003BD690 | sub_003B2618, sub_003B2AE0, sub_003B2F98, sub_003B45E8, sub_003B4818, sub_003B5048, sub_003B5900, sub_003B62C0, sub_003B6740, sub_003B6FE0, sub_003B7460, sub_003BAE50 ... (+7) | VU0 |
| sub_003BD760 | 0x3BD760 | 0x3BD7E4 | 34 | sub_003BD318, 0x41D3D8, 0x41D490, sub_003BD690 | sub_003BD7E8 | - |
| sub_003BD7E8 | 0x3BD7E8 | 0x3BD92C | 82 | sub_003BD318, 0x41D3D8, 0x41D490, sub_003BD690, sub_003BD7E8, sub_003BD760 | sub_003BD7E8 | - |
| sub_003BD930 | 0x3BD930 | 0x3BDAD4 | 106 | sub_003BD368, sub_003BD318, sub_003BD450, sub_003BD498, sub_003BD500, sub_003BD538 | sub_003B2618, sub_003B2AE0 | - |
| sub_003BDAD8 | 0x3BDAD8 | 0x3BDAD8 | 1 | - | sub_003B3470 | - |
| sub_003BDAE0 | 0x3BDAE0 | 0x3BDAE4 | 2 | - | sub_003BAF98 | - |
| sub_003BDAE8 | 0x3BDAE8 | 0x3BDAEC | 2 | - | - | - |
| sub_003BDAF0 | 0x3BDAF0 | 0x3BDC2C | 80 | - | - | - |
| sub_003BDC30 | 0x3BDC30 | 0x3BDC3C | 4 | - | sub_003B0800, sub_003B2D90, sub_003BBDC8 | - |
| sub_003BDC40 | 0x3BDC40 | 0x3BDC4C | 4 | - | sub_003B1248 | - |
| sub_003BDC50 | 0x3BDC50 | 0x3BDC9C | 20 | - | sub_003B18B8, sub_003B1C18, sub_003B2D30, sub_003B2E28 | - |
| sub_003BDCA0 | 0x3BDCA0 | 0x3BDCBC | 8 | - | sub_003BE178 | - |
| sub_003BDCC0 | 0x3BDCC0 | 0x3BDCEC | 12 | - | sub_003AC4B0, sub_003AC690, sub_003ACA70, sub_003B2E28 | - |
| sub_003BDCF0 | 0x3BDCF0 | 0x3BDD04 | 6 | - | sub_003BE178 | - |
| sub_003BDD08 | 0x3BDD08 | 0x3BDD34 | 12 | - | sub_003BE178 | - |
| sub_003BDD38 | 0x3BDD38 | 0x3BDD94 | 24 | - | sub_003AC690, sub_003ACA70, sub_003B0048 | - |
| sub_003BDD98 | 0x3BDD98 | 0x3BDDAC | 6 | - | sub_003B0048 | - |
| sub_003BDDB0 | 0x3BDDB0 | 0x3BDDC4 | 6 | - | sub_003B0098 | - |
| sub_003BDDC8 | 0x3BDDC8 | 0x3BDDDC | 6 | - | sub_003ACA70 | - |
| sub_003BDDE0 | 0x3BDDE0 | 0x3BDE8C | 44 | - | sub_003AC4B0, sub_003AC690 | - |
| sub_003BDE90 | 0x3BDE90 | 0x3BDEAC | 8 | - | sub_003BE178 | - |
| sub_003BDEB0 | 0x3BDEB0 | 0x3BDF04 | 20 | - | sub_003AC258 | - |
| sub_003BDF08 | 0x3BDF08 | 0x3BDF2C | 10 | - | sub_003AF478, sub_003AF530, sub_003AF6F8, sub_003BE178 | - |
| sub_003BDF30 | 0x3BDF30 | 0x3BDF3C | 4 | - | sub_003B0098 | - |
| sub_003BDF40 | 0x3BDF40 | 0x3BDF6C | 12 | - | sub_003B0048, sub_003B0098, sub_003B0800 | - |
| sub_003BDF70 | 0x3BDF70 | 0x3BDFA4 | 13 | - | sub_003BE178 | - |
| sub_003BDFA8 | 0x3BDFA8 | 0x3BE0FC | 86 | - | sub_003BE178 | - |
| sub_003BE100 | 0x3BE100 | 0x3BE140 | 17 | - | - | VU0 |
| sub_003BE148 | 0x3BE148 | 0x3BE15C | 6 | - | sub_003BE178 | - |
| sub_003BE160 | 0x3BE160 | 0x3BE174 | 6 | - | sub_003BE178 | - |
| sub_003BE178 | 0x3BE178 | 0x3BE594 | 264 | sub_003BE178, sub_003BE160, sub_003BE148, sub_003BDD08, sub_003BDCF0, sub_003BDCA0, sub_003BDE90, sub_003BDF08, sub_003BDF70, sub_003BDFA8 | sub_003BE178 | - |
| sub_003BE598 | 0x3BE598 | 0x3BE5F4 | 24 | 0x4326F8, 0x42B528, 0x428E40 | sub_003B92B8 | - |
| sub_003BE5F8 | 0x3BE5F8 | 0x3BE614 | 8 | 0x435D60 | sub_003B3470, sub_003B4010, sub_003BA0C8 | - |
| sub_003BE618 | 0x3BE618 | 0x3BE654 | 16 | - | sub_003BF9A0 | - |
| sub_003BE658 | 0x3BE658 | 0x3BE7D8 | 96 | - | sub_003BE7E0, sub_003BE890, sub_003BE940 | - |
| sub_003BE7E0 | 0x3BE7E0 | 0x3BE88C | 51 | sub_003BE658 | - | - |
| sub_003BE890 | 0x3BE890 | 0x3BE93C | 51 | sub_003BE658 | - | - |
| sub_003BE940 | 0x3BE940 | 0x3BE9EC | 51 | sub_003BE658 | - | - |
| sub_003BE9F0 | 0x3BE9F0 | 0x3BEE1C | 292 | sub_003C0A48, sub_003BD2E0, sub_003BD398 | - | - |
| sub_003BEE20 | 0x3BEE20 | 0x3BF234 | 284 | sub_003C17B0 | - | - |
| sub_003BF238 | 0x3BF238 | 0x3BF5EC | 255 | sub_003C1030 | - | - |
| sub_003BF5F0 | 0x3BF5F0 | 0x3BF99C | 254 | sub_003C1470 | - | - |
| sub_003BF9A0 | 0x3BF9A0 | 0x3BFDE4 | 310 | sub_003BD3B0, sub_003BF9A0, sub_003BD538, sub_003BE618, sub_003BD690 | sub_003BF9A0 | - |
| sub_003BFDE8 | 0x3BFDE8 | 0x3BFE5C | 30 | - | - | - |
| sub_003BFE60 | 0x3BFE60 | 0x3BFED4 | 30 | - | - | - |
| sub_003BFED8 | 0x3BFED8 | 0x3BFEFC | 10 | - | - | - |
| sub_003BFF00 | 0x3BFF00 | 0x3C0484 | 384 | sub_003BD3B0, sub_003BD470, sub_003BD338, sub_003C17B0, sub_003C3A98 | - | - |
| sub_003C0488 | 0x3C0488 | 0x3C0A44 | 397 | sub_003BD3B0, sub_003BD470, sub_003BD338, sub_003C1470, sub_003C3A18 | - | - |
| sub_003C0A48 | 0x3C0A48 | 0x3C0A6C | 10 | - | sub_003BE9F0, sub_003C2160 | - |
| sub_003C0A70 | 0x3C0A70 | 0x3C0B34 | 49 | sub_003BD3B0, sub_003BD470, sub_003BD338 | sub_003C2160, sub_003C2220 | - |
| sub_003C0B38 | 0x3C0B38 | 0x3C0BF8 | 48 | sub_003BD3B0, sub_003BD470, sub_003BD338 | sub_003C2160, sub_003C2220 | - |
| sub_003C0C00 | 0x3C0C00 | 0x3C102C | 263 | sub_003BD3B0, sub_003BD470, sub_003BD338 | sub_003C2220, sub_003C22F0, sub_003C28D8 | - |
| sub_003C1030 | 0x3C1030 | 0x3C146C | 270 | sub_003BD3B0, sub_003BD470 | sub_003BF238, sub_003C22F0 | - |
| sub_003C1470 | 0x3C1470 | 0x3C17AC | 207 | sub_003BD3B0, sub_003BD470 | sub_003BF5F0, sub_003C0488, sub_003C22F0 | - |
| sub_003C17B0 | 0x3C17B0 | 0x3C1D14 | 341 | - | sub_003BEE20, sub_003BFF00, sub_003C22F0 | - |
| sub_003C1D18 | 0x3C1D18 | 0x3C1E6C | 86 | sub_003BD3B0 | - | - |
| sub_003C1E70 | 0x3C1E70 | 0x3C1F00 | 36 | - | sub_003C2008 | - |
| sub_003C1F08 | 0x3C1F08 | 0x3C1F54 | 20 | - | sub_003C1F58 | - |
| sub_003C1F58 | 0x3C1F58 | 0x3C2004 | 43 | sub_003C1F08 | - | - |
| sub_003C2008 | 0x3C2008 | 0x3C204C | 18 | sub_003C1E70 | - | - |
| sub_003C2050 | 0x3C2050 | 0x3C2104 | 45 | sub_003C2108 | - | - |
| sub_003C2108 | 0x3C2108 | 0x3C215C | 22 | - | sub_003C2050 | - |
| sub_003C2160 | 0x3C2160 | 0x3C221C | 48 | sub_003C0A48, sub_003C0A70, sub_003C0B38 | - | - |
| sub_003C2220 | 0x3C2220 | 0x3C22EC | 52 | sub_003C0C00, sub_003C0A70, sub_003C0B38 | - | - |
| sub_003C22F0 | 0x3C22F0 | 0x3C2544 | 150 | sub_003C0C00, sub_003C1030, sub_003C1470, sub_003C17B0 | - | - |
| sub_003C2548 | 0x3C2548 | 0x3C2644 | 63 | sub_003BD3B0, sub_003BD470 | sub_003C2648, sub_003C26C8 | - |
| sub_003C2648 | 0x3C2648 | 0x3C26C4 | 32 | sub_003C2548 | sub_003C26C8 | - |
| sub_003C26C8 | 0x3C26C8 | 0x3C28D4 | 132 | sub_003C2548, sub_003BD2E0, sub_003C26C8, sub_003C2648 | sub_003C26C8 | - |
| sub_003C28D8 | 0x3C28D8 | 0x3C2A64 | 98 | sub_003C0C00, sub_003BD398, sub_003BD498, sub_003BD3B0, sub_003BD470, sub_003C3588, sub_003C3648 | sub_003C36C8, sub_003C3910 | - |
| sub_003C2A68 | 0x3C2A68 | 0x3C2AA4 | 16 | sub_003C36C8 | - | - |
| sub_003C2AA8 | 0x3C2AA8 | 0x3C2B84 | 56 | - | sub_003C2B88, sub_003C3008 | - |
| sub_003C2B88 | 0x3C2B88 | 0x3C3004 | 284 | sub_003BD498, sub_003C2AA8, sub_003BD470, sub_003BD338, sub_003BD3B0 | sub_003C3588, sub_003C36C8, sub_003C3910 | - |
| sub_003C3008 | 0x3C3008 | 0x3C3584 | 351 | sub_003BD498, sub_003C2AA8, sub_003BD470, sub_003BD338, sub_003BD3B0 | sub_003C3A18, sub_003C3A98 | - |
| sub_003C3588 | 0x3C3588 | 0x3C3644 | 48 | sub_003BD338, sub_003BD398, sub_003BD470, sub_003C2B88 | sub_003C28D8, sub_003C3648, sub_003C36C8 | - |
| sub_003C3648 | 0x3C3648 | 0x3C36C4 | 32 | sub_003C3588 | sub_003C28D8 | - |
| sub_003C36C8 | 0x3C36C8 | 0x3C390C | 145 | sub_003C3588, sub_003BD338, sub_003BD398, sub_003BD470, sub_003C2B88, sub_003C28D8 | sub_003C2A68 | - |
| sub_003C3910 | 0x3C3910 | 0x3C3A14 | 65 | sub_003C28D8, sub_003BD338, sub_003BD398, sub_003BD470, sub_003C2B88 | - | - |
| sub_003C3A18 | 0x3C3A18 | 0x3C3A94 | 32 | sub_003C3008 | sub_003C0488 | - |
| sub_003C3A98 | 0x3C3A98 | 0x3C3D7C | 186 | sub_003C3008, sub_003BD2E0 | sub_003BFF00 | - |
| sub_003C3D80 | 0x3C3D80 | 0x3C3DFC | 32 | - | sub_003C3E40, sub_003C3EC8, sub_003C4008 | - |
| sub_003C3E00 | 0x3C3E00 | 0x3C3E3C | 16 | - | sub_003C3E40, sub_003C3EC8, sub_003C4008, sub_003C48A0 | - |
| sub_003C3E40 | 0x3C3E40 | 0x3C3EC4 | 34 | sub_003BD3B0, sub_003BD450, sub_003C3E00, sub_003C3D80 | sub_003C4008 | - |
| sub_003C3EC8 | 0x3C3EC8 | 0x3C4004 | 79 | sub_003BD3B0, sub_003C3E00, sub_003BD450, sub_003C3D80 | sub_003C4008 | - |
| sub_003C4008 | 0x3C4008 | 0x3C41E4 | 120 | sub_003BD338, sub_003BD398, sub_003BD3B0, sub_003C3E00, sub_003BD450, sub_003C3D80, sub_003C3E40, sub_003C3EC8 | sub_003C41E8 | - |
| sub_003C41E8 | 0x3C41E8 | 0x3C422C | 18 | sub_003C4008 | - | - |
| sub_003C4230 | 0x3C4230 | 0x3C435C | 76 | - | - | - |
| sub_003C4360 | 0x3C4360 | 0x3C4604 | 166 | - | - | - |
| sub_003C4608 | 0x3C4608 | 0x3C46BC | 43 | - | sub_003C46C0 | - |
| sub_003C46C0 | 0x3C46C0 | 0x3C489C | 120 | sub_003C4608 | sub_003C48A0 | - |
| sub_003C48A0 | 0x3C48A0 | 0x3C4A0C | 92 | sub_003BD3B0, sub_003C3E00, sub_003C46C0, sub_003C48A0 | sub_003C48A0, sub_003C4A10 | - |
| sub_003C4A10 | 0x3C4A10 | 0x3C4A74 | 26 | sub_003C48A0 | - | - |
| sub_003C4A78 | 0x3C4A78 | 0x3C4AE4 | 28 | 0x43AE68, 0x43B4B0, 0x43B0F8 | sub_003C4AE8 | VU1CMD 0x0E |
| sub_003C4AE8 | 0x3C4AE8 | 0x3C4B24 | 15 | sub_003C4A78 | sub_003C4B28, sub_003C4C28, sub_003C4C78, sub_003C4CE0 | - |
| sub_003C4B28 | 0x3C4B28 | 0x3C4C24 | 61 | 0x435B90, sub_003C4AE8 | - | - |
| sub_003C4C28 | 0x3C4C28 | 0x3C4C74 | 19 | sub_003C4AE8, 0x435B90 | sub_003C5120 | - |
| sub_003C4C78 | 0x3C4C78 | 0x3C4CDC | 25 | sub_003C4AE8, 0x435B90, 0x435DF0 | - | - |
| sub_003C4CE0 | 0x3C4CE0 | 0x3C4DAC | 50 | sub_003C4AE8, 0x435B90, 0x435DF0 | sub_003C5120 | - |
| sub_003C4DB0 | 0x3C4DB0 | 0x3C4DDC | 12 | - | sub_003C4E00 | VU1CMD 0x0A |
| sub_003C4DE0 | 0x3C4DE0 | 0x3C4DFC | 8 | - | sub_003C4E00 | - |
| sub_003C4E00 | 0x3C4E00 | 0x3C502C | 139 | sub_003C4DE0, sub_003C4DB0 | sub_003C5060 | - |
| sub_003C5030 | 0x3C5030 | 0x3C5058 | 11 | - | sub_003C5060 | - |
| sub_003C5060 | 0x3C5060 | 0x3C511C | 48 | sub_003C4E00, sub_003C5030, sub_003C5060 | sub_003C5060 | - |
| sub_003C5120 | 0x3C5120 | 0x3C51CC | 42 | sub_003C4C28, sub_003C4CE0, sub_003C5C80, 0x43FBA0, 0x43FBF0 | - | - |
| sub_003C51D0 | 0x3C51D0 | 0x3C526C | 37 | 0x435B10 | - | - |
| sub_003C5270 | 0x3C5270 | 0x3C53DC | 103 | 0x435B20, 0x435920, 0x4387C8, 0x4358E0, 0x436C20, 0x435970 | - | - |
| sub_003C53E0 | 0x3C53E0 | 0x3C5494 | 46 | - | - | - |
| sub_003C5498 | 0x3C5498 | 0x3C557C | 58 | 0x435AE0 | sub_003C5770, sub_003C5A90, sub_003C5D90, sub_003C6280 | - |
| sub_003C5580 | 0x3C5580 | 0x3C569C | 68 | 0x435B00, 0x435AF0, 0x43FBA0, 0x438CA0, sub_003C56F8, 0x43FBF0 | - | GIF |
| sub_003C56A0 | 0x3C56A0 | 0x3C56F4 | 26 | - | - | - |
| sub_003C56F8 | 0x3C56F8 | 0x3C576C | 29 | 0x43FBA0, 0x438C28, 0x43FBF0 | sub_003C5580 | GIF |
| sub_003C5770 | 0x3C5770 | 0x3C5A6C | 188 | sub_003C5498, 0x435B30, sub_003C5C80, 0x4390A0, 0x439848, 0x4387C8, 0x438FF0, 0x439A28, 0x435B00 | sub_003C5A70 | GIF |
| sub_003C5A70 | 0x3C5A70 | 0x3C5A8C | 8 | sub_003C5770 | - | - |
| sub_003C5A90 | 0x3C5A90 | 0x3C5BE4 | 82 | sub_003C5498, 0x435B30, 0x4387C8, sub_003C5C80, 0x435B00, 0x4390A0, 0x439848 | - | GIF |
| sub_003C5BE8 | 0x3C5BE8 | - | 0 | - | - | - |
| sub_003C5C80 | 0x3C5C80 | - | 0 | - | sub_003C5120, sub_003C5770, sub_003C5A90 | - |
| sub_003C5D20 | 0x3C5D20 | - | 0 | - | sub_003C5D90, sub_003C6280 | - |
| sub_003C5D90 | 0x3C5D90 | 0x3C5F94 | 126 | sub_003C5498, 0x435B30, 0x4387C8, sub_003C5D20, 0x435B00, 0x4390A0, 0x439848 | - | GIF |
| sub_003C5F98 | 0x3C5F98 | - | 0 | - | - | - |
| sub_003C6280 | 0x3C6280 | 0x3C6494 | 128 | 0x4387C8, 0x43FBA0, 0x43FBF0, sub_003C5498, 0x435B30, sub_003C5D20, 0x4390A0, 0x439848, 0x438FF0, 0x439A28, 0x435B00 | - | GIF |
| sub_003C6498 | 0x3C6498 | - | 0 | - | - | - |
| sub_003C66B8 | 0x3C66B8 | - | 0 | - | - | - |
| sub_003C6898 | 0x3C6898 | - | 0 | - | - | - |
| sub_003C69F0 | 0x3C69F0 | - | 0 | - | - | - |
| sub_003C6AA0 | 0x3C6AA0 | - | 0 | - | - | - |
| sub_003C6B50 | 0x3C6B50 | - | 0 | - | - | - |
| sub_003C6BE8 | 0x3C6BE8 | - | 0 | - | - | - |
| sub_003C6CE0 | 0x3C6CE0 | - | 0 | - | - | - |
| sub_003C6DA0 | 0x3C6DA0 | 0x3C6E2C | 32 | sub_003C6F78, 0x42B528 | sub_003C6F78 | - |
| sub_003C6E30 | 0x3C6E30 | 0x3C6E3C | 4 | - | - | - |
| sub_003C6E40 | 0x3C6E40 | 0x3C6ECC | 32 | sub_003C6F78, 0x42B528 | sub_003C6F78 | - |
| sub_003C6ED0 | 0x3C6ED0 | 0x3C6EDC | 4 | - | - | - |
| sub_003C6EE0 | 0x3C6EE0 | 0x3C6F74 | 34 | sub_003C6F78, 0x42B528 | sub_003C6F78 | - |
| sub_003C6F78 | 0x3C6F78 | 0x3C72E4 | 206 | sub_003C6DA0, sub_003C6E40, sub_003C6EE0, 0x3CDC50, 0x3CC100, 0x3CD418, sub_003C6F78, 0x42B528 | sub_003C6DA0, sub_003C6E40, sub_003C6EE0, sub_003C6F78, sub_003C72E8, sub_003C7D78, sub_003C7FD0 | - |
| sub_003C72E8 | 0x3C72E8 | 0x3C7D74 | 769 | sub_003C6F78, 0x42B528 | - | - |
| sub_003C7D78 | 0x3C7D78 | 0x3C7FCC | 173 | sub_003C6F78, 0x42B528 | - | - |
| sub_003C7FD0 | 0x3C7FD0 | 0x3C8D24 | 987 | sub_003C6F78, 0x42B528, 0x423AC8 | - | - |

## 2. VU1CMD / VIF Functions and Caller Chains (up to 4 levels)

| Function | Start | Flags | Caller Chains |
| --- | --- | --- | --- |
| sub_003A07C8 | 0x3A07C8 | VU1CMD 0x15C; VIF 0x0400,0x5000,0x7A60,0x7B20,0x7CC0,0x7F00,0x7F80 | sub_003A3BA8 -> sub_003A07C8 |
| sub_003A1ED4 | 0x3A1ED4 | VU1CMD 0x0A | sub_003A2D98 -> sub_003A1ED4 |
| sub_003AD0F8 | 0x3AD0F8 | VU1CMD 0x0E; VIF 0x1000,0x5000; DMA | sub_003B3D98 -> sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 -> sub_003AD0F8 |
| sub_003AD2B0 | 0x3AD2B0 | VU1CMD 0x0E; VIF 0x1000,0x5000; DMA | sub_003B3D98 -> sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 -> sub_003AD2B0 |
| sub_003AD608 | 0x3AD608 | VU1CMD 0x0A | (no callers in set) |
| sub_003ADD08 | 0x3ADD08 | VU1CMD 0x0A | (no callers in set) |
| sub_003ADEC0 | 0x3ADEC0 | VIF 0x1400,0x6C01,0x7200,0x7210,0x7240 | sub_003B3E28 -> sub_003B3D98 -> sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 |
| sub_003AEA18 | 0x3AEA18 | VU1CMD 0x0A,0x0E; VIF 0x0100,0x1400,0x6000 | sub_003AE900 -> sub_003AEA18 |
| sub_003AFDD8 | 0x3AFDD8 | VIF 0x1100,0x5000 | sub_003A3BA8 -> sub_003A07C8 -> sub_003AFE58 -> sub_003AFDD8<br>sub_003A5534 -> sub_003A4750 -> sub_003AFE58 -> sub_003AFDD8<br>sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 -> sub_003AFE58 -> sub_003AFDD8<br>sub_003B4010 -> sub_003B93D8 -> sub_003AFFA0 -> sub_003AFE58 -> sub_003AFDD8<br>sub_003B4010 -> sub_003B93D8 -> sub_003AFFA0 -> sub_003AFDD8<br>sub_003B0800 -> sub_003B0098 -> sub_003AFDD8 |
| sub_003AFE58 | 0x3AFE58 | VU1CMD 0x0E | sub_003A3BA8 -> sub_003A07C8 -> sub_003AFE58<br>sub_003A5534 -> sub_003A4750 -> sub_003AFE58<br>sub_003B3D98 -> sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 -> sub_003AFE58<br>sub_003B4010 -> sub_003B93D8 -> sub_003AFFA0 -> sub_003AFE58 |
| sub_003AFEA8 | 0x3AFEA8 | VIF 0x5000 | sub_003A5534 -> sub_003A4750 -> sub_003AFEA8<br>sub_003B2EA8 -> sub_003AFEA8 |
| sub_003AFED8 | 0x3AFED8 | VIF 0x5000 | sub_003B2EA8 -> sub_003AFED8 |
| sub_003AFFA0 | 0x3AFFA0 | VU1CMD 0x11 | sub_003B4010 -> sub_003B93D8 -> sub_003AFFA0 |
| sub_003B0098 | 0x3B0098 | VU1CMD 0x0A; VIF 0x0535 | sub_003B0800 -> sub_003B0098 |
| sub_003B0A48 | 0x3B0A48 | VU1CMD 0x11 | (no callers in set) |
| sub_003B0C50 | 0x3B0C50 | VIF 0x5151 | (no callers in set) |
| sub_003B0E40 | 0x3B0E40 | VU1CMD 0x11 | sub_003B2618 -> sub_003B0E40<br>sub_003B2F98 -> sub_003B2AE0 -> sub_003B0E40 |
| sub_003B1048 | 0x3B1048 | VU1CMD 0x11 | sub_003B2618 -> sub_003B1048 |
| sub_003B1248 | 0x3B1248 | VU1CMD 0x15,0x190; VIF 0x0100,0x0320,0x1000,0x1400,0x6001,0x6002,0x6500,0x6600,0x6C00,0x6C02,0x6C09,0x7C50; DMA | sub_003B2618 -> sub_003B1248<br>sub_003B2F98 -> sub_003B2AE0 -> sub_003B1248 |
| sub_003B18B8 | 0x3B18B8 | VIF 0x0100,0x0320,0x1000,0x1400,0x5000,0x6000,0x6500,0x6600,0x6C00; DMA | sub_003B1C18 -> sub_003B18B8 |
| sub_003B1C18 | 0x3B1C18 | VIF 0x0100,0x0320,0x1000,0x1400,0x6000,0x6500,0x6600,0x6C00,0x7C00; DMA | sub_003B18B8 -> sub_003B1C18 |
| sub_003B2D30 | 0x3B2D30 | VIF 0x1000,0x6C03; DMA | sub_003B2E28 -> sub_003B2D30 |
| sub_003B2D90 | 0x3B2D90 | VIF 0x1000,0x6C01; DMA | (no callers in set) |
| sub_003B2EA8 | 0x3B2EA8 | VIF 0x0100,0x6C02 | (no callers in set) |
| sub_003B2F98 | 0x3B2F98 | VU1CMD 0x0A,0x0E; VIF 0x0100,0x1000,0x1400,0x6001,0x6C02; DMA | (no callers in set) |
| sub_003B3470 | 0x3B3470 | VIF 0x1000,0x7000; DMA | (no callers in set) |
| sub_003B3640 | 0x3B3640 | VIF 0x7000 | (no callers in set) |
| sub_003B3820 | 0x3B3820 | VU1CMD 0x0E; VIF 0x1000,0x1100,0x5000; DMA | sub_003B3E28 -> sub_003B3D98 -> sub_003B3820 |
| sub_003B3B40 | 0x3B3B40 | VIF 0x1000; DMA | sub_003B3D98 -> sub_003B3820 -> sub_003B85B8 -> sub_003ADEC0 -> sub_003B3B40<br>sub_003B3470 -> sub_003B3B40 |
| sub_003B4290 | 0x3B4290 | VIF 0x1001 | sub_003B45E8 -> sub_003B4818 -> sub_003B4290<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B4290 |
| sub_003B42D0 | 0x3B42D0 | VIF 0x0100,0x6000,0x6500 | sub_003A7498 -> sub_003A73E8 -> sub_003AEB90 -> sub_003B42D0 |
| sub_003B45E8 | 0x3B45E8 | VIF 0x1000; DMA | (no callers in set) |
| sub_003B4818 | 0x3B4818 | VU1CMD 0x11,0x190; VIF 0x0100,0x1400,0x6C10,0x7000 | sub_003B45E8 -> sub_003B4818 |
| sub_003B4A60 | 0x3B4A60 | VU1CMD 0x11,0x190; VIF 0x0100,0x1400,0x6C10,0x7000; VU0 | sub_003B45E8 -> sub_003B4A60 |
| sub_003B5048 | 0x3B5048 | VIF 0x5000 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 |
| sub_003B5508 | 0x3B5508 | VIF 0x5000 | sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 |
| sub_003B57C0 | 0x3B57C0 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x6002,0x6C03 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B57C0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B57C0<br>sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5900 -> sub_003B57C0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B5900 -> sub_003B57C0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5900 -> sub_003B57C0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B6CF0 -> sub_003B57C0 |
| sub_003B5890 | 0x3B5890 | VIF 0x5000 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5890<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5890<br>sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5900 -> sub_003B5890<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B5900 -> sub_003B5890<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5900 -> sub_003B5890<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B69D8 -> sub_003B5890 |
| sub_003B5900 | 0x3B5900 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6000,0x6002,0x6500,0x6C03; GIF | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5900<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B5900<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5900 |
| sub_003B62C0 | 0x3B62C0 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B62C0 |
| sub_003B6508 | 0x3B6508 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B6508 |
| sub_003B6740 | 0x3B6740 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B6740 |
| sub_003B69D8 | 0x3B69D8 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6000,0x6002,0x6C03 | sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B69D8 |
| sub_003B6CF0 | 0x3B6CF0 | VIF 0x5000,0x6000; GIF | sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B6CF0 |
| sub_003B6FE0 | 0x3B6FE0 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03 | sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B6FE0 |
| sub_003B7220 | 0x3B7220 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF | sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B7220 |
| sub_003B7460 | 0x3B7460 | VU1CMD 0x15,0x190; VIF 0x0100,0x1400,0x5000,0x6002,0x6C03; GIF | sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B7460 |
| sub_003B7FC0 | 0x3B7FC0 | VIF 0x7FFF | sub_003B3740 -> sub_003B8448 -> sub_003B8380 -> sub_003B80F0 -> sub_003B7FC0 |
| sub_003B8380 | 0x3B8380 | VU1CMD 0x11 | sub_003B3E28 -> sub_003B3740 -> sub_003B8448 -> sub_003B8380 |
| sub_003B8A98 | 0x3B8A98 | VIF 0x7000 | sub_003B3E28 -> sub_003B8FE0 -> sub_003B8A98 |
| sub_003B8CC8 | 0x3B8CC8 | VIF 0x7000 | sub_003B3E28 -> sub_003B8FE0 -> sub_003B8CC8 |
| sub_003B90B0 | 0x3B90B0 | VIF 0x5000 | (no callers in set) |
| sub_003B9158 | 0x3B9158 | VIF 0x5000 | (no callers in set) |
| sub_003B9758 | 0x3B9758 | VU1CMD 0x0E | sub_003B3E28 -> sub_003B3D98 -> sub_003B3820 -> sub_003B9758 |
| sub_003B99B8 | 0x3B99B8 | VU1CMD 0x0E | sub_003B3E28 -> sub_003AFB90 -> sub_003B99B8<br>sub_003B3E28 -> sub_003B3D98 -> sub_003B3820 -> sub_003B99B8 |
| sub_003BA2A0 | 0x3BA2A0 | VIF 0x1001,0x7000; VU0 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5900 -> sub_003BA2A0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B5900 -> sub_003BA2A0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5900 -> sub_003BA2A0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B69D8 -> sub_003BA2A0<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B6CF0 -> sub_003BA2A0 |
| sub_003BA7D8 | 0x3BA7D8 | VIF 0x0100,0x6C00 | sub_003A7498 -> sub_003A73E8 -> sub_003AEB90 -> sub_003B42D0 -> sub_003BA7D8<br>sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003B5900 -> sub_003BA7D8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B5900 -> sub_003BA7D8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003B5900 -> sub_003BA7D8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B69D8 -> sub_003BA7D8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003B6CF0 -> sub_003BA7D8 |
| sub_003BAF98 | 0x3BAF98 | VU1CMD 0x0A,0x0E,0x11,0x190; VIF 0x0100,0x1400,0x6002,0x6C06,0x6C0A | (no callers in set) |
| sub_003BB8E8 | 0x3BB8E8 | VU1CMD 0x11; VIF 0x0100,0x6002,0x6401,0x6C06 | sub_003B45E8 -> sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8<br>sub_003B45E8 -> sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 |
| sub_003BBDC8 | 0x3BBDC8 | VU1CMD 0x0A,0x0E,0x190; VIF 0x0100,0x1400,0x6002,0x6C00 | sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBDC8<br>sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBDC8<br>sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBDC8 |
| sub_003BBF80 | 0x3BBF80 | VU1CMD 0x0A,0x0E,0x11,0x190; VIF 0x0100,0x1400,0x6002,0x6C00 | sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80<br>sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80<br>sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80 |
| sub_003BC278 | 0x3BC278 | VU1CMD 0x39,0xC8,0x108,0x212,0x2BC,0x2E4; VIF 0x0100,0x1400,0x6001,0x6C00,0x6C08 | sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC278<br>sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC278<br>sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC278 |
| sub_003BC770 | 0x3BC770 | VU1CMD 0x320,0x398,0x39B; VIF 0x0100,0x1000,0x1400,0x6000; DMA | sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC770<br>sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC770<br>sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BC770 |
| sub_003BCC50 | 0x3BCC50 | VU1CMD 0x389,0x3DC,0x3DE; VIF 0x0100,0x6003,0x6C00 | sub_003B4818 -> sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BCC50<br>sub_003B4A60 -> sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BCC50<br>sub_003B4A60 -> sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BCC50 |
| sub_003BD048 | 0x3BD048 | VU1CMD 0x0A | sub_003B5048 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80 -> sub_003BD048<br>sub_003B5368 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80 -> sub_003BD048<br>sub_003B5508 -> sub_003BBB50 -> sub_003BB8E8 -> sub_003BBF80 -> sub_003BD048 |
| sub_003C4A78 | 0x3C4A78 | VU1CMD 0x0E | sub_003C4B28 -> sub_003C4AE8 -> sub_003C4A78<br>sub_003C5120 -> sub_003C4C28 -> sub_003C4AE8 -> sub_003C4A78<br>sub_003C4C78 -> sub_003C4AE8 -> sub_003C4A78<br>sub_003C5120 -> sub_003C4CE0 -> sub_003C4AE8 -> sub_003C4A78 |
| sub_003C4DB0 | 0x3C4DB0 | VU1CMD 0x0A | sub_003C5060 -> sub_003C4E00 -> sub_003C4DB0 |

## 3. Roots (No Callers in Set, Reach VIF/VU1CMD)

| Root | Start | Flags | Reachable VIF/VU1CMD Targets |
| --- | --- | --- | --- |
| sub_003A2D98 | 0x3A2D98 | - | sub_003A1ED4 |
| sub_003A3BA8 | 0x3A3BA8 | - | sub_003A07C8, sub_003AFDD8, sub_003AFE58 |
| sub_003A5534 | 0x3A5534 | - | sub_003AFDD8, sub_003AFE58, sub_003AFEA8 |
| sub_003A7498 | 0x3A7498 | - | sub_003B42D0, sub_003BA7D8 |
| sub_003AD608 | 0x3AD608 | VU1CMD 0x0A | sub_003AD608 |
| sub_003ADD08 | 0x3ADD08 | VU1CMD 0x0A | sub_003ADD08 |
| sub_003AE900 | 0x3AE900 | - | sub_003AEA18 |
| sub_003B0800 | 0x3B0800 | - | sub_003AFDD8, sub_003B0098 |
| sub_003B0A48 | 0x3B0A48 | VU1CMD 0x11 | sub_003AFDD8, sub_003B0A48 |
| sub_003B0B78 | 0x3B0B78 | - | sub_003AFDD8 |
| sub_003B0C50 | 0x3B0C50 | VIF 0x5151 | sub_003AFDD8, sub_003B0C50 |
| sub_003B2618 | 0x3B2618 | - | sub_003AFDD8, sub_003B0E40, sub_003B1048, sub_003B1248 |
| sub_003B2D90 | 0x3B2D90 | VIF 0x1000,0x6C01; DMA | sub_003B2D90 |
| sub_003B2E28 | 0x3B2E28 | - | sub_003B2D30 |
| sub_003B2EA8 | 0x3B2EA8 | VIF 0x0100,0x6C02 | sub_003AFEA8, sub_003AFED8, sub_003B2EA8 |
| sub_003B2F98 | 0x3B2F98 | VU1CMD 0x0A,0x0E; VIF 0x0100,0x1000,0x1400,0x6001,0x6C02; DMA | sub_003AFDD8, sub_003B0E40, sub_003B1248, sub_003B2F98 |
| sub_003B3470 | 0x3B3470 | VIF 0x1000,0x7000; DMA | sub_003B3470, sub_003B3B40 |
| sub_003B3640 | 0x3B3640 | VIF 0x7000 | sub_003B3640 |
| sub_003B3E28 | 0x3B3E28 | - | sub_003AD0F8, sub_003AD2B0, sub_003ADEC0, sub_003AFDD8, sub_003AFE58, sub_003B3820, sub_003B3B40, sub_003B7FC0, sub_003B8380, sub_003B8A98, sub_003B8CC8, sub_003B9758 ... (+1) |
| sub_003B4010 | 0x3B4010 | - | sub_003AFDD8, sub_003AFE58, sub_003AFFA0 |
| sub_003B45E8 | 0x3B45E8 | VIF 0x1000; DMA | sub_003B4290, sub_003B45E8, sub_003B4818, sub_003B4A60, sub_003B5048, sub_003B5508, sub_003B57C0, sub_003B5890, sub_003B5900, sub_003B62C0, sub_003B6508, sub_003B6740 ... (+14) |
| sub_003B90B0 | 0x3B90B0 | VIF 0x5000 | sub_003B90B0 |
| sub_003B9158 | 0x3B9158 | VIF 0x5000 | sub_003B9158 |
| sub_003BAF98 | 0x3BAF98 | VU1CMD 0x0A,0x0E,0x11,0x190; VIF 0x0100,0x1400,0x6002,0x6C06,0x6C0A | sub_003BAF98 |
| sub_003C4B28 | 0x3C4B28 | - | sub_003C4A78 |
| sub_003C4C78 | 0x3C4C78 | - | sub_003C4A78 |
| sub_003C5120 | 0x3C5120 | - | sub_003C4A78 |
