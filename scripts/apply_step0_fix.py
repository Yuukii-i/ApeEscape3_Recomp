path = 'PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp'
with open(path, 'rb') as f:
    content = f.read()

target1 = b'''void ps2xSafeLog(const char *fmt, ...)
{
    std::lock_guard<std::mutex> lock(s_logMutex);
    va_list args;
    va_start(args, fmt);
    std::vfprintf(stderr, fmt, args);
    va_end(args);
    std::fflush(stderr);
}'''.replace(b'\n', b'\r\n')

replacement1 = b'''void ps2xSafeLog(const char *fmt, ...)
{
    char buf[4096];
    va_list args;
    va_start(args, fmt);
    int len = std::vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    if (len > 0)
    {
        size_t writeLen = (len < static_cast<int>(sizeof(buf))) ? static_cast<size_t>(len) : (sizeof(buf) - 1);
        std::lock_guard<std::mutex> lock(s_logMutex);
        std::fwrite(buf, 1, writeLen, stderr);
        std::fflush(stderr);
    }
}'''.replace(b'\n', b'\r\n')

assert target1 in content, "target1 not found!"
content = content.replace(target1, replacement1, 1)

target2 = b'''        if (it != s_boundConfigStubs.end())
        {
            it->second.handler(rdram, ctx, runtime);
        }'''.replace(b'\n', b'\r\n')

replacement2 = b'''        if (it != s_boundConfigStubs.end())
        {
            it->second.handler(rdram, ctx, runtime);
            if (it->second.name == "vfprintf" || it->second.name == "_vfprintf_r" ||
                it->second.name == "sprintf" || it->second.name == "_sprintf_r" ||
                it->second.name == "printf" || it->second.name == "_printf_r")
            {
                std::lock_guard<std::mutex> lock(s_logMutex);
                std::fputc('\\n', stderr);
                std::fflush(stderr);
            }
        }'''.replace(b'\n', b'\r\n')

assert target2 in content, "target2 not found!"
content = content.replace(target2, replacement2, 1)

with open(path, 'wb') as f:
    f.write(content)

print("Successfully applied step 0 log buffering fix to ps2_runtime.cpp")
