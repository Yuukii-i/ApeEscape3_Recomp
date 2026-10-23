import sys
import numpy as np
from PIL import Image

def compare_textures(dump_path, ref_path):
    dump_im = Image.open(dump_path).convert('RGBA')
    ref_im = Image.open(ref_path).convert('RGBA')
    
    print(f"Comparing dump: {dump_path} ({dump_im.size}) vs ref: {ref_path} ({ref_im.size})")
    
    # Resize or assert size
    if dump_im.size != ref_im.size:
        print(f"Size mismatch: {dump_im.size} vs {ref_im.size}")
        return
        
    w, h = dump_im.size
    dump_arr = np.array(dump_im, dtype=np.uint8)
    ref_arr = np.array(ref_im, dtype=np.uint8)
    
    # Normalize alpha: A=128 -> 255 if ref or dump has PS2 alpha convention
    # Let's inspect RGB differences where ref alpha > 0
    ref_rgb = ref_arr[:, :, :3]
    dump_rgb = dump_arr[:, :, :3]
    
    diff_rgb = np.abs(ref_rgb.astype(int) - dump_rgb.astype(int))
    mismatches = np.any(diff_rgb > 2, axis=2) # tolerance of 2
    mismatch_pct = (np.count_nonzero(mismatches) / (w * h)) * 100.0
    print(f"Direct Mismatch (tolerance 2): {mismatch_pct:.2f}% ({np.count_nonzero(mismatches)} / {w*h} px)")
    
    # Cyclic shift search (dx, dy)
    best_shift = (0, 0)
    min_mismatch_pct = mismatch_pct
    for dy in range(-8, 9):
        for dx in range(-32, 33):
            shifted_dump = np.roll(np.roll(dump_rgb, dy, axis=0), dx, axis=1)
            diff = np.abs(ref_rgb.astype(int) - shifted_dump.astype(int))
            pct = (np.count_nonzero(np.any(diff > 2, axis=2)) / (w * h)) * 100.0
            if pct < min_mismatch_pct:
                min_mismatch_pct = pct
                best_shift = (dx, dy)
                
    print(f"Best cyclic shift (dx={best_shift[0]}, dy={best_shift[1]}): {min_mismatch_pct:.2f}% mismatch")
    
    # 16x16 block mapping analysis
    print("\n16x16 Block Mapping Analysis:")
    bx_count = w // 16
    by_count = h // 16
    for by in range(by_count):
        for bx in range(bx_count):
            ref_blk = ref_rgb[by*16:(by+1)*16, bx*16:(bx+1)*16]
            # Search which 16x16 block in dump best matches this ref block
            best_blk = None
            best_diff = 1e9
            for dby in range(by_count):
                for dbx in range(bx_count):
                    dump_blk = dump_rgb[dby*16:(dby+1)*16, dbx*16:(dbx+1)*16]
                    d = np.sum(np.abs(ref_blk.astype(int) - dump_blk.astype(int)))
                    if d < best_diff:
                        best_diff = d
                        best_blk = (dbx, dby)
            print(f"  Ref Block ({bx}, {by}) best matches Dump Block {best_blk} with sum L1 diff={best_diff}")
            
    # Sample some mismatched pixels
    print("\nSample Mismatched Pixels (ref vs dump):")
    mismatched_coords = np.argwhere(mismatches)
    for y, x in mismatched_coords[:15]:
        print(f"  ({x:3d}, {y:3d}): Ref={ref_arr[y,x].tolist()} Dump={dump_arr[y,x].tolist()}")

if __name__ == '__main__':
    dump_file = sys.argv[1] if len(sys.argv) > 1 else 'frames/tex/tex_2_tbp10752_psm0x13_128x64.png'
    ref_file = sys.argv[2] if len(sys.argv) > 2 else 'refs/pcsx2_dumps/9f84bb7963941376-179ef34bcdc6a643-000019d3.png'
    compare_textures(dump_file, ref_file)
