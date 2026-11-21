import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from stamp_guard import differences, env_values, translation_switches


class StampGuard(unittest.TestCase):
    def test_uses_build_switch_list(self):
        source = 'const char* TranslationSwitches[] = {"EDEN_DRAW", // "IGNORED"\n "EDEN_CACHE",};'
        self.assertEqual(translation_switches(source), {'EDEN_DRAW', 'EDEN_CACHE'})
        with self.assertRaises(ValueError):
            translation_switches('const char* TranslationSwitches[] = {};')

    def test_overlays_and_empty_values(self):
        reference = env_values(' EDEN_DRAW=1 \r\n# EDEN_DRAW=0\nEDEN_REPORT=1\n')
        candidate = env_values('EDEN_DRAW=1\nEDEN_REPORT=0\n', 'EDEN_DRAW=\r\n')
        self.assertEqual(differences(reference, candidate, {'EDEN_DRAW'}),
                         [('EDEN_DRAW', '1', '')])
        self.assertEqual(differences({}, {'EDEN_DRAW': ''}, {'EDEN_DRAW'}),
                         [('EDEN_DRAW', None, '')])
        self.assertEqual(differences(reference, env_values('EDEN_DRAW=1'), {'EDEN_DRAW'}), [])

    def test_exemptions_require_matching_runtime_mode(self):
        runtime = 'EDEN_NX2_PRELOAD_ALL_PIPELINES'
        source = {'EDEN_UP_SHADER_PREP_SOURCE_STAMP': '1'}
        self.assertTrue(differences(source, {**source, runtime: '1'}, {runtime}))
        self.assertEqual(differences(source, {**source, runtime: '1'}, {runtime}, True), [])
        with self.assertRaises(ValueError):
            differences(source, {**source, 'EDEN_UP_SHADER_PREP_EXE': ''}, {runtime}, True)
        skip = {'EDEN_UP_SHADER_PREP_SKIP_RUNTIME': '1'}
        self.assertEqual(differences(skip, {**skip, runtime: '1'}, {runtime}), [])
        self.assertTrue(differences({}, skip, set()))
