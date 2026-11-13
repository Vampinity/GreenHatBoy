# 2026-11-12-FX2-freeze

- **Build:** 01.219.915 (Nov 12 2026 10:31:24) · **firmware:** – · **author:** GrowingBlackBeans
- **Route:** GrowingBlackBeans Kokiri benchmark: Continue, house, out, walk loop to the water
- **What the player saw:** The freeze during runFX2 (12 Nov); env.txt was not saved with it.
- **Menu:** renderer Vulkan, Console mode Handheld, block list off, async shaders off, fast GPU on, unsafe CPU on, unsafe DMA off, reactive flushing off, skip invalidation off, Mods none, Language en-US (chosen en-US), Controls vibration on, buttons as usual ("unsafe CPU" is Faster CPU emulation)
- **Key switches:** – (0 env lines)

## Speed

0 play windows of 5 s, – fps mean; worst frame – ms. Era: unknown. Standing – fps (0 windows), walking – fps (0 windows, heavy share –).

| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |
|---|---|---|---|---|---|---|---|---|---|---|
| light | 0 | – | – | – | – | – | – | – | – | – |
| queued | 0 | – | – | – | – | – | – | – | – | – |
| mid | 0 | – | – | – | – | – | – | – | – | – |
| heavy | 0 | – | – | – | – | – | – | – | – | – |

Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned at the end of the session.

## Textures and memory

Texture churn per 600 frames (whole run): 9 images created, 0 deleted, 188 uploads, 375 MiB.
Memory margins: out of memory in 0 of 22 lines (max 0 MiB).

## Copy guard

96 page copies per 5 s; pool peak 2 of 2048; full 0 times.

## Hitches (frames ≥ 100 ms in play)

None.

Shaders built while playing: 0 (0 ms).

## What this run cannot tell you

Missing: game thread times (EDEN_GBB_SVC_PROFILE); back breakdown (EDEN_GBB_BACK_CALLS).
