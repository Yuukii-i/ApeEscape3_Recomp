#include "process.h"

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
#include <algorithm>
#include <cwctype>
#include <map>
#else
#include <cerrno>
#include <cstring>
#include <fcntl.h>
#include <signal.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <unistd.h>
#endif

namespace ape3::launcher
{
namespace
{

#ifdef _WIN32
std::wstring utf8ToWide(const std::string &s)
{
    if (s.empty())
        return {};
    const int needed = MultiByteToWideChar(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), nullptr, 0);
    if (needed <= 0)
        return {};
    std::wstring out(static_cast<size_t>(needed), L'\0');
    MultiByteToWideChar(CP_UTF8, 0, s.c_str(), static_cast<int>(s.size()), out.data(), needed);
    return out;
}

std::wstring quoteArgWindows(const std::wstring &arg)
{
    if (!arg.empty() && arg.find_first_of(L" \t\n\v\"") == std::wstring::npos)
        return arg;

    std::wstring out = L"\"";
    for (auto it = arg.begin();; ++it)
    {
        size_t backslashes = 0;
        while (it != arg.end() && *it == L'\\')
        {
            ++it;
            ++backslashes;
        }
        if (it == arg.end())
        {
            out.append(backslashes * 2, L'\\');
            break;
        }
        if (*it == L'"')
        {
            out.append(backslashes * 2 + 1, L'\\');
            out.push_back(L'"');
        }
        else
        {
            out.append(backslashes, L'\\');
            out.push_back(*it);
        }
    }
    out.push_back(L'"');
    return out;
}

struct CaseInsensitiveLess
{
    bool operator()(const std::wstring &a, const std::wstring &b) const
    {
        return _wcsicmp(a.c_str(), b.c_str()) < 0;
    }
};

std::vector<wchar_t> buildEnvBlockWindows(const std::vector<std::pair<std::string, std::string>> &overrides)
{
    std::map<std::wstring, std::wstring, CaseInsensitiveLess> envMap;
    if (LPWCH raw = GetEnvironmentStringsW())
    {
        const wchar_t *p = raw;
        while (*p != L'\0')
        {
            const std::wstring entry(p);
            const size_t eq = entry.find(L'=');
            if (eq != std::wstring::npos && eq > 0)
            {
                envMap[entry.substr(0, eq)] = entry.substr(eq + 1);
            }
            p += entry.size() + 1;
        }
        FreeEnvironmentStringsW(raw);
    }

    for (const auto &kv : overrides)
    {
        envMap[utf8ToWide(kv.first)] = utf8ToWide(kv.second);
    }

    std::vector<wchar_t> block;
    for (const auto &kv : envMap)
    {
        block.insert(block.end(), kv.first.begin(), kv.first.end());
        block.push_back(L'=');
        block.insert(block.end(), kv.second.begin(), kv.second.end());
        block.push_back(L'\0');
    }
    if (block.empty())
        block.push_back(L'\0');
    block.push_back(L'\0');
    return block;
}

void closeHandles(ProcessHandle &handle)
{
    if (handle.process)
    {
        CloseHandle(static_cast<HANDLE>(handle.process));
        handle.process = nullptr;
    }
    if (handle.thread)
    {
        CloseHandle(static_cast<HANDLE>(handle.thread));
        handle.thread = nullptr;
    }
    if (handle.readPipe)
    {
        CloseHandle(static_cast<HANDLE>(handle.readPipe));
        handle.readPipe = nullptr;
    }
}
#endif

} // namespace

bool startRuntime(const std::filesystem::path &runtimeExe,
                  const std::filesystem::path &workingDir,
                  const std::vector<std::string> &args,
                  const std::vector<std::pair<std::string, std::string>> &env,
                  ProcessHandle &handle,
                  std::string *errorOut)
{
    if (isRunning(handle))
        stop(handle);

    handle.running = false;
    handle.hasExited = false;
    handle.exitCode = -1;

#ifdef _WIN32
    closeHandles(handle);

    std::error_code ec;
    if (runtimeExe.empty() || !std::filesystem::exists(runtimeExe, ec))
    {
        if (errorOut)
            *errorOut = "Runtime executable not found: " + runtimeExe.string();
        return false;
    }

    SECURITY_ATTRIBUTES sa{};
    sa.nLength = sizeof(sa);
    sa.bInheritHandle = TRUE;

    HANDLE readPipe = nullptr;
    HANDLE writePipe = nullptr;
    if (!CreatePipe(&readPipe, &writePipe, &sa, 0))
    {
        if (errorOut)
            *errorOut = "Failed to create output pipe.";
        return false;
    }
    SetHandleInformation(readPipe, HANDLE_FLAG_INHERIT, 0);

    std::wstring cmdLine = quoteArgWindows(runtimeExe.wstring());
    for (const std::string &arg : args)
    {
        cmdLine.push_back(L' ');
        cmdLine += quoteArgWindows(utf8ToWide(arg));
    }

    std::vector<wchar_t> envBlock = buildEnvBlockWindows(env);

    STARTUPINFOW si{};
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESTDHANDLES;
    si.hStdOutput = writePipe;
    si.hStdError = writePipe;
    si.hStdInput = GetStdHandle(STD_INPUT_HANDLE);

    PROCESS_INFORMATION pi{};
    const std::wstring exeW = runtimeExe.wstring();
    const std::wstring dirW = workingDir.wstring();
    const BOOL ok = CreateProcessW(
        exeW.c_str(),
        cmdLine.data(),
        nullptr,
        nullptr,
        TRUE,
        CREATE_UNICODE_ENVIRONMENT | CREATE_NO_WINDOW,
        envBlock.data(),
        dirW.empty() ? nullptr : dirW.c_str(),
        &si,
        &pi);

    CloseHandle(writePipe);

    if (!ok)
    {
        const DWORD err = GetLastError();
        CloseHandle(readPipe);
        if (errorOut)
            *errorOut = "CreateProcessW failed with error code " + std::to_string(err) + ".";
        return false;
    }

    handle.process = pi.hProcess;
    handle.thread = pi.hThread;
    handle.readPipe = readPipe;
    handle.running = true;
    return true;
#else
    if (handle.readFd >= 0)
    {
        close(handle.readFd);
        handle.readFd = -1;
    }

    int pipefd[2]{-1, -1};
    if (pipe(pipefd) != 0)
    {
        if (errorOut)
            *errorOut = "pipe() failed: " + std::string(std::strerror(errno));
        return false;
    }

    const pid_t pid = fork();
    if (pid < 0)
    {
        close(pipefd[0]);
        close(pipefd[1]);
        if (errorOut)
            *errorOut = "fork() failed: " + std::string(std::strerror(errno));
        return false;
    }

    if (pid == 0)
    {
        close(pipefd[0]);
        dup2(pipefd[1], STDOUT_FILENO);
        dup2(pipefd[1], STDERR_FILENO);
        close(pipefd[1]);

        if (!workingDir.empty())
            chdir(workingDir.c_str());

        for (const auto &kv : env)
            setenv(kv.first.c_str(), kv.second.c_str(), 1);

        std::vector<std::string> storage;
        storage.reserve(args.size() + 1);
        storage.push_back(runtimeExe.string());
        for (const auto &a : args)
            storage.push_back(a);

        std::vector<char *> argv;
        argv.reserve(storage.size() + 1);
        for (auto &s : storage)
            argv.push_back(s.data());
        argv.push_back(nullptr);

        execvp(runtimeExe.c_str(), argv.data());
        _exit(127);
    }

    close(pipefd[1]);
    const int flags = fcntl(pipefd[0], F_GETFL, 0);
    if (flags >= 0)
        fcntl(pipefd[0], F_SETFL, flags | O_NONBLOCK);

    handle.pid = static_cast<int>(pid);
    handle.readFd = pipefd[0];
    handle.running = true;
    return true;
#endif
}

bool pollOutput(ProcessHandle &handle, std::string &chunk)
{
    chunk.clear();
#ifdef _WIN32
    if (!handle.readPipe)
        return false;

    bool gotAny = false;
    char buffer[4096];
    for (;;)
    {
        DWORD avail = 0;
        if (!PeekNamedPipe(static_cast<HANDLE>(handle.readPipe), nullptr, 0, nullptr, &avail, nullptr))
            break;
        if (avail == 0)
            break;
        DWORD toRead = avail < sizeof(buffer) ? avail : static_cast<DWORD>(sizeof(buffer));
        DWORD bytesRead = 0;
        if (!ReadFile(static_cast<HANDLE>(handle.readPipe), buffer, toRead, &bytesRead, nullptr) || bytesRead == 0)
            break;
        chunk.append(buffer, bytesRead);
        gotAny = true;
    }
    return gotAny;
#else
    if (handle.readFd < 0)
        return false;

    bool gotAny = false;
    char buffer[4096];
    for (;;)
    {
        const ssize_t n = read(handle.readFd, buffer, sizeof(buffer));
        if (n > 0)
        {
            chunk.append(buffer, static_cast<size_t>(n));
            gotAny = true;
            continue;
        }
        break;
    }
    return gotAny;
#endif
}

bool isRunning(ProcessHandle &handle)
{
    if (!handle.running)
        return false;

#ifdef _WIN32
    if (!handle.process)
    {
        handle.running = false;
        return false;
    }
    const DWORD wait = WaitForSingleObject(static_cast<HANDLE>(handle.process), 0);
    if (wait == WAIT_OBJECT_0)
    {
        DWORD code = 0;
        GetExitCodeProcess(static_cast<HANDLE>(handle.process), &code);
        handle.exitCode = static_cast<int>(code);
        handle.running = false;
        handle.hasExited = true;
        CloseHandle(static_cast<HANDLE>(handle.process));
        handle.process = nullptr;
        if (handle.thread)
        {
            CloseHandle(static_cast<HANDLE>(handle.thread));
            handle.thread = nullptr;
        }
        return false;
    }
    return true;
#else
    if (handle.pid <= 0)
    {
        handle.running = false;
        return false;
    }
    int status = 0;
    const pid_t res = waitpid(static_cast<pid_t>(handle.pid), &status, WNOHANG);
    if (res > 0)
    {
        handle.exitCode = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
        handle.running = false;
        handle.hasExited = true;
        handle.pid = -1;
        return false;
    }
    return true;
#endif
}

void stop(ProcessHandle &handle)
{
#ifdef _WIN32
    if (handle.process)
    {
        TerminateProcess(static_cast<HANDLE>(handle.process), 1);
        WaitForSingleObject(static_cast<HANDLE>(handle.process), 2000);
        DWORD code = 1;
        GetExitCodeProcess(static_cast<HANDLE>(handle.process), &code);
        handle.exitCode = static_cast<int>(code);
    }
    closeHandles(handle);
    handle.running = false;
    handle.hasExited = true;
#else
    if (handle.pid > 0)
    {
        kill(static_cast<pid_t>(handle.pid), SIGTERM);
        int status = 0;
        waitpid(static_cast<pid_t>(handle.pid), &status, 0);
        handle.exitCode = WIFEXITED(status) ? WEXITSTATUS(status) : -1;
        handle.pid = -1;
    }
    if (handle.readFd >= 0)
    {
        close(handle.readFd);
        handle.readFd = -1;
    }
    handle.running = false;
    handle.hasExited = true;
#endif
}

int exitCode(const ProcessHandle &handle)
{
    return handle.exitCode;
}

} // namespace ape3::launcher
