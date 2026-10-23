import sys
sys.path.append('tools/iop')
from analyze_dbc_irx import parse_elf
import struct
import capstone

sections = parse_elf('tools/iop/sg2iopm1.irx')
text = sections['.text']['data']
data = sections['.data']['data']
rodata = sections['.rodata']['data']
cs = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)

diff = 0x4820 - sections['.data']['addr']
table = []
for i in range(36):
    target, = struct.unpack('<I', data[diff + i*4 : diff + (i+1)*4])
    table.append((i, target))

print(f"Total SG2 opcodes: {len(table)}")

for fno, target in table:
    # Disassemble 10 instructions from target
    insns = list(cs.disasm(text[target : target + 48], target))
    calls = []
    for ins in insns:
        if ins.mnemonic in ['jal', 'bal']:
            calls.append(ins.op_str)
    first_few = "; ".join([f"{ins.mnemonic} {ins.op_str}" for ins in insns[:4]])
    print(f"fno 0x{fno:02x} (target 0x{target:04x}): calls={calls} | {first_few}")
