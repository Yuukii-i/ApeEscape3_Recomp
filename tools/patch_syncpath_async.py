"""One-shot patch (PERF-SA): PS2X_SYNCPATH_ASYNC=1 -> sceGsSyncPath(0) no longer waits for the VIF1 worker / GIF (skips the VIF1_STAT and GIF_STAT polls, which fence)."""
p = "C:/ApeEscape3_Recomp/PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/GS.cpp"
t = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in t
if crlf:
    t = t.replace("\r\n", "\n")
a = "            while ((mem.readIORegister(0x10003C00) & 0x1F000003) != 0)\n            {"
assert t.count(a) == 1
b = '''            // PERF-SA (PS2X_SYNCPATH_ASYNC=1): the packets of this frame are already copied into the VIF1 worker's queue, so the guest's buffers are free;
            // the VIF1_STAT / GIF_STAT polls below would block the EE until the worker (VU1 + GIF) has finished the frame. Skipped: EE and worker overlap.
            static const bool s_syncPathAsync = []() { const char *e = std::getenv("PS2X_SYNCPATH_ASYNC"); return e && e[0] == '1'; }();
            if (s_syncPathAsync)
            {
                setReturnS32(ctx, 0);
                return;
            }

''' + a
t = t.replace(a, b)
if crlf:
    t = t.replace("\n", "\r\n")
open(p, "w", encoding="utf-8", newline="").write(t)
print("ok")
