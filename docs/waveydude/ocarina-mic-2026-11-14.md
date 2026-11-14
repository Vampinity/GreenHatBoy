# Native ocarina microphone on PS5 9.40

W-32-mic-signal corrected the raw mono input ring layout and fed the ring after the game's stream engaged. The guest advanced the read cursor and received approximately 48,000 real microphone samples per second in the captured active interval. An earlier signal check measured a sustained tone near 182 Hz with peaks close to the PCM limit. That measurement came from a different session.

[ZeldaMicTrace startup proof](../../runs/waveydude/2026-11-14-w32-mic-recognizer/trace-audit.md) established that guest code could log through `OutputDebugString`. The [9.40 mode comparison](../../runs/waveydude/2026-11-14-w32-mic-instruments/) used the route trace already loaded at launch.

- With Humming selected (selector 0), the trace observed guest reads on READB and zero hits at the traced pitch-return site. Humming may use another processing path.
- With Instruments selected (selector 1), Zelda displayed “Receiving audio.” At 808.217 seconds, READA had reported 4,609,216 samples across 19,190 calls. The input and native pitch-return sites each recorded 9,000 hits by 808.228 seconds. The pitch record's `frames` field is a placeholder. It contains no measured pitch or note ID.
- The virtual audio output ring remained empty during the Instruments capture. Native pitch processing ran under that condition.
- The player reported that humming produced an in-game ocarina response after switching to Instruments, and that the game sometimes picked a different song than intended. The player also reported intermittent low microphone volume warnings. The captured route trace has no signal-level measurement synchronized with those warnings. The log does not tie any individual song selection to a detected pitch or establish why the first success occurred.

For a repeatable recognition check, keep the same build and input mode, hum one known melody, and record the intended and selected songs. Use the native pitch-value diagnostic only if the mismatch repeats and pitch values are needed to explain it. The patch files cover microphone delivery. The guest tracing IPS was used for diagnosis.

## Follow-up comparisons

- [9.40 Humming](../../runs/waveydude/2026-11-14-w32-humming-940/mic-log.txt). Zelda read the controller mic and measured about −6.2 dBFS while the native level gate was on. The gate went off when the input fell back to about −76 dBFS. The player got no song. The audio worker selects the opposite input for its first processing path in Humming mode, and the virtual game-audio stream stayed empty during the attempt. Whether that empty stream explains the missing song remains unverified.
- [13.60 Instruments](../../runs/waveydude/2026-11-14-w32-instruments-136/mic-log.txt). On the older W-32 mic feed with the copied 9.40 save, the game read cursor advanced and the emulator logged 48,000 captured samples written per second with zero inserted silence. The player got no ocarina response. This setup writes PCM at `+0x2000`, while the game SDK for the traced raw mono stream reads from `+0x1040`. Cursor movement alone cannot establish that the game read the intended samples. This comparison also changes consoles and builds, so it cannot isolate the effect of the offset.
- [9.40 Instruments volume](../../runs/waveydude/2026-11-14-w32-volume-940/mic-log.txt). During active listening, capture levels ranged from below −74 dBFS to about −6 dBFS, with peaks near full scale. The log does not timestamp the reported low-volume warning, so its exact trigger remains open.
