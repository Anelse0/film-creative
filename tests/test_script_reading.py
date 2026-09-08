import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from assemble_script import assemble, body


class ScriptReadingTests(unittest.TestCase):
    def test_explicit_order_body_only_and_source_integrity(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            a, b, out = root/'01.md', root/'02.md', root/'reading.md'
            a.write_text('分析\n<!-- script-body:start -->\n场 01\n甲\n    我今天回来了。\n<!-- script-body:end -->\n## 有序表演块\n保留的执行信息')
            b.write_text('<!-- script-body:start -->\n场 02\n水声停止。\n<!-- script-body:end -->')
            before = a.read_bytes()
            assemble([b, a], out)
            self.assertEqual(out.read_text(), '场 02\n水声停止。\n\n场 01\n甲\n    我今天回来了。\n')
            self.assertEqual(a.read_bytes(), before)
            self.assertEqual(json.loads(out.with_suffix('.sources.json').read_text())['sources'][1]['sha256'], hashlib.sha256(before).hexdigest())

    def test_legacy_body_and_external_heading(self):
        self.assertEqual(body('场 01 · 家\n参数：强\n## 剧本页\n甲说：“行。”\n## 台词四件套\n注释'), '场 01 · 家\n\n甲说：“行。”')

    def test_ambiguous_or_missing_body_refused(self):
        for text in ('整篇没有正文标记', '<!-- script-body:end --><!-- script-body:start -->', '<!-- script-body:start --><!-- script-body:start --><!-- script-body:end -->', '<!-- script-body:start --><!-- script-body:end -->'):
            with self.subTest(text=text), self.assertRaises(ValueError):
                body(text)

    def test_no_partial_result_on_invalid_source(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';out=Path(d)/'out';p.write_text('invalid')
            with self.assertRaises(ValueError): assemble([p],out)
            self.assertFalse(out.exists())

    def test_source_overwrite_and_duplicates_refused(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'a';p.write_text('## 剧本页\n台词')
            with self.assertRaises(ValueError): assemble([p],p)
            with self.assertRaises(ValueError): assemble([p,p],p.parent/'out')

    def test_legacy_does_not_duplicate_heading_or_mask_empty_body(self):
        self.assertEqual(body('场 01\n## 剧本页\n场 01\n雨停了。'), '场 01\n雨停了。')
        with self.assertRaises(ValueError): body('场 01\n## 剧本页\n## 注释\nnot body')

    def test_portable_manifest_verifies_after_project_move(self):
        import shutil
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)/'project';root.mkdir()
            a=root/'场一.md'; a.write_text('## 剧本页\n场 01\n雨停了。')
            out=root/'derived'/'reading.md';assemble([a],out)
            info=verify(out)
            self.assertEqual(info['sources'][0]['path'], '../场一.md')
            moved=Path(d)/'moved';shutil.move(str(root),str(moved))
            verify(moved/'derived'/'reading.md')

    def test_changed_source_requires_rebuild(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            assemble([a],out);a.write_text('## 剧本页\n新稿')
            with self.assertRaisesRegex(ValueError,'source changed'): verify(out)
            assemble([a],out);verify(out)
            self.assertEqual(out.read_text(),'新稿\n')

    def test_tampered_reading_and_unmanaged_output_protected(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            out.write_text('别覆盖')
            with self.assertRaises(ValueError): assemble([a],out)
            self.assertEqual(out.read_text(),'别覆盖');out.unlink()
            assemble([a],out);out.write_text('有人工改动')
            with self.assertRaises(ValueError): verify(out)
            with self.assertRaises(ValueError): assemble([a],out)
            self.assertEqual(out.read_text(),'有人工改动')

    def test_manifest_order_tampering_detected(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';b=Path(d)/'b';out=Path(d)/'out.md'
            a.write_text('## 剧本页\n甲');b.write_text('## 剧本页\n乙')
            assemble([a,b],out);m=out.with_suffix('.sources.json');info=json.loads(m.read_text())
            info['sources'].reverse();m.write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError,'source order'): verify(out)

    def test_hardlink_and_manifest_output_aliases_refused(self):
        import os
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';alias=Path(d)/'alias';a.write_text('## 剧本页\n原稿');os.link(a,alias)
            with self.assertRaises(ValueError): assemble([a,alias],Path(d)/'out')
            with self.assertRaises(ValueError): assemble([a],alias)
            with self.assertRaises(ValueError): assemble([a],Path(d)/'out.sources.json')
            out=Path(d)/'out.md';m=out.with_suffix('.sources.json');os.link(a,m)
            with self.assertRaises(ValueError): assemble([a],out)
            self.assertEqual(a.read_text(),'## 剧本页\n原稿')

    def test_failed_second_replace_rolls_back_pair(self):
        import os
        from unittest.mock import patch
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            assemble([a],out);m=out.with_suffix('.sources.json')
            old=(out.read_bytes(),m.read_bytes());a.write_text('## 剧本页\n新稿')
            real_replace=os.replace
            def fail_manifest(src,dst):
                if dst.resolve() == m.resolve(): raise OSError('injected second-file failure')
                return real_replace(src,dst)
            with patch('assemble_script.os.replace',side_effect=fail_manifest):
                with self.assertRaises(OSError): assemble([a],out)
            self.assertEqual((out.read_bytes(),m.read_bytes()),old)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()),['a','out.md','out.sources.json'])
            assemble([a],out);verify(out)

    def test_failed_first_publication_leaves_no_derived_files(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            m=out.with_suffix('.sources.json');real_replace=os.replace
            def fail_manifest(src,dst):
                if dst.resolve() == m.resolve(): raise OSError('injected failure')
                return real_replace(src,dst)
            with patch('assemble_script.os.replace',side_effect=fail_manifest):
                with self.assertRaises(OSError): assemble([a],out)
            self.assertEqual(list(Path(d).iterdir()),[a])

    def test_legacy_absolute_manifest_verification(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            assemble([a],out);m=out.with_suffix('.sources.json');info=json.loads(m.read_text())
            del info['schema_version'];del info['path_base'];info['sources'][0]['path']=str(a)
            m.write_text(json.dumps(info));verify(out)

    def test_malformed_manifests_fail_with_value_error(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            out=Path(d)/'out.md';out.write_text('正文');m=out.with_suffix('.sources.json')
            for info in ([],{}, {'derived':True,'sources':[None],'output_sha256':'x'},
                         {'derived':True,'sources':[],'output_sha256':'x'}):
                with self.subTest(info=info):
                    m.write_text(json.dumps(info))
                    with self.assertRaises(ValueError): verify(out)

    def test_marker_body_preserves_locked_spaces_and_multiline_dialogue(self):
        from assemble_script import verify
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'reading.md'
            locked='  我不是不走。  \n我只是还没告诉她。  '
            a.write_text('说明\n<!-- script-body:start -->\n'+locked+'\n<!-- script-body:end -->\n注释')
            before=a.read_bytes();assemble([a],out);verify(out)
            self.assertEqual(out.read_text(),locked+'\n')
            self.assertEqual(a.read_bytes(),before)

    def test_filled_scene_template_assembles_only_reader_content(self):
        from assemble_script import verify
        template=(Path(__file__).resolve().parents[1]/'templates/script-scene.md').read_text()
        values={'〈作品名〉':'雨停之后','〈场号〉':'01','〈实际版本〉':'v1',
                '〈草稿/已采用/用户确认〉':'草稿','〈日期〉':'2026-09-08',
                '〈内景/外景〉':'内景','〈地点〉':'修鞋店','〈时刻〉':'夜',
                '〈动作正文：谁在做什么，发生什么可见可听的事。〉':'师傅翻开合同。',
                '〈角色名〉':'师傅','〈对白正文。〉':'你妈签了没有？',
                '〈必要的动作或听者反应。〉':'小林摇头。',
                '〈另一角色名〉':'小林','〈回应正文。〉':'她还不知道我要走。',
                '〈与前后场相关的必要依据、实际修改与影响、需要决定的缺口。〉':'下一场才告知母亲。'}
        for old,new in values.items():template=template.replace(old,new)
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'scene.md';out=Path(d)/'reading.md';a.write_text(template)
            assemble([a],out);verify(out)
            self.assertEqual(out.read_text(),'### 场 01 · 内景 · 修鞋店 · 夜\n\n师傅翻开合同。\n\n**师傅**\n\n你妈签了没有？\n\n小林摇头。\n\n**小林**\n\n她还不知道我要走。\n')

    def test_failed_rollback_retains_recovery_backup(self):
        import os
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'a';out=Path(d)/'out.md';a.write_text('## 剧本页\n原稿')
            assemble([a],out);old=out.read_bytes();a.write_text('## 剧本页\n新稿')
            real_replace=os.replace;calls=[]
            def fail_after_first(src,dst):
                calls.append(dst)
                if len(calls)>1:raise OSError('injected persistent failure')
                return real_replace(src,dst)
            with patch('assemble_script.os.replace',side_effect=fail_after_first):
                with self.assertRaisesRegex(OSError,'retained backups'):assemble([a],out)
            backups=list(Path(d).glob('.out.md.*'))
            self.assertEqual(len(backups),1)
            self.assertEqual(backups[0].read_bytes(),old)
