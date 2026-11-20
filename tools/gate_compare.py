"""Compare baseline and candidate stage screenshots for gate.ps1."""

import os
import re
import sys
from PIL import Image, ImageChops, ImageStat


def infer_stage(path: str) -> str:
    base = os.path.basename(path)
    m = re.match(r"^.+_(?:vb\d+|vc\d+)_(.+)\.png$", base, re.IGNORECASE)
    if m:
        return m.group(1)
    return os.path.splitext(base)[0]


def mean_brightness(img: Image.Image) -> float:
    stat = ImageStat.Stat(img)
    return sum(stat.mean[:3]) / 3.0


def pair_metrics(img1: Image.Image, img2: Image.Image) -> tuple[float, float]:
    diff = ImageChops.difference(img1, img2)
    mean_diff = sum(ImageStat.Stat(diff).mean[:3]) / 3.0
    raw = diff.tobytes()
    n_pix = len(raw) // 3
    if n_pix == 0:
        return 0.0, 0.0
    over = 0
    for i in range(0, len(raw), 3):
        if raw[i] > 24 or raw[i + 1] > 24 or raw[i + 2] > 24:
            over += 1
    return mean_diff, over / n_pix


def main() -> int:
    if len(sys.argv) != 4:
        print("FAIL usage mean=0.000 frac=1.0000 noise_mean=0.000 noise_frac=0.0000")
        return 1

    a_path, b_path, c_path = sys.argv[1:4]
    stage = infer_stage(c_path)

    for p in (a_path, b_path, c_path):
        if not os.path.isfile(p):
            print(f"FAIL {stage} mean=0.000 frac=1.0000 noise_mean=0.000 noise_frac=0.0000")
            return 1

    try:
        a = Image.open(a_path).convert("RGB")
        b = Image.open(b_path).convert("RGB")
        c = Image.open(c_path).convert("RGB")
    except Exception:
        print(f"FAIL {stage} mean=0.000 frac=1.0000 noise_mean=0.000 noise_frac=0.0000")
        return 1

    resample = getattr(Image, "Resampling", Image).BICUBIC
    if b.size != a.size:
        b = b.resize(a.size, resample)
    if c.size != a.size:
        c = c.resize(a.size, resample)

    w, h = a.size
    if h > 100:
        box = (0, 100, w, h)
        a = a.crop(box)
        b = b.crop(box)
        c = c.crop(box)

    if mean_brightness(a) < 3.0 or mean_brightness(b) < 3.0 or mean_brightness(c) < 3.0:
        print(f"FAIL {stage} mean=0.000 frac=1.0000 noise_mean=0.000 noise_frac=0.0000")
        return 1

    noise_mean, noise_frac = pair_metrics(a, b)
    cand_mean, cand_frac = pair_metrics(a, c)

    failed = (cand_mean > max(2.0 * noise_mean, 4.5)) or (cand_frac > max(2.0 * noise_frac, 0.09))
    status = "FAIL" if failed else "OK"
    print(
        f"{status} {stage} mean={cand_mean:.3f} frac={cand_frac:.4f} "
        f"noise_mean={noise_mean:.3f} noise_frac={noise_frac:.4f}"
    )
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
