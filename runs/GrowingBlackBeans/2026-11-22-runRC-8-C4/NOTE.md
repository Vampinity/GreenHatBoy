# runRC-8-C4: booted cold and crashed in the load; NOT a control (22 Nov 2026)

- **Boot cold:** `store prep_5093ab9e new (0 pipelines)`, 0 known, 0 records, count 0, driver cache 0 pipelines. The
  restore didn't reach the console (the local copy checks out, 27 of 27 files). By the header's boot rule it isn't a
  control, whatever happened after: replaced by runRC-9-C4r.
- **The crash:** 389 s after the app started, about 140 s into the load past the gate (the black at script 236 s; warm
  starts 140-176 s): SIGSEGV on VkPipelineBuilder, largest free block 1 MiB. 763 MiB at the black.
- Frames in that load: 21.2, 35.8, 31.1 s. Refusals before the crash: 0 graphics refusals; 1 pack on refusal, 1 reclaim.
- **Read on its own:** a cold start of the control env that did not survive the field load. The cold floor's four (FC2-5)
  and 21 Nov's cold C3 did. It says nothing about R x C (both units were on).
- The main eden_log.txt and stderr.log are the app's relaunch after the crash: read crash-20261122-070822-*.
