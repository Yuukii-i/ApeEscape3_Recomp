#pragma once

#include <filesystem>
#include <string>
#include <utility>
#include <vector>

namespace ape3::launcher
{

struct ProcessHandle
{
    bool running = false;
    bool hasExited = false;
    int exitCode = -1;
#ifdef _WIN32
    void *process = nullptr;
    void *thread = nullptr;
    void *readPipe = nullptr;
#else
    int pid = -1;
    int readFd = -1;
#endif
};

bool startRuntime(const std::filesystem::path &runtimeExe,
                  const std::filesystem::path &workingDir,
                  const std::vector<std::string> &args,
                  const std::vector<std::pair<std::string, std::string>> &env,
                  ProcessHandle &handle,
                  std::string *errorOut = nullptr);

bool pollOutput(ProcessHandle &handle, std::string &chunk);
bool isRunning(ProcessHandle &handle);
void stop(ProcessHandle &handle);
int exitCode(const ProcessHandle &handle);

} // namespace ape3::launcher
