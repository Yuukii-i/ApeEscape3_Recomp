"""One-shot patch (PERF-PU): GSVulkanBackend::Present releases the wrapper mutex before cpu_->Present (VRAM snapshot + display conversion, protected by the CPU backend's own mutex)."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/gs/ps2_vk_gs_backend.cpp"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
a = "        PresentationFrame Present(const GSPresentationRequest &request) override\n        {\n            std::lock_guard<std::mutex> lk(m_);\n"
assert t.count(a) == 1
b = "        PresentationFrame Present(const GSPresentationRequest &request) override\n        {\n            std::unique_lock<std::mutex> lk(m_);\n"
t = t.replace(a, b)
a2 = "            ++presents_;\n            maybePrintStats();\n            primsThisFrame_ = 0;\n            return cpu_->Present(request);\n        }"
assert t.count(a2) == 1
b2 = "            ++presents_;\n            maybePrintStats();\n            primsThisFrame_ = 0;\n            lk.unlock(); // PERF-PU: the VRAM snapshot + display conversion run under the CPU backend's own mutex; the draw thread no longer waits for them\n            return cpu_->Present(request);\n        }"
t = t.replace(a2, b2)
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
