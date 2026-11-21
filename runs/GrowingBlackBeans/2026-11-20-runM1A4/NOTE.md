# runM1A4: a clean start; the fourth crash in the load (20 Nov 2026)

- **Clean:** store 80,770 reused, 3 own records, Total Pipeline Count 4; 0 swapper or pack lines.
- **The black** at script 147.8 s with 513 MiB free.
- **The crash** at app 203 s, about 51 s into the load, with 1 MiB free: CPUCore_5 at eboot+0x4c867b, **the same
  address as M1A1**.
- **M1A, all four starts:** four crashes in the same load (three clean). These four and today's controls are one
  batch under Vampinity's condition 4 (PR #27, 20 Nov).
