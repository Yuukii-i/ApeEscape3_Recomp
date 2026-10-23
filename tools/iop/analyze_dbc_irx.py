import struct
import os
import capstone

def parse_elf(filepath):
    with open(filepath, 'rb') as f:
        data = f.read()

    e_shoff, = struct.unpack('<I', data[32:36])
    e_shentsize, e_shnum, e_shstrndx = struct.unpack('<HHH', data[46:52])

    shstr_hdr = data[e_shoff + e_shstrndx * e_shentsize : e_shoff + (e_shstrndx + 1) * e_shentsize]
    shstr_off, = struct.unpack('<I', shstr_hdr[16:20])

    sections = {}
    for i in range(e_shnum):
        sh = data[e_shoff + i * e_shentsize : e_shoff + (i + 1) * e_shentsize]
        sh_name_idx, sh_type, sh_flags, sh_addr, sh_offset, sh_size = struct.unpack('<IIIIII', sh[:24])
        name_end = data.find(b'\0', shstr_off + sh_name_idx)
        name = data[shstr_off + sh_name_idx : name_end].decode('latin-1')
        sections[name] = {
            'addr': sh_addr,
            'offset': sh_offset,
            'size': sh_size,
            'data': data[sh_offset : sh_offset + sh_size]
        }
    return sections

def search_rpc(name):
    path = os.path.join('tools', 'vfi', '_out', 'bin', 'irx', '3.0', name)
    sections = parse_elf(path)
    text_data = sections['.text']['data']
    cs = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 + capstone.CS_MODE_LITTLE_ENDIAN)
    
    print(f"=== Disassembling {name} for RPC patterns ===")
    instructions = list(cs.disasm(text_data, 0))
    for i, insn in enumerate(instructions):
        # Look for lui with 0x8000
        if insn.mnemonic == 'lui' and '0x8000' in insn.op_str:
            # Check next few instructions for ori/addiu with 0x13xx
            for j in range(i+1, min(i+6, len(instructions))):
                if any(x in instructions[j].op_str for x in ['0x1300', '0x131c', '0x131e', '0x131f', '0x1304', '0x1363']):
                    print(f"Match around 0x{insn.address:04x}:")
                    for k in range(max(0, i-2), min(len(instructions), j+8)):
                        print(f"  0x{instructions[k].address:04x}: {instructions[k].mnemonic:10s} {instructions[k].op_str}")
                    print()
                    break

search_rpc('dbcman.irx')
search_rpc('ds1o.irx')
search_rpc('ds2o.irx')
