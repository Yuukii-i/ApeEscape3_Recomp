import sys, glob, os
sys.path.append('tools/gs')
from eval_metrics import evaluate_sprite

for name in ['swz0_rel0', 'swz0_rel1', 'swz1_rel0', 'swz1_rel1']:
    d = os.path.join('build/PS2Recomp/ps2xRuntime/logs', f'frames_{name}')
    pngs = glob.glob(os.path.join(d, '*window*.png'))
    if pngs:
        m = evaluate_sprite(pngs[0], 'refs/ref_now_loading.png', f'logs/montage_{name}.png')
        print(f"{name}: yellow={m['yellow_frac']:.4f}, black={m['black_frac']:.4f}, mad={m['mad']:.2f}, wrap={m['has_left_wrap']}")
    else:
        print(f"{name}: no window dump found")
