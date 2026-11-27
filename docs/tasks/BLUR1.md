# Task BLUR1: stop the game's frame-drop motion blur from firing on single host hitches. One file, NO header edits.
Do NOT build/run/commit. Do not explore; edit only PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp.
Background (verified): guest routine 0x0051E198 runs once per game frame. A frame >1.16 vblanks sets a half-rate mode
(only if byte rdram[0x00649DD8]==1); on recovery it arms a motion blur by writing guest u32 0x0072D498=1.
Add, next to the other replaceFunction overrides in loadELF (see the C332 one ~3428 and the 0x0015993C one ~3449 for
the slot pattern: slot=(addr - g_ps2RecompiledFunctionTableBase)>>2, static orig = g_ps2RecompiledFunctionTable[slot],
bounds check, skip if orig is null), an override for 0x0051E198 that calls orig(rdram, ctx, runtime) and does:
A) env PS2X_DROPBLUR: unless it is "1" (original behaviour), at ENTRY write u32 0 to rdram+0x0072D498.
B) env PS2X_DROPGUARD: unless it is "0":
 - keep a ring of the last 20 call intervals; interval = current vsync tick (runtime->eeScheduler().currentVSyncTick())
   minus the previous call's tick; "slow" = interval >= 2. sustained = at least 10 of the last 20 slow.
 - at entry: if a previous call left the byte forced (static bool forced) and rdram[0x00649DD8]==0 and the u32 at
   rdram+0x00649DD0 equals the value saved when forcing, set the byte back to 1; forced=false.
 - if !sustained and rdram[0x00649DD8]==1: save the u32 at 0x00649DD0, set the byte to 0, forced=true.
 - remember ra=getRegU32(ctx,31) before calling orig; after orig, if forced and ctx->pc == ra (routine completed) and
   the byte is still 0 and the u32 at 0x00649DD0 is unchanged: set the byte back to 1, forced=false.
Log with ps2xSafeLog (file already uses it): once at install "[dropblur] override on blur=%d guard=%d"; and a line
"[dropblur] calls=%u forced=%u sustained=%u" every 600 calls.
Comment above the block: "FIX-BLUR1 (Hack Ledger): PS2X_DROPBLUR=1 and PS2X_DROPGUARD=0 restore the game's behaviour."
Reply with the line range, <=3 lines.
