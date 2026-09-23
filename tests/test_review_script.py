"""3.3.0: 出稿后对白 review——THE ORDER EP02 场 1 v1 必须判为有问题，v3 对白连通必须通过；安静戏与有理由的短句不误判。
3.5.0 / 3.6.0 的赌注卡与场面轨在 3.7.0 合为事件轨（checks.events）；这些旧样本没有事件轨，整体 verdict 为 issues、checks.events = missing。"""
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
        self.assertEqual(r['checks']['events'], 'missing')

    def test_v3_passes_and_is_clearly_better(self):
        r1, r3 = rs.review_file(V1), rs.review_file(V3)
        self.assertEqual(r3['checks']['dialogue'], 'pass')
        self.assertEqual(r3['checks']['events'], 'missing')
        self.assertEqual([i['key'] for i in r3['issues']], ['events'])  # 3.7.0：赌注卡与场面轨合为事件轨，旧样本缺
        self.assertEqual(r3['stats']['offscreen_lines'], [])
        self.assertGreaterEqual(r3['stats']['longest_exchange'], 5)
        self.assertGreater(r3['stats']['conversation_share'], r1['stats']['conversation_share'] + 0.4)
        self.assertGreater(r3['stats']['mean_words'], r1['stats']['mean_words'] + 2)
        self.assertLess(r3['stats']['third_party_jump_share'], r1['stats']['third_party_jump_share'])
        self.assertIn('对白连通通过', r3['text'])
        self.assertIn('事件轨：缺事件轨', r3['text'])
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
            self.assertEqual(rs.main([str(V3)]), 1)  # 缺事件轨即报问题
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


EV_HEAD = ('| # | 谁 → 对谁 | 变化：进 → 出（类别） | 说出口（逐字）／不说：理由；代价 | 删掉损失 | 地点（子空间） | 活动 | 时间 | 锚句（逐字） | 估时 s |\n'
           '|---|---|---|---|---|---|---|---|---|---|\n')
TRYOUT_BODY = ('更衣室，两人各自系鞋带。\n\n**MAYA**\nThey posted the list for Friday. You saw it?\n\n**JON**\nI saw it. Two spots.\n\n'
               '**MAYA**\nIf you go, they only need one of us.\n\n**JON**\nMy dad gave me one year. This is the year.\n\n'
               '**MAYA**\nSo you\'re going.\n\n**JON**\nI\'m going. I\'m sorry.\n')
TRYOUT_CAST = ('- **Maya**｜持续赌注：周五试训名额（测试设定）｜此刻向 Jon 要：他别去｜怕：名额只剩一个｜为什么是现在：名单刚贴出\n'
               '- **Jon**｜持续赌注：家里只供一年（测试设定）｜此刻向 Maya 要：她理解｜怕：回老家｜为什么是现在：名单刚贴出\n\n')
ROW_MAYA = '| 1 | Maya → Jon | Jon：以为只是看名单 → 知道 Maya 要他别去（信息） | {maya} | Maya 的要求 | 更衣室 | 系鞋带 | — | If you go, they only need one of us. | 3 |\n'
ROW_JON = '| 2 | Jon → Maya | Maya：不知道他的期限 → 知道他家只给一年（信息） | {jon} | Jon 的赌注 | 更衣室 | 系鞋带 | 连续 | My dad gave me one year. | 3 |\n'
ROW_END = '| 3 | Jon → Maya | Maya：要他别去 → 他还是去（没得到；代价：两人同去竞争） | — | 结果 | 更衣室 | 系鞋带 | 连续 | I\'m going. I\'m sorry. | 3 |\n'


def tryout(maya='"If you go, they only need one of us."', jon='"My dad gave me one year."', cast=TRYOUT_CAST, extra=''):
    return ('## 事件轨\n\n' + cast + EV_HEAD + ROW_MAYA.format(maya=maya) + ROW_JON.format(jon=jon) + ROW_END + '\n'
            + extra + '总估时 ≈ 11 s\n\n' + scene(TRYOUT_BODY))


POSITIVE = tryout()


def review_text(text, **kw):
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / 's.md'
        p.write_text(text, encoding='utf-8')
        return rs.review_file(p, **kw)


class EventStakesTests(unittest.TestCase):
    """3.5.0 的赌注核对挪到事件轨：人物清单写谁要什么，行上逐字核对说出口的句子；
    EP03 场 4 v3（用户 2026-09-23 否决"平铺说话"）为校准样本。"""

    def test_ep03_s04_without_track_is_flagged_first(self):
        r = rs.review_file(EP03_S4)
        self.assertEqual(r['checks']['events'], 'missing')
        self.assertEqual(r['issues'][0]['key'], 'events')
        self.assertIn('Diego 4 句', r['issues'][0]['evidence'])
        self.assertIn('Isa 3 句', r['issues'][0]['evidence'])
        self.assertIn('S6', r['issues'][0]['sources'])
        self.assertIn('事件轨：缺事件轨', r['text'])
        self.assertLessEqual(chars(r['text']), 800)

    def test_ep03_s04_v3_backfilled_shows_isa_never_voices(self):
        r = rs.review_file(EP03_S4_V3)
        self.assertEqual(r['checks']['events'], 'issues')
        it = r['issues'][0]
        self.assertEqual(it['title'], '事件轨有问题')
        self.assertIn('Isa 在"人物"里，但哪一行都没说出口', it['evidence'])
        self.assertIn('全额奖学金', it['evidence'])
        self.assertNotIn('Diego 在"人物"里', it['evidence'])  # Diego 的那句逐字在正文里、由本人说
        self.assertEqual([v['who'] for v in r['events']['voiced']], ['Diego'])
        review = ' '.join(r['events']['review'])
        self.assertIn('没人再说话', review)                 # Diego 说出口后无人接
        self.assertIn('这句说的是不是这件事', review)          # 语义交模型复核，脚本不判
        self.assertIn('Isa「推迟」没写代价', review)          # 被接住收掉的欲望

    def test_positive_scene_passes(self):
        r = review_text(POSITIVE)
        self.assertEqual(r['checks'], {'dialogue': 'pass', 'events': 'pass'}, r['text'])
        self.assertEqual(r['verdict'], 'pass')
        self.assertEqual({v['who'] for v in r['events']['voiced']}, {'Maya', 'Jon'})
        self.assertTrue(all(v.get('reply') for v in r['events']['voiced']))
        self.assertIn('说出口——', r['text'])
        self.assertEqual(r['events']['changes'], 3)

    def test_quote_not_in_body_or_wrong_speaker_is_mismatch(self):
        r = review_text(tryout(maya='"I need this spot."', jon='"If you go, they only need one of us."'))
        ev = r['issues'][0]['evidence']
        self.assertIn('"I need this spot."不在正文里', ev)
        self.assertIn('正文里是 Maya 说的', ev)
        self.assertEqual(r['checks']['events'], 'issues')

    def test_all_withheld_needs_registered_exception(self):
        maya, jon = '不说：理由 怕他真的放弃；代价 他以为她不在乎', '不说：理由 说了像施压；代价 她不知道他的期限'
        r = review_text(tryout(maya=maya, jon=jon))
        self.assertEqual(r['checks']['events'], 'issues')
        self.assertIn('全场没有一个人把自己要的说出口', r['issues'][0]['evidence'])
        r2 = review_text(tryout(maya=maya, jon=jon, extra='本场不说出口：余韵戏，赌注已在上一场说过\n\n'))
        self.assertEqual(r2['checks']['events'], 'excepted')
        self.assertNotIn('events', {i['key'] for i in r2['issues']})
        self.assertIn('已登记例外', r2['review_needed'][0])

    def test_withheld_without_reason_and_cost_is_flagged(self):
        r = review_text(tryout(jon='不说'))
        self.assertIn('Jon 在"人物"里，但哪一行都没说出口，也没写不说的理由与代价', r['issues'][0]['evidence'])

    def test_main_speaker_missing_from_cast(self):
        cast = TRYOUT_CAST.split('\n')[0] + '\n\n'
        r = review_text(tryout(cast=cast))
        ev = r['issues'][0]['evidence']
        self.assertIn('Jon 说了 3 句，"人物"里没有他此刻要什么', ev)
        self.assertIn('第 1 行的变化主体 Jon 不在"人物"里', ev)

    def test_voiced_stake_is_not_unanchored_subtext(self):
        """探针：3.4.0 会把 Isa「Not my scholarship.」判为潜台词无支点，逼人物解释自己的赌注；人物清单写了出处时不再报。"""
        body = EP03_S4.read_text(encoding='utf-8').replace("That's fair.", 'Not my scholarship.')
        without = review_text(body)
        self.assertTrue(any('scholarship' in e['refs'][0] for e in without['anchoring']['candidates']))
        track = ('## 事件轨\n\n- **Isa**｜持续赌注：全额奖学金（ip.md 人物表 Isaiah Marsh）｜此刻向 Diego 要：别再提｜怕：奖学金｜为什么是现在：周一\n'
                 '- **Diego**｜持续赌注：补测（ip.md Diego）｜此刻向 Isa 要：一句信任｜怕：被刷｜为什么是现在：周一\n\n' + EV_HEAD
                 + '| 1 | Isa → Diego | Diego：以为 Isa 只是道谢 → 听到 Isa 不许他碰奖学金（信息） | "Not my scholarship." | Isa 的赌注 | 跑道 | 跑步 | — | Not my scholarship. | 4 |\n'
                 '| 2 | Diego → Isa | Isa：只想把昨晚翻过去 → 知道 Diego 周一可能连补测都没有（信息） | "Monday they decide if I even get to take the test." | Diego 的赌注 | 跑道 | 跑步 | 连续 | Monday they decide | 20 |\n\n')
        with_track = review_text(body.replace('## 剧本页', track + '## 剧本页', 1))
        self.assertFalse(any('scholarship' in e['refs'][0] for e in with_track['anchoring']['candidates']))
        self.assertEqual(with_track['events']['problems'], [])

    def test_quiet_and_single_speaker_scenes_are_not_asked_for_tracks(self):
        quiet = review_text(scene('两人对坐。\n\n**A**\nStay.\n\n**B**\nOkay.\n'))
        self.assertEqual(quiet['checks']['events'], 'n/a')
        solo = review_text(scene('他对着镜子。\n\n**A**\nOne.\n\n**A**\nTwo.\n\n**A**\nThree.\n\n**A**\nFour.\n'))
        self.assertEqual(solo['checks']['events'], 'n/a')


EP03_S4_V3 = FIX / 'theorder-ep03-s04-v3-events.md'
EP03_S4_V4 = FIX / 'theorder-ep03-s04-v4-events.md'
EP03_S4_V41 = FIX / 'theorder-ep03-s04-v4.1-events.md'
EP03_S4_V41_CUT = FIX / 'theorder-ep03-s04-v4.1-cut-events.md'
EP03_S4_V41_LEGACY = FIX / 'theorder-ep03-s04-v4.1-track.md'
BULLPEN_ROW = '| 11 | Diego → Isa | 无（余韵：Isa 没答应，Diego 在等他） |'
LONG_BODY = ('天台，风很大。两个人靠着栏杆，楼下是整条街的车灯。她把外套拉紧，他把烟掐了又点上。远处有警笛，一辆接一辆开过去。\n\n'
             + ''.join(f'**MAYA**\nI keep thinking about the list they posted on Friday morning, number {i}.\n\n'
                       f'**JON**\nI keep thinking about it too, and I still do not know what to say, number {i}.\n\n' for i in range(4))
             + '她转身走向楼梯口。他没有跟。楼梯间的灯一盏一盏亮下去。门在她身后关上。风把他的烟吹灭了。\n')
ROOF_CAST = ('- **Maya**｜持续赌注：周五名单（测试）｜此刻向 Jon 要：一句留下｜怕：他不留｜为什么是现在：名单刚贴出\n'
             '- **Jon**｜持续赌注：家里的期限（测试）｜此刻向 Maya 要：她别逼他｜怕：说了就得走｜为什么是现在：同上\n\n')


def roof(rows, extra=''):
    return '## 事件轨\n\n' + ROOF_CAST + EV_HEAD + rows + '\n' + extra + '总估时 ≈ 40 s\n\n' + scene(LONG_BODY)


ROOF_ONE_CHANGE = ('| 1 | Maya → Jon | Jon：— → 被问住（信息） | "I keep thinking about the list they posted on Friday morning, number 0." | 两人卡住 | 天台（栏杆边） | 说话 | — | 天台，风很大。 | 28 |\n'
                   '| 2 | Jon → Maya | 无（余韵：她走、他不跟） | 不说：理由 说了就得走；代价 她走了 | 她走、他没跟 | 天台（楼梯口） | 说话 | 连续 | 她转身走向楼梯口。 | 12 |\n')


class EventProgressTests(unittest.TestCase):
    """3.7.0：推进只数变化，不数地点。EP03 场 4 v4（整场跑道、每段有事）通过并列复核；
    v4.1（加"几分钟后，牛棚边"，没有人得到或失去什么）报问题；v4.1 删掉牛棚为对照，通过。"""

    def test_v41_bullpen_is_flagged_as_a_segment_without_event(self):
        r = rs.review_file(EP03_S4_V41)
        self.assertEqual(r['checks']['events'], 'issues', r['text'])
        ev = next(i for i in r['issues'] if i['key'] == 'events')['evidence']
        self.assertIn('第 11 行换了地点（牛棚）、跳了时间（跳：几分钟后），却标为余韵、没有变化', ev)
        self.assertEqual((r['events']['changes'], r['events']['jumps'], len(r['events']['places'])), (9, 1, 2))
        self.assertTrue(any('余韵合计' in x for x in r['events']['review']))
        self.assertIn('S13', next(i for i in r['issues'] if i['key'] == 'events')['sources'])

    def test_v4_one_place_with_events_passes_with_diagnosis_review(self):
        for f in (EP03_S4_V4, EP03_S4_V41_CUT):
            r = rs.review_file(f)
            self.assertEqual(r['checks']['events'], 'pass', f.name + r['text'])
            self.assertEqual(r['events']['changes'], 9)
            self.assertEqual(len(r['events']['places']), 1)
            review = ' '.join(r['events']['review'])
            self.assertIn('全场一个地点、一种活动', review)       # 3.6 判"问题"，3.7 只列复核：先诊断缺什么
            self.assertIn('不为换景加段', review)
            self.assertIn('事件轨：9 次变化', r['text'])

    def test_bullpen_rewritten_as_repeat_of_isa_state_is_flagged(self):
        t = EP03_S4_V41.read_text(encoding='utf-8').replace(
            BULLPEN_ROW, '| 11 | Diego → Isa | Isa：领先一个身位过线 → 领先一个身位过线（推迟） |')
        ev = review_text(t)['events']['problems']
        self.assertTrue(any('进出相同' in x for x in ev), ev)
        t2 = EP03_S4_V41.read_text(encoding='utf-8').replace(
            BULLPEN_ROW, '| 11 | Diego → Isa | Isa：还坐着 → 不答，改成比最后一段直道（推迟） |')
        ev2 = review_text(t2)['events']['problems']
        self.assertTrue(any('与第 6 行相同：同一状态再演一遍' in x for x in ev2), ev2)

    def test_silent_subject_must_be_in_cast(self):
        """无台词的人也要进人物清单（3.5.0 只管说 ≥3 句的人，Diego 一句台词都没有）。"""
        t = EP03_S4_V41.read_text(encoding='utf-8').replace(
            BULLPEN_ROW, '| 11 | Diego → Isa | Diego：绑护腿 → 蹲在本垒板后等 Isa（关系） |')
        r = review_text(t)
        self.assertTrue(any('变化主体 Diego 不在"人物"里（不说话的人也要写持续赌注与此刻要什么）' in x
                            for x in r['events']['problems']), r['events']['problems'])

    def test_bullpen_with_stated_change_goes_to_deletion_test_with_evidence(self):
        """写得出变化就不报问题——但换地点 / 跳时间 / 无台词的行必须带着证据交模型做删除测试。脚本不判"是不是新的"。"""
        t = EP03_S4_V41.read_text(encoding='utf-8').replace(
            BULLPEN_ROW, '| 11 | Diego → Isa | Diego：绑护腿 → 蹲在本垒板后等 Isa（关系） |')
        t = t.replace('\n| # |', '- **Diego**｜持续赌注：补测未批（ip.md Diego 行）｜此刻向 Isa 要：投给他｜怕：周一被刷｜为什么是现在：Isa 刚没答应\n\n| # |', 1)
        t = t.replace('| 11 | Diego → Isa | Diego：绑护腿 → 蹲在本垒板后等 Isa（关系） | — |',
                      '| 11 | Diego → Isa | Diego：绑护腿 → 蹲在本垒板后等 Isa（关系） | 不说：理由 Isa 刚当着全队没答；代价 Isa 还坐着 |')
        r = review_text(t)
        self.assertEqual(r['events']['problems'], [])
        item = next(x for x in r['events']['review'] if x.startswith('第 11 行'))
        for part in ('换了地点（牛棚）', '跳了时间', '无台词', '删掉损失', 'Isa 作为对象的上一行', '删除测试'):
            self.assertIn(part, item)

    def test_linger_only_in_place(self):
        """余韵可以留（"队伍跑进太阳"），但不能把观众带到新地方。"""
        r = rs.review_file(EP03_S4_V41_CUT)
        self.assertEqual(r['events']['problems'], [])
        self.assertGreater(r['events']['linger_s'], 0)

    def test_too_few_changes_needs_registered_reason(self):
        r = review_text(roof(ROOF_ONE_CHANGE))
        self.assertGreaterEqual(r['events']['estimate'], 30)
        self.assertEqual(r['checks']['events'], 'issues')
        self.assertTrue(any('只有 1 行有变化' in x for x in r['events']['problems']))
        r2 = review_text(roof(ROOF_ONE_CHANGE, '本场静止：有意一镜到底，两人谁都不肯先走\n\n'))
        self.assertEqual(r2['checks']['events'], 'excepted', r2['text'])
        self.assertIn('已登记理由：有意一镜到底', ' '.join(r2['review_needed']))
        r3 = review_text(roof(ROOF_ONE_CHANGE, '本场单一画面：困住的压迫感\n\n'))  # 3.6 的登记写法仍认
        self.assertEqual(r3['checks']['events'], 'excepted')

    def test_anchor_must_be_verbatim_and_in_order(self):
        bad = ROOF_ONE_CHANGE.replace('她转身走向楼梯口。', '她走了。')
        r = review_text(roof(bad))
        self.assertIn('第 2 行锚句「她走了。」不在正文里', ' '.join(r['events']['problems']))
        swapped = ('| 1 | Maya → Jon | Jon：— → 被问住（信息） | — | 卡住 | 天台 | 说话 | — | 她转身走向楼梯口。 | 10 |\n'
                   '| 2 | Maya → Jon | Maya：等 → 走（决定） | — | 走 | 楼梯间 | 下楼 | 跳：稍后 | 天台，风很大。 | 10 |\n')
        r2 = review_text(roof(swapped))
        self.assertIn('顺序与正文不符', ' '.join(r2['events']['problems']))

    def test_long_wait_for_a_change_goes_to_model_review(self):
        long_body = ('天台，风很大。\n\n' + ''.join(f'**MAYA**\nI keep thinking about the list they posted on Friday morning, again and again, {i}.\n\n'
                                                 f'**JON**\nI keep thinking about it too, and I still do not know what I should say to you, {i}.\n\n' for i in range(10))
                     + '几分钟后，街角便利店。她站在冰柜前，他在门口。店员抬头看了他们一眼。收银机响了一声。\n')
        rows = ('| 1 | Maya → Jon | Jon：— → 被问住（信息） | "I keep thinking about the list" | 卡住 | 天台 | 说话 | — | I keep thinking about it too, and I still do not know what I should say to you, 9. | 45 |\n'
                '| 2 | Jon → Maya | Maya：等他开口 → 看见他跟她下了楼（关系） | 不说：理由 说了就得走；代价 她还在等 | 他跟着她 | 便利店 | 买东西 | 跳：几分钟后 | 几分钟后，街角便利店。 | 6 |\n')
        r = review_text('## 事件轨\n\n' + ROOF_CAST + EV_HEAD + rows + '\n' + scene(long_body))
        self.assertEqual(r['events']['problems'], [], r['text'])
        self.assertTrue(any('观众等了' in x and '第 1 行' in x for x in r['events']['review']))

    def test_legacy_card_and_track_are_reported_as_missing(self):
        r = rs.review_file(EP03_S4_V41_LEGACY)
        self.assertEqual(r['checks']['events'], 'missing')
        self.assertIn('旧格式', r['issues'][0]['evidence'])

    def test_text_estimate_is_closer_than_draft_estimate(self):
        """剧本自报 57 / 69 s，分镜实排 74 / 88 s；文本估时落在两者之间、误差 ≤ 16%（[推论]，5 场校准见 dialogue-review-sources.md §三）。"""
        for f, produced in ((EP03_S4_V4, 74), (EP03_S4_V41, 88)):
            e = rs.review_file(f)['events']
            self.assertGreater(e['estimate'], e['declared'])
            self.assertLess(abs(e['estimate'] / produced - 1), 0.16)

    def test_production_overrun_is_a_reminder_not_a_return(self):
        """3.6.1：对 film-director 是告知不是锁定；超 20% 只提醒，回不回剧本层由用户定。"""
        r = rs.review_file(EP03_S4_V41_CUT, production_total=88)
        self.assertIn('production_over', r['events'])
        self.assertIn('提醒，是否回剧本层由用户定', r['text'].splitlines()[0])
        self.assertIn('由用户定', r['events']['review'][0])
        self.assertNotIn('events', {i['key'] for i in r['issues']})  # 提醒不是问题
        ok = rs.review_file(EP03_S4_V41_CUT, production_total=r['events']['declared'] * 1.1)
        self.assertNotIn('production_over', ok['events'])
        with redirect_stdout(io.StringIO()):
            rs.main([str(EP03_S4_V41_CUT), '--production-total', '88'])

    def test_wps_and_action_sec_are_parameters(self):
        saved = dict(rs.THRESHOLDS)
        try:
            base = rs.review_file(EP03_S4_V4)['events']['estimate']
            with redirect_stdout(io.StringIO()):
                rs.main([str(EP03_S4_V4), '--wps', '2.5', '--action-sec', '2'])
            slow = rs.review_file(EP03_S4_V4)['events']['estimate']
            self.assertGreater(slow, base)
        finally:
            rs.THRESHOLDS.clear()
            rs.THRESHOLDS.update(saved)


class DocsWiringTests(unittest.TestCase):
    def test_template_has_one_event_track_before_the_body(self):
        tpl = (ROOT / 'templates' / 'script-scene.md').read_text(encoding='utf-8')
        self.assertLess(tpl.index('## 事件轨'), tpl.index('## 剧本页'))
        self.assertNotIn('## 本场赌注', tpl)
        self.assertNotIn('## 场面轨', tpl)
        for col in ('谁 → 对谁', '变化', '删掉损失', '地点', '活动', '时间', '锚句', '估时'):
            self.assertIn(col, tpl)  # film-director 读场地清单要的列仍在

    def test_docs_route_monotony_to_diagnosis_before_scene_change(self):
        s3c = (ROOT / 'references' / 'stage-3c-script.md').read_text(encoding='utf-8')
        self.assertIn('事件轨', s3c)
        self.assertLess(s3c.index('3c.0b'), s3c.index('3c.1 '))
        self.assertNotIn('Diego 在牛棚里蹲着等他）', s3c)        # 3.6 把 v4.1 当正样本的示例已撤
        self.assertIn('先诊断', s3c)
        contract = (ROOT / 'references' / 'execution-contract.md').read_text(encoding='utf-8')
        self.assertIn('删掉损失', contract)                     # 加段 / 换景的改法选项要写出新行
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        self.assertIn('事件轨', skill)
        self.assertIn('告知，不锁定', skill)
        self.assertIn('20%', skill)
        self.assertNotIn('台词与场景是生产侧的锁定输入', skill)
        src = (ROOT / 'references' / 'dialogue-review-sources.md').read_text(encoding='utf-8')
        self.assertRegex(src, r'\| S13 \|')
        ledger = (ROOT / 'references' / 'preference-ledger.md').read_text(encoding='utf-8')
        self.assertIn('这 16 s 存在的意义是', ledger)
        self.assertIn('整个场 4 都是球场跑步', ledger)


if __name__ == '__main__':
    unittest.main()
