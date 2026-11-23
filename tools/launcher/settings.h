#pragma once

#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace ape3::launcher
{

struct Settings
{
    std::string isoPath;
    std::string gameDir;
    std::string elfName = "SCUS_975.01";
    std::string renderer = "new";      // classic | new
    std::string aspect = "fill";
    std::string aspectMax = "21:9";
    std::string hudAnchor = "edge";
    int renderScale = 100;
    int msaa = 4;
    bool vsync = true;
    bool fullscreen = false;
    std::string windowSize = "1280x960"; // WxH
    std::string texturePack = "mods/textures";
    int volume = 100;
    std::string loadTiming = "original"; // original | fast
    std::string memoryCard;
    bool developer = false;
};

struct IniExtras
{
    std::vector<std::string> lines;
};

bool loadIni(const std::filesystem::path &path, Settings &settings, IniExtras &extras);
bool saveIni(const std::filesystem::path &path, const Settings &settings, const IniExtras &extras);

std::vector<std::pair<std::string, std::string>> buildEnvironment(const Settings &settings);
std::vector<std::string> buildArgs(const Settings &settings);
std::string validate(const Settings &settings);

} // namespace ape3::launcher
