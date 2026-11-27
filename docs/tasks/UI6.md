# Task UI6: clip HUD-anchored draws to the HUD safe box. One file, one edit. Do NOT explore, build, run or commit.
File: PS2Recomp/ps2xRuntime/src/lib/render/rd_view.cpp, inside the `// FIX-UI5` block (about line 4140).
Today only `anchor == 0` batches get their scissor adjusted. Directly after that `if (anchor == 0 && b.scissor != 0ull) { ... }` block add:
```cpp
                    else if (anchor != 0 && m > 0.0f && b.scissor != 0ull) // FIX-UI6: off-frame HUD stays hidden in the side margins
                    {
                        const float n0 = std::min(2047.0f, std::floor(m));
                        const float n1 = std::max(n0, std::min(2047.0f, std::ceil(fbW - m) - 1.0f));
                        b.scissor = (b.scissor & ~(0x7FFull | (0x7FFull << 16))) |
                                    static_cast<uint64_t>(n0) | (static_cast<uint64_t>(n1) << 16);
                    }
```
Reply in <=2 lines.
