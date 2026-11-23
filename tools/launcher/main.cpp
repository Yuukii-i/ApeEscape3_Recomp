#include "process.h"
#include "settings.h"
#include "ui.h"

#include "imgui.h"
#include "imgui_impl_sdl3.h"
#include "imgui_impl_sdlrenderer3.h"

#include <SDL3/SDL.h>
#include <SDL3/SDL_main.h>

#include <chrono>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <string>
#include <thread>

namespace
{

bool isDirWritable(const std::filesystem::path &dir, const std::filesystem::path &probeFile)
{
    std::error_code ec;
    if (std::filesystem::exists(probeFile, ec))
    {
        std::ofstream test(probeFile, std::ios::app);
        return test.good();
    }
    std::filesystem::path tempProbe = dir / ".ape3_write_test.tmp";
    std::ofstream test(tempProbe, std::ios::trunc);
    const bool ok = test.good();
    test.close();
    std::filesystem::remove(tempProbe, ec);
    return ok;
}

std::filesystem::path getAppDataConfigDir()
{
#ifdef _WIN32
    if (const char *appData = std::getenv("APPDATA"))
        return std::filesystem::path(appData) / "ape3recomp";
#endif
    if (const char *home = std::getenv("HOME"))
        return std::filesystem::path(home) / ".config" / "ape3recomp";
    return std::filesystem::current_path();
}

void initLauncherPaths(ape3::launcher::LauncherState &state,
                       const std::filesystem::path &exeDir,
                       const std::filesystem::path &overrideIni)
{
    state.exeDir = exeDir;
    const std::filesystem::path appDataDir = getAppDataConfigDir();
    state.fallbackIniPath = appDataDir / "ps2x.ini";
    state.fallbackLauncherIniPath = appDataDir / "launcher.ini";

    const std::filesystem::path exeIni = state.exeDir / "ps2x.ini";
    std::error_code ec;
    if (!overrideIni.empty())
    {
        state.iniPath = overrideIni;
        state.launcherIniPath = isDirWritable(state.exeDir, state.exeDir / "launcher.ini")
                                    ? (state.exeDir / "launcher.ini")
                                    : state.fallbackLauncherIniPath;
        if (std::filesystem::exists(state.iniPath, ec))
            ape3::launcher::loadIni(state.iniPath, state.settings, state.extras);
    }
    else
    {
        if (isDirWritable(state.exeDir, exeIni))
        {
            state.iniPath = exeIni;
            state.launcherIniPath = state.exeDir / "launcher.ini";
        }
        else
        {
            std::filesystem::create_directories(appDataDir, ec);
            state.iniPath = state.fallbackIniPath;
            state.launcherIniPath = state.fallbackLauncherIniPath;
            state.statusMessage = "Config folder read-only; using " + state.iniPath.string();
        }

        if (std::filesystem::exists(state.iniPath, ec))
        {
            ape3::launcher::loadIni(state.iniPath, state.settings, state.extras);
        }
        else if (state.iniPath != exeIni && std::filesystem::exists(exeIni, ec))
        {
            ape3::launcher::loadIni(exeIni, state.settings, state.extras);
        }
    }

#ifdef _WIN32
    const std::string devExeName = "ps2EntryRunner_dev.exe";
    const std::string relExeName = "ps2EntryRunner.exe";
#else
    const std::string devExeName = "ps2EntryRunner_dev";
    const std::string relExeName = "ps2EntryRunner";
#endif
    const std::filesystem::path devRuntime = state.exeDir / devExeName;
    const std::filesystem::path relRuntime = state.exeDir / relExeName;

    if (std::filesystem::exists(state.launcherIniPath, ec))
        state.runtimeExe = ape3::launcher::loadLauncherIni(state.launcherIniPath);
    if (state.runtimeExe.empty())
    {
        if (std::filesystem::exists(devRuntime, ec))
            state.runtimeExe = devRuntime.string();
        else if (std::filesystem::exists(relRuntime, ec))
            state.runtimeExe = relRuntime.string();
        else
            state.runtimeExe = devRuntime.string();

        if (overrideIni.empty())
            ape3::launcher::saveLauncherIni(state.launcherIniPath, state.runtimeExe);
    }
    state.validationError = ape3::launcher::validate(state.settings);
}

int runPrintLaunch(ape3::launcher::LauncherState &state, bool withPlay)
{
    const std::filesystem::path exePath = ape3::launcher::resolveRuntimeExePath(state);
    const std::filesystem::path workDir = ape3::launcher::resolveRuntimeWorkDir(state);

    ape3::launcher::PlayIniResult playIni;
    if (withPlay)
        playIni = ape3::launcher::writePlayInis(state);

    const auto args = ape3::launcher::buildArgs(state.settings);
    std::string argsStr;
    for (size_t i = 0; i < args.size(); ++i)
    {
        if (i > 0)
            argsStr.push_back(' ');
        argsStr += args[i];
    }

    std::cout << "exe=" << exePath.string() << '\n';
    std::cout << "cwd=" << workDir.string() << '\n';
    if (withPlay)
    {
        std::string writtenStr;
        for (size_t i = 0; i < playIni.writtenPaths.size(); ++i)
        {
            if (i > 0)
                writtenStr.push_back(';');
            writtenStr += playIni.writtenPaths[i].string();
        }
        std::cout << "ini_written=" << (writtenStr.empty() ? "none" : writtenStr) << '\n';
        if (!playIni.runtimeDirWritable && !playIni.note.empty())
            std::cout << "note=" << playIni.note << '\n';
    }
    std::cout << "args=" << argsStr << '\n';

    const auto env = ape3::launcher::buildEnvironment(state.settings);
    for (const auto &kv : env)
        std::cout << "ENV " << kv.first << '=' << kv.second << '\n';

    const std::string valErr = ape3::launcher::validate(state.settings);
    std::cout << "validate=" << (valErr.empty() ? "ok" : valErr) << '\n';
    return valErr.empty() ? 0 : 2;
}

int runHeadlessPlay(ape3::launcher::LauncherState &state)
{
    const ape3::launcher::PlayIniResult playIni = ape3::launcher::writePlayInis(state);
    if (!playIni.runtimeDirWritable && !playIni.note.empty())
        std::cerr << playIni.note << '\n';

    const std::string valErr = ape3::launcher::validate(state.settings);
    if (!valErr.empty())
    {
        std::cerr << valErr << '\n';
        return 2;
    }

    const std::filesystem::path exePath = ape3::launcher::resolveRuntimeExePath(state);
    const std::filesystem::path workDir = ape3::launcher::resolveRuntimeWorkDir(state);

    const auto args = ape3::launcher::buildArgs(state.settings);
    const auto env = ape3::launcher::buildEnvironment(state.settings);

    ape3::launcher::ProcessHandle proc;
    std::string err;
    if (!ape3::launcher::startRuntime(exePath, workDir, args, env, proc, &err))
    {
        std::cerr << (err.empty() ? "Failed to start runtime." : err) << '\n';
        return 1;
    }

    while (ape3::launcher::isRunning(proc))
    {
        std::string chunk;
        if (ape3::launcher::pollOutput(proc, chunk))
            std::cout << chunk << std::flush;
        else
            std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }

    std::string chunk;
    while (ape3::launcher::pollOutput(proc, chunk) && !chunk.empty())
        std::cout << chunk << std::flush;

    return ape3::launcher::exitCode(proc);
}

} // namespace

int main(int argc, char *argv[])
{
    bool printLaunch = false;
    bool headlessPlay = false;
    std::filesystem::path cliIniPath;

    for (int i = 1; i < argc; ++i)
    {
        const std::string arg = argv[i];
        if (arg == "--print-launch")
        {
            printLaunch = true;
        }
        else if (arg == "--play")
        {
            headlessPlay = true;
        }
        else if (arg == "--ini")
        {
            if (i + 1 >= argc)
            {
                std::cerr << "--ini requires a file path\n";
                return 1;
            }
            cliIniPath = argv[++i];
        }
    }

    if (printLaunch || headlessPlay)
    {
        std::error_code ec;
        std::filesystem::path exeDir = std::filesystem::current_path(ec);
        if (argc > 0 && argv[0] && argv[0][0] != '\0')
        {
            const std::filesystem::path p = std::filesystem::absolute(argv[0], ec);
            if (!ec && p.has_parent_path())
                exeDir = p.parent_path();
        }
        ape3::launcher::LauncherState headlessState;
        initLauncherPaths(headlessState, exeDir, cliIniPath);
        if (printLaunch)
            return runPrintLaunch(headlessState, headlessPlay);
        return runHeadlessPlay(headlessState);
    }

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_GAMEPAD))
        return 1;

    SDL_Window *window = SDL_CreateWindow("Ape Escape 3 Recomp Launcher", 900, 620, SDL_WINDOW_RESIZABLE);
    if (!window)
    {
        SDL_Quit();
        return 1;
    }

    SDL_Renderer *renderer = SDL_CreateRenderer(window, nullptr);
    if (!renderer)
    {
        SDL_DestroyWindow(window);
        SDL_Quit();
        return 1;
    }
    SDL_SetRenderVSync(renderer, 1);

    IMGUI_CHECKVERSION();
    ImGui::CreateContext();
    ImGuiIO &io = ImGui::GetIO();
    io.IniFilename = nullptr;
    ImGui::StyleColorsDark();

    ImGui_ImplSDL3_InitForSDLRenderer(window, renderer);
    ImGui_ImplSDLRenderer3_Init(renderer);

    ape3::launcher::LauncherState state;
    const char *basePath = SDL_GetBasePath();
    const std::filesystem::path exeDir = basePath ? std::filesystem::path(basePath) : std::filesystem::current_path();
    initLauncherPaths(state, exeDir, cliIniPath);

    bool running = true;
    while (running && !state.quitRequested)
    {
        SDL_Event event;
        while (SDL_PollEvent(&event))
        {
            ImGui_ImplSDL3_ProcessEvent(&event);
            if (event.type == SDL_EVENT_QUIT)
                running = false;
            if (event.type == SDL_EVENT_WINDOW_CLOSE_REQUESTED &&
                event.window.windowID == SDL_GetWindowID(window))
            {
                running = false;
            }
        }

        std::string chunk;
        if (ape3::launcher::pollOutput(state.process, chunk))
            ape3::launcher::appendLogChunk(state, chunk);
        ape3::launcher::isRunning(state.process);

        ImGui_ImplSDLRenderer3_NewFrame();
        ImGui_ImplSDL3_NewFrame();
        ImGui::NewFrame();

        ape3::launcher::renderLauncherUi(state, window);

        ImGui::Render();
        SDL_SetRenderDrawColor(renderer, 20, 20, 24, 255);
        SDL_RenderClear(renderer);
        ImGui_ImplSDLRenderer3_RenderDrawData(ImGui::GetDrawData(), renderer);
        SDL_RenderPresent(renderer);
    }

    if (ape3::launcher::isRunning(state.process))
        ape3::launcher::stop(state.process);

    ImGui_ImplSDLRenderer3_Shutdown();
    ImGui_ImplSDL3_Shutdown();
    ImGui::DestroyContext();

    SDL_DestroyRenderer(renderer);
    SDL_DestroyWindow(window);
    SDL_Quit();
    return 0;
}
