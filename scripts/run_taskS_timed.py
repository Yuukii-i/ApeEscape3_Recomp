import subprocess
import time
import os
import sys

exe = os.path.abspath("build/PS2Recomp/ps2xRuntime/ps2EntryRunner.exe")
elf = os.path.abspath("SCUS_975.01")
out_log = os.path.abspath("logs/run_taskS_test.log")
err_log = os.path.abspath("logs/run_taskS_test_err.log")

env = os.environ.copy()
env["PS2X_AUTO_PAD"] = "1"
env["PS2X_DUMP_FRAMES"] = "30"

print(f"Launching {exe} with ELF {elf} for 150 seconds...")
stdout_file = open(out_log, "w", encoding="utf-8")
stderr_file = open(err_log, "w", encoding="utf-8")

proc = subprocess.Popen([exe, elf], stdout=stdout_file, stderr=stderr_file, env=env)

try:
    for s in range(150):
        time.sleep(1)
        if proc.poll() is not None:
            print(f"Process exited at {s+1} seconds with code {proc.returncode}")
            break
        if (s + 1) % 10 == 0:
            print(f"Running... {s+1}s elapsed")
finally:
    if proc.poll() is None:
        print("150s timeout reached, terminating runner...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
    stdout_file.close()
    stderr_file.close()

print("Run complete.")
