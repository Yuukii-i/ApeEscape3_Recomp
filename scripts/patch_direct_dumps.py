with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'rb') as f:
    content = f.read()

target = b'''    if (dbp == 10752 || dbp == 10784)
    {
        static int s_upLogCount = 0;
        if (s_upLogCount++ < 10)
        {
            std::fprintf(stderr, "[GS:UPLOAD_IMAGE] dbp=%u dpsm=0x%02X sizeBytes=%u first8=[%u,%u,%u,%u,%u,%u,%u,%u]\\n",
                         dbp, m_transfer.bitbltbuf.dpsm, sizeBytes,
                         data[0], data[1], data[2], data[3], data[4], data[5], data[6], data[7]);
            std::fflush(stderr);
        }
    }'''

replacement = b'''    if (dbp == 10752)
    {
        static bool s_dumped10752 = false;
        if (!s_dumped10752)
        {
            s_dumped10752 = true;
            std::filesystem::create_directories("logs/gs");
            FILE *f = std::fopen("logs/gs/upload_fixed_10752.bin", "wb");
            if (f) { std::fwrite(data, 1, sizeBytes, f); std::fclose(f); }
            std::fprintf(stderr, "[GS:UPLOAD_IMAGE] Dumped fixed upload to logs/gs/upload_fixed_10752.bin (size=%u)\\n", sizeBytes);
            std::fflush(stderr);
        }
    }
    if (dbp == 10784)
    {
        static bool s_dumped10784 = false;
        if (!s_dumped10784)
        {
            s_dumped10784 = true;
            std::filesystem::create_directories("logs/gs");
            FILE *f = std::fopen("logs/gs/upload_fixed_10784.bin", "wb");
            if (f) { std::fwrite(data, 1, sizeBytes, f); std::fclose(f); }
            std::fprintf(stderr, "[GS:UPLOAD_IMAGE] Dumped fixed upload to logs/gs/upload_fixed_10784.bin (size=%u)\\n", sizeBytes);
            std::fflush(stderr);
        }
    }'''

if b'\r\n' in content:
    target = target.replace(b'\n', b'\r\n')
    replacement = replacement.replace(b'\n', b'\r\n')

assert target in content, 'Target not found in gs_cpu_backend.cpp!'
content = content.replace(target, replacement, 1)

# Also ensure tex_2 is dumped to frames/tex when tbp0=10752 in DrawPrimitive!
target_prim = b'''    if (s_texDump == 1 && state.prim.tme && s_dumpedTexKeys.size() < 16u)'''
replacement_prim = b'''    if ((s_texDump == 1 || ctx.tex0.tbp0 == 10752u) && state.prim.tme && s_dumpedTexKeys.size() < 16u)'''

if b'\r\n' in content:
    target_prim = target_prim.replace(b'\n', b'\r\n')
    replacement_prim = replacement_prim.replace(b'\n', b'\r\n')

assert target_prim in content, 'Target prim not found in gs_cpu_backend.cpp!'
content = content.replace(target_prim, replacement_prim, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'wb') as f:
    f.write(content)
print('Successfully patched gs_cpu_backend.cpp!')
