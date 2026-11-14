# ZeldaMicTrace audit

The first console run showed the loader announcing the IPS file. Its game log contained no `ZELDA_MIC` records, so that run alone did not verify the guest hooks or the logging path.

| IPS32 file offset | Main NSO virtual offset | Contents |
| --- | --- | --- |
| `0x336db30` | `0x336da30` | Branch to the input-block hook at `0x3c461d0` |
| `0x336db98` | `0x336da98` | Branch to the pitch-output hook at `0x3c46280` |
| `0x3c462d0` | `0x3c461d0` | Original 521-byte payload in executable page padding |
| `0x1227ee0` | `0x1227de0` | Added startup branch at the first `DT_INIT_ARRAY` function |
| `0x3c46500` | `0x3c46400` | Added startup marker payload |

Eden applies IPS32 offsets to a synthetic image made of the 0x100-byte NSO header followed by the decompressed module image. The offsets above include that header. The startup payload restores the displaced page-address calculation and resumes at `main+0x1227de4`. ARM64 emulation confirmed the marker bytes at the SVC boundary and verified the restored register state.

The guest uses `svc #0x27` with pointer in x0 and length in x1. The installed build's symbolized executable contains `OutputDebugString`, which reads guest memory and calls the emulator logger. The fresh PS5 9.40 run recorded `ZELDA_MIC_TRACE_BOOT v2 0f7d2d79` under `Debug.Emulated` at 14.676642 s. That establishes that the patched guest startup code reached the emulator logger. The input-block and pitch hooks still require their own runtime evidence.

The startup marker was installed by FTP and read back byte-for-byte. The two original mic hooks were retained. The separate SDK-read probe was built for local testing and held back pending the startup proof.
