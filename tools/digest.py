import sys
import os
import glob

def main():
    if len(sys.argv) > 1:
        log_file = sys.argv[1]
    else:
        logs = glob.glob('logs/*.log') + glob.glob('logs/*.txt')
        if not logs:
            print("No log files found in logs/")
            return
        log_file = max(logs, key=os.path.getmtime)

    if not os.path.exists(log_file):
        print(f"File not found: {log_file}")
        return

    print(f"=== DIGEST: {log_file} ===")
    movie_lines = []
    scene_lines = []
    fps_line = None
    probe_lines = []
    first_calls_lines = []
    sif_intc_lines = []
    last_scene = None

    with open(log_file, 'rb') as bf:
        bom = bf.read(2)
    enc = 'utf-16' if bom in (b'\xff\xfe', b'\xfe\xff') else 'utf-8'
    with open(log_file, 'r', encoding=enc, errors='ignore') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith('[probe] first_calls'):
                first_calls_lines.append(line_str)
            elif line_str.startswith('[probe] sif_') or line_str.startswith('[probe] intc_'):
                sif_intc_lines.append(line_str)
            elif '[movie]' in line_str:
                movie_lines.append(line_str)
                if len(movie_lines) > 2:
                    movie_lines.pop(0)
            elif '[scene]' in line_str:
                if line_str != last_scene:
                    scene_lines.append(line_str)
                    last_scene = line_str
            elif '[fps]' in line_str:
                fps_line = line_str
            elif '[probe' in line_str or '[trace]' in line_str:
                probe_lines.append(line_str)

    # Print distinct scenes
    if scene_lines:
        print(f"-- Scenes ({len(scene_lines)}) --")
        for s in scene_lines[:10]:
            print(s)

    # Print last fps
    if fps_line:
        print(f"-- Last FPS --\n{fps_line}")

    # Print last 2 movie lines
    if movie_lines:
        print(f"-- Last Movie Lines ({len(movie_lines)}) --")
        for m in movie_lines:
            print(m)

    # Print one-time first_calls lines
    if first_calls_lines:
        print(f"-- First Calls ({len(first_calls_lines)}) --")
        for fc in first_calls_lines:
            print(fc)

    # Print one-time SIF / INTC lines
    if sif_intc_lines:
        print(f"-- SIF/INTC Events ({len(sif_intc_lines)}) --")
        for si in sif_intc_lines:
            print(si)

    # Print probe lines (last 15 if more)
    if probe_lines:
        show_probe = probe_lines[-15:] if len(probe_lines) > 15 else probe_lines
        print(f"-- Probes/Traces ({len(probe_lines)} total, showing last {len(show_probe)}) --")
        for p in show_probe:
            print(p)

if __name__ == '__main__':
    main()
