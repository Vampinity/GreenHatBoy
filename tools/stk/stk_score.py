#!/usr/bin/env python3
"""Shared single-run scorer (stk_score.py) for EglantinePS5 Ocarina of Time runs.

Original: waveydude (stk_score.py, 16 Nov 2026).
Run-contract changes: GrowingBlackBeans, 16 Nov 2026, to be offered back to him. Every change is listed
in CHANGES.md; his rules are kept: missing is null with a reason, never 0; every number says where it
came from (`*_source`); fps_mean is kept beside fps_median; sampling windows are recorded.

Reads one run folder - raw or packed, flat or with logs/, .gz or not (runfolder.py) - and emits one
row: run conditions derived from the logs, the ten dossier metrics, the route's scoring windows
(windows.json), and the run-contract checks.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import statistics as st
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from runfolder import RunFolder  # noqa: E402
import route_check  # noqa: E402  (waveydude)

SCORER_VERSION = "stk_score 7 (waveydude 1 + run contract v1 + his route_check + build in the key, 16 Nov 2026)"

# No machine's paths here: the control's env comes from --alpha-env or $STK_ALPHA_ENV.
DEFAULT_ALPHA_ENV = os.environ.get("STK_ALPHA_ENV")
WINDOWS_FILE = Path(__file__).resolve().parent / "windows.json"
HARNESS_KEYS = {"EDEN_TEST_SCRIPT", "EDEN_TEST_BOOT", "EDEN_TEST_DISCARD_SAVE"}
OOM_LOG_CAP = 64  # EDEN_RADV_OUT_OF_MEMORY stops printing after 64 lines per process

VI2_RE = re.compile(
    r"\[\s*([\d.]+)\].*?nx2:vi2 5 s:\s*(\d+)\s*frames,\s*([\d.]+)\s*fps,\s*"
    r"mean\s*([\d.]+)\s*ms,\s*1% low\s*([\d.]+)\s*ms,\s*worst\s*([\d.]+)\s*ms"
)
# The app writes "new" for a store it starts empty (a cold start); "created" kept for older builds.
STAMP_RE = re.compile(
    r"SOURCE_STAMP:\s*id\s+(\S+).*?store\s+(prep_\w+)\s+(reused|created|new)\s+\((\d+)\s+pipelines\)(?:,\s*build\s+(\d+))?"
)
DEVICE_RE = re.compile(r"\(files\s+(\d+)\)\s+(dev[0-9a-f]+)")
TEST_RE = re.compile(r"EDEN_TEST ([a-z_]+)")
TOTAL_PIPES_RE = re.compile(r"Total Pipeline Count:\s*(\d+)")
KNOWN_RE = re.compile(r"Shader preparation: (\d+) pipelines known, (\d+) left to prepare")
OWN_RE = re.compile(r"Shader preparation stats: (\d+) records read \((\d+) own")
DRIVER_LOADED_RE = re.compile(r"Loaded Vulkan driver pipeline cache")
SDK_RE = re.compile(r"sdk_version\s+0x([0-9a-fA-F]+)")
BOOT_BUILD_RE = re.compile(r"diagnostic build\s+(\S+)\s+\(([^)]*)\)")
CENSUS_RE = re.compile(r"^EDEN_MEM_CENSUS\s+n=(\d+)\s+why=(\S+)\s+t_s=([\d.]+)\s+largest=(\d+)")
CENSUS_POOL_RE = re.compile(r"^EDEN_MEM_CENSUS_POOL\s+n=(\d+)\b.*?free_pages=(\d+).*?fragmented=(\d+).*?vma_slack=(\d+)")
LOW_MIB = 16          # "under 16 MiB": the census's own low mark for the largest free block (19 Nov)
CENSUS_EVERY_S = 2.0  # one EDEN_MEM_CENSUS line every 2 s
RADV_MEM_RE = re.compile(r"^RADV_PS5_MEMORY\s+t_s=([\d.]+)\s+pool_mib=(\d+)\s+available_mib=(\d+)")
REFUSED_LARGEST_RE = re.compile(r"the largest (\d+) MiB")
POOL_MEM_RE = re.compile(r"EDEN_MEMORY\s+pool\s+largest\s+free\s+block\s+(\d+)\s+MiB")
FLASH_RE = re.compile(r"\[\s*([\d.]+)\].*EDEN_UP_FLASH\s+frame")
RUNTIME_PIPE_RE = re.compile(r"\[\s*([\d.]+)\].*ReportRuntimePipeline:\s*Graphics pipeline built on the GPU thread")
HITCH_LINE_RE = re.compile(r"EDEN_UP_HITCH(?:_TRACE)?\b.*?(?:hitch_ms|total_ms)=([\d.]+)")
GAME_SPEED_RE = re.compile(r"(?:EDEN_GAME_SPEED|game_speed)[=:\s]+([\d.]+)")
GUEST_START_RE = re.compile(r"^\[\s*([\d.]+)\].*EDEN_GUEST_START")
MARK_RE = re.compile(r"EDEN_TEST (wait_met|wait_skipped|steer_met|script_end|script_done)(?: line=(\d+))? at=([\d.]+)")
CLOSE_RE = re.compile(r"EDEN_AUDIO_PORT_CLOSED")


def parse_env_text(text: str) -> tuple[dict[str, str], str | None]:
    if not text:
        return {}, None
    items: dict[str, str] = {}
    canonical: list[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        items[k.strip()] = v.strip()
        if k.strip() not in HARNESS_KEYS:
            canonical.append(f"{k.strip()}={v.strip()}")
    return items, hashlib.sha256("\n".join(sorted(canonical)).encode("utf-8")).hexdigest()[:12]


def percentile(values: list[float], p: float) -> float:
    if not values:
        raise ValueError("empty")
    s = sorted(values)
    pos = (len(s) - 1) * p
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return s[int(pos)]
    return s[lo] * (hi - pos) + s[hi] * (pos - lo)


def decode_sdk_version(hex_str: str) -> str:
    # BCD: 0x09400008 -> 9.40, 0x12400009 -> 12.40, 0x13600007 -> 13.60
    val = hex_str.zfill(8)
    return f"{int(val[0:2])}.{val[2:4]}"


def classify_settings(env: dict[str, str], alpha_env: dict[str, str]) -> tuple[str, list[str]]:
    if not env:
        return "unknown_no_env", []
    if not alpha_env:
        return "env_present_no_ref", []
    diffs = [k for k in sorted(set(env) | set(alpha_env))
             if k not in HARNESS_KEYS and env.get(k) != alpha_env.get(k)]
    if not diffs:
        return "stock_alpha_v40", []
    if diffs == ["EDEN_GUEST_SWAP_AHEAD_MIB"] and env.get("EDEN_GUEST_SWAP_AHEAD_MIB") == "2048":
        return "stock_alpha_v40_13x", diffs
    return f"custom_diff_{len(diffs)}", diffs


def load_windows() -> dict[str, Any]:
    try:
        return json.loads(WINDOWS_FILE.read_text()).get("routes", {})
    except Exception:
        return {}


def identify_route(rf: RunFolder, env: dict[str, str]) -> tuple[str | None, str | None, str]:
    """(route key in windows.json, script sha1[:12], source)."""
    script_text, source = "", "missing"
    name = env.get("EDEN_TEST_SCRIPT")
    for cand in ("script.txt", name):
        if cand and rf.has(cand):
            script_text, source = rf.text(cand), f"file.{cand}"
            break
    sha = hashlib.sha1(script_text.encode("utf-8")).hexdigest()[:12] if script_text else None
    for key, r in load_windows().items():
        if (sha and sha in r.get("sha1", [])) or (name and name in r.get("names", [])):
            return key, sha, source if sha in r.get("sha1", []) else "env.EDEN_TEST_SCRIPT_name"
    return None, sha, source


def window_lines(defn: dict[str, Any]) -> list[int]:
    """The script lines a window is placed by."""
    return [defn[k] for k in ("anchor_line", "start_line", "end_line", "after_line") if k in defn]


def window_value(defn: dict[str, Any], vi: list[tuple], marks: dict[int, float], last_t: float | None,
                 skipped: set[int] | frozenset = frozenset()):
    """One window's value from the 5 s lines (app clock); (value, n, reason). A window placed by a line that was
    skipped (a MAYBE that timed out) has no value: the place it measures was not reached or not seen."""
    stat = st.median if defn.get("stat") == "median" else st.mean
    kind = defn["kind"]
    if not defn.get("clock_marks"):
        for ln in window_lines(defn):
            if ln in skipped and ln not in marks:
                return None, 0, f"anchor_skipped_line_{ln}"
    if kind == "stamped":
        a = marks.get(defn["anchor_line"])
        if a is None:
            return None, 0, f"missing_mark_line_{defn['anchor_line']}"
        sel = [w[2] for w in vi if a + defn["from_s"] <= w[0] <= a + defn["to_s"]]
    elif kind in ("whole", "between"):
        s = marks.get(defn["start_line"])
        e = marks.get(defn["end_line"])
        if s is None or e is None:
            return None, 0, f"missing_mark_line_{defn['start_line'] if s is None else defn['end_line']}"
        s += defn.get("start_offset_s", 0)
        sel = [w[2] for w in vi if w[0] - 5.0 >= s and w[0] <= e]
    elif kind == "after_load_low":
        e = marks.get(defn["after_line"])
        if e is None:
            return None, 0, f"missing_mark_line_{defn['after_line']}"
        after = [w for w in vi if w[0] > e]
        fast = [w for w in after if w[2] >= defn["fast_fps"]]
        if not fast:
            return None, 0, "missing_fast_load_stretch"
        f_t = fast[-1][0]
        cand = [w for w in after if f_t < w[0] <= f_t + defn["low_within_s"]]
        if not cand:
            return None, 0, "missing_low_line_in_load"
        low_t = min(cand, key=lambda w: w[2])[0]
        sel = [w[2] for w in vi if w[0] >= low_t + defn["from_low_s"]]
    else:
        return None, 0, f"unknown_window_kind_{kind}"
    if not sel:
        return None, 0, "missing_no_5s_lines_in_window"
    return round(stat(sel), 2), len(sel), "eden_log.nx2_vi2_5s"


def score_run(run_dir: str | Path, alpha_env_path: str | Path | None = DEFAULT_ALPHA_ENV) -> dict[str, Any]:
    rf = RunFolder(run_dir)
    eden_lines = rf.lines("eden_log.txt")
    stderr_lines = rf.lines("stderr.log")
    boot_text = rf.text("boot-trace.txt")

    run_meta: dict[str, Any] = {}
    if rf.has("run.json"):
        try:
            run_meta = json.loads(rf.text("run.json"))
        except Exception:
            run_meta = {}
    declared: dict[str, Any] = {}
    if rf.has("declared.json"):
        try:
            declared = json.loads(rf.text("declared.json"))
        except Exception:
            declared = {}

    env, env_hash = parse_env_text(rf.text("env.txt"))
    alpha_env: dict[str, str] = {}
    if alpha_env_path and Path(alpha_env_path).is_file():
        alpha_env, _ = parse_env_text(Path(alpha_env_path).read_text(errors="replace"))
    settings_profile, env_diffs = classify_settings(env, alpha_env)

    # --- Firmware: from the log only (sdk_version). No address maps: an address never goes in a run.
    firmware, firmware_source = None, "missing_no_sdk_version_line"
    for src, text in (("boot-trace.sdk_version", boot_text), ("log.sdk_version", "\n".join(eden_lines[:3000] + stderr_lines[:3000]))):
        m = SDK_RE.search(text)
        if m:
            firmware, firmware_source = decode_sdk_version(m.group(1)), src
            break

    # --- Build: version line with compile time (tells T185 from T186), plus the store's build number.
    build, build_source = None, "missing"
    build_version_line = None
    m = BOOT_BUILD_RE.search(boot_text)
    if m:
        build_version_line = f"{m.group(1)} ({m.group(2)})"
    shader_store = cache_store_state = None
    store_pipelines = None
    translation_id = device_id = translation_files = None
    cache_source = "missing_no_source_stamp_line"
    for l in eden_lines[:3000]:
        m = STAMP_RE.search(l)
        if m:
            tx_id, store_id, state, pipe_cnt, bnum = m.groups()
            translation_id = tx_id
            d = DEVICE_RE.search(l)
            if d:
                translation_files, device_id = int(d.group(1)), d.group(2)
            shader_store = store_id
            cache_store_state = "new" if state in ("new", "created") else "reused"
            store_pipelines = int(pipe_cnt)
            cache_source = "eden_log.SOURCE_STAMP"
            if bnum:
                build, build_source = f"build_{bnum}", "eden_log.SOURCE_STAMP"
            break
    if build is None and run_meta.get("build"):
        b = run_meta["build"]
        build = (b.get("tag") or b.get("commit") or json.dumps(b, sort_keys=True)) if isinstance(b, dict) else str(b)
        build_source = "run_json.build"

    # --- Cache state, derived (waveydude's store record + what runAC2 showed it needs).
    total_pipelines = None
    for l in eden_lines[:5000]:
        m = TOTAL_PIPES_RE.search(l)
        if m:
            total_pipelines = int(m.group(1))
            break
    driver_cache_loaded = any(DRIVER_LOADED_RE.search(l) for l in eden_lines[:5000]) if eden_lines else None
    # The warm boot (19 Nov): what the start booted with besides the store. A warm control restores the whole cache
    # first, and the boot proves it: every store pipeline known, none left to prepare, and the app's own records and
    # the total count the same as the control's (ours: 80770 / 0 / 3 own / 4). N alone doesn't show it.
    pipelines_known = left_to_prepare = own_records = None
    for l in eden_lines[:5000]:
        if pipelines_known is None and (m := KNOWN_RE.search(l)):
            pipelines_known, left_to_prepare = int(m.group(1)), int(m.group(2))
        if own_records is None and (m := OWN_RE.search(l)):
            own_records = int(m.group(2))
        if pipelines_known is not None and own_records is not None:
            break
    if cache_store_state is None:
        cache_class = None
    elif cache_store_state == "reused":
        cache_class = "warm"
    elif (total_pipelines or 0) == 0 and not driver_cache_loaded:
        cache_class = "cold"
    else:
        cache_class = "half"  # store new, but pipelines or a driver cache came from an earlier start

    # --- Route, clocks, script marks.
    route_key, script_sha, route_source = identify_route(rf, env)
    route = env.get("EDEN_TEST_SCRIPT") or route_key
    guest_start_t = None
    for l in eden_lines[:3000]:
        m = GUEST_START_RE.match(l)
        if m:
            guest_start_t = float(m.group(1))
            break
    marks: dict[int, float] = {}       # lines met (wait_met, steer_met, script_end): where a window can anchor
    skipped_lines: set[int] = set()     # lines logged as wait_skipped: never an anchor (PR #18 review, point 4) ...
    skipped_at: dict[int, float] = {}   # ... except in a window whose lines are clock marks (windows.json)
    script_done_t = None
    waits_met = 0
    for l in stderr_lines:
        m = MARK_RE.search(l)
        if not m:
            continue
        kind, line, at = m.group(1), m.group(2), float(m.group(3))
        app_t = at + (guest_start_t or 0.0)
        if line and kind == "wait_skipped":
            skipped_lines.add(int(line))   # a MAYBE that timed out: logged with its line, but nothing was seen there
            skipped_at.setdefault(int(line), app_t)
        elif line:
            marks.setdefault(int(line), app_t)
        if kind == "wait_met":
            waits_met += 1
        if kind == "script_done":
            script_done_t = app_t

    # --- Route proof (waveydude's route_check.py): did the run actually run its route? A failed WAIT or
    # STEER ends in a timeout; a route whose last stretch nothing confirms is `tail_unverified`.
    test_counts: dict[str, int] = {}
    for l in stderr_lines:
        m = TEST_RE.search(l)
        if m:
            test_counts[m.group(1)] = test_counts.get(m.group(1), 0) + 1
    route_text = (rf.text("script.txt") or rf.text("route.txt")
                  or (rf.text(env["EDEN_TEST_SCRIPT"]) if env.get("EDEN_TEST_SCRIPT") else ""))
    rc = route_check.check("\n".join(stderr_lines), route_text or None)
    route_result, route_reason = rc["route_result"], rc["route_reason"]
    # Ran to its end (confirmed or not) / did not / no script.
    route_completed = None if route_result == "manual" else route_result in ("completed", "tail_unverified")

    # --- Start and end, derived.
    if "opening the launcher" in boot_text:
        start_method = "launcher"
    elif env.get("EDEN_TEST_BOOT") and boot_text:
        start_method = "test_boot"
    else:
        start_method = None
    crash_files, other_crash_files = rf.crash_files()
    last_t = rf.last_app_time()
    if crash_files:
        end_kind = "crash"
    elif any(CLOSE_RE.search(l) for l in eden_lines[-3000:]):
        end_kind = "app_closed"   # a normal close: test-quit, or the app closed properly
    elif eden_lines:
        end_kind = "log_cut"      # the log stops with no close lines (stopped by hand, or copied while running)
    else:
        end_kind = None
    tail_after_script_s = round(last_t - script_done_t, 1) if (last_t is not None and script_done_t is not None) else None

    crash_text = crash_files[-1].read_text(errors="replace") if crash_files else ""
    mode_resolution, mode_source = None, "missing_not_logged_in_eden_log"
    if crash_text:
        m = re.search(r"^running:\s*game\s+.*?,\s*Vulkan,\s*(.+)$", crash_text, re.M)
        if m:
            mode_resolution, mode_source = m.group(1).strip(), f"crash_file.{crash_files[-1].name}"

    session_age_s, session_age_source = None, "missing"
    cands = []
    if last_t is not None:
        cands.append(("eden_log.last_timestamp", last_t))
    if crash_text:
        m = re.search(r",\s*(\d+)\s*s after the app started", crash_text)
        if m:
            cands.append((f"crash_file.{crash_files[-1].name}", float(m.group(1))))
    if cands:
        session_age_source, session_age_s = max(cands, key=lambda x: x[1])

    # --- 5 s windows.
    vi = []
    for l in eden_lines:
        m = VI2_RE.search(l)
        if m:
            t, frames, fps, mean_ms, low1_ms, worst_ms = (float(x) for x in m.groups())
            vi.append((t, int(frames), fps, mean_ms, low1_ms, worst_ms))
    play_start = (guest_start_t + 5.0) if guest_start_t is not None else 65.0
    play_end = (script_done_t + 10.0) if script_done_t is not None else None  # where test-quit ends a run
    play = [w for w in vi if w[0] >= play_start and (play_end is None or w[0] <= play_end)]
    sampling_window = (f"nx2:vi2_5s {play_start:.1f}s..{'end' if play_end is None else f'{play_end:.1f}s'} (n={len(play)})"
                       if play else "none")

    fps_mean = fps_median = fps_p10 = worst_frame_ms = None
    fps_source = "missing_no_vi2_5s_windows"
    if play:
        fps_vals = [w[2] for w in play]
        fps_mean = round(st.mean(fps_vals), 2)
        fps_median = round(st.median(fps_vals), 2)
        fps_p10 = round(percentile(fps_vals, 0.10), 2)
        worst_frame_ms = round(max(w[5] for w in play), 1)
        fps_source = "eden_log.nx2_vi2_5s" + ("_to_script_done+10s" if play_end is not None else "_to_log_end")

    # Route windows (the gate's numbers).
    route_windows: dict[str, Any] = {}
    anchors_skipped: list[str] = []     # "window:line" for each window whose anchor was skipped
    routes = load_windows()
    if route_key and route_key in routes:
        for wname, defn in routes[route_key]["windows"].items():
            if route_completed is False:
                v, n, why = None, 0, f"route_{route_result}: {route_reason}"  # not scored: the route did not run to its end
            else:
                placed = {**skipped_at, **marks} if defn.get("clock_marks") else marks
                # The open-ended window (after_load_low: "to the end") stops where test-quit ends a run, script_done
                # + 10 s (Vampinity, PR #20); it used to run to the log's end, so a start quit later got more tail.
                # The other kinds end at their own marks or stamps (some, like new-game's village, by design a few
                # seconds past script_done), so they are left as they were.
                vi_win = ([w for w in vi if play_end is None or w[0] <= play_end]
                          if defn.get("kind") == "after_load_low" else vi)
                v, n, why = window_value(defn, vi_win, placed, last_t, skipped_lines)
                if why.startswith("anchor_skipped_line_"):
                    anchors_skipped.append(f"{wname}:{why.rsplit('_', 1)[1]}")
            route_windows[f"win_{wname}_fps"] = v
            route_windows[f"win_{wname}_n"] = n
            route_windows[f"win_{wname}_source"] = why

    # The load (MEASURING.md: "black screen at each load"), for routes with a load window: from the load's mark to the
    # start of the first 5 s line from which play holds at half the after-load fps or more for 15 s. It takes in the
    # black (about 60 fps) and the stall after it (0-6 fps) and ends when play has settled; the search starts after the
    # black's last 5 s line, as the after_load_low window does. 5 s resolution.
    load_s, load_source = None, "no_load_window_on_this_route"
    for wname, defn in (routes.get(route_key, {}) if route_key else {}).get("windows", {}).items():
        if defn.get("kind") != "after_load_low":
            continue
        e, steady = marks.get(defn["after_line"]), route_windows.get(f"win_{wname}_fps")
        if e is None or not steady:
            load_s, load_source = None, f"missing_mark_or_window_{wname}"
            break
        after = [w for w in vi if w[0] > e and (play_end is None or w[0] <= play_end)]
        fast = [w for w in after if w[2] >= defn["fast_fps"]]   # the black, as the load window finds it
        if not fast:
            load_source = "missing_fast_load_stretch"
            break
        after = [w for w in after if w[0] > fast[-1][0]]
        for i, w in enumerate(after):
            span = [x for x in after[i:] if x[0] <= w[0] + 15.0]
            if len(span) >= 3 and all(x[2] >= steady / 2 for x in span):
                load_s, load_source = round(max(0.0, w[0] - 5.0 - e), 1), f"eden_log.nx2_vi2_5s_after_line_{defn['after_line']}"
                break
        else:
            load_source = "missing_play_never_settled"
        break

    shader_builds_in_play, shader_builds_source = None, "missing_no_eden_log"
    if eden_lines:
        shader_builds_in_play = sum(1 for l in eden_lines
                                    if (m := RUNTIME_PIPE_RE.match(l)) and float(m.group(1)) >= play_start)
        shader_builds_source = "eden_log.ReportRuntimePipeline_after_play_start"

    # Memory: his fallback chain for the row, plus the driver line on its own so that two runs can
    # always be compared on the same source (the two lines disagree on a run's minimum).
    census = [int(m.group(4)) for l in stderr_lines if (m := CENSUS_RE.match(l))]
    radv = [int(m.group(3)) for l in stderr_lines if (m := RADV_MEM_RE.match(l))]
    largest_free_block_mib, largest_free_block_source = None, "missing"
    if census:
        largest_free_block_mib, largest_free_block_source = min(census), "stderr.EDEN_MEM_CENSUS_min"
    elif radv:
        largest_free_block_mib, largest_free_block_source = min(radv), "stderr.RADV_PS5_MEMORY_min"
    else:
        pool = [int(m.group(1)) for l in stderr_lines if (m := POOL_MEM_RE.search(l))]
        if pool:
            largest_free_block_mib, largest_free_block_source = min(pool), "stderr.EDEN_MEMORY_pool_min"
        elif crash_text:
            m = re.search(r"largest free block\s+(\d+)\s+MiB", crash_text)
            if m:
                largest_free_block_mib, largest_free_block_source = int(m.group(1)), f"crash_file.{crash_files[-1].name}"
    driver_free_min = min(radv) if radv else None

    # Memory at the wall (19 Nov, Fable's check of the Phase 4 plan): the free block's minimum sits at 0-2 MiB on the
    # field route, so it can't show a change for the worse. Three numbers that can, all from lines the alpha logs:
    # - refused_pool_events: EDEN_REFUSED_POOL lines (the pool refused an allocation; not capped like the OOM lines);
    # - seconds_under_16_mib: census lines whose largest free block is under 16 MiB, at 2 s each;
    # - stranded_at_low_mib: at the census with the lowest largest free block, what is free but unusable: the heap's
    #   free pages + fragmented + the GPU blocks' slack (the same pool line memmap.py reads).
    # 20 Nov, after Vampinity's review of PR #24:
    # - They stop where test-quit ends a run, like fps (point 2). The census clock (t_s) runs about 13 s behind the
    #   script's, so the cut is by log order: everything up to the script_done line, then the census lines of the
    #   next 10 s, counted on their own clock from the first census line after it (five lines at the 2 s cadence).
    #   Refusal lines carry no time and stop at the same place in the log. A start with no census after script_done
    #   stops at the script_done line; one with no script_done reads to the log's end, as fps does.
    # - A refusal line whose largest free block is 16 MiB or more is not counted (point 1): EDEN_NX2_POOL_WALK=1 prints
    #   the pool line every 20 s with nothing refused (his run215: 16 of them, 7.5-11.4 GiB free).
    # - stranded_at_low_mib is the median over the census lines tied at the lowest block (point 4): docked, many tie
    #   at 0 MiB, and the first of them is the least steady choice.
    mem_lines, memory_window = stderr_lines, "to_log_end"
    sd_idx = next((i for i, l in enumerate(stderr_lines) if "EDEN_TEST script_done" in l), None)
    if sd_idx is not None:
        cut_idx, first_after = sd_idx + 1, None
        for i in range(sd_idx + 1, len(stderr_lines)):
            m = CENSUS_RE.match(stderr_lines[i])
            if not m:
                continue
            t = float(m.group(3))
            if first_after is None:
                first_after = t
            elif t >= first_after + 10.0:
                cut_idx = i
                break
        else:
            if first_after is not None:
                cut_idx = len(stderr_lines)
        mem_lines = stderr_lines[:cut_idx]
        memory_window = "to_script_done+10s" if first_after is not None else "to_script_done_line"
    refused_pool_events = None
    if stderr_lines:
        refused_pool_events = 0
        for l in mem_lines:
            if "EDEN_REFUSED_POOL" in l:
                m = REFUSED_LARGEST_RE.search(l)
                if m is None or int(m.group(1)) < LOW_MIB:
                    refused_pool_events += 1
    census_rows = [(int(m.group(1)), int(m.group(4))) for l in mem_lines if (m := CENSUS_RE.match(l))]
    seconds_under_16_mib = (round(sum(1 for _, big in census_rows if big < LOW_MIB) * CENSUS_EVERY_S, 1)
                            if census_rows else None)
    stranded_at_low_mib = None
    if census_rows:
        low = min(big for _, big in census_rows)
        tied = {n for n, big in census_rows if big == low}
        stranded = [int(m.group(2)) + int(m.group(3)) + int(m.group(4))
                    for l in mem_lines if (m := CENSUS_POOL_RE.match(l)) and int(m.group(1)) in tied]
        if stranded:
            v = st.median(stranded)
            stranded_at_low_mib = int(v) if v == int(v) else round(v, 1)

    hitch_ms_per_min, hitch_source = None, "missing_no_flight_recorder_or_hitch_trace"
    hitch_vals = [float(m.group(1)) for l in (eden_lines + stderr_lines) if (m := HITCH_LINE_RE.search(l))]
    if hitch_vals and session_age_s:
        hitch_ms_per_min, hitch_source = round(sum(hitch_vals) / (session_age_s / 60.0), 2), "log.EDEN_UP_HITCH"

    flashes_per_min, flashes_source = None, "missing_no_60fps_capture_and_counter_off"
    if env.get("EDEN_UP_FLASH_COUNT") == "1" and eden_lines and play:
        flash_ts = [float(m.group(1)) for l in eden_lines if (m := FLASH_RE.match(l)) and float(m.group(1)) >= play_start]
        dur = max((play[-1][0] - play_start) / 60.0, 1e-6)
        flashes_per_min, flashes_source = round(len(flash_ts) / dur, 2), "eden_log.EDEN_UP_FLASH_uncalibrated_log_only"

    game_speed, game_speed_source = None, "missing_not_instrumented_in_t186"
    gs_vals = [float(m.group(1)) for l in (eden_lines + stderr_lines) if (m := GAME_SPEED_RE.search(l))]
    if gs_vals:
        game_speed, game_speed_source = round(st.median(gs_vals), 3), "log.game_speed_median"

    radv_oom = sum("EDEN_RADV_OUT_OF_MEMORY" in l for l in stderr_lines) if stderr_lines else None
    oom_device = sum("OUT_OF_DEVICE_MEMORY" in l for l in (eden_lines + stderr_lines))
    survival_result, survival_source = "unknown", "missing"
    crash_class, crash_source = "none", "no_crash_evidence"
    if crash_files:
        survival_result, survival_source = "crashed", f"crash_file.{crash_files[-1].name}"
        m_reason = re.search(r"^reason:\s*(.+)$", crash_text, re.M)
        m_what = re.search(r"^what:\s*(.+)$", crash_text, re.M)
        crash_class = (m_reason or m_what).group(1).strip() if (m_reason or m_what) else "crash_file_present"
        crash_source = f"crash_file.{crash_files[-1].name}"
    elif oom_device > 0:
        survival_result, survival_source = "crashed", "log.OUT_OF_DEVICE_MEMORY"
        crash_class = crash_source = "VK_ERROR_OUT_OF_DEVICE_MEMORY"
    elif script_done_t is not None:
        survival_result, survival_source = "completed", "stderr.EDEN_TEST_script_done"
    elif any("timeout" in l and "EDEN_TEST" in l for l in stderr_lines):
        survival_result, survival_source = "timeout", "stderr.EDEN_TEST_timeout"
    elif marks:
        survival_result, survival_source = "stopped_early", "stderr.EDEN_TEST_no_script_done"
    elif run_meta.get("was_running_at_stop"):
        survival_result, survival_source = "running_at_pull", "run_json.was_running_at_stop"
    elif run_meta.get("end"):
        survival_result, survival_source = str(run_meta["end"])[:40], "run_json.end"

    # No crash file and no end line: whether the run crashed is unknown, so the crash class is too.
    if survival_result in ("unknown", "running_at_pull") and crash_class == "none":
        crash_class, crash_source = None, "missing_survival_unknown"

    # --- Run-contract checks.
    intended = declared.get("intended_cache")
    cache_matches_intent = (None if not intended or cache_class is None
                            else (intended == "any" or intended == cache_class))
    start_ok = None if start_method is None else start_method == "test_boot"
    # The app closed normally (test-quit, or closed properly), so its caches were saved and the next
    # start's cache state is known. How long after the script it closed is recorded, not judged: whole-run
    # figures are cut at script_done + 10 s, so no number depends on it (dropped 16 Nov by GrowingBlackBeans).
    end_ok = None if end_kind is None else end_kind == "app_closed"
    env_ok = settings_profile in ("stock_alpha_v40", "stock_alpha_v40_13x") or len(env_diffs) <= 1 if alpha_env else None
    intent_ok = True if not intended else bool(cache_matches_intent)  # undeclared runs are not failed on intent
    window_comparable = (intent_ok and bool(env_ok) and survival_result == "completed"
                         and route_completed is True and cache_class in ("cold", "warm") and not anchors_skipped)
    # The build the run actually ran. The boot trace's version + compile time tells two builds apart
    # even when they share a store, which is the case waveydude raised on PR #11: with the translation
    # id forced to keep a store, A186-keep ... keep4 all carry src116270f1... with different code. The
    # store stamp's own build number names whichever build wrote the store, not this one, so it is not
    # used here; a build declared in run.json is, since the runner states it.
    build_key = build_version_line or (build if build_source == "run_json.build" else None)
    # Two rows may face each other only with the same key (waveydude): the same route, the same build,
    # the same translation id (a new build can start a new store with an identical env), the same store,
    # and the same kind of control - cold against cold, warm against warm. Firmware too: the gate judges
    # a change against the control on the same console, and our 13.60 cold starts sit ~280 MiB tighter
    # than 12.40's.
    comparison_key = "|".join(str(x) for x in
                              (route_key, firmware, build_key, translation_id, shader_store, cache_class)) \
        if (route_key and firmware and build_key and translation_id and shader_store and cache_class) else None
    control_eligible = bool(declared.get("control")) and window_comparable and bool(start_ok) and bool(end_ok)

    row: dict[str, Any] = {
        "run_id": rf.path.name,
        "run_path": str(rf.path),
        "scorer": SCORER_VERSION,
        "firmware": firmware, "firmware_source": firmware_source,
        "build": build, "build_source": build_source, "build_version_line": build_version_line,
        "build_key": build_key,
        "route": route, "route_key": route_key, "script_sha1": script_sha, "route_source": route_source,
        "settings_profile": settings_profile, "env_hash": env_hash,
        "env_diff_keys": ";".join(env_diffs) if env_diffs else "",
        "translation_id": translation_id, "translation_files": translation_files, "device_id": device_id,
        "shader_store": shader_store, "store_state": cache_store_state, "store_pipelines": store_pipelines,
        "total_pipeline_count": total_pipelines, "driver_cache_loaded": driver_cache_loaded,
        "pipelines_known": pipelines_known, "left_to_prepare": left_to_prepare, "own_records": own_records,
        "cache_class": cache_class, "cache_source": cache_source,
        "start_method": start_method, "game_start_app_s": guest_start_t,
        "end_kind": end_kind, "tail_after_script_s": tail_after_script_s,
        "crash_files_ignored": other_crash_files,
        "mode_resolution": mode_resolution, "mode_source": mode_source,
        "session_age_s": round(session_age_s, 1) if session_age_s is not None else None,
        "session_age_source": session_age_source,
        "sampling_window": sampling_window,
        "fps_mean": fps_mean, "fps_median": fps_median, "fps_p10": fps_p10, "worst_frame_ms": worst_frame_ms,
        "fps_source": fps_source,
        "shader_builds_in_play": shader_builds_in_play, "shader_builds_source": shader_builds_source,
        "largest_free_block_min_mib": largest_free_block_mib, "largest_free_block_source": largest_free_block_source,
        "refused_pool_events": refused_pool_events, "seconds_under_16_mib": seconds_under_16_mib,
        "stranded_at_low_mib": stranded_at_low_mib, "memory_window": memory_window, "load_s": load_s, "load_source": load_source,
        "largest_free_block_driver_min_mib": driver_free_min,
        # A count at the cap is a floor, not a count: written ">=64" so no reader can compare two floors.
        "radv_oom_events": (f">={OOM_LOG_CAP}" if (radv_oom is not None and radv_oom >= OOM_LOG_CAP) else radv_oom),
        "radv_oom_capped": (radv_oom is not None and radv_oom >= OOM_LOG_CAP),
        "hitch_ms_per_min": hitch_ms_per_min, "hitch_source": hitch_source,
        "flashes_per_min": flashes_per_min, "flashes_source": flashes_source,
        "game_speed": game_speed, "game_speed_source": game_speed_source,
        "survival_result": survival_result, "survival_source": survival_source,
        "crash_class": crash_class, "crash_source": crash_source,
        "waits_met": waits_met, "waits_skipped": test_counts.get("wait_skipped", 0),
        "wait_timeouts": test_counts.get("wait_timeout", 0), "steer_timeouts": test_counts.get("steer_timeout", 0),
        "route_result": route_result, "route_reason": route_reason, "route_completed": route_completed,
        "anchors_skipped": anchors_skipped,
        "steer_legs_met": rc["steer_legs_met"], "steer_legs_expected": rc["steer_legs_expected"],
        "required_waits_met": rc["required_waits_met"], "required_waits_expected": rc["required_waits_expected"],
        "route_sha256_12": rc["route_sha256_12"],
        "declared_control": declared.get("control"), "declared_cache": intended,
        "cache_matches_intent": cache_matches_intent, "start_ok": start_ok, "end_ok": end_ok, "env_ok": env_ok,
        "window_comparable": window_comparable, "control_eligible": control_eligible,
        "control_kind": cache_class if cache_class in ("cold", "warm") else None,
        "comparison_key": comparison_key,
    }
    row.update(route_windows)
    return row


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Score one or more EglantinePS5 run folders (raw or packed).")
    ap.add_argument("run_dirs", nargs="+", help="Path(s) to run folders")
    ap.add_argument("--format", choices=("json", "csv"), default="json")
    ap.add_argument("--alpha-env", default=DEFAULT_ALPHA_ENV,
                    help="the control's env.txt (default: $STK_ALPHA_ENV)")
    ap.add_argument("--out", help="Optional output file path")
    args = ap.parse_args(argv)

    rows = [score_run(p, args.alpha_env) for p in args.run_dirs]
    if args.format == "json":
        txt = json.dumps(rows[0] if len(rows) == 1 else rows, indent=2) + "\n"
    else:
        import io
        keys: list[str] = []
        for r in rows:
            keys += [k for k in r if k not in keys]
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=keys)
        writer.writeheader()
        writer.writerows(rows)
        txt = buf.getvalue()
    if args.out:
        Path(args.out).write_text(txt)
    else:
        sys.stdout.write(txt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
