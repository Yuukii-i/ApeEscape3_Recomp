#!/usr/bin/env python3
"""Analyze PresentMon + per-thread CPU CSVs produced by tools/pcsx2_frametime.ps1."""

import argparse
import csv
import math
import os
import sys
from collections import Counter, defaultdict


def percentile(sorted_vals, pct):
    if not sorted_vals:
        return 0.0
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    idx = (pct / 100.0) * (len(sorted_vals) - 1)
    lo = int(math.floor(idx))
    hi = int(math.ceil(idx))
    if lo == hi:
        return sorted_vals[lo]
    frac = idx - lo
    return sorted_vals[lo] * (1.0 - frac) + sorted_vals[hi] * frac


def low_fps(ft_ms_list, pct_slowest):
    if not ft_ms_list:
        return 0.0
    n = max(1, int(len(ft_ms_list) * (pct_slowest / 100.0)))
    slowest = sorted(ft_ms_list, reverse=True)[:n]
    mean_ms = sum(slowest) / len(slowest)
    return 1000.0 / mean_ms if mean_ms > 0.0 else 0.0


def parse_float(val, default=None):
    try:
        v = float(val)
        return v if math.isfinite(v) else default
    except (TypeError, ValueError):
        return default


def load_presents(path):
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames:
            return []
        col_map = {c.strip().lower(): c for c in reader.fieldnames if c}

        time_col = (
            col_map.get("timeinseconds")
            or col_map.get("cpustarttime")
            or col_map.get("cpustartqpc")
        )
        ft_col = col_map.get("msbetweenpresents") or col_map.get("frametime")
        swap_col = col_map.get("swapchainaddress")

        if not time_col or not ft_col:
            raise ValueError(
                f"Unrecognized PresentMon columns in {path}: {reader.fieldnames}"
            )

        for r in reader:
            t = parse_float(r.get(time_col))
            ft = parse_float(r.get(ft_col))
            if t is None or ft is None or ft <= 0.0:
                continue
            sc = (r.get(swap_col) or "").strip() if swap_col else ""
            rows.append((t, ft, sc))

    if not rows:
        return []

    if any(sc for _, _, sc in rows):
        counts = Counter(sc for _, _, sc in rows if sc)
        if counts:
            main_sc, _ = counts.most_common(1)[0]
            rows = [(t, ft, sc) for t, ft, sc in rows if sc == main_sc]

    rows.sort(key=lambda x: x[0])
    return [(t, ft) for t, ft, _ in rows]


def load_cpu_windows(path):
    if not os.path.exists(path):
        return [], []
    with open(path, "r", newline="", encoding="utf-8-sig", errors="replace") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        if not header or len(header) < 3:
            return [], []
        thread_cols = header[3:]
        windows = []
        t_prev = 0.0
        for row in reader:
            if not row or len(row) < 3:
                continue
            t_curr = parse_float(row[0])
            tag_val = parse_float(row[1], 0.0)
            total_cpu = parse_float(row[2], 0.0)
            if t_curr is None or t_curr <= t_prev:
                continue
            thr_deltas = {}
            for idx, name in enumerate(thread_cols):
                col_i = 3 + idx
                val = parse_float(row[col_i], 0.0) if col_i < len(row) else 0.0
                thr_deltas[name] = val
            windows.append(
                {
                    "t_start": t_prev,
                    "t_end": t_curr,
                    "dt": t_curr - t_prev,
                    "tag": int(tag_val),
                    "total_cpu_ms": total_cpu,
                    "thr_deltas": thr_deltas,
                }
            )
            t_prev = t_curr
    return windows, thread_cols


def align_windows(windows, presents, drop_warmup):
    p_idx = 0
    n_p = len(presents)
    aligned = []
    for w in windows:
        t0, t1, dt = w["t_start"], w["t_end"], w["dt"]
        while p_idx < n_p and presents[p_idx][0] < t0:
            p_idx += 1
        win_presents = []
        j = p_idx
        while j < n_p and presents[j][0] < t1:
            win_presents.append(presents[j][1])
            j += 1
        p_idx = j

        if t1 <= drop_warmup:
            continue

        frames = len(win_presents)
        fps = frames / dt if dt > 0 else 0.0
        cpu_pf = w["total_cpu_ms"] / frames if frames > 0 else 0.0
        thr_pf = {
            name: (val / frames if frames > 0 else 0.0)
            for name, val in w["thr_deltas"].items()
        }
        aligned.append(
            {
                "t_start": t0,
                "t_end": t1,
                "dt": dt,
                "tag": w["tag"],
                "frames": frames,
                "fps": fps,
                "cpu_ms_total": w["total_cpu_ms"],
                "cpu_ms_per_frame": cpu_pf,
                "thr_ms_per_frame": thr_pf,
                "frame_times": win_presents,
            }
        )
    return aligned


def format_section(title, frame_times, windows, thread_cols):
    lines = [f"=== {title} ==="]
    n_frames = len(frame_times)
    if n_frames > 0:
        s_ft = sorted(frame_times)
        mean_ft = sum(s_ft) / n_frames
        avg_fps = 1000.0 / mean_ft if mean_ft > 0 else 0.0
        p50 = percentile(s_ft, 50)
        p95 = percentile(s_ft, 95)
        p99 = percentile(s_ft, 99)
        p999 = percentile(s_ft, 99.9)
        ft_max = s_ft[-1]
        low1 = low_fps(s_ft, 1.0)
        low01 = low_fps(s_ft, 0.1)
        fps_p99 = 1000.0 / p99 if p99 > 0 else 0.0
        lines.append(
            f"Frames: {n_frames} | Avg FPS: {avg_fps:.2f} | "
            f"1% low: {low1:.2f} fps | 0.1% low: {low01:.2f} fps | FPS@p99: {fps_p99:.2f}"
        )
        lines.append(
            f"Frame time (ms): p50={p50:.2f}  p95={p95:.2f}  "
            f"p99={p99:.2f}  p99.9={p999:.2f}  max={ft_max:.2f}"
        )
    else:
        lines.append("Frames: 0 (no presents in this slice)")

    valid_wins = [w for w in windows if w["frames"] > 0]
    if valid_wins:
        cpf = sorted(w["cpu_ms_per_frame"] for w in valid_wins)
        cpf_mean = sum(cpf) / len(cpf)
        lines.append(
            f"CPU ms/frame ({len(valid_wins)} windows): mean={cpf_mean:.2f}  "
            f"p50={percentile(cpf, 50):.2f}  p90={percentile(cpf, 90):.2f}  "
            f"p95={percentile(cpf, 95):.2f}  p99={percentile(cpf, 99):.2f}  max={cpf[-1]:.2f}"
        )
        thr_means = []
        for col in thread_cols:
            m = sum(w["thr_ms_per_frame"].get(col, 0.0) for w in valid_wins) / len(valid_wins)
            if m >= 0.01:
                thr_means.append((m, col))
        thr_means.sort(reverse=True)
        if thr_means:
            lines.append("Per-thread mean CPU ms/frame:")
            for m, col in thr_means:
                lines.append(f"  {col:<24} {m:7.2f} ms/frame")
    else:
        lines.append("CPU ms/frame: no windows with frames > 0")
    lines.append("")
    return lines


def format_histogram(valid_wins):
    if not valid_wins:
        return ["CPU/frame histogram: (no data)"]
    vals = [w["cpu_ms_per_frame"] for w in valid_wins]
    lo, hi = min(vals), max(vals)
    if hi <= lo:
        return [f"CPU/frame histogram: all {len(vals)} windows at {lo:.2f} ms"]
    bins = 8
    step = (hi - lo) / bins
    counts = [0] * bins
    for v in vals:
        idx = min(bins - 1, int((v - lo) / step))
        counts[idx] += 1
    max_c = max(counts) or 1
    lines = ["CPU/frame histogram (windows):"]
    for i in range(bins):
        b0 = lo + i * step
        b1 = lo + (i + 1) * step
        bar = "#" * max(1, int(round(24 * counts[i] / max_c))) if counts[i] > 0 else ""
        lines.append(f"  [{b0:6.2f} - {b1:6.2f} ms) {counts[i]:4d} {bar}")
    return lines


def write_windows_csv(path, windows, thread_cols):
    header = [
        "t_start",
        "t_end",
        "dt",
        "tag",
        "frames",
        "fps",
        "cpu_ms_total",
        "cpu_ms_per_frame",
    ] + list(thread_cols)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        for row in windows:
            vals = [
                f"{row['t_start']:.3f}",
                f"{row['t_end']:.3f}",
                f"{row['dt']:.3f}",
                row["tag"],
                row["frames"],
                f"{row['fps']:.2f}",
                f"{row['cpu_ms_total']:.3f}",
                f"{row['cpu_ms_per_frame']:.3f}",
            ] + [f"{row['thr_ms_per_frame'].get(c, 0.0):.3f}" for c in thread_cols]
            w.writerow(vals)


def run_report(prefix, drop_warmup, quiet=False):
    presents_path = f"{prefix}_presents.csv"
    cpu_path = f"{prefix}_cpu.csv"
    windows_path = f"{prefix}_windows.csv"
    report_path = f"{prefix}_report.txt"
    args = argparse.Namespace(out_prefix=prefix, drop_warmup=drop_warmup)

    presents = load_presents(presents_path)
    windows, thread_cols = load_cpu_windows(cpu_path)

    if not windows:
        msg = f"No CPU windows found in {cpu_path}."
        print(msg)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(msg + "\n")
        return 1, None

    aligned = align_windows(windows, presents, args.drop_warmup)
    if not aligned:
        aligned = align_windows(windows, presents, 0.0)

    write_windows_csv(windows_path, aligned, thread_cols)

    all_ft = [ft for w in aligned for ft in w["frame_times"]]
    if not all_ft and presents:
        all_ft = [ft for t, ft in presents if t >= args.drop_warmup]

    report_lines = [
        f"Frametime Report: {args.out_prefix} (drop_warmup={args.drop_warmup}s)",
        f"Presents file: {presents_path} ({len(presents)} valid presents)",
        f"CPU windows file: {cpu_path} ({len(aligned)} windows after warmup)",
        "",
    ]
    report_lines.extend(format_section("OVERALL", all_ft, aligned, thread_cols))

    by_tag = defaultdict(list)
    for w in aligned:
        by_tag[w["tag"]].append(w)
    if len(by_tag) > 1 or (len(by_tag) == 1 and 0 not in by_tag):
        for tag in sorted(by_tag.keys()):
            wins = by_tag[tag]
            tag_ft = [ft for w in wins for ft in w["frame_times"]]
            report_lines.extend(format_section(f"TAG {tag}", tag_ft, wins, thread_cols))

    valid_wins = [w for w in aligned if w["frames"] > 0]
    heaviest = sorted(valid_wins, key=lambda w: w["cpu_ms_per_frame"], reverse=True)[:5]
    report_lines.append("Top 5 heaviest windows (by cpu/frame):")
    if heaviest:
        for w in heaviest:
            report_lines.append(
                f"  t={w['t_start']:.1f}-{w['t_end']:.1f}s  tag={w['tag']}  "
                f"cpu/frame={w['cpu_ms_per_frame']:.2f} ms  fps={w['fps']:.1f}"
            )
    else:
        report_lines.append("  (none)")
    report_lines.append("")
    report_lines.extend(format_histogram(valid_wins))
    report_lines.append("")
    report_lines.append(
        "Note: cpu/frame is only comparable when presented frames == emulated frames "
        "and the frame limiter is on; PCSX2 spin-waits can inflate CPU."
    )

    text = "\n".join(report_lines) + "\n"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(text)
    if not quiet:
        print(text, end="")
    info = {
        "presents": len(presents),
        "all_ft": all_ft,
        "tags": sorted(by_tag.keys()),
        "windows": len(aligned),
    }
    return 0, info


def selftest():
    import tempfile

    tmp = tempfile.mkdtemp(prefix="ft_selftest_")
    prefix = os.path.join(tmp, "st")
    total_t = 28.0
    t = 0.0
    i = 0
    main_rows = []
    while t < total_t:
        if i % 1000 == 500:
            ft = 80.0
        elif i % 100 == 50:
            ft = 40.0
        else:
            ft = 1000.0 / 60.0
        t += ft / 1000.0
        main_rows.append((t, ft))
        i += 1
    with open(prefix + "_presents.csv", "w", newline="") as f:
        f.write("Application,SwapChainAddress,TimeInSeconds,msBetweenPresents\n")
        for tt, ft in main_rows:
            f.write(f"fake.exe,0xAAAA,{tt:.6f},{ft:.4f}\n")
        for k in range(20):
            f.write(f"fake.exe,0xBBBB,{1.0 + k * 1.3:.6f},{1300.0:.4f}\n")
    with open(prefix + "_cpu.csv", "w", newline="") as f:
        f.write("t_seconds_since_start,tag,total_cpu_ms_delta,EE,GS,VU1\n")
        for w in range(1, 15):
            tag = 0 if w <= 7 else 1
            f.write(f"{w * 2.0:.3f},{tag},2000.000,1000.0,600.0,300.0\n")

    rc, info = run_report(prefix, 5.0, quiet=True)
    errs = []
    if rc != 0 or info is None:
        errs.append("report failed")
    else:
        ft = info["all_ft"]
        s_ft = sorted(ft)
        if not ft:
            errs.append("no frames")
        else:
            avg = 1000.0 / (sum(ft) / len(ft))
            p50_fps = 1000.0 / percentile(s_ft, 50)
            low1 = low_fps(s_ft, 1.0)
            if not (57.0 <= avg <= 60.5):
                errs.append(f"avg fps {avg:.2f} not in 57..60.5")
            if not (low1 < p50_fps * 0.75):
                errs.append(f"1% low {low1:.2f} not well below p50 {p50_fps:.2f}")
            if max(ft) < 79.0:
                errs.append("80 ms frames missing")
            if max(ft) > 100.0:
                errs.append("wrong swap chain chosen (1300 ms frames present)")
        if info["presents"] != len(main_rows):
            errs.append(f"swap chain filter: {info['presents']} presents, expected {len(main_rows)}")
        if info["tags"] != [0, 1]:
            errs.append(f"tags {info['tags']} != [0, 1]")
    if errs:
        print("FAIL: " + "; ".join(errs))
        return 1
    print("PASS")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Analyze PresentMon + CPU frametime logs.")
    ap.add_argument("out_prefix", nargs="?", help="Output prefix (e.g. logs\\ft_pcsx2-qt_...)")
    ap.add_argument("--drop-warmup", type=float, default=5.0, help="Seconds of warmup to drop")
    ap.add_argument("--selftest", action="store_true", help="Run synthetic self-test")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.out_prefix:
        ap.error("out_prefix required unless --selftest")
    rc, _ = run_report(args.out_prefix, args.drop_warmup)
    return rc


if __name__ == "__main__":
    sys.exit(main())
