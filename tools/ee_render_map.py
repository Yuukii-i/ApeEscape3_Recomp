#!/usr/bin/env python3
"""Static map of the EE graphics engine from recompiled guest C++ files."""

from __future__ import annotations

import os
import re
import sys
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path

VU1CMD_IMMS = frozenset({
    0x0A, 0x0E, 0x11, 0x15, 0x33, 0x39, 0x5C, 0x6D, 0xC8, 0x108,
    0x15C, 0x167, 0x17B, 0x187, 0x190, 0x198, 0x212, 0x2BC, 0x2E4, 0x320,
    0x322, 0x343, 0x389, 0x398, 0x39B, 0x3CA, 0x3DC, 0x3DE, 0x62C, 0x654,
})

VIF_TOP_BYTES = (
    set(range(0x01, 0x08))
    | {0x10, 0x11, 0x13, 0x14, 0x15, 0x17, 0x50, 0x51}
    | set(range(0x60, 0x80))
)

VU0_MNEMONICS = frozenset({"qmfc2", "qmtc2", "vcallms", "ctc2", "cfc2"})

FILE_ADDR_RE = re.compile(r"^(.+)_0x([0-9a-fA-F]+)\.cpp$")
INSN_LINE_RE = re.compile(
    r"^\s*//\s*0x([0-9a-fA-F]+):\s*0x[0-9a-fA-F]+\s+(\S+)(?:\s+(.*))?$"
)
DELAY_SLOT_RE = re.compile(r"\s*\(Delay Slot\)\s*$")
IMM_ZERO_RE = re.compile(r"^\$\w+,\s*\$zero,\s*(0x[0-9a-fA-F]+|\d+)$")
LUI_RE = re.compile(r"^\$\w+,\s*(0x[0-9a-fA-F]+|\d+)$")
JAL_TARGET_RE = re.compile(r"(?:func_|sub_|0x)([0-9a-fA-F]+)")


@dataclass
class FuncInfo:
    name: str
    start_addr: int
    last_addr: int | None = None
    insn_count: int = 0
    callees: list[int] = field(default_factory=list)
    callers: list[int] = field(default_factory=list)
    vu1cmds: list[int] = field(default_factory=list)
    vifs: list[int] = field(default_factory=list)
    has_gif: bool = False
    has_vu0: bool = False
    has_dma: bool = False

    @property
    def has_vif_or_vu1(self) -> bool:
        return bool(self.vu1cmds or self.vifs)

    def format_flags(self) -> str:
        parts: list[str] = []
        if self.vu1cmds:
            imms = ",".join(f"0x{x:02X}" if x < 0x100 else f"0x{x:X}" for x in self.vu1cmds)
            parts.append(f"VU1CMD {imms}")
        if self.vifs:
            vifs = ",".join(f"0x{x:04X}" for x in self.vifs)
            parts.append(f"VIF {vifs}")
        if self.has_gif:
            parts.append("GIF")
        if self.has_vu0:
            parts.append("VU0")
        if self.has_dma:
            parts.append("DMA")
        return "; ".join(parts) if parts else "-"


def parse_function_file(path: Path, start_addr: int) -> FuncInfo:
    stem_name = path.stem.rsplit("_0x", 1)[0]
    info = FuncInfo(name=stem_name, start_addr=start_addr)
    callee_set: set[int] = set()
    vu1_set: set[int] = set()
    vif_set: set[int] = set()

    with path.open("r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = INSN_LINE_RE.match(line)
            if not m:
                continue
            addr = int(m.group(1), 16)
            mnemonic = m.group(2).lower()
            operands = DELAY_SLOT_RE.sub("", m.group(3) or "").strip()

            info.insn_count += 1
            info.last_addr = addr

            if mnemonic == "jal":
                tm = JAL_TARGET_RE.search(operands)
                if tm:
                    target = int(tm.group(1), 16)
                    if target not in callee_set:
                        callee_set.add(target)
                        info.callees.append(target)
            elif mnemonic in ("addiu", "ori"):
                im = IMM_ZERO_RE.match(operands)
                if im:
                    imm = int(im.group(1), 0) & 0xFFFF
                    if imm in VU1CMD_IMMS and imm not in vu1_set:
                        vu1_set.add(imm)
                        info.vu1cmds.append(imm)
            elif mnemonic == "lui":
                lm = LUI_RE.match(operands)
                if lm:
                    uh = int(lm.group(1), 0) & 0xFFFF
                    top_byte = (uh >> 8) & 0xFF
                    if top_byte in VIF_TOP_BYTES and uh not in vif_set:
                        vif_set.add(uh)
                        info.vifs.append(uh)
                    if uh == 0x8000:
                        info.has_gif = True
                    if uh == 0x1000:
                        info.has_dma = True
            elif mnemonic in VU0_MNEMONICS:
                info.has_vu0 = True

    info.vu1cmds.sort()
    info.vifs.sort()
    return info


def fmt_addr_list(addrs: list[int], funcs: dict[int, FuncInfo], limit: int = 12) -> str:
    if not addrs:
        return "-"
    shown = addrs[:limit]
    items = [
        funcs[a].name if a in funcs else f"0x{a:06X}"
        for a in shown
    ]
    text = ", ".join(items)
    if len(addrs) > limit:
        text += f" ... (+{len(addrs) - limit})"
    return text


def caller_chains(
    start: int,
    funcs: dict[int, FuncInfo],
    max_depth: int = 4,
    max_chains: int = 8,
) -> list[str]:
    chains: list[str] = []

    def dfs(curr: int, path: list[int], depth: int) -> None:
        if len(chains) >= max_chains:
            return
        callers = funcs[curr].callers
        if depth >= max_depth or not callers:
            if len(path) > 1:
                # Reverse so root-most caller appears first -> ... -> target
                ordered = list(reversed(path))
                chains.append(" -> ".join(funcs[a].name for a in ordered))
            return
        progressed = False
        for c in callers:
            if c in path:
                continue
            progressed = True
            dfs(c, path + [c], depth + 1)
            if len(chains) >= max_chains:
                return
        if not progressed and len(path) > 1:
            ordered = list(reversed(path))
            chains.append(" -> ".join(funcs[a].name for a in ordered))

    dfs(start, [start], 0)
    return chains


def find_roots(funcs: dict[int, FuncInfo]) -> list[tuple[FuncInfo, list[int]]]:
    # Reverse reachability from all VIF/VU1CMD functions within the scanned set
    targets = [a for a, fn in funcs.items() if fn.has_vif_or_vu1]
    reaches_gfx: dict[int, set[int]] = defaultdict(set)

    for t in targets:
        queue: deque[int] = deque([t])
        visited = {t}
        while queue:
            curr = queue.popleft()
            reaches_gfx[curr].add(t)
            for caller in funcs[curr].callers:
                if caller not in visited:
                    visited.add(caller)
                    queue.append(caller)

    roots: list[tuple[FuncInfo, list[int]]] = []
    for addr in sorted(funcs):
        fn = funcs[addr]
        if not fn.callers and reaches_gfx[addr]:
            roots.append((fn, sorted(reaches_gfx[addr])))
    return roots


def write_report(
    out_path: Path,
    lo: int,
    hi: int,
    funcs: dict[int, FuncInfo],
) -> None:
    lines: list[str] = []
    lines.append(f"# EE Render Map (`0x{lo:06X}` - `0x{hi:06X}`)")
    lines.append("")
    lines.append(f"Scanned **{len(funcs)}** functions in `[0x{lo:06X}, 0x{hi:06X})`.")
    lines.append("")

    # Section 1: Per function
    lines.append("## 1. Functions")
    lines.append("")
    lines.append("| Function | Start | Last | Insns | Callees (max 12) | Callers (in set) | Flags |")
    lines.append("| --- | --- | --- | ---: | --- | --- | --- |")
    for addr in sorted(funcs):
        fn = funcs[addr]
        last_str = f"0x{fn.last_addr:06X}" if fn.last_addr is not None else "-"
        callees_str = fmt_addr_list(fn.callees, funcs, limit=12)
        callers_str = fmt_addr_list(fn.callers, funcs, limit=12)
        flags_str = fn.format_flags()
        lines.append(
            f"| {fn.name} | 0x{fn.start_addr:06X} | {last_str} | {fn.insn_count} "
            f"| {callees_str} | {callers_str} | {flags_str} |"
        )
    lines.append("")

    # Section 2: Summary of VU1CMD / VIF functions with caller chains
    gfx_funcs = [funcs[a] for a in sorted(funcs) if funcs[a].has_vif_or_vu1]
    lines.append("## 2. VU1CMD / VIF Functions and Caller Chains (up to 4 levels)")
    lines.append("")
    lines.append("| Function | Start | Flags | Caller Chains |")
    lines.append("| --- | --- | --- | --- |")
    for fn in gfx_funcs:
        chains = caller_chains(fn.start_addr, funcs, max_depth=4, max_chains=6)
        chains_str = "<br>".join(chains) if chains else "(no callers in set)"
        lines.append(
            f"| {fn.name} | 0x{fn.start_addr:06X} | {fn.format_flags()} | {chains_str} |"
        )
    lines.append("")

    # Section 3: Roots
    roots = find_roots(funcs)
    lines.append("## 3. Roots (No Callers in Set, Reach VIF/VU1CMD)")
    lines.append("")
    lines.append("| Root | Start | Flags | Reachable VIF/VU1CMD Targets |")
    lines.append("| --- | --- | --- | --- |")
    for fn, targets in roots:
        targets_str = fmt_addr_list(targets, funcs, limit=12)
        lines.append(
            f"| {fn.name} | 0x{fn.start_addr:06X} | {fn.format_flags()} | {targets_str} |"
        )
    lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        sys.stderr.write(f"Usage: {argv[0]} <lo_hex> <hi_hex> <out.md>\n")
        return 1

    lo = int(argv[1], 16)
    hi = int(argv[2], 16)
    out_path = Path(argv[3])

    repo_root = Path(__file__).resolve().parent.parent
    recomp_dir = repo_root / "recomp_source"
    if not recomp_dir.is_dir():
        sys.stderr.write(f"recomp_source directory not found: {recomp_dir}\n")
        return 1

    candidates: list[tuple[int, Path]] = []
    with os.scandir(recomp_dir) as it:
        for entry in it:
            if not entry.is_file():
                continue
            m = FILE_ADDR_RE.match(entry.name)
            if not m:
                continue
            addr = int(m.group(2), 16)
            if lo <= addr < hi:
                candidates.append((addr, Path(entry.path)))

    candidates.sort(key=lambda item: item[0])

    funcs: dict[int, FuncInfo] = {}
    for addr, path in candidates:
        funcs[addr] = parse_function_file(path, addr)

    # Populate callers from scanned set
    caller_sets: dict[int, set[int]] = defaultdict(set)
    for addr, fn in funcs.items():
        for callee in fn.callees:
            if callee in funcs and addr not in caller_sets[callee]:
                caller_sets[callee].add(addr)
                funcs[callee].callers.append(addr)

    for fn in funcs.values():
        fn.callers.sort()

    write_report(out_path, lo, hi, funcs)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
