#include "settings.h"

#include <algorithm>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <map>
#include <string>
#include <vector>

using namespace ape3::launcher;

namespace
{

bool containsLine(const std::vector<std::string> &lines, const std::string &needle)
{
    return std::find(lines.begin(), lines.end(), needle) != lines.end();
}

std::vector<std::string> readLines(const std::filesystem::path &path)
{
    std::vector<std::string> lines;
    std::ifstream in(path);
    std::string line;
    while (std::getline(in, line))
    {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        lines.push_back(line);
    }
    return lines;
}

} // namespace

int main(int argc, char **argv)
{
    const std::filesystem::path iniPath = (argc >= 2) ? argv[1] : "ps2x.ini";

    // 1. Round-trip ps2x.ini preserving comments and unknown sections/keys
    Settings s;
    IniExtras extras;
    if (!loadIni(iniPath, s, extras))
    {
        std::cerr << "FAIL: loadIni failed for " << iniPath << "\n";
        return 1;
    }

    if (s.renderer != "new" || s.aspect != "fill" || s.msaa != 4 || s.windowSize != "1600x900" ||
        s.renderScale != 100 || !s.vsync || !s.fullscreen)
    {
        std::cerr << "FAIL: loaded ps2x.ini values did not match expected\n";
        return 1;
    }

    const std::filesystem::path tempIni =
        std::filesystem::temp_directory_path() / "ape3_launcher_test_ps2x.ini";
    s.renderScale = 150;
    if (!saveIni(tempIni, s, extras))
    {
        std::cerr << "FAIL: saveIni failed\n";
        return 1;
    }

    const std::vector<std::string> savedLines = readLines(tempIni);
    if (!containsLine(savedLines, "# Ape Escape 3 recomp settings. Environment variables (PS2X_*) override this file.") ||
        !containsLine(savedLines, "[debug]") ||
        !containsLine(savedLines, "# background_window: 1 keeps the window behind others") ||
        !containsLine(savedLines, "background_window = 0") ||
        !containsLine(savedLines, "render_scale = 150"))
    {
        std::cerr << "FAIL: round-trip did not preserve unknown lines or rewrite known key\n";
        std::filesystem::remove(tempIni);
        return 1;
    }

    Settings reloaded;
    IniExtras reloadedExtras;
    if (!loadIni(tempIni, reloaded, reloadedExtras) || reloaded.renderScale != 150)
    {
        std::cerr << "FAIL: reloaded renderScale mismatch\n";
        std::filesystem::remove(tempIni);
        return 1;
    }

    reloaded.gameDir = "extracted_game";
    reloaded.volume = 65;
    if (!saveIni(tempIni, reloaded, reloadedExtras))
    {
        std::cerr << "FAIL: saveIni with gameDir/volume failed\n";
        std::filesystem::remove(tempIni);
        return 1;
    }
    Settings reloadedGameAudio;
    IniExtras reloadedGameAudioExtras;
    if (!loadIni(tempIni, reloadedGameAudio, reloadedGameAudioExtras) ||
        reloadedGameAudio.gameDir != "extracted_game" || reloadedGameAudio.volume != 65)
    {
        std::cerr << "FAIL: reloaded gameDir/volume mismatch\n";
        std::filesystem::remove(tempIni);
        return 1;
    }
    std::filesystem::remove(tempIni);
    std::cout << "PASS: ini round-trip preserves unknown lines and rewrites known keys\n";

    // 2. buildEnvironment release profile + field mappings + no developer keys
    Settings envSettings;
    envSettings.developer = false;
    envSettings.memoryCard = "mc0.ps2";
    envSettings.loadTiming = "fast";
    envSettings.aspect = "16:9";
    envSettings.aspectMax = "21:9";
    envSettings.hudAnchor = "16:9";
    envSettings.renderScale = 125;
    envSettings.msaa = 2;
    envSettings.fullscreen = true;
    envSettings.windowSize = "1920x1080";
    envSettings.texturePack = "mods/hd";

    const auto env = buildEnvironment(envSettings);
    std::map<std::string, std::string> envMap;
    for (const auto &kv : env)
    {
        if (kv.first.rfind("PS2X_DEV_CMD", 0) == 0 ||
            kv.first.rfind("PS2X_PAD_", 0) == 0 ||
            kv.first.find("PROBE") != std::string::npos)
        {
            std::cerr << "FAIL: developer/probe env var emitted when developer=false: " << kv.first << "\n";
            return 1;
        }
        envMap[kv.first] = kv.second;
    }

    const std::vector<std::pair<std::string, std::string>> expectedRelease = {
        {"PS2X_GS_ASYNC", "1"},
        {"PS2X_VIF1_ASYNC", "1"},
        {"PS2X_GS_VULKAN", "1"},
        {"PS2X_SG2_LLE", "1"},
        {"PS2X_EEDC", "1"},
        {"PS2X_EEDC_CHECK", "0"},
        {"PS2X_FRONTEND", "sdl"},
        {"PS2X_SDL_RD", "1"},
        {"PS2X_RD_VIEW", "1"},
        {"PS2X_RD_CUT_ADAPT", "1"},
        {"PS2X_RD_COVER_TOL", "400"},
        {"PS2X_RD_PAIRLAG", "1"},
        {"PS2X_MC", "mc0.ps2"},
        {"PS2X_LOAD_TIMING", "fast"},
        {"PS2X_ASPECT", "16:9"},
        {"PS2X_ASPECT_MAX", "21:9"},
        {"PS2X_HUD_ANCHOR", "16:9"},
        {"PS2X_RENDER_SCALE", "125"},
        {"PS2X_MSAA", "2"},
        {"PS2X_FULLSCREEN", "1"},
        {"PS2X_WINDOW_SIZE", "1920x1080"},
        {"PS2X_TEX_REPLACE_DIR", "mods/hd"},
    };

    for (const auto &kv : expectedRelease)
    {
        auto it = envMap.find(kv.first);
        if (it == envMap.end() || it->second != kv.second)
        {
            std::cerr << "FAIL: env var mismatch for " << kv.first << "\n";
            return 1;
        }
    }
    std::cout << "PASS: buildEnvironment emits all 14 release-profile keys and no developer keys\n";

    // 3. buildArgs
    Settings argsSettings;
    auto argsNoIso = buildArgs(argsSettings);
    if (argsNoIso.size() != 1 || argsNoIso[0] != "SCUS_975.01")
    {
        std::cerr << "FAIL: buildArgs without isoPath unexpected\n";
        return 1;
    }
    argsSettings.isoPath = "game.iso";
    auto argsWithIso = buildArgs(argsSettings);
    if (argsWithIso.size() != 3 || argsWithIso[0] != "SCUS_975.01" ||
        argsWithIso[1] != "--iso" || argsWithIso[2] != "game.iso")
    {
        std::cerr << "FAIL: buildArgs with isoPath unexpected\n";
        return 1;
    }
    std::cout << "PASS: buildArgs formats elfName and optional --iso\n";

    // 4. validate
    Settings valid;
    valid.isoPath = iniPath.string();
    if (!validate(valid).empty())
    {
        std::cerr << "FAIL: validate rejected valid settings: " << validate(valid) << "\n";
        return 1;
    }

    Settings missingIso = valid;
    missingIso.isoPath.clear();
    missingIso.gameDir.clear();
    if (validate(missingIso) != "No game image selected.")
    {
        std::cerr << "FAIL: validate did not return expected message for empty isoPath and gameDir\n";
        return 1;
    }

    Settings validGameDir = valid;
    validGameDir.isoPath.clear();
    validGameDir.gameDir = std::filesystem::temp_directory_path().string();
    if (!validate(validGameDir).empty())
    {
        std::cerr << "FAIL: validate rejected valid gameDir: " << validate(validGameDir) << "\n";
        return 1;
    }

    Settings badIso = valid;
    badIso.isoPath = "nonexistent_ape3_image_12345.iso";
    if (validate(badIso).find(badIso.isoPath) == std::string::npos)
    {
        std::cerr << "FAIL: validate did not reject missing isoPath with path\n";
        return 1;
    }

    Settings badGameDir = valid;
    badGameDir.isoPath.clear();
    badGameDir.gameDir = "nonexistent_ape3_dir_12345";
    if (validate(badGameDir).find(badGameDir.gameDir) == std::string::npos)
    {
        std::cerr << "FAIL: validate did not reject missing gameDir with path\n";
        return 1;
    }

    Settings badScale = valid;
    badScale.renderScale = 10;
    if (validate(badScale).empty())
    {
        std::cerr << "FAIL: validate accepted renderScale=10\n";
        return 1;
    }

    Settings badMsaa = valid;
    badMsaa.msaa = 3;
    if (validate(badMsaa).empty())
    {
        std::cerr << "FAIL: validate accepted msaa=3\n";
        return 1;
    }

    Settings badWin = valid;
    badWin.windowSize = "1280x0";
    if (validate(badWin).empty())
    {
        std::cerr << "FAIL: validate accepted windowSize=1280x0\n";
        return 1;
    }
    std::cout << "PASS: validate accepts valid settings and rejects invalid cases\n";

    return 0;
}
