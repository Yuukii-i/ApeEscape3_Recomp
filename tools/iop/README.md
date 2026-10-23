# IOP Disassembly & Protocol Analysis Tools

This directory contains read-only Python analysis scripts designed to inspect extracted IOP modules and EE recompiled code for Ape Escape 3.

## Requirements
- Python 3.10+
- `capstone` (MIPS32 little-endian disassembler):
  ```bash
  pip install capstone
  ```

## Scripts

### 1. `analyze_dbc_ee.py`
Scans EE recompiled functions in `recomp_source/` (`sub_00406CC0`, `sub_00407008`, `sub_00407A60`, etc.) for DBC RPC function numbers (`0x1300..0x1363`) and `sceSifCallRpc` callers.

### 2. `analyze_dbc_irx.py`
Parses ELF section headers of `dbcman.irx`, `ds1o.irx`, and `ds2o.irx`. Disassembles SIF RPC server registration routines, export tables, and SIF DMA push routines (`sceSifSetDma` targeting `0x00757D40`).

### 3. `analyze_sg2_irx.py`
Parses `sg2iopm1.irx`, extracts the 36-entry opcode jump table at `.data:0x4820`, and disassembles individual opcode handler routines and `libsd.irx` imported calls.
