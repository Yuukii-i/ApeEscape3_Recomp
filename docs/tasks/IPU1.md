# Task IPU1: decode the game's IPU IDEC picture jobs (level-select previews). Two .cpp files, NO header edits. Do NOT build/run/commit.
Cause: the override of 0x100E64 (ps2_runtime.cpp ~3428) retires every IPU job without decoding, so dst stays zero.
Fix: decode with the FFmpeg MPEG-2 decoder (same libs/guards as Kernel/Stubs/MPEG.cpp, PS2X_HAS_FFMPEG).
1) PS2Recomp/ps2xRuntime/src/lib/Kernel/Stubs/IPU.cpp: add GLOBAL-namespace `bool ps2xIpuIdecJob(uint8_t *rdram, uint32_t jobAddr)` (returns false without FFmpeg or on any check failing; writes dst only on success).
Job (guest, jobAddr&0x01FFFFFF): +2 u8 cmd (need (cmd&0xF0)==0x10), +3 u8 ctl, +4 u16 inQw, +6 u16 outQw, +8 u32 src, +12 u32 dst.
IDP=ctl&3, AS=(ctl>>4)&1, IVF=(ctl>>5)&1, QST=(ctl>>6)&1. N=outQw/64 macroblocks (1..256). Reject src/dst with bit31 set or range past 32MB (else mask 0x01FFFFFF).
width = N*16, but if N*16>=4096 use N*16-1 (4095). height=16.
Build an elementary stream with a small MSB-first bit writer (start codes byte aligned, zero padded):
 000001B3: width&0xFFF(12), height(12), aspect=1(4), rate=4(4), bitrate=0x3FFFF(18), 1(1), vbv=112(10), 0(1), load_intra=1(1), 64 bytes copied from rdram 0x0062EBB0 (8 bits each, already zigzag order), load_non_intra=0(1).
 000001B5: id=1(4), profile_level=0x44(8), progressive_seq=1(1), chroma=1(2), hsize_ext=width>>12(2), vsize_ext=0(2), bitrate_ext=0(12), 1(1), vbv_ext=0(8), low_delay=1(1), 0(2), 0(5).
 00000100: temporal_ref=0(10), coding_type=1(3), vbv_delay=0xFFFF(16), 0(1).
 000001B5: id=8(4), 0xF(4) four times, IDP(2), picture_structure=3(2), tff=1(1), frame_pred_frame_dct=1(1), concealment=0(1), QST(1), IVF(1), AS(1), repeat_first=0(1), chroma420type=1(1), progressive_frame=1(1), composite=0(1).
 00000101 (slice): quantiser_scale_code=1(5), 0(1), then '1'(1, address increment of first macroblock), then ALL inQw*16 source bytes written through the bit writer (bit shifted), align, then 000001B7.
Decode: AV_CODEC_ID_MPEG2VIDEO, thread_count=1, AV_CODEC_FLAG_LOW_DELAY; open once (static, mutex), packet with AV_INPUT_BUFFER_PADDING_SIZE zeros; send_packet, send NULL, receive_frame, then avcodec_flush_buffers. Free frame/packet. Check frame height>=16 and format YUV420P.
Output: macroblock i (x=i*16 in the frame) -> rdram dst + i*1024, 16 rows of 16 pixels, bytes R,G,B,A=0x80. For x==width (the clipped column) just read linesize data. Chroma is 2x2 shared. Exact conversion:
 lum=(149*max(0,Y-16))>>6; cr=V-128; cb=U-128; r=clamp((lum+((204*cr)>>6)+1)>>1); g=clamp((lum+((-104*cr)>>6)+((-50*cb)>>6)+1)>>1); b=clamp((lum+((258*cb)>>6)+1)>>1).
Env PS2X_IPU_DECODE=0 -> return false at once.
Logging (use the same safe log function ps2_runtime.cpp uses, ps2xSafeLog, declare it extern the same way if needed; else fprintf(stderr)): for the first 8 jobs, and every job when PS2X_IPU_LOG=1:
 "[ipu] job=0x%08x src=0x%08x dst=0x%08x n=%u ok=%d src8=<8 hex bytes of src> out16=<16 hex bytes of dst>".
2) PS2Recomp/ps2xRuntime/src/lib/ps2_runtime.cpp, the C332 override: declare `bool ps2xIpuIdecJob(uint8_t *, uint32_t);` at file scope, call it with getRegU32(ctx,4) BEFORE the dispatch to 0x100F7C; remove the old "(retired without decode)" log block; keep the dispatch. Update the comment (job is now decoded; PS2X_IPU_HLE=0 still disables the whole override, PS2X_IPU_DECODE=0 only the decoding).
Reply with the line ranges touched, <=4 lines.
