# Docked starts of 19 Nov 2026: the load switches, the pair, and the controls that crashed (runs 2001 to 2034)

Twenty scripted starts, all docked, packed so GrowingBlackBeans (discussion 2, 19 Nov) and anyone else can read
them with their own numbers: refused-pool lines, time under 16 MiB, stranded MiB, and the rest. Logs as they came
off the console, packed with `tools/stk/pack_run.py` (run contract v1, author Vampinity). The only changes are the
redactions counted under "redacted" in each run.json: the console user number and its pad lines, the save-profile
id, the save's name in the script's comment, one private word (the owner's) and the other titles in config.json.
Timestamps and numbers are unchanged.

## The runs

The arm names: **CB** = the docked control, **SD** and **SL** = the pair (`EDEN_NX2_TC_SUPERSEDED=1` plus
`EDEN_UP_DRAIN_TO_POOL=1`), **DP** = `EDEN_UP_DRAIN_TO_POOL=1` alone, **SP** = the pair plus
`EDEN_UP_L1639_PARK_WAIT=1`. CK and CP in batch A are the same control env.

| run | batch | arm | build | how it ended | app s | crash class |
|---|---|---|---|---|---|---|
| 2001 | A, start 6 of 12 | DCK2, control | T196 | crash, SIGSEGV on CPUCore_2 | 238 | G |
| 2004 | A, start 9 of 12 | DCP3, control | T191 | crash, SIGSEGV on CPUCore_4 | 386 | G |
| 2008 | B, docked block | DCB0, control (throwaway, not counted) | T191 | crash, SIGSEGV on CPUCore_4 | 331 | G |
| 2009 | B | DSD1, the pair | T191 | script done | 521 | |
| 2010 | B | DDP1, drain to pool | T191 | script done | 524 | |
| 2011 | B | DCB1, control | T191 | crash, VK_ERROR_OUT_OF_DEVICE_MEMORY on GPUBack | 350 | B |
| 2012 | B | DDP2, drain to pool | T191 | script done | 520 | |
| 2013 | B | DCB2, control | T191 | crash, VK_ERROR_OUT_OF_DEVICE_MEMORY on GPUBack | 321 | B |
| 2014 | B | DSD2, the pair | T191 | script done (the log ends without the close line) | 517 | |
| 2015 | B | DCB3, control | T191 | crash, SIGSEGV on CPUCore_1 | 342 | G |
| 2016 | B | DSD3, the pair | T191 | script done | 521 | |
| 2017 | B | DDP3, drain to pool | T191 | script done | 530 | |
| 2027 | S | DSP1, pair + park wait | T191 | script done | 508 | |
| 2028 | S | DSL1, the pair | T191 | script done | 525 | |
| 2029 | S | DSL2, the pair | T191 | script done (the log ends without the close line) | 522 | |
| 2030 | S | DSP2, pair + park wait | T191 | script done | 510 | |
| 2031 | S | DSP3, pair + park wait | T191 | script done (the log ends without the close line) | 510 | |
| 2032 | S | DSL3, the pair | T191 | script done | 516 | |
| 2033 | S | DSL4, the pair | T191 | script done | 537 | |
| 2034 | S | DSP4, pair + park wait | T191 | script done | 508 | |

As counts: in batch B all four docked controls crashed (DCB0 not counted) and none of the six arm starts did.
Batch S had eight arm starts, no control and no crash. Run2001 and run2004 are the two of batch A's six docked
controls that crashed; the other four (runs 1997, 1999, 2002 and 2006) ran to the end and are not in this set.

"app s" is the time after the app started at the crash, or at the log's last line for the starts that ran to the
end (from run.json, `derived.session_age_s`).

**The crash classes**, each checked in that run's own logs:

- **B**: the driver refuses an 8,294,400-byte buffer (1920 x 1080 x 4, usage 0x3), the "asked once more" retry
  is refused again, and the app ends with `terminate: VK_ERROR_OUT_OF_DEVICE_MEMORY` on GPUBack. The line is
  `EDEN_GRAPHICS_MEMORY asked once more: result -2, buffer of 8294400 bytes, usage 0x3`, near the end of the
  crash copy of stderr (run2011, run2013).
- **G**: a game CPU thread touches swapped-out memory, the 10 s memory wait runs out
  (`EDEN_UP_FAULT_NAMED end ... waited_ms=10053 to 10075 outcome=lost`, in the crash copy of stderr), then a SIGSEGV on a game CPU thread (`CPUCore_N`),
  at an address outside the app's code (run2001, run2004, run2008, run2015).

No start that ran to the end had a lost wait; their longest memory wait was 1.6 to 8.1 s.

## Setup

- **Builds.** T191: eboot sha16 c7a41ac1c9207bdf, version 01.219.028 (Nov 15 2026 20:47:19). T196: eboot sha16
  12172e4e14656b61, 01.219.028 (Nov 18 2026 07:09:53). Base PS5, firmware 12.40, docked, resolution 1x, the shader store of earlier starts in place (warm, store `prep_5093ab9e` reused, 78,735 pipelines).
- **Settings.** The control is play settings v4.0 plus `EDEN_TEST_DISCARD_SAVE=1` (writes go to a copy, never to
  the save) and `EDEN_UP_FAULT_LOG=1`. Every arm differs from it by its own lines only; `derived.env_diff_keys` in
  run.json lists them against run2011's env (so `settings_profile: stock_alpha_v40` on a control only means "the
  same env as run2011"). The two batch A controls have the same env as batch B's control.
- **Route** (`script.txt`, route-field-to-past-field.works-run1397.txt, the same route as the 15 Nov field
  starts): a save in the field, walked by minimap steering to the gate, the load into the next area, then about
  300 s there. The six crashes came 238 to 386 s after the app started.
- **Order.** Batch B's docked block ran DCB0 then DSD1 DDP1 DCB1 DDP2 DCB2 DSD2 DCB3 DSD3 DDP3, an arm before a
  control. DCB0 was the first start after batch A had put T196 on and T191 back, so it is a throwaway and not
  counted. Batch S ran SP1 SL1 SL2 SP2 SP3 SL3 SL4 SP4. The two batch A starts were each the first start after a
  fresh install (the other build went on first, then this one).
- **Capture.** Starts 2030 to 2032 had no game picture on the capture card. That does not touch these logs. No
  video, pictures or frame grids are in this set.

## The files in each folder

- `eden_log.txt.gz`: the emulator's log. The superseded-image lines (`EDEN_NX2_TC_SUPERSEDED last 600 frames`,
  arms with the pair only), the park wait lines (`EDEN_UP_L1639_PARK_WAIT`, SP only), the frame rate every 5 s
  (`nx2:vi2`) and the shader store line (`SOURCE_STAMP`).
- `stderr.log.gz`: the memory side.
  - Free pool: `RADV_PS5_MEMORY t_s=... available_mib=...`, about every 5 s. Use it for time under 16 MiB.
  - Largest free block: `EDEN_MEM_CENSUS n=... t_s=... largest=...`, every 2 s while it is under 768 MiB and at
    each area change, with what holds the memory. There are also `EDEN_HEAP_SLACK`, `EDEN_HEAP_SPACES` and
    `EDEN_VMA_USAGE`.
  - Refusals: `EDEN_GRAPHICS_MEMORY` (budget refused, asked again, a buffer was refused and what went back) and
    `EDEN_REFUSED_IMAGES`. `EDEN_RADV_OUT_OF_MEMORY` stops at 64 lines.
  - The drain: `EDEN_UP_DRAIN_TO_POOL drain N` (DP, SD, SL and SP only) gives the MiB freed, how much of it went
    back to the driver, and the room left inside the blocks. `EDEN_UP_PRESSURE_DRAIN` lines are in every run.
  - Memory waits: `EDEN_UP_FAULT_NAMED end ... waited_ms=... outcome=...` and `EDEN_UP_FAULT_BY_THREAD`.
  - The Vulkan failures (`CreateBuffer VkResult=-2`) and, in a class B crash, the `asked once more` line and the
    `terminate:` line.
- `heap.log.gz`: the env as the app read it (`EDEN_ENV`) and the heap and arena lines.
- `crash-<time>.txt` and `crash-<time>-eden_log.txt.gz`, `-stderr.log.gz`, `-heap.log.gz` (crashed starts only):
  the crash report and the copies of the three logs taken at the crash. The stderr copy can run a few lines
  further than the plain `stderr.log` (in run2011 and run2013 only the copy has the `asked once more` and
  `terminate:` lines, and in run2001, run2004, run2008 and run2015 only the copy has the `outcome=lost` waits), so read the last lines from the copy.
- `env.txt`, `script.txt`, `config.json` (the app's settings, `console_mode: docked`), `boot-trace.txt`.
- `report.txt` and `result.json`: the bench's own summary of the start (timeline, pool, collector, refusals).
- `declared.json` (arm, its lines, control or not, counted or not) and `run.json` (what the shared scorer read
  from the logs, plus the redaction counts).
