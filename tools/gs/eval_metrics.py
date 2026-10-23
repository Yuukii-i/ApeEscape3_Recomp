#!/usr/bin/env python3
"""
tools/gs/eval_metrics.py: Evaluates visual metrics of rendered frames against reference.
"""

import sys
import os
import argparse
import numpy as np
from PIL import Image

def find_sprite_bbox(img_arr, threshold=15):
    # img_arr shape: (H, W, 3) or (H, W, 4)
    rgb = img_arr[:, :, :3]
    mask = (rgb[:, :, 0] > threshold) | (rgb[:, :, 1] > threshold) | (rgb[:, :, 2] > threshold)
    coords = np.argwhere(mask)
    if len(coords) == 0:
        return (0, 0, 0, 0)
    y0, x0 = coords.min(axis=0)
    y1, x1 = coords.max(axis=0) + 1
    return (int(x0), int(y0), int(x1), int(y1))

def evaluate_sprite(ours_path, ref_path, montage_path=None, fixed_box=(192, 352, 320, 416)):
    ours_img = Image.open(ours_path).convert("RGB")
    ours_arr = np.array(ours_img)

    # Sprite crop
    x0, y0, x1, y1 = fixed_box
    ours_crop = ours_arr[y0:y1, x0:x1]

    # Metrics on ours_crop
    total_px = ours_crop.shape[0] * ours_crop.shape[1]
    r, g, b = ours_crop[:, :, 0], ours_crop[:, :, 1], ours_crop[:, :, 2]
    yellow_mask = (r > 180) & (g > 150) & (b < 120)
    black_mask = (r < 30) & (g < 30) & (b < 30)
    yellow_frac = float(np.sum(yellow_mask)) / total_px
    black_frac = float(np.sum(black_mask)) / total_px

    # Edge wrap check: in left 16 columns (x=0..15), check for non-black text pixels
    left_16 = ours_crop[:, 0:16]
    left_non_black = np.sum((left_16[:, :, 0] > 30) | (left_16[:, :, 1] > 30) | (left_16[:, :, 2] > 30))
    # Right 16 columns (x=112..127)
    right_16 = ours_crop[:, 112:128]
    right_non_black = np.sum((right_16[:, :, 0] > 30) | (right_16[:, :, 1] > 30) | (right_16[:, :, 2] > 30))
    has_left_wrap = bool(left_non_black > 20)

    # Reference crop & resize to match ours_crop (128x64)
    ref_img = Image.open(ref_path).convert("RGB")
    ref_crop = ref_img.crop((497, 724, 818, 804)).resize((ours_crop.shape[1], ours_crop.shape[0]), Image.Resampling.BILINEAR)
    ref_arr = np.array(ref_crop)

    # MAD
    mad = float(np.mean(np.abs(ours_crop.astype(np.float32) - ref_arr.astype(np.float32))))

    # Side-by-side montage
    if montage_path:
        w = ours_crop.shape[1]
        h = ours_crop.shape[0]
        # 3x scale for comfortable viewing
        scale = 3
        montage = Image.new("RGB", (w * 2 * scale + 10, h * scale), (40, 40, 40))
        ref_scaled = ref_crop.resize((w * scale, h * scale), Image.Resampling.NEAREST)
        ours_scaled = Image.fromarray(ours_crop).resize((w * scale, h * scale), Image.Resampling.NEAREST)
        montage.paste(ref_scaled, (0, 0))
        montage.paste(ours_scaled, (w * scale + 10, 0))
        os.makedirs(os.path.dirname(montage_path) or ".", exist_ok=True)
        montage.save(montage_path)

    result = {
        "box": (x0, y0, x1, y1),
        "yellow_frac": yellow_frac,
        "black_frac": black_frac,
        "mad": mad,
        "has_left_wrap": has_left_wrap,
        "left_non_black": int(left_non_black),
        "right_non_black": int(right_non_black)
    }
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ours", required=True)
    parser.add_argument("--ref", default="refs/ref_now_loading.png")
    parser.add_argument("--montage", default=None)
    args = parser.parse_args()

    res = evaluate_sprite(args.ours, args.ref, args.montage)
    print(f"Results for {args.ours}:")
    print(f"  Box: {res['box']}")
    print(f"  Yellow fraction: {res['yellow_frac']:.4f} (target ~0.104)")
    print(f"  Near-black fraction: {res['black_frac']:.4f} (target ~0.513)")
    print(f"  MAD vs ref: {res['mad']:.2f}")
    print(f"  Left edge wrap (16px): {res['has_left_wrap']} (non-black count: {res['left_non_black']})")
    if args.montage:
        print(f"  Montage saved: {args.montage}")

if __name__ == "__main__":
    main()
