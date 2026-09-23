"""3.3.0: 出稿后对白 review——THE ORDER EP02 场 1 v1 必须判为有问题，v3 对白连通必须通过；安静戏与有理由的短句不误判。
3.5.0: 人物赌注与连通分开判；这些旧样本没有赌注卡，整体 verdict 为 issues、checks.stakes = missing。"""
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
S2 = FIX / 'theorder-ep02-s02-v2.md'
S3_BAD = FIX / 'theorder-ep02-s03-v2-key-unanchored.md'
S3_OK = FIX / 'theorder-ep02-s03-v2-key-asked.md'
EP03_S4 = FIX / 'theorder-ep03-s04-v3.md'
EP03_S4_CARD = FIX / 'theorder-ep03-s04-v3-card.md'


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
        self.assertEqual(r3['checks']['dialogue'], 'pass')
        self.assertEqual(r3['checks']['stakes'], 'missing')
        self.assertEqual([i['key'] for i in r3['issues']], ['stakes'])
        self.assertEqual(r3['stats']['offscreen_lines'], [])
        self.assertGreaterEqual(r3['stats']['longest_exchange'], 5)
        self.assertGreater(r3['stats']['conversation_share'], r1['stats']['conversation_share'] + 0.4)
        self.assertGreater(r3['stats']['mean_words'], r1['stats']['mean_words'] + 2)
        self.assertLess(r3['stats']['third_party_jump_share'], r1['stats']['third_party_jump_share'])
        self.assertIn('对白连通通过', r3['text'])
        self.assertIn('人物赌注：缺卡', r3['text'])
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
        self.assertEqual(r['checks']['dialogue'], 'pass', r['text'])
        self.assertGreaterEqual(r['stats']['longest_exchange'], 3)
        self.assertLess(r['stats']['short_unexcused_share'], 0.45)

    def test_chinese_plain_format_parses_and_skips_length_metrics(self):
        text = scene('姐姐在切菜，弟弟站在门口。\n\n姐\n    你什么时候搬？\n\n弟\n    周六。车已经找好了。\n\n姐\n    我不忙，就不能先听一声？\n\n弟\n    那……周六你帮我看着车？\n\n姐\n    看着车。行。\n')
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.md'
            p.write_text(text, encoding='utf-8')
            r = rs.review_file(p)
        self.assertEqual(r['checks']['dialogue'], 'pass')
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
        self.assertEqual(r['checks']['dialogue'], 'pass')


class AnchoringTests(unittest.TestCase):
    """3.4.0: 潜台词支点——场 3 v2 钥匙段（修复前）必须报；有前文支点的省略与修复稿不报。"""

    def test_key_segment_is_flagged_first_with_fixes(self):
        r = rs.review_file(S3_BAD, context=[V3, S2])
        self.assertEqual(r['verdict'], 'issues')
        it = next(i for i in r['issues'] if i['key'] == 'unanchored_subtext')
        self.assertIn('You have a key', it['evidence'])
        self.assertIn('指了指', it['evidence'])           # 只由动作行承载
        self.assertIn('…Yeah. Okay.', it['evidence'])    # 没人问
        self.assertEqual(r['anchoring']['candidates'][0]['refs'][0], 'key')
        self.assertTrue(r['anchoring']['candidates'][0]['load_bearing'])
        self.assertEqual(len(it['fixes']), 3)
        for f in it['fixes']:
            self.assertIn('这场变成', f)
            self.assertIn('影响后面', f)
        self.assertIn('[推论]', it['basis'])
        self.assertIn('S10', it['sources'])
        self.assertIn('改法', r['text'])
        self.assertLessEqual(chars(r['text']), 800)
        # 账本已声明的 lake house 不进问题，只进复核
        self.assertNotIn('lake house', it['evidence'])
        self.assertTrue(any('lake house' in x and '账本已声明' in x for x in r['review_needed']))

    def test_fixed_scene_and_prior_scenes_pass(self):
        for path in (S3_OK, S2, V3):
            r = rs.review_file(path)
            self.assertNotIn('unanchored_subtext', {i['key'] for i in r['issues']}, path.name)
        self.assertEqual(rs.review_file(S3_OK)['anchoring']['candidates'], [])

    def test_grounded_ellipsis_is_not_a_candidate(self):
        quotes = [e['quote'] for p in (V3, S2) for e in rs.review_file(p)['anchoring']['candidates']]
        for line in ('Sloane, you might want to step back.', 'Nothing.', 'Everything.'):
            self.assertFalse(any(line in q for q in quotes), line)
        # "my phone's right here"：指着画面里的东西，本句即支点
        planted = [e['refs'][0] for e in rs.review_file(V3)['anchoring']['planted']]
        self.assertIn('phone', planted)

    def test_context_files_establish_terms(self):
        text = scene('两人在门口。\n\n**A**\nSo bring the ladder.\n\n**B**\nFine.\n\n**A**\nAnd the rope.\n\n**B**\nOkay.\n')
        prior = scene('**B**\nThe ladder is in the shed, with the rope.\n\n**A**\nGood.\n')
        with tempfile.TemporaryDirectory() as d:
            p, q = Path(d) / 's.md', Path(d) / 'prior.md'
            p.write_text(text, encoding='utf-8')
            q.write_text(prior, encoding='utf-8')
            without = rs.review_file(p)['anchoring']['candidates']
            with_ctx = rs.review_file(p, context=[q])['anchoring']['candidates']
        self.assertTrue(any(e['refs'][0] == 'ladder' for e in without))
        self.assertEqual(with_ctx, [])


class CliTests(unittest.TestCase):
    def test_exit_codes_and_json(self):
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = rs.main([str(V1), str(V3), '--json'])
        self.assertEqual(rc, 1)
        data = json.loads(buf.getvalue())
        self.assertEqual([d['checks']['dialogue'] for d in data], ['issues', 'pass'])
        self.assertIn('thresholds', data[0])
        with redirect_stdout(io.StringIO()):
            self.assertEqual(rs.main([str(V3)]), 1)  # 3.5.0：缺赌注卡即报问题
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'ok.md'
            p.write_text(POSITIVE, encoding='utf-8')
            with redirect_stdout(io.StringIO()):
                self.assertEqual(rs.main([str(p)]), 0)
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
        for code in ('S1', 'S2', 'S3', 'S4', 'S5', 'S6', 'S7', 'S8', 'S9', 'S10', 'S11', 'S12'):
            self.assertRegex(src, r'\| ' + code + r' \|')
        self.assertIn('[推论', src)
        self.assertIn('不改稿', skill)


CARD_HEAD = ('## 本场赌注\n\n| 人物 | 持续赌注（出处） | 此刻向谁要什么 | 怕失去什么 | 为什么是现在 | 说出口（逐字台词）／不说的理由与代价 | 场末 |\n'
             '|---|---|---|---|---|---|---|\n')
TRYOUT_BODY = ('更衣室，两人各自系鞋带。\n\n**MAYA**\nThey posted the list for Friday. You saw it?\n\n**JON**\nI saw it. Two spots.\n\n'
               '**MAYA**\nIf you go, they only need one of us.\n\n**JON**\nMy dad gave me one year. This is the year.\n\n'
               '**MAYA**\nSo you\'re going.\n\n**JON**\nI\'m going. I\'m sorry.\n')
POSITIVE = CARD_HEAD + (
    '| Maya | 周五试训名额（测试设定） | 向 Jon 要他别去 | 名额只剩一个 | 名单刚贴出 | "If you go, they only need one of us." | 没得到；代价：两人同去竞争 |\n'
    '| Jon | 家里只供一年（测试设定） | 向 Maya 要她理解 | 回老家 | 同上 | "My dad gave me one year." | 得到一半；代价：Maya 不再说话 |\n\n') + scene(TRYOUT_BODY)


def review_text(text, **kw):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 's.md'
        p.write_text(text, encoding='utf-8')
        return rs.review_file(p, **kw)


class StakesTests(unittest.TestCase):
    """3.5.0: 人物赌注——写台词前的卡与正文逐字核对；EP03 场 4 v3（用户 2026-09-23 否决"平铺说话"）为校准样本。"""

    def test_ep03_s04_without_card_is_flagged_first(self):
        r = rs.review_file(EP03_S4)
        self.assertEqual(r['checks']['stakes'], 'missing')
        self.assertEqual(r['issues'][0]['key'], 'stakes')
        self.assertIn('Diego 4 句', r['issues'][0]['evidence'])
        self.assertIn('Isa 3 句', r['issues'][0]['evidence'])
        self.assertIn('S6', r['issues'][0]['sources'])
        self.assertIn('人物赌注：缺卡', r['text'])
        self.assertLessEqual(chars(r['text']), 800)

    def test_ep03_s04_card_backfilled_from_draft_shows_isa_never_voices(self):
        r = rs.review_file(EP03_S4_CARD)
        self.assertEqual(r['checks']['stakes'], 'issues')
        it = r['issues'][0]
        self.assertEqual(it['title'], '人物赌注没落到台词')
        self.assertIn('Isa 上了卡', it['evidence'])
        self.assertIn('全额奖学金', it['evidence'])
        self.assertNotIn('Diego 上了卡', it['evidence'])  # Diego 的那句逐字在正文里、由本人说
        self.assertEqual([v['who'] for v in r['stakes']['voiced']], ['Diego'])
        review = ' '.join(r['stakes']['review'])
        self.assertIn('没人再说话', review)                 # Diego 说出口后无人接
        self.assertIn('这句说的是不是这件事', review)          # 语义交模型复核，脚本不判
        self.assertIn('Isa 场末"推迟"没写代价', review)       # 被接住收掉的欲望

    def test_positive_scene_passes_both_checks(self):
        r = review_text(POSITIVE)
        self.assertEqual(r['checks'], {'dialogue': 'pass', 'stakes': 'pass'}, r['text'])
        self.assertEqual(r['verdict'], 'pass')
        self.assertEqual({v['who'] for v in r['stakes']['voiced']}, {'Maya', 'Jon'})
        self.assertTrue(all(v.get('reply') for v in r['stakes']['voiced']))
        self.assertIn('人物赌注：说出口', r['text'])

    def test_quote_not_in_body_or_wrong_speaker_is_mismatch(self):
        text = CARD_HEAD + (
            '| Maya | 名额（测试） | 要他别去 | 名额 | 名单 | "I need this spot." | 没得到；代价：同去 |\n'
            '| Jon | 一年（测试） | 要理解 | 回家 | 同上 | "If you go, they only need one of us." | 得到一半；代价：沉默 |\n\n') + scene(TRYOUT_BODY)
        r = review_text(text)
        ev = r['issues'][0]['evidence']
        self.assertIn('"I need this spot."不在正文里', ev)
        self.assertIn('正文里是 Maya 说的', ev)
        self.assertEqual(r['checks']['stakes'], 'issues')

    def test_all_withheld_needs_registered_exception(self):
        rows = ('| Maya | 名额（测试） | 要他别去 | 名额 | 名单 | 不说：理由 怕他真的放弃；代价 他以为她不在乎 | 没得到；代价：同去 |\n'
                '| Jon | 一年（测试） | 要理解 | 回家 | 同上 | 不说：理由 说了像施压；代价 她不知道他的期限 | 推迟；代价：误会延续 |\n')
        r = review_text(CARD_HEAD + rows + '\n' + scene(TRYOUT_BODY))
        self.assertEqual(r['checks']['stakes'], 'issues')
        self.assertIn('全场没有一个人把自己的赌注说出口', r['issues'][0]['evidence'])
        r2 = review_text(CARD_HEAD + rows + '\n本场不说出口：余韵戏，赌注已在上一场说过\n\n' + scene(TRYOUT_BODY))
        self.assertEqual(r2['checks']['stakes'], 'excepted')
        self.assertNotIn('stakes', {i['key'] for i in r2['issues']})
        self.assertIn('已登记例外', r2['review_needed'][0])

    def test_withheld_without_reason_and_cost_is_flagged(self):
        text = CARD_HEAD + (
            '| Maya | 名额（测试） | 要他别去 | 名额 | 名单 | "If you go, they only need one of us." | 没得到；代价：同去 |\n'
            '| Jon | 一年（测试） | 要理解 | 回家 | 同上 | 不说 | 推迟 |\n\n') + scene(TRYOUT_BODY)
        r = review_text(text)
        self.assertIn('Jon 上了卡，但既没有说出口的台词，也没写不说的理由与代价', r['issues'][0]['evidence'])

    def test_main_speaker_missing_from_card(self):
        text = CARD_HEAD + '| Maya | 名额（测试） | 要他别去 | 名额 | 名单 | "If you go, they only need one of us." | 没得到；代价：同去 |\n\n' + scene(TRYOUT_BODY)
        r = review_text(text)
        self.assertIn('Jon 说了 3 句，卡上没有他此刻要什么', r['issues'][0]['evidence'])

    def test_voiced_stake_is_not_unanchored_subtext(self):
        """探针：3.4.0 会把 Isa「Not my scholarship.」判为潜台词无支点，逼人物解释自己的赌注；卡上有出处时不再报。"""
        body = EP03_S4.read_text(encoding='utf-8').replace("That's fair.", 'Not my scholarship.')
        without = review_text(body)
        self.assertTrue(any('scholarship' in e['refs'][0] for e in without['anchoring']['candidates']))
        card = CARD_HEAD + ('| Isa | 全额奖学金（ip.md 人物表 Isaiah Marsh） | 要 Diego 别再提 | 奖学金 | 周一 | "Not my scholarship." | 推迟；代价：Diego 不信他 |\n'
                            '| Diego | 补测（ip.md Diego） | 要一句信任 | 被刷 | 周一 | "Monday they decide if I even get to take the test." | 没得到；代价：没解决 |\n\n')
        with_card = review_text(body.replace('## 剧本页', card + '## 剧本页', 1))
        self.assertFalse(any('scholarship' in e['refs'][0] for e in with_card['anchoring']['candidates']))
        self.assertEqual(with_card['checks']['stakes'], 'pass')

    def test_quiet_and_single_speaker_scenes_are_not_asked_for_cards(self):
        quiet = review_text(scene('两人对坐。\n\n**A**\nStay.\n\n**B**\nOkay.\n'))
        self.assertEqual(quiet['checks']['stakes'], 'n/a')
        solo = review_text(scene('他对着镜子。\n\n**A**\nOne.\n\n**A**\nTwo.\n\n**A**\nThree.\n\n**A**\nFour.\n'))
        self.assertEqual(solo['checks']['stakes'], 'n/a')

    def test_docs_make_the_card_a_pre_dialogue_artifact(self):
        tpl = (ROOT / 'templates' / 'script-scene.md').read_text(encoding='utf-8')
        self.assertLess(tpl.index('## 本场赌注'), tpl.index('## 剧本页'))
        s3c = (ROOT / 'references' / 'stage-3c-script.md').read_text(encoding='utf-8')
        self.assertIn('本场赌注', s3c)
        self.assertLess(s3c.index('3c.0b'), s3c.index('3c.1'))
        ledger = (ROOT / 'references' / 'preference-ledger.md').read_text(encoding='utf-8')
        self.assertIn('2026-09-23', ledger)
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('本场赌注', skill)


if __name__ == '__main__':
    unittest.main()
