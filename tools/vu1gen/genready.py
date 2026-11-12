"""Emit the ready-time assignments of generated hot blocks as C++ lines for a kernel that replaces a chain of blocks.
Usage: python tools/vu1gen/genready.py vuH_10:Sp vuH_4:Sl vuH_17:St   -> lines 'vu.m_vfReady[r][l] = <Var> + k;' grouped per block, in the given order
(a later block overwrites an earlier one, exactly as the real chain does; S of a block is the cycle at which it started, or its last loop iteration)."""
import re
import sys

SRC = "PS2Recomp/ps2xRuntime/src/lib/vu/generated/vu1_hot_blocks.cpp"


def main():
    t = open(SRC, encoding="utf-8", errors="replace").read().split("\n")
    for spec in sys.argv[1:]:
        name, var = spec.split(":")
        i = next(k for k, ln in enumerate(t) if ln.startswith("static int %s(" % name))
        j = i
        while t[j] != "}":
            j += 1
        print("    // %s -> %s" % (name, var))
        for ln in t[i:j + 1]:
            m = re.match(r"\s*vu\.m_(accReady|vfReady|viReady)((?:\[\d+\])+) = S \+ (\d+)u; // PERF-LEAN", ln)
            if m:
                print("    vu.m_%s%s = %s + %su;" % (m.group(1), m.group(2), var, m.group(3)))


if __name__ == "__main__":
    main()
