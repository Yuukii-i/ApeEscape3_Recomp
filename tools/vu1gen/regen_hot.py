"""Rebuild PS2Recomp/.../generated/vu1_hot_blocks.cpp from a merged, transfer-free block dump (tools/vu1gen/hotgen_norm.py output).

Two block families are generated from the same record list:
  vuH_*  the fully optimised family (loop fusion, no per-cycle transfer stepping: such blocks decline while an XGKICK transfer runs)  -> vu1HotLookup
  vuX_*  the transfer-aware family (stages xg / lean / inline / inline2 only: every cycle steps a running transfer)                 -> vu1HotLookupXg
The dispatcher picks the family by the transfer state; both are keyed by the same transfer-free timing hash.
Usage: python tools/vu1gen/regen_hot.py <merged_blocks.txt> [--image 86503d3905e35276] [--work <dir>] [--dry]"""
import os
import re
import shutil
import subprocess
import sys

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GEN = "PS2Recomp/ps2xRuntime/src/lib/vu/generated"
HOT = GEN + "/vu1_hot_blocks.cpp"


def run(cmd, cwd):
    r = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit("FAILED %s\n%s\n%s" % (" ".join(cmd), r.stdout[-1500:], r.stderr[-1500:]))
    return r.stdout


def stage_tree(work, name, image, blk_path):
    t = os.path.join(work, name)
    shutil.rmtree(t, ignore_errors=True)
    os.makedirs(os.path.join(t, "tools/vu1gen"))
    os.makedirs(os.path.join(t, "logs"))
    os.makedirs(os.path.join(t, GEN))
    for f in os.listdir(os.path.join(REPO, "tools/vu1gen")):
        if f.endswith(".py"):
            shutil.copy(os.path.join(REPO, "tools/vu1gen", f), os.path.join(t, "tools/vu1gen", f))
    for f in os.listdir(os.path.join(REPO, GEN)):
        if f.endswith(".cpp"):
            shutil.copy(os.path.join(REPO, GEN, f), os.path.join(t, GEN, f))
    shutil.copy(os.path.join(REPO, "logs/vuusage_u1_%s.txt" % image), os.path.join(t, "logs"))
    shutil.copy(blk_path, os.path.join(t, "logs/blk.txt"))
    # wanted list: every record of the merged dump
    with open(os.path.join(t, "tools/vu1gen/hot_blocks.txt"), "w") as f:
        for ln in open(blk_path):
            m = re.match(r"B pc=([0-9A-Fa-f]+) sig=([0-9a-f]+)", ln)
            if m:
                f.write("%s %s\n" % (m.group(1), m.group(2)))
    return t


def build(t, image, full):
    u, b = "logs/vuusage_u1_%s.txt" % image, "logs/blk.txt"
    py = sys.executable
    out = run([py, "tools/vu1gen/gen_vu1_hot.py", u, b], t)
    print("  ", out.strip().splitlines()[-1])
    steps = [("patch_xg_hot.py", []), ("patch_lean_hot.py", [])]
    if full:
        steps.append(("patch_loop_hot.py", [b]))
    steps += [("patch_inline_hot.py", []), ("patch_inline2_hot.py", [])]
    if full:
        steps += [("patch_adv_hot.py", [b]), ("patch_regs_hot.py", [b]), ("patch_nrm_hot.py", [])]
    for s, a in steps:
        run([py, "tools/vu1gen/" + s] + a, t)
    return open(os.path.join(t, HOT), encoding="utf-8", newline="").read()


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    image = "86503d3905e35276"
    work = os.path.join(REPO, "logs", "regen_work")
    if "--image" in sys.argv:
        image = sys.argv[sys.argv.index("--image") + 1]
    if "--work" in sys.argv:
        work = sys.argv[sys.argv.index("--work") + 1]
    blk = os.path.abspath(args[0])
    dry = "--dry" in sys.argv
    print("fast family")
    fast = build(stage_tree(work, "fast", image, blk), image, True)
    print("transfer-aware family")
    xg = build(stage_tree(work, "xg", image, blk), image, False)

    i0 = xg.index("static int vuH_0(")
    i1 = xg.index("VuHotFn vu1HotLookup(")
    i2 = xg.index("const bool kVu1HotStart")
    body = xg[i0:i1].replace("vuH_", "vuX_")
    look = xg[i1:i2].replace("vu1HotLookup(", "vu1HotLookupXg(").replace("vuH_", "vuX_")
    nfast = len(re.findall(r"^static int vuH_\d+\(", fast, re.M))
    nxg = len(re.findall(r"^static int vuX_\d+\(", body, re.M))
    final = fast.rstrip("\n") + "\n\n// PERF-LB-XG: transfer-aware block family (same blocks, every cycle steps a running XGKICK transfer); selected by the dispatcher while a transfer runs\n" + body + look
    print("fast blocks %d, transfer-aware blocks %d" % (nfast, nxg))
    out = os.path.join(REPO, HOT)
    if dry:
        out = os.path.join(work, "vu1_hot_blocks.final.cpp")
    with open(out, "w", encoding="utf-8", newline="") as f:
        f.write(final)
    print("wrote", out, len(final))


if __name__ == "__main__":
    main()
