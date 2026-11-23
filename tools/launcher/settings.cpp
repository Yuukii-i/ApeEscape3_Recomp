#include "settings.h"

#include <algorithm>
#include <cctype>
#include <fstream>
#include <set>
#include <sstream>

namespace ape3::launcher
{
namespace
{

std::string trim(const std::string &s)
{
    const size_t first = s.find_first_not_of(" \t\r\n");
    if (first == std::string::npos)
        return "";
    const size_t last = s.find_last_not_of(" \t\r\n");
    return s.substr(first, last - first + 1);
}

std::string toLower(std::string s)
{
    for (char &c : s)
        c = static_cast<char>(std::tolower(static_cast<unsigned char>(c)));
    return s;
}

bool parseBool(const std::string &val, bool fallback)
{
    const std::string l = toLower(trim(val));
    if (l == "1" || l == "on" || l == "true" || l == "yes")
        return true;
    if (l == "0" || l == "off" || l == "false" || l == "no")
        return false;
    return fallback;
}

bool parseIntStrict(const std::string &val, int &out)
{
    const std::string t = trim(val);
    if (t.empty())
        return false;
    size_t idx = 0;
    try
    {
        int parsed = std::stoi(t, &idx);
        if (idx != t.size())
            return false;
        out = parsed;
        return true;
    }
    catch (...)
    {
        return false;
    }
}

bool parseSectionHeader(const std::string &trimmedLine, std::string &sectionOut)
{
    if (trimmedLine.size() < 2 || trimmedLine.front() != '[')
        return false;
    const size_t close = trimmedLine.find(']');
    if (close == std::string::npos)
        return false;
    sectionOut = toLower(trim(trimmedLine.substr(1, close - 1)));
    return true;
}

bool parseKeyValue(const std::string &trimmedLine, std::string &keyOut, std::string &valOut)
{
    if (trimmedLine.empty() || trimmedLine.front() == '#' || trimmedLine.front() == ';' || trimmedLine.front() == '[')
        return false;
    const size_t eq = trimmedLine.find('=');
    if (eq == std::string::npos)
        return false;
    keyOut = toLower(trim(trimmedLine.substr(0, eq)));
    valOut = trim(trimmedLine.substr(eq + 1));
    return !keyOut.empty();
}

struct KeyEntry
{
    const char *key;
    std::string (*getter)(const Settings &);
};

const KeyEntry kGraphicsKeys[] = {
    {"renderer", [](const Settings &s) { return s.renderer; }},
    {"aspect", [](const Settings &s) { return s.aspect; }},
    {"aspect_max", [](const Settings &s) { return s.aspectMax; }},
    {"hud_anchor", [](const Settings &s) { return s.hudAnchor; }},
    {"render_scale", [](const Settings &s) { return std::to_string(s.renderScale); }},
    {"msaa", [](const Settings &s) { return std::to_string(s.msaa); }},
    {"vsync", [](const Settings &s) -> std::string { return s.vsync ? "on" : "off"; }},
    {"fullscreen", [](const Settings &s) -> std::string { return s.fullscreen ? "1" : "0"; }},
    {"window", [](const Settings &s) { return s.windowSize; }},
    {"texture_pack", [](const Settings &s) { return s.texturePack; }},
};

const KeyEntry kLauncherKeys[] = {
    {"iso_path", [](const Settings &s) { return s.isoPath; }},
    {"elf_name", [](const Settings &s) { return s.elfName; }},
    {"load_timing", [](const Settings &s) { return s.loadTiming; }},
    {"memory_card", [](const Settings &s) { return s.memoryCard; }},
    {"developer", [](const Settings &s) -> std::string { return s.developer ? "1" : "0"; }},
};

const KeyEntry kGameKeys[] = {
    {"game_dir", [](const Settings &s) { return s.gameDir; }},
};

const KeyEntry kAudioKeys[] = {
    {"volume", [](const Settings &s) { return std::to_string(s.volume); }},
};

const KeyEntry *findKeyEntry(const std::string &section, const std::string &key)
{
    if (section == "graphics")
    {
        for (const auto &entry : kGraphicsKeys)
        {
            if (key == entry.key)
                return &entry;
        }
    }
    else if (section == "launcher")
    {
        for (const auto &entry : kLauncherKeys)
        {
            if (key == entry.key)
                return &entry;
        }
    }
    else if (section == "game")
    {
        for (const auto &entry : kGameKeys)
        {
            if (key == entry.key)
                return &entry;
        }
    }
    else if (section == "audio")
    {
        for (const auto &entry : kAudioKeys)
        {
            if (key == entry.key)
                return &entry;
        }
    }
    return nullptr;
}

bool hasLauncherValues(const Settings &s)
{
    return !s.isoPath.empty() || s.elfName != "SCUS_975.01" || s.loadTiming != "original" ||
           !s.memoryCard.empty() || s.developer;
}

bool hasGameValues(const Settings &s)
{
    return !s.gameDir.empty();
}

bool hasAudioValues(const Settings &s)
{
    return s.volume != 100;
}

} // namespace

bool loadIni(const std::filesystem::path &path, Settings &settings, IniExtras &extras)
{
    std::ifstream in(path);
    if (!in)
        return false;

    extras.lines.clear();
    std::string line;
    std::string currentSection;

    while (std::getline(in, line))
    {
        if (!line.empty() && line.back() == '\r')
            line.pop_back();
        extras.lines.push_back(line);

        const std::string t = trim(line);
        std::string sec;
        if (parseSectionHeader(t, sec))
        {
            currentSection = sec;
            continue;
        }

        std::string key;
        std::string val;
        if (!parseKeyValue(t, key, val))
            continue;

        if (currentSection == "graphics")
        {
            if (key == "renderer")
                settings.renderer = toLower(val);
            else if (key == "aspect")
                settings.aspect = toLower(val);
            else if (key == "aspect_max")
                settings.aspectMax = toLower(val);
            else if (key == "hud_anchor")
                settings.hudAnchor = toLower(val);
            else if (key == "render_scale")
            {
                int v = 0;
                if (parseIntStrict(val, v))
                    settings.renderScale = v;
            }
            else if (key == "msaa")
            {
                int v = 0;
                if (parseIntStrict(val, v))
                    settings.msaa = v;
            }
            else if (key == "vsync")
                settings.vsync = parseBool(val, settings.vsync);
            else if (key == "fullscreen")
                settings.fullscreen = parseBool(val, settings.fullscreen);
            else if (key == "window")
                settings.windowSize = val;
            else if (key == "texture_pack")
                settings.texturePack = val;
        }
        else if (currentSection == "launcher")
        {
            if (key == "iso_path")
                settings.isoPath = val;
            else if (key == "elf_name" && !val.empty())
                settings.elfName = val;
            else if (key == "load_timing")
                settings.loadTiming = toLower(val);
            else if (key == "memory_card")
                settings.memoryCard = val;
            else if (key == "developer")
                settings.developer = parseBool(val, settings.developer);
        }
        else if (currentSection == "game")
        {
            if (key == "game_dir")
                settings.gameDir = val;
        }
        else if (currentSection == "audio")
        {
            if (key == "volume")
            {
                int v = 100;
                if (parseIntStrict(val, v))
                    settings.volume = std::clamp(v, 0, 100);
            }
        }
    }

    return true;
}

bool saveIni(const std::filesystem::path &path, const Settings &settings, const IniExtras &extras)
{
    std::vector<std::string> outLines;
    outLines.reserve(extras.lines.size() + 16);

    std::string currentSection;
    std::set<std::string> writtenGraphics;
    std::set<std::string> writtenLauncher;
    std::set<std::string> writtenGame;
    std::set<std::string> writtenAudio;
    bool sawGraphicsSection = false;
    bool sawLauncherSection = false;
    bool sawGameSection = false;
    bool sawAudioSection = false;

    auto flushMissingForSection = [&](const std::string &sec) {
        if (sec == "graphics")
        {
            for (const auto &entry : kGraphicsKeys)
            {
                if (writtenGraphics.find(entry.key) == writtenGraphics.end())
                {
                    outLines.push_back(std::string(entry.key) + " = " + entry.getter(settings));
                    writtenGraphics.insert(entry.key);
                }
            }
        }
        else if (sec == "launcher")
        {
            for (const auto &entry : kLauncherKeys)
            {
                if (writtenLauncher.find(entry.key) == writtenLauncher.end())
                {
                    outLines.push_back(std::string(entry.key) + " = " + entry.getter(settings));
                    writtenLauncher.insert(entry.key);
                }
            }
        }
        else if (sec == "game")
        {
            for (const auto &entry : kGameKeys)
            {
                if (writtenGame.find(entry.key) == writtenGame.end())
                {
                    outLines.push_back(std::string(entry.key) + " = " + entry.getter(settings));
                    writtenGame.insert(entry.key);
                }
            }
        }
        else if (sec == "audio")
        {
            for (const auto &entry : kAudioKeys)
            {
                if (writtenAudio.find(entry.key) == writtenAudio.end())
                {
                    outLines.push_back(std::string(entry.key) + " = " + entry.getter(settings));
                    writtenAudio.insert(entry.key);
                }
            }
        }
    };

    for (const std::string &rawLine : extras.lines)
    {
        const std::string t = trim(rawLine);
        std::string nextSection;
        if (parseSectionHeader(t, nextSection))
        {
            flushMissingForSection(currentSection);
            currentSection = nextSection;
            if (currentSection == "graphics")
                sawGraphicsSection = true;
            else if (currentSection == "launcher")
                sawLauncherSection = true;
            else if (currentSection == "game")
                sawGameSection = true;
            else if (currentSection == "audio")
                sawAudioSection = true;
            outLines.push_back(rawLine);
            continue;
        }

        std::string key;
        std::string val;
        if (parseKeyValue(t, key, val))
        {
            if (const KeyEntry *entry = findKeyEntry(currentSection, key))
            {
                outLines.push_back(std::string(entry->key) + " = " + entry->getter(settings));
                if (currentSection == "graphics")
                    writtenGraphics.insert(entry->key);
                else if (currentSection == "launcher")
                    writtenLauncher.insert(entry->key);
                else if (currentSection == "game")
                    writtenGame.insert(entry->key);
                else if (currentSection == "audio")
                    writtenAudio.insert(entry->key);
                continue;
            }
        }

        outLines.push_back(rawLine);
    }

    flushMissingForSection(currentSection);

    if (!sawGraphicsSection)
    {
        if (!outLines.empty() && !outLines.back().empty())
            outLines.emplace_back("");
        outLines.emplace_back("[graphics]");
        flushMissingForSection("graphics");
    }

    if (!sawLauncherSection && hasLauncherValues(settings))
    {
        if (!outLines.empty() && !outLines.back().empty())
            outLines.emplace_back("");
        outLines.emplace_back("[launcher]");
        flushMissingForSection("launcher");
    }

    if (!sawGameSection && hasGameValues(settings))
    {
        if (!outLines.empty() && !outLines.back().empty())
            outLines.emplace_back("");
        outLines.emplace_back("[game]");
        flushMissingForSection("game");
    }

    if (!sawAudioSection && hasAudioValues(settings))
    {
        if (!outLines.empty() && !outLines.back().empty())
            outLines.emplace_back("");
        outLines.emplace_back("[audio]");
        flushMissingForSection("audio");
    }

    std::ofstream out(path, std::ios::trunc);
    if (!out)
        return false;

    for (const std::string &l : outLines)
        out << l << '\n';

    return out.good();
}

namespace
{

std::vector<std::string> extractUnknownLines(const IniExtras &extras)
{
    std::vector<std::string> unknown;
    std::string currentSection;
    for (const std::string &rawLine : extras.lines)
    {
        const std::string t = trim(rawLine);
        if (t.empty())
            continue;

        std::string sec;
        if (parseSectionHeader(t, sec))
        {
            currentSection = sec;
            if (sec != "graphics" && sec != "launcher" && sec != "game" && sec != "audio")
                unknown.push_back("[" + sec + "]");
            continue;
        }

        std::string key;
        std::string val;
        if (parseKeyValue(t, key, val))
        {
            if (findKeyEntry(currentSection, key) == nullptr)
                unknown.push_back(currentSection + "." + key + "=" + val);
            continue;
        }

        unknown.push_back(t);
    }
    return unknown;
}

} // namespace

bool hasDifferentUnknownContent(const IniExtras &a, const IniExtras &b)
{
    return extractUnknownLines(a) != extractUnknownLines(b);
}

std::vector<std::pair<std::string, std::string>> buildEnvironment(const Settings &settings)
{
    std::vector<std::pair<std::string, std::string>> env = {
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
        {"PS2X_MC", settings.memoryCard},
        {"PS2X_LOAD_TIMING", settings.loadTiming},
        {"PS2X_ASPECT", settings.aspect},
        {"PS2X_ASPECT_MAX", settings.aspectMax},
        {"PS2X_HUD_ANCHOR", settings.hudAnchor},
        {"PS2X_RENDER_SCALE", std::to_string(settings.renderScale)},
        {"PS2X_MSAA", std::to_string(settings.msaa)},
        {"PS2X_FULLSCREEN", settings.fullscreen ? "1" : "0"},
        {"PS2X_WINDOW_SIZE", settings.windowSize},
        {"PS2X_TEX_REPLACE_DIR", settings.texturePack},
        {"PS2X_VK_PRESENT", settings.vsync ? "fifo" : "immediate"},
    };
    return env;
}

std::vector<std::string> buildArgs(const Settings &settings)
{
    std::vector<std::string> args;
    args.push_back(settings.elfName);
    if (!settings.isoPath.empty())
    {
        args.push_back("--iso");
        args.push_back(settings.isoPath);
    }
    return args;
}

std::string validate(const Settings &settings)
{
    if (settings.isoPath.empty() && settings.gameDir.empty())
        return "No game image selected.";

    std::error_code ec;
    if (!settings.isoPath.empty())
    {
        if (!std::filesystem::exists(settings.isoPath, ec) ||
            !std::filesystem::is_regular_file(settings.isoPath, ec))
        {
            return "ISO path does not exist or is not a regular file: " + settings.isoPath;
        }

        std::ifstream isoStream(settings.isoPath, std::ios::binary);
        if (!isoStream.good())
            return "ISO path is not readable: " + settings.isoPath;
    }

    if (!settings.gameDir.empty())
    {
        if (!std::filesystem::exists(settings.gameDir, ec) ||
            !std::filesystem::is_directory(settings.gameDir, ec))
        {
            return "Extracted game folder does not exist or is not a directory: " + settings.gameDir;
        }
    }

    if (settings.renderScale < 25 || settings.renderScale > 400)
        return "render_scale must be between 25 and 400.";

    if (settings.msaa != 0 && settings.msaa != 2 && settings.msaa != 4 && settings.msaa != 8)
        return "msaa must be 0, 2, 4, or 8.";

    const size_t xPos = settings.windowSize.find_first_of("xX");
    if (xPos == std::string::npos || xPos == 0 || xPos + 1 >= settings.windowSize.size())
        return "window size must be WxH.";

    const std::string wStr = settings.windowSize.substr(0, xPos);
    const std::string hStr = settings.windowSize.substr(xPos + 1);
    int w = 0;
    int h = 0;
    if (!parseIntStrict(wStr, w) || !parseIntStrict(hStr, h) || w <= 0 || h <= 0)
        return "window size must be WxH with positive integers.";

    return "";
}

} // namespace ape3::launcher
