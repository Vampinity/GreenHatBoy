#!/usr/bin/env python3
"""Offline crash census; Python 3 standard library only. See README.md in this folder."""
import argparse
import csv
import hashlib
import json
import math
import re
import sys
import tempfile
import unittest
from collections import Counter, defaultdict
from pathlib import Path

UNKNOWN = 'unknown'
KINDS = ('out of memory', 'device lost', 'hang or watchdog', 'CPU JIT fault', 'other')
BUCKETS = ('0–1', '1–2', '2–5', '5–10', '10–20', '20–60', '60+', UNKNOWN)
FIELDS = (
    'crash_id', 'run_id', 'batch', 'kind', 'classification_confidence',
    'classification_evidence', 'build', 'build_label', 'build_source',
    'script', 'place', 'last_marker', 'marker_seconds', 'marker_source',
    'seconds_into_session', 'minutes_into_session', 'minute_bucket', 'time_source',
    'thread', 'reason', 'where', 'signature', 'request_kind', 'request_size',
    'request_bytes', 'request_evidence', 'control_arm', 'env_diff',
    'env_diff_source', 'association', 'source_files',
)


def read_text(path):
    return path.read_text(encoding='utf-8', errors='replace') if path.is_file() else ''


def read_json(path, warnings):
    if not path.is_file():
        return {}
    try:
        return json.loads(read_text(path))
    except (ValueError, OSError) as exc:
        warnings.append('{}: {}'.format(path.as_posix(), exc))
        return {}


def clean(value):
    return str(value).strip() if value is not None and str(value).strip() not in ('', '?') else UNKNOWN


def headers(text):
    return dict(re.findall(r'^([a-z_]+):[ \t]*(.*)$', text, re.M))


def number(value):
    try:
        n = float(value)
        return n if math.isfinite(n) and n >= 0 else None
    except (TypeError, ValueError):
        return None


def session_seconds(meta, result, report):
    for source, text in [('crash time', str(meta.get('time', ''))),
                         ('report Duration', '\n'.join(re.findall(r'^Duration:.*$', report, re.M)))]:
        m = re.search(r'(\d+(?:\.\d+)?)\s*s(?:econds)? after the app started', text)
        if m:
            return float(m[1]), source
    n = number(result.get('seconds'))
    return (n, 'result.seconds (time of observed failure)') if n is not None else (None, UNKNOWN)


def minute_bucket(seconds):
    if seconds is None:
        return UNKNOWN
    for ceiling, label in zip((60, 120, 300, 600, 1200, 3600), BUCKETS):
        if seconds < ceiling:
            return label
    return '60+'


def normalise(text):
    text = re.sub(r'^\s*\[\s*\d+(?:\.\d+)?\]\s*', '', text)
    # Module-relative offsets identify native frames; absolute addresses vary per run.
    text = re.sub(r'eboot\+(0x[0-9a-f]+)', lambda m: 'eboot+@' + m[1].lower(), text, flags=re.I)
    text = re.sub(r'(?<!@)\b0x[0-9a-f]+\b', '<addr>', text, flags=re.I).replace('eboot+@', 'eboot+')
    text = re.sub(r'\b\d+(?:\.\d+)?\b', '<n>', text)
    return re.sub(r'\s+', ' ', text).strip()


def classify(meta, detail):
    terminal = ' '.join(str(meta.get(k, '')) for k in ('reason', 'what')).strip() or detail
    where, thread = str(meta.get('where', '')), str(meta.get('thread', ''))
    if re.search(r'VK_ERROR_DEVICE_LOST|device lost|GPU (?:hang|reset)', terminal, re.I):
        return 'device lost', 'reported', terminal.strip()
    if re.search(r'VK_ERROR_OUT_OF_(?:DEVICE|HOST)_MEMORY|\bbad_alloc\b|out of memory|heap exhausted', terminal, re.I):
        return 'out of memory', 'reported', terminal.strip()
    if re.search(r'SIGSEGV', terminal, re.I):
        explicit_jit = re.search(r'\bJIT\b|generated code', where, re.I) and 'system library or' not in where
        probable_jit = re.search(r'\bCPUCore[_ -]?\d+', thread, re.I) and 'outside the app' in where
        if explicit_jit or probable_jit:
            confidence = 'reported' if explicit_jit else 'inferred'
            evidence = 'SIGSEGV on {} at {}'.format(thread, where)
            if not explicit_jit:
                evidence += '; CPU thread outside eboot suggests JIT; system library not ruled out'
            return 'CPU JIT fault', confidence, evidence
        return 'other', 'reported', terminal.strip()
    if re.search(r'watchdog (?:fired|expired|timeout|triggered)|^(?:watchdog|hang)$|\b(?:hang|hung|freeze)\b|waited \d+(?:\.\d+)? s for the GPU', terminal, re.I):
        return 'hang or watchdog', 'reported', terminal.strip()
    # A terminal buffer refusal is an allocation failure, but an arbitrary upload
    # refusal (e.g. corrupt dimensions) is not evidence of OOM.
    if re.search(r'(?:buffer.*(?:refused|allocation failed)|refused.*buffer).*\d+\s*bytes', terminal, re.I):
        return 'out of memory', 'inferred', terminal.strip()
    return 'other', 'reported' if terminal.strip() else UNKNOWN, clean(terminal)


def request_info(kind, meta, report, log):
    if kind != 'out of memory':
        return (UNKNOWN,) * 5
    reason = str(meta.get('reason', ''))
    token = re.search(r'VK_ERROR_OUT_OF_(?:DEVICE|HOST)_MEMORY|(?:std::)?bad_alloc', reason)
    request_kind = token[0] if token else UNKNOWN
    # Keep exact byte requests separate from rounded MiB amounts in reports.
    patterns = (
        r'(?i)(?:refused\s+(?:a\s+)?buffer(?:\s+of)?|buffer[^\n]{0,100}?(?:refused|failed))[: =]*(\d[\d,]*)\s*bytes',
        r'(?i)(?:operator new|allocation|request)[^\n]{0,80}?(?:size[=: ]+|refused[=: ]+|failed[=: ]+)(\d[\d,]*)\s*(?:bytes|B)\b',
    )
    for text in (str(meta.get('reason', '')), report, log):
        for line in reversed(text.splitlines()):
            for pattern in patterns:
                m = re.search(pattern, line)
                if m:
                    size = int(m[1].replace(',', ''))
                    obj = 'buffer' if 'buffer' in m[0].lower() else 'operator new / allocation'
                    return request_kind, str(size) + ' bytes', str(size), obj, line.strip()
    m = re.search(r'heap could not give (\d+(?:\.\d+)?)\s*(MiB|KiB|GiB|bytes)', report)
    if m:
        exact = m[1] if m[2] == 'bytes' and '.' not in m[1] else UNKNOWN
        return request_kind, '{} {} (reported; may be rounded)'.format(m[1], m[2]), exact, 'operator new / heap', m[0]
    return request_kind, UNKNOWN, UNKNOWN, UNKNOWN, UNKNOWN


def parse_env(value):
    if isinstance(value, dict):
        return {str(k): str(v) for k, v in value.items()}
    lines = value if isinstance(value, list) else str(value).splitlines()
    env = {}
    for line in lines:
        m = re.match(r'\s*(?:export\s+)?([A-Za-z_][A-Za-z_0-9]*)=(.*)$', str(line))
        if m:
            env[m[1]] = m[2].strip()
    return env


def switches(env):
    # The generated script filename differs in every arm; it is harness metadata.
    return {k: v for k, v in env.items() if k not in ('EDEN_TEST_SCRIPT', 'EDEN_TEST_BOOT')}


def plan_entry(plan, result, run):
    matches = [e for e in plan if e.get('name') == result.get('name') or e.get('folder') == run.name]
    return matches[0] if len(matches) == 1 else {}


def environment_diff(run, result, plan, entry):
    candidates = [e for e in plan if e.get('control') is True or e.get('role') == 'control'
                  or re.search(r'(?:^|[-_])control\d*(?:$|[-_])', str(e.get('name', '')), re.I)]
    if not candidates:
        return UNKNOWN, UNKNOWN, UNKNOWN
    actual = read_text(run / 'env.txt')
    current = parse_env(actual) if actual else parse_env(entry['env']) if 'env' in entry else None
    if current is None:
        return UNKNOWN, UNKNOWN, UNKNOWN
    baselines = []
    for candidate in candidates:
        # Match names, never assume the first test is the control.
        control_runs = []
        for p in sorted(run.parent.glob('*/result.json')):
            try:
                d = json.loads(read_text(p))
            except ValueError:
                continue
            if isinstance(d, dict) and d.get('name') == candidate.get('name') and (p.parent / 'env.txt').is_file():
                control_runs.append(switches(parse_env(read_text(p.parent / 'env.txt'))))
        if control_runs:
            baselines.extend(control_runs)
        elif 'env' in candidate:
            baselines.append(switches(parse_env(candidate['env'])))
        else:
            return UNKNOWN, UNKNOWN, UNKNOWN
    # Multiple named controls must agree, otherwise no unique baseline exists.
    if not baselines or any(e != baselines[0] for e in baselines[1:]):
        return UNKNOWN, UNKNOWN, 'ambiguous control environments'
    base, current = baselines[0], switches(current)
    delta = {k: {'control': base.get(k, '<unset>'), 'run': current.get(k, '<unset>')}
             for k in sorted(base.keys() | current.keys()) if base.get(k) != current.get(k)}
    names = ', '.join(str(e.get('name', UNKNOWN)) for e in candidates)
    return names, json.dumps(delta, sort_keys=True, ensure_ascii=False), 'env.txt/plan.env; named batch control'


def build_info(batch, result, report, meta, warnings):
    eboot = read_json(batch / 'eboot.json', warnings) if batch else {}
    summary = read_json(batch / 'summary.json', warnings) if batch else {}
    summary = summary if isinstance(summary, dict) else {}
    label = clean(result.get('build') or summary.get('build') or meta.get('version'))
    if label == UNKNOWN:
        m = re.search(r'\bbuild\s+([^\n,]+)', report)
        label = clean(m[1]) if m else UNKNOWN
    for key in ('sha256', 'sha16', 'hash', 'label', 'build'):
        if isinstance(eboot, dict) and eboot.get(key):
            return clean(eboot[key]), label, 'eboot.json:' + key
    for key in ('eboot_sha256', 'eboot_hash', 'build'):
        if result.get(key):
            return clean(result[key]), label, 'result.json:' + key
    if label != UNKNOWN:
        return label, label, 'summary.json/report.txt/crash version (label only)'
    return UNKNOWN, UNKNOWN, UNKNOWN


def location(report, seconds):
    """Only observed report markers; script comments describe intentions, not progress."""
    candidates = []
    report = report.split('Compared with', 1)[0]
    for index, line in enumerate(report.splitlines()):
        if line.lstrip().startswith(('Settings:', '#')):
            continue
        if not re.search(r'(?i)\b(?:last\s+)?(?:location|scene|load(?:ing)?(?: marker)?|area)\s*[:=]|\b(?:entered|loaded)\s+(?:area|scene|location)\b', line):
            continue
        if re.search(r'no log names the scene|no (?:location|scene)|unknown', line, re.I):
            continue
        # Prefix [123.4], 'at 123 s', '123 s: Location:', or trailing ': 12-34 s'.
        m = re.search(r'\[\s*(\d+(?:\.\d+)?)\]|\bat[= ]+(\d+(?:\.\d+)?)\s*s\b|(?:^|:)\s*(\d+(?:\.\d+)?)(?:-(\d+(?:\.\d+)?))?\s*s\b', line)
        stamp = None
        if m:
            stamp = float(next(g for g in reversed(m.groups()) if g is not None))
            if seconds is not None and stamp > seconds:
                continue
        label = (line[:m.start()] + line[m.end():]).strip(' :') if m else line.strip()
        candidates.append((stamp if stamp is not None else -1, index, label))
    if not candidates:
        return UNKNOWN, UNKNOWN, UNKNOWN
    stamp, index, marker = max(candidates)
    return marker, fmt(stamp) if stamp >= 0 else UNKNOWN, 'report.txt:' + str(index + 1)


def fmt(n):
    return UNKNOWN if n is None else '{:.6f}'.format(n).rstrip('0').rstrip('.')


def script_name(entry, result, run):
    if entry.get('script'):
        return str(entry['script']).replace('\\', '/').rsplit('/', 1)[-1]
    env = parse_env(read_text(run / 'env.txt'))
    if env.get('EDEN_TEST_SCRIPT'):
        return env['EDEN_TEST_SCRIPT'].rsplit('/', 1)[-1]
    for mark in result.get('test_marks', []):
        m = re.search(r'(?:script=|script_start file=)(\S+)', str(mark))
        if m:
            return m[1].rsplit('/', 1)[-1]
    return UNKNOWN


def event_row(event, root, warnings):
    meta = dict(event['meta'])
    run = event.get('run')
    result = event.get('result', {})
    report = read_text(run / 'report.txt') if run else ''
    batch = run.parent if run else None
    plan = read_json(batch / 'plan.json', warnings) if batch else []
    plan = [e for e in plan if isinstance(e, dict)] if isinstance(plan, list) else []
    entry = plan_entry(plan, result, run) if run else {}
    detail = clean(result.get('detail'))
    if not meta.get('reason') and not meta.get('what'):
        meta['what'] = detail if detail != UNKNOWN else str(result.get('ending', ''))
    kind, confidence, evidence = classify(meta, detail)
    seconds, time_source = session_seconds(meta, result, report)
    build, label, build_source = build_info(batch, result, report, meta, warnings)
    script = script_name(entry, result, run) if run else UNKNOWN
    marker, marker_time, marker_source = location(report, seconds)
    place = script if marker == UNKNOWN else (script + ' / ' + marker if script != UNKNOWN else marker)
    where = clean(meta.get('where'))
    reason = clean(meta.get('reason') or meta.get('what') or result.get('detail'))
    # Prefer a stable terminal message; otherwise preserve the native first PC.
    message = reason if meta.get('reason') else (reason + ' @ ' + where if where != UNKNOWN else reason)
    signature = normalise(message)
    logs = []
    for path in event.get('logs', []):
        for line in read_text(path).splitlines():
            m = re.match(r'\[\s*(\d+(?:\.\d+)?)\]', line)
            if seconds is None or not m or float(m[1]) <= seconds + 1:
                if re.search(r'refus|alloc|heap|request', line, re.I):
                    logs.append(line)
    req_kind, req_size, req_bytes, req_object, req_evidence = request_info(kind, meta, report, '\n'.join(logs))
    if req_object != UNKNOWN:
        req_kind = req_kind + ' / ' + req_object if req_kind != UNKNOWN else req_object
    control, diff, diff_source = environment_diff(run, result, plan, entry) if run else (UNKNOWN,) * 3
    row = dict.fromkeys(FIELDS, UNKNOWN)
    row.update(crash_id=event['id'], run_id=run.name if run else UNKNOWN,
               batch=batch.name if batch else UNKNOWN, kind=kind,
               classification_confidence=confidence, classification_evidence=evidence,
               build=build, build_label=label, build_source=build_source,
               script=script, place=place, last_marker=marker, marker_seconds=marker_time,
               marker_source=marker_source, seconds_into_session=fmt(seconds),
               minutes_into_session=fmt(seconds / 60 if seconds is not None else None),
               minute_bucket=minute_bucket(seconds), time_source=time_source,
               thread=re.sub(r'\s*\(0x[0-9a-fA-F]+\)\s*$', '', clean(meta.get('thread'))),
               reason=reason, where=where, signature=signature,
               request_kind=req_kind, request_size=req_size, request_bytes=req_bytes,
               request_evidence=req_evidence, control_arm=control, env_diff=diff,
               env_diff_source=diff_source, association='matched run' if run else 'historical; run unknown',
               source_files='; '.join(sorted(str(p.relative_to(root)) for p in event['sources'])))
    return row


def collect(root):
    warnings = []
    files = sorted(root.rglob('crash-*.txt'))
    primary = [p for p in files if p.name != 'crash-index.txt' and not p.name.endswith('-eden_log.txt')]
    results = {}
    for p in sorted(root.rglob('result.json')):
        d = read_json(p, warnings)
        if isinstance(d, dict):
            results[p.parent] = d
    groups = defaultdict(list)
    for p in primary:
        # A copy with the same event id and payload is one event. Same-name,
        # different-payload files stay distinct and receive a digest suffix.
        digest = hashlib.sha256(read_text(p).encode('utf-8')).hexdigest()
        groups[(p.stem, digest)].append(p)
    events, accounted = [], set()
    names = Counter(stem for stem, _ in groups)
    for (stem, digest), copies in sorted(groups.items()):
        owner = None
        for p in copies:
            d = results.get(p.parent, {})
            crash = d.get('crash') if isinstance(d.get('crash'), dict) else {}
            valid = d.get('ending') == 'crash' or (d.get('ending') == 'system_error' and crash)
            if (valid and (not crash.get('report') or Path(crash['report']).name == p.name)) or p.parent not in results:
                accounted.add(p.parent)
                if owner is None:
                    owner = p.parent
        logs = [p.with_name(p.stem + '-eden_log.txt') for p in copies if p.with_name(p.stem + '-eden_log.txt').is_file()]
        event = {'id': stem + ('-' + digest[:10] if names[stem] > 1 else ''),
                 'meta': headers(read_text(copies[0])), 'sources': copies + logs,
                 'logs': logs[:1]}
        if owner:
            event.update(run=owner, result=results.get(owner, {}))
            accounted.add(owner)
        events.append(event)
    # Explicit failures without a crash report. A script WAIT timeout, time limit,
    # network loss, or unresponsive sandbox alone is not proof of a hang/crash.
    for run, d in sorted(results.items()):
        ending = d.get('ending')
        if run in accounted or ending not in ('crash', 'freeze', 'hang', 'watchdog'):
            continue
        meta = d.get('crash') if isinstance(d.get('crash'), dict) else {}
        events.append({'id': run.name + '-' + str(ending), 'meta': meta,
                       'sources': [run / 'result.json'], 'run': run, 'result': d})
    rows = [event_row(event, root, warnings) for event in events]
    stats = {'matching_files': len(files), 'indexes': sum(p.name == 'crash-index.txt' for p in files),
             'logs': sum(p.name.endswith('-eden_log.txt') for p in files), 'primary_reports': len(primary),
             'unique_reports': len(groups), 'duplicate_copies': len(primary) - len(groups),
             'metadata_only_failures': len(events) - len(groups), 'runs': len(results),
             'historical_events': sum(r['run_id'] == UNKNOWN for r in rows),
             'endings': Counter(d.get('ending', UNKNOWN) for d in results.values())}
    return sorted(rows, key=lambda r: r['crash_id']), stats, sorted(set(warnings))


def md_cell(value):
    return str(value).replace('|', '\\|').replace('\n', ' ').replace('\r', ' ')


def table(headings, rows):
    return ['| ' + ' | '.join(md_cell(x) for x in headings) + ' |',
            '| ' + ' | '.join('---' for _ in headings) + ' |'] + [
                '| ' + ' | '.join(md_cell(x) for x in row) + ' |' for row in rows]


def render(rows, stats, warnings):
    counts = Counter(r['kind'] for r in rows)
    lines = ['# Crash census', '',
             '{} events from {} run results: {} unique crash reports and {} explicit failures without reports.'.format(
                 len(rows), stats['runs'], stats['unique_reports'], stats['metadata_only_failures']), '',
             'File audit: {} crash-*.txt matches = {} indexes + {} companion logs + {} primary reports. '
             '{} duplicate report copies collapsed. {} historical events have no reliable run association.'.format(
                 stats['matching_files'], stats['indexes'], stats['logs'], stats['primary_reports'],
                 stats['duplicate_copies'], stats['historical_events']), '',
             'Counts describe observed failures, not failure rates. Companion logs and crash indexes are evidence, '
             'not additional crashes. Stale result.crash metadata in unstarted/interrupted runs is not attributed to those runs.', '',
             'CPU JIT classifications marked inferred use CPUCore SIGSEGV outside eboot; the report cannot rule out a system library. '
             'Earlier memory pressure does not override a terminal SIGSEGV or SIGABRT. '
             'Place combines the script basename (scenario context, not proof of an exact scene) with any observed location/load marker; markers '
             'are retained separately. Missing evidence is unknown. Time is app-session time, not wall-clock batch time.', '',
             '## Crashes per kind', '']
    lines += table(('Kind', 'Count'), [(k, counts[k]) for k in KINDS] + [('Total', len(rows))])
    lines += ['', '## Crashes per kind per build', '']
    builds = sorted(set(r['build'] for r in rows))
    lines += table(('Build (hash or label)',) + KINDS + ('Total',),
                   [(b,) + tuple(sum(r['build'] == b and r['kind'] == k for r in rows) for k in KINDS)
                    + (sum(r['build'] == b for r in rows),) for b in builds])
    lines += ['', '## Crashes per place (script scenario / observed marker)', '']
    places = Counter(r['place'] for r in rows)
    lines += table(('Place',) + KINDS + ('Total',),
                   [(p,) + tuple(sum(r['place'] == p and r['kind'] == k for r in rows) for k in KINDS) + (n,)
                    for p, n in sorted(places.items(), key=lambda pair: (-pair[1], pair[0]))])
    lines += ['', '## Minutes into session', '', 'Buckets are lower-inclusive and upper-exclusive.', '']
    lines += table(('Minutes',) + KINDS + ('Total',),
                   [(b,) + tuple(sum(r['minute_bucket'] == b and r['kind'] == k for r in rows) for k in KINDS)
                    + (sum(r['minute_bucket'] == b for r in rows),) for b in BUCKETS])
    sigs = Counter(r['signature'] for r in rows)
    lines += ['', '## Top 15 crash signatures', '']
    lines += table(('Signature', 'Count', 'Example run ids'),
                   [(s, n, ', '.join(list(dict.fromkeys(r['run_id'] if r['run_id'] != UNKNOWN else r['crash_id'] + ' (run unknown)'
                                                       for r in rows if r['signature'] == s))[:3]))
                    for s, n in sorted(sigs.items(), key=lambda pair: (-pair[1], pair[0]))[:15]])
    lines += ['', '## Recovery coverage', '']
    coverage = ('build', 'script', 'last_marker', 'minutes_into_session', 'thread', 'env_diff')
    lines += table(('Field', 'Recovered', 'Unknown'),
                   [(k, sum(r[k] != UNKNOWN for r in rows), sum(r[k] == UNKNOWN for r in rows)) for k in coverage])
    lines += ['', '{} CPU JIT classifications are inferred. {} / {} OOM events have a recovered request size; '
              'rounded sizes are not converted into invented exact byte counts.'.format(
                  sum(r['kind'] == 'CPU JIT fault' and r['classification_confidence'] == 'inferred' for r in rows),
                  sum(r['kind'] == 'out of memory' and r['request_size'] != UNKNOWN for r in rows), counts['out of memory']), '',
              '## Run endings (input audit)', '']
    lines += table(('Ending', 'Runs'), sorted(stats['endings'].items(), key=lambda pair: (-pair[1], pair[0])))
    lines += ['', 'Only explicit crash/freeze/hang/watchdog results add events when no report exists. '
              'Time limits, script WAIT timeouts, network/no_answer, restart and system_error alone are not classified as crashes.', '',
              '## Input warnings', '']
    lines += ['- ' + w for w in warnings] if warnings else ['None.']
    return '\n'.join(lines) + '\n'


def write_outputs(rows, stats, warnings, output):
    output.mkdir(parents=True, exist_ok=True)
    with (output / 'crashes.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    (output / 'crash-census.md').write_text(render(rows, stats, warnings), encoding='utf-8')


def self_test():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CensusTests)
    return unittest.TextTestRunner(verbosity=2).run(suite).wasSuccessful()


class CensusTests(unittest.TestCase):
    def setUp(self):
        # Tests obey the same workspace-only rule as the real invocation.
        self.tmp = tempfile.TemporaryDirectory(prefix='.census-test-', dir=Path(__file__).resolve().parent)
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def put(self, path, data):
        p = self.root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data) if isinstance(data, (dict, list)) else data, encoding='utf-8')
        return p

    def crash(self, run='batch/run1-control', reason='std::bad_alloc', extra='', ending='crash'):
        self.put(run + '/result.json', {'name': run.split('/')[-1], 'ending': ending, 'seconds': 999,
                                       'crash': {'report': 'crash-1.txt'}})
        return self.put(run + '/crash-1.txt', 'time: 2026-01-01, 120 s after the app started\nreason: ' + reason + '\n' + extra)

    def test_all_kinds_and_terminal_precedence(self):
        cases = [({'reason': 'VK_ERROR_OUT_OF_DEVICE_MEMORY'}, 'out of memory'),
                 ({'reason': 'VK_ERROR_OUT_OF_HOST_MEMORY'}, 'out of memory'),
                 ({'reason': 'std::bad_alloc'}, 'out of memory'),
                 ({'reason': 'VK_ERROR_DEVICE_LOST'}, 'device lost'),
                 ({'what': 'watchdog fired'}, 'hang or watchdog'),
                 ({'what': 'SIGSEGV', 'thread': 'CPUCore_2', 'where': 'outside the app code'}, 'CPU JIT fault'),
                 ({'what': 'SIGSEGV', 'thread': 'GPUBack', 'where': 'eboot+0x99'}, 'other'),
                 ({'reason': 'VK_ERROR_INITIALIZATION_FAILED'}, 'other'),
                 ({'what': 'SIGABRT', 'thread': 'CPUCore_0'}, 'other'),
                 ({'reason': 'refused buffer of 4096 bytes'}, 'out of memory')]
        for meta, expected in cases:
            with self.subTest(meta=meta):
                self.assertEqual(classify(meta, 'earlier out of memory')[0], expected)
        self.assertEqual(classify({'what': 'SIGSEGV', 'thread': 'CPUCore_2', 'where': 'eboot+0x42'}, '')[0], 'other')

    def test_dedup_stale_association_and_unknowns(self):
        p = self.crash(extra='thread: GPUBack (0x123)\n')
        self.put('later/run2/crash-1.txt', p.read_text())
        self.put('later/run2/result.json', {'ending': 'not_started', 'crash': {'report': 'crash-1.txt'}})
        self.put('later/run2/crash-index.txt', 'crash-1\ncrash-old\n')
        self.put('later/run2/crash-1-eden_log.txt', 'hang watch on\n')
        self.put('later/run2/crash-old.txt', 'what: SIGABRT\n')
        rows, stats, _ = collect(self.root)
        self.assertEqual(len(rows), 2)
        current = next(r for r in rows if r['crash_id'] == 'crash-1')
        old = next(r for r in rows if r['crash_id'] == 'crash-old')
        self.assertEqual(current['run_id'], 'run1-control')
        self.assertEqual(current['thread'], 'GPUBack')
        self.assertEqual(current['minutes_into_session'], '2')
        self.assertEqual(old['run_id'], UNKNOWN)
        self.assertEqual(old['env_diff'], UNKNOWN)
        self.assertEqual(old['build'], UNKNOWN)
        self.assertEqual(stats['duplicate_copies'], 1)

    def test_metadata_only_freeze_and_no_false_hangs(self):
        for ending in ('freeze', 'time_limit', 'script_stopped', 'no_answer', 'system_error'):
            self.put('batch/' + ending + '/result.json', {'ending': ending, 'seconds': 60, 'detail': 'freeze' if ending == 'freeze' else 'WAIT timeout'})
        rows, _, _ = collect(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]['kind'], 'hang or watchdog')

    def test_requests_and_rounded_amounts(self):
        p = self.crash(extra='thread: FS\n')
        self.put(str(p.parent.relative_to(self.root)) + '/report.txt', 'Ended: bad_alloc after the heap could not give 4.1 MiB\n')
        rows, _, _ = collect(self.root)
        self.assertIn('4.1 MiB', rows[0]['request_size'])
        self.assertEqual(rows[0]['request_bytes'], UNKNOWN)
        self.put(str(p.parent.relative_to(self.root)) + '/crash-1-eden_log.txt', '[119] Buffer allocation failed: 8192 bytes\n[125] Buffer refused: 9999 bytes\n')
        rows, _, _ = collect(self.root)
        self.assertEqual(rows[0]['request_bytes'], '8192')

    def test_control_build_markers_and_csv(self):
        p = self.crash()
        self.put('batch/eboot.json', {'sha256': 'abc123'})
        self.put('batch/plan.json', [{'name': 'run1-control', 'script': '/route/door.txt', 'env': ['A=1']},
                                    {'name': 'run2-treatment', 'env': ['A=2', 'B=3']}])
        self.put('batch/run1-control/env.txt', 'A=1\nEDEN_TEST_SCRIPT=control.txt\n')
        self.put('batch/run2-treatment/env.txt', 'A=2\nB=3\nEDEN_TEST_SCRIPT=treatment.txt\n')
        self.put('batch/run1-control/report.txt', '[50] location: House\n[110] load: Field\n[140] location: Village\n')
        rows, stats, warnings = collect(self.root)
        self.assertEqual(rows[0]['build'], 'abc123')
        self.assertEqual(rows[0]['script'], 'door.txt')
        self.assertEqual(rows[0]['last_marker'], 'load: Field')
        self.assertEqual(rows[0]['place'], 'door.txt / load: Field')
        self.assertEqual(rows[0]['env_diff'], '{}')
        d = environment_diff(self.root/'batch/run2-treatment', {},
                             json.loads(read_text(self.root/'batch/plan.json')), {})
        self.assertEqual(json.loads(d[1]), {'A': {'control': '1', 'run': '2'}, 'B': {'control': '<unset>', 'run': '3'}})
        write_outputs(rows, stats, warnings, self.root/'out')
        with (self.root/'out/crashes.csv').open(newline='') as f:
            self.assertEqual(list(csv.DictReader(f))[0], rows[0])
        self.assertIn('Top 15 crash signatures', read_text(self.root/'out/crash-census.md'))

    def test_ambiguous_control_and_missing_files(self):
        plan = [{'name': 'a-control', 'env': ['A=1']}, {'name': 'b-control', 'env': ['A=2']}]
        self.put('batch/run/env.txt', 'A=3\n')
        self.assertEqual(environment_diff(self.root/'batch/run', {}, plan, {})[1], UNKNOWN)
        self.put('batch/run/result.json', '{broken')
        self.put('batch/run/crash-a.txt', 'what: SIGSEGV\nwhere: eboot+0xabc\n')
        rows, _, warnings = collect(self.root)
        self.assertEqual(rows[0]['minutes_into_session'], UNKNOWN)
        self.assertTrue(warnings)

    def test_boundaries_and_normalisation(self):
        self.assertEqual([minute_bucket(x) for x in (0, 60, 120, 300, 600, 1200, 3600, None)], list(BUCKETS))
        a = normalise('SIGSEGV address 0x1234 @ eboot+0xAbC')
        b = normalise('SIGSEGV address 0x9999 @ eboot+0xabc')
        self.assertEqual(a, b)
        self.assertIn('eboot+0xabc', a)
        self.assertNotEqual(a, normalise('SIGSEGV address 0x1234 @ eboot+0xdef'))

    def test_settings_are_not_load_markers(self):
        report = 'Settings: UP_HELD_VS_DOWNLOAD=1 UP_DRAIN_AT_AREA=1\nTimeline (no log names the scene):\n  movie decoder opened: 36 s\n'
        self.assertEqual(location(report, 120), (UNKNOWN,) * 3)
        self.assertEqual(location('last location: Field', 120)[0], 'last location: Field')

    def test_same_name_different_reports_are_distinct(self):
        self.crash(run='batch/run1', reason='std::bad_alloc')
        self.crash(run='batch/run2', reason='VK_ERROR_DEVICE_LOST')
        rows, stats, _ = collect(self.root)
        self.assertEqual(len(rows), 2)
        self.assertEqual(len({r['crash_id'] for r in rows}), 2)
        self.assertEqual(stats['duplicate_copies'], 0)

    def test_duplicate_valid_runs_do_not_add_metadata_events(self):
        self.crash(run='batch/run1')
        self.crash(run='batch/run2')
        rows, stats, _ = collect(self.root)
        self.assertEqual(len(rows), 1)
        self.assertEqual(stats['duplicate_copies'], 1)
        self.assertEqual(stats['metadata_only_failures'], 0)

    def test_missing_primary_uses_result_crash(self):
        self.put('batch/run/result.json', {'ending': 'crash', 'seconds': 300,
                 'build': 'test-build', 'crash': {'reason': 'VK_ERROR_DEVICE_LOST',
                 'time': '75 s after the app started', 'thread': 'GPUBack'}})
        rows, _, _ = collect(self.root)
        self.assertEqual(rows[0]['kind'], 'device lost')
        self.assertEqual(rows[0]['seconds_into_session'], '75')
        self.assertEqual(rows[0]['build'], 'test-build')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs', type=Path, default=Path('runs'), help='input runs directory (default: runs)')
    parser.add_argument('--output-dir', type=Path, default=Path('.'), help='output directory (default: current directory)')
    parser.add_argument('--self-test', action='store_true', help='run synthetic tests only; leave real outputs unchanged')
    args = parser.parse_args()
    if args.self_test:
        return 0 if self_test() else 1
    if not args.runs.is_dir():
        parser.error('input directory does not exist: {}'.format(args.runs))
    rows, stats, warnings = collect(args.runs)
    write_outputs(rows, stats, warnings, args.output_dir)
    print('{} events; {} unique reports, {} duplicate copies collapsed, {} metadata-only failures'.format(
        len(rows), stats['unique_reports'], stats['duplicate_copies'], stats['metadata_only_failures']))
    for kind in KINDS:
        print('{}: {}'.format(kind, sum(r['kind'] == kind for r in rows)))
    print('Wrote {} and {}'.format(args.output_dir/'crash-census.md', args.output_dir/'crashes.csv'))
    if warnings:
        print('{} input warnings; see report'.format(len(warnings)), file=sys.stderr)
    return 0


if __name__ == '__main__':
    sys.exit(main())
