# runM1A4: a clean start; the fourth crash in the load (20 Nov 2026)

- **Clean:** store 80,770 reused, 3 own records, Total Pipeline Count 4; 0 swapper or pack lines.
- **The black** at script 147.8 s with 582 MiB free (the driver's last line before the black; corrected 22 Nov from 513).
- **The crash** at app 203 s, about 51 s into the load, with 1 MiB free: CPUCore_5 at eboot+0x4c867b, **the same
  address as M1A1**.
- **M1A, all four starts:** four crashes in the same load (three clean). They are read against WF2-5 (19 Nov, the same
  build), not against controls from the same batch, so condition 4 on #27 isn't met here (corrected 22 Nov). M1A-S's
  interleaved controls are in #33.
