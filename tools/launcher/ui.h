#pragma once

#include "process.h"
#include "settings.h"

#include <filesystem>
#include <mutex>
#include <string>
#include <vector>

struct SDL_Window;

namespace ape3::launcher
{

struct LauncherState
{
    Settings settings;
    IniExtras extras;
    std::filesystem::path iniPath;
    std::filesystem::path fallbackIniPath;
    std::filesystem::path launcherIniPath;
    std::filesystem::path fallbackLauncherIniPath;
    std::filesystem::path exeDir;
    std::string runtimeExe;
    std::string validationError;
    std::string statusMessage;

    ProcessHandle process;
    std::vector<std::string> logLines;
    std::string partialLine;
    bool scrollLogToBottom = false;
    bool quitRequested = false;

    std::mutex dialogMutex;
    bool hasPendingIso = false;
    std::string pendingIsoPath;
    bool hasPendingGameDir = false;
    std::string pendingGameDir;
};

void appendLogChunk(LauncherState &state, const std::string &chunk);
bool saveLauncherIni(const std::filesystem::path &path, const std::string &runtimeExe);
std::string loadLauncherIni(const std::filesystem::path &path);
void renderLauncherUi(LauncherState &state, SDL_Window *window);

} // namespace ape3::launcher
