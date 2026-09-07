"""Exercise structured boundaries and precedence, not natural-language classification."""
import copy
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from route_check import validate


def example():
    return json.loads((ROOT / 'templates/execution-record.json').read_text())


class ExecutionContractTests(unittest.TestCase):
    def test_audit_records_preserve_interpreted_scope(self):
        rows = json.loads((ROOT / 'tests/fixtures/routing-2.6.0/audit-probes.json').read_text())
        for row in rows:
            with self.subTest(case=row['id']):
                result = validate(row['record'])
                self.assertEqual(result['errors'], [])
                self.assertEqual(result['decision']['write_files'], row['expected_write'])
                self.assertFalse(result['decision']['confirmed'])
                self.assertEqual(result['semantic_match'], 'not_verified')

    def test_raw_audit_inputs_do_not_trigger_save_or_route(self):
        rows = json.loads((ROOT / 'tests/fixtures/routing-2.6.0/audit-probes.json').read_text())
        for row in rows:
            out = subprocess.run([sys.executable, str(ROOT/'scripts/route_check.py'), row['record']['source']], capture_output=True, text=True)
            self.assertEqual(out.returncode, 2)
            self.assertIn('语义理解', out.stdout)

    def test_explicit_no_overrides_prior_always_and_autonomy(self):
        r = example();r['request'].update(save='no', autonomy='autonomous')
        r['history']['save_policy'] = 'always'
        self.assertFalse(validate(r)['decision']['write_files'])
        r['decision'] = validate(r)['decision'].copy();r['decision']['write_files'] = True
        self.assertTrue(any(e.startswith('R07') for e in validate(r)['errors']))

    def test_historical_save_authorization_survives_turns(self):
        r = example();r['history']['save_policy']='always'
        self.assertTrue(validate(r)['decision']['write_files'])
        r['request']['save']='no'
        self.assertFalse(validate(r)['decision']['write_files'])

    def test_confirmation_never_creates_save_policy(self):
        r=example();r['confirmation']={'confirmed':True,'evidence':'用户：场01就按此版'}
        self.assertFalse(validate(r)['decision']['write_files'])
        r['history']['save_policy']='after_confirmation'
        self.assertTrue(validate(r)['decision']['write_files'])
        r['confirmation']['confirmed']=False
        self.assertFalse(validate(r)['decision']['write_files'])

    def test_saving_does_not_confirm(self):
        r=example();r['request']['save']='yes'
        d=validate(r)['decision'];self.assertTrue(d['write_files']);self.assertFalse(d['confirmed'])

    def test_scope_exclusions_and_endpoints(self):
        for plan in [['S4','S5','S6'],['S5','S4'],['S4','S4','S5']]:
            r=example();r['planned_stages']=plan
            self.assertTrue(validate(r)['errors'])

    def test_one_scene_does_not_limit_clips_or_imply_prompt(self):
        r=example();r['request']['units']={'scenes':1,'shots':None,'clips':3}
        d=validate(r);self.assertFalse(d['errors']);self.assertEqual(d['decision']['target'],'S5')

    def test_confirmation_requires_evidence(self):
        r=example();r['confirmation']['confirmed']=True
        self.assertTrue(any(e.startswith('R05') for e in validate(r)['errors']))

    def test_malformed_records_fail_without_crashing(self):
        for record in [None,[],{'version':True},{'version':1,'request':[]}, {'version':1,'source':'x','request':{'entry':{},'target':[]},'planned_stages':[]}]:
            self.assertTrue(validate(record)['errors'])

    def test_cli_invalid_json(self):
        out=subprocess.run([sys.executable,str(ROOT/'scripts/route_check.py'),'--record',str(ROOT/'SKILL.md')],capture_output=True,text=True)
        self.assertEqual(out.returncode,1)

    def test_concept_can_omit_auxiliary_fields(self):
        from test_concept import run, JUDGEMENT
        rc,out=run(JUDGEMENT+'\n候选 〈晚班〉\n一句话：两位同事终于有空一起吃饭，却仍在互相报工作进度。\n独特之处：亲近从不再急着填满沉默开始。\n')
        self.assertEqual(rc,0,out);self.assertNotIn('C09',out)
