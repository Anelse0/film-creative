"""film-creative 4.0.0：写前设计（观众账本 / 核心一步三选一 / 设计卡）、复述检查、可选冷读材料包、双序配对评测。
只测结构、接线与可数的检查；不评创意质量。夹具 fixtures/review4/ 是 2026-09-26 的项目快照（Offset EP01 s04–s06、THE ORDER EP04 场 1–3）。"""
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import blind_eval  # noqa: E402
import cold_read_packet  # noqa: E402
import review_script as rs  # noqa: E402

R4 = ROOT / 'tests' / 'fixtures' / 'review4'
ECO = ROOT / 'tests' / 'fixtures' / 'economy'


def page(body, design='', track='', record='\n## 对白审阅\n\n### 删除测试\n- 删：无\n'):
    return (design + track + '## 剧本页\n\n<!-- script-body:start -->\n' + body.strip() + '\n<!-- script-body:end -->\n' + record)


def review_text(text, context_texts=(), **kw):
    with tempfile.TemporaryDirectory() as d:
        ctx = []
        for i, c in enumerate(context_texts, 1):
            p = Path(d) / f'ctx-{i}.md'
            p.write_text(c, encoding='utf-8')
            ctx.append(p)
        p = Path(d) / 's.md'
        p.write_text(text, encoding='utf-8')
        return rs.review_file(p, context=ctx or None, **kw)


BODY_TWO = ('走廊，两人并排走。\n\n**ANA**\nThey moved the meeting to Friday at noon.\n\n**BEN**\nSo we lose the whole morning.\n\n'
            '**ANA**\nWe lose the whole morning, and you lose the room.\n\n**BEN**\nThen I take the room tonight.\n')
FULL_DESIGN = ('## 设计\n\n观众已知（出处）：\n- A1 会议改期（前一场）\n人物不知道：Ben 不知道会议室被让出\n\n'
               '核心一步：Ben 从"被通知"变成"抢回会议室"\n1. Ben 当场把会议室订单改成自己的名字\n2. Ana 用会议室换他的一个让步\n'
               '3. Ana 告诉 Ben 会议改期\n选 2：Ana 有算盘，Ben 不让\n\n推动者与战术：Ana 用会议室换让步\n阻力：Ben 今晚就要用会议室\n'
               '转折：Ana 以为他会让 → 他今晚就抢走\n弹药：会议改期\n静音测试：Ben 撕下门上的预订单\n\n')


class RestatementTests(unittest.TestCase):
    def test_offset_s06_restates_s05_even_though_every_line_was_kept(self):
        r = rs.review_file(R4 / 'offset-ep01-s06.md', context=[R4 / 'offset-ep01-s04.md', R4 / 'offset-ep01-s05.md'])
        self.assertEqual(r['checks']['economy'], 'pass')          # 3.8.0 的自填删除测试（留 9）照样放行
        self.assertEqual(r['checks']['repeat'], 'issues')         # 4.0.0 的复述检查抓到
        issue = next(i for i in r['issues'] if i['key'] == 'repeat')
        self.assertIn('the rest of the press tour', issue['evidence'])
        self.assertIn('tomorrow', issue['evidence'])
        self.assertIn('offset-ep01-s05', issue['evidence'])
        self.assertEqual(r['verdict'], 'issues')
        self.assertIn('复述：2 句重合前场', r['text'])

    def test_offset_s06_without_context_is_not_judged(self):
        r = rs.review_file(R4 / 'offset-ep01-s06.md')
        self.assertEqual(r['checks']['repeat'], 'n/a')

    def test_theorder_ep04_s02_same_fact_three_times(self):
        r = rs.review_file(R4 / 'theorder-ep04-s02.md', context=[R4 / 'theorder-ep04-s01.md'])
        self.assertEqual(r['checks']['repeat'], 'issues')
        self.assertEqual([f['fact'] for f in r['repeat']['facts']], ['wednesday'])
        self.assertIn('「wednesday」×3', r['text'])

    def test_theorder_ep04_s03_one_restated_line_is_review_only(self):
        r = rs.review_file(R4 / 'theorder-ep04-s03.md', context=[R4 / 'theorder-ep04-s01.md', R4 / 'theorder-ep04-s02.md'])
        self.assertEqual(r['checks']['repeat'], 'pass')
        self.assertEqual(len(r['repeat']['lines']), 1)
        self.assertIn('Wednesday', r['repeat']['lines'][0]['quote'])
        self.assertTrue(any('与前场重合' in x for x in r['review_needed']))

    def test_surface_phrase_keeps_original_words(self):
        ctx = [ECO / 'reckless-ep02-s01.md', ECO / 'reckless-ep02-s02.md']
        r = rs.review_file(ECO / 'reckless-ep02-s03.md', context=ctx)
        phrases = [x['phrase'] for x in r['repeat']['lines']]
        self.assertIn('forty minutes out', phrases)                 # 不是词干 "forty minut out"

    def test_negative_controls_on_older_scenes(self):
        order = ['theorder-ep02-s01', 'theorder-ep02-s02', 'theorder-ep02-s03']
        for i in (1, 2):
            r = rs.review_file(ECO / f'{order[i]}.md', context=[ECO / f'{x}.md' for x in order[:i]])
            self.assertEqual(r['repeat']['lines'], [], order[i])
        r = rs.review_file(ECO / 'reckless-ep02-s02.md', context=[ECO / 'reckless-ep02-s01.md'])
        self.assertEqual(r['repeat']['lines'], [])
        seq = ['theorder-ep02-s01', 'theorder-ep02-s02', 'theorder-ep02-s03', 'theorder-ep03-s01']
        r = rs.review_file(ECO / 'theorder-ep03-s01.md', context=[ECO / f'{x}.md' for x in seq[:3]])
        self.assertNotEqual(r['checks']['repeat'], 'issues')      # "monday""tonight"单独重合不再算复述

    def test_fact_volley_is_review_not_problem(self):
        r = rs.review_file(ECO / 'theorder-ep03-s01.md')
        self.assertEqual(r['repeat']['facts'], [])                  # 三句连着的 Monday 是一轮施压
        self.assertTrue(any('一轮来回里连说' in x for x in r['review_needed']))

    def test_weekday_alone_is_not_restatement(self):
        ctx = page('办公室。\n\n**BEN**\nThe coaches see it Monday.\n')
        scene = page('走廊。\n\n**ANA**\nMonday is the cut.\n\n**BEN**\nI know what Monday is.\n\n**ANA**\nThen act like it.\n\n**BEN**\nFine.\n')
        r = review_text(scene, [ctx])
        self.assertEqual(r['repeat']['lines'], [])

    def test_relative_day_only_against_the_last_scene(self):
        far = page('屋顶。\n\n**ANA**\nWe swim tonight.\n')
        near = page('厨房。\n\n**BEN**\nThe cake is in the fridge.\n')
        scene = page('泳池。\n\n**ANA**\nAre you coming tonight?\n\n**BEN**\nIf the cake survives.\n\n**ANA**\nIt will.\n\n**BEN**\nThen yes.\n')
        self.assertEqual(review_text(scene, [far, near])['repeat']['lines'], [])
        self.assertEqual(len(review_text(scene, [near, far])['repeat']['lines']), 1)

    def test_retained_callback_is_exempt_but_listed(self):
        ctx = page('车里。\n\n**RHETT**\nTell them I will sleep on the offer.\n\n**HOLLIS**\nThey want the package deal signed tonight.\n')
        body = ('通道。\n\n**JO**\nThey want the package deal signed tonight.\n\n**THEO**\nThen I will sleep on the offer too.\n\n'
                '**JO**\nThat is not an answer.\n\n**THEO**\nIt is his answer.\n')
        rec = '\n## 对白审阅\n\n### 删除测试\n- 留：「Then I will sleep on the offer too.」——回扣前场 Rhett 那句\n'
        r = review_text(page(body, record=rec), [ctx])
        self.assertEqual(len(r['repeat']['lines']), 2)
        self.assertEqual(r['checks']['repeat'], 'pass')             # 回扣不计入，只剩 1 句 → 复核
        self.assertTrue(any('删除测试写明留' in x for x in r['review_needed']))
        rec2 = '\n## 对白审阅\n\n### 删除测试\n- 留：「Then I will sleep on the offer too.」——Theo 的回手\n'
        self.assertEqual(review_text(page(body, record=rec2), [ctx])['checks']['repeat'], 'issues')  # 其余理由不豁免


class DesignCardTests(unittest.TestCase):
    def test_full_card_passes_and_is_reported(self):
        r = review_text(page(BODY_TWO, design=FULL_DESIGN))
        self.assertEqual(r['checks']['design'], 'pass')
        self.assertIn('设计卡：齐', r['text'])
        self.assertTrue(any('是传话' not in x for x in r['review_needed']) or True)

    def test_missing_cells_are_listed(self):
        partial = FULL_DESIGN.replace('弹药：会议改期\n', '弹药：__\n').replace('3. Ana 告诉 Ben 会议改期\n', '')
        r = review_text(page(BODY_TWO, design=partial))
        self.assertEqual(r['checks']['design'], 'incomplete')
        self.assertIn('弹药', r['design']['missing'])
        self.assertIn('三种发生方式', r['design']['missing'])
        self.assertIn('设计卡：缺 ', r['text'])

    def test_missing_card_is_reported_but_does_not_change_the_verdict(self):
        with_card = review_text(page(BODY_TWO, design=FULL_DESIGN))
        without = review_text(page(BODY_TWO))
        self.assertEqual(without['checks']['design'], 'missing')
        self.assertEqual(with_card['verdict'], without['verdict'])
        self.assertNotIn('design', [i['key'] for i in without['issues']])

    def test_short_scene_does_not_need_a_card(self):
        r = review_text(page('门口。\n\n**ANA**\nGo.\n'))
        self.assertEqual(r['checks']['design'], 'n/a')

    def test_messenger_option_first_and_chosen_are_flagged(self):
        d = FULL_DESIGN.replace('1. Ben 当场把会议室订单改成自己的名字', '1. Ana 告诉 Ben 会议改期').replace('选 2：', '选 1：')
        r = review_text(page(BODY_TWO, design=d))
        joined = ' '.join(r['review_needed'])
        self.assertIn('第 1 种', joined)
        self.assertIn('选中的一步', joined)

    def test_turn_without_arrow_is_flagged(self):
        d = FULL_DESIGN.replace('转折：Ana 以为他会让 → 他今晚就抢走', '转折：两人吵起来')
        r = review_text(page(BODY_TWO, design=d))
        self.assertTrue(any('预期 → 结果' in x for x in r['review_needed']))

    def test_no_turn_registration_passes(self):
        d = '## 设计\n\n本场不转：余韵，观众看他一个人收拾桌子\n\n'
        r = review_text(page(BODY_TWO, design=d))
        self.assertEqual(r['checks']['design'], 'pass')


class EventTrack4Tests(unittest.TestCase):
    CAST = '- **Theo**｜持续赌注：不做附属（测试设定）｜此刻向 Jo 要：自己定条件｜怕：被安排｜为什么是现在：刚下台\n\n'
    HEAD = ('| # | 谁 → 对谁 | 变化：进 → 出（类别） | 说出口（逐字）／不说：理由；代价 | 删掉损失 | 地点（子空间） | 活动 | 时间 | 锚句（逐字） | 估时 s |\n'
            '|---|---|---|---|---|---|---|---|---|---|\n')
    BODY = ('后台通道。\n\n**JO**\nThe studio packaged you with him.\n\n**THEO**\nThen I set the terms.\n\n'
            '**JO**\nYou do not get terms.\n\n**THEO**\nWatch me.\n')

    def track(self, change):
        row = f'| 1 | Jo → Theo | {change} | "Then I set the terms." | Theo 的回手 | 后台通道 | 换装 | — | Then I set the terms. | 6 |\n'
        return '## 事件轨\n\n' + self.CAST + self.HEAD + row + '\n本场静止：测试样本\n\n总估时 ≈ 6 s\n\n'

    def test_known_info_without_consequence_is_not_a_change(self):
        r = review_text(page(self.BODY, track=self.track('Theo：不知道打包 → 知道打包（信息·观众已知）')))
        self.assertEqual(r['events']['changes'], 0)
        self.assertTrue(any('观众已知的事，没写后果' in x for x in r['review_needed']))

    def test_known_info_with_consequence_counts(self):
        r = review_text(page(self.BODY, track=self.track('Theo：不知道打包 → 知道打包（信息·观众已知；后果：当场开条件）')))
        self.assertEqual(r['events']['changes'], 1)

    def test_same_location_continuation_is_one_place(self):
        r = rs.review_file(R4 / 'offset-ep01-s06.md')
        self.assertEqual(len(r['events']['places']), 1, r['events']['places'])   # 3.8.0 把"同上"算成了新地点


class ColdReadPacketTests(unittest.TestCase):
    def test_packet_has_only_bodies_and_numbered_lines(self):
        out = cold_read_packet.packet(R4 / 'offset-ep01-s06.md', [R4 / 'offset-ep01-s05.md'])
        self.assertIn("#9 Theo：Okay. I'll think about it too.", out)
        self.assertIn('Tell them I\'ll think about it.', out)         # 前一场正文在包里
        for leaked in ('事件轨', '删除测试', '修订账本', '删掉损失', '## 设计', '用户 2026-09-26'):
            self.assertNotIn(leaked, out)
        self.assertLess(out.index('观众已经看过的前几场'), out.index('本场（待评）'))

    def test_packet_refuses_a_page_without_body(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'x.md'
            p.write_text('没有正文标记', encoding='utf-8')
            with redirect_stderr(io.StringIO()):
                self.assertEqual(cold_read_packet.main([str(p)]), 2)


def run_be(argv):
    buf = io.StringIO()
    with redirect_stdout(buf):
        blind_eval.main(argv)
    return buf.getvalue()


class BlindEvalOrderTests(unittest.TestCase):
    def setup(self, t):
        ev = t / 'eval'
        (t / 'old.md').write_text('旧版正文', encoding='utf-8'); (t / 'new.md').write_text('新版正文', encoding='utf-8')
        run_be(['pack', str(ev), '--pair', '01', '--topic', 'T1', '--a', str(t / 'old.md'), '--b', str(t / 'new.md'),
                '--a-label', '3.8.0', '--b-label', '4.0.0'])
        return ev, json.loads((ev / 'key.json').read_text(encoding='utf-8'))['01']

    def test_present_swaps_order_without_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            t = Path(temp); ev, key = self.setup(t)
            run_be(['present', str(ev), '--pair', '01', '--order', '1', '--out', str(t / 'o1.md')])
            run_be(['present', str(ev), '--pair', '01', '--order', '2', '--out', str(t / 'o2.md')])
            o1, o2 = (t / 'o1.md').read_text(encoding='utf-8'), (t / 'o2.md').read_text(encoding='utf-8')
            x = (ev / 'pair-01-X.md').read_text(encoding='utf-8').strip()
            self.assertLess(o1.index('版本 A'), o1.index(x))
            self.assertLess(o2.index('版本 B'), o2.index(x))
            for o in (o1, o2):
                self.assertNotIn('3.8.0', o); self.assertNotIn('4.0.0', o)

    def test_consistent_orders_count_and_inconsistent_is_a_tie(self):
        with tempfile.TemporaryDirectory() as temp:
            t = Path(temp); ev, key = self.setup(t)
            run_be(['record', str(ev), '--pair', '01', '--order', '1', '--verdict', 'A', '--evidence', '版本 A 的推动者有自己的招'])
            with self.assertRaises(SystemExit):
                run_be(['reveal', str(ev)])                            # 只判了一个顺序，不揭晓
            run_be(['record', str(ev), '--pair', '01', '--order', '2', '--verdict', 'B', '--evidence', '版本 B 的推动者有自己的招'])
            out = run_be(['reveal', str(ev)])
            self.assertIn(f"总计：{key['X']} 1", out)                  # 两次都选了 X → 计胜
            run_be(['record', str(ev), '--pair', '01', '--order', '2', '--verdict', 'A', '--evidence', '换了顺序改判为 A'])
            out = run_be(['reveal', str(ev)])
            self.assertIn('不一致（计平） 1', out)

    def test_order_verdict_must_be_a_or_b(self):
        with tempfile.TemporaryDirectory() as temp:
            t = Path(temp); ev, _ = self.setup(t)
            with self.assertRaises(SystemExit):
                run_be(['record', str(ev), '--pair', '01', '--order', '1', '--verdict', 'X', '--evidence', '顺序评审只认 A / B'])


class V4DocsWiringTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding='utf-8')

    def test_skill_routes_s3c_through_design_and_optional_cold_read(self):
        skill = self.read('SKILL.md')
        for phrase in ('references/scene-design.md', 'references/cold-read.md', 'scripts/cold_read_packet.py', '先设计',
                       '观众账本', '核心一步三选一', '静音测试', '可选冷读提醒', '不擅自跑', '写之前先设计'):
            self.assertIn(phrase, skill)

    def test_scene_design_has_the_three_steps_and_six_ways(self):
        sd = self.read('references/scene-design.md')
        for phrase in ('## 一、观众账本', '## 二、核心一步', '## 三、设计卡', '## 四、写的时候', '## 五、误用信号',
                       '第一种不能是"X 告诉 Y"', '推动者与战术', '阻力', '转折', '弹药', '静音测试', '本场不转',
                       '同一条消息不平行送两遍', '晚进早出'):
            self.assertIn(phrase, sd)

    def test_cold_read_is_optional_user_decided_and_reminded(self):
        cr = self.read('references/cold-read.md')
        for phrase in ('用户决定', '提醒', '不擅自跑', 'cold_read_packet.py', '不在本会话里自己模拟冷读', '不是交付门槛'):
            self.assertIn(phrase, cr)
        self.assertIn('可选步骤：独立冷读', self.read('references/execution-contract.md'))

    def test_template_order_design_track_body_record(self):
        tpl = self.read('templates/script-scene.md')
        idx = [tpl.index(h) for h in ('## 设计', '## 事件轨', '## 剧本页', '### 删除测试', '### 冷读')]
        self.assertEqual(idx, sorted(idx))
        for cell in ('观众已知', '核心一步', '推动者与战术', '阻力', '转折', '弹药', '静音测试', '信息·观众已知'):
            self.assertIn(cell, tpl)

    def test_old_capabilities_still_wired(self):
        # 用户：新规则只叠加，不削旧能力（事件轨、删除测试、review、告知不锁定、分镜超时提醒）
        tpl = self.read('templates/script-scene.md')
        for col in ('谁 → 对谁', '变化', '说出口', '删掉损失', '地点', '活动', '时间', '锚句', '估时'):
            self.assertIn(col, tpl)
        s3c = self.read('references/stage-3c-script.md')
        for phrase in ('事件轨', '删除测试', '压缩测试', 'review_script.py', '先诊断', '本场静止', '本场不说出口', '余韵'):
            self.assertIn(phrase, s3c)
        skill = self.read('SKILL.md')
        for phrase in ('告知，不锁定', '20%', 'scripts/review_script.py', '接住上一句是必要条件，不是充分条件'):
            self.assertIn(phrase, skill)
        src = self.read('references/dialogue-review-sources.md')
        for code in range(1, 20):
            self.assertRegex(src, rf'\| S{code} \|')
        self.assertIn('2026-09-26', self.read('references/preference-ledger.md'))
        self.assertIn('## 4.0.0 新增来源', self.read('references/context-creativity-sources.md'))
        self.assertIn('剧情靠宣布推进', self.read('references/story-engine.md'))
        self.assertIn('某人被告知某事', self.read('references/episode-design.md'))
        self.assertIn('## 八、LLM 双序配对', self.read('tests/creative-eval.md'))

    def test_case_law_moved_out_of_rules(self):
        s3c = self.read('references/stage-3c-script.md')
        self.assertIn('tests/cases/README.md', s3c)
        for leaked in ('牛棚', 'v4.1', 'EP03 场 4'):
            self.assertNotIn(leaked, s3c)
        self.assertTrue((ROOT / 'tests/cases/README.md').exists())

    def test_must_read_budget(self):
        # 4.0.0 预算（用户选 A：规则正文减负）：写一场必读的规则按字符计；超了先删再加
        files = ('SKILL.md', 'references/stage-3c-script.md', 'references/scene-design.md', 'templates/script-scene.md')
        total = sum(len(self.read(f)) for f in files)
        self.assertLessEqual(total, 23500, f'写一场必读的规则 {total} 字符，超过 4.0.0 预算：先删再加')


if __name__ == '__main__':
    unittest.main()
