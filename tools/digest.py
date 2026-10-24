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
    cid1_lines = []
    sg2_lines = []
    raw8_lines = []
    f9_f10_lines = []
    last_scene = None

    with open(log_file, 'rb') as bf:
        bom = bf.read(2)
    enc = 'utf-16' if bom in (b'\xff\xfe', b'\xfe\xff') else 'utf-8'
    with open(log_file, 'r', encoding=enc, errors='ignore') as f:
        for line in f:
            line_str = line.strip()
            if line_str.startswith('[probe] first_calls'):
                first_calls_lines.append(line_str)
            elif line_str.startswith('[probe] f9') or line_str.startswith('[probe] f10') or line_str.startswith('[probe] 31a') or line_str.startswith('[probe] str_') or line_str.startswith('[probe] c8') or line_str.startswith('[probe] seek') or line_str.startswith('[probe] scan') or line_str.startswith('[probe] 24c8') or line_str.startswith('[probe] ar'):
                f9_f10_lines.append(line_str)
            elif line_str.startswith('[probe] sif_') or line_str.startswith('[probe] intc_') or line_str.startswith('[probe] vt_write'):
                sif_intc_lines.append(line_str)
            elif '[CID1:batch]' in line_str or '[CID1:Seek:raw_req]' in line_str or '[CID1:Open]' in line_str:
                cid1_lines.append(line_str)
            elif '[sg2]' in line_str:
                sg2_lines.append(line_str)
            elif '[mpeg:raw8]' in line_str:
                raw8_lines.append(line_str)
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

    # Print CID1 Batch / Seek lines
    if cid1_lines:
        show_cid1 = cid1_lines[:25]
        print(f"-- CID1 Batch / Seek ({len(cid1_lines)} total, showing first {len(show_cid1)}) --")
        for cl in show_cid1:
            print(cl)

    # Print SG2 Audio lines
    if sg2_lines:
        show_sg2 = sg2_lines[:25]
        print(f"-- SG2 Audio ({len(sg2_lines)} total, showing first {len(show_sg2)}) --")
        for sl in show_sg2:
            print(sl)

    # Print RAW8 MPEG lines
    if raw8_lines:
        show_raw8 = raw8_lines[:25]
        print(f"-- MPEG RAW8 ({len(raw8_lines)} total, showing first {len(show_raw8)}) --")
        for rl in show_raw8:
            print(rl)

    # Print Task AN f9 / f10 / 31a Probe Lines
    if f9_f10_lines:
        print(f"-- Task AN Probe Lines ({len(f9_f10_lines)}) --")
        for fl in f9_f10_lines:
            print(fl)

    # Print probe lines (last 15 if more)
    if probe_lines:
        show_probe = probe_lines[-15:] if len(probe_lines) > 15 else probe_lines
        print(f"-- Probes/Traces ({len(probe_lines)} total, showing last {len(show_probe)}) --")
        for p in show_probe:
            print(p)

if __name__ == '__main__':
    main()
