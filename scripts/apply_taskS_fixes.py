import os

# 1. Patch ps2_memory.cpp
mem_path = 'PS2Recomp/ps2xRuntime/src/lib/ps2_memory.cpp'
with open(mem_path, 'r', encoding='utf-8') as f:
    mem_content = f.read()

if 'std::atomic<uint64_t> g_gsFrameKicks' not in mem_content:
    old_target = 'inline bool isIoRegister(uint32_t addr)'
    new_target = 'std::atomic<uint64_t> g_gsFrameKicks{0};\n\n    inline bool isIoRegister(uint32_t addr)'
    assert old_target in mem_content, "Target not found in ps2_memory.cpp"
    mem_content = mem_content.replace(old_target, new_target, 1)

    old_enqueue = 'else if (channelBase == 0x10009000u)\n                        m_pendingVif1Transfers.push_back(pt);'
    new_enqueue = 'else if (channelBase == 0x10009000u)\n                    {\n                        m_pendingVif1Transfers.push_back(pt);\n                        g_gsFrameKicks.fetch_add(1, std::memory_order_release);\n                    }'
    assert old_enqueue in mem_content, "Enqueue target not found in ps2_memory.cpp"
    mem_content = mem_content.replace(old_enqueue, new_enqueue, 1)

    with open(mem_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(mem_content)
    print("ps2_memory.cpp patched successfully")
else:
    print("ps2_memory.cpp already patched")

# 2. Patch EeScheduler.cpp
sched_path = 'PS2Recomp/ps2xRuntime/src/lib/Kernel/EeScheduler.cpp'
with open(sched_path, 'r', encoding='utf-8') as f:
    sched_content = f.read()

target_sched_old = '''            } else if (m_vsyncTick >= 5) {
                // Auto-confirm pulse for headless test runs:
                // Alternate pulses: Cross (5 on, 5 off), Circle (5 on, 5 off), Start (5 on, 5 off)
                const uint64_t phase = (m_vsyncTick / 10) % 3;
                const bool press = ((m_vsyncTick % 10) < 5);
                if (press) {
                    if (phase == 0) activeMask |= (1u << 14); // CROSS
                    else if (phase == 1) activeMask |= (1u << 13); // CIRCLE
                    else activeMask |= (1u << 3); // START
                }
                static uint64_t s_lastLogVsync = 0;
                if (m_vsyncTick != s_lastLogVsync && (m_vsyncTick % 5) == 0) {
                    s_lastLogVsync = m_vsyncTick;
                    ps2xSafeLog("[pad:inject] vsync=%llu phase=%llu press=%d btn=0x%04x\\n",
                                (unsigned long long)m_vsyncTick, (unsigned long long)phase, press ? 1 : 0, activeMask);
                    std::fflush(stderr);
                }
            }'''

target_sched_new = '''            } else {
                extern std::atomic<uint16_t> g_hostPadButtons;
                static int s_autoPad = -1;
                if (s_autoPad == -1) {
                    const char *env = std::getenv("PS2X_AUTO_PAD");
                    s_autoPad = (env && (env[0] == '1' || env[0] == 't')) ? 1 : 0;
                }
                if (s_autoPad && m_vsyncTick >= 5) {
                    const uint64_t phase = (m_vsyncTick / 10) % 3;
                    const bool press = ((m_vsyncTick % 10) < 5);
                    if (press) {
                        if (phase == 0) activeMask |= (1u << 14); // CROSS
                        else if (phase == 1) activeMask |= (1u << 13); // CIRCLE
                        else activeMask |= (1u << 3); // START
                    }
                    static uint64_t s_lastLogVsync = 0;
                    if (m_vsyncTick != s_lastLogVsync && (m_vsyncTick % 60) == 0) {
                        s_lastLogVsync = m_vsyncTick;
                        ps2xSafeLog("[pad:inject:auto] vsync=%llu phase=%llu press=%d btn=0x%04x\\n",
                                    (unsigned long long)m_vsyncTick, (unsigned long long)phase, press ? 1 : 0, activeMask);
                        std::fflush(stderr);
                    }
                } else {
                    activeMask = g_hostPadButtons.load(std::memory_order_acquire);
                }
            }'''

if target_sched_old in sched_content:
    sched_content = sched_content.replace(target_sched_old, target_sched_new, 1)
    with open(sched_path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(sched_content)
    print("EeScheduler.cpp patched successfully")
else:
    print("EeScheduler.cpp already patched or pattern not found")

# 3. Patch ps2_runtime.cpp
rt_path = 'PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp'
with open(rt_path, 'r', encoding='utf-8') as f:
    rt_content = f.read()

# Add g_hostPadButtons definition
if 'std::atomic<uint16_t> g_hostPadButtons{0};' not in rt_content:
    rt_content = 'std::atomic<uint16_t> g_hostPadButtons{0};\n' + rt_content

# Fix dispatchGuestBranch line 2837 and line 2901
old_dispatch_check1 = '''    // Every inter-function transfer is also a deterministic EE safe point.
    // Backward edges inside generated functions use eeCheckpointDue(), while
    // this charge bounds straight-line call chains that have no local loop.
    if (m_eeScheduler && m_eeScheduler->checkpointDue(EeScheduler::kGuestDispatchCycles))
    {
        return false;
    }'''

new_dispatch_check1 = '''    // Every inter-function transfer accounts cycles.
    // Never return false here for calls/transfers, as that unwinds host C++ frames and breaks main loop.
    if (m_eeScheduler)
    {
        m_eeScheduler->accountCycles(EeScheduler::kGuestDispatchCycles);
    }'''

old_dispatch_check2 = '''        if (m_eeScheduler && m_eeScheduler->checkpointDue(EeScheduler::kGuestDispatchCycles))
        {
            return false;
        }'''

new_dispatch_check2 = '''        if (m_eeScheduler)
        {
            m_eeScheduler->accountCycles(EeScheduler::kGuestDispatchCycles);
        }'''

if old_dispatch_check1 in rt_content:
    rt_content = rt_content.replace(old_dispatch_check1, new_dispatch_check1, 1)
    print("dispatchGuestBranch check 1 replaced")

if old_dispatch_check2 in rt_content:
    rt_content = rt_content.replace(old_dispatch_check2, new_dispatch_check2, 1)
    print("dispatchGuestBranch check 2 replaced")

# Fix UploadFrame auto-pulse
old_upload_auto = '''        } else if (currentTick >= 68 && currentTick < 300) {
            // Auto-pulse CROSS/CIRCLE on Memory Card screen when headless
            bool pressConfirm = ((currentTick % 20) < 10);
            if (pressConfirm) {
                activeMask |= (1u << 14) | (1u << 13); // CROSS + CIRCLE
            }
            static bool s_autoConfirmReported = false;
            if (!s_autoConfirmReported) {
                s_autoConfirmReported = true;
                ps2xSafeLog("[pad:inject] auto-confirming on Memory Card screen at tick=%llu\\n", (unsigned long long)currentTick);
                std::fflush(stderr);
            }
        }

        if (activeMask != 0) {
            ps2_stubs::setPadOverrideState(static_cast<uint16_t>(~activeMask), 0x80, 0x80, 0x80, 0x80);
        } else {
            ps2_stubs::setPadOverrideState(0xFFFFu, 0x80, 0x80, 0x80, 0x80);
        }'''

new_upload_auto = '''        } else {
            static int s_autoPadUpload = -1;
            if (s_autoPadUpload == -1) {
                const char *env = std::getenv("PS2X_AUTO_PAD");
                s_autoPadUpload = (env && (env[0] == '1' || env[0] == 't')) ? 1 : 0;
            }
            if (s_autoPadUpload && currentTick >= 68 && currentTick < 300) {
                bool pressConfirm = ((currentTick % 20) < 10);
                if (pressConfirm) {
                    activeMask |= (1u << 14) | (1u << 13); // CROSS + CIRCLE
                }
            }
        }

        if (activeMask != 0) {
            ps2_stubs::setPadOverrideState(static_cast<uint16_t>(~activeMask), 0x80, 0x80, 0x80, 0x80);
        }'''

if old_upload_auto in rt_content:
    rt_content = rt_content.replace(old_upload_auto, new_upload_auto, 1)
    print("UploadFrame auto-pulse gated")

# Fix host presentation loop in PS2Runtime::run()
old_run_loop = '''        uint32_t presentWidth = FB_WIDTH;
        uint32_t presentHeight = DEFAULT_DISPLAY_HEIGHT;
        if (tick <= 5) { fprintf(stderr, "[tick %llu] before UploadFrame\\n", (unsigned long long)tick); fflush(stderr); }
        UploadFrame(frameTex, this, presentWidth, presentHeight, tick);
        if (tick <= 5) { fprintf(stderr, "[tick %llu] after UploadFrame\\n", (unsigned long long)tick); fflush(stderr); }

        BeginDrawing();
        ClearBackground(BLACK);
        const float srcWidth = static_cast<float>(std::max<uint32_t>(1u, presentWidth));
        const float srcHeight = static_cast<float>(std::max<uint32_t>(1u, presentHeight));
        const float screenWidth = static_cast<float>(GetScreenWidth());
        const float screenHeight = static_cast<float>(GetScreenHeight());
        const float scale = std::min(screenWidth / srcWidth, screenHeight / srcHeight);
        const float dstWidth = srcWidth * scale;
        const float dstHeight = srcHeight * scale;
        const Rectangle srcRect{0.0f, 0.0f, srcWidth, srcHeight};
        const Rectangle dstRect{
            (screenWidth - dstWidth) * 0.5f,
            (screenHeight - dstHeight) * 0.5f,
            dstWidth,
            dstHeight};
        DrawTexturePro(frameTex, srcRect, dstRect, Vector2{0.0f, 0.0f}, 0.0f, WHITE);
        if (m_debugUiInitialized && m_debugUiDrawCallback)
        {
            m_debugUiDrawCallback(*this, m_debugUiUserData);
        }
        EndDrawing();
        if (tick <= 5) { fprintf(stderr, "[tick %llu] after EndDrawing\\n", (unsigned long long)tick); fflush(stderr); }'''

new_run_loop = '''        // Sample real keyboard state from Raylib window thread
        uint16_t activeButtons = 0;
        if (IsKeyDown(KEY_ENTER)) activeButtons |= (1u << 3); // START
        if (IsKeyDown(KEY_RIGHT_SHIFT) || IsKeyDown(KEY_BACKSPACE)) activeButtons |= (1u << 0); // SELECT
        if (IsKeyDown(KEY_X) || IsKeyDown(KEY_K)) activeButtons |= (1u << 14); // CROSS
        if (IsKeyDown(KEY_Z) || IsKeyDown(KEY_L) || IsKeyDown(KEY_SPACE)) activeButtons |= (1u << 13); // CIRCLE
        if (IsKeyDown(KEY_A) || IsKeyDown(KEY_J)) activeButtons |= (1u << 15); // SQUARE
        if (IsKeyDown(KEY_S) || IsKeyDown(KEY_I)) activeButtons |= (1u << 12); // TRIANGLE
        if (IsKeyDown(KEY_UP)) activeButtons |= (1u << 4); // UP
        if (IsKeyDown(KEY_RIGHT)) activeButtons |= (1u << 5); // RIGHT
        if (IsKeyDown(KEY_DOWN)) activeButtons |= (1u << 6); // DOWN
        if (IsKeyDown(KEY_LEFT)) activeButtons |= (1u << 7); // LEFT
        if (IsKeyDown(KEY_Q)) activeButtons |= (1u << 10); // L1
        if (IsKeyDown(KEY_W)) activeButtons |= (1u << 8); // L2
        if (IsKeyDown(KEY_E)) activeButtons |= (1u << 11); // R1
        if (IsKeyDown(KEY_R)) activeButtons |= (1u << 9); // R2
        g_hostPadButtons.store(activeButtons, std::memory_order_release);

        extern std::atomic<uint64_t> g_gsFrameKicks;
        static uint64_t s_lastPresentedGsKicks = std::numeric_limits<uint64_t>::max();
        static auto s_lastPresentTime = std::chrono::steady_clock::now();
        static uint32_t s_fpsCounter = 0;
        static auto s_lastFpsLogTime = std::chrono::steady_clock::now();

        const uint64_t currentGsKicks = g_gsFrameKicks.load(std::memory_order_acquire);
        const auto now = std::chrono::steady_clock::now();
        const auto timeSinceLastPresent = std::chrono::duration_cast<std::chrono::milliseconds>(now - s_lastPresentTime).count();
        const bool shouldPresent = (currentGsKicks != s_lastPresentedGsKicks) || (timeSinceLastPresent >= 33);

        if (shouldPresent)
        {
            s_lastPresentedGsKicks = currentGsKicks;
            s_lastPresentTime = now;
            s_fpsCounter++;

            uint32_t presentWidth = FB_WIDTH;
            uint32_t presentHeight = DEFAULT_DISPLAY_HEIGHT;
            UploadFrame(frameTex, this, presentWidth, presentHeight, tick);

            BeginDrawing();
            ClearBackground(BLACK);
            const float srcWidth = static_cast<float>(std::max<uint32_t>(1u, presentWidth));
            const float srcHeight = static_cast<float>(std::max<uint32_t>(1u, presentHeight));
            const float screenWidth = static_cast<float>(GetScreenWidth());
            const float screenHeight = static_cast<float>(GetScreenHeight());
            const float scale = std::min(screenWidth / srcWidth, screenHeight / srcHeight);
            const float dstWidth = srcWidth * scale;
            const float dstHeight = srcHeight * scale;
            const Rectangle srcRect{0.0f, 0.0f, srcWidth, srcHeight};
            const Rectangle dstRect{
                (screenWidth - dstWidth) * 0.5f,
                (screenHeight - dstHeight) * 0.5f,
                dstWidth,
                dstHeight};
            DrawTexturePro(frameTex, srcRect, dstRect, Vector2{0.0f, 0.0f}, 0.0f, WHITE);
            if (m_debugUiInitialized && m_debugUiDrawCallback)
            {
                m_debugUiDrawCallback(*this, m_debugUiUserData);
            }
            EndDrawing();
        }
        else
        {
            PollInputEvents();
            std::this_thread::yield();
        }

        const auto timeSinceLastFpsLog = std::chrono::duration_cast<std::chrono::milliseconds>(now - s_lastFpsLogTime).count();
        if (timeSinceLastFpsLog >= 1000)
        {
            uint32_t currentFps = static_cast<uint32_t>(s_fpsCounter * 1000.0 / timeSinceLastFpsLog);
            ps2xSafeLog("[fps] FPS: %u (GS frames/sec), kicks=%llu, vsyncTick=%llu\\n",
                        currentFps, (unsigned long long)currentGsKicks, (unsigned long long)(m_eeScheduler ? m_eeScheduler->currentVSyncTick() : 0));
            char titleBuf[128];
            std::snprintf(titleBuf, sizeof(titleBuf), "Ape Escape 3 Recomp - FPS: %u (GS %llu)", currentFps, (unsigned long long)currentGsKicks);
            SetWindowTitle(titleBuf);
            s_fpsCounter = 0;
            s_lastFpsLogTime = now;
        }'''

if old_run_loop in rt_content:
    rt_content = rt_content.replace(old_run_loop, new_run_loop, 1)
    print("PS2Runtime::run loop decoupled")

with open(rt_path, 'w', encoding='utf-8', newline='\n') as f:
    f.write(rt_content)
print("ps2_runtime.cpp patched successfully")
