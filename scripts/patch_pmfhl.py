import os, glob, re

target_dir = 'recomp_source'
old_pattern = re.compile(r'PS2_PMFHL_LW\(ctx->hi,\s*ctx->lo\)')
new_replacement = 'PS2_PMFHL_LW(ctx->hi, ctx->lo, ctx->hi1, ctx->lo1)'

files_changed = 0
lines_changed = 0
before_shapes = set()
after_shapes = set()

for filepath in glob.glob(os.path.join(target_dir, '*.cpp')):
    with open(filepath, 'r', errors='ignore') as f:
        content = f.read()
    
    if 'PS2_PMFHL_LW(ctx->hi, ctx->lo)' in content:
        lines = content.splitlines(keepends=True)
        new_lines = []
        file_modified = False
        for line in lines:
            if 'PS2_PMFHL_LW(ctx->hi, ctx->lo)' in line:
                before_shapes.add(line.strip())
                new_line = old_pattern.sub(new_replacement, line)
                after_shapes.add(new_line.strip())
                new_lines.append(new_line)
                lines_changed += 1
                file_modified = True
            else:
                new_lines.append(line)
        
        if file_modified:
            files_changed += 1
            with open(filepath, 'w', newline='') as f:
                f.writelines(new_lines)

print(f"Files changed: {files_changed}")
print(f"Lines changed: {lines_changed}")
print("\nDistinct before line shapes:")
for s in sorted(before_shapes):
    print(f"  BEFORE: {s}")
print("\nDistinct after line shapes:")
for s in sorted(after_shapes):
    print(f"  AFTER : {s}")
