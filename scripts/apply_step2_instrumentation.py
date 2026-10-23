import sys

with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'r', encoding='utf-8') as f:
    src = f.read()

# 1. Update DumpedTexKey and globals
t_old1 = '''struct DumpedTexKey {
    uint32_t tbp0;
    uint32_t cbp;
    uint8_t psm;
    uint32_t w;
    uint32_t h;
    uint32_t clutHash;
};
static std::vector<DumpedTexKey> s_dumpedTexKeys;'''

t_new1 = '''static int s_primLogFrom = -1;
static int s_primLogMax = -1;
static int s_drawStepDump = -1;

struct DumpedTexKey {
    uint32_t tbp0;
    uint32_t tbw;
    uint8_t psm;
    uint32_t tw;
    uint32_t th;
    uint32_t cbp;
    uint8_t cpsm;
    uint8_t csm;
    uint8_t csa;
    uint32_t clutHash;
};
static std::vector<DumpedTexKey> s_dumpedTexKeys;'''

assert t_old1 in src, 't_old1 not found'
src = src.replace(t_old1, t_new1, 1)

# 2. Add prim logging window before s_clutDrawtimeReload
t_old2 = '''    if (s_clutDrawtimeReload == -1)'''

t_new2 = '''    static std::atomic<uint32_t> s_globalPrimIndex{0};
    uint32_t currentPrimIdx = s_globalPrimIndex.fetch_add(1u, std::memory_order_relaxed);

    if (s_primLogFrom == -1)
    {
        const char *envFrom = std::getenv("PS2X_GS_PRIM_LOG_FROM");
        s_primLogFrom = envFrom ? std::atoi(envFrom) : 0;
        const char *envMax = std::getenv("PS2X_GS_PRIM_LOG_MAX");
        s_primLogMax = envMax ? std::atoi(envMax) : 0;
    }

    if (s_primLogMax > 0 &&
        currentPrimIdx >= static_cast<uint32_t>(s_primLogFrom) &&
        currentPrimIdx < static_cast<uint32_t>(s_primLogFrom + s_primLogMax))
    {
        const char *primName = "UNKNOWN";
        switch (state.prim.type)
        {
        case GS_PRIM_POINT: primName = "POINT"; break;
        case GS_PRIM_LINE: primName = "LINE"; break;
        case GS_PRIM_LINESTRIP: primName = "LINESTRIP"; break;
        case GS_PRIM_TRIANGLE: primName = "TRIANGLE"; break;
        case GS_PRIM_TRISTRIP: primName = "TRISTRIP"; break;
        case GS_PRIM_TRIFAN: primName = "TRIFAN"; break;
        case GS_PRIM_SPRITE: primName = "SPRITE"; break;
        }
        int ofx = ctx.xyoffset.ofx >> 4;
        int ofy = ctx.xyoffset.ofy >> 4;
        float x0 = batch.vertices.size() > 0 ? (batch.vertices[0].x - static_cast<float>(ofx)) : 0.f;
        float y0 = batch.vertices.size() > 0 ? (batch.vertices[0].y - static_cast<float>(ofy)) : 0.f;
        float x1 = batch.vertices.size() > 1 ? (batch.vertices[1].x - static_cast<float>(ofx)) : 0.f;
        float y1 = batch.vertices.size() > 1 ? (batch.vertices[1].y - static_cast<float>(ofy)) : 0.f;

        std::fprintf(stderr, "[GS:PRIM] idx=%u type=%s(0x%x) fbp=%u fbw=%u psm=0x%x tme=%u abe=%u fst=%u "
                             "tbp0=%u tbw=%u tpsm=0x%x tw=%u th=%u cbp=%u cpsm=0x%x csm=%u csa=%u "
                             "alpha=0x%llx test=0x%llx rect=(%.1f,%.1f)-(%.1f,%.1f) v1_rgba=(%u,%u,%u,%u)\\n",
                     currentPrimIdx, primName, static_cast<unsigned>(state.prim.type),
                     ctx.frame.fbp, ctx.frame.fbw, static_cast<unsigned>(ctx.frame.psm),
                     state.prim.tme, state.prim.abe, state.prim.fst,
                     ctx.tex0.tbp0, static_cast<unsigned>(ctx.tex0.tbw), static_cast<unsigned>(ctx.tex0.psm),
                     static_cast<unsigned>(ctx.tex0.tw), static_cast<unsigned>(ctx.tex0.th),
                     (ctx.tex0.cbp != 0u) ? ctx.tex0.cbp : m_clutCbp[0],
                     static_cast<unsigned>(ctx.tex0.cpsm), static_cast<unsigned>(ctx.tex0.csm), static_cast<unsigned>(ctx.tex0.csa),
                     static_cast<unsigned long long>(ctx.alpha), static_cast<unsigned long long>(ctx.test),
                     x0, y0, x1, y1,
                     batch.vertices.size() > 1 ? batch.vertices[1].r : (batch.vertices.size() > 0 ? batch.vertices[0].r : 0),
                     batch.vertices.size() > 1 ? batch.vertices[1].g : (batch.vertices.size() > 0 ? batch.vertices[0].g : 0),
                     batch.vertices.size() > 1 ? batch.vertices[1].b : (batch.vertices.size() > 0 ? batch.vertices[0].b : 0),
                     batch.vertices.size() > 1 ? batch.vertices[1].a : (batch.vertices.size() > 0 ? batch.vertices[0].a : 0));
        std::fflush(stderr);
    }

    if (s_clutDrawtimeReload == -1)'''

assert t_old2 in src, 't_old2 not found'
src = src.replace(t_old2, t_new2, 1)

# 3. Update tex dump logic
t_old3 = '''    if (s_texDump == -1)
    {
        const char *env = std::getenv("PS2X_GS_TEXDUMP");
        s_texDump = (env && (std::strcmp(env, "1") == 0 || std::strcmp(env, "true") == 0)) ? 1 : 0;
    }
    if (s_texDump == 1 && state.prim.tme && s_dumpedTexKeys.size() < 16u)
    {
        const uint32_t effectiveCbp = (ctx.tex0.cbp != 0u) ? ctx.tex0.cbp : m_clutCbp[0];
        uint32_t clutHash = calculateCrc32(reinterpret_cast<const uint8_t*>(m_clut.data()), sizeof(m_clut));
        uint32_t tw_px = 1u << ctx.tex0.tw;
        uint32_t th_px = 1u << ctx.tex0.th;

        bool alreadyDumped = false;
        for (const auto &k : s_dumpedTexKeys)
        {
            if (k.tbp0 == ctx.tex0.tbp0 && k.cbp == effectiveCbp && k.psm == ctx.tex0.psm &&
                k.w == tw_px && k.h == th_px && k.clutHash == clutHash)
            {
                alreadyDumped = true;
                break;
            }
        }
        if (!alreadyDumped)
        {
            s_dumpedTexKeys.push_back({ctx.tex0.tbp0, effectiveCbp, ctx.tex0.psm, tw_px, th_px, clutHash});
            uint32_t seq = static_cast<uint32_t>(s_dumpedTexKeys.size());
            std::vector<uint8_t> sampledRgba(tw_px * th_px * 4u, 0u);
            for (uint32_t sy = 0; sy < th_px; ++sy)
            {
                for (uint32_t sx = 0; sx < tw_px; ++sx)
                {
                    uint32_t rgba = SampleTexture(state, 0.f, 0.f, 1.f, static_cast<uint16_t>(sx * 16u), static_cast<uint16_t>(sy * 16u));
                    sampledRgba[(sy * tw_px + sx) * 4u + 0] = static_cast<uint8_t>(rgba & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 1] = static_cast<uint8_t>((rgba >> 8u) & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 2] = static_cast<uint8_t>((rgba >> 16u) & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 3] = static_cast<uint8_t>((rgba >> 24u) & 0xFFu);
                }
            }
            char fn[256];
            std::snprintf(fn, sizeof(fn), "logs/gs/tex_%u_tbp%u_psm0x%02x_%ux%u.png",
                          seq, ctx.tex0.tbp0, static_cast<unsigned>(ctx.tex0.psm), tw_px, th_px);
            writeUncompressedPng(tw_px, th_px, sampledRgba.data(), fn);

            // Dump CLUT 16x16
            std::vector<uint8_t> clutRgba(16u * 16u * 4u, 0u);
            for (uint32_t ci = 0; ci < 256u; ++ci)
            {
                uint32_t raw = (ctx.tex0.cpsm == GS_PSM_CT16 || ctx.tex0.cpsm == GS_PSM_CT16S)
                    ? Rgba5551ToRgba8888(m_clut[ci])
                    : (static_cast<uint32_t>(m_clut[ci]) | (static_cast<uint32_t>(m_clut[ci + 256u]) << 16u));
                clutRgba[ci * 4u + 0] = static_cast<uint8_t>(raw & 0xFFu);
                clutRgba[ci * 4u + 1] = static_cast<uint8_t>((raw >> 8u) & 0xFFu);
                clutRgba[ci * 4u + 2] = static_cast<uint8_t>((raw >> 16u) & 0xFFu);
                clutRgba[ci * 4u + 3] = static_cast<uint8_t>((raw >> 24u) & 0xFFu);
            }
            char clutFn[256];
            std::snprintf(clutFn, sizeof(clutFn), "logs/gs/clut_%u_cbp%u_cpsm0x%02x.png",
                          seq, effectiveCbp, static_cast<unsigned>(ctx.tex0.cpsm));
            writeUncompressedPng(16u, 16u, clutRgba.data(), clutFn);

            std::fprintf(stderr, "[GS:TEXDUMP] [%u/16] tex=(tbp0=%u, cbp=%u, psm=0x%02x, %ux%u) clutHash=0x%08x -> %s\\n",
                         seq, ctx.tex0.tbp0, effectiveCbp, static_cast<unsigned>(ctx.tex0.psm), tw_px, th_px, clutHash, fn);
            std::fflush(stderr);
        }
    }'''

t_new3 = '''    if (s_texDump == -1)
    {
        const char *env = std::getenv("PS2X_TEX_DUMP");
        if (!env) env = std::getenv("PS2X_GS_TEXDUMP");
        s_texDump = (env && (std::strcmp(env, "1") == 0 || std::strcmp(env, "true") == 0)) ? 1 : 0;
    }
    if (s_texDump == 1 && state.prim.tme && s_dumpedTexKeys.size() < 16u)
    {
        const uint32_t effectiveCbp = (ctx.tex0.cbp != 0u) ? ctx.tex0.cbp : m_clutCbp[0];
        uint32_t clutHash = calculateCrc32(reinterpret_cast<const uint8_t*>(m_clut.data()), sizeof(m_clut));
        uint32_t tw_px = 1u << ctx.tex0.tw;
        uint32_t th_px = 1u << ctx.tex0.th;

        bool alreadyDumped = false;
        for (const auto &k : s_dumpedTexKeys)
        {
            if (k.tbp0 == ctx.tex0.tbp0 && k.tbw == ctx.tex0.tbw && k.psm == ctx.tex0.psm &&
                k.tw == ctx.tex0.tw && k.th == ctx.tex0.th && k.cbp == effectiveCbp &&
                k.cpsm == ctx.tex0.cpsm && k.csm == ctx.tex0.csm && k.csa == ctx.tex0.csa &&
                k.clutHash == clutHash)
            {
                alreadyDumped = true;
                break;
            }
        }
        if (!alreadyDumped)
        {
            s_dumpedTexKeys.push_back({ctx.tex0.tbp0, ctx.tex0.tbw, ctx.tex0.psm, ctx.tex0.tw, ctx.tex0.th,
                                       effectiveCbp, ctx.tex0.cpsm, ctx.tex0.csm, ctx.tex0.csa, clutHash});
            uint32_t seq = static_cast<uint32_t>(s_dumpedTexKeys.size());
            std::vector<uint8_t> sampledRgba(tw_px * th_px * 4u, 0u);
            for (uint32_t sy = 0; sy < th_px; ++sy)
            {
                for (uint32_t sx = 0; sx < tw_px; ++sx)
                {
                    uint32_t rgba = SampleTexture(state, 0.f, 0.f, 1.f, static_cast<uint16_t>(sx * 16u), static_cast<uint16_t>(sy * 16u));
                    sampledRgba[(sy * tw_px + sx) * 4u + 0] = static_cast<uint8_t>(rgba & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 1] = static_cast<uint8_t>((rgba >> 8u) & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 2] = static_cast<uint8_t>((rgba >> 16u) & 0xFFu);
                    sampledRgba[(sy * tw_px + sx) * 4u + 3] = static_cast<uint8_t>((rgba >> 24u) & 0xFFu);
                }
            }
            std::filesystem::create_directories("frames/tex");
            char fn[256];
            std::snprintf(fn, sizeof(fn), "frames/tex/tex_%u_tbp%u_psm0x%02x_%ux%u.png",
                          seq, ctx.tex0.tbp0, static_cast<unsigned>(ctx.tex0.psm), tw_px, th_px);
            writeUncompressedPng(tw_px, th_px, sampledRgba.data(), fn);

            // Dump CLUT 16x16
            std::vector<uint8_t> clutRgba(16u * 16u * 4u, 0u);
            for (uint32_t ci = 0; ci < 256u; ++ci)
            {
                uint32_t raw = (ctx.tex0.cpsm == GS_PSM_CT16 || ctx.tex0.cpsm == GS_PSM_CT16S)
                    ? Rgba5551ToRgba8888(m_clut[ci])
                    : (static_cast<uint32_t>(m_clut[ci]) | (static_cast<uint32_t>(m_clut[ci + 256u]) << 16u));
                clutRgba[ci * 4u + 0] = static_cast<uint8_t>(raw & 0xFFu);
                clutRgba[ci * 4u + 1] = static_cast<uint8_t>((raw >> 8u) & 0xFFu);
                clutRgba[ci * 4u + 2] = static_cast<uint8_t>((raw >> 16u) & 0xFFu);
                clutRgba[ci * 4u + 3] = static_cast<uint8_t>((raw >> 24u) & 0xFFu);
            }
            char clutFn[256];
            std::snprintf(clutFn, sizeof(clutFn), "frames/tex/clut_%u_cbp%u_cpsm0x%02x.png",
                          seq, effectiveCbp, static_cast<unsigned>(ctx.tex0.cpsm));
            writeUncompressedPng(16u, 16u, clutRgba.data(), clutFn);

            const bool csm1Remapped = (ctx.tex0.csm == 0 && (ctx.tex0.cpsm == GS_PSM_CT16 || ctx.tex0.cpsm == GS_PSM_CT16S));
            std::fprintf(stderr, "[GS:TEXDUMP] [%u/16] tex=(tbp0=%u, tbw=%u, psm=0x%02x, tw=%u, th=%u, %ux%u) cbp=%u csa=%u csm=%u csm1_remap=%d clutHash=0x%08x -> %s\\n",
                         seq, ctx.tex0.tbp0, static_cast<unsigned>(ctx.tex0.tbw), static_cast<unsigned>(ctx.tex0.psm),
                         static_cast<unsigned>(ctx.tex0.tw), static_cast<unsigned>(ctx.tex0.th), tw_px, th_px,
                         effectiveCbp, static_cast<unsigned>(ctx.tex0.csa), static_cast<unsigned>(ctx.tex0.csm),
                         csm1Remapped ? 1 : 0, clutHash, fn);
            std::fflush(stderr);
        }
    }'''

assert t_old3 in src, 't_old3 not found'
src = src.replace(t_old3, t_new3, 1)

# 4. Add Step 6 PS2X_DRAW_STEP_DUMP after DrawPrimitive switch
t_old4 = '''    switch (state.prim.type)
    {
    case GS_PRIM_SPRITE:
        DrawSprite(batch);
        break;
    case GS_PRIM_TRIANGLE:
    case GS_PRIM_TRISTRIP:
    case GS_PRIM_TRIFAN:
        DrawTriangle(batch);
        break;
    case GS_PRIM_LINE:
    case GS_PRIM_LINESTRIP:
        DrawLine(batch);
        break;
    case GS_PRIM_POINT:
    {
        const GSVertex &v = batch.vertices[0];
        const auto &ctx = state.context;
        int px = static_cast<int>(v.x) - (ctx.xyoffset.ofx >> 4);
        int py = static_cast<int>(v.y) - (ctx.xyoffset.ofy >> 4);
        WritePixel(state, px, py, static_cast<u32>(v.z), v.r, v.g, v.b, v.a, v.fog);
        break;
    }
    default:
        break;
    }'''

t_new4 = '''    switch (state.prim.type)
    {
    case GS_PRIM_SPRITE:
        DrawSprite(batch);
        break;
    case GS_PRIM_TRIANGLE:
    case GS_PRIM_TRISTRIP:
    case GS_PRIM_TRIFAN:
        DrawTriangle(batch);
        break;
    case GS_PRIM_LINE:
    case GS_PRIM_LINESTRIP:
        DrawLine(batch);
        break;
    case GS_PRIM_POINT:
    {
        const GSVertex &v = batch.vertices[0];
        const auto &ctx = state.context;
        int px = static_cast<int>(v.x) - (ctx.xyoffset.ofx >> 4);
        int py = static_cast<int>(v.y) - (ctx.xyoffset.ofy >> 4);
        WritePixel(state, px, py, static_cast<u32>(v.z), v.r, v.g, v.b, v.a, v.fog);
        break;
    }
    default:
        break;
    }

    if (s_drawStepDump == -1)
    {
        const char *envStep = std::getenv("PS2X_DRAW_STEP_DUMP");
        s_drawStepDump = envStep ? std::atoi(envStep) : -2;
    }
    if (s_drawStepDump >= 0 && currentPrimIdx == static_cast<uint32_t>(s_drawStepDump))
    {
        std::filesystem::create_directories("logs/gs");
        char stepFn[256];
        std::snprintf(stepFn, sizeof(stepFn), "logs/gs/step_draw_%u.png", currentPrimIdx);
        std::vector<uint8_t> snapRgba(640u * 512u * 4u, 0u);
        const uint32_t fbp = GSInternal::framePageBaseToBlock(ctx.frame.fbp);
        const uint32_t fbw = std::max<uint32_t>(ctx.frame.fbw, 1u);
        for (uint32_t py = 0; py < 512u; ++py)
        {
            for (uint32_t px = 0; px < 640u; ++px)
            {
                uint32_t raw = ReadVramUnlocked(ctx.frame.psm, fbp, fbw, px, py);
                uint32_t c = (ctx.frame.psm == GS_PSM_CT32) ? raw :
                             ((ctx.frame.psm == GS_PSM_CT16 || ctx.frame.psm == GS_PSM_CT16S) ? Rgba5551ToRgba8888(raw) : raw);
                snapRgba[(py * 640u + px) * 4u + 0] = static_cast<uint8_t>(c & 0xFFu);
                snapRgba[(py * 640u + px) * 4u + 1] = static_cast<uint8_t>((c >> 8u) & 0xFFu);
                snapRgba[(py * 640u + px) * 4u + 2] = static_cast<uint8_t>((c >> 16u) & 0xFFu);
                snapRgba[(py * 640u + px) * 4u + 3] = static_cast<uint8_t>((c >> 24u) & 0xFFu);
            }
        }
        writeUncompressedPng(640u, 512u, snapRgba.data(), stepFn);
        std::fprintf(stderr, "[GS:STEP_DUMP] Prim %u dumped framebuffer fbp=%u to %s\\n", currentPrimIdx, ctx.frame.fbp, stepFn);
        std::fflush(stderr);
    }'''

assert t_old4 in src, 't_old4 not found'
src = src.replace(t_old4, t_new4, 1)

with open('PS2Recomp/ps2xRuntime/src/lib/gs/gs_cpu_backend.cpp', 'w', encoding='utf-8') as f:
    f.write(src)
print('Successfully patched gs_cpu_backend.cpp via helper script')
