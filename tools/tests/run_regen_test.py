import os, subprocess, shutil, glob

recomp_exe = os.path.abspath('PS2Recomp/build/ps2xRecomp/ps2_recomp.exe')
regen_dir = os.path.abspath('build/regen_pmfhl')
os.makedirs(regen_dir, exist_ok=True)

with open('config.toml', 'r') as f:
    cfg = f.read()

cfg_regen = cfg.replace('"recomp_source"', f'"{regen_dir.replace(chr(92), "/")}"')
temp_cfg = os.path.abspath('build/temp_config_pmfhl.toml')
with open(temp_cfg, 'w') as f:
    f.write(cfg_regen)

print(f"Running {recomp_exe} with {temp_cfg}...")
res = subprocess.run([recomp_exe, temp_cfg], capture_output=True, text=True)
print(f"Exit code: {res.returncode}")
if res.returncode != 0:
    print("STDOUT:", res.stdout[:500])
    print("STDERR:", res.stderr[:500])
else:
    print("Recompilation finished successfully.")

# Compare ONLY the lines containing PS2_PMFHL between build/regen_pmfhl and recomp_source
mismatches = 0
checked_lines = 0
for sf in glob.glob('recomp_source/*.cpp'):
    fname = os.path.basename(sf)
    rf = os.path.join(regen_dir, fname)
    if not os.path.exists(rf):
        continue
    with open(sf, 'r') as f1, open(rf, 'r') as f2:
        l1 = [line.strip() for line in f1 if 'PS2_PMFHL' in line]
        l2 = [line.strip() for line in f2 if 'PS2_PMFHL' in line]
    if l1 or l2:
        checked_lines += len(l1)
        if l1 != l2:
            print(f"Mismatch in {fname}:")
            print(f"  recomp_source: {l1}")
            print(f"  regen_pmfhl  : {l2}")
            mismatches += 1

print(f"Comparison complete: checked {checked_lines} PS2_PMFHL lines across files. Mismatches: {mismatches}")
