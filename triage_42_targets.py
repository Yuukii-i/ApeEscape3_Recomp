import os
import struct

def main():
    elf_path = "SCUS_975.01"
    
    # 1. Load function ranges from recomp_source
    funcs = []
    for fname in os.listdir("recomp_source"):
        if fname.startswith("sub_") and fname.endswith(".cpp"):
            # Address range in header comments: // Address: 0x... - 0x...
            path = os.path.join("recomp_source", fname)
            with open(path, "r", errors="ignore") as f:
                for line in f:
                    if "// Address: 0x" in line:
                        parts = line.strip().split("// Address: 0x")[1].split(" - 0x")
                        if len(parts) == 2:
                            start = int(parts[0], 16)
                            end = int(parts[1], 16)
                            funcs.append((start, end, fname))
                        break
    funcs.sort()
    print(f"Loaded {len(funcs)} function ranges from recomp_source")

    # 47 missing targets from scan_missing_targets.py
    named = {0x00406390, 0x00412840, 0x004133A0, 0x004135C8, 0x00436E08}
    all_missing = [
        0x00000000, 0x0015BA78, 0x00164240, 0x001874FC, 0x001F071C,
        0x002221F4, 0x00239954, 0x00248B34, 0x002AA01C, 0x002AB40C,
        0x002AB7F4, 0x002ABC60, 0x00329D0C, 0x0032D2B8, 0x00331758,
        0x00347084, 0x0035070C, 0x00406318, 0x00406390, 0x004063C0,
        0x00406468, 0x00412840, 0x004133A0, 0x004135C8, 0x00428F50,
        0x0042B578, 0x0042E428, 0x0042E9D0, 0x0042F2D0, 0x004356E0,
        0x00435700, 0x00435720, 0x00436E08, 0x00468FC8, 0x004690B4,
        0x0048FF68, 0x004DA294, 0x004EE6B8, 0x0050D404, 0x00542F40,
        0x00543984, 0x00573488, 0x00580CB0, 0x00594EE0, 0x0059C4D0,
        0x0059CBC8, 0x005F6A98
    ]

    unnamed_42 = [t for t in all_missing if t not in named]
    print(f"Total unnamed missing targets to triage: {len(unnamed_42)}")

    # Also find caller(s) for each target
    with open(elf_path, "rb") as f:
        f.seek(0x1000)
        text = f.read(0x528258)

    callers_map = {}
    for i in range(0, len(text), 4):
        caller_pc = 0x100000 + i
        inst = struct.unpack("<I", text[i:i+4])[0]
        opcode = (inst >> 26) & 0x3F
        if opcode in (2, 3):
            target = (inst & 0x03FFFFFF) << 2
            if target in unnamed_42:
                if target not in callers_map:
                    callers_map[target] = []
                callers_map[target].append((caller_pc, "JAL" if opcode == 3 else "J"))

    results = []
    with open(elf_path, "rb") as f:
        for target in unnamed_42:
            callers = callers_map.get(target, [])
            caller_str = ", ".join(f"0x{c[0]:08X}" for c in callers)
            
            # Check source + 8
            eq_source_plus_8 = any(target == c[0] + 8 for c in callers)

            # Check inside range of emitted function
            inside_func = None
            for start, end, fname in funcs:
                if start <= target < end:
                    inside_func = (start, end, fname)
                    break

            # Read first 8 instructions at target
            disasm_lines = []
            is_prologue = False
            first_raw = ""
            
            if target >= 0x100000 and target < 0x628258:
                file_off = target - 0xFF000
                f.seek(file_off)
                raw_bytes = f.read(32)
                first_raw = raw_bytes[:16].hex()
                
                # Check instructions
                for k in range(0, min(len(raw_bytes), 32), 4):
                    inst_word = struct.unpack("<I", raw_bytes[k:k+4])[0]
                    # Check addiu sp, sp, -N (opcode 9, rs=29, rt=29, imm < 0)
                    op = (inst_word >> 26) & 0x3F
                    rs = (inst_word >> 21) & 0x1F
                    rt = (inst_word >> 16) & 0x1F
                    imm = struct.unpack("<h", raw_bytes[k:k+2])[0] # signed 16-bit
                    
                    line_desc = f"0x{inst_word:08X}"
                    if op == 9 and rs == 29 and rt == 29 and imm < 0:
                        line_desc += f" (addiu sp, sp, {imm})"
                        if k == 0:
                            is_prologue = True
                    disasm_lines.append(line_desc)
            else:
                first_raw = "N/A"
                disasm_lines.append("Outside .text")

            results.append({
                "target": target,
                "callers": caller_str,
                "eq_source_plus_8": eq_source_plus_8,
                "inside_func": inside_func,
                "is_prologue": is_prologue,
                "first_raw": first_raw,
                "disasm": disasm_lines
            })

    print("\n" + "="*120)
    for r in results:
        t = r["target"]
        inside = f"Inside {r['inside_func'][2]} (0x{r['inside_func'][0]:X}-0x{r['inside_func'][1]:X})" if r["inside_func"] else "NOT inside emitted func"
        print(f"Target: 0x{t:08X} | Caller(s): {r['callers']} | src+8: {r['eq_source_plus_8']} | Prologue: {r['is_prologue']}")
        print(f"  Emitted func: {inside}")
        print(f"  First 4 insts: {', '.join(r['disasm'][:4])}")
        print(f"  Next 4 insts:  {', '.join(r['disasm'][4:8])}")
        print("-" * 120)

if __name__ == "__main__":
    main()
