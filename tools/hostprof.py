#!/usr/bin/env python3
"""External host-RIP sampling profiler for a running Windows x64 process.

Uses ctypes + Win32 ToolHelp32/Psapi/Kernel32/Winmm/DbgHelp to sample
thread RIPs (and optional StackWalk64 call stacks) with minimal suspend time.
"""

import argparse
import collections
import ctypes
from ctypes import wintypes
import datetime
import math
import os
import re
import subprocess
import sys
import time
import winreg
import winsound

# ---------------------------------------------------------------------------
# Win32 Constants
# ---------------------------------------------------------------------------

TH32CS_SNAPPROCESS = 0x00000002
TH32CS_SNAPTHREAD = 0x00000004
INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010

THREAD_SUSPEND_RESUME = 0x0002
THREAD_GET_CONTEXT = 0x0008
THREAD_QUERY_INFORMATION = 0x0040
THREAD_QUERY_LIMITED_INFORMATION = 0x0800

CONTEXT_AMD64 = 0x00100000
CONTEXT_CONTROL = CONTEXT_AMD64 | 0x00000001
CONTEXT_INTEGER = CONTEXT_AMD64 | 0x00000002
CONTEXT_FLAGS_TARGET = CONTEXT_CONTROL | CONTEXT_INTEGER

CONTEXT_SIZE = 1232
CONTEXT_OFF_FLAGS = 0x30
CONTEXT_OFF_RSP = 0x98
CONTEXT_OFF_RBP = 0xA0
CONTEXT_OFF_RIP = 0xF8

SYMOPT_UNDNAME = 0x00000002
SYMOPT_DEFERRED_LOADS = 0x00000004

IMAGE_FILE_MACHINE_AMD64 = 0x8664
ADDR_MODE_FLAT = 3
MAX_SYM_NAME = 1024
MAX_PATH = 260

GUEST_SUB_RE = re.compile(r"^sub_([0-9A-Fa-f]{6,8})(?:_|$)")


# ---------------------------------------------------------------------------
# Win32 Structures (64-bit)
# ---------------------------------------------------------------------------

class PROCESSENTRY32W(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ProcessID", wintypes.DWORD),
        ("th32DefaultHeapID", ctypes.c_size_t),
        ("th32ModuleID", wintypes.DWORD),
        ("cntThreads", wintypes.DWORD),
        ("th32ParentProcessID", wintypes.DWORD),
        ("pcPriClassBase", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
        ("szExeFile", ctypes.c_wchar * MAX_PATH),
    ]


class THREADENTRY32(ctypes.Structure):
    _fields_ = [
        ("dwSize", wintypes.DWORD),
        ("cntUsage", wintypes.DWORD),
        ("th32ThreadID", wintypes.DWORD),
        ("th32OwnerProcessID", wintypes.DWORD),
        ("tpBasePri", wintypes.LONG),
        ("tpDeltaPri", wintypes.LONG),
        ("dwFlags", wintypes.DWORD),
    ]


class MODULEINFO(ctypes.Structure):
    _fields_ = [
        ("lpBaseOfDll", ctypes.c_void_p),
        ("SizeOfImage", wintypes.DWORD),
        ("EntryPoint", ctypes.c_void_p),
    ]


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


class SYMBOL_INFOW(ctypes.Structure):
    _fields_ = [
        ("SizeOfStruct", wintypes.ULONG),
        ("TypeIndex", wintypes.ULONG),
        ("Reserved", ctypes.c_uint64 * 2),
        ("Index", wintypes.ULONG),
        ("Size", wintypes.ULONG),
        ("ModBase", ctypes.c_uint64),
        ("Flags", wintypes.ULONG),
        ("Value", ctypes.c_uint64),
        ("Address", ctypes.c_uint64),
        ("Register", wintypes.ULONG),
        ("Scope", wintypes.ULONG),
        ("Tag", wintypes.ULONG),
        ("NameLen", wintypes.ULONG),
        ("MaxNameLen", wintypes.ULONG),
        ("Name", ctypes.c_wchar * MAX_SYM_NAME),
    ]


# sizeof(SYMBOL_INFOW) with Name[1] on x64 is 88 bytes (offsetof(Name) == 84).
SYMBOL_INFOW_BASE_SIZE = 88


class ADDRESS64(ctypes.Structure):
    _fields_ = [
        ("Offset", ctypes.c_uint64),
        ("Segment", ctypes.c_uint16),
        ("Mode", ctypes.c_uint32),
    ]


class KDHELP64(ctypes.Structure):
    _fields_ = [
        ("Thread", ctypes.c_uint64),
        ("ThCallbackStack", wintypes.DWORD),
        ("ThCallbackBStore", wintypes.DWORD),
        ("NextCallback", wintypes.DWORD),
        ("FramePointer", wintypes.DWORD),
        ("KiCallUserMode", ctypes.c_uint64),
        ("KeUserCallbackDispatcher", ctypes.c_uint64),
        ("SystemRangeStart", ctypes.c_uint64),
        ("KiUserExceptionDispatcher", ctypes.c_uint64),
        ("StackBase", ctypes.c_uint64),
        ("StackLimit", ctypes.c_uint64),
        ("BuildVersion", wintypes.DWORD),
        ("RetpolineStubFunctionTableSize", wintypes.DWORD),
        ("RetpolineStubFunctionTable", ctypes.c_uint64),
        ("RetpolineStubOffset", wintypes.DWORD),
        ("RetpolineStubSize", wintypes.DWORD),
        ("Reserved0", ctypes.c_uint64 * 2),
    ]


class STACKFRAME64(ctypes.Structure):
    _fields_ = [
        ("AddrPC", ADDRESS64),
        ("AddrReturn", ADDRESS64),
        ("AddrFrame", ADDRESS64),
        ("AddrStack", ADDRESS64),
        ("AddrBStore", ADDRESS64),
        ("FuncTableEntry", ctypes.c_void_p),
        ("Params", ctypes.c_uint64 * 4),
        ("Far", wintypes.BOOL),
        ("Virtual", wintypes.BOOL),
        ("Reserved", ctypes.c_uint64 * 3),
        ("KdHelp", KDHELP64),
    ]


# ---------------------------------------------------------------------------
# DLL Bindings
# ---------------------------------------------------------------------------

kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
psapi = ctypes.WinDLL("psapi", use_last_error=True)
dbghelp = ctypes.WinDLL("dbghelp", use_last_error=True)
winmm = ctypes.WinDLL("winmm", use_last_error=False)

# kernel32
kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
kernel32.CreateToolhelp32Snapshot.restype = ctypes.c_void_p

kernel32.Process32FirstW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32FirstW.restype = wintypes.BOOL

kernel32.Process32NextW.argtypes = [ctypes.c_void_p, ctypes.POINTER(PROCESSENTRY32W)]
kernel32.Process32NextW.restype = wintypes.BOOL

kernel32.Thread32First.argtypes = [ctypes.c_void_p, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32First.restype = wintypes.BOOL

kernel32.Thread32Next.argtypes = [ctypes.c_void_p, ctypes.POINTER(THREADENTRY32)]
kernel32.Thread32Next.restype = wintypes.BOOL

kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = ctypes.c_void_p

kernel32.OpenThread.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenThread.restype = ctypes.c_void_p

kernel32.SuspendThread.argtypes = [ctypes.c_void_p]
kernel32.SuspendThread.restype = wintypes.DWORD

kernel32.ResumeThread.argtypes = [ctypes.c_void_p]
kernel32.ResumeThread.restype = wintypes.DWORD

kernel32.GetThreadContext.argtypes = [ctypes.c_void_p, ctypes.c_void_p]
kernel32.GetThreadContext.restype = wintypes.BOOL

kernel32.GetThreadDescription.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_wchar_p)]
kernel32.GetThreadDescription.restype = ctypes.c_long

kernel32.GetThreadTimes.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
    ctypes.POINTER(wintypes.FILETIME),
]
kernel32.GetThreadTimes.restype = wintypes.BOOL

kernel32.LocalFree.argtypes = [ctypes.c_void_p]
kernel32.LocalFree.restype = ctypes.c_void_p

kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
kernel32.CloseHandle.restype = wintypes.BOOL

# psapi
psapi.EnumProcessModules.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(ctypes.c_void_p),
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
]
psapi.EnumProcessModules.restype = wintypes.BOOL

psapi.GetModuleInformation.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(MODULEINFO),
    wintypes.DWORD,
]
psapi.GetModuleInformation.restype = wintypes.BOOL

psapi.GetModuleBaseNameW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    wintypes.DWORD,
]
psapi.GetModuleBaseNameW.restype = wintypes.DWORD

psapi.GetModuleFileNameExW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    wintypes.DWORD,
]
psapi.GetModuleFileNameExW.restype = wintypes.DWORD

psapi.GetProcessMemoryInfo.argtypes = [
    ctypes.c_void_p,
    ctypes.POINTER(PROCESS_MEMORY_COUNTERS),
    wintypes.DWORD,
]
psapi.GetProcessMemoryInfo.restype = wintypes.BOOL

# dbghelp
dbghelp.SymGetOptions.argtypes = []
dbghelp.SymGetOptions.restype = wintypes.DWORD

dbghelp.SymSetOptions.argtypes = [wintypes.DWORD]
dbghelp.SymSetOptions.restype = wintypes.DWORD

dbghelp.SymInitializeW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, wintypes.BOOL]
dbghelp.SymInitializeW.restype = wintypes.BOOL

dbghelp.SymSetSearchPathW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
dbghelp.SymSetSearchPathW.restype = wintypes.BOOL

dbghelp.SymLoadModuleExW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    ctypes.c_uint64,
    wintypes.DWORD,
    ctypes.c_void_p,
    wintypes.DWORD,
]
dbghelp.SymLoadModuleExW.restype = ctypes.c_uint64

dbghelp.SymFromAddrW.argtypes = [
    ctypes.c_void_p,
    ctypes.c_uint64,
    ctypes.POINTER(ctypes.c_uint64),
    ctypes.POINTER(SYMBOL_INFOW),
]
dbghelp.SymFromAddrW.restype = wintypes.BOOL

dbghelp.SymCleanup.argtypes = [ctypes.c_void_p]
dbghelp.SymCleanup.restype = wintypes.BOOL

dbghelp.StackWalk64.argtypes = [
    wintypes.DWORD,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.POINTER(STACKFRAME64),
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
    ctypes.c_void_p,
]
dbghelp.StackWalk64.restype = wintypes.BOOL

# winmm
winmm.timeBeginPeriod.argtypes = [wintypes.UINT]
winmm.timeBeginPeriod.restype = wintypes.UINT

winmm.timeEndPeriod.argtypes = [wintypes.UINT]
winmm.timeEndPeriod.restype = wintypes.UINT


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def find_process_by_name(exe_name: str) -> int:
    """Return PID of the first process matching exe_name (case-insensitive)."""
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == INVALID_HANDLE_VALUE or not snap:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        pe = PROCESSENTRY32W()
        pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        if not kernel32.Process32FirstW(snap, ctypes.byref(pe)):
            raise ctypes.WinError(ctypes.get_last_error())
        target = exe_name.lower()
        while True:
            if pe.szExeFile.lower() == target:
                return int(pe.th32ProcessID)
            if not kernel32.Process32NextW(snap, ctypes.byref(pe)):
                break
    finally:
        kernel32.CloseHandle(snap)
    raise RuntimeError(f"Process '{exe_name}' not found")


def get_process_stats(h_proc: int, pid: int) -> tuple[int, int]:
    """Return (working_set_bytes, thread_count) for pid."""
    ws_bytes = 0
    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    if psapi.GetProcessMemoryInfo(h_proc, ctypes.byref(pmc), pmc.cb):
        ws_bytes = int(pmc.WorkingSetSize)

    thr_count = 0
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap and snap != INVALID_HANDLE_VALUE:
        try:
            pe = PROCESSENTRY32W()
            pe.dwSize = ctypes.sizeof(PROCESSENTRY32W)
            if kernel32.Process32FirstW(snap, ctypes.byref(pe)):
                while True:
                    if pe.th32ProcessID == pid:
                        thr_count = int(pe.cntThreads)
                        break
                    if not kernel32.Process32NextW(snap, ctypes.byref(pe)):
                        break
        finally:
            kernel32.CloseHandle(snap)
    return ws_bytes, thr_count


def get_cpu_model_name() -> str:
    """Read CPU ProcessorNameString from Windows registry."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"HARDWARE\DESCRIPTION\System\CentralProcessor\0",
        ) as key:
            val, _ = winreg.QueryValueEx(key, "ProcessorNameString")
            return str(val).strip()
    except OSError:
        return "<unknown>"


def get_active_power_scheme() -> str:
    """Return `powercfg /getactivescheme` output."""
    try:
        out = subprocess.check_output(
            ["powercfg", "/getactivescheme"],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=5,
        )
        return " ".join(out.strip().split())
    except Exception as exc:
        return f"<error: {exc}>"


def get_thread_description(h_thread: int) -> str:
    """Return the Win32 thread description string, or empty string on failure."""
    desc_ptr = ctypes.c_wchar_p()
    hr = kernel32.GetThreadDescription(h_thread, ctypes.byref(desc_ptr))
    if hr < 0 or not desc_ptr.value:
        if desc_ptr:
            kernel32.LocalFree(desc_ptr)
        return ""
    try:
        return desc_ptr.value
    finally:
        kernel32.LocalFree(desc_ptr)


def get_thread_cpu_time_100ns(h_thread: int) -> int:
    """Return cumulative kernel + user CPU time for h_thread in 100-ns units."""
    creation = wintypes.FILETIME()
    exit_t = wintypes.FILETIME()
    kernel = wintypes.FILETIME()
    user = wintypes.FILETIME()
    if not kernel32.GetThreadTimes(
        h_thread,
        ctypes.byref(creation),
        ctypes.byref(exit_t),
        ctypes.byref(kernel),
        ctypes.byref(user),
    ):
        return 0
    k_val = (kernel.dwHighDateTime << 32) | kernel.dwLowDateTime
    u_val = (user.dwHighDateTime << 32) | user.dwLowDateTime
    return k_val + u_val


def find_target_threads(pid: int, target_names: list[str]) -> list[tuple[str, int, int]]:
    """Return list of (thread_name, tid, h_thread) matching target_names."""
    wanted = set(target_names)
    include_unnamed = "unnamed" in wanted
    snap = kernel32.CreateToolhelp32Snapshot(TH32CS_SNAPTHREAD, 0)
    if snap == INVALID_HANDLE_VALUE or not snap:
        raise ctypes.WinError(ctypes.get_last_error())
    matched: list[tuple[str, int, int]] = []
    access = THREAD_SUSPEND_RESUME | THREAD_GET_CONTEXT | THREAD_QUERY_INFORMATION
    try:
        te = THREADENTRY32()
        te.dwSize = ctypes.sizeof(THREADENTRY32)
        if not kernel32.Thread32First(snap, ctypes.byref(te)):
            raise ctypes.WinError(ctypes.get_last_error())
        while True:
            if te.th32OwnerProcessID == pid:
                tid = int(te.th32ThreadID)
                h_thread = kernel32.OpenThread(access, False, tid)
                if h_thread:
                    desc = get_thread_description(h_thread)
                    if desc in wanted:
                        matched.append((desc, tid, h_thread))
                    elif include_unnamed and desc == "":
                        matched.append((f"<unnamed tid {tid}>", tid, h_thread))
                    else:
                        kernel32.CloseHandle(h_thread)
            if not kernel32.Thread32Next(snap, ctypes.byref(te)):
                break
    finally:
        kernel32.CloseHandle(snap)
    return matched


def enumerate_modules(h_proc: int) -> list[tuple[int, int, str, str]]:
    """Return list of (base_addr, size, base_name, full_path) for loaded modules."""
    needed = wintypes.DWORD(0)
    arr_len = 256
    while True:
        mods = (ctypes.c_void_p * arr_len)()
        if not psapi.EnumProcessModules(
            h_proc, mods, ctypes.sizeof(mods), ctypes.byref(needed)
        ):
            raise ctypes.WinError(ctypes.get_last_error())
        count = needed.value // ctypes.sizeof(ctypes.c_void_p)
        if count <= arr_len:
            break
        arr_len = count + 64

    result: list[tuple[int, int, str, str]] = []
    name_buf = ctypes.create_unicode_buffer(512)
    path_buf = ctypes.create_unicode_buffer(1024)
    mi = MODULEINFO()
    for i in range(count):
        h_mod = mods[i]
        if not h_mod:
            continue
        if not psapi.GetModuleInformation(
            h_proc, h_mod, ctypes.byref(mi), ctypes.sizeof(mi)
        ):
            continue
        psapi.GetModuleBaseNameW(h_proc, h_mod, name_buf, len(name_buf))
        psapi.GetModuleFileNameExW(h_proc, h_mod, path_buf, len(path_buf))
        base_addr = int(mi.lpBaseOfDll or 0)
        result.append((base_addr, int(mi.SizeOfImage), name_buf.value, path_buf.value))
    return result


def alloc_aligned_context() -> tuple[ctypes.Array, int]:
    """Allocate a 16-byte aligned AMD64 CONTEXT buffer and return (raw_buf, addr)."""
    raw = (ctypes.c_ubyte * (CONTEXT_SIZE + 16))()
    addr = (ctypes.addressof(raw) + 15) & ~15
    return raw, addr


def read_u64(addr: int, offset: int) -> int:
    return ctypes.c_uint64.from_address(addr + offset).value


def write_u32(addr: int, offset: int, val: int) -> None:
    ctypes.c_uint32.from_address(addr + offset).value = val


def init_dbghelp(h_proc: int, exe_path: str, exe_base: int, exe_size: int, pdb_path: str | None) -> None:
    """Initialize DbgHelp with SYMOPT_UNDNAME on and SYMOPT_DEFERRED_LOADS off."""
    opts = dbghelp.SymGetOptions()
    opts = (opts | SYMOPT_UNDNAME) & ~SYMOPT_DEFERRED_LOADS
    dbghelp.SymSetOptions(opts)

    if not dbghelp.SymInitializeW(h_proc, None, False):
        raise ctypes.WinError(ctypes.get_last_error())

    search_dirs: list[str] = []
    if pdb_path:
        pdb_dir = os.path.dirname(os.path.abspath(pdb_path))
        if pdb_dir:
            search_dirs.append(pdb_dir)
    exe_dir = os.path.dirname(os.path.abspath(exe_path))
    if exe_dir and exe_dir not in search_dirs:
        search_dirs.append(exe_dir)
    if search_dirs:
        dbghelp.SymSetSearchPathW(h_proc, ";".join(search_dirs))

    loaded = dbghelp.SymLoadModuleExW(
        h_proc, None, exe_path, None, exe_base, exe_size, None, 0
    )
    if not loaded:
        err = ctypes.get_last_error()
        if err != 0:
            raise ctypes.WinError(err)


STACK_DEPTH = 16

WAIT_LEAF_DLLS = ("<ntdll.dll>", "<kernelbase.dll>", "<win32u.dll>")
WAIT_CALLER_LEAF_DLLS = ("<ntdll.dll>", "<kernelbase.dll>", "<win32u.dll>", "<nvoglv64.dll>")


def walk_stack(
    h_proc: int,
    h_thread: int,
    ctx_addr: int,
    fn_table_access: int,
    get_mod_base: int,
    max_depth: int = STACK_DEPTH,
) -> list[int]:
    """Capture up to max_depth PC addresses via StackWalk64 on an already-suspended thread."""
    frame = STACKFRAME64()
    frame.AddrPC.Offset = read_u64(ctx_addr, CONTEXT_OFF_RIP)
    frame.AddrPC.Mode = ADDR_MODE_FLAT
    frame.AddrFrame.Offset = read_u64(ctx_addr, CONTEXT_OFF_RBP)
    frame.AddrFrame.Mode = ADDR_MODE_FLAT
    frame.AddrStack.Offset = read_u64(ctx_addr, CONTEXT_OFF_RSP)
    frame.AddrStack.Mode = ADDR_MODE_FLAT

    pcs: list[int] = []
    for _ in range(max_depth):
        ok = dbghelp.StackWalk64(
            IMAGE_FILE_MACHINE_AMD64,
            h_proc,
            h_thread,
            ctypes.byref(frame),
            ctx_addr,
            None,
            fn_table_access,
            get_mod_base,
            None,
        )
        if not ok or frame.AddrPC.Offset == 0:
            break
        pcs.append(int(frame.AddrPC.Offset))
    return pcs


class SymbolResolver:
    """Cached RIP -> symbol/external-module resolver."""

    def __init__(
        self,
        h_proc: int,
        exe_base: int,
        exe_size: int,
        modules: list[tuple[int, int, str, str]],
    ) -> None:
        self.h_proc = h_proc
        self.exe_base = exe_base
        self.exe_end = exe_base + exe_size
        self.modules = modules
        self.cache: dict[int, str] = {}
        self._sym = SYMBOL_INFOW()
        self._sym.SizeOfStruct = SYMBOL_INFOW_BASE_SIZE
        self._sym.MaxNameLen = MAX_SYM_NAME
        self._disp = ctypes.c_uint64(0)

    def resolve(self, rip: int) -> str:
        cached = self.cache.get(rip)
        if cached is not None:
            return cached

        if self.exe_base <= rip < self.exe_end:
            if dbghelp.SymFromAddrW(
                self.h_proc, rip, ctypes.byref(self._disp), ctypes.byref(self._sym)
            ):
                name = self._sym.Name or f"0x{rip:016X}"
            else:
                name = f"0x{rip:016X}"
        else:
            mod_name = None
            for base, size, bname, _ in self.modules:
                if base <= rip < base + size:
                    mod_name = bname
                    break
            name = f"<{mod_name}>" if mod_name else "<unknown>"

        self.cache[rip] = name
        return name


# ---------------------------------------------------------------------------
# Sampling & Reporting
# ---------------------------------------------------------------------------

THREAD_ALIASES = [
    ("GameThread", "GT"),
    ("GsWorker", "GS"),
    ("Vu1Exec", "V1"),
    ("Vif1Worker", "VF"),
    ("MainLoop", "ML"),
]


def is_idle_symbol(sym: str) -> bool:
    """Treat <ntdll.dll>, <KERNELBASE.dll>, and wait/sleep frames as idle."""
    s = sym.lower()
    if s in ("<ntdll.dll>", "<kernelbase.dll>"):
        return True
    if not s.startswith("sub_") and (
        "wait" in s or "sleep" in s or "delayexecution" in s
    ):
        return True
    return False


def sample_threads(
    h_proc: int,
    threads: list[tuple[str, int, int]],
    seconds: float,
    interval_us: float,
    capture_stacks: bool,
    show_progress: bool = True,
) -> dict[tuple[str, int], tuple[list[int], list[list[int]], list[float]]]:
    """Sample all target threads for `seconds` at `interval_us` intervals."""
    samples: dict[tuple[str, int], tuple[list[int], list[list[int]], list[float]]] = {
        (name, tid): ([], [], []) for name, tid, _ in threads
    }

    _, ctx_addr = alloc_aligned_context()
    fn_table_access = ctypes.cast(dbghelp.SymFunctionTableAccess64, ctypes.c_void_p).value
    get_mod_base = ctypes.cast(dbghelp.SymGetModuleBase64, ctypes.c_void_p).value

    interval_s = max(interval_us / 1_000_000.0, 0.00001)
    winmm.timeBeginPeriod(1)
    try:
        t_start = time.perf_counter()
        t_end = t_start + seconds
        next_t = t_start
        last_progress_t = -1.0

        while True:
            now = time.perf_counter()
            if now >= t_end:
                break

            if show_progress and (last_progress_t < 0.0 or now - last_progress_t >= 0.25):
                last_progress_t = now
                rem_s = max(0.0, t_end - now)
                sys.stdout.write(f"\r  {rem_s:5.1f} s left...   ")
                sys.stdout.flush()

            t_rel = now - t_start
            for name, tid, h_thread in threads:
                prev_susp = kernel32.SuspendThread(h_thread)
                if prev_susp == 0xFFFFFFFF:
                    continue
                rip = 0
                stack_pcs: list[int] = []
                try:
                    write_u32(ctx_addr, CONTEXT_OFF_FLAGS, CONTEXT_FLAGS_TARGET)
                    if kernel32.GetThreadContext(h_thread, ctx_addr):
                        rip = read_u64(ctx_addr, CONTEXT_OFF_RIP)
                        if capture_stacks:
                            stack_pcs = walk_stack(
                                h_proc,
                                h_thread,
                                ctx_addr,
                                fn_table_access,
                                get_mod_base,
                                STACK_DEPTH,
                            )
                finally:
                    kernel32.ResumeThread(h_thread)

                if rip:
                    rips, stacks, t_rels = samples[(name, tid)]
                    rips.append(rip)
                    t_rels.append(t_rel)
                    if capture_stacks:
                        stacks.append(stack_pcs)

            next_t += interval_s
            now = time.perf_counter()
            if next_t <= now:
                next_t = now
                continue
            rem = next_t - now
            if rem > 0.0015:
                time.sleep(rem - 0.001)
            while time.perf_counter() < next_t:
                pass
    finally:
        winmm.timeEndPeriod(1)
        if show_progress:
            sys.stdout.write("\r" + " " * 32 + "\r")
            sys.stdout.flush()

    return samples


def compute_busy_and_timeline(
    samples: dict[tuple[str, int], tuple[list[int], list[list[int]], list[float]]],
    resolver: SymbolResolver,
    seconds: float,
    seg_epoch_ms_start: int,
) -> tuple[dict[str, float], list[str]]:
    """Compute per-thread busy % and per-second timeline lines."""
    num_secs = max(1, int(math.ceil(seconds)))
    per_thr_total: dict[str, int] = collections.defaultdict(int)
    per_thr_busy: dict[str, int] = collections.defaultdict(int)
    per_sec_syms: dict[tuple[str, int], list[str]] = collections.defaultdict(list)

    for (tname, _tid), (rips, _stacks, t_rels) in samples.items():
        for rip, t_rel in zip(rips, t_rels):
            sym = resolver.resolve(rip)
            sec = min(num_secs - 1, max(0, int(t_rel)))
            per_thr_total[tname] += 1
            if not is_idle_symbol(sym):
                per_thr_busy[tname] += 1
            per_sec_syms[(tname, sec)].append(sym)

    busy_pcts: dict[str, float] = {}
    for tname, tot in per_thr_total.items():
        busy_pcts[tname] = (100.0 * per_thr_busy[tname] / tot) if tot > 0 else 0.0

    timeline_lines: list[str] = ["[Per-Second Timeline]"]
    for sec in range(num_secs):
        epoch_ms = seg_epoch_ms_start + sec * 1000
        parts: list[str] = []
        for full_name, abbr in THREAD_ALIASES:
            syms = per_sec_syms.get((full_name, sec), [])
            if syms:
                busy = 100.0 * sum(1 for s in syms if not is_idle_symbol(s)) / len(syms)
                parts.append(f"{abbr}={busy:.1f}%")
            else:
                parts.append(f"{abbr}=0.0%")

        def top_for(tname: str) -> str:
            syms = per_sec_syms.get((tname, sec), [])
            if not syms:
                return "none 0.0%"
            fn, cnt = collections.Counter(syms).most_common(1)[0]
            return f"{fn} {100.0 * cnt / len(syms):.1f}%"

        timeline_lines.append(
            f"t={sec} epoch_ms={epoch_ms} {' '.join(parts)} | "
            f"GT top: {top_for('GameThread')} | GS top: {top_for('GsWorker')}"
        )

    return busy_pcts, timeline_lines


def is_unnamed_thread(tname: str) -> bool:
    return tname.startswith("<unnamed tid ")


def format_report(
    samples: dict[tuple[str, int], tuple[list[int], list[list[int]], list[float]]],
    resolver: SymbolResolver,
    top_n: int,
    capture_stacks: bool,
    cpu_ms_by_thread: dict[tuple[str, int], float],
    seg_wall_ms: float,
) -> str:
    """Format per-thread self, guest-address, and optional inclusive tables."""
    lines: list[str] = []

    named_items = [
        (key, val) for key, val in samples.items() if not is_unnamed_thread(key[0])
    ]
    min_unnamed_cpu_ms = 0.02 * seg_wall_ms
    unnamed_items = sorted(
        (
            (key, val)
            for key, val in samples.items()
            if is_unnamed_thread(key[0])
            and cpu_ms_by_thread.get(key, 0.0) >= min_unnamed_cpu_ms
        ),
        key=lambda kv: cpu_ms_by_thread.get(kv[0], 0.0),
        reverse=True,
    )

    for (tname, tid), (rips, stacks, _t_rels) in named_items + unnamed_items:
        total = len(rips)
        cpu_ms = cpu_ms_by_thread.get((tname, tid), 0.0)
        lines.append(
            f"=== Thread: {tname} (TID {tid}) | total samples: {total} | cpu_ms: {cpu_ms:.2f} ==="
        )
        if total == 0:
            lines.append("  (no samples collected)\n")
            continue

        self_counts: collections.Counter[str] = collections.Counter()
        guest_counts: collections.Counter[str] = collections.Counter()
        sub_samples = 0

        for rip in rips:
            sym = resolver.resolve(rip)
            self_counts[sym] += 1
            if sym.startswith("sub_"):
                sub_samples += 1
                m = GUEST_SUB_RE.match(sym)
                if m:
                    guest_addr = f"0x{m.group(1).upper()}"
                    guest_counts[guest_addr] += 1

        sub_pct = 100.0 * sub_samples / total
        other_pct = 100.0 - sub_pct
        lines.append(
            f"  Recompiled guest (sub_*): {sub_samples}/{total} ({sub_pct:.2f}%) | "
            f"Other (runtime/ext): {total - sub_samples}/{total} ({other_pct:.2f}%)"
        )

        lines.append(f"\n  [Self Time - Top {top_n}]")
        lines.append(f"  {'Pct':>7}  {'Samples':>8}  Function")
        for sym, cnt in self_counts.most_common(top_n):
            lines.append(f"  {100.0 * cnt / total:6.2f}%  {cnt:8d}  {sym}")

        lines.append(f"\n  [By Guest Address - Top {top_n}]")
        lines.append(f"  {'Pct':>7}  {'Samples':>8}  GuestAddr")
        if guest_counts:
            for gaddr, cnt in guest_counts.most_common(top_n):
                lines.append(f"  {100.0 * cnt / total:6.2f}%  {cnt:8d}  {gaddr}")
        else:
            lines.append("  (no sub_* guest functions sampled)")

        if capture_stacks:
            inc_counts: collections.Counter[str] = collections.Counter()
            path_counts: collections.Counter[tuple[str, ...]] = collections.Counter()
            wait_callers: collections.Counter[str] = collections.Counter()

            for pcs in stacks:
                if not pcs:
                    continue
                syms = [resolver.resolve(pc) for pc in pcs]

                for sym in set(syms):
                    inc_counts[sym] += 1

                # Merge consecutive duplicate frames for call-path signature.
                dedup: list[str] = []
                for sym in syms:
                    if not dedup or dedup[-1] != sym:
                        dedup.append(sym)

                # Collapse leading <ntdll.dll>/<KERNELBASE.dll>/<win32u.dll> frames into 'WAIT'.
                idx = 0
                while idx < len(dedup) and dedup[idx].lower() in WAIT_LEAF_DLLS:
                    idx += 1
                if idx > 0:
                    sig = ("WAIT", *dedup[idx:])
                else:
                    sig = tuple(dedup)
                path_counts[sig] += 1

                # For wait/driver-wait leaves, find first resolved runtime frame.
                if syms[0].lower() in WAIT_CALLER_LEAF_DLLS:
                    caller = "<unresolved>"
                    for sym in syms:
                        if not sym.startswith("<") and not sym.startswith("0x"):
                            caller = sym
                            break
                    wait_callers[caller] += 1

            lines.append(f"\n  [Inclusive Time (StackWalk64 depth {STACK_DEPTH}) - Top {top_n}]")
            lines.append(f"  {'Pct':>7}  {'Samples':>8}  Function")
            for sym, cnt in inc_counts.most_common(top_n):
                lines.append(f"  {100.0 * cnt / total:6.2f}%  {cnt:8d}  {sym}")

            lines.append("\n  [Top Call Paths - leaf first]")
            lines.append(f"  {'Pct':>7}  {'Samples':>8}  Path")
            for sig, cnt in path_counts.most_common(15):
                path_str = " <- ".join(sig[:10])
                lines.append(f"  {100.0 * cnt / total:6.2f}%  {cnt:8d}  {path_str}")

            lines.append("\n  [Wait Callers]")
            lines.append(f"  {'Pct':>7}  {'Samples':>8}  Caller")
            if wait_callers:
                for sym, cnt in wait_callers.most_common(top_n):
                    lines.append(f"  {100.0 * cnt / total:6.2f}%  {cnt:8d}  {sym}")
            else:
                lines.append("  (no wait samples)")

        lines.append("")

    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="External host-RIP sampling profiler for Windows x64 executables."
    )
    parser.add_argument(
        "--exe-name",
        default="ps2EntryRunner_dev.exe",
        help="Target process image name (default: ps2EntryRunner_dev.exe)",
    )
    parser.add_argument(
        "--pdb",
        default=None,
        help="Path to PDB file (its directory is added to DbgHelp search path)",
    )
    parser.add_argument(
        "--thread",
        default="GameThread",
        help="Target thread description, 'unnamed' for threads without a description, or comma-separated list (default: GameThread)",
    )
    parser.add_argument(
        "--seconds",
        type=float,
        default=20.0,
        help="Sampling duration in seconds (default: 20)",
    )
    parser.add_argument(
        "--interval-us",
        type=float,
        default=500.0,
        help="Sampling interval in microseconds (default: 500)",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=40,
        help="Number of top entries to display per table (default: 40)",
    )
    parser.add_argument(
        "--out",
        default=None,
        help="Optional output file path to append the report",
    )
    parser.add_argument(
        "--segments",
        type=int,
        default=1,
        help="Number of sampling segments to run (default: 1)",
    )
    parser.add_argument(
        "--labels",
        default=None,
        help="Comma-separated segment labels (default: seg1,seg2,...)",
    )
    parser.add_argument(
        "--gap",
        type=float,
        default=20.0,
        help="Gap seconds between segments with countdown and beep (default: 20)",
    )
    parser.add_argument(
        "--stacks",
        action="store_true",
        help="Capture up to 16 stack frames via StackWalk64 and report inclusive time, top call paths, and wait callers",
    )
    args = parser.parse_args()

    if args.segments < 1:
        print("Error: --segments must be >= 1.", file=sys.stderr)
        return 1

    target_threads = [t.strip() for t in args.thread.split(",") if t.strip()]
    if not target_threads:
        print("Error: --thread must specify at least one thread name.", file=sys.stderr)
        return 1

    raw_labels = [s.strip() for s in args.labels.split(",") if s.strip()] if args.labels else []
    labels = [
        raw_labels[i] if i < len(raw_labels) else f"seg{i + 1}"
        for i in range(args.segments)
    ]

    pid = find_process_by_name(args.exe_name)
    h_proc = kernel32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h_proc:
        raise ctypes.WinError(ctypes.get_last_error())

    threads: list[tuple[str, int, int]] = []
    sym_inited = False
    try:
        threads = find_target_threads(pid, target_threads)
        if not threads:
            raise RuntimeError(
                f"No threads found in PID {pid} matching: {', '.join(target_threads)}"
            )

        modules = enumerate_modules(h_proc)
        exe_mod = next(
            (m for m in modules if m[2].lower() == args.exe_name.lower()), None
        )
        if exe_mod is None:
            raise RuntimeError(f"Module '{args.exe_name}' not found in PID {pid}")
        exe_base, exe_size, _, exe_path = exe_mod

        init_dbghelp(h_proc, exe_path, exe_base, exe_size, args.pdb)
        sym_inited = True
        resolver = SymbolResolver(h_proc, exe_base, exe_size, modules)

        out_file = None
        if args.out:
            out_dir = os.path.dirname(os.path.abspath(args.out))
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
            out_file = open(args.out, "a", encoding="utf-8")
            run_iso = datetime.datetime.now().astimezone().isoformat()
            cpu_model = get_cpu_model_name()
            power_scheme = get_active_power_scheme()
            out_file.write(
                "\n" + "=" * 80 + "\n"
                f"HOSTPROF RUN | start={run_iso} | cpu={cpu_model}\n"
                f"power_scheme={power_scheme}\n"
                + "=" * 80 + "\n"
            )
            out_file.flush()

        summary_rows: list[tuple[str, dict[str, float]]] = []
        try:
            for seg_idx in range(args.segments):
                k = seg_idx + 1
                label = labels[seg_idx]
                print(f"[seg {k}/{args.segments} {label}] sampling {args.seconds:g} s ...")

                seg_iso = datetime.datetime.now().astimezone().isoformat()
                seg_epoch_ms = int(time.time() * 1000)
                ws_start, thr_start = get_process_stats(h_proc, pid)
                cpu_start = {
                    (tname, tid): get_thread_cpu_time_100ns(h_thread)
                    for tname, tid, h_thread in threads
                }
                seg_wall_start = time.perf_counter()

                samples = sample_threads(
                    h_proc,
                    threads,
                    args.seconds,
                    args.interval_us,
                    args.stacks,
                    show_progress=True,
                )

                seg_wall_ms = max((time.perf_counter() - seg_wall_start) * 1000.0, 1e-6)
                cpu_end = {
                    (tname, tid): get_thread_cpu_time_100ns(h_thread)
                    for tname, tid, h_thread in threads
                }
                cpu_ms_by_thread = {
                    key: max(0, cpu_end[key] - cpu_start[key]) / 10_000.0
                    for key in cpu_start
                }
                ws_end, thr_end = get_process_stats(h_proc, pid)
                total_samples = sum(len(rips) for rips, _, _ in samples.values())

                busy_pcts, timeline_lines = compute_busy_and_timeline(
                    samples, resolver, args.seconds, seg_epoch_ms
                )
                summary_rows.append((label, busy_pcts))
                report = format_report(
                    samples,
                    resolver,
                    args.top,
                    args.stacks,
                    cpu_ms_by_thread,
                    seg_wall_ms,
                )

                if out_file is not None:
                    cpu_header_parts = [
                        f"{tname}(tid={tid})={cpu_ms:.2f}ms"
                        for (tname, tid), cpu_ms in sorted(
                            cpu_ms_by_thread.items(), key=lambda kv: kv[1], reverse=True
                        )
                    ]
                    out_file.write(
                        "\n" + "-" * 80 + "\n"
                        f"SEGMENT {k}/{args.segments} | label={label} | start_iso={seg_iso} | "
                        f"start_epoch_ms={seg_epoch_ms} | wall_ms={seg_wall_ms:.2f} | "
                        f"interval_us={args.interval_us:g} | threads={','.join(target_threads)}\n"
                        f"proc_start: working_set_mb={ws_start / (1024.0 * 1024.0):.2f} threads={thr_start}\n"
                        f"proc_end:   working_set_mb={ws_end / (1024.0 * 1024.0):.2f} threads={thr_end}\n"
                        f"thread_cpu_ms: {', '.join(cpu_header_parts)}\n"
                        + "-" * 80 + "\n"
                    )
                    out_file.write("\n".join(timeline_lines) + "\n\n")
                    out_file.write(report + "\n")
                    out_file.flush()
                    print(f"[seg {k}/{args.segments} {label}] done, {total_samples} samples -> appended to {args.out}")
                else:
                    print(f"[seg {k}/{args.segments} {label}] done, {total_samples} samples")

                if k < args.segments and args.gap > 0:
                    end_gap = time.perf_counter() + args.gap
                    while True:
                        left = end_gap - time.perf_counter()
                        if left <= 0:
                            break
                        sys.stdout.write(
                            f"\rswitch level now, next segment in {int(math.ceil(left))} s   "
                        )
                        sys.stdout.flush()
                        time.sleep(min(0.5, left))
                    sys.stdout.write("\rswitch level now, next segment in 0 s   \n")
                    sys.stdout.flush()
                    try:
                        winsound.Beep(880, 250)
                    except Exception:
                        sys.stdout.write("\a")
                        sys.stdout.flush()
        finally:
            if out_file is not None:
                out_file.close()

        summary_cols = [full for full, _ in THREAD_ALIASES]
        print("\nSummary (Busy %):")
        print(
            f"{'Segment':<14} "
            + " ".join(f"{col:>10}" for col in summary_cols)
        )
        for label, bp in summary_rows:
            vals = " ".join(f"{bp.get(col, 0.0):9.1f}%" for col in summary_cols)
            print(f"{label:<14} {vals}")
    finally:
        for _, _, h_thread in threads:
            kernel32.CloseHandle(h_thread)
        if sym_inited:
            dbghelp.SymCleanup(h_proc)
        kernel32.CloseHandle(h_proc)

    return 0


if __name__ == "__main__":
    sys.exit(main())
