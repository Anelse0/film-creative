"""Executable routing regressions for the independent creative skill.

These tests validate execution scope, never creative quality or NLP understanding.
"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from route_check import validate


def record(entry='S3c', target='S3c', plan=None):
    return {
        'version': 1,
        'source': '只改现有剧本的一场，其他设定与结尾保持。',
        'request': {'entry': entry, 'target': target, 'excluded': [],
                    'autonomy': 'autonomous', 'save': 'no'},
        'planned_stages': [entry] if plan is None else plan,
        'hard_locks': ['其他设定与结尾保持'],
    }


class CreativeBoundaries(unittest.TestCase):
    def test_every_production_target_is_rejected(self):
        # The old checker accepted every one of these independent routes.
        for stage in ('S4', 'S5', 'S5b', 'S6', 'S7', 'performance', 'raw'):
            with self.subTest(stage=stage):
                result = validate(record(stage, stage))
                self.assertTrue(any(e.startswith('R02') for e in result['errors']))
                self.assertEqual(result['semantic_match'], 'not_verified')

    def test_production_cannot_be_inserted_into_creative_plan(self):
        r = record('S3a', 'S3c', ['S3a', 'S4', 'S3c'])
        self.assertTrue(validate(r)['errors'])

    def test_production_exclusions_are_valid_handoff_context(self):
        r = record()
        r['request']['excluded'] = ['S4', 'S5', 'S5b', 'S6', 'S7', 'performance', 'raw']
        self.assertEqual(validate(r)['errors'], [])

    def test_all_creative_entry_and_target_pairs(self):
        stages = ['S3a', 'S3b', 'S3c']
        for i, entry in enumerate(stages):
            for j in range(i, len(stages)):
                with self.subTest(entry=entry, target=stages[j]):
                    result = validate(record(entry, stages[j], stages[i:j + 1]))
                    self.assertEqual(result['errors'], [])
                    self.assertFalse(result['decision']['write_files'])
                    self.assertFalse(result['decision']['confirmed'])

    def test_autonomy_cannot_expand_a_story_request_to_script(self):
        r = record('S3b', 'S3b', ['S3b', 'S3c'])
        self.assertTrue(validate(r)['errors'])

    def test_save_only_still_works_without_starting_creative_work(self):
        r = record('save_only', 'save_only', [])
        r['request']['save'] = 'yes'
        self.assertEqual(validate(r)['errors'], [])
        r['planned_stages'] = ['S3a']
        self.assertTrue(validate(r)['errors'])

    def test_shots_and_clips_are_preserved_without_expanding_scope(self):
        r = record()
        r['request']['units'] = {'scenes': 1, 'shots': 4, 'clips': 2}
        result = validate(r)
        self.assertEqual(result['errors'], [])
        self.assertEqual(result['decision']['target'], 'S3c')
        self.assertEqual(result['decision']['units'], r['request']['units'])

    def test_open_method_under_guided_autonomy_delivers_options_not_rewrite(self):
        r = record()
        r['request']['autonomy'] = 'guided'
        r['request']['method'] = 'open'
        r['deliverable'] = 'rewrite'
        result = validate(r)
        self.assertTrue(any(e.startswith('R08') for e in result['errors']))
        self.assertFalse(result['decision']['rewrite_allowed'])
        r['deliverable'] = 'options'
        self.assertEqual(validate(r)['errors'], [])

    def test_given_method_or_autonomous_allows_rewrite(self):
        r = record(); r['request']['method'] = 'given'; r['request']['autonomy'] = 'guided'
        self.assertTrue(validate(r)['decision']['rewrite_allowed'])
        r = record(); r['request']['method'] = 'open'; r['request']['autonomy'] = 'autonomous'
        r['deliverable'] = 'rewrite'
        result = validate(r)
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['decision']['rewrite_allowed'])

    def test_rewrite_is_exploratory_until_user_adopts(self):
        r = record(); r['request']['method'] = 'given'
        result = validate(r)
        self.assertEqual(result['decision']['adoption'], 'exploratory')
        self.assertFalse(result['decision']['sync_dependents'])
        r['request']['adoption'] = 'adopted'
        self.assertTrue(any(e.startswith('R08') for e in validate(r)['errors']))
        r['confirmation'] = {'confirmed': True, 'evidence': '用户："就这样，同步到故事"'}
        result = validate(r)
        self.assertEqual(result['errors'], [])
        self.assertTrue(result['decision']['sync_dependents'])

    def test_cli_rejects_production_and_accepts_shipped_template(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / 'route.json'
            path.write_text(json.dumps(record('S5', 'S5')), encoding='utf-8')
            result = subprocess.run([sys.executable, str(ROOT / 'scripts/route_check.py'),
                                     '--record', str(path)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1)
            self.assertIn('film-director', result.stdout)
        result = subprocess.run([sys.executable, str(ROOT / 'scripts/route_check.py'),
                                 '--record', str(ROOT / 'templates/execution-record.json')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertEqual(json.loads(result.stdout)['decision']['target'], 'S3c')


if __name__ == '__main__':
    unittest.main()
