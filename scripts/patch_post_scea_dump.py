path = 'PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp'
with open(path, 'r', encoding='utf-8') as f:
    c = f.read()

target = '    if (currentTick >= 160)\n    {\n'
assert target in c, 'Target not found in ps2_runtime.cpp'

addition = """    if (currentTick >= 250)
    {
        static uint64_t s_lastPostSceaDump = 0;
        if (currentTick >= s_lastPostSceaDump + 50 && !s_scratch.empty() && width != 0 && height != 0 && hasNonZeroPixels)
        {
            s_lastPostSceaDump = currentTick;
            extern void writeUncompressedPng(uint32_t w, uint32_t h, const uint8_t *rgba, const char *filename);
            std::filesystem::create_directories("frames");
            std::string name = "frames/frame_post_scea_" + std::to_string(currentTick) + ".png";
            writeUncompressedPng(width, height, s_scratch.data(), name.c_str());
            ps2xSafeLog("[frame:dump] Dumped post-SCEA frame at tick=%llu hash=0x%08x to %s\\n",
                        (unsigned long long)currentTick, frameHash, name.c_str());
        }
    }
"""

c = c.replace(target, addition + target, 1)
with open(path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(c)
print('Added post-SCEA periodic frame dumper')
