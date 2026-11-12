# VU1 dual executor (two Vu1Exec threads) — plan

Goal: Vu1Exec is the frame limiter (~20 ms/frame silent, VU1 compute ~14.7). Run consecutive MSCAL programs on two threads, exactly.

## Facts (AUTONOMOUS_LOG 28-29, shop corpus of 8,000 consecutive calls)
- Program output (VU memory + GIF bytes) never depends on inherited registers or flags (scramble masks 1/2/4/8/15: 0 diffs).
- The only cross-program state in VU memory: qword 1023 (output-buffer toggle, words 2/3 swap 0x179<->0x94) and the double-buffered table qwords 636-795 (written by "palette writer" programs, 11% of calls). Output-buffer leftovers never matter.
- Header word 1 of the input batch at TOP predicts "swaps the toggle" 100%; the first qword at TOP predicts "palette writer" 100%.

## Design
- Thread X0 = today's Vu1Exec (real VU memory, runtime m_vu1 via the MSCAL callback). Thread X1 = new thread with its own VU1Interpreter instance and a shadow 16 KB VU data copy.
- Both consume the same ordered event stream (two read cursors; a ring slot is free when both passed it). VIF write records are applied by both to their own copy. MSCAL k goes to thread k&1 (alternation); MSCNT / sync points drain both (sequential fallback).
- Watched state W = qword 1023 + qwords 636-795 (161 qwords). Published per program: after running MSCAL k its thread stores W_after(k) in a slot ring indexed by k, with the observed outcome (swapped?, wrote table?).
- Before running MSCAL k, thread T sets its copy's W to the sequential value:
  - if program k-1 is finished: W_after(k-1), then re-apply VIF writes between MSCAL k-1 and k that hit W;
  - else (running concurrently on the other thread): start from W_after(k-2) (own thread, exact) + VIF writes since, and apply the PREDICTED effect of k-1: toggle swap if its header type says so. If k-1 is predicted to write the table, or its header type is unknown, or a VIF write hit W since k-2: wait for k-1 (sequential).
- After running k, if k ran on a prediction: wait for k-1 to finish, compare the assumed entry W with the true one; on a mismatch re-run k from the corrected W (its GIF output is not submitted yet; output-buffer leftovers do not matter).
- GIF ordering: each program's XGKICK output is captured (thread_local s_vfyCapture) and submitted in program order (submit turn counter); DIRECT packets get a turn number too.
- Learned table: header word 1 -> swap outcome; first qword -> table writer; filled from observed runs (entries only trusted after they were seen; a conflict disables prediction for that key).
- End of job / sync point: drain both, copy the final W to both copies, then X1's copy = memcpy(X0's) so both start equal.
- Fallback: any code image other than the one the facts were measured on, any probe, PS2X_VU1_DUAL=0 -> single executor.

## Tasks
- DA: thread-safety of the VU1 run path for two concurrent VU1Interpreter instances (flag rings thread_local, audit of mutable statics on the run path).
- DB: the dual engine in ps2_vif1_interpreter.cpp (second thread, cursors, W slots, prediction, ordered GIF submit), default off.
- DC: verification mode (PS2X_VU1_DUAL_VERIFY: X1 results recomputed sequentially and compared) + A/B.
