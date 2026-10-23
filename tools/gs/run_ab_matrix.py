#!/usr/bin/env python3
"""
tools/gs/run_ab_matrix.py: Runs the 4 A/B configurations for Now Loading, computes metrics, and produces montages.
"""

import subprocess
import os
import glob
import time
from eval_metrics import evaluate_sprite

RUNS = [
    {"name": "swz0_rel0", "swz": "0", "rel": "0"},
    {"name": "swz0_rel1", "swz": "0", "rel": "1"},
    {"name": "swz1_rel0", "swz": "1", "rel": "0"},
    {"name": "swz1_rel1", "swz": "1", "rel": "1"},
]

results = []

for r in RUNS:
    name = r["name"]
    dump_dir = f"logs/frames_{name}"
    os.makedirs(dump_dir, exist_ok=True)
    # clean old dump
    for f in glob.glob(f"{dump_dir}/*"):
        os.remove(f)

    env = os.environ.copy()
    env["PS2X_GS_CLUT32_SWIZZLE"] = r["swz"]
    env["PS2X_GS_CLUT_DRAWTIME_RELOAD"] = r["rel"]
    env["PS2X_FRAME_DUMP"] = dump_dir
    env["PS2X_FRAME_DUMP_EVERY"] = "60"
    env["PS2X_FRAME_DUMP_MAX"] = "2"

    print(f"\n=======================================================")
    print(f"Running A/B Matrix: {name} (swizzle={r['swz']}, reload={r['rel']})...")
    print(f"=======================================================")

    cmd = ["powershell", "-File", "scripts\\run.ps1", "-TimeoutSeconds", "40"]
    log_path = f"logs/run_matrix_{name}.log"
    with open(log_path, "w") as log_f:
        p = subprocess.Popen(cmd, env=env, stdout=log_f, stderr=subprocess.STDOUT)
        p.wait()

    # Look for dumped frame
    # Frame dump might be in dump_dir or build\PS2Recomp\ps2xRuntime\dump_dir
    search_dirs = [dump_dir, os.path.join("build/PS2Recomp/ps2xRuntime", dump_dir)]
    dumped_windows = []
    for sd in search_dirs:
        dumped_windows.extend(glob.glob(f"{sd}/*window*.png"))

    if not dumped_windows:
        print(f"ERROR: No window dump found for {name}!")
        continue

    # Pick the latest window dump
    ours_png = sorted(dumped_windows)[-1]
    print(f"Found window dump: {ours_png}")

    montage_path = f"logs/montage_{name}.png"
    metric = evaluate_sprite(ours_png, "refs/ref_now_loading.png", montage_path)
    metric["run"] = name
    metric["swizzle"] = r["swz"]
    metric["reload"] = r["rel"]
    metric["ours_png"] = ours_png
    metric["montage"] = montage_path
    results.append(metric)

print("\n" + "="*80)
print("A/B MATRIX RESULTS SUMMARY")
print("="*80)
print(f"{'Run':<12} | {'Swz':<4} | {'Rel':<4} | {'Yellow Frac':<12} | {'Black Frac':<12} | {'MAD':<8} | {'Wrap':<6} | {'Montage'}")
print("-" * 80)
for res in results:
    print(f"{res['run']:<12} | {res['swizzle']:<4} | {res['reload']:<4} | {res['yellow_frac']:<12.4f} | {res['black_frac']:<12.4f} | {res['mad']:<8.2f} | {str(res['has_left_wrap']):<6} | {res['montage']}")
print("="*80)
