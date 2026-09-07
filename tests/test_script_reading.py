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
