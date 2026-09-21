"""3.3.0: 出稿后对白 review——THE ORDER EP02 场 1 v1 必须判为有问题，v3 必须通过；安静戏与有理由的短句不误判。"""
import io
import json
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import review_script as rs  # noqa: E402

FIX = ROOT / 'tests' / 'fixtures' / 'review'
V1 = FIX / 'theorder-ep02-s01-v1.md'
V3 = FIX / 'theorder-ep02-s01-v3.md'


def scene(body_text):
    return '## 剧本页\n<!-- script-body:start -->\n场 01 〈测试〉 · 地点 · 夜\n\n' + body_text + '\n<!-- script-body:end -->\n'


def chars(text):
    return len(re.sub(r'\s', '', text))


class RealSampleTests(unittest.TestCase):
    def test_v1_is_flagged_with_evidence_and_sources(self):
        r = rs.review_file(V1)
        self.assertEqual(r['verdict'], 'issues')
        keys = {i['key'] for i in r['issues']}
        self.assertIn('no_exchange', keys)
        self.assertIn('slogan', keys)
        self.assertEqual(len(r['stats']['offscreen_lines']), 3)
        self.assertEqual(r['stats']['longest_exchange'], 0)
        self.assertLess(r['stats']['conversation_share'], 0.5)
        self.assertLess(r['stats']['mean_words'], 4)
        # 每个问题都有文本证据与来源编号
        for it in r['issues']:
            self.assertRegex(it['evidence'], r'「.+」')
            self.assertTrue(it['sources'])
            self.assertIn('[推论]', it['basis'])  # 3.3.1: 输出同步标注哪些是来源、哪些是推论
        self.assertIn('[推论]', r['text'])
        self.assertIn("Not in this shirt", r['text'])
        self.assertIn('交接 film-director', r['text'])
        self.assertLessEqual(chars(r['text']), 800)
        self.assertLessEqual(len(r['issues']), 3)

    def test_v3_passes_and_is_clearly_better(self):
        r1, r3 = rs.review_file(V1), rs.review_file(V3)
        self.assertEqual(r3['verdict'], 'pass')
        self.assertEqual(r3['issues'], [])
        self.assertEqual(r3['stats']['offscreen_lines'], [])
        self.assertGreaterEqual(r3['stats']['longest_exchange'], 5)
        self.assertGreater(r3['stats']['conversation_share'], r1['stats']['conversation_share'] + 0.4)
        self.assertGreater(r3['stats']['mean_words'], r1['stats']['mean_words'] + 2)
        self.assertLess(r3['stats']['third_party_jump_share'], r1['stats']['third_party_jump_share'])
        self.assertIn('通过', r3['text'])
        self.assertLessEqual(chars(r3['text']), 800)

    def test_v1_lines_parsed_in_order(self):
        lines, _ = rs.parse(V1.read_text(encoding='utf-8'))
        self.assertEqual([ln['speaker'] for ln in lines][:4], ['Isa', 'Mack', 'Beckett', 'Cole'])
        self.assertEqual(lines[1]['text'], "Ten. I'm working.")
        self.assertTrue(lines[1]['offscreen'])
        self.assertFalse(lines[0]['offscreen'])


class FalsePositiveGuardTests(unittest.TestCase):
    def test_quiet_scene_not_judged(self):
        text = scene('两人对坐。\n\n**A**\nStay.\n\n**B**\nOkay.\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.md'
            p.write_text(text, encoding='utf-8')
            r = rs.review_file(p)
        self.assertEqual(r['verdict'], 'insufficient')
        self.assertEqual(r['issues'], [])

    def test_short_answers_with_reasons_pass(self):
        text = scene('厨房。她背对他洗碗。\n\n**MAYA**\nWhere were you?\n\n**JON**\nWork.\n\n**MAYA**\nUntil now?\n\n**JON**\nUntil now.\n\n**MAYA**\nYou could have called.\n\n**JON**\nI know.\n\n**MAYA**\nJon.\n\n**JON**\nI know, Maya.\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.md'
            p.write_text(text, encoding='utf-8')
            r = rs.review_file(p)
        self.assertEqual(r['verdict'], 'pass', r['text'])
        self.assertGreaterEqual(r['stats']['longest_exchange'], 3)
        self.assertLess(r['stats']['short_unexcused_share'], 0.45)

    def test_chinese_plain_format_parses_and_skips_length_metrics(self):
        text = scene('姐姐在切菜，弟弟站在门口。\n\n姐\n    你什么时候搬？\n\n弟\n    周六。车已经找好了。\n\n姐\n    我不忙，就不能先听一声？\n\n弟\n    那……周六你帮我看着车？\n\n姐\n    看着车。行。\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.md'
            p.write_text(text, encoding='utf-8')
            r = rs.review_file(p)
        self.assertEqual(r['verdict'], 'pass')
        self.assertEqual(r['stats']['english_lines'], 0)
        self.assertIsNone(r['stats']['mean_words'])
        self.assertEqual(r['stats']['questions_answered'], 3)
        self.assertEqual(r['lines'][0]['addressee'], '弟')


class ScriptLevelShotChecksTests(unittest.TestCase):
    def test_offscreen_markers_in_both_conventions(self):
        text = scene('A 在门口，B 在里屋。\n\n**A**\n(O.S.)\nYou coming?\n\n**B**\n（画外）\nIn a minute.\n\n**A**\nThat was a minute.\n\n**B**\nThen two.\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.md'
            p.write_text(text, encoding='utf-8')
            r = rs.review_file(p)
        self.assertEqual(len(r['stats']['offscreen_lines']), 2)
        self.assertTrue(any(i['key'] == 'offscreen' for i in r['issues']))
        self.assertIn('S9', r['text'])

    def test_unknown_addressee_goes_to_model_review_not_verdict(self):
        r = rs.review_file(V3)
        self.assertTrue(r['review_needed'])
        self.assertIn('需模型复核', r['text'])
        self.assertEqual(r['verdict'], 'pass')


class CliTests(unittest.TestCase):
    def test_exit_codes_and_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = rs.main([str(V1), str(V3), '--json'])
        self.assertEqual(rc, 1)
        data = json.loads(buf.getvalue())
        self.assertEqual([d['verdict'] for d in data], ['issues', 'pass'])
        self.assertIn('thresholds', data[0])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(rs.main([str(V3)]), 0)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'bad.md'
            p.write_text('没有剧本页标记', encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(rs.main([str(p)]), 2)


class WiringTests(unittest.TestCase):
    def test_docs_wire_the_reviewer_in(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('scripts/review_script.py', skill)
        self.assertIn('references/dialogue-review-sources.md', skill)
        s3c = (ROOT / 'references' / 'stage-3c-script.md').read_text(encoding='utf-8')
        self.assertIn('review_script.py', s3c)
        src = (ROOT / 'references' / 'dialogue-review-sources.md').read_text(encoding='utf-8')
        for code in ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9'):
            self.assertRegex(src, r'\| ' + code + r' \|')
        self.assertIn('[推论', src)
        self.assertIn('不改稿', skill)


if __name__ == '__main__':
    unittest.main()
