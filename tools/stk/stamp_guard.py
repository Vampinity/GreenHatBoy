#!/usr/bin/env python3
"""Check the environment inputs to a prepared shader store stamp."""
import argparse
import re
from pathlib import Path

SOURCE_STAMP = "EDEN_UP_SHADER_PREP_SOURCE_STAMP"
EXE_STAMP = "EDEN_UP_SHADER_PREP_EXE"
SKIP_RUNTIME = "EDEN_UP_SHADER_PREP_SKIP_RUNTIME"
RUNTIME_ONLY = {"EDEN_NX2_TRANSCODE_WAIT", "EDEN_NX2_PRELOAD_ALL_PIPELINES"}
STAMP_CONTROLS = {SOURCE_STAMP, EXE_STAMP, SKIP_RUNTIME}


def translation_switches(source):
    block = re.search(r'\bTranslationSwitches\[\]\s*=\s*\{([^}]*)\}\s*;', source)
    if block is None:
        raise ValueError("TranslationSwitches array missing from the supplied C++ source")
    entries = re.sub(r'/\*.*?\*/|//[^\n]*', '', block[1], flags=re.S)
    names = [entry.strip() for entry in entries.strip().removesuffix(',').split(',')]
    if not all(re.fullmatch(r'"[A-Z_][A-Z0-9_]*"', name) for name in names):
        raise ValueError("TranslationSwitches must contain explicit switch names")
    return {name[1:-1] for name in names}


def env_values(*documents):
    values = {}
    for document in documents:
        for raw in document.split('\n'):
            line = raw.lstrip(' \t').rstrip(' \t\r')
            name, separator, value = line.partition('=')
            if not line.startswith('#') and separator and name:
                values[name] = value
    return values


def differences(reference, candidate, names, source_stamp=False):
    if source_stamp and any(
        env.get(SOURCE_STAMP) != '1' or EXE_STAMP in env for env in (reference, candidate)
    ):
        raise ValueError("--source-stamp requires both environments to request source stamps without an executable override")
    if source_stamp or all(env.get(SKIP_RUNTIME) == '1' for env in (reference, candidate)):
        names = names - RUNTIME_ONLY
    return [
        (name, reference.get(name), candidate.get(name))
        for name in sorted(names | STAMP_CONTROLS)
        if reference.get(name) != candidate.get(name)
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('reference', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--cpp', type=Path, required=True, help='vk_pipeline_prep.cpp from the target build')
    parser.add_argument('--reference-overlay', type=Path, action='append', default=[])
    parser.add_argument('--candidate-overlay', type=Path, action='append', default=[])
    parser.add_argument('--source-stamp', action='store_true',
                        help='allow runtime-only differences if the target build is verified to use a source stamp')
    args = parser.parse_args()
    try:
        names = translation_switches(args.cpp.read_text(encoding='utf-8'))
        reference = env_values(*(path.read_text(encoding='utf-8') for path in
                                 [args.reference, *args.reference_overlay]))
        candidate = env_values(*(path.read_text(encoding='utf-8') for path in
                                 [args.candidate, *args.candidate_overlay]))
        changed = differences(reference, candidate, names, args.source_stamp)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    for name, before, after in changed:
        print(f'Shader stamp input changed: {name} {before!r} -> {after!r}')
    if not changed:
        print('Shader stamp environment check passed')
    return int(bool(changed))


if __name__ == '__main__':
    raise SystemExit(main())
