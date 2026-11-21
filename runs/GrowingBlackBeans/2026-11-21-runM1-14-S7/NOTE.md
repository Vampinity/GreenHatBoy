# runM1-14-S7, split S7: R (pack on refusal), C (reclaim) and A (swap ahead) out; P T in (21 Nov 2026)

- Env: C1's minus `EDEN_GUEST_SWAP_AHEAD_MIB=2048`, `EDEN_GUEST_SWAP_RECLAIM=1` and `EDEN_UP_PACK_ON_REFUSAL=1`.
- Boot warm: store prep_5093ab9e reused (80770), 3 own, count 4; 01.219.028. Logs folder renamed.
- Removed units gone: 0 on-refusal asks (`on_refusal=0`), 0 reclaim lines, no EDEN_SWAP_AHEAD line.
- Kept: pressure passes 3,305 (4,764 MiB, the most freed in the batch).
- Largest free block at the black 1,195 MiB (in the controls' 1,106-1,366: P is in). Low 0, recovered; through
  the load; no crash files.
- Refused pool events 32 (controls 0-4; S6 33). Worst frame 4,166 ms, normal (S6's was 6,922).
- Pattern to test at the end: the two starts with both R and C out (S6, S7) have 32-33 refusals; starts with only
  one of them out have 0-14 (S1 9, S3 6, S4 0, S5 14). A refused ask that neither refusal-pack nor reclaim can take
  stays refused: a possible R x C pair, per the rule confirmed 4 v 4 if it holds.
