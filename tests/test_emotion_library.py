"""Data integrity, exact retrieval, portable operation and explicit failure modes."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import emotion_lookup as e
from route_check import validate

class EmotionTests(unittest.TestCase):
    def test_originals_and_all_notes_verify(self):
        self.assertEqual(e.verify(),[])

    def test_every_raw_record_is_returned_without_rewriting(self):
        raw,notes=e.load_library()
        for item in raw:
            with self.subTest(id=item['id']):
                result=e.select(raw,notes,ids=[item['id']])
                self.assertEqual(result,[item])
                self.assertIs(result[0],item)

    def test_derived_notes_cannot_override_original_fields(self):
        raw,notes=e.load_library()
        self.assertTrue(all('prompt' not in n and 'intensity' not in n for n in notes.values()))
        before=json.dumps(raw,ensure_ascii=False)
        e.select(raw,notes,query='内疚')
        self.assertEqual(json.dumps(raw,ensure_ascii=False),before)

    def test_query_and_family_filter(self):
        raw,notes=e.load_library()
        self.assertEqual([x['id'] for x in e.select(raw,notes,query='假笑')],[25])
        self.assertEqual([x['id'] for x in e.select(raw,notes,family='fear')],[3,9,18])
        self.assertEqual(e.select(raw,notes,query='假笑',family='Fear'),[])

    def test_unknown_id_not_silently_substituted(self):
        raw,notes=e.load_library()
        for ids in ([0],[26],[1,26],[-1]):
            with self.assertRaises(ValueError):e.select(raw,notes,ids=ids)

    def test_cli_from_unrelated_directory_and_raw_schema(self):
        raw,_=e.load_library()
        with tempfile.TemporaryDirectory() as d:
            p=subprocess.run([sys.executable,str(ROOT/'scripts/emotion_lookup.py'),'--id','20','25','--raw'],cwd=d,capture_output=True,text=True)
        self.assertEqual(p.returncode,0,p.stderr)
        self.assertEqual(json.loads(p.stdout),[raw[19],raw[24]])

    def test_empty_query_result_has_explicit_nonzero_status(self):
        p=subprocess.run([sys.executable,str(ROOT/'scripts/emotion_lookup.py'),'--query','zzzz-no-match-zzz'],capture_output=True,text=True)
        self.assertEqual(p.returncode,3)
        self.assertEqual(json.loads(p.stdout)['matches'],[])
        self.assertIn('No matching',p.stderr)

    def test_tampered_source_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'assets',root/'assets');shutil.copytree(ROOT/'references',root/'references')
            p=root/'assets/emotion/prompts.json';p.write_text(p.read_text().replace('The eyes squeeze','The eyes close'))
            errors=e.verify(root)
            self.assertTrue(any('checksum' in x for x in errors))
            self.assertTrue(any('JSON/Markdown' in x for x in errors))

    def test_duplicate_notes_do_not_pass_coverage(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);shutil.copytree(ROOT/'assets',root/'assets');shutil.copytree(ROOT/'references',root/'references')
            p=root/'references/emotion-notes.json';data=json.loads(p.read_text());data['entries'][1]=data['entries'][0];p.write_text(json.dumps(data))
            self.assertTrue(any('derived notes' in x for x in e.verify(root)))

    def test_reference_route_does_not_authorize_creative_stages(self):
        r={'version':1,'source':'仅查原始第20条，不增加场景。','request':{'target':'reference','entry':'reference','save':'no'},'planned_stages':[]}
        result=validate(r)
        self.assertEqual(result['errors'],[])
        self.assertFalse(result['decision']['write_files'])
        r['planned_stages']=['S3c']
        self.assertTrue(validate(r)['errors'])

if __name__=='__main__':unittest.main()
