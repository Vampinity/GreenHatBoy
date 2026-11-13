# waveydude's runs (11 Nov 2026)

Shared in issue 21 and packed here by GrowingBlackBeans with tools/GrowingBlackBeans/pack-gbb.py. Each run's env.txt is waveydude's app-wide env.txt followed by the per-game overrides (env-title.txt), which is the env the game ran with. Their own notes follow.

# Ocarina of Time 1.1.1 on base PS5 13.60

Four captures for Issue #21. Each folder contains sanitized text copied from the original artifacts. Controller-user lines were removed. Copies were checked for credentials and identifiers, and local addresses, home paths, profile labels, and boot-trace user/group fields were masked where present. Original logs were preserved.

Launch settings across the four runs were Vulkan, Handheld, 0.75x, Bilinear, 1080p at 60 Hz, Fast GPU on, unsafe CPU off, async shaders off, and Reactive flushing off. The base PS5 app-wide env.txt was recovered from an FTP capture at 09:23 local time, before the first of these four launches. Its SHA-256 matches two earlier captures. The intervening install records show executable and title-preset changes. No per-launch app-wide hash is available. Each folder includes that captured env.txt and the separate per-game overrides as env-title.txt.

## 01-astc-crash-18m58s

Lon Lon Ranch and back toward Kokiri. GPUBack failed allocating 32,435,200 bytes for ASTC opacity scan scratch. Largest free block was 4 MiB. Frame generation was absent from the launch log.
First memory-waits binary. Source commit bef232bb72fba49af9416b4937a971b5d8fa6542 records this run and code span 0x2c2e5f0, and contains the revised handler. The exact initial-handler commit is unconfirmed.
Signed eboot.bin SHA-256: 54c498a4461a58f76cf00985d4cda8fa60353f29ad441169c2f51f5a8479a3e0

Boot trace was recovered from the previous-session file after relaunch.
Title overrides are the staged preset.

| File | Artifact source | Removed lines | Masked values |
| --- | --- | ---: | ---: |
| eden_log.txt | t120-build-o-memory-waits/run1-crash/crash-20261111-095523-eden_log.txt | 2 | 0 |
| stderr.log | t120-build-o-memory-waits/run1-crash/crash-20261111-095523-stderr.log | 0 | 2 |
| env-title.txt | t120-build-o-memory-waits/presets/env-0400486024dec000.txt | 0 | 0 |
| boot-trace.txt | t120-build-o-memory-waits/run1-crash/boot-trace.prev.txt | 0 | 3 |
| crash-summary.txt | t120-build-o-memory-waits/run1-crash/crash-20261111-095523.txt | 0 | 0 |

## 02-later-area-a-35m47s

Beat Stalfos and crashed leaving Lost Woods. Same GPUBack allocation failed with a 2 MiB largest free block. 2x frame generation.
Revised memory-waits binary. Source commit bef232bb72fba49af9416b4937a971b5d8fa6542 describes the revised handler and matching code span 0x2c2e630.
Signed eboot.bin SHA-256: 10bd81b279a1bddab047e1b757f7701c75f07db85df485ca5404e9bb663f8746

A boot trace attributable to this session was not recovered.
Title overrides are the staged preset.

| File | Artifact source | Removed lines | Masked values |
| --- | --- | ---: | ---: |
| eden_log.txt | t120-build-o-memory-waits-2/crash-20261111-105250/crash-20261111-105250-eden_log.txt | 2 | 0 |
| stderr.log | t120-build-o-memory-waits-2/crash-20261111-105250/crash-20261111-105250-stderr.log | 0 | 2 |
| env-title.txt | t120-build-o-memory-waits-2/presets/env-0400486024dec000.txt | 0 | 0 |
| crash-summary.txt | t120-build-o-memory-waits-2/crash-20261111-105250/crash-20261111-105250.txt | 0 | 0 |
| framegen.txt | t120-build-o-memory-waits-2/presets/framegen.txt | 0 | 0 |

## 03-later-area-b-9m11s

Cleared Lost Woods, then CPUCore_5 failed allocating 65,011,712 bytes growing the Dynarmic JIT link table. Largest free block was 1 MiB. 2x frame generation. A ten-second window saw 252 runtime pipeline builds, 219 already on disk.
Bounded ASTC scan. Published source equivalent e86889c515f5ecac1fde6519c62c6335e39ef8c4, same tree as c405b1f. Install record verified the signed executable and unchanged title settings and framegen file.
Signed eboot.bin SHA-256: f4a77219ea263b99110b66e007d8426c32dee5cecc9a4d8bcf25576e987be34d

A boot trace attributable to this session was not recovered.
The install record says settings were unchanged, so the preceding build’s staged title overrides and framegen file are included as inherited settings.

| File | Artifact source | Removed lines | Masked values |
| --- | --- | ---: | ---: |
| eden_log.txt | t120-build-o-astc-scan-bounded/crash-20261111-110634/crash-20261111-110634-eden_log.txt | 2 | 0 |
| stderr.log | t120-build-o-astc-scan-bounded/crash-20261111-110634/crash-20261111-110634-stderr.log | 0 | 2 |
| env-title.txt | t120-build-o-memory-waits-2/presets/env-0400486024dec000.txt | 0 | 0 |
| crash-summary.txt | t120-build-o-astc-scan-bounded/crash-20261111-110634/crash-20261111-110634.txt | 0 | 0 |
| framegen.txt | t120-build-o-memory-waits-2/presets/framegen.txt | 0 | 0 |

## 04-later-area-c-24m05s

Reached Dodongo’s Cavern via Kakariko, beat the Lizalfos and stopped voluntarily after 24m05s of logged runtime. 2x frame generation.
JIT shards stability baseline. Published source equivalent a657c6b764f15203a966f9249def754129feef81, same tree as 1f3c15b. Install record verified the signed executable and unchanged title settings and framegen file. Wave Ocarina 01 (4af9c45) came later.
Signed eboot.bin SHA-256: 6c93cc177b3c788f649eae19f9ed98cf6e13574de80f1a8ea95185625a2348a3

Boot trace was recovered from the previous-session file after relaunch.
The gameplay stderr is the rotated stderr.prev.log. Active stderr was empty after relaunch.
The install record says settings were unchanged, so the preceding build’s staged title overrides and framegen file are included as inherited settings.

| File | Artifact source | Removed lines | Masked values |
| --- | --- | ---: | ---: |
| eden_log.txt | t120-build-o-jit-site-shards/dodongos-cavern-checkpoint/eden_log.txt | 2 | 0 |
| stderr.log | t120-build-o-jit-site-shards/dodongos-cavern-checkpoint/stderr.prev.log | 0 | 2 |
| env-title.txt | t120-build-o-memory-waits-2/presets/env-0400486024dec000.txt | 0 | 0 |
| boot-trace.txt | t120-build-o-jit-site-shards/dodongos-cavern-checkpoint/boot-trace.prev.txt | 0 | 3 |
| framegen.txt | t120-build-o-memory-waits-2/presets/framegen.txt | 0 | 0 |

An additional 851-second crash had the same ASTC request size. Its route is unconfirmed.

# Ocarina of Time on base Digital PS5, firmware 9.40

- 01-black-screen: First launch played music with a black screen. The logs record a stalled split GPU command and frame-fence timeouts.
- 02-rendered: The next captured launch rendered. Opening cutscene music was reported missing. Both launch logs report Fast GPU on and Reactive flushing off. The source folder name for the second run refers to an intended Fast GPU change. An explicit Off override was verified later in saved settings, so these captures do not establish what happens on a clean launch with Fast GPU off.

The install record links the executable to the t120-build-o-lichii-state-writes artifact. Signed eboot SHA-256 is 7220adbcb3db578afc48dc02b875c897d53491e842b660a680c27bd9ac31e74f. An exact source commit for this installed binary has not been verified. Both boot traces report build 01.219.028 and firmware SDK 0x09400008. The staged title override is included as env-title.txt. A 9.40 app-wide env.txt for these sessions was not verified.

Controller-user lines were removed from copies. Included text was screened for credentials and identifiers. Originals were preserved. This archive contains the two prior captures.

# 13 Nov 2026: W-13 to W-19 on base PS5 13.60 (seven sessions, five crashes)

Packed by me with `tools/pack-run.py` (its redaction; counts in each `run.json`), plus `heap.log.gz` and, for a crash, `crash-summary.txt` through the same redaction. Each `env.txt` is the app-wide env.txt followed by the per-game overrides the session ran with. Place names in settings comments were replaced with "a later area". What they show: `docs/waveydude/pool-holes-in-place-pack-2026-11-13.md`.

| Folder | Build | Ended |
|---|---|---|
| `2026-11-13-w13-crash-80m` | W-13 | SIGSEGV on a CPU core writing guest memory, 4,836 s |
| `2026-11-13-w14-crash-13m` | W-14 | SIGSEGV on a CPU core, 772 s |
| `2026-11-13-w15-crash-51m` | W-15 | SIGSEGV clearing guest memory for a heap growth of the game, 3,048 s |
| `2026-11-13-w17-crash-19m` | W-17 | `std::bad_alloc` on the GPU back thread, 1,144 s |
| `2026-11-13-w18-crash-38m` | W-18 | SIGSEGV on a CPU core, 2,303 s |
| `2026-11-13-w19-run1-24m` | W-19 | closed by hand, 1,412 s |
| `2026-11-13-w19-run2-16m` | W-19 | closed by hand, 973 s |

Every one ended with the pool's largest free block at 1 to 48 MiB. Crash addresses are read with each build's own symbol file, which is not here.

