import os
import struct
import re

def main():
    print("=== Scanning missing static jump/call targets ===")
    
    # 1. Parse registered function table or filenames
    # In PS2Recomp, register_functions.cpp contains:
    #   g_ps2RecompiledFunctionTable[slot] = sub_...; // 0x<vaddr>
    # Also collect function entry points from filenames in recomp_source/
    registered_table_addrs = set()
    reg_file = os.path.join("recomp_source", "register_functions.cpp")
    if os.path.exists(reg_file):
        with open(reg_file, "r") as f:
            for line in f:
                idx = line.find("// 0x")
                if idx != -1:
                    addr_str = line[idx+5:].strip()
                    try:
                        registered_table_addrs.add(int(addr_str, 16))
                    except ValueError:
                        pass
        print(f"Loaded {len(registered_table_addrs)} registered instructions from {reg_file}")

    # Also collect function entry points from sub_XXXXXXXX_0x... filenames
    recomp_funcs = set()
    recomp_dir = "recomp_source"
    for fname in os.listdir(recomp_dir):
        if fname.startswith("sub_") and fname.endswith(".cpp"):
            m = re.search(r"_0x([0-9a-fA-F]+)\.cpp", fname)
            if m:
                recomp_funcs.add(int(m.group(1), 16))
    print(f"Loaded {len(recomp_funcs)} recompiled function entry points from {recomp_dir}")

    # Also load stubs from config.toml for reference
    stubs = {}
    if os.path.exists("config.toml"):
        with open("config.toml", "r") as f:
            for line in f:
                if "@0x" in line:
                    clean = line.strip().strip('",')
                    parts = clean.split("@0x")
                    if len(parts) == 2:
                        name = parts[0].strip('" ')
                        try:
                            addr = int(parts[1], 16)
                            stubs[addr] = name
                        except ValueError:
                            pass

    # 2. Read .text from SCUS_975.01
    elf_path = "SCUS_975.01"
    with open(elf_path, "rb") as f:
        # Read ELF header
        f.seek(0x20)
        shoff = struct.unpack("<I", f.read(4))[0]
        f.seek(0x2E)
        shentsize, shnum, shstrndx = struct.unpack("<HHH", f.read(6))

        # Read section string table
        f.seek(shoff + shstrndx * shentsize)
        _, _, _, _, str_off, str_size, _, _, _, _ = struct.unpack("<IIIIIIIIII", f.read(40))
        f.seek(str_off)
        shstrtab = f.read(str_size)

        text_vaddr = None
        text_off = None
        text_size = None

        for i in range(shnum):
            f.seek(shoff + i * shentsize)
            sh_name, sh_type, sh_flags, sh_addr, sh_offset, sh_size, _, _, _, _ = struct.unpack("<IIIIIIIIII", f.read(40))
            name = shstrtab[sh_name:].split(b"\0")[0].decode("latin1")
            if name == ".text":
                text_vaddr = sh_addr
                text_off = sh_offset
                text_size = sh_size
                break

    print(f".text section: vaddr=0x{text_vaddr:08X}, file_offset=0x{text_off:08X}, size=0x{text_size:08X} ({text_size} bytes)")

    with open(elf_path, "rb") as f:
        f.seek(text_off)
        text_bytes = f.read(text_size)

    # 3. Decode every J and JAL instruction in .text
    missing_targets = {} # target -> list of (caller_pc, opcode_name)
    total_j_jal = 0

    for i in range(0, len(text_bytes), 4):
        caller_pc = text_vaddr + i
        inst = struct.unpack("<I", text_bytes[i:i+4])[0]
        opcode = (inst >> 26) & 0x3F

        if opcode in (2, 3): # 2 = J, 3 = JAL
            total_j_jal += 1
            op_name = "JAL" if opcode == 3 else "J"
            instr_index = inst & 0x03FFFFFF
            # In MIPS, target PC shares the high 4 bits of the delay slot PC
            delay_slot_pc = caller_pc + 4
            target_pc = (delay_slot_pc & 0xF0000000) | (instr_index << 2)

            # Check if target is registered in g_ps2RecompiledFunctionTable
            if target_pc not in registered_table_addrs:
                if target_pc not in missing_targets:
                    missing_targets[target_pc] = []
                missing_targets[target_pc].append((caller_pc, op_name))

    print(f"\nTotal J/JAL instructions scanned in .text: {total_j_jal}")
    print(f"Total distinct missing targets (not in register_functions.cpp table): {len(missing_targets)}\n")

    print(f"{'Target PC':<12} {'Callers':<8} {'JAL':<6} {'J':<6} {'In config.toml?':<30} {'Sample Callers'}")
    print("-" * 100)

    for target in sorted(missing_targets.keys()):
        callers = missing_targets[target]
        jal_count = sum(1 for c in callers if c[1] == "JAL")
        j_count = sum(1 for c in callers if c[1] == "J")
        stub_name = stubs.get(target, "-")
        sample_callers = ", ".join(f"0x{c[0]:08X}({c[1]})" for c in callers[:3])
        if len(callers) > 3:
            sample_callers += f", ... (+{len(callers)-3} more)"
        print(f"0x{target:08X}   {len(callers):<8} {jal_count:<6} {j_count:<6} {stub_name:<30} {sample_callers}")

if __name__ == "__main__":
    main()
