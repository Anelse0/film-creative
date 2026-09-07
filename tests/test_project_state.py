import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from project_check import inspect, sha
from baseline_snapshot import create, verify

class ProjectStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.path=self.root/'project-state.json'
        self.state={'version':1,'artifacts':{},'pending':['核对新结尾']}
    def tearDown(self): self.tmp.cleanup()
    def file(self,name,text):
        path=self.root/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_text(text)
        return {'path':name,'sha256':sha(path)}
    def artifact(self,name,text,deps=None):
        self.state['artifacts'][name]={'current':self.file(name+'.md',text),'depends_on':deps or {},'history':[],'drafts':[]}
    def check(self):
        self.path.write_text(json.dumps(self.state));return inspect(self.path)
    def test_resume_finds_current_without_adopting_draft(self):
        self.artifact('script','原台词')
        self.state['artifacts']['script']['drafts']=[self.file('drafts/try.md','尝试替代')]
        out=self.check();self.assertEqual(out['stale'],[]);self.assertEqual(out['current']['script'],sha(self.root/'script.md'))
        self.assertEqual(out['pending'],['核对新结尾'])
    def test_update_preserves_approved_snapshot_and_invalidates_transitive_only(self):
        self.artifact('script','原台词');old=self.state['artifacts']['script']['current']['sha256']
        approved=self.file('history/script/v1.md','原台词');approved['evidence']='用户确认场01'
        self.state['artifacts']['script']['approved']=approved
        self.artifact('shot','镜头',{'script':old})
        self.artifact('prompt','编译',{'shot':self.state['artifacts']['shot']['current']['sha256']})
        self.artifact('other','无关场景')
        self.state['artifacts']['script']['current']=self.file('script.md','改稿')
        self.state['artifacts']['script']['history']=[{k:v for k,v in approved.items() if k!='evidence'}]
        out=self.check();self.assertFalse(out['errors']);self.assertEqual(out['stale'],['prompt','shot'])
        self.assertEqual((self.root/'history/script/v1.md').read_text(),'原台词')
    def test_unrecorded_edit_is_not_silently_accepted(self):
        self.artifact('script','原台词');(self.root/'script.md').write_text('外部修改')
        out=self.check();self.assertTrue(out['errors']);self.assertIn('script',out['stale'])
    def test_confirmation_requires_immutable_snapshot_and_evidence(self):
        self.artifact('script','台词');self.state['artifacts']['script']['approved']=dict(self.state['artifacts']['script']['current'])
        out=self.check();self.assertEqual(len(out['errors']),2)
    def test_upload_reorder_affects_only_dependent_clip(self):
        self.artifact('stable-character','角色资产')
        asset=self.state['artifacts']['stable-character']['current']['sha256']
        self.artifact('upload-a','img1=角色 img2=房间',{'stable-character':asset})
        self.artifact('clip-a','正文A',{'upload-a':self.state['artifacts']['upload-a']['current']['sha256']})
        self.artifact('clip-b','正文B',{'stable-character':asset})
        self.state['artifacts']['upload-a']['current']=self.file('upload-a.md','img1=房间 img2=角色')
        self.assertEqual(self.check()['stale'],['clip-a'])
    def test_dependency_cycle_and_missing_node_fail(self):
        self.artifact('a','a',{'b':'x'});self.artifact('b','b',{'a':'x','missing':'x'})
        self.assertTrue(self.check()['errors'])

class BaselineTests(unittest.TestCase):
    def test_non_git_snapshot_round_trip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);source=root/'source';source.mkdir()
            (source/'SKILL.md').write_text('test');(source/'VERSION').write_text('2.5.5')
            out=create(source,root/'copy');expected=out['manifest_sha256']
            self.assertEqual(verify(root/'copy',expected)['errors'],[])
            (root/'copy'/'SKILL.md').write_text('modified')
            self.assertTrue(verify(root/'copy',expected)['errors'])
    def test_nested_destination_rejected_before_writing(self):
        with tempfile.TemporaryDirectory() as d:
            source=Path(d);(source/'SKILL.md').write_text('test');(source/'VERSION').write_text('x')
            with self.assertRaises(ValueError):create(source,source/'copy')
            self.assertFalse((source/'copy').exists())
