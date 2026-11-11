#!/usr/bin/env python3
"""runreport.py RUN [--out FILE]: a one-page Markdown report for one run.

What it answers, in order: what ran (build, env, route), how fast (play fps by regime), where a frame went
(stage budget per regime), what hurt (hitches with causes), and what the run cannot tell you (missing families).
Agents: start here for a single run, then open eglog.py windows for detail. Standard library only.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import eglog  # noqa: E402

KEY_SWITCHES = ["EDEN_NX2_FRAMES_AHEAD", "EDEN_UP_AHEAD_GUARD", "EDEN_UP_AHEAD_ALWAYS", "EDEN_GBB_GUARD_EARLY",
                "EDEN_GBB_TRUST_COPY", "EDEN_NX2_RESNAPSHOT", "EDEN_UP_SHADER_PREP", "EDEN_NX2_DMA_SNAPSHOT",
                "EDEN_UP_FRITCHII_LISTSYNC", "EDEN_UP_FRITCHII_LISTSKIP", "EDEN_NX2_READBACK_WAIT",
                "EDEN_NX2_OVERWRITE_CHECK", "EDEN_NX2_GPU_PROFILE", "EDEN_GBB_BACK_CALLS", "EDEN_GBB_SVC_PROFILE",
                "EDEN_GBB_COST", "EDEN_GPU_TIME", "EDEN_NX2_SPLIT_WAITS"]
COSTLY = {"EDEN_NX2_GPU_PROFILE": "profiler: about -20% fps, inflates back zones",
          "EDEN_NX2_OVERWRITE_CHECK": "audit: a few % fps, more with 0920 landings",
          "EDEN_GBB_SVC_PROFILE": "per-SVC timing: small", "EDEN_GBB_COST": "rdtsc scopes: small"}


def f(v, nd=1):
    return "–" if v is None else (f"{v:.{nd}f}" if isinstance(v, float) else str(v))


def report(path):
    run = eglog.load(path)
    s = run.summary()
    L = [f"# {s['run']}", ""]
    L.append(f"- **Build:** {f(s['build'])} · **firmware:** {f(run.firmware)} · **author:** {f(s['author'])}")
    L.append(f"- **Route:** {f(s['route'])}")
    if run.meta.get("impressions"):
        L.append(f"- **What the player saw:** {run.meta['impressions']}")
    sw = [f"`{k}={run.env[k]}`" for k in KEY_SWITCHES if k in run.env]
    L.append(f"- **Key switches:** {', '.join(sw) if sw else '–'} ({len(run.env)} env lines)")
    costly = [f"{k} ({v})" for k, v in COSTLY.items() if run.env.get(k, "0") not in ("0", "")]
    if costly:
        L.append(f"- **Measurement cost in this run:** {'; '.join(costly)}. Compare fps only with runs that have the same.")
    L += ["", "## Speed", "",
          f"{s['play_windows']} play windows of 5 s, {f(s['play_fps'])} fps mean; worst frame {f(s['worst_ms'], 0)} ms. "
          f"Era: {s['era']}. Standing {f(s['standing']['fps'])} fps ({s['standing']['windows']} windows), walking "
          f"{f(s['walking']['fps'])} fps ({s['walking']['windows']} windows, heavy share {f(s['walking']['heavy_share'], 2)})"
          f"{'; door at ' + format(s['door_s'], '.0f') + ' s' if s['door_s'] else ''}.", "",
          "| Regime | Windows | Share | fps | Frame ms | Fence wait | Back busy | Front waits | Ring k words | Host GPU ms | GPU busy |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in ("light", "queued", "mid", "heavy"):
        g = s["regimes"][r]
        L.append(f"| {r} | {g['windows']} | {f(g['share'], 2)} | {f(g['fps'])} | {f(g['frame_ms'])} | {f(g['fence_ms'])} | "
                 f"{f(g['back_busy_ms'])} | {f(g['front_waited_ms'])} | {f(g['ring_kwords'], 0)} | {f(g['gpu_ms'])} | "
                 f"{f(g['gpu_busy_pct'], 0)}{'%' if g['gpu_busy_pct'] is not None else ''} |")
    L += ["", "Per-frame ms unless noted. Light = fence wait < 1 ms with the back idle 20% or more (the game's CPU sets "
          "the pace); queued = no fence wait but the back over 80% busy (the GPU side throttles through the command "
          "queue); heavy = fence wait ≥ 5 ms. Back busy from the split's idle figure; host GPU from stderr, aligned "
          f"{'one window before the end' if s.get('gpu_align') == -1 else 'at the end'} of the session.", ""]
    hv = run.play("heavy")
    if hv and any(w.drains for w in hv):
        tot = {}
        for w in hv:
            for k, (ms, n) in w.drains.items():
                tot.setdefault(k, []).append((ms, n))
        L += ["## Front waits on the back, heavy windows", "", "| Site | ms per frame | waits per frame | µs each |", "|---|---|---|---|"]
        for k, v in sorted(tot.items(), key=lambda x: -sum(y[0] for y in x[1])):
            ms = sum(y[0] for y in v) / len(v)
            n = sum(y[1] for y in v) / len(v)
            if ms >= 0.1:
                L.append(f"| {k} | {ms:.1f} | {n:.0f} | {ms / n * 1000 if n else 0:.0f} |")
        L.append("")
    if run.svcprof:
        play_t = [w.t for w in run.play()]
        lo = min(play_t) if play_t else 0
        thr = {}
        for t, tid, frames, mspf, svc, outside in run.svcprof:
            if t >= lo and frames >= 40:
                thr.setdefault(tid, []).append(outside)
        top = sorted(thr.items(), key=lambda x: -sum(x[1]) / len(x[1]))[:8]
        L += ["## Game threads (ms per frame outside SVCs, play)", "",
              ", ".join(f"t{t} {sum(v) / len(v):.1f}" for t, v in top), ""]
    if s.get("texture_churn_per_600_frames") or s.get("memory"):
        L += ["## Textures and memory", ""]
        c = s.get("texture_churn_per_600_frames")
        if c:
            L.append(f"Texture churn per 600 frames ({c['scope']}): {c['created']} images created, {c['deleted']} deleted, "
                     f"{f(c['uploads'])} uploads, {f(c['upload_mib'])} MiB.")
        mm = s.get("memory")
        if mm:
            L.append(f"Memory margins: out of memory in {mm['out_of_memory_events']} of {mm['lines']} lines "
                     f"(max {mm['out_of_memory_max_mib']} MiB).")
        L.append("")
    if s.get("live_phases"):
        L += ["## In-run live-switch phases", "", "| Label | Phases | fps |", "|---|---|---|"]
        for k, v in s["live_phases"].items():
            L.append(f"| {k} | {v['phases']} | {v['fps']} |")
        L += ["", "Compare the labels with `abcompare.py --live RUN` (interleaved phases: the most precise A/B we have).", ""]
    if s.get("guard"):
        g = s["guard"]
        L += ["## Copy guard", "", f"{g['copies_per_5s']} page copies per 5 s; pool peak {g['pool_peak']} of "
              f"{g['pool_size']}; full {g['pool_full']} times.", ""]
    L += ["## Hitches (frames ≥ 100 ms in play)", ""]
    if s["hitches"]:
        L += ["| Log s | Worst ms | fps | Likely cause |", "|---|---|---|---|"]
        for h in s["hitches"]:
            L.append(f"| {h['t']:.0f} | {h['worst_ms']:.0f} | {h['fps']:.1f} | {h['cause']} |")
    else:
        L.append("None.")
    L += ["", f"Shaders built while playing: {s['pipelines_in_play']} ({s['pipeline_ms_in_play']} ms).", "",
          "## What this run cannot tell you", ""]
    missing = [name for key, name in [("split", "front/back split (EDEN_NX2_SPLIT_WAITS=1)"),
                                      ("gpu_time", "host GPU time (EDEN_GPU_TIME=1, stderr)"),
                                      ("svcprof", "game thread times (EDEN_GBB_SVC_PROFILE)"),
                                      ("back_calls", "back breakdown (EDEN_GBB_BACK_CALLS)")] if not s["has"][key]]
    L.append("Missing: " + ("; ".join(missing) if missing else "nothing from the standard set") + ".")
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    text = report(sys.argv[1])
    if "--out" in sys.argv:
        open(sys.argv[sys.argv.index("--out") + 1], "w").write(text)
    else:
        sys.stdout.write(text)
