# Golden PCSX2 data (Task AE) - collected 2026-10-23. Boot order: loading -> memory card screen -> SCEA (plain image+sound, NOT an FMV) -> dolby FMV (new_dolby_pl2.str) -> intro FMV -> title. F/G/0x772180 ctx belong to the FMV player (first user: dolby FMV).
Method: pcsx2 MCP (DebugServer). `pcsx2_continue` is non-blocking and there is NO hit counter, so
per-5s hit counts were NOT measured; one-hit-at-a-time sampling with EE cycle stamps instead.
Values are [pcsx2] observed unless tagged [INFERRED]. Reference run has no memory card.

## 2 Smoke test
bp 0x24C64C hit with ra=0x24C77C (in your ra list). Tools: connect, set_breakpoint, continue (async),
status (PC+cycles), evaluate (reg), read_memory (u32_array), disassemble, clear_all_breakpoints.

## 3a F entry 0x24C164 (hit right after G, +35 cycles)
a0=0x772180 a1=2 a2=0 s0=0x772180(=a0) s1=2 ra=0x24CEA8
F ctx @0x772180: [+8]=9 (STATE) [+C]=1 [+48]=0x018A7E20 [+4C]=0x018B7200 [+50]=2 [+58]=0x17800 [+5C]=0xFB
 [+60]=2 [+64]=2 [+68]=0x4000 [+6C]=0 [+70]=4 ; [0x018A7E20]=0x12,[+4]=8 ; [0x018B7210]=4
Flags: byte[0x72C7A0]=1 byte[0x72D3A0]=1 word[0x635480]=0
F hits once per frame (G->F, same frame, +35 cycles). Sampled frame gaps: 2.8M and 7.0M cycles.
## 3b G entry 0x24CE28: a0=2 a1=0 ra=0x4E2E00
## 3c counts: NOT MEASURED. Observed in 4 consecutive frames: 0x24BDC8 and 0x24C24C never hit (once at
   FMV start only); 0x24C620,0x24C64C,0x24C650 hit every sampled frame; 0x24C680 hit in 2 of 3.
   One sampled 620->64C->650 pass had no G/F entry before it (loop reached by a path other than F entry?) OPEN.
   Frame order: G -> F(+35) -> 24C620(+66) -> 24C64C(+3, ra=24CEA8) -> 24C650(+1) -> 24C680(+25).

## 3d Control-flow of F for state 9 (native disasm) -- CORRECTION to earlier static outline
F is a state machine: [s0+8]; jr table[0x6EAFBC]: 0:24C2B8 1:24C1DC 2:24C310 3:24C37C 4:24C408 5:24C430
 6,7:24C4A4 8:24C4C0 9:24C4F8 10:24C2B8. Shared epilogue 24C2B8..24C2D4 (jr ra).
State 9 @24C4F8: s5=1; t7=[s0+4C]; beqz -> 24C784 (alt exit).
 s2=[s0+60]+a1; if [0x635480]==1 s2=24B840(s2). t6=[s0+70] < [[s0+48]+4]; if so:
 t7=[[s0+4C]+0x10] (clamped >=0); if (t7 < s2) -> 24C690 (alt) ; else fallthrough 24C560.
 24C560: bnez s5 -> 24C61C ; 24C61C: lb[0x72D3A0] bnez -> 24C64C (else one-time init: [0x72D448]=0x6AF328, flag=1).
 24C64C: a1=s1; v0=func_508684(a0=0x72D448,a1); v0==0 -> 24C568 (s5=0 path); s1=v0.
 24C668: lbu [s1+0xC]==0 -> 24C61C ; else 24C680: jalr [[s1]+0xC](s1, s3, s2-s3); 24C688: b 24C620 (loop).
 NOTE 24C680 is a VIRTUAL call, not jal 31A240. PCSX2: target t7=0x57F2DC, s1=0x741918, s2=4, s3=2.
 List: [0x72D448]=0x6AF328 [0x72D44C]=0x741918 ; node @0x741918: vtbl=0x6B1910 next=0x741918 prev=0x741918 [+C]=1
 (single-element circular list). func_508684(list,0) returns list->[+4] (first node).

## 3e Branch outcomes, F entry -> 24C680 (one frame, derived from regs/mem above; 9 branches)
24C190 bnez lb[72C7A0]=1 TAKEN | 24C1BC beqz state>=11 NOT | 24C1D4 jr -> 24C4F8 (state 9)
24C500 beqz [s0+4C]!=0 NOT | 24C518 bne [635480]=0!=1 TAKEN | 24C53C beqz (4<8)=1 NOT
24C558 bnez (4<s2=4)=0 NOT (BORDERLINE: equal) | 24C560 bnez s5=1 TAKEN | 24C624 bnez flag=1 TAKEN -> 24C64C
24C658 bnez v0!=0 TAKEN | 24C66C beqz [s1+C]=1 NOT | 24C680 jalr 0x57F2DC

## 4 State-word writer trace (watchpoint onchange @0x772188, reference boot -> 1st FMV; 2026-10-23)
Order of writes (pc = store instr, value = new state, ra at break):
 0x24BB20 sw zero,8(a0)  -> 0   init ctor, ra=4E2774
 0x24BD40 sw t7,8(s1)    -> 1   ra=24BD34
 0x24C2B4 (F, via 24C304)-> 5   ra=24C300   (state 1 path, not via state 2)
 0x24C2B4 (F, state 5)   -> 6   ra=24C46C
 0x24CE24 sw t7,8(s1)    -> 7   ra=24CE14   OUTSIDE F: code @24CE0C: jal 24CBFC(v0); bnez v0 -> fail(-2); else state=7
 0x24CBB8 sw t6,8(s0)    -> 9   (~2.4k cycles after the 7 write, same call chain) in func 24CB38:
    if state==7 && byte[s0+7C]!=0 && func_3F75E8([s0+30])==0 { 3F7590([s0+30],100); 3F7150([s0+30],[s0+80]*[0x6EB000]);
    [s0+60]=[s0+64]=0; state = ([s0+84]==0)?9:8 }
func 24CBFC(ctx): readiness check of 2 async slots [ctx+0x10] and [ctx+0xC] via func_1DA880(0x771798,slot,0,0)==1; slot<0 counts as done;
    returns 0 = all done. pcsx2: both slots == -1 at that time.
ctx at state 9: [+7C]=1 [+7D]=1 [+30]=0x01900E00 [+80]=0x3F333333(f32) [+84]=0 [+14]=0 [+10]=-1.

## 5 Command 16 (2nd reference boot, cond bp 0x24CD04 a1==0x10; 2026-10-23)
Hit: a0=0x01900E00 (decoder obj == [ctx+0x30]) a1=0x10 a2=0 a3=0 ra=0x3F7A74 (jalr inside func 3F7A18 <- 3F7E38 <- F state 6 handler 24C4A4).
ctx 0x772180 at that moment: [+8]=6 [+C]=-1 [+10]=-1 (=> 24CBFC returns 0). (state-9 snapshot later: [+C]=1 [+10]=0.)
3F7A18(obj): command ring: head=[obj+0x228]=3 tail=[obj+0x22C]=4; entry i: a1=[obj+0xA0+0xC*i+8], a2=[..+0xC], a3=[obj+0xB0+0xC*i];
  calls fnptr [gp-0x7A60]=0x24CD04(obj,a1,a2,a3); v0<0 -> 3F7B58 (retry/keep entry; dispatcher returns -2 when 24CBFC!=0).
1DA880(mgr=0x771798,h,wait,x): h&0x60000000==0 -> dev=[mgr+0xC]?:[mgr+4]=0x771B88 (vtbl 0x6AD4B0), vtbl[1]=0x1DC650:
  slot=dev+h*16+0x34 -> 1DC578(dev,slot,wait): wait=0 -> pump 1DD010(dev), done iff [slot+8]<0 (wait!=0 loops until <0). For h=1: slot=0x771BCC.

## 6 Async job lifecycle, 3rd reference boot (watchpoints onchange @0x77218C=[ctx+0xC], @0x771BD4=slot1+8; cycles = EE cycle counter)
 131.87M 0x24BB24  ctor writes [ctx+0xC]; 132.11M 0x24BCBC (ra 31A0AC); 132.14M 0x1DC80C sw v0,(s3): job0 submit via 24BC48->1DACF8->1DAC20->1DC7BC, handle v0=0 (chain: 319F38->24BC48)
 195.83M F 0x24C21C [+C]=-1 ; 195.84M 0x1DC9B8 [+C]=handle 0 via F 0x24C2F8 -> 1DB074 -> 1DAF20 -> 1DC968 ; 205.67M F 0x24C474 [+C]=-1 (state 5 -> 6)
 215.5143M 0x1DCC70 sw v0,(s2): [ctx+0xC]=1 (job1 submit, chain 1DB3E4 -> 1DCC30); then 0x1DC1EC sb 0x0E -> byte [slot1+0xB] (slot1=0x771BCC, +8 word top byte = status 0x0E "pending")
 289.2M..295.2M+ 0x1DCF8C sw t6,8(s1) (func 1DCEE0) called from handler 0x438EA8 in INTERRUPT context (sp 0x81ef0, stack 0x81fc0): low 25 bits of slot1+8 accumulate progress
   (0x0E000000 -> 0x0E021800 ...); handler 0x438EA8 = SIF command-packet callback: reads packet from buffer [0x76A518]=0x2076A440, copies, calls 435ED0, dispatches (cmd id bit31 etc).
 Job done <=> word<0 (bit31 set by a later packet; not captured). => IOP->EE SIF packets drive job1 progress+completion ~74M cycles (~0.25 s) after submit.
 Slot1+8 was never written before 215.5M. pcsx2 [ctx+0xC]=1 at 215.5M matches recomp's cbfc0C=1.

## 7 CID1 requests batched in one sceSifSendCmd (4th reference boot; cond bp 0x438E28 [guest sceSifSendCmd] a0==1 && [a3+4]==7; 2026-10-23)
sceSifSendCmd(a0=cid, a1=pkt, a2=psize, a3=srcExtra, t0=destExtra(IOP ring), t1=sizeExtra); ra=0x1DD0C4. Request = 0x20 bytes: {size=0x20, op=7, slotPtr, seq, fd, dst, reqSize, flags}.
 hit1 @215.53M cyc: a3=0xA15220: req seq 0x6E slot 0x771BBC fd=0 dst=0x177B00 size=0x10000 flags=1 ; IMMEDIATELY FOLLOWED in the same buffer by
                    req seq 0x6F slot 0x771BCC fd=0 dst=0x018A7E00 size=0x21800 flags=0   (== job1; 0x21800 = progress seen later)
 hit2 @323.78M cyc: a3=0xA15260, t1(sizeExtra)=0x40 = TWO requests: seq 0x70 slot 0x771BBC dst 0x177B00 size 0x4000 flags 1 ; seq 0x71 slot 0x771BCC ...
So one sceSifSendCmd carries N packed 0x20-byte requests (sizeExtra = N*0x20). Each gets its own completion (reply packet -> guest cb 0x1DCEE0).
Note: pcsx2 Open/Seek requests use fd=0 in the request; recomp Open returns fd=3 and logs fd=3 in raw_req (internal base 3) - equivalent, not the bug.

## 8 Sound-driver shared memory (5th reference run, resumed from the SCEA/pre-SCEA screens; F reaches state 9 during the DOLBY FMV, ~1B cycles after resume)
Layout [INFERRED from 3FBCE8/3FBE78]: command ring at 0x747080 (1024 x 16-byte {cmd,a1,a2,a3}, index gp-0x7A4C), enqueued by 3FBCE8(cmd,a1,a2,a3); status/shadow area at 0x74B080 (= ring end).
 Voice table word v = [0x74B140 + 4*v] (read by 3FBE78 via 402888, used by 3F7780). Values are LIVE (time varying), seen: t_a [0x74B140]=0x8000 [0x74B144]=0x8000 ; t_b [0x74B140]=0 [0x74B144]=0xC000 (F already in state 9 both times).
 Also [0x74B080]=[0x74B084]=0x7FFF. State 8->9 needs 3F7780(obj,0) >= [s0+0x84]=0x4000 at some poll.
 A CPU watchpoint (onchange) on 0x74B140 NEVER fired although the word changed => written by IOP->EE DMA (SIF), not by EE stores.

## 9 Voice table vs time in state 8 (6th reference run, cond bp 0x3FBE78 [0x772188]==8)
 313.9287M cyc: state 8 first poll (voice0 a0=0, then voice1 +101 cyc): [0x74B140]=[0x74B144]=0.
 323.77M cyc (+9.84M ~ 2 frames): [0x74B140]=[0x74B144]=0x4000 (== [s0+0x84]) -> 8->9. Later samples 0x8000, 0xC000 (steps of 0x4000 = stream chunk size; requests seq 0x70 size 0x4000).
 => voice word v = IOP-reported progress of the streamed-audio voice in 0x4000 chunks (INFERRED: SPU transfer/play position). Voices 0 and 1 (mask 3, stereo pair).
SG2 audio RPC path (docs/SG2_SPEC.md): sid 0x11223344 client 0x74B240, send ring 0x747080 (N*16B {op,a1,a2,a3}, N=[0x72C624]), recv 0x74B080 (0x1C0 B) = IOP status block (IOP buf 0x8D38). Called each frame from 3FBFB0 (ra 0x3F6360).
 Recomp HLE (RPC.cpp ~441-560, SG2_AUDIO) zeroes the recv buffer on every call => table stays 0 forever. Sample ring prefix at a late call: ops 0x13(a1=0x187b00,a2=0x25010,a3=0x23b0), 0x10, 0x0f, 0x0e(a2=a3=0x1e3c), 0x0d, 0x0b(a1=1,a2=0x1dffff).

## 10 SG2 audio RPC calls at dolby FMV start (7th reference run; cond bp 0x439A28 [guest sceSifCallRpc] a0==0x74B240 && t0!=0 && [0x772188]>=5; send=0x747080 N=t0/16)
 call A @196.2M cyc, F state 5, N=2: {0x18, 0x0002401B, 0x58800100, 0x00177B00} {0x18, 0x0102401B, 0x98800100, 0x00177F00}   (op 0x18 "Transfer Waveform": a3 = EE source 0x177B00/0x177F00 = movie audio chunk read by CID1 job0 dst 0x177B00)
 call B @304.45M cyc, F state 8, N=7 (stream start, 2 voices mask 3): {0x1C,3,0,0} {0x1A,1,0,0x3FFF0000} {0x1A,2,0,0x00003FFF} {0x1B,3,0,0xBB80} {0x1B,3,0,0xBB80} {0x1A,1,0,0x2C800000} {0x1A,2,0,0x00002C80}  (0xBB80=48000 Hz)
 call C @1.66B cyc, state 9, N=2: {0x18,...,0x177B00} {0x18,...,0x177F00} then op 0x19 a1=1 queued (next chunk refill / stop).
 Status words after call B: voice table [0x74B140+4v]: 0 -> 0x4000 within ~2 frames; later 0x8000 / 0xC000 / 0 (wrap) with voice0 and voice1 at different values.
 MODEL [INFERRED, fits all samples]: ring buffer of 0x10000 bytes per voice in SPU RAM, 0x4000 chunks; status[v] = END of the chunk currently being played = (((pos>>14)+1)<<14) & 0xFFFF;
 pos advances at real-time ADPCM rate = 48000*16/28 = 27428 B/s per voice (pitch 1.0) from key-on (op 0x1C a1=mask). => first poll after key-on = 0x4000 = [s0+0x84] => state 8->9 immediately.
 The game refills a chunk (CID1 Seek size 0x4000) each time the reported end-offset changes.

## 11 sceMpegGetPictureRAW8 reference (8th run; bp 0x31A2B8 / 0x31A2C0 around `jal 319F14` in 31A240)
Call: 319F14(a0=0x772310 [sceMpeg ctx], a1=dst 0x163A280, a2=0x300 (MB capacity), a3=([s1+0x1FC]==1) =1 -> j 408DB8 [= RAW8 impl: sets inner=[a0+0x40]: [+F8]=a2 [+EC]=(a1&0x0FFFFFFF)|0x20000000 [+F0]=[+F4]=[+C4]=0, jal 4084D0 decode loop (IPU)]).
 Returns v0=1 after ~1 frame (synchronous); first frame output is black: per MB Y=0x00 x256, Cb=Cr=0x80 x128. Later frames carry real data (Y 0x0F..0xFF, TV-range black ~0x10; chroma ~0x80).
 sceMpeg ctx during playback: [a0+0]=0x200 (width 512) [a0+4]=0x140 (height 320) [a0+8]=frame counter (0xE2=226 at sample) [a0+0x20]=0xDB; at first call all 0 and [+0x10..]=-1.
 OUTPUT LAYOUT (verified by edge continuity, MB k and k+1 vertically adjacent: diff ~7 vs ~170 horizontally): macroblocks are COLUMN-MAJOR (mb index = mbx*MBrows + mby); each MB = 384 bytes:
   Y 16x16 raster (256) | Cb 8x8 raster (64) | Cr 8x8 raster (64). Picture grid = 32 x 20 MBs (512x320) = 640 MBs (a2=768 is buffer capacity, 32x24).
 Triple buffer ids in [s1+0x1D8..]=0x96,0x97,0x98 (buffers at 0x163A280 + k*0x48000 observed).

## 12 Movie loop timing / end condition (9th run)
 31A240 per F frame: call1 a1=0 [s1+0x1F0]=0 [s1+0x1F4]=0 [s1+0x1F8]=0; call2 (next F frame) a1=2 [+1F0]=1 [+1F4]=1 [+1F8]=2 (time advances +2/frame; decode when a1 >= [s1+0x1F8]).
 0x57F2DC (vtbl[3] of list node 0x741918, called from 24C680): first call inits (24BB00(0x772180), flag [0x72D390]=1, [s0+0x1FC]=0, [s0+0x188]=0, 428B80(cb 0x31A3C8)), then tail-calls 31A240(0x772180, a1=time).
 F state 9 path end 24C5A0 (slt t7,t5,t7 ; t5=[s0+0x64] t7=[s0+0x5C]): frame1: t5=4 t7=0xFB(251) => continue; else state=10 (24C5AC). ctx at that time: [+58]=0x17800 [+5C]=0xFB [+60]=4 [+64]=4 [+68]=0x4000 [+6C]=0 [+70]=4 [+4C]=0x018B7200 [+48]=0x018A7E20.

## 13 F state-9 frame-1 control flow (10th run; bp 24C4F8/24C5A0/24C5E8)
 PCSX2 frame1: 24C4F8 ([s0+4C]=0x018A7E30) -> 24C5A0 ([+60]=[+64]=2, [+4C]=0x018B7200) -> NO 24C5E8 -> next frame 24C4F8 (so 24C5A0 exits via 24C5B8..24C5C8 bnez t6 -> 24C4B0 [jal 3F7E38] -> 24C2BC exit).
 24C5C8 test: t6 = [s0+0x6C] + [[s0+0x48]] ; t6 = slt(t5=[s0+0x64], t6) ; bnez -> 24C4B0.   PCSX2 [s0+0x48]=0x018A7E20 -> [0x018A7E20]=0x12 (frame/size field), [+4]=8.
 24C5D0 path (clears [s0+4C], pump 3F7E38, expects refill [s0+4C]!=0) is the *other* branch (taken when t5 >= t6).

## 14 Writers of F ctx [+0x48] (0x7721C8) and [+0x58] (0x7721D8) (11th run, onchange watchpoints)
 ctor 0x24BCF0 (func 24BC48 via 319F38) zeroes [+0x48]/[+0x4C]; F 0x24C25C sw t7,0x58(s0)=0x21800 (hdr+0x18, 195.84M cyc);
 REAL SETUP: @304.0754M cyc [+0x48]=0x018A7E20 written by 0x24C900 and [+0x58] by 0x24C914 (t5; later 0x17800) inside func 24C8B4, called from 24C7DC (jal at 24C87C... chain),
 which is called by the command dispatcher cmd-8 case at 0x24CDFC (`jal 24C7DC` a0=s1 ctx, a1=s3) when: 24CBFC==0, [s1+8]!=8 (state was 6), and [s1+0x64]<=0 (blez at 24CDD4; pcsx2 [+0x64]=0 [+0x60]=0 [+0x68]=0x10000 [+0x6C]=0).
 24C7DC itself: init flag [0x72C7A0], jal 24CBFC again (bnez -> exit), releases slots [s0+0x10],[s0+0xC] (1DB6A4/1DB798, sets -1), then 24C8B4 sets the stream buffers.
 Order in pcsx2: cmd 8 executes while F state == 6 (304.07M), then cmd 16 -> state 7 (304.09M) -> 24CB38 -> state 8 -> 9.
 Dispatcher cmd 8 case when [s1+8]==8 returns -2 forever (24CDCC b 24CD80): so cmd 8 MUST run before state 8.

## 15 Chunk magic check in 24C8B4 (12th run; bp 0x24C8E4)
 24C8B4: t4=[s0+0x34+4*[s0+0x50]] (=0x018A7E00 in pcsx2) -> [s0+4C]; lq 16 bytes at t4 compared (MMI lq/pceqw/ppach/nor/sltiu) with 16-byte constant at ELF 0x6EAFF0 = "GroupOfDataInfo\0" (47726f75704f6644617461496e666f00); equal -> [+48]=t4+0x20 (24C900), [+6C]=[t4+0x10], [+58]=[t4+0x28]... ; else branch 24CA2C (error).
 pcsx2 buffers after the CID1 Seeks: 0x018A7E00 (job1, 0x21800 B): "GroupOfDataInfo\0" 00000000 10000000 ... 12000000 08000000 00780100 ... "Mpeg2Video\0.." (data directory).
   0x00177B00 (job0, 0x10000 B, dst differs in recomp = 0x18D000): head 54000fae 82730046 02000f24 f801cdc5 0002ccc5 62fa050c ac000fae 08000f8e d4040426 7000117e (looks like MIPS-like/ADPCM-ish binary).
   F header @0xD15B00: 73747200 00000000 fb000000 6a170000 0e000000 00c80200 00180200 00600300 80bb0000 02000000 00040000 00400000 00000100 40040000.

## 16 Movie file layout vs CID1 Seek positions (recomp probe_ap scan of new_dolby_pl2.str, size 1968128 = 0x1E0800)
 "GroupOfDataInfo\0" at file offsets 0x10800, 0x36000, 0x51800, 0x75800, 0x96800. Header (2048 B = 0x800) at offset 0 ('str', frames 251).
 pcsx2 stream reads (sizes 0x10000, 0x21800, 0x4000, ...) are sequential from file offset 0x800: 0x800..0x10800 (job0), 0x10800..0x32000 (job1, starts "GroupOfDataInfo"), 0x32000..0x36000 (seq 0x70, next group at 0x36000 exactly).
 Recomp started at offset 0 => job1 got file[0x10000..] (no magic) => 24C8F4 compare fails (t7_cmp=0) => [+0x48]/[+0x58] never set.

## 17 SG2 op 0x18 (waveform transfer) packet format (10th run; bp 0x3FBCE8 a0==0x18, caller 0x402658 packs a struct at a0)
 Call A args: a1=0x0002401B a2=0x58800100 a3=0x00177B00 (t7=0x4000 size field, t6=0x100, t5=0x1B). Packing (from 0x402658-0x4026BC, S=struct ptr):
  a1 = (byte S[0]<<24) | (S[4]&0xFF0000) | (S[0x14]&0xFF00) | ((S[0x10]&0xFF0000)>>16)
  a2 = (S[0x10]<<16) | ((S[0xC]>>8)&0xFFFF)
  a3 = (S[0xC]<<24) | (S[8]&0xFFFFFF)   -> S[8]=EE source addr (0x177B00 / 0x177F00); size/SPU-dest fields not yet decoded.
 Stream header (movie hdr words): 48000 Hz (0xBB80), interleave fields 0x400/0x4000/0x10000. Movie audio = SPU-ADPCM, 2 voices (L=mask1,R=mask2), vol 0x3FFF, key-on op 0x1C mask 3.
 Recomp already receives the same ops 0x18/0x1A/0x1B/0x1C (probe_aq.log) but SG2 HLE only fakes status; no ADPCM decode/output (ps2_audio.cpp backend exists: onVagTransferFromBuffer, play(sampleAddr,pitch,vol,voice)).

## 18 Movie bitstream feed (11th run; bp 0x319E0C hit, backtrace 319E0C <- 408FE0 <- 40FC48/40FEB0/412148 <- 4084D0 <- 408DB8 [RAW8] <- 31A240 <- 24C2DC)
 319E0C = Nodata callback (sceMpegAddCallback type 1) called FROM INSIDE RAW8's decode loop. It pops {addr,size} from a guest ring (entries 0x696D88+8*idx, 32 entries, write idx [0x696E88], read idx [0x696E8C]); empty -> feeds dummy 0x696D40 (00 00 01 B7); else sets [0x696D54]=addr [0x696D58]=size and programs IPU_TO DMA4 (0x1000B410 MADR, 0x1000B420 QWC=(size+15)>>4, 0x1000B400 CHCR=0x101).
 First call: head=0 tail=8; entries {18A7E50,1154} {18A8FD0,7BA8} {18B0BA0,1490} {18B2050,51A8} {18B7220,547C} {18BC6C0,1700} {18BDDE0,59C8} {18C37D0,5D08}. Entry0 = MPEG-2 ES `00 00 01 B3 20 01 80 14 ...` (seq hdr 512x320). Group header at [0x18A7E20]: 12 00.. 08 00.. 00 78 01 00 | "Mpeg2Video" | +0x24 size 0x1154.
 Recomp: guest never calls sceMpegDemuxPss/AddBs; HLE RAW8 never feeds the decoder -> have=0 forever (probe_ay: 6 calls, all black). Perf (probe_ay): per movie frame ~1100 MSCALs x ~0.8 ms in VU1 interpreter = ~0.85 s/frame; memcard screen: GIF/raster ~890 ms/s.

## 19 Movie VU1 colour conversion (from recomp dumps logs\vu1dump, 2026-10-24; NOT a PCSX2 observation, but the guest program/data are identical)
 VU1 program start PC 0x048 (code sig FNV1a64[0:0xE00]=0xF72A6639E95D7AC8) per 16x16 MB: 16 GIF packets x 16 POINTs (PACKED RGBAQ,XYZ2, PRIM 0x200 -> context 2), target FRAME_2 FBP 0x150 FBW 8 CT32, 512x384. MB order column-major (mbx=k/24, mby=k%24). VU memory: qw 0x60+p (p 0..255): x=Y[p] raster, y lane = Cb[p] (p<64, via UNPACK S-8 masked lanes), z lane = Cr[p] (p<64), w=Y; same Y/Cb/Cr bytes as guest RAW8 MB (idx*384: Y|Cb@+0x100|Cr@+0x140).
 Output colour ~ JFIF full range: R=Y+1.402(Cr-128) G=Y-0.344136(Cb-128)-0.714136(Cr-128) B=Y+1.772(Cb-128), clamp; mean abs error vs dumped points 0.5-2 (nearest chroma (py/2)*8+px/2); max ~15-20 => the real program likely interpolates chroma slightly or uses fixed-point coefficients.

## 20 Movie shutdown 0x24BFF8 at the natural end of the dolby movie (12th run; bp 0x24BFF8, a0=0x772180)
 Entry state: ctx[+8]=0x0A (state 10), [+0xC]=0xFFFFFFFF, [+0x10]=0x00000000 (handle 0), [+0x14]=0, [+0x18]=0xFFFFFFFF. CID1 device 0x771B88: dev30 [0x771BB8]=1; slot0 (0x771BBC) allocated: words 'DFCF',0x8B,0x8E000000.. (completed, bit31 of word2 set); slots 1..15 empty. So at the natural end exactly ONE job slot (handle 0) is allocated, no reads in flight; 0x24BFF8 polls+releases it (1DA880 a2=1, 1DB798), then Close(op4) allocates its own slot (dev30=1 at the Close send, seen with bp 0x438E28 a0==1 && [a3+4]==4).
 Recomp (probe_bm): dev30_before=3 at the Close, dev30 stays 2 after => 2 extra slots (max dev30 reached 4 in recomp during movie 1; the game keeps >2 reads in flight when playback is slow/early-ended) that 0x24BFF8 does not track ([s0+0xC],[s0+0x10] hold only 2 handles).

## 21 CID1 device job slots in steady state (advertise movie, F state 9; PCSX2 13th run, paused mid-play)
 ctx[+0xC]/[+0x10] handles; dev30 [0x771BB8]=2; slot0 (0x771BBC) 'DFCF', seq 0xD7, word2 0x8E004000, word3 0x4000; slot1 (0x771BCC) 'DFCF', seq 0xD8, word2 0x8E022000, word3 0x22000; slots 2..15 empty. bp 0x1DC67C (alloc+submit method) never hits in 10 s of playback => reads RE-ARM slots 0/1; release (1DBAA0) only via shutdown 24BFF8. 1DA880(dev=0x771798,h,a2,a3)=generic wait/poll -> device vtable[1] = 1DC650 -> 1DC578 (poll via 1DD010 which does a sceSifSendCmd(0x10?) pump). 1DC67C(dev,&handleOut,a2,a3,t0)=alloc slot (1DBA64) + submit (1DBB00). Movie file here: debug/us/movie/new_advertise.str (2nd movie after dolby; header frames 0x1845=6213).

## 22 CID1 slot alloc/release sequence at the START of the dolby movie (PCSX2 14th run; bp 0x1DBA64 alloc and 0x1DBAA0 release, cond [0x772188]!=0)
 #1 alloc (dev30 0->1, F state 1, ctx[+0xC]=[+0x10]=[+0x14]=-1): chain 1DBA64 <- 1DC7BC <- 1DAC20 <- 1DACF8 <- 24BC48 (movie Open) <- 319F38 <- 4E2730 (Open job -> slot 0, handle stored in ctx[+0xC]).
 #2 release slot 0 (a1=0): 1DBAA0 <- 1DCEC4 <- 1DB798 <- F state-1 handler at 0x24C218 (code 24C1DC: poll 1DA880(h=[s0+0xC]) ==1, 1DB6A4 get result, 1DB798 release, [s0+0xC]=-1, then magic check "str" at [s0+0x1C], 24BDC8 header parse).
 #3 alloc: 1DBA64 <- 1DC968 <- 1DAF20 <- 1DB074 <- 0x24C2DC (state-1/5 block: first stream read submit, with the F ctx now holding the header fields [+0x48],[+0x58]..).
 #4 release a1=0 from 0x24C46C (inside the 0x24C2DC block).
 #5 alloc: 1DBA64 <- 1DCC30 <- 1DB3E4 (other submit type).
 Steady state afterwards = slots 0/1 re-armed (golden sec.21). i.e. the Open slot MUST be released at 0x24C218 (and the next at 0x24C46C) so the stream jobs land in slots 0/1 again.
