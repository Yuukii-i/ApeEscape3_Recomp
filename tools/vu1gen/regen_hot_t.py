"""Hot-block tables for the differing pairs of a variant microcode image (PERF-VAR), next to the main-image table.
Usage: python tools/vu1gen/regen_hot_t.py <variant hash> <tag> <merged_blocks.txt>     (merged by hotgen_norm.py from logs/vublk2_u1_<variant>.txt)
Writes generated/vu1_hot_blocks_<tag>.cpp with vuH_<tag>_N / vuX_<tag>_N, vu1HotLookup_<tag>, vu1HotLookupXg_<tag>, kVu1HotStart_<tag>.
"""
import os
import re
import sys

import regen_hot as r


def main():
    variant, tag, blk = sys.argv[1], sys.argv[2], os.path.abspath(sys.argv[3])
    work = os.path.join(r.REPO, "logs", "regen_work_" + tag)
    print("fast family")
    fast = r.build(r.stage_tree(work, "fast", variant, blk), variant, True)
    print("transfer-aware family")
    xg = r.build(r.stage_tree(work, "xg", variant, blk), variant, False)
    i0 = xg.index("static int vuH_0(")
    i1 = xg.index("VuHotFn vu1HotLookup(")
    i2 = xg.index("const bool kVu1HotStart")
    body = xg[i0:i1].replace("vuH_", "vuX_")
    look = xg[i1:i2].replace("vu1HotLookup(", "vu1HotLookupXg(").replace("vuH_", "vuX_")
    final = fast.rstrip("\n") + "\n\n" + body + look
    # per-image symbol names (the main table keeps the plain ones)
    final = re.sub(r"\bvuH_(\d+)\b", r"vuH_%s_\1" % tag, final)
    final = re.sub(r"\bvuX_(\d+)\b", r"vuX_%s_\1" % tag, final)
    final = final.replace("vu1HotLookupXg(", "vu1HotLookupXg_%s(" % tag).replace("vu1HotLookup(", "vu1HotLookup_%s(" % tag)
    final = final.replace("kVu1HotStart", "kVu1HotStart_%s" % tag)
    final = final.replace("const bool kVu1HotStart_%s[2048] = {" % tag, "extern const bool kVu1HotStart_%s[2048];" % tag + chr(10) + "const bool kVu1HotStart_%s[2048] = {" % tag)
    out = os.path.join(r.REPO, r.GEN, "vu1_hot_blocks_%s.cpp" % tag)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write(final)
    print("wrote", out, len(final), "blocks fast", len(re.findall(r"^static int vuH_%s_\d+\(" % tag, final, re.M)))


main()
