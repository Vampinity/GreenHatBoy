# runM1-24-S12, split 12: all five units out, the swapper alone (21 Nov 2026)

- Env = C1's minus the eight lines of P, R, C, A and T, nothing else. Boot warm: store prep_5093ab9e reused (80770),
  count 4; 01.219.028. Logs folder renamed (no .prev files). Script ended 449 s; log to t_s 968.
- Proof lines: no EDEN_UP_PACK line at all (P and R out), no EDEN_SWAP reclaim line (C out), no EDEN_SWAP_AHEAD
  line (A out). The swapper itself runs (EDEN_SWAP_CHECK ok=1, mode 3).
- Largest free block at the black 929 MiB (controls 986-1,366; P-out splits 838-1,042). Low 0, recovered; through
  the load; no crash files.
- Harm signs, both "worse beyond the noise, not yet shown" (one start) against WF2-5: refused pool events 32
  (controls 0-9 in this batch; corrected 22 Nov from 1-14); worst frame 7,431 ms (controls ~3.7-4.1 s). Load 22.5 s, within the noise.
- The R x C pattern repeats: S6, S7 and S12, the three starts with both pack on refusal and reclaim out, are the
  only ones with 32-33 refused pool events. Under M1-DESIGN's rule that is a possible pair: confirm R x C together,
  4 against 4.
- The long worst frame is narrower: S6 (6.9 s) and S12 (7.4 s) also have P out; S7 (P in) had 4.2 s. A lead that
  P x R x C, not the pair alone, drives the long frame. Two starts; not shown.
- Corrected 22 Nov: the 32 is a throttled report line, not a count. Graphics refusals to script_end: 320 (314 images,
  6 buffers); the 21 other counted starts 0-15.
