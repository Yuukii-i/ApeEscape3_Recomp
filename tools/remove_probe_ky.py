"""Remove every `// PROBE-KY` line (white-screen / heap-corruption diagnostics, task KY) from recomp_source and EeScheduler.cpp.
They are diagnostic only: malloc/free rings in the guest allocator, std::map counters in the string helpers (one map insert per call),
a steady_clock read per scheduler iteration, an atomic + memory compare per checkpoint. Backups go to the directory in PS2X_BACKUP_DIR.
Usage: PS2X_BACKUP_DIR=<dir> python tools/remove_probe_ky.py [--dry]"""
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DRY = "--dry" in sys.argv
BK = os.environ.get("PS2X_BACKUP_DIR")
targets = sorted((ROOT / "recomp_source").glob("sub_*.cpp")) + [ROOT / "PS2Recomp/ps2xRuntime/src/lib/Kernel/EeScheduler.cpp"]
total = 0
files = 0
for f in targets:
    data = f.read_bytes()
    if b"PROBE-KY" not in data:
        continue
    text = data.decode("utf-8", errors="surrogateescape")
    lines = text.split("\n")
    keep = [ln for ln in lines if "PROBE-KY" not in ln]
    removed = len(lines) - len(keep)
    if removed == 0:
        continue
    total += removed
    files += 1
    print("%-48s -%d" % (f.name, removed))
    if not DRY:
        if BK:
            pathlib.Path(BK).mkdir(parents=True, exist_ok=True)
            dst = pathlib.Path(BK) / f.name
            if not dst.exists():
                shutil.copy2(f, dst)
        f.write_bytes("\n".join(keep).encode("utf-8", errors="surrogateescape"))
print("files:", files, "lines removed:", total, "(dry run)" if DRY else "")
