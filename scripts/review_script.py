#!/usr/bin/env python3
"""出稿后的剧本 review：对白连通、台词经济（接住之外带来了什么）、复述、事件轨（谁要什么、每一行变了什么）、设计卡（film-creative 4.0.0）。

用法:
  review_script.py 03_script/scene-03.md [scene-04.md ...] [--context scene-01.md scene-02.md] [--later scene-04.md] [--json] [--full]
                   [--wps 4] [--action-sec 1.5] [--production-total 88]
  --context：按 story-context 指认的前几场，只用来建立"前文已出现过的设定"、查"前文说过"，不 review 它们。
  --later：后几场，只用来查候选台词在后文有没有回扣（可能是铺垫），不 review 它们。
  --production-total：film-director 分镜实排的场总时长；比剧本估时多 20% 以上时提醒（不退回，是否回剧本层由用户定）。

读 `templates/script-scene.md` 格式的剧本页（`<!-- script-body:start/end -->` 之间；
台词块为 `**NAME**` 或独立一行的角色名，下一行台词；括号行是表演/声音提示），
只做可量化的部分：收件人链、来回（exchange）、句长分布、短句占比、连续无人接的句子、
主谓宾完整度、画外标注、每句换人（一句一镜代理量）、潜台词支点（省略句依赖的设定前文有没有建立）。
3.7.0 起另报"事件轨"（合并 3.5.0 赌注卡与 3.6.0 场面轨）：读正文前的"## 事件轨"——人物清单（持续赌注 / 此刻向谁要什么 /
怕 / 为什么是现在；主要说话人与每个变化主体都要在，含不说话的人）+ 每行一次变化的表（谁 → 对谁 / 变化：进 → 出（类别）/
说出口或不说的理由与代价 / 删掉损失 / 地点 / 活动 / 时间 / 锚句 / 估时）。逐字核对锚句与说出口的句子在正文里、顺序一致、
本人说、有人接；进出相同、同一人的"出"重演、换了地点或跳了时间却没有变化、变化主体不在人物里、≥30 s 只有 ≤1 次变化
（未登记"本场静止：理由"）判为问题。推进只数变化，不数地点。换地点 / 跳时间 / 无台词 / 只改变观众所知的行，
列出它的变化、删掉损失与同一人前几次的状态，交模型做删除测试；全场一个地点只列复核。镜头与机位不在这里判——那是 film-director 的事。
3.8.0 起另报"台词经济"：接住上一句只是必要条件。脚本判不了一句是不是废话（10 场盲评标注上表面规则精确率 0.32），
只列候选（重复 / 接话 / 递话问句 / 截断）与低信息段，附"前文哪里说过 / 后文哪里回扣"交删除测试与压缩测试；
判为问题的只有：缺剧本页"### 删除测试"记录、记录与正文不符。总判断不再报"有人接的台词占比""最长来回"，
不再输出"全场没有一个问句"——它们推着作者补接话。
4.0.0 起另报"复述"与"设计卡"。复述：本场台词与 --context 前几场（台词 + 英文画面文字）重合的三词短语（至少含一个实词）、
同一事实（星期、钟点、明天 / 今晚）在本场 ≥3 句台词里反复出现——前者 ≥2 句、后者一次即判问题，删除测试里写明"回扣 / 铺垫 / 锁定"
的"留"不计入但列复核。设计卡：读正文前的"## 设计"（观众已知 / 核心一步三种发生方式 / 推动者 / 阻力 / 转折 / 弹药 / 静音测试），
只在总判断里报齐不齐，不改变结论——写作步骤不靠脚本判；选中的一步是传话、转折没写成"预期 → 结果"列复核。
事件轨里"（信息·观众已知；后果：…）"写不出后果的行不计为变化。
对白、台词经济、复述、事件轨与设计卡分开给结论（checks.dialogue / checks.economy / checks.repeat / checks.events / checks.design），"对白连通通过"不代表人物有戏。语义判断不冒充已判定，
列为"需模型复核"的证据清单。阈值全部是 `[推论]`（按 THE ORDER EP02 场 1 v1/v3、EP03 场 4 v3/v4/v4.1 校准），
在 THRESHOLDS 里改。每条判断引用的一手来源见 references/dialogue-review-sources.md（S1–S19）。

不改稿，不替用户采用；零外部依赖。退出码：0 = 通过或只有信号，1 = 有问题，2 = 输入无法解析。
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_script import body  # noqa: E402

# ---- 阈值（全部 [推论]；见 dialogue-review-sources.md §三） -------------------
THRESHOLDS = {
    'min_lines': 4,            # 台词少于此数不做统计判断（安静戏）
    'longest_exchange_min': 3,  # 最长两人来回少于 3 轮（A→B→A）→ 没有一组来回
    'exchange_coverage_min': 0.5,  # 能看出在接上一句的台词占比低于此 → 各说各的
    'mean_words_min': 4.0,     # 平均词数（Switchboard ≈ 6.8 词/句，屏幕对白取 4）
    'short_unexcused_max': 0.45,  # 无理由的 ≤4 词短句占比（v1 = 0.5，v3 = 0.08）
    'fragment_unexcused_max': 0.4,  # 无理由的碎句/无主语句占比
    'third_party_jump_max': 0.4,  # 换到第三个人说且不接前句的比例（一句一镜代理量）
    'orphan_run_min': 3,       # 连续多少句互不接话算一段
    'short_words': 4,
    'elliptical_words': 5,     # ≤ 此词数或被截断 / 以回应词起句的句子视为省略句（支点检查用）
    'stake_min_lines': 3,      # 说了这么多句的人必须在事件轨"人物"里（主要说话人；不说话的变化主体另外也要在）
    # 事件轨估时（3.6.0 起；按 THE ORDER EP02 场 1、EP03 场 1–4 的剧本估时与分镜实排校准，见 dialogue-review-sources.md §三）
    'wps': 4.0,                # 英文台词语速（词/秒；THE ORDER 用户定 4，`--wps` 可改）
    'cjk_cps': 4.5,            # 中文台词语速（字/秒）
    'action_s': 1.5,           # 无台词段里每个动作句的时长（秒；`--action-sec` 可改）
    'insert_max_sents': 2,     # 两句台词之间 ≤ 此数的动作句视为反应插入，与台词同步，不另计时
    'picture_min_s': 30,       # 按文本估时 ≥ 此秒数的场（或有对话的场）要事件轨；≥ 此秒数才判"变化太少"
    'min_changes': 2,          # ≥30 s 的场至少几行有变化；少于此数须登记"本场静止：理由"（3.7.0）
    'gap_review_s': 40,        # 观众等一次变化等了 ≥ 此秒数 → 需模型复核（3.6.0 的"同一段画面 ≥40 s"改按变化算）
    'linger_review_s': 10,     # 余韵（没有变化的行）合计 ≥ 此秒数 → 需模型复核（EP03 场 4 v4.1 牛棚段估 12 s、成片 16 s）
    'silent_review_s': 8,      # 无台词的变化行覆盖 ≥ 此秒数 → 列删除测试（短的反应行不列）
    # 台词经济（3.8.0；候选规则只是复核线索，按 10 场 219 句盲评标注：精确率约 0.32、召回约 0.68，见 dialogue-review-sources.md §三）
    'run_min': 4,              # 低信息段：至少几句
    'run_new_max': 0.75,       # 低信息段：平均每句新实词不超过此数
    'estimate_under': 0.85,    # 作者自报总估时 < 按文本估时 × 此比例 → 需模型复核（文本估时误差约 ±15%）
    'production_over': 1.2,    # 分镜实排 > 剧本估时 × 此比例 → 提醒用户（场面轨是告知不是锁定；回不回剧本层由用户定）
    # 复述与设计卡（4.0.0；按 Offset EP01 s04–s06、THE ORDER EP04 场 1–3、reckless EP02 场 1–3 非盲校准，见 dialogue-review-sources.md §三）
    'restate_ngram': 3,        # 与前几场重合的短语长度（词，至少含一个实词）
    'restate_problem_min': 2,  # 本场 ≥ 此句数复述前几场 → 判问题；1 句列复核
    'fact_repeat_min': 3,      # 同一事实（星期 / 钟点 / 明天今晚）在本场 ≥ 此句数台词里出现 → 判问题
    'design_min_s': 20,        # 按文本估时 ≥ 此秒数或有对话的场，写正文前要有设计卡（只在总判断里报）
}

START_ACTION_RESET = re.compile(r'^场\s*\d+')
CUE_BOLD = re.compile(r'^\*\*([^*]+)\*\*\s*$')
CUE_PLAIN = re.compile(r'^([A-Z][A-Z .\'-]{0,30}|[一-鿿·]{1,8})\s*$')
PAREN = re.compile(r'^[（(].*[)）]$')
OFFSCREEN = re.compile(r'画外|\bO\.?S\.?(?![A-Za-z])|\bV\.?O\.?(?![A-Za-z])|\bO\.?C\.?(?![A-Za-z])|off[- ]?screen|off[- ]?camera', re.I)

SUBJECTS = {'i', 'you', 'he', 'she', 'it', 'we', 'they', 'that', 'this', 'there', 'who', 'what', 'somebody',
            'nobody', 'everybody', 'everyone', 'someone', 'anyone', 'people', 'my', 'your', 'his', 'her', 'their'}
AUX = {'am', 'is', 'are', 'was', 'were', 'be', 'been', 'do', 'does', 'did', 'have', 'has', 'had', 'can', 'could',
       'will', 'would', 'should', 'might', 'must', "'m", "'re", "'s", "'ll", "'ve", "'d", "n't"}
VERBS = {'go', 'going', 'get', 'got', 'come', 'take', 'bring', 'hold', 'count', 'watch', 'look', 'say', 'said',
         'know', 'think', 'want', 'need', 'put', 'give', 'let', 'see', 'work', 'working', 'drink', 'drop', 'drops',
         'sit', 'sitting', 'stay', 'step', 'swing', 'swung', 'iron', 'ironed', 'carry', 'carrying', 'excuse', 'wait',
         'stop', 'move', 'tell', 'ask', 'help', 'make', 'made', 'run', 'walk', 'call', 'leave', 'keep', 'try',
         'mean', 'like', 'love', 'hate', 'hear', 'feel', 'talk', 'turn', 'open', 'close', 'pick', 'throw', 'jump',
         'swim', 'grab', 'hand', 'pass', 'send', 'read', 'write', 'play', 'start', 'finish', 'bet', 'guess', 'sound'}
CONNECTIVES = {'so', 'because', 'then', 'but', 'and', 'yeah', 'yes', 'no', 'okay', 'ok', 'not', 'why', 'what',
               "that's", 'well', 'oh', 'sure', 'fine', 'right', 'nope', 'yep', 'wait', 'sorry', 'still', 'also'}
STOP = {'the', 'a', 'an', 'to', 'of', 'in', 'on', 'at', 'is', 'are', 'was', 'were', 'be', 'and', 'or', 'but', 'so',
        'not', 'you', 'your', 'i', 'me', 'my', 'we', 'he', 'she', 'it', 'they', 'this', 'that', 'here', 'there',
        'up', 'out', 'for', 'with', 'do', 'did', 'does', 'have', 'has', 'go', 'get', 'got', 'okay', 'oh', 'yeah',
        'what', 'who', 'how', 'why', 'all', 'just', 'now', 'like', 'come', 'man', 'hey', 'no', 'yes'}
HESITATION = re.compile(r"—|…|\.\.\.|\b(um+|uh+|er+|well|you know|i mean|okay|oh)\b|嗯|呃|那个|就是说|哎", re.I)
CJK = re.compile(r'[\u4e00-\u9fff]')
CJK_CONNECTIVES = ('那', '所以', '可是', '但', '不', '对', '嗯', '好', '为什么', '什么', '行', '是', '没', '别', '你', '谁', '哪')
CJK_STOP = set('的了是我你他她它们这那在有和就都也不吗呢吧啊哦嗯把被给对说去来')
GROUP_SPEAKERS = {'众人', '众', 'ALL', 'EVERYONE', 'CROWD', '群众', '来宾们'}


# ---- 解析 ------------------------------------------------------------------
def norm_name(raw):
    raw = raw.strip().strip('*').strip()
    return raw.title() if re.fullmatch(r"[A-Z .'-]+", raw) else raw


def parse(text):
    """返回 (lines, actions)。lines: dict(speaker, text, parens, offscreen, action_idx)；actions: 动作段列表。"""
    lines, actions = [], []
    src = body(text).splitlines()
    i, n = 0, len(src)
    buf = []

    def flush():
        if buf:
            actions.append(' '.join(buf))
            buf.clear()

    while i < n:
        s = src[i].strip()
        m = CUE_BOLD.match(s)
        is_cue = bool(m)
        if not m and CUE_PLAIN.match(s) and not START_ACTION_RESET.match(s):
            # 独立一行角色名，且下一非空行是缩进台词或括号
            j = i + 1
            while j < n and not src[j].strip():
                j += 1
            if j < n and (src[j].startswith('    ') or src[j].startswith('\t') or PAREN.match(src[j].strip())):
                m, is_cue = re.match(r'^(.+)$', s), True
        if is_cue:
            flush()
            speaker = norm_name(m.group(1))
            i += 1
            parens, words = [], []
            while i < n and src[i].strip():
                t = src[i].strip()
                if PAREN.match(t):
                    parens.append(t)
                else:
                    words.append(t)
                i += 1
            if words:
                lines.append({'speaker': speaker, 'text': ' '.join(words), 'parens': parens,
                              'offscreen': any(OFFSCREEN.search(p) for p in parens),
                              'action_idx': len(actions) - 1})
            continue
        if s:
            buf.append(s)
        else:
            flush()
        i += 1
    flush()
    return lines, actions


# ---- 单句特征 ----------------------------------------------------------------
def tokens(text):
    return re.findall(r"[A-Za-z]+(?:'[a-z]+)?|\d+", text.lower())


def words(text):
    return re.findall(r"[A-Za-z0-9]+(?:'[a-z]+)?", text)


def is_cjk(text):
    return bool(CJK.search(text)) and len(words(text)) == 0


def content_words(text):
    if is_cjk(text):
        chars = [c for c in text if CJK.match(c) and c not in CJK_STOP]
        return {a + b for a, b in zip(chars, chars[1:])}
    return {t for t in tokens(text) if len(t) >= 3 and t not in STOP}


LEADING_VOCATIVE = re.compile(r"^\s*[A-Z][a-z]+[,!—.]\s*")
SENT_SPLIT = re.compile(r'(?<=[.!?—])\s+')


def _clause_of_sentence(sent):
    toks = tokens(sent)
    if not toks:
        return None
    parts = []
    for t in toks:
        if "'" in t:
            a, b = t.split("'", 1)
            parts += [a, "'" + b]
        else:
            parts.append(t)
    verb_at = next((k for k, p in enumerate(parts) if p in AUX or p in VERBS or (p.endswith('ing') and len(p) > 4)), None)
    if verb_at is None:
        if len(parts) <= 2 and sent.rstrip()[-1:] in '!—':
            return 'vocative'
        return 'fragment'
    before, after = parts[:verb_at], parts[verb_at + 1:verb_at + 2]
    # 谓语前有代词主语，或有一个不是功能词的名词（Cup drops / makeup form is）；疑问倒装（Did you / Why would I）也算
    if any(p in SUBJECTS for p in before) or any(p not in STOP and p not in AUX and p not in VERBS and p.isalpha() for p in before):
        return 'full'
    if parts[verb_at] in AUX and after and after[0] in SUBJECTS:
        return 'full'
    return 'imperative'


def clause_type(text):
    """full = 任一句谓语前有主语；imperative = 动词起句、谓语前无主语；fragment = 无谓语；vocative = 只有名字/感叹。
    句首的称呼（Tess, / Cole. / Beckett!）先剥掉再判。"""
    kinds = []
    for sent in SENT_SPLIT.split(text.strip()):
        stripped = sent
        for _ in range(2):
            stripped = LEADING_VOCATIVE.sub('', stripped)
        k = _clause_of_sentence(stripped) or ('vocative' if sent.strip() else None)
        if k:
            kinds.append(k)
    for k in ('full', 'imperative', 'vocative', 'fragment'):
        if k in kinds:
            return k
    return 'fragment'


def vocative_target(text, names):
    """台词里点到的名字（Sloane, / Tess! / Cole. Come on）。"""
    for name in names:
        if re.search(r'(^|[^A-Za-z])' + re.escape(name) + r'(?=[\s,.!?—-]|$)', text):
            return name
    return None


def link_to_prev(line, prev):
    """这句是否明显接住上一句：回答问题 / 点名 / 词汇回声 / 连接词起句。返回原因或 None。"""
    if prev is None or prev['speaker'] == line['speaker']:
        return None
    if '?' in prev['text'] or '？' in prev['text']:
        return '回答上一句的问题'
    if prev['text'].rstrip().endswith('—') or line['text'].lstrip().startswith('—'):
        return '打断 / 接上被截断的话'
    if vocative_target(line['text'], [prev['speaker']]):
        return '点名上一位说话人'
    echo = content_words(line['text']) & content_words(prev['text'])
    echo |= {a for a in content_words(line['text']) for b in content_words(prev['text'])
             if a != b and (a.startswith(b[:4]) or b.startswith(a[:4])) and len(a) >= 4 and len(b) >= 4}
    if echo:
        return '接住上一句的词（' + ', '.join(sorted(echo)[:2]) + '）'
    first = tokens(line['text'])[:1]
    if first and first[0] in CONNECTIVES:
        return '以回应词起句（' + first[0] + '）'
    if is_cjk(line['text']) and line['text'].lstrip('“"「').startswith(CJK_CONNECTIVES):
        return '以回应词起句'
    if line['text'].rstrip()[-1:] in '?？' and prev['text'].rstrip()[-1:] in '.!—。！':
        return '追问上一句'
    return None


# ---- 结构量 ------------------------------------------------------------------
def exchanges(lines):
    """两人来回：连续台词只在两个人之间交替，按"轮"计（同一人连说算一轮），至少 A→B→A 三轮才算来回。
    返回每段 (start_line, end_line, turns, {a, b})。多人对话（A 问 B 答 C 补）不在这里计，靠 link 指标兜底。"""
    turns = []  # (speaker, first_line, last_line)
    for k, ln in enumerate(lines):
        if turns and turns[-1][0] == ln['speaker']:
            turns[-1] = (ln['speaker'], turns[-1][1], k)
        else:
            turns.append((ln['speaker'], k, k))
    runs, i, n = [], 0, len(turns)
    while i < n:
        pair, j = {turns[i][0]}, i
        while j + 1 < n and (turns[j + 1][0] in pair or len(pair) < 2):
            pair.add(turns[j + 1][0])
            j += 1
        if len(pair) == 2 and j - i + 1 >= 3:
            runs.append((turns[i][1], turns[j][2], j - i + 1, pair))
            i = j + 1
        else:
            i += 1
    return runs


def analyse(lines, actions, names):
    T = THRESHOLDS
    n = len(lines)
    for k, ln in enumerate(lines):
        prev = lines[k - 1] if k else None
        nxt = lines[k + 1] if k + 1 < n else None
        ln['cjk'] = is_cjk(ln['text'])
        ln['words'] = len(words(ln['text']))
        ln['clause'] = 'n/a' if ln['cjk'] else clause_type(ln['text'])
        ln['vocative'] = vocative_target(ln['text'], [nm for nm in names if nm != ln['speaker']])
        ln['link_prev'] = link_to_prev(ln, prev)
        ln['question'] = ln['text'].rstrip()[-1:] in '?？'
        ln['answered'] = bool(ln['question'] and nxt and nxt['speaker'] != ln['speaker'])
        ln['is_group'] = ln['speaker'] in GROUP_SPEAKERS
        ln['third_party'] = bool(k >= 2 and ln['speaker'] not in (lines[k - 1]['speaker'], lines[k - 2]['speaker']))
        # 收件人：点名 > 接住上一句者 > 动作行"冲/对/朝 X" > 未知
        addr = ln['vocative']
        if not addr and ln['link_prev'] and prev:
            addr = prev['speaker']
        if not addr and ln['action_idx'] >= 0:
            m = re.search(r'[冲对朝向跟]\s*([A-Z][a-z]+|[一-鿿]{1,4})', actions[ln['action_idx']])
            if m and norm_name(m.group(1)) in names:
                addr = norm_name(m.group(1))
        if not addr:
            others = [nm for nm in names if nm != ln['speaker'] and nm not in GROUP_SPEAKERS]
            if len(others) == 1:
                addr = others[0]  # 两人戏：收件人只能是对方
        ln['addressee'] = addr
        # 有理由的短句：回答问题 / 喊人名 / 群体齐喊 / 感叹 / 明显接住上一句
        ln['short'] = (not ln['cjk']) and ln['words'] <= T['short_words']
        ln['short_excused'] = bool(ln['link_prev'] or ln['clause'] == 'vocative' or ln['is_group']
                                   or (ln['words'] <= 2 and ln['text'].rstrip().endswith('!')))
        ln['fragmentish'] = ln['clause'] in ('fragment', 'imperative')  # 中文行 n/a 不计
        ln['fragment_excused'] = ln['short_excused'] or bool(ln['vocative'])
    for k, ln in enumerate(lines):
        nxt = lines[k + 1] if k + 1 < n else None
        ln['linked_next'] = bool(nxt and nxt['link_prev'])
        ln['in_conversation'] = bool(ln['link_prev'] or ln['linked_next'])
        ln['orphan'] = not ln['in_conversation'] and not ln['is_group']
        ln['third_party_unlinked'] = ln['third_party'] and not ln['link_prev']
    runs = exchanges(lines)
    covered = sum(e - s + 1 for s, e, _, _ in runs)
    orphan_runs, k = [], 0
    while k < n:
        if lines[k]['orphan']:
            j = k
            while j + 1 < n and lines[j + 1]['orphan']:
                j += 1
            if j - k + 1 >= T['orphan_run_min']:
                orphan_runs.append((k, j))
            k = j + 1
        else:
            k += 1
    speakers = [ln['speaker'] for ln in lines]
    en = [ln for ln in lines if not ln['cjk']]
    m = len(en)
    stats = {
        'lines': n,
        'english_lines': m,
        'speakers': len(set(speakers)),
        'words_total': sum(ln['words'] for ln in en),
        'mean_words': round(sum(ln['words'] for ln in en) / m, 2) if m else None,
        'short_share': round(sum(ln['short'] for ln in en) / m, 2) if m else None,
        'short_unexcused_share': round(sum(ln['short'] and not ln['short_excused'] for ln in en) / m, 2) if m else None,
        'fragment_unexcused_share': round(sum(ln['fragmentish'] and not ln['fragment_excused'] for ln in en) / m, 2) if m else None,
        'longest_exchange': max((t for _, _, t, _ in runs), default=0),
        'exchange_coverage': round(covered / n, 2) if n else 0,
        'exchanges': [{'from': s, 'to': e, 'turns': t, 'between': sorted(p)} for s, e, t, p in runs],
        'linked_share': round(sum(bool(ln['link_prev']) for ln in lines) / n, 2) if n else 0,
        'conversation_share': round(sum(ln['in_conversation'] for ln in lines) / n, 2) if n else 0,
        'orphan_runs': orphan_runs,
        'questions': sum(ln['question'] for ln in lines),
        'questions_answered': sum(ln['answered'] for ln in lines),
        'hesitation_marks': sum(bool(HESITATION.search(ln['text'])) for ln in lines),
        'offscreen_lines': [k for k, ln in enumerate(lines) if ln['offscreen']],
        'third_party_jump_share': round(sum(ln['third_party_unlinked'] for ln in lines) / n, 2) if n else 0,
        'unknown_addressee': [k for k, ln in enumerate(lines) if not ln['addressee'] and not ln['is_group']],
    }
    return stats


# ---- 潜台词支点：省略句依赖的设定，前文有没有建立 ------------------------------
# 依据：说话人按共同基础与收件人设计说话（S10 Clark & Brennan 1991；S1 SSJ 1974 p.727），人物之间省略得掉的，
# 观众不在他们的共同基础里就读不出来；设定"凭空出现"会显得生硬，好的做法是让它由本场此刻的需要引出，或有人当场问一句（S11 Scriptnotes 693）。
# 可量化的代理量 [推论]：一句省略句里出现"当作已知"的指称（你的 X / 那个 X / 你有 X / 还 X），该指称在前文台词与英文动作行里没出现过，
# 且接下来没人问——记为"无支点"。中文动作行无法与英文指称自动对齐，只能引用出来交模型复核。
DETERMINERS = {'the', 'that', 'those', 'my', 'your', 'his', 'her', 'their', 'our'}  # this / these 指画面里的东西，本句即支点，不算当作已知
ITERATIVES = re.compile(r"\b(still|again|anymore|all over|by the way|as usual|the other|last time|like before)\b", re.I)
KNOWN_TO_YOU = re.compile(r"\byou(?:'ve| have|'ve got| still have| kept| left)\s+(?:got\s+)?(?:a|an|the|my|your|his|her|their)\s+((?:[a-z]+\s?){1,3})", re.I)
DEICTIC = re.compile(r"\b(right here|here|over there|this one|these)\b", re.I)
NP_STOP = {'one', 'thing', 'things', 'way', 'time', 'lot', 'bit', 'kind', 'sort', 'guy', 'guys', 'man', 'people',
           'everybody', 'everyone', 'somebody', 'nobody', 'same', 'whole', 'rest', 'point', 'rule', 'story', 'minute',
           'second', 'night', 'tonight', 'day', 'morning', 'today', 'week', 'place', 'here', 'there', 'now'}
ELLIPTICAL_OPENERS = {'so', 'then', 'and', 'but', 'or'}


def _stem(w):
    w = w.lower().rstrip("'")
    w = re.sub(r"'s$", '', w)
    for suf in ('ies', 'es', 's'):
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[:-len(suf)] if suf != 'ies' else w[:-3] + 'y'
    return w


def _np_heads(text):
    """当作已知的指称：限定词 / 物主 + 名词短语的中心词；"you have a X"；配 still/again 等重复词的名词。返回 [(head, phrase)]。"""
    found = []
    toks = re.findall(r"[A-Za-z]+(?:'[a-z]+)?", text)
    low = [t.lower() for t in toks]
    for i, t in enumerate(low):
        if t in DETERMINERS:
            phrase = []
            for j in range(i + 1, min(i + 4, len(low))):
                w = low[j]
                owner = w.endswith("'s")  # hoodie's = hoodie is：名词本身仍算，短语到此为止
                w = re.sub(r"'s$", '', w)
                if w in STOP or w in AUX or w in VERBS or w in DETERMINERS or "'" in w:
                    break
                phrase.append(w)
                if owner:
                    break
            if phrase and phrase[-1] not in NP_STOP and len(phrase[-1]) >= 3:
                found.append((_stem(phrase[-1]), ' '.join(phrase)))
    for m in KNOWN_TO_YOU.finditer(text):
        phrase = [w for w in m.group(1).lower().split() if w not in STOP and w not in AUX and w not in VERBS]
        if phrase and phrase[-1] not in NP_STOP and len(phrase[-1]) >= 3:
            found.append((_stem(phrase[-1]), ' '.join(phrase)))
    seen, out = set(), []
    for h, ph in found:
        if h not in seen:
            seen.add(h)
            out.append((h, ph))
    return out


def is_elliptical(ln):
    """省略句：很短、以回应词起句、或被截断的短句；一句 13 词的完整陈述即使末尾被打断也不算。"""
    t = ln['text'].strip()
    first = tokens(t)[:1]
    return bool(ln['words'] <= THRESHOLDS['elliptical_words']
                or t.startswith('—')
                or (t.endswith('—') and ln['words'] <= THRESHOLDS['elliptical_words'] + 3)
                or (first and first[0] in ELLIPTICAL_OPENERS))


def has_imperative_or_decision(ln):
    return ln['clause'] == 'imperative' or bool(re.match(r"^\s*(so|then)\b", ln['text'], re.I)) or \
        bool(re.search(r"\b(i'm gonna|i'll|let's|go|come|take|bring|keep|give)\b", ln['text'], re.I))


def anchoring(lines, actions, context_text='', ledger_text='', stake_terms=frozenset()):
    """逐句检查省略句里当作已知的指称是否在前文建立过。返回 candidates（无支点）、planted（本句明说的新设定）、declared（账本已声明不交代）。
    ledger_text = 剧本页正文之外的文字（修订账本 / 上下文承接 / 对白审阅）：指称出现在那里，视为作者已声明的决定，降为复核项。
    stake_terms = 赌注卡上声明的持续赌注与说出口句子里的词：人物说出自己的赌注是表态，不是待铺垫的旧梗，不报无支点（3.5.0）。"""
    established = {_stem(t) for t in tokens(context_text) if len(t) >= 3}
    declared_terms = {_stem(t) for t in tokens(ledger_text) if len(t) >= 3}
    declared = []
    cjk_actions_before = bool(CJK.search(' '.join(actions))) and not any(len(tokens(a)) >= 3 for a in actions)
    candidates, planted = [], []
    act_cursor = -1
    for k, ln in enumerate(lines):
        # 先把本句之前的动作行并入已建立词表（英文部分）
        while act_cursor < ln['action_idx']:
            act_cursor += 1
            established |= {_stem(t) for t in tokens(actions[act_cursor]) if len(t) >= 3}
        if ln['cjk']:
            ln['presupposed'] = []
            established |= {_stem(t) for t in tokens(ln['text']) if len(t) >= 3}
            continue
        heads = _np_heads(ln['text'])
        iterative = ITERATIVES.search(ln['text'])
        new_refs = [(h, ph) for h, ph in heads if h not in established and h not in {_stem(x) for x in tokens(ln['speaker'])}]
        ln['presupposed'] = [ph for _, ph in new_refs]
        if new_refs:
            ell = is_elliptical(ln)
            nxt = [x for x in lines[k + 1:k + 4] if x['speaker'] != ln['speaker'] and x['action_idx'] <= ln['action_idx'] + 1][:2]
            asked = any(x['question'] and any(h in {_stem(t) for t in tokens(x['text'])} for h, _ in new_refs) for x in nxt)
            asked_any = any(x['question'] for x in nxt)
            act = actions[ln['action_idx']] if ln['action_idx'] >= 0 else ''
            entry = {
                'line': k, 'quote': quote(ln), 'refs': [ph for _, ph in new_refs], 'iterative': bool(iterative),
                'elliptical': ell, 'asked_about': asked, 'asked_any': asked_any,
                'load_bearing': has_imperative_or_decision(ln),
                'preceding_action': act[:60], 'action_is_cjk': bool(CJK.search(act)) and not tokens(act),
                'next': quote(nxt[0]) if nxt else '（无人接）',
            }
            visible = bool(DEICTIC.search(ln['text']))  # "my phone's right here"：指着画面里的东西，本句即支点
            entry['stake'] = all(h in stake_terms for h, _ in new_refs)
            if ell and not asked and not visible and not entry['stake']:
                if all(h in declared_terms for h, _ in new_refs):
                    declared.append(entry)
                else:
                    candidates.append(entry)
            else:
                planted.append(entry)
        established |= {_stem(t) for t in tokens(ln['text']) if len(t) >= 3}
    candidates.sort(key=lambda e: (not e['load_bearing'], e['line']))
    return candidates, planted, declared


FIX_TEMPLATES = (
    ('直说来历', '{who} 把"{ref}"说成一句完整的话再接现在这句', '明说，默契感减一层', '后场不必再交代，新事实进 ip.md'),
    ('用当场动作引出', '让"{ref}"由本场此刻的需要带出——被用到、被交接、被当场撞见，而不是只被提到或指到', '多一个动作节拍', '物件或事件的初末态与前场要核'),
    ('让在场的人当场问', '在场另一人带着自己的立场问（怀疑、起哄、护短），不是替观众递一句"What {head}?"；答一句', '多一来一回，旁人知情，问的人也露出自己的态度', '知情范围扩大，"只限两人"的设定会变'),
)


def fixes_for(entry):
    """按 SKILL.md"批评已有稿、改法未定"契约：两到三种改法，各一两句（改什么 / 这场变成什么 / 影响后面什么），不改稿。"""
    ref = entry['refs'][0]
    head = ref.split()[-1]
    who = entry['quote'].split('「')[0]
    return [f"{name}：{what.format(who=who, ref=ref, head=head)}；这场变成 {becomes}；影响后面 {after}" for name, what, becomes, after in FIX_TEMPLATES]


# ---- 事件轨：谁要什么、每一行变了什么（3.7.0；合并 3.5.0 赌注卡与 3.6.0 场面轨） ----------------
# 依据：Mamet 每场三问 WHO WANTS WHAT? / WHAT HAPPENS IF THEY DON'T GET IT? / WHY NOW?（S6）；Mazin "Fear is our
# connection to a character"（S12）；说出口后有没有人接按相邻对（S1, S2）；地点与时长的问题（August 第 4、6 步，S13）。
# 3.6 的"画面推进"数"地点 × 活动"组合：加一个没有事件的新地点就能通过（THE ORDER EP03 场 4 v4.1"几分钟后，牛棚边"，
# 用户 2026-09-23 看成片问"这 16 s 存在的意义是？"）；无台词的人又不在赌注卡上。3.7.0 起两张卡合为一张事件轨：
# 每行是一次变化（谁：进 → 出），地点、活动、时间只是这次变化的属性；推进只数变化，不数地点；
# 变化的主体——包括不说话的人——都要在"人物"里写持续赌注与此刻要什么。
# 脚本不判一句话、一个画面"有没有意义"（那会变成关键词表）：它只逐字核对作者写正文前填的轨与正文、比较同一人的
# 前后状态、找出换地点却没有变化的行；变化是不是新的、删掉观众损失什么，列为需模型复核（删除测试，取向 5）。
EVENTS_HEAD = re.compile(r'^##\s*事件轨[^\n]*$', re.M)
LEGACY_HEAD = re.compile(r'^##\s*(本场赌注|场面轨)[^\n]*$', re.M)
QUOTED = re.compile(r'[“"「]([^”"」]+)[”"」]')
EVENT_COLS = (('seg', '#'), ('who', '谁'), ('change', '变化'), ('voiced', '说出口'), ('loss', '删掉'),
              ('loc', '地点'), ('act', '活动'), ('time', '时间'), ('anchor', '锚句'), ('est', '估时'))
CATEGORIES = ('没得到', '得到', '推迟', '失去', '信息', '关系', '决定', '物件', '地位')
LINGER = re.compile(r'^\s*(无|余韵)')
AUDIENCE = {'观众'}
EMPTY_CELL = {'', '—', '-', '无', '没有', '空', '未写', '__'}
CONTINUOUS = {'连续', '接上', '同上', '同前', '紧接'}
ACTION_SENT = re.compile(r'[。！？；!?]|(?<=[a-z])\.\s')
PARENS = re.compile(r'[（(][^)）]*[)）]')
TAIL_PAREN = re.compile(r'[（(]([^()（）]*)[)）]\s*$')
ARROW = re.compile(r'\s*(?:→|->)\s*')


def _cells(row):
    return [c.strip() for c in row.strip().strip('|').split('|')]


def _norm_quote(t):
    t = t.replace('’', "'").replace('‘', "'").replace('…', '...').lower()
    return re.sub(r'\s+', ' ', re.sub(r'[.!?,;:—\-]+$', '', t.strip()))


def _field(cell, key):
    """cell 里"理由：…""代价：…"一类字段的内容；没有该字段或内容为空 / 无 → None。"""
    m = re.search(key + r'\s*[:：]?\s*([^；;|]*)', cell)
    if not m:
        return None
    val = m.group(1).strip(' ，,。')
    return None if val in EMPTY_CELL else val


def _plain(t):
    return re.sub(r'\s+', '', re.sub(r'[“”"「」*]', '', t))


def _combo_key(cell):
    return re.sub(r'\s+', '', PARENS.sub('', cell)).lower()


def _split_top(cell, sep='；'):
    """按分隔符切，括号里的不切。"""
    out, depth, cur = [], 0, ''
    for ch in cell:
        depth += ch in '（(' and 1 or 0
        depth -= ch in '）)' and 1 or 0
        if ch in sep and depth <= 0:
            out.append(cur)
            cur = ''
        else:
            cur += ch
    out.append(cur)
    return [c.strip() for c in out if c.strip()]


def parse_change(cell):
    """变化格：'Isa：没路 → 拿到路（信息）；Beckett：… → …（推迟；代价：…）' 或 '无（余韵：理由）'。
    返回 {'linger': bool, 'reason', 'items': [{'who', 'from', 'to', 'cat', 'cost'}], 'bad': [原文]}。"""
    cell = cell.strip()
    if LINGER.match(cell):
        m = re.search(r'余韵\s*[:：]?\s*([^)）]*)', cell)
        return {'linger': True, 'reason': (m.group(1).strip() if m else '') or None, 'items': [], 'bad': []}
    items, bad = [], []
    for part in _split_top(cell):
        m = re.match(r'^([^：:→]+)[：:]\s*(.*)$', part)
        if not m or not ARROW.search(m.group(2)):
            bad.append(part)
            continue
        who = norm_name(m.group(1).strip().strip('*'))
        frm, to = ARROW.split(m.group(2), maxsplit=1)
        tail = TAIL_PAREN.search(to)
        meta = tail.group(1) if tail else ''
        state = to[:tail.start()].strip() if tail else to.strip()
        cat = next((c for c in CATEGORIES if meta.strip().startswith(c)), None)
        items.append({'who': who, 'from': frm.strip(), 'to': state, 'cat': cat, 'cost': _field(meta, '代价'),
                      'known': '观众已知' in meta, 'after': _field(meta, '后果')})
    return {'linger': False, 'reason': None, 'items': items, 'bad': bad}


def _cast_line(line):
    """'- **Isa**｜持续赌注：…（出处）｜此刻向 Beckett 要：…｜怕：…｜为什么是现在：…'"""
    parts = [p.strip() for p in re.split(r'[｜|]', line.lstrip('-* ').strip())]
    if len(parts) < 2:
        return None
    row = {'name': norm_name(parts[0].strip('*').strip()), 'standing': '', 'want': '', 'fear': '', 'why_now': ''}
    for p in parts[1:]:
        for key, word in (('standing', '持续赌注'), ('want', '此刻向'), ('fear', '怕'), ('why_now', '为什么是现在')):
            if p.startswith(word) and not row[key]:
                row[key] = re.sub(r'^[^：:]*[：:]\s*', '', p, count=1) if key != 'want' else p
    return row


def events_card(text):
    """剧本页正文前的"## 事件轨"：人物清单 + 变化表。返回 None（无轨）或
    {'cast': {name: row}, 'rows': [...], 'withheld_ok', 'still', 'total'}。"""
    m = EVENTS_HEAD.search(text)
    if not m:
        return None
    sec = re.split(r'\n## ', text[m.end():], maxsplit=1)[0]
    cast = {}
    for ln in sec.splitlines():
        if re.match(r'^\s*[-*]\s', ln):
            row = _cast_line(ln)
            if row and row['name'] not in EMPTY_CELL:
                cast[row['name']] = row
    table = [r for r in sec.splitlines() if r.strip().startswith('|')]
    rows = []
    if table:
        header = _cells(table[0])
        idx = {k: next((i for i, h in enumerate(header) if w in h), None) for k, w in EVENT_COLS}
        for r in table[1:]:
            cells = _cells(r)
            if all(set(c) <= set('-: ') for c in cells):
                continue
            get = lambda k: cells[idx[k]] if idx[k] is not None and idx[k] < len(cells) else ''
            row = {k: get(k) for k, _ in EVENT_COLS}
            if not any(row[k].strip() for k in ('who', 'change', 'anchor')):
                continue
            actor = re.split(r'→|->', row['who'])[0].strip().strip('*')
            row['actor'] = norm_name(actor) if actor and actor not in EMPTY_CELL else None
            tgt = re.split(r'→|->', row['who'])[1].strip() if re.search(r'→|->', row['who']) else ''
            row['targets'] = [norm_name(t.strip()) for t in re.split(r'[、,，/]', tgt) if t.strip() and t.strip() not in EMPTY_CELL]
            row['parsed'] = parse_change(row['change'])
            rows.append(row)
    reg = lambda word: (lambda mm: mm.group(1).strip() if mm and mm.group(1).strip().strip('_ ') not in EMPTY_CELL else None)(
        re.search(word + r'\s*[:：]\s*(\S[^\n]*)', sec))
    tot = re.search(r'总估时\s*[≈约]?\s*(\d+(?:\.\d+)?)\s*s', sec)
    total = float(tot.group(1)) if tot else None
    if total is None:
        nums = [re.search(r'\d+(?:\.\d+)?', r['est']) for r in rows]
        total = sum(float(n.group(0)) for n in nums if n) if rows and all(nums) else None
    return {'cast': cast, 'rows': rows, 'withheld_ok': reg('本场不说出口'),
            'still': reg('本场静止') or reg('本场单一画面'), 'total': total}


def declared_total(text, card):
    """作者自报的总估时：事件轨"总估时"或各行估时之和；旧稿回退到节拍表"总窗口 ≈ N s"。"""
    if card and card['total'] is not None:
        return card['total']
    m = re.search(r'总窗口\s*[≈约]?\s*(\d+(?:\.\d+)?)\s*s', text)
    return float(m.group(1)) if m else None


def _sents(action):
    return len([s for s in ACTION_SENT.split(action) if s.strip()])


def timeline(lines, actions):
    """按文本估时：台词按语速；无台词段（开场、收尾、台词之间 ≥3 句动作）每句 action_s 秒；
    台词之间 ≤2 句的反应插入与台词同步不另计（`[推论]`，校准见 dialogue-review-sources.md §三）。
    返回逐动作段 / 逐句的秒数：{'action': [s…], 'line': [s…], 'total': s}。"""
    T = THRESHOLDS
    line_s = []
    for ln in lines:
        if is_cjk(ln['text']):
            line_s.append(len(CJK.findall(ln['text'])) / T['cjk_cps'])
        else:
            line_s.append(len(words(ln['text'])) / T['wps'])
    act_s = [0.0] * len(actions)
    runs, prev = [], -1
    for ln in lines:
        runs.append(list(range(prev + 1, ln['action_idx'] + 1)))
        prev = max(prev, ln['action_idx'])
    runs.append(list(range(prev + 1, len(actions))))  # 收尾
    for k, ix in enumerate(runs):
        ix = [i for i in ix if not START_ACTION_RESET.match(actions[i])]
        n = sum(_sents(actions[i]) for i in ix)
        is_insert = k not in (0, len(runs) - 1) and n <= T['insert_max_sents']
        for i in ix:
            act_s[i] = 0.0 if is_insert else _sents(actions[i]) * T['action_s']
    return {'action': act_s, 'line': line_s, 'total': round(sum(act_s) + sum(line_s), 1)}


def _units(lines, actions):
    """正文按出现顺序排成单元：('a', i) 动作段、('l', k) 台词。"""
    order = []
    for i in range(-1, len(actions)):
        if i >= 0:
            order.append(('a', i))
        order.extend(('l', k) for k, ln in enumerate(lines) if ln['action_idx'] == i)
    return order


def _short(t, n=28):
    t = t.strip()
    return t if len(t) <= n else t[:n] + '…'


def check_events(text, card, lines, actions, names, production_total=None):
    """事件轨与正文核对。status：n/a（短场且台词少）、missing、issues、excepted（登记了不说出口 / 静止）、pass。"""
    T = THRESHOLDS
    tl = timeline(lines, actions)
    speakers = [nm for nm in names if nm not in GROUP_SPEAKERS]
    counts = {nm: sum(ln['speaker'] == nm for ln in lines) for nm in speakers}
    heading = next((a for a in actions if START_ACTION_RESET.match(a)), '')
    res = {'status': 'n/a', 'problems': [], 'review': [], 'voiced': [], 'terms': set(), 'rows': [],
           'estimate': tl['total'], 'declared': declared_total(text, card), 'changes': 0, 'places': [],
           'jumps': 0, 'linger_s': 0.0, 'longest_gap': 0.0, 'ends': {}}
    dialogue_scene = len(lines) >= T['min_lines'] and len(speakers) >= 2
    if res['declared'] and res['declared'] < tl['total'] * T['estimate_under']:
        res['review'].append(f"自报总估时 {res['declared']:g} s，按文本估 ≈ {tl['total']:g} s：无台词动作（越过、冲刺、过线、看一眼）"
                             f"有没有算进去（文本估时误差约 ±15%，[推论]）")
    if production_total and res['declared'] and production_total > res['declared'] * T['production_over']:
        res['production_over'] = round((production_total / res['declared'] - 1) * 100)
        res['review'].insert(0, f"分镜实排 {production_total:g} s，比剧本估时 {res['declared']:g} s 多 "
                                f"{res['production_over']}%（≥{round((T['production_over'] - 1) * 100)}%）："
                                f"提醒——多出来的时间观众在看哪一行变化，还是同一个画面拉长了；要不要回剧本层由用户定")
    if card is None:
        if dialogue_scene or tl['total'] >= T['picture_min_s']:
            res['status'] = 'missing'
            res['place'] = heading.split('·')[1].strip() if heading.count('·') >= 2 else '（标题未写地点）'
            main = [f'{nm} {c} 句' for nm, c in sorted(counts.items(), key=lambda x: -x[1]) if c >= T['stake_min_lines']]
            legacy = LEGACY_HEAD.findall(text)
            res['problems'].append(
                '没有"## 事件轨"' + (f'（有旧格式"{"""、""".join(dict.fromkeys(legacy))}"：3.7.0 起合为事件轨，每行一次变化）' if legacy else '')
                + (f'，主要说话人 {"、".join(main)}' if main else '')
                + f'，只有场景标题的地点「{res["place"]}」，按文本估 ≈ {tl["total"]:g} s：看不出谁要什么、每一行变了什么')
        return res

    cast = card['cast']
    rows = card['rows']
    if not rows:
        res['problems'].append('"## 事件轨"是空表')
    # 人物：主要说话人与每个变化主体（含不说话的人）都要在清单里（3.5.0 的"≥3 句上卡"扩到无台词的变化主体）
    for nm, c in counts.items():
        if c >= T['stake_min_lines'] and nm not in cast:
            res['problems'].append(f'{nm} 说了 {c} 句，"人物"里没有他此刻要什么')
    for nm, row in cast.items():
        res['terms'] |= {_stem(t) for t in tokens(row['standing']) if len(t) >= 3}
        if not row['want'] or re.sub(r'^此刻向\S*\s*要\s*[:：]?', '', row['want']).strip() in EMPTY_CELL:
            res['problems'].append(f'"人物"里 {nm} 没写此刻向谁要什么')
        if not re.search(r'[（(][^)）]+[)）]', row['standing']):
            res['review'].append(f'{nm} 的持续赌注没写出处（ip.md / 故事 / 框架哪一行）')
    # 锚句：逐字在正文（动作行或台词）里、按顺序
    units = _units(lines, actions)
    utext = [actions[i] if kind == 'a' else lines[i]['text'] for kind, i in units]
    usec = [tl['action'][i] if kind == 'a' else tl['line'][i] for kind, i in units]
    pos, last = [], 0
    for k, row in enumerate(rows, 1):
        a = _plain(row['anchor'])
        if not a or a in EMPTY_CELL:
            res['problems'].append(f'第 {k} 行没写锚句（这次变化在正文里看得见的那一句，逐字）')
            pos.append(None)
            continue
        hit = next((u for u in range(last, len(units)) if a in _plain(utext[u])), None)
        if hit is None:
            before = next((u for u in range(0, last) if a in _plain(utext[u])), None)
            res['problems'].append(f'第 {k} 行锚句「{_short(row["anchor"], 24)}」' +
                                   ('在正文里出现在上一行之前（事件轨顺序与正文不符）' if before is not None else '不在正文里'))
        pos.append(hit)
        if hit is not None:
            last = hit
    # 逐行覆盖的正文与秒数：上一行锚句之后到本行锚句；第一行从开场起，最后一行含收尾
    ok_pos = rows and all(p is not None for p in pos)
    for k, row in enumerate(rows):
        s = (pos[k - 1] + 1) if ok_pos and k else 0
        e = (pos[k] + 1) if ok_pos else 0
        if ok_pos and k == len(rows) - 1:
            e = len(units)
        cover = list(range(s, e))
        row['secs'] = round(sum(usec[u] for u in cover), 1)
        row['silent'] = ok_pos and not any(units[u][0] == 'l' for u in cover)
        row['lines'] = [units[u][1] for u in cover if units[u][0] == 'l']
    # 地点与时间：只是属性；记录换地点 / 跳时间，供"换了地点却没有变化"与删除测试复核
    prev_loc = None
    for k, row in enumerate(rows):
        raw_loc = row['loc'].strip()
        same = raw_loc in EMPTY_CELL or any(raw_loc.startswith(c) for c in CONTINUOUS)  # "同上，沿通道往出口" 是同一处
        loc = prev_loc if same else _combo_key(raw_loc)
        t = _combo_key(row['time'])
        row['jump'] = bool(k and t and row['time'].strip() not in EMPTY_CELL and not any(t.startswith(c) for c in CONTINUOUS))
        row['moved'] = bool(k and loc and prev_loc and loc != prev_loc)
        if loc and not same and loc not in [_combo_key(p) for p in res['places']]:
            res['places'].append(PARENS.sub('', row['loc']).strip())
        res['jumps'] += row['jump']
        prev_loc = loc or prev_loc
    # 每一行的变化
    last_state, history = {}, {}
    for k, row in enumerate(rows, 1):
        ch = row['parsed']
        where = '、'.join(x for x in (f'换了地点（{PARENS.sub("", row["loc"]).strip()}）' if row['moved'] else '',
                                     f'跳了时间（{row["time"].strip()}）' if row['jump'] else '') if x)
        if not row['loss'].strip() or row['loss'].strip() in EMPTY_CELL:
            res['problems'].append(f'第 {k} 行没写删掉损失（删掉这一行，观众少知道 / 少感到什么）')
        if ch['linger']:
            res['linger_s'] += row.get('secs', 0)
            if where:
                res['problems'].append(f'第 {k} 行{where}，却标为余韵、没有变化：把观众带到新地方，那里没有事发生'
                                       f'（删掉损失：{_short(row["loss"], 30) or "空"}）')
            continue
        if ch['bad'] or not ch['items']:
            res['problems'].append(f'第 {k} 行的变化没写成"谁：进 → 出（类别）"'
                                   + (f'：「{_short(ch["bad"][0], 30)}」' if ch['bad'] else '') + '；没有变化就标"无（余韵：理由）"')
            continue
        real = False
        for it in ch['items']:
            who = it['who']
            if who not in AUDIENCE and who not in cast:
                res['problems'].append(f'第 {k} 行的变化主体 {who} 不在"人物"里'
                                       f'{"（不说话的人也要写持续赌注与此刻要什么）" if not counts.get(who) else ""}')
            if _plain(it['from']) == _plain(it['to']):
                res['problems'].append(f'第 {k} 行 {who}「{_short(it["to"], 24)}」进出相同：这一行没有变化')
                continue
            if who in last_state and _plain(it['to']) in [_plain(x['to']) for x in history.get(who, [])]:
                j = next(x['row'] for x in history[who] if _plain(x['to']) == _plain(it['to']))
                res['problems'].append(f'第 {k} 行 {who} 的"出"「{_short(it["to"], 24)}」与第 {j} 行相同：同一状态再演一遍')
                continue
            if it['cat'] == '信息' and it.get('known') and who not in AUDIENCE and not it.get('after'):
                res['review'].append(f'第 {k} 行 {who}「{_short(it["to"], 24)}」是观众已知的事，没写后果：不计为变化——'
                                     f'晚进（从他知道之后开始）、写出他因此做的新事，或删（scene-design §一）')
                continue
            if not it['cat']:
                res['review'].append(f'第 {k} 行 {who} 的变化没标类别（{"/".join(CATEGORIES)}）')
            if it['cat'] in ('推迟', '没得到') and not it['cost']:
                res['review'].append(f'第 {k} 行 {who}「{it["cat"]}」没写代价：欲望是不是被一句"That\'s fair / Okay"接住收掉了')
            real = True
            prev = history.get(who, [])[-1] if history.get(who) else None
            it['prev'] = prev
            history.setdefault(who, []).append({'row': k, 'to': it['to'], 'cat': it['cat']})
            last_state[who] = it['to']
            if who not in AUDIENCE:
                res['ends'][who] = f'{it["to"]}（{it["cat"] or "?"}，第 {k} 行）'
        row['real'] = real
        res['changes'] += real
        # 删除测试（交模型）：换了地点 / 跳了时间、整行没有台词、或只改变观众所知的行
        silent_long = row.get('silent') and row.get('secs', 0) >= T['silent_review_s']
        if real and (where or silent_long or all(it['who'] in AUDIENCE for it in ch['items'])):
            ctx = []
            for it in ch['items']:
                p = it.get('prev')
                if p:
                    same = '，同为「' + p['cat'] + '」' if p['cat'] and p['cat'] == it['cat'] else ''
                    ctx.append(f'{it["who"]} 上一次在第 {p["row"]} 行「{_short(p["to"], 20)}」{same}')
            for tg in row['targets']:
                asked = [(j, r) for j, r in enumerate(rows[:k - 1], 1) if tg in r['targets'] and r['actor'] != row['actor']]
                if asked:
                    j, r = asked[-1]
                    ctx.append(f'{tg} 作为对象的上一行是第 {j} 行 {r["actor"] or "?"}（{_short(r["change"], 24)}）')
            tags = '、'.join(x for x in (where, '无台词' if silent_long else '') if x)
            res['review'].append(f'第 {k} 行（{tags or "只改变观众所知"}，≈ {row.get("secs", 0):g} s）：变化「{_short(row["change"], 36)}」，'
                                 f'删掉损失「{_short(row["loss"], 30)}」' + ('；' + '；'.join(ctx) if ctx else '')
                                 + '——删除测试：删掉这一行，观众少知道 / 少感到的，前面哪一行没给过')
    # 说出口：逐字、本人说、有人接（3.5.0 的赌注核对，挪到事件轨的行上）
    voiced_by, withheld = set(), {}
    for k, row in enumerate(rows, 1):
        who = row['actor']
        withholding = bool(re.match(r'^\s*不说', row['voiced']))
        quotes = [] if withholding else QUOTED.findall(row['voiced'])
        if quotes:
            for q in quotes:
                nq = _norm_quote(q)
                hit = [i for i, ln in enumerate(lines) if nq and nq in _norm_quote(ln['text'])]
                own = [i for i in hit if lines[i]['speaker'] == who]
                if not hit:
                    res['problems'].append(f'第 {k} 行 {who} 说出口的"{_short(q, 30)}"不在正文里')
                    continue
                if not own:
                    res['problems'].append(f'第 {k} 行记为 {who} 说出口的"{_short(q, 30)}"，正文里是 {lines[hit[0]]["speaker"]} 说的')
                    continue
                i = own[0]
                voiced_by.add(who)
                res['voiced'].append({'who': who, 'line': i, 'row': k, 'quote': quote(lines[i])})
                res['terms'] |= {_stem(t) for t in tokens(q) if len(t) >= 3}
                nxt = lines[i + 1] if i + 1 < len(lines) else None
                if nxt and nxt['speaker'] != who and nxt['link_prev']:
                    res['voiced'][-1]['reply'] = quote(nxt)
                else:
                    res['review'].append(f'{quote(lines[i])} 说出口后对方没有用台词接：对方用什么接的（动作、沉默、转开），'
                                         f'正文里看得见吗——不需要为它补一句接话')
                want = cast.get(who, {}).get('want', '')
                res['review'].append(f'{who} 此刻要的是"{_short(want, 30)}"，说出口的是 {quote(lines[i])}：'
                                     f'这句说的是不是这件事（按取向 6：面对谁、刚发生什么、为什么此刻）')
        elif withholding and who:
            withheld.setdefault(who, []).append((_field(row['voiced'], '理由'), _field(row['voiced'], '代价')))
    for nm in cast:
        if nm in voiced_by:
            continue
        ok = [(r, c) for r, c in withheld.get(nm, []) if r and c]
        if ok:
            res['review'].append(f'{nm} 不说：{ok[0][0]}；代价 {ok[0][1]}——观众能从处境读出他在绕什么吗')
        else:
            res['problems'].append(f'{nm} 在"人物"里，但哪一行都没说出口，也没写不说的理由与代价'
                                   f'（持续赌注：{_short(cast[nm]["standing"], 30) or "空"}）')
    if dialogue_scene and not voiced_by:
        if card['withheld_ok']:
            res['review'].insert(0, f'全场无人把赌注说出口，已登记例外：{card["withheld_ok"]}')
        else:
            res['problems'].append('全场没有一个人把自己要的说出口，也没有登记"本场不说出口：理由"')
    # 推进：只数变化，不数地点（3.7.0）
    gaps = [r.get('secs', 0) for r in rows if r.get('real')]
    res['longest_gap'] = max(gaps) if gaps else 0.0
    if rows and res['longest_gap'] >= T['gap_review_s']:
        k = next(i for i, r in enumerate(rows, 1) if r.get('real') and r.get('secs', 0) == res['longest_gap'])
        res['review'].append(f"第 {k} 行之前观众等了 ≈ {res['longest_gap']:g} s 才看到这次变化：是有意的压迫 / 等待 / 一镜到底，"
                             f"还是中间缺一次变化")
    if rows and res['linger_s'] >= T['linger_review_s']:
        res['review'].append(f"余韵合计 ≈ {res['linger_s']:g} s（没有变化的行）：是在让刚发生的结果停留，还是在拖；"
                             f"交给分镜时不要把它扩成独立的一条")
    still = rows and tl['total'] >= T['picture_min_s'] and res['changes'] < T['min_changes']
    if still:
        if card['still']:
            res['review'].insert(0, f"全场只有 {res['changes']} 次变化，已登记理由：{card['still']}——观众在这 "
                                    f"{tl['total']:g} s 里看见处境怎么变")
        else:
            res['problems'].append(f"按文本估 ≈ {tl['total']:g} s，只有 {res['changes']} 行有变化，也没有登记"
                                   f'"本场静止：理由"（余韵戏、有意一镜到底、对峙 / 等待的压迫感）')
    if rows and tl['total'] >= T['picture_min_s'] and len(res['places']) == 1 and not res['jumps'] \
            and len({_combo_key(r['act']) for r in rows if r['act'].strip() not in EMPTY_CELL}) <= 1:
        res['review'].append(f"全场一个地点、一种活动（{res['places'][0]} · {PARENS.sub('', rows[0]['act']).strip() or '?'}，"
                             f"≈ {tl['total']:g} s，{res['changes']} 次变化）：这些变化观众看得见，还是都在台词里——"
                             f"缺的是事件、人还是信息；只是画面单调、事件不缺时交分镜处理，不为换景加段")
    if res['problems']:
        res['status'] = 'issues'
    elif (dialogue_scene and not voiced_by and card['withheld_ok']) or (still and card['still']):
        res['status'] = 'excepted'
    else:
        res['status'] = 'pass'
    return res


# ---- 台词经济：接住之外，还要带来东西（3.8.0） -----------------------------------
# 依据：S5 Scriptnotes 609 的后半——"if the audience hears it once, don't make them hear it twice"、重复的台词
# "you have to eliminate those"、uh-huh / yeah 这类接话在剧本里"rare"、"you may not put every utterance … in the dialogue"；
# 它称赞的 "what's more" 是"接住 + 往上加"。S2–S4 是真实会话语料，真实会话满是接话，屏幕对白要压缩，不能拿它们当目标。
# 脚本判不了一句是不是废话：按 THE ORDER / reckless 10 场 219 句的盲评标注校准，下面的表面规则精确率约 0.32、召回约 0.68
# （讨价还价、回扣、调情、嘴硬都长得像接话或重复）。所以它只做两件事：列出候选并给出"真实剧情"里的证据
# （前文哪里说过、后文哪里回扣），以及核对作者写下的删除测试记录；删不删由删除测试 / 压缩测试决定。
ACK_OPENER = re.compile(r"^\W*(okay|ok|oh|yeah|yes|yep|right|sure|fine|alright|i know|i heard|that's|good|got it|hey)\b", re.I)
YES_NO = {'yes', 'no', 'yeah', 'nope', 'yep', 'sure', 'nah'}
DELETION_HEAD = re.compile(r'^#{2,3}\s*删除测试[^\n]*$', re.M)
DECISION = re.compile(r'^\s*(?:[-*]\s*)?(删|并|留|压缩)\s*[:：]\s*(.*)$')
ECO_GENERIC = {'know', 'look', 'said', 'back', 'right', 'just', 'like', 'want', 'think', 'thing', 'going', 'gonna', 'really',
               'well', 'come', 'would', 'could', 'should', 'there', 'where', 'here', 'what', 'then', 'than', 'about', 'with',
               'from', 'into', 'them', 'they', 'your', 'you', "i'm", "it's", "don't", "that's", 'didn', 'doesn', 'said',
               'tell', 'talk', 'talking', 'take', 'give', 'make', 'need', 'still', 'even', 'much', 'more', 'some', 'something',
               'anything', 'nothing', 'everything', 'yeah', 'okay', 'say', 'before', 'after', 'past', 'half', 'over'}
ECO_KINDS = {'重复': '本场或前文说过的内容再说一遍', '接话': '确认 / 附和 / 回应词', '递话问句': '答案下一句就给、问句本身不带立场',
             '截断': '被打断前只说了半句'}


def scene_lines(paths):
    """[(标签, lines)]：前后场只取台词，用来查"前文说过 / 后文回扣"。解析失败的文件跳过。"""
    out = []
    for p in paths or ():
        p = Path(p)
        try:
            lines, _ = parse(p.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue
        out.append((f'{p.parent.parent.name}/{p.stem}' if p.parent.name == '03_script' else p.stem, lines))
    return out


def economy(lines, names, context=(), later=()):
    """候选（重复 / 接话 / 递话问句 / 截断）与低信息段；每个候选附前文出处与后文回扣。"""
    T = THRESHOLDS
    nm = {x.lower() for x in names}
    freq = {}
    for _, L in list(context) + [('', lines)] + list(later):
        for ln in L:
            for w in content_words(ln['text']):
                freq[w] = freq.get(w, 0) + 1
    specific = lambda ws: sorted((w for w in ws if w not in ECO_GENERIC and w not in nm and freq.get(w, 0) <= 4),
                                 key=lambda w: (freq.get(w, 0), w))
    seen = {}  # 词 → 第一次出现在哪
    for label, L in context:
        for ln in L:
            for w in content_words(ln['text']):
                seen.setdefault(w, f'{label} {quote(ln)[:48]}')
    ahead = {}
    for label, L in later:
        for ln in L:
            for w in content_words(ln['text']):
                ahead.setdefault(w, f'{label} {quote(ln)[:48]}')
    cands, newc = [], []
    for k, ln in enumerate(lines):
        cw = content_words(ln['text'])
        new = cw - set(seen) - nm
        toks = words(ln['text'])
        w = len(toks) if not ln['cjk'] else len(CJK.findall(ln['text'])) // 2
        prev = lines[k - 1] if k else None
        nxt = lines[k + 1] if k + 1 < len(lines) else None
        answers_q = bool(prev and prev['speaker'] != ln['speaker'] and prev['text'].rstrip()[-1:] in '?？')
        vocative_only = 0 < len(toks) <= 2 and all(t.lower() in nm for t in toks)
        asks = ln['text'].rstrip()[-1:] in '?？'
        kind = None
        if ln['is_group'] or vocative_only:
            pass
        elif answers_q and toks and toks[0].lower() in YES_NO and w <= 4:
            pass  # 对问句的是 / 否：回答本身
        elif not new and cw and w >= 5:
            kind = '重复'
        elif len(new) <= 1 and ACK_OPENER.match(ln['text']):
            kind = '接话'
        elif not new and w <= 5:
            kind = '递话问句' if asks else '接话'
        elif asks and w <= 7 and len(new) <= 1 and nxt and nxt['speaker'] != ln['speaker'] \
                and content_words(nxt['text']) - set(seen) - cw:
            kind = '递话问句'
        elif ln['text'].rstrip().endswith(('—', '-')) and w <= 4:
            kind = '截断'
        if kind:
            rep_w = specific(cw & set(seen))[:2]
            pay_w = specific(cw & set(ahead))[:1]
            before = [f'"{x}" ← {seen[x]}' for x in rep_w]
            payoff = [f'"{x}" → {ahead[x]}' for x in pay_w]
            cands.append({'line': k, 'kind': kind, 'quote': quote(ln), 'said_before': before, 'later': payoff})
        newc.append(len(new))
        for x in cw:
            seen.setdefault(x, f'本场 {quote(ln)[:48]}')
    runs, k, n = [], 0, len(lines)
    while k < n:  # 低信息段：≥ run_min 句，平均每句新实词 ≤ run_new_max，首尾都是低信息句
        best = None
        for j in range(k + T['run_min'] - 1, n):
            seg = newc[k:j + 1]
            if sum(seg) <= len(seg) * T['run_new_max'] and newc[k] <= 1 and newc[j] <= 1:
                best = j
        if best is not None:
            runs.append({'from': k, 'to': best, 'lines': best - k + 1, 'new_words': sum(newc[k:best + 1])})
            k = best + 1
        else:
            k += 1
    return {'candidates': cands, 'runs': runs, 'new_words': newc}


def deletion_record(text):
    """剧本页"删除测试"一节：删 / 并 / 留 / 压缩，每条带逐字引号。没有这一节返回 None。"""
    m = DELETION_HEAD.search(text)
    if not m:
        return None
    sec = re.split(r'\n#{1,3} ', text[m.end():], maxsplit=1)[0]
    rec = {'删': [], '并': [], '留': [], '压缩': [], 'none': False}
    for line in sec.splitlines():
        d = DECISION.match(line)
        if not d:
            continue
        kind, rest = d.group(1), d.group(2)
        qs = QUOTED.findall(rest)
        if not qs and kind == '删' and rest.strip().strip('。') in ('无', '没有'):
            rec['none'] = True
            continue
        reason = re.split(r'[—–]{1,2}|\s-\s', QUOTED.sub('', rest), maxsplit=1)
        rec[kind].append({'quotes': qs, 'reason': (reason[-1] if len(reason) > 1 else '').strip(' ：:。')})
    return rec


def _still_there(q, texts):
    """删 / 并记录里的原句还在不在正文：与某句台词的整句（或连续几句）相同才算；四词以上的片段在词边界上出现也算。
    只按子串比，会把正文 "you and Rhett at the same table" 认成已删的 "And Rhett?"（4.0.0 验收时写作代理报的误报）。"""
    nq = _norm_quote(q)
    if not nq:
        return False
    for t in texts:
        sents = [s for s in re.split(r'(?<=[.!?…])\s+|\s+[—–]+\s+|\s*--\s*', t.strip()) if s.strip()]
        if any(_norm_quote(' '.join(sents[i:j + 1])) == nq for i in range(len(sents)) for j in range(i, len(sents))):
            return True
        if len(nq.split()) >= 4 and re.search(r"(?<![\w'])" + re.escape(nq) + r"(?![\w'])", _norm_quote(t)):
            return True
    return False


def check_economy(text, eco, lines):
    """核对删除测试记录与正文；候选与低信息段没被记录覆盖的列为复核。status：n/a / missing / issues / pass。"""
    T = THRESHOLDS
    res = {'status': 'n/a', 'problems': [], 'review': [], 'candidates': eco['candidates'], 'runs': eco['runs'], 'record': None}
    if len(lines) < T['min_lines']:
        return res
    rec = deletion_record(text)
    res['record'] = rec
    body_q = [_norm_quote(ln['text']) for ln in lines]
    in_body = lambda q: any(_norm_quote(q) and _norm_quote(q) in b for b in body_q)
    covered = set()
    if rec is None:
        res['status'] = 'missing'
        kinds = {}
        for c in eco['candidates']:
            kinds[c['kind']] = kinds.get(c['kind'], 0) + 1
        res['problems'].append('没有"删除测试"记录（剧本页"对白审阅"下：逐句删掉观众少什么、逐段最少几句）'
                               + (f"；脚本候选 {len(eco['candidates'])} 句（" + ' / '.join(f'{k} {v}' for k, v in kinds.items()) + '）'
                                  if eco['candidates'] else '')
                               + (f"，低信息段 {len(eco['runs'])} 段" if eco['runs'] else '')
                               + (f"，如 {eco['candidates'][0]['quote'][:40]}" if eco['candidates']
                                  else f"，如 {quote(lines[eco['runs'][0]['from']])[:40]}…" if eco['runs'] else ''))
    else:
        for kind in ('删', '并'):
            for item in rec[kind]:
                if item['quotes'] and _still_there(item['quotes'][0], [ln['text'] for ln in lines]):
                    res['problems'].append(f'删除测试记为"{kind}"的「{_short(item["quotes"][0], 30)}」还在正文里')
        for item in rec['留']:
            for q in item['quotes'][:1]:
                if not in_body(q):
                    res['problems'].append(f'删除测试记为"留"的「{_short(q, 30)}」不在正文里')
            if not item['reason']:
                res['problems'].append(f'「{_short((item["quotes"] or ["?"])[0], 30)}」记为"留"但没写它带来什么')
        quoted = [_norm_quote(q) for kind in ('留', '压缩') for it in rec[kind] for q in it['quotes']]
        gone = [q for kind in ('删', '并') for it in rec[kind] for q in it['quotes']]
        for i, b in enumerate(body_q):
            if any(q and q in b for q in quoted) or any(_still_there(q, [lines[i]['text']]) for q in gone):
                covered.add(i)
        res['status'] = 'issues' if res['problems'] else 'pass'
    for c in eco['candidates']:
        if c['line'] in covered:
            continue
        ev = ('；前文：' + ' / '.join(c['said_before'])) if c['said_before'] else ''
        ev += ('；后文回扣：' + c['later'][0]) if c['later'] else ''
        res['review'].append(f"{c['quote']}（{c['kind']}候选{ev}）：删掉它观众少知道 / 少感到什么；"
                             + ('后文有回扣时先确认它是不是铺垫' if c['later'] else '答不出就删，或并进下一句 / 一个动作'))
    for run in eco['runs']:
        if run['from'] in covered or run['to'] in covered:
            continue
        res['review'].append(f"{quote(lines[run['from']])[:40]}…{quote(lines[run['to']])[:40]}：{run['lines']} 句只多了 "
                             f"{run['new_words']} 个新实词——压缩测试：这段要改变的一件事是什么、最少几句能做到、"
                             f"每一回合有没有人的立场或压力在变（讨价还价、调情、回扣是在变，复述和确认不是）")
    return res


def ECONOMY_ISSUE(eco):
    missing = eco['status'] == 'missing'
    return {
        'key': 'economy', 'compact': missing,  # 缺记录只在总判断里报一句，不占 ≤3 个问题的位置
        'title': '缺删除测试' if missing else '删除测试记录与正文不符',
        'evidence': '；'.join(eco['problems']),
        'why': '接住上一句只是必要条件：观众已经听过、看过的不再说，简单的事一两句说完；每句多出来的秒数都要带来信息、要求、关系或笑点。',
        'sources': ['S5'],
        'basis': '"听过一次不再听第二次""重复的台词要删""接话在剧本里很少"有来源（S5）；候选规则与低信息段阈值是[推论]，只作复核线索',
    }


# ---- 复述：观众听过一次的不再听第二次（4.0.0） ---------------------------------------
# 依据：S5 Scriptnotes 609（"if the audience hears it once, don't make them hear it twice"）；S14 McKee（两个人互相说
# 都知道的事，要重新发明这场）；S17 Scriptnotes 357（"As you and I both know… then why are we saying it?"）。
# 3.8.0 的"重复"候选按单个实词比，一句里只要有一个新词就放行（Offset EP01 s06 把 s05 的打包宣传、"考虑一下"、
# 明天碰面又说了一遍，仍判"删除测试已做（留 9）"）。这里改按短语与事实比：与前几场重合的三词短语（至少含一个实词）、
# 同一事实在本场反复出现。回扣与铺垫在字面上长得一样，所以作者在删除测试里写明"回扣 / 铺垫 / 锁定"的"留"不计入，
# 但列出来交复核——豁免只看这几个词，其余"留"的理由不豁免（自填的理由正是 3.8.0 放过复述的原因）。
FUNC = STOP | SUBJECTS | AUX | CONNECTIVES | {
    'about', 'into', 'from', 'with', 'them', 'him', 'her', 'his', 'our', 'their', 'us', 'been', 'being', 'will', 'if',
    'than', 'as', 'by', 'very', 'too', 'much', 'more', 'some', 'any', 'each', 'every', 'again', 'back', 'off', 'over',
    'down', 'one', "i'm", "it's", "don't", "that's", "i'll", "you're", "he's", "she's", "we're", "they're", "can't",
    "won't", "didn't", "isn't", "wasn't", 'gonna', 'let', "let's", 'got', 'get', 'going'}
GENERIC_STEMS = {_stem(w) for w in ECO_GENERIC}
WEEKDAY = {'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'}
WEEKDAY_ABBR = re.compile(r'\b(MON|TUE|TUES|WED|THU|THUR|THURS|FRI|SAT|SUN)\b')
ABBR_FULL = {'MON': 'monday', 'TUE': 'tuesday', 'TUES': 'tuesday', 'WED': 'wednesday', 'THU': 'thursday',
             'THUR': 'thursday', 'THURS': 'thursday', 'FRI': 'friday', 'SAT': 'saturday', 'SUN': 'sunday'}
HOURS = {w: i for i, w in enumerate(('one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten',
                                      'eleven', 'twelve'), 1)}
MINUTES = {'fifteen': '15', 'thirty': '30', 'forty-five': '45', "o'clock": '00'}
CLOCK_WORDS = re.compile(r"\b(" + '|'.join(HOURS) + r")[- ](fifteen|thirty|forty-five|o'clock)\b", re.I)
CLOCK_DIGITS = re.compile(r'\b(\d{1,2}):(\d{2})\b')
DAY_WORDS = {'tomorrow', 'tonight', 'yesterday'}
RETAIN_OK = re.compile(r'回扣|铺垫|锁定|弹药|callback', re.I)


def facts(text):
    """一句里的事实记号：星期、钟点（three-thirty = 3:30）、明天 / 今晚 / 昨天。"""
    out = set()
    low = text.lower()
    out |= {w for w in WEEKDAY if re.search(r'\b' + w + r'\b', low)}
    out |= {ABBR_FULL[m] for m in WEEKDAY_ABBR.findall(text)}
    out |= {f'{HOURS[h.lower()]}:{MINUTES[m.lower()]}' for h, m in CLOCK_WORDS.findall(text)}
    out |= {f'{int(h)}:{m}' for h, m in CLOCK_DIGITS.findall(text)}
    out |= {w for w in DAY_WORDS if re.search(r'\b' + w + r'\b', low)}
    return out


def _grams(text, n):
    toks = [_stem(w) for w in tokens(text)]
    out = set()
    for i in range(len(toks) - n + 1):
        g = tuple(toks[i:i + n])
        if any(len(w) >= 3 and w not in FUNC and w not in GENERIC_STEMS for w in g):
            out.add(g)
    return out


def _surface(text, grams):
    """把重合的词组还原成原句里的写法（相邻的三词组连成一段）；事实记号原样。"""
    toks = tokens(text)
    stems = [_stem(w) for w in toks]
    hit = set()
    for g in grams:
        if g[0] == '#fact':
            continue
        for i in range(len(stems) - len(g) + 1):
            if tuple(stems[i:i + len(g)]) == g:
                hit.update(range(i, i + len(g)))
    runs, cur = [], []
    for i in sorted(hit):
        if cur and i != cur[-1] + 1:
            runs.append(cur)
            cur = []
        cur.append(i)
    if cur:
        runs.append(cur)
    words_ = [' '.join(toks[i] for i in r) for r in sorted(runs, key=len, reverse=True)[:2]]
    words_ += [g[1] for g in grams if g[0] == '#fact' and not words_]
    return ' / '.join(words_)


def _context_units(paths):
    """前几场的台词与含英文的动作段（画面上的字）：[(标签, 引文, 文本)]。"""
    units = []
    for p in paths or ():
        p = Path(p)
        try:
            lines, actions = parse(p.read_text(encoding='utf-8'))
        except (ValueError, OSError):
            continue
        label = p.stem
        units += [(label, quote(ln), ln['text']) for ln in lines if not is_cjk(ln['text'])]
        units += [(label, f'画面「{_short(a, 30)}」', ' '.join(words(a))) for a in actions if len(words(a)) >= 2]
    return units


def restatement(lines, context=(), text=''):
    """与前几场重合的短语、同一事实反复出现。status：n/a / pass / issues；复述行附出处。"""
    T = THRESHOLDS
    n = T['restate_ngram']
    res = {'status': 'n/a', 'problems': [], 'review': [], 'lines': [], 'facts': []}
    rec = deletion_record(text) if text else None
    retained = {}
    for item in (rec or {}).get('留', []):
        if RETAIN_OK.search(item['reason'] or ''):
            for q in item['quotes']:
                retained[_norm_quote(q)] = item['reason']
    units = _context_units(context)
    last = Path(list(context)[-1]).stem if context else None
    index = {}
    for label, q, txt in units:
        for g in _grams(txt, n):
            index.setdefault(g, (label, q))
        for f in facts(txt):
            if f in DAY_WORDS and label != last:
                continue  # "明天 / 今晚"只和紧挨着的上一场比：隔了几场的"tonight"多半是另一晚
            index.setdefault(('#fact', f), (label, q))
    if units:
        res['status'] = 'pass'
        for k, ln in enumerate(lines):
            if is_cjk(ln['text']) or ln.get('is_group'):
                continue
            shared = {}
            for g in _grams(ln['text'], n):
                if g in index:
                    shared.setdefault(index[g], []).append(g)
            for f in facts(ln['text']):
                if ('#fact', f) in index:
                    shared.setdefault(index[('#fact', f)], []).append(('#fact', f))
            # 只重合一个星期几不算复述（反复提到的期限，如"Monday = Cut Day"，是在施压）；钟点、明天 / 今晚、短语才算
            shared = {s: gs for s, gs in shared.items() if any(g[0] != '#fact' or g[1] not in WEEKDAY for g in gs)}
            if not shared:
                continue
            (label, src), gs = max(shared.items(), key=lambda kv: len(kv[1]))
            nq = _norm_quote(ln['text'])
            why = next((r for q, r in retained.items() if q and q in nq), None)
            res['lines'].append({'line': k, 'quote': quote(ln), 'phrase': _surface(ln['text'], gs),
                                 'source': f'{label} {src}', 'exempt': why})
    per_fact = {}
    for k, ln in enumerate(lines):
        if is_cjk(ln['text']) or ln.get('is_group'):
            continue
        for f in facts(ln['text']):
            per_fact.setdefault(f, []).append(k)
    for f, ks in sorted(per_fact.items()):
        if len(ks) < T['fact_repeat_min']:
            continue
        item = {'fact': f, 'lines': ks, 'quotes': [quote(lines[k]) for k in ks]}
        if ks[-1] - ks[0] == len(ks) - 1:
            # 连着几句都在说它（"Coaches see it Monday." / "Monday's Cut Day." / "I know what Monday is."）是一轮
            # 围着这件事的来回——施压、讨价还价——不算复述，只列复核
            res['review'].append(f"同一事实「{f}」在一轮来回里连说 {len(ks)} 次（" + ' / '.join(item['quotes'][:3])
                                 + '）：每一句有没有人的立场在变——施压、讨价还价可以，复述不行')
            continue
        res['facts'].append(item)
    if res['facts'] and res['status'] == 'n/a':
        res['status'] = 'pass'
    counted = [x for x in res['lines'] if not x['exempt']]
    if len(counted) >= T['restate_problem_min']:
        ev = '；'.join(f"{x['quote']}（\"{x['phrase']}\" ← {x['source'][:60]}）" for x in counted[:3])
        res['problems'].append(f'{len(counted)} 句复述前几场观众已经听过或看过的内容：{ev}')
    elif counted:
        x = counted[0]
        res['review'].append(f"{x['quote']} 与前场重合（\"{x['phrase']}\" ← {x['source'][:60]}）：观众已知——"
                             f"这句要么是在拿它换东西（弹药），要么删；有意回扣就在删除测试里写明")
    for f in res['facts']:
        res['problems'].append(f"同一事实「{f['fact']}」在本场 {len(f['lines'])} 句台词里出现：" + ' / '.join(f['quotes'][:3]))
    for x in res['lines']:
        if x['exempt']:
            res['review'].append(f"{x['quote']} 与前场重合（← {x['source'][:50]}），删除测试写明留：{_short(x['exempt'], 30)}"
                                 f"——确认它是回扣 / 铺垫（产生新意思），不是复述")
    if res['problems']:
        res['status'] = 'issues'
    return res


def RESTATE_ISSUE(rep):
    return {
        'key': 'repeat',
        'title': '复述观众已知 / 同一事实反复',
        'evidence': '；'.join(rep['problems']),
        'why': '观众听过一次的不需要听第二次；把同一条消息再告诉另一个人、把同一个时间再报一遍，是在替观众做笔记。'
               '要么晚进（从人物已经知道之后开始），要么让它成为弹药（有人拿它换东西），要么交给画面。',
        'sources': ['S5', 'S14', 'S17'],
        'basis': '"听过一次不再听第二次"（S5）、"两个人互相说都知道的事要重新发明这场"（S14）有来源；三词短语、≥2 句、≥3 次是[推论]阈值',
    }


# ---- 设计卡：写正文前定这场怎么转（4.0.0；写作步骤，只在总判断里报） ----------------------
DESIGN_HEAD = re.compile(r'^##\s*设计[^\n]*$', re.M)
DESIGN_CELLS = ('推动者', '阻力', '转折', '弹药', '静音测试')
MESSENGER = re.compile(r'告诉|转达|通知|宣布|汇报|传话|报信|\btells?\b|\binforms?\b|\bannounces?\b', re.I)


def design_card(text):
    m = DESIGN_HEAD.search(text)
    if not m:
        return None
    sec = re.split(r'\n## ', text[m.end():], maxsplit=1)[0]
    cells = {}
    for key in DESIGN_CELLS:
        mm = re.search(key + r'[^：:\n]{0,8}[：:]\s*([^\n]*)', sec)
        v = (mm.group(1) if mm else '').strip()
        cells[key] = '' if (not v or set(v) <= set('_ ') or v in EMPTY_CELL) else v
    options = [o for _, o in re.findall(r'^\s*(\d)\s*[.、)）]\s*(\S[^\n]*)$', sec, re.M)]
    chosen = re.search(r'选\s*(\d)\s*[：:]\s*([^\n]*)', sec)
    noturn = re.search(r'本场不转\s*[:：]\s*(\S[^\n]*)', sec)
    return {'cells': cells, 'options': options, 'chosen': int(chosen.group(1)) if chosen else None,
            'chosen_reason': chosen.group(2).strip() if chosen else '', 'ledger': bool(re.search(r'观众(已知|账本)', sec)),
            'noturn': noturn.group(1).strip() if noturn else None}


def check_design(card, lines, total):
    T = THRESHOLDS
    res = {'status': 'n/a', 'missing': [], 'review': [], 'card': card}
    if len(lines) < T['min_lines'] and total < T['design_min_s']:
        return res
    if card is None:
        res['status'] = 'missing'
        return res
    if card['noturn']:
        res['status'] = 'pass'
        res['review'].append(f"设计卡登记本场不转：{_short(card['noturn'], 40)}——观众这段在看什么")
        return res
    res['missing'] = [k for k in DESIGN_CELLS if not card['cells'][k]]
    if not card['ledger']:
        res['missing'].append('观众已知')
    if len(card['options']) < 3:
        res['missing'].append('三种发生方式')
    turn = card['cells']['转折']
    if turn and not re.search(r'→|->', turn):
        res['review'].append(f'设计卡的转折「{_short(turn, 30)}」没写成"预期 → 结果"')
    if card['options'] and MESSENGER.search(card['options'][0]):
        res['review'].append(f"核心一步第 1 种「{_short(card['options'][0], 30)}」是传话：第一种应是别的发生方式（scene-design §二）")
    k = card['chosen']
    if k and 1 <= k <= len(card['options']) and MESSENGER.search(card['options'][k - 1]):
        res['review'].append(f"选中的一步「{_short(card['options'][k - 1], 30)}」是传话：带消息的人要换什么、"
                             f"消息遇到什么抵抗——理由「{_short(card['chosen_reason'], 30)}」说清了吗")
    res['status'] = 'incomplete' if res['missing'] else 'pass'
    return res


# ---- 判断 --------------------------------------------------------------------
def quote(ln):
    return f"{ln['speaker']}「{ln['text']}」"


def judge(lines, actions, stats, candidates=(), planted=(), declared=(), events=None, econ=None, rep=None, design=None):
    """返回 issues（问题）、signals（信号，不判定）、review_needed（需模型复核）。"""
    T = THRESHOLDS
    issues, signals, review = [], [], []
    n = stats['lines']
    if events and events['status'] in ('missing', 'issues'):
        # 事件轨排第一：连通只说明有人接话，事件轨说明这场谁要什么、每一段变了什么（3.5.0 / 3.7.0）
        issues.append(EVENTS_ISSUE(events))
    if rep and rep['status'] == 'issues':
        issues.append(RESTATE_ISSUE(rep))  # 4.0.0：复述排在事件轨之后、对白连通之前
    if events:
        review.extend(events['review'])
    if rep:
        review.extend(rep['review'])
    if design:
        review.extend(design['review'])
    if econ:
        review.extend(econ['review'])
    if n < T['min_lines']:
        signals.append(f'台词只有 {n} 句，统计判断不适用；按安静戏人工读。')
        return issues, signals, review
    # (a) 来回
    no_pair = stats['longest_exchange'] < T['longest_exchange_min']
    weak_link = stats['conversation_share'] < T['exchange_coverage_min']
    if no_pair and weak_link:
        ev = []
        for s, e in stats['orphan_runs'][:1]:
            ev.append('连续互不接话：' + ' / '.join(quote(lines[k]) for k in range(s, min(e, s + 3) + 1)))
        if not ev:
            ev.append('无人接的句子：' + ' / '.join(quote(lines[k]) for k in range(n) if lines[k]['orphan'])[:160])
        issues.append({
            'key': 'no_exchange',
            'title': '台词没有形成来回',
            'evidence': f"{n} 句 / {stats['speakers']} 个说话人，最长两人来回 {stats['longest_exchange']} 轮，"
                        f"能看出有人接或在接别人的台词只有 {int(stats['conversation_share'] * 100)}%；" + '；'.join(ev),
            'why': '每句都在对谁说、下一句接不接住，是会话成立的最小条件；观众听到的是各丢一句，没人对着谁说。补的应是对方的立场、要求或反应（可以是动作），不是 Okay / I know 这类接话。',
            'sources': ['S1', 'S5'],
            'basis': '相邻对与交错独白有来源（S1, S5）；"三轮才算来回""50%"是[推论]阈值',
        })
    # (b) 标语化：短、碎、每句换人
    slogan = []
    if stats['english_lines'] == 0:
        signals.append('台词无英文行：句长、短句、主谓宾指标未计算（只对英文台词实现）。')
        stats = dict(stats, mean_words=T['mean_words_min'], short_unexcused_share=0, fragment_unexcused_share=0)
    # 句长本身不判错（S1 §4.6）：平均句长只在来回也不成立时才算证据
    if stats['mean_words'] < T['mean_words_min'] and (no_pair or weak_link):
        ex = [quote(ln) for ln in lines if ln['short'] and not ln['is_group']][:4]
        slogan.append(f"平均 {stats['mean_words']} 词/句（{'、'.join(ex)}）")
    if stats['short_unexcused_share'] > T['short_unexcused_max']:
        ex = [quote(ln) for ln in lines if ln['short'] and not ln['short_excused']][:4]
        slogan.append(f"无理由的 ≤{T['short_words']} 词短句 {int(stats['short_unexcused_share'] * 100)}%（{'、'.join(ex)}）")
    if stats['fragment_unexcused_share'] > T['fragment_unexcused_max']:
        slogan.append(f"无主谓的碎句 {int(stats['fragment_unexcused_share'] * 100)}%")
    if stats['third_party_jump_share'] > T['third_party_jump_max'] and stats['longest_exchange'] < T['longest_exchange_min']:
        slogan.append(f"{int(stats['third_party_jump_share'] * 100)}% 的句子换到第三个人说且不接前句")
    if slogan:
        issues.append({
            'key': 'slogan',
            'title': '一人一句的标语化',
            'evidence': '；'.join(slogan),
            'why': '真实会话的单句平均约 1.7 秒、六七个词，长短随回应变化；连续的两到四词短句配上每句换人，只能一句一镜，声音落不到脸上。',
            'sources': ['S3', 'S4', 'S9', 'S8'],
            'basis': '轮次时长与语料均值有来源（S3, S4）；4 词/句、短句占比、"第三人跳"代理量是[推论]',
        })
    # (c) 画外 / 同框
    off = stats['offscreen_lines']
    if off:
        ev = ' / '.join(quote(lines[k]) for k in off[:3])
        item = {
            'key': 'offscreen',
            'title': '画外句配在别人脸上',
            'evidence': f'{len(off)} 句标了画外：{ev}',
            'why': '观众的视线跟着说话人的脸走，画外句落在别人脸上时听不出谁对谁说。',
            'sources': ['S9'],
            'basis': '视线跟随说话人有来源（S9）；由此判画外句为问题是[推论]',
        }
        host = next((i for i in issues if i['key'] == 'no_exchange'), None)
        if len(off) >= 2 and host:
            # 与来回问题同根因（没人对着谁说），合并进该条，不另立
            host['evidence'] += f'；其中 {len(off)} 句标为画外（{ev}）'
            host['sources'] = sorted(set(host['sources']) | {'S9'})
            host['basis'] += '；画外句判为问题依据 S9，属[推论]'
        else:
            issues.append(item)
    elif no_pair or weak_link:
        signals.append(f"两人来回最长 {stats['longest_exchange']} 轮、有人接的台词 {int(stats['conversation_share'] * 100)}%：多人场可以成立，读一遍确认谁在回应谁。")
    # (d) 潜台词支点：省略句 + 当作已知的新设定 + 无人问
    if candidates:
        c = candidates[0]
        carrier = ('本句前只有动作行「' + c['preceding_action'] + '」' + ('（中文动作行，能否算铺垫需人工核）' if c['action_is_cjk'] else '')) \
            if c['preceding_action'] else '前文没有任何句子或动作提到它'
        others = '；同类：' + '、'.join(f"{e['quote']}（{e['refs'][0]}）" for e in candidates[1:3]) if len(candidates) > 1 else ''
        issues.append({
            'key': 'unanchored_subtext',
            'title': '潜台词无支点',
            'evidence': f"{c['quote']} 把\"{c['refs'][0]}\"当作双方已知，{carrier}；下一句 {c['next']} 没人问" + others,
            'why': '人物之间省得掉的话，观众不在他们的共同基础里就读不出；一个凭空出现的设定要靠观众自己推三层，就是"看不懂"。若是有意不交代的旧梗，请在账本标明，模型复核时按此区分。',
            'sources': ['S10', 'S1', 'S11'],
            'basis': '共同基础与收件人设计有来源（S10, S1）；"省略句+新指称+无人问"作为看不懂的代理量是[推论]',
            'fixes': fixes_for(c),
        })

    # 信号（不判定）
    fresh = [e for e in planted if not e.get('stake')]
    if fresh:
        signals.append('本句明说的新设定（可作后文支点）：' + '、'.join(f"{e['quote'].split('「')[0]}—{e['refs'][0]}" for e in fresh[:4]) + '。')
    # 3.8.0：不再输出"全场没有一个问句""犹豫 / 口头填充 N 句"——它们把问句和填充当成要补的东西；数值仍在 JSON stats 里
    # 需模型复核
    for e in candidates[:3]:
        review.append(f"{e['quote']}：\"{e['refs'][0]}\"是有意不交代的旧梗，还是观众需要的设定？{'（前置中文动作行：' + e['preceding_action'][:30] + '…）' if e['action_is_cjk'] else ''}")
    for e in declared[:2]:
        review.append(f"{e['quote']}：\"{e['refs'][0]}\"账本已声明不交代——确认观众只需知道'有共同过去'，不需要内容。")
    for k in stats['unknown_addressee'][:6]:
        ln = lines[k]
        act = actions[ln['action_idx']] if ln['action_idx'] >= 0 else '（无前置动作行）'
        review.append(f"{quote(ln)} 收件人不明（前置动作行「{act[:40]}…」）：对谁说、对方在不在同一画面。")
    if econ and econ['status'] in ('missing', 'issues'):
        issues.append(ECONOMY_ISSUE(econ))
    for k, ln in enumerate(lines):
        if ln['addressee'] and ln['action_idx'] >= 0 and not ln['offscreen']:
            act = actions[ln['action_idx']]
            if ln['speaker'] not in act and ln['addressee'] not in act and not ln['is_group']:
                review.append(f"{quote(ln)} → {ln['addressee']}：最近的动作行没提到两人位置，能否同框。")
                if len(review) >= 8:
                    break
    return issues, signals, review


def EVENTS_ISSUE(events):
    missing = events['status'] == 'missing'
    return {
        'key': 'events',
        'title': '缺事件轨' if missing else '事件轨有问题',
        'evidence': '；'.join(events['problems']),
        'why': '观众不为信息、也不为换了背景收看：谁此刻要什么、每一行变了什么，他们才会看下去；地点只是变化的属性（EP03 场 4 v4.1 牛棚 16 s 没有事发生）。',
        'sources': ['S6', 'S12', 'S13', 'S1'],
        'basis': '三问与地点问题有来源（S6, S12, S13）；逐字核对与各阈值是[推论]，可登记例外',
    }


SOURCE_LEGEND = '来源编号 S1–S19 与[推论]阈值见 references/dialogue-review-sources.md；判为通过只表示没触发已知问题；说出口的是不是那件事、变化是不是新的由模型复核'


def _count(text):
    return len(re.sub(r'\s', '', text))


EVENTS_TXT = {'n/a': '不适用', 'missing': '缺事件轨', 'issues': '有问题'}


def events_phrase(ev):
    if not ev:
        return ''
    st = ev['status']
    if st in EVENTS_TXT and st != 'issues':
        head = EVENTS_TXT[st]
    else:
        head = (f"{ev['changes']} 次变化" + (f"、{len(ev['places'])} 处地点" if ev['places'] else '')
                + (f"、{ev['jumps']} 次时间跳" if ev['jumps'] else '') + f"（按文本估 ≈ {ev['estimate']:g} s）")
        if st == 'issues':
            head = '有问题——' + head
        elif st == 'excepted':
            head += '，已登记例外'
        if ev['voiced']:
            head += '；说出口——' + '、'.join(f"{v['who']}「{v['quote'].split('「', 1)[1][:30]}" for v in ev['voiced'][:2])
    back = (f"；分镜实排比剧本估时多 {ev['production_over']}%（提醒，是否回剧本层由用户定）"
            if ev.get('production_over') else '')
    return f"；事件轨：{head}{back}"


ECONOMY_TXT = {'n/a': '不适用', 'missing': '缺删除测试', 'issues': '记录与正文不符'}


def economy_phrase(econ):
    if not econ:
        return ''
    st = econ['status']
    if st == 'pass':
        rec = econ['record']
        head = '删除测试已做（' + ' '.join(f"{k} {len(rec[k])}" for k in ('删', '并', '压缩', '留') if rec[k]) + '）' \
            if any(rec[k] for k in ('删', '并', '压缩', '留')) else '删除测试已做（删：无）'
    else:
        head = ECONOMY_TXT[st]
    left = sum(1 for r in econ['review'])
    return f"；台词经济：{head}" + (f"，待复核 {left} 处" if left and st != 'n/a' else '')


REPEAT_TXT = {'n/a': '不适用（没给 --context）'}


def repeat_phrase(rep):
    if not rep or rep['status'] == 'n/a':
        return ''
    if rep['status'] == 'pass':
        n = len([x for x in rep['lines'] if not x['exempt']])
        m = len([x for x in rep['lines'] if x['exempt']])
        if not n and not m:
            return '；复述：未见'
        return '；复述：' + '、'.join(x for x in (f'{n} 句重合前场（列复核）' if n else '', f'{m} 句写明回扣' if m else '') if x)
    n = len([x for x in rep['lines'] if not x['exempt']])
    parts = ([f'{n} 句重合前场'] if n else []) + [f"「{f['fact']}」×{len(f['lines'])}" for f in rep['facts']]
    return '；复述：' + '、'.join(parts)


DESIGN_TXT = {'missing': '缺', 'pass': '齐'}


def design_phrase(design):
    if not design or design['status'] == 'n/a':
        return ''
    if design['status'] == 'incomplete':
        return '；设计卡：缺 ' + '、'.join(design['missing'])
    return '；设计卡：' + DESIGN_TXT[design['status']]


def render(path, stats, issues, signals, review, full=False, limit=800, events=None, econ=None, rep=None, design=None):
    """一句总判断（对白连通 / 事件轨分开）+ ≤3 个问题 + 信号 + 需模型复核 + 交接提示。
    默认 ≤ limit 字（不计空白）：超出先减复核条目，再减信号。"""
    n = stats['lines']
    dialogue_issues = [i for i in issues if i['key'] not in ('events', 'economy', 'repeat')]
    ev = economy_phrase(econ) + repeat_phrase(rep) + events_phrase(events) + design_phrase(design)
    if n < THRESHOLDS['min_lines']:
        verdict = f'{path.name}：台词 {n} 句，材料太少，不做对白统计{ev}。'
    elif not dialogue_issues:
        # 3.8.0：总判断不再报"X% 台词有人接""最长来回 N 轮""平均词数"——它们把接话和轮数当成越多越好；数值在 JSON stats 里
        verdict = (f"{path.name}：对白连通通过（{n} 句 / {stats['speakers']} 人，画外 {len(stats['offscreen_lines'])} 句；"
                   f"连通只说明有人对着人说，不说明每句有用）{ev}。")
    else:
        verdict = f"{path.name}：对白连通有问题{ev}。"
    listed = [i for i in issues if not i.get('compact')]  # 缺删除测试只在总判断的"台词经济"里报
    if listed:
        verdict += f"问题：{'、'.join(i['title'] for i in listed)}。"
    shown = listed[:3]
    def head_lines(with_why=True):
        out = [verdict] + [f"{i}. {it['title']}：{it['evidence']}。" + (it['why'] if with_why else '') + f"（{it['basis']}）"
                           for i, it in enumerate(shown, 1)]
        for it in shown:
            if it.get('fixes'):
                out.append('改法（改法未定时供选，不改稿）：' + ' '.join(f'({i}) {f}' for i, f in enumerate(it['fixes'], 1)))
        return out
    head = head_lines()
    tail = []
    if stats['offscreen_lines']:
        tail.append(f"交接 film-director：画外句 {len(stats['offscreen_lines'])} 句，分镜时核对声画对位。")
    tail.append(SOURCE_LEGEND)
    k = len(review) if full else min(len(review), 3)
    while True:
        mid = []
        if signals:
            mid.append('信号：' + ' '.join(signals))
        if k:
            mid.append('需模型复核：' + ' '.join(f'({i}) {r}' for i, r in enumerate(review[:k], 1)))
        text = '\n'.join(head + mid + tail)
        if full or _count(text) <= limit:
            return text
        if k:
            k -= 1
        elif signals:
            signals = []
        elif head == head_lines():
            head = head_lines(with_why=False)  # 最后一步：问题只留证据与依据，去掉"为什么"
        else:
            return text


def ledger_text(text):
    """模板里作者声明决定的位置：'## 剧本页' 之前的版本 / 修订账本行，以及 '## 上下文承接' 一节。对白审阅等分析栏目不算声明。"""
    head = text.split('## 剧本页', 1)[0] if '## 剧本页' in text else ''
    m = re.search(r'## 上下文承接.*?(?=\n## |\Z)', text, re.S)
    bullet = re.search(r'^\s*[-*]\s*上下文承接[：:][^\n]*', text, re.M)  # 4.0.0 模板：按需附注里的一行
    return head + ('\n' + m.group(0) if m else '') + ('\n' + bullet.group(0) if bullet else '')


def context_text(paths):
    """前几场的正文（台词 + 动作行）只用来建立已出现过的设定；解析失败的文件按纯文本并入。"""
    parts = []
    for p in paths or ():
        raw = Path(p).read_text(encoding='utf-8')
        try:
            parts.append(body(raw))
        except ValueError:
            parts.append(raw)
    return '\n'.join(parts)


def review_file(path, full=False, context=None, production_total=None, later=None):
    text = Path(path).read_text(encoding='utf-8')
    lines, actions = parse(text)
    names = sorted({ln['speaker'] for ln in lines})
    stats = analyse(lines, actions, names)
    ledger = ledger_text(text)
    events = check_events(text, events_card(text), lines, actions, names, production_total)
    econ = check_economy(text, economy(lines, names, scene_lines(context), scene_lines(later)), lines)
    rep = restatement(lines, context, text)
    design = check_design(design_card(text), lines, events['estimate'])
    candidates, planted, declared = anchoring(lines, actions, context_text(context), ledger, events['terms'])
    stats['unanchored'] = [e['line'] for e in candidates]
    stats['planted'] = [e['line'] for e in planted]
    stats['declared'] = [e['line'] for e in declared]
    issues, signals, review = judge(lines, actions, stats, candidates, planted, declared, events, econ, rep, design)
    dialogue_ok = not [i for i in issues if i['key'] not in ('events', 'economy', 'repeat')]
    return {
        'file': str(path), 'context': [str(c) for c in (context or [])], 'later': [str(c) for c in (later or [])],
        'stats': stats, 'issues': issues, 'signals': signals, 'review_needed': review,
        'anchoring': {'candidates': candidates, 'planted': planted, 'declared': declared},
        'verdict': 'issues' if issues else ('insufficient' if stats['lines'] < THRESHOLDS['min_lines'] else 'pass'),
        'checks': {'dialogue': 'insufficient' if stats['lines'] < THRESHOLDS['min_lines'] else ('pass' if dialogue_ok else 'issues'),
                   'economy': econ['status'], 'repeat': rep['status'], 'events': events['status'],
                   'design': design['status']},
        'economy': econ,
        'repeat': rep,
        'design': {k: v for k, v in design.items()},
        'events': {k: v for k, v in events.items() if k != 'terms'},
        'lines': [{k: v for k, v in ln.items() if k in ('speaker', 'text', 'words', 'clause', 'addressee', 'link_prev', 'offscreen', 'orphan', 'in_conversation', 'presupposed')} for ln in lines],
        'thresholds': THRESHOLDS,
        'text': render(Path(path), stats, issues, signals, review, full=full, events=events, econ=econ, rep=rep, design=design),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scenes', nargs='+')
    ap.add_argument('--json', action='store_true', help='输出 JSON（含逐句特征与阈值）')
    ap.add_argument('--full', action='store_true', help='不截到 800 字，复核清单全列')
    ap.add_argument('--context', nargs='*', default=[], help='前几场剧本页：建立前文已出现的设定、查"前文说过"，不 review')
    ap.add_argument('--later', nargs='*', default=[], help='后几场剧本页：查候选台词在后文有没有回扣（可能是铺垫），不 review')
    ap.add_argument('--wps', type=float, help=f"英文台词语速（词/秒，默认 {THRESHOLDS['wps']:g}）")
    ap.add_argument('--action-sec', type=float, help=f"无台词段每个动作句的秒数（默认 {THRESHOLDS['action_s']:g}）")
    ap.add_argument('--production-total', type=float,
                    help='film-director 分镜实排的场总时长（秒）：比剧本估时多 20%% 以上时提醒用户（不退回）')
    args = ap.parse_args(argv)
    if args.wps:
        THRESHOLDS['wps'] = args.wps
    if args.action_sec is not None:
        THRESHOLDS['action_s'] = args.action_sec
    results = []
    for p in args.scenes:
        try:
            results.append(review_file(p, full=args.full, context=args.context, production_total=args.production_total,
                                       later=args.later))
        except (ValueError, OSError) as e:
            print(f'{p}: 无法解析（{e}）', file=sys.stderr)
            return 2
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print('\n\n'.join(r['text'] for r in results))
    return 1 if any(r['verdict'] == 'issues' for r in results) else 0


if __name__ == '__main__':
    sys.exit(main())
