#include "ui.h"

#include "imgui.h"
#include <SDL3/SDL.h>

#include <algorithm>
#include <cctype>
#include <cstring>
#include <fstream>
#include <sstream>

namespace ape3::launcher
{
namespace
{

constexpr size_t kMaxLogLines = 2000;

bool inputTextString(const char *label, std::string &value, size_t maxLen = 1024)
{
    std::vector<char> buf(std::max(maxLen, value.size() + 64), '\0');
    std::memcpy(buf.data(), value.data(), std::min(value.size(), buf.size() - 1));
    if (ImGui::InputText(label, buf.data(), buf.size()))
    {
        value = buf.data();
        return true;
    }
    return false;
}

void SDLCALL onIsoSelected(void *userdata, const char *const *filelist, int /*filter*/)
{
    auto *state = static_cast<LauncherState *>(userdata);
    if (!state || !filelist || !filelist[0])
        return;

    std::lock_guard<std::mutex> lock(state->dialogMutex);
    state->pendingIsoPath = filelist[0];
    state->hasPendingIso = true;
}

void SDLCALL onGameDirSelected(void *userdata, const char *const *filelist, int /*filter*/)
{
    auto *state = static_cast<LauncherState *>(userdata);
    if (!state || !filelist || !filelist[0])
        return;

    std::lock_guard<std::mutex> lock(state->dialogMutex);
    state->pendingGameDir = filelist[0];
    state->hasPendingGameDir = true;
}

bool runtimeExeExists(const LauncherState &state)
{
    const std::filesystem::path exePath = resolveRuntimeExePath(state);
    if (exePath.empty())
        return false;
    std::error_code ec;
    return std::filesystem::exists(exePath, ec) &&
           std::filesystem::is_regular_file(exePath, ec);
}

bool pathsEqual(const std::filesystem::path &a, const std::filesystem::path &b)
{
    std::error_code ec;
    if (std::filesystem::exists(a, ec) && std::filesystem::exists(b, ec))
    {
        if (std::filesystem::equivalent(a, b, ec))
            return true;
    }
    return a.lexically_normal() == b.lexically_normal();
}

bool saveAll(LauncherState &state)
{
    if (!saveIni(state.iniPath, state.settings, state.extras))
    {
        if (!state.fallbackIniPath.empty() && state.iniPath != state.fallbackIniPath)
        {
            std::error_code ec;
            if (state.fallbackIniPath.has_parent_path())
                std::filesystem::create_directories(state.fallbackIniPath.parent_path(), ec);
            if (saveIni(state.fallbackIniPath, state.settings, state.extras))
            {
                const std::string failedPath = state.iniPath.string();
                state.iniPath = state.fallbackIniPath;
                if (!state.fallbackLauncherIniPath.empty())
                {
                    state.launcherIniPath = state.fallbackLauncherIniPath;
                    saveLauncherIni(state.launcherIniPath, state.runtimeExe);
                }
                state.statusMessage = "Failed to save " + failedPath + "; fell back to " + state.iniPath.string();
                return true;
            }
        }
        state.statusMessage = "Failed to save " + state.iniPath.string();
        return false;
    }
    if (!state.launcherIniPath.empty())
    {
        saveLauncherIni(state.launcherIniPath, state.runtimeExe);
    }
    state.statusMessage = "Saved " + state.iniPath.string();
    return true;
}

void startGame(LauncherState &state)
{
    const PlayIniResult playIni = writePlayInis(state);
    state.validationError = validate(state.settings);
    if (!state.validationError.empty())
        return;

    const std::filesystem::path exePath = resolveRuntimeExePath(state);
    const std::filesystem::path workDir = resolveRuntimeWorkDir(state);

    const auto args = buildArgs(state.settings);
    const auto env = buildEnvironment(state.settings);

    std::string err;
    state.logLines.clear();
    state.partialLine.clear();
    if (!playIni.runtimeDirWritable && !playIni.note.empty())
        appendLogChunk(state, playIni.note + "\n");

    if (!startRuntime(exePath, workDir, args, env, state.process, &err))
    {
        state.validationError = err.empty() ? "Failed to start runtime." : err;
    }
    else
    {
        state.statusMessage = "Running " + exePath.filename().string();
        state.scrollLogToBottom = true;
    }
}

void renderGameTab(LauncherState &state, SDL_Window *window)
{
    ImGui::Spacing();

    if (state.settings.isoPath.empty() && state.settings.gameDir.empty())
    {
        ImGui::BeginChild("FirstRunBox", ImVec2(0, 56.0f), true);
        ImGui::TextWrapped("No game image selected. This launcher contains no game data: choose your own Ape Escape 3 disc image (.iso) or the extracted game folder.");
        ImGui::EndChild();
        ImGui::Spacing();
    }

    if (inputTextString("ISO Path", state.settings.isoPath))
        state.validationError = validate(state.settings);
    ImGui::SameLine();
    if (ImGui::Button("Browse##Iso"))
    {
        static const SDL_DialogFileFilter kFilters[] = {
            {"Disc Images", "iso;bin"},
            {"All Files", "*"},
        };
        const char *defaultLoc = state.settings.isoPath.empty() ? nullptr : state.settings.isoPath.c_str();
        SDL_ShowOpenFileDialog(onIsoSelected, &state, window, kFilters, 2, defaultLoc, false);
    }

    if (inputTextString("Extracted game folder", state.settings.gameDir))
        state.validationError = validate(state.settings);
    ImGui::SameLine();
    if (ImGui::Button("Browse##GameDir"))
    {
        const char *defaultLoc = state.settings.gameDir.empty() ? nullptr : state.settings.gameDir.c_str();
        SDL_ShowOpenFolderDialog(onGameDirSelected, &state, window, defaultLoc, false);
    }

    if (inputTextString("ELF Name", state.settings.elfName, 128))
        state.validationError = validate(state.settings);

    if (!state.validationError.empty())
    {
        ImGui::Spacing();
        ImGui::TextColored(ImVec4(1.0f, 0.35f, 0.35f, 1.0f), "%s", state.validationError.c_str());
    }

    if (!runtimeExeExists(state))
    {
        ImGui::Spacing();
        ImGui::TextColored(ImVec4(1.0f, 0.35f, 0.35f, 1.0f), "Runtime executable not found: %s", state.runtimeExe.c_str());
    }
}

void renderVideoTab(LauncherState &state)
{
    ImGui::Spacing();

    const char *renderers[] = {"classic", "new"};
    int rendererIdx = (state.settings.renderer == "classic") ? 0 : 1;
    if (ImGui::Combo("Renderer", &rendererIdx, renderers, IM_ARRAYSIZE(renderers)))
        state.settings.renderer = renderers[rendererIdx];

    inputTextString("Window Size", state.settings.windowSize, 64);
    ImGui::Checkbox("Fullscreen", &state.settings.fullscreen);
    ImGui::Checkbox("VSync", &state.settings.vsync);
    ImGui::SliderInt("Render Scale (%)", &state.settings.renderScale, 25, 400);

    const int msaaValues[] = {0, 2, 4, 8};
    const char *msaaLabels[] = {"0 (Off)", "2x", "4x", "8x"};
    int msaaIdx = 2;
    for (int i = 0; i < 4; ++i)
    {
        if (state.settings.msaa == msaaValues[i])
        {
            msaaIdx = i;
            break;
        }
    }
    if (ImGui::Combo("MSAA", &msaaIdx, msaaLabels, IM_ARRAYSIZE(msaaLabels)))
        state.settings.msaa = msaaValues[msaaIdx];

    const char *aspects[] = {"4:3", "fill", "16:9", "native"};
    int aspectIdx = 1;
    for (int i = 0; i < 4; ++i)
    {
        if (state.settings.aspect == aspects[i])
        {
            aspectIdx = i;
            break;
        }
    }
    if (ImGui::Combo("Aspect Ratio", &aspectIdx, aspects, IM_ARRAYSIZE(aspects)))
        state.settings.aspect = aspects[aspectIdx];

    inputTextString("Aspect Max", state.settings.aspectMax, 32);
    inputTextString("HUD Anchor", state.settings.hudAnchor, 32);
    inputTextString("Texture Pack Folder", state.settings.texturePack);
}

void renderAudioTab(LauncherState &state)
{
    ImGui::Spacing();
    ImGui::SliderInt("Master Volume", &state.settings.volume, 0, 100);
    ImGui::Spacing();
    ImGui::TextDisabled("Audio device selection is not available yet");
}

struct KeyBindingRow
{
    const char *key;
    const char *action;
};

constexpr KeyBindingRow kKeyboardBindings[] = {
    {"Arrow Keys", "D-Pad"},
    {"W / A / S / D", "Left Stick"},
    {"I / J / K / L", "Face Buttons"},
    {"Enter", "Start"},
    {"Backspace / Tab", "Select"},
    {"Q / E", "L1 / R1"},
    {"1 / 3", "L2 / R2"},
};

void renderInputTab()
{
    ImGui::Spacing();
    if (ImGui::BeginTable("KeyboardBindings", 2, ImGuiTableFlags_Borders | ImGuiTableFlags_RowBg))
    {
        ImGui::TableSetupColumn("Key");
        ImGui::TableSetupColumn("Action");
        ImGui::TableHeadersRow();
        for (const auto &row : kKeyboardBindings)
        {
            ImGui::TableNextRow();
            ImGui::TableNextColumn();
            ImGui::TextUnformatted(row.key);
            ImGui::TableNextColumn();
            ImGui::TextUnformatted(row.action);
        }
        ImGui::EndTable();
    }
    ImGui::Spacing();
    ImGui::TextDisabled("Key remapping comes later.");
}

void renderAdvancedTab(LauncherState &state)
{
    ImGui::Spacing();

    const char *timingLabels[] = {"Original", "Fast"};
    const char *timingValues[] = {"original", "fast"};
    int timingIdx = (state.settings.loadTiming == "fast") ? 1 : 0;
    if (ImGui::Combo("Load Timing", &timingIdx, timingLabels, IM_ARRAYSIZE(timingLabels)))
        state.settings.loadTiming = timingValues[timingIdx];

    inputTextString("Memory Card Path", state.settings.memoryCard);
    ImGui::Checkbox("Developer", &state.settings.developer);
    inputTextString("Runtime Exe Path", state.runtimeExe);

    if (!runtimeExeExists(state))
    {
        ImGui::Spacing();
        ImGui::TextColored(ImVec4(1.0f, 0.35f, 0.35f, 1.0f), "Runtime executable not found: %s", state.runtimeExe.c_str());
    }
}

void renderLogTab(LauncherState &state)
{
    ImGui::Spacing();
    const bool running = isRunning(state.process);
    if (running)
    {
        ImGui::Text("Status: Running");
        ImGui::SameLine();
        if (ImGui::Button("Stop"))
            stop(state.process);
    }
    else if (state.process.hasExited)
    {
        ImGui::Text("Status: Exited (code %d)", exitCode(state.process));
    }
    else
    {
        ImGui::Text("Status: Idle");
    }

    ImGui::SameLine();
    if (ImGui::Button("Clear"))
    {
        state.logLines.clear();
        state.partialLine.clear();
    }

    ImGui::Separator();
    ImGui::BeginChild("LogScroll", ImVec2(0, 0), true, ImGuiWindowFlags_HorizontalScrollbar);
    for (const std::string &line : state.logLines)
        ImGui::TextUnformatted(line.c_str());
    if (!state.partialLine.empty())
        ImGui::TextUnformatted(state.partialLine.c_str());
    if (state.scrollLogToBottom)
    {
        ImGui::SetScrollHereY(1.0f);
        state.scrollLogToBottom = false;
    }
    ImGui::EndChild();
}

void renderAboutTab()
{
    ImGui::Spacing();
    ImGui::TextWrapped("Bring your own disc image. This program contains no game data.");
    ImGui::Spacing();
    ImGui::Separator();
    ImGui::Spacing();

    const int sdlVer = SDL_GetVersion();
    ImGui::Text("Launcher: Ape Escape 3 Recomp Launcher 0.1");
    ImGui::Text("Version: %s", __DATE__);
    ImGui::Text("SDL3: %d.%d.%d", SDL_VERSIONNUM_MAJOR(sdlVer), SDL_VERSIONNUM_MINOR(sdlVer), SDL_VERSIONNUM_MICRO(sdlVer));
    ImGui::Text("Dear ImGui: %s", IMGUI_VERSION);
    ImGui::Spacing();
    ImGui::TextWrapped("Licence: Placeholder — see repository LICENSE and third-party notices.");
}

} // namespace

std::filesystem::path resolveRuntimeExePath(const LauncherState &state)
{
    if (state.runtimeExe.empty())
        return {};
    std::filesystem::path p(state.runtimeExe);
    if (p.is_relative())
    {
        std::error_code ec;
        const std::filesystem::path fromExeDir = state.exeDir / p;
        if (p.parent_path().empty() || std::filesystem::exists(fromExeDir, ec))
            p = fromExeDir;
        else
            p = std::filesystem::absolute(p, ec);
    }
    return p.lexically_normal();
}

std::filesystem::path resolveRuntimeWorkDir(const LauncherState &state)
{
    const std::filesystem::path exePath = resolveRuntimeExePath(state);
    std::filesystem::path workDir = exePath.parent_path();
    if (workDir.empty())
        workDir = state.exeDir;
    return workDir;
}

PlayIniResult writePlayInis(LauncherState &state)
{
    PlayIniResult result;
    if (saveAll(state) && !state.iniPath.empty())
        result.writtenPaths.push_back(state.iniPath);

    const std::filesystem::path runtimeDir = resolveRuntimeWorkDir(state);
    const std::filesystem::path runtimeIniPath = runtimeDir / "ps2x.ini";
    if (!state.iniPath.empty() && pathsEqual(state.iniPath, runtimeIniPath))
        return result;

    std::error_code ec;
    const IniExtras *extrasToWrite = &state.extras;
    IniExtras runtimeExtras;
    if (std::filesystem::exists(runtimeIniPath, ec))
    {
        Settings existingSettings;
        if (loadIni(runtimeIniPath, existingSettings, runtimeExtras))
        {
            if (hasDifferentUnknownContent(runtimeExtras, state.extras))
            {
                const std::filesystem::path bakPath = runtimeDir / "ps2x.ini.bak";
                if (!std::filesystem::exists(bakPath, ec))
                    std::filesystem::copy_file(runtimeIniPath, bakPath, std::filesystem::copy_options::none, ec);
            }
            extrasToWrite = &runtimeExtras;
        }
    }

    if (saveIni(runtimeIniPath, state.settings, *extrasToWrite))
    {
        result.writtenPaths.push_back(runtimeIniPath);
    }
    else
    {
        result.runtimeDirWritable = false;
        result.note = "Note: runtime dir not writable (" + runtimeDir.string() + "); using environment settings.";
    }
    return result;
}

void appendLogChunk(LauncherState &state, const std::string &chunk)
{
    for (char c : chunk)
    {
        if (c == '\r')
            continue;
        if (c == '\n')
        {
            state.logLines.push_back(std::move(state.partialLine));
            state.partialLine.clear();
            if (state.logLines.size() > kMaxLogLines)
                state.logLines.erase(state.logLines.begin(),
                                     state.logLines.begin() + static_cast<ptrdiff_t>(state.logLines.size() - kMaxLogLines));
            state.scrollLogToBottom = true;
        }
        else
        {
            state.partialLine.push_back(c);
        }
    }
}

bool saveLauncherIni(const std::filesystem::path &path, const std::string &runtimeExe)
{
    std::error_code ec;
    if (path.has_parent_path())
        std::filesystem::create_directories(path.parent_path(), ec);

    std::ofstream out(path, std::ios::trunc);
    if (!out)
        return false;
    out << "runtime_exe = " << runtimeExe << '\n';
    return out.good();
}

std::string loadLauncherIni(const std::filesystem::path &path)
{
    std::ifstream in(path);
    if (!in)
        return {};
    std::string line;
    while (std::getline(in, line))
    {
        const size_t eq = line.find('=');
        if (eq == std::string::npos)
            continue;
        std::string key = line.substr(0, eq);
        std::string val = line.substr(eq + 1);
        auto trimStr = [](std::string &s) {
            const size_t first = s.find_first_not_of(" \t\r\n");
            if (first == std::string::npos)
            {
                s.clear();
                return;
            }
            const size_t last = s.find_last_not_of(" \t\r\n");
            s = s.substr(first, last - first + 1);
        };
        trimStr(key);
        trimStr(val);
        for (char &c : key)
            c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
        if (key == "runtime_exe" && !val.empty())
            return val;
    }
    return {};
}

void renderLauncherUi(LauncherState &state, SDL_Window *window)
{
    {
        std::lock_guard<std::mutex> lock(state.dialogMutex);
        if (state.hasPendingIso)
        {
            state.settings.isoPath = state.pendingIsoPath;
            state.hasPendingIso = false;
            state.validationError = validate(state.settings);
        }
        if (state.hasPendingGameDir)
        {
            state.settings.gameDir = state.pendingGameDir;
            state.hasPendingGameDir = false;
            state.validationError = validate(state.settings);
        }
    }

    const ImGuiViewport *viewport = ImGui::GetMainViewport();
    ImGui::SetNextWindowPos(viewport->WorkPos);
    ImGui::SetNextWindowSize(viewport->WorkSize);
    constexpr ImGuiWindowFlags kRootFlags = ImGuiWindowFlags_NoDecoration | ImGuiWindowFlags_NoMove |
                                            ImGuiWindowFlags_NoResize | ImGuiWindowFlags_NoSavedSettings;

    ImGui::Begin("ApeEscape3LauncherRoot", nullptr, kRootFlags);

    const float footerHeight = ImGui::GetFrameHeightWithSpacing() + 12.0f;
    if (ImGui::BeginChild("MainContent", ImVec2(0, -footerHeight), false))
    {
        if (ImGui::BeginTabBar("LauncherTabs"))
        {
            if (ImGui::BeginTabItem("Game"))
            {
                renderGameTab(state, window);
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("Video"))
            {
                renderVideoTab(state);
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("Audio"))
            {
                renderAudioTab(state);
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("Input"))
            {
                renderInputTab();
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("Advanced"))
            {
                renderAdvancedTab(state);
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("Log"))
            {
                renderLogTab(state);
                ImGui::EndTabItem();
            }
            if (ImGui::BeginTabItem("About"))
            {
                renderAboutTab();
                ImGui::EndTabItem();
            }
            ImGui::EndTabBar();
        }
    }
    ImGui::EndChild();

    ImGui::Separator();

    if (ImGui::Button("Save", ImVec2(90, 0)))
        saveAll(state);

    ImGui::SameLine();
    const bool running = isRunning(state.process);
    const bool canPlay = !running && runtimeExeExists(state);
    ImGui::BeginDisabled(!canPlay);
    if (ImGui::Button("Play", ImVec2(90, 0)))
        startGame(state);
    ImGui::EndDisabled();

    ImGui::SameLine();
    if (ImGui::Button("Quit", ImVec2(90, 0)))
        state.quitRequested = true;

    if (!state.statusMessage.empty())
    {
        ImGui::SameLine();
        ImGui::TextDisabled("%s", state.statusMessage.c_str());
    }

    ImGui::End();
}

} // namespace ape3::launcher
