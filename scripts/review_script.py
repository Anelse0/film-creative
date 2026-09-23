#!/usr/bin/env python3
"""出稿后的剧本 review：对白连通、人物赌注、画面推进（film-creative 3.6.1）。

用法:
  review_script.py 03_script/scene-03.md [scene-04.md ...] [--context scene-01.md scene-02.md] [--json] [--full]
                   [--wps 4] [--action-sec 1.5] [--production-total 88]
  --context：按 story-context 指认的前几场，只用来建立"前文已出现过的设定"，不 review 它们。
  --production-total：film-director 分镜实排的场总时长；比剧本估时多 20% 以上时提醒（不退回，是否回剧本层由用户定）。

读 `templates/script-scene.md` 格式的剧本页（`<!-- script-body:start/end -->` 之间；
台词块为 `**NAME**` 或独立一行的角色名，下一行台词；括号行是表演/声音提示），
只做可量化的部分：收件人链、来回（exchange）、句长分布、短句占比、连续无人接的句子、
主谓宾完整度、画外标注、每句换人（一句一镜代理量）、潜台词支点（省略句依赖的设定前文有没有建立）；
3.5.0 起另报"人物赌注"：读剧本页正文前的"## 本场赌注"卡，逐字核对卡上声明说出口的句子是否在正文里、
是不是本人说的、有没有人接；不说的要有理由与代价；缺卡或全场无人说出口（未登记例外）判为问题。
3.6.0 起另报"画面推进"：读正文前的"## 场面轨"（每段：地点 / 主要活动 / 时间 / 在场的人 / 观众新看见什么 / 锚句 / 估时），
逐字核对锚句在正文动作行里且顺序一致；按文本估时（台词按语速，无台词段按动作句数）；估时 ≥30 s 的场缺轨、
或全场只有一个"地点 × 活动"组合且无时间跳、未登记"本场单一画面：理由"判为问题；某一段画面不变 ≥40 s、自报估时偏小
列为需模型复核。镜头与机位不在这里判——那是 film-director 的事。
连通性、赌注与画面分开给结论（checks.dialogue / checks.stakes / checks.picture），"对白连通通过"不代表人物有戏。语义判断不冒充已判定，
列为"需模型复核"的证据清单。阈值全部是 `[推论]`（按 THE ORDER EP02 场 1 v1/v3 校准），
在 THRESHOLDS 里改。每条判断引用的一手来源见 references/dialogue-review-sources.md（S1–S12）。

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
    'stake_min_lines': 3,      # 说了这么多句的人必须上赌注卡（主要说话人）
    'min_voiced': 1,           # 全场至少几个人把自己的赌注说出口；卡上写"本场不说出口：理由"可登记例外
    # 画面推进（3.6.0；按 THE ORDER EP02 场 1、EP03 场 1–4 的剧本估时与分镜实排校准，见 dialogue-review-sources.md §三）
    'wps': 4.0,                # 英文台词语速（词/秒；THE ORDER 用户定 4，`--wps` 可改）
    'cjk_cps': 4.5,            # 中文台词语速（字/秒）
    'action_s': 1.5,           # 无台词段里每个动作句的时长（秒；`--action-sec` 可改）
    'insert_max_sents': 2,     # 两句台词之间 ≤ 此数的动作句视为反应插入，与台词同步，不另计时
    'picture_min_s': 30,       # 按文本估时 ≥ 此秒数的场才要场面轨、才判"全场一个画面"
    'segment_review_s': 40,    # 一段画面（地点×活动×在场人物都不变）估时 ≥ 此秒数 → 需模型复核
    'estimate_under': 0.85,    # 作者自报总估时 < 按文本估时 × 此比例 → 需模型复核（文本估时误差约 ±15%）
    'production_over': 1.2,    # 分镜实排 > 剧本估时 × 此比例 → 提醒用户（场面轨是告知不是锁定；回不回剧本层由用户定）
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
    ('让第三人替观众问', '在场另一人问一句"What {head}?"，答一句', '多一来一回，旁人知情', '知情范围扩大，"只限两人"的设定会变'),
)


def fixes_for(entry):
    """按 SKILL.md"批评已有稿、改法未定"契约：两到三种改法，各一两句（改什么 / 这场变成什么 / 影响后面什么），不改稿。"""
    ref = entry['refs'][0]
    head = ref.split()[-1]
    who = entry['quote'].split('「')[0]
    return [f"{name}：{what.format(who=who, ref=ref, head=head)}；这场变成 {becomes}；影响后面 {after}" for name, what, becomes, after in FIX_TEMPLATES]


# ---- 人物赌注：谁要什么、有没有说出口（3.5.0） ------------------------------------
# 依据：Mamet 每场三问 WHO WANTS WHAT? / WHAT HAPPENS IF THEY DON'T GET IT? / WHY NOW?，"THE AUDIENCE WILL NOT TUNE IN
# TO WATCH INFORMATION"（S6）；Mazin "Fear is our connection to a character"（S12）；说出口后有没有人接按相邻对（S1, S2）。
# 脚本不判一句话"有没有欲望"（那会变成关键词表）：它只逐字核对作者写台词前填的卡与正文是否一致，
# 语义（这句说的是不是卡上那件事）列为需模型复核。
STAKES_HEAD = re.compile(r'^##\s*本场赌注[^\n]*$', re.M)
QUOTED = re.compile(r'[“"「]([^”"」]+)[”"」]')
STAKE_COLS = (('name', '人物'), ('standing', '持续赌注'), ('want', '要什么'), ('fear', '怕'),
              ('why_now', '为什么'), ('voiced', '说出口'), ('end', '场末'))
EMPTY_CELL = {'', '—', '-', '无', '没有', '空', '未写', '__'}


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


def stakes_card(text):
    """剧本页正文前的"## 本场赌注"表。返回 None（无卡）或 {'rows': [...], 'exception': str|None}。"""
    m = STAKES_HEAD.search(text)
    if not m:
        return None
    sec = re.split(r'\n## ', text[m.end():], maxsplit=1)[0]
    rows = [r for r in sec.splitlines() if r.strip().startswith('|')]
    exc = re.search(r'本场不说出口\s*[:：]\s*(\S[^\n]*)', sec)
    exception = exc.group(1).strip() if exc and exc.group(1).strip() not in EMPTY_CELL else None
    if not rows:
        return {'rows': [], 'exception': exception}
    header = _cells(rows[0])
    idx = {}
    for key, word in STAKE_COLS:
        idx[key] = next((i for i, h in enumerate(header) if word in h), None)
    out = []
    for r in rows[1:]:
        cells = _cells(r)
        if all(set(c) <= set('-: ') for c in cells):
            continue
        get = lambda k: cells[idx[k]] if idx[k] is not None and idx[k] < len(cells) else ''
        name = get('name').strip('*').strip()
        if not name or name in EMPTY_CELL:
            continue
        out.append({k: get(k) for k, _ in STAKE_COLS} | {'name': name})
    return {'rows': out, 'exception': exception}


def check_stakes(card, lines, names):
    """逐字核对赌注卡与正文。返回 {'status', 'problems', 'review', 'voiced', 'terms'}。
    status：n/a（安静戏 / 独角戏）、missing（无卡）、issues、excepted（无人说出口但登记了例外）、pass。"""
    T = THRESHOLDS
    speakers = [nm for nm in names if nm not in GROUP_SPEAKERS]
    res = {'status': 'n/a', 'problems': [], 'review': [], 'voiced': [], 'terms': set()}
    if len(lines) < T['min_lines'] or len(speakers) < 2:
        return res
    if card is None:
        res['status'] = 'missing'
        counts = {nm: sum(ln['speaker'] == nm for ln in lines) for nm in speakers}
        ranked = sorted(counts.items(), key=lambda x: -x[1])
        main = [f'{nm} {c} 句' for nm, c in ranked if c >= T['stake_min_lines']]
        first = next(ln for ln in lines if ln['speaker'] == ranked[0][0])
        res['problems'].append('没有"## 本场赌注"卡' + (f'（主要说话人：{"、".join(main)}）' if main else '')
                               + f'，台词只能自证连通，如 {quote(first)[:48]}')
        return res
    by_name = {}
    for row in card['rows']:
        who = next((nm for nm in speakers if nm.lower() == norm_name(row['name']).lower()), row['name'])
        by_name[who] = row
    counts = {nm: sum(ln['speaker'] == nm for ln in lines) for nm in speakers}
    for nm, c in counts.items():
        if c >= T['stake_min_lines'] and nm not in by_name:
            res['problems'].append(f'{nm} 说了 {c} 句，卡上没有他此刻要什么')
    for who, row in by_name.items():
        res['terms'] |= {_stem(t) for t in tokens(row['standing']) if len(t) >= 3}
        quotes = QUOTED.findall(row['voiced'])
        if quotes:
            for q in quotes:
                nq = _norm_quote(q)
                hit = [k for k, ln in enumerate(lines) if nq and nq in _norm_quote(ln['text'])]
                own = [k for k in hit if lines[k]['speaker'] == who]
                if not hit:
                    res['problems'].append(f'卡上 {who} 说出口的"{q}"不在正文里')
                    continue
                if not own:
                    res['problems'].append(f'卡上记为 {who} 说出口的"{q}"，正文里是 {lines[hit[0]]["speaker"]} 说的')
                    continue
                k = own[0]
                res['voiced'].append({'who': who, 'line': k, 'quote': quote(lines[k])})
                res['terms'] |= {_stem(t) for t in tokens(q) if len(t) >= 3}
                nxt = lines[k + 1] if k + 1 < len(lines) else None
                if nxt and nxt['speaker'] != who and nxt['link_prev']:
                    res['voiced'][-1]['reply'] = quote(nxt)
                else:
                    res['review'].append(f'{quote(lines[k])} 说出口后{"下一句 " + quote(nxt) + " 没有接它" if nxt else "没人再说话"}：'
                                         f'是有意的不答吗？不答的人为什么不答，卡上有没有写')
                res['review'].append(f'{who} 卡上的赌注是"{(row["want"] or row["standing"])[:30]}"，说出口的是 {quote(lines[k])}：'
                                     f'这句说的是不是这件事（按取向 6：面对谁、刚发生什么、为什么此刻）')
        else:
            reason, cost = _field(row['voiced'], '理由'), _field(row['voiced'], '代价')
            if not (reason and cost):
                res['problems'].append(f'{who} 上了卡，但既没有说出口的台词，也没写不说的理由与代价'
                                       f'（持续赌注：{row["standing"][:40] or "空"}）')
            else:
                res['review'].append(f'{who} 不说：{reason}；代价 {cost}——观众能从处境读出他在绕什么吗')
        if not re.search(r'[（(][^)）]+[)）]', row['standing']):
            res['review'].append(f'{who} 的持续赌注没写出处（ip.md / 故事 / 框架哪一行）')
        end = row['end'].strip()
        if not end or end in EMPTY_CELL:
            res['review'].append(f'{who} 场末没写得到 / 没得到 / 推迟')
        elif re.search(r'推迟|没得到|未得到|放下', end) and not _field(end, '代价'):
            res['review'].append(f'{who} 场末"{end[:24]}"没写代价：欲望是不是被一句"That\'s fair / Okay"接住收掉了')
    if res['problems']:
        res['status'] = 'issues'
    elif len({v['who'] for v in res['voiced']}) < T['min_voiced']:
        if card['exception']:
            res['status'] = 'excepted'
            res['review'].insert(0, f'全场无人把赌注说出口，已登记例外：{card["exception"]}')
        else:
            res['status'] = 'issues'
            res['problems'].append('全场没有一个人把自己的赌注说出口（卡上都是不说），也没有登记"本场不说出口：理由"')
    else:
        res['status'] = 'pass'
    return res


# ---- 画面推进（3.6.0） ----------------------------------------------------------
TRACK_HEAD = re.compile(r'^##\s*场面轨[^\n]*$', re.M)
TRACK_COLS = (('seg', '段'), ('loc', '地点'), ('act', '活动'), ('time', '时间'), ('who', '谁'),
              ('new', '新看见'), ('anchor', '锚句'), ('est', '估时'))
CONTINUOUS = {'连续', '接上', '同上', '紧接'}
ACTION_SENT = re.compile(r'[。！？；!?]|(?<=[a-z])\.\s')
PARENS = re.compile(r'[（(][^)）]*[)）]')


def _plain(t):
    return re.sub(r'\s+', '', re.sub(r'[“”"「」]', '', t))


def _combo_key(cell):
    return re.sub(r'\s+', '', PARENS.sub('', cell)).lower()


def track_card(text):
    """剧本页正文前的"## 场面轨"表。返回 None（无轨）或 {'rows', 'exception', 'total'}。"""
    m = TRACK_HEAD.search(text)
    if not m:
        return None
    sec = re.split(r'\n## ', text[m.end():], maxsplit=1)[0]
    rows = [r for r in sec.splitlines() if r.strip().startswith('|')]
    exc = re.search(r'本场单一画面\s*[:：]\s*(\S[^\n]*)', sec)
    exception = exc.group(1).strip() if exc and exc.group(1).strip().strip('_ ') not in EMPTY_CELL else None
    tot = re.search(r'总估时\s*[≈约]?\s*(\d+(?:\.\d+)?)\s*s', sec)
    out = []
    if rows:
        header = _cells(rows[0])
        idx = {k: next((i for i, h in enumerate(header) if w in h), None) for k, w in TRACK_COLS}
        for r in rows[1:]:
            cells = _cells(r)
            if all(set(c) <= set('-: ') for c in cells):
                continue
            get = lambda k: cells[idx[k]] if idx[k] is not None and idx[k] < len(cells) else ''
            if not get('loc') or get('loc') in EMPTY_CELL:
                continue
            out.append({k: get(k) for k, _ in TRACK_COLS})
    total = float(tot.group(1)) if tot else None
    if total is None:
        nums = [re.search(r'\d+(?:\.\d+)?', r['est']) for r in out]
        total = sum(float(n.group(0)) for n in nums if n) if out and all(nums) else None
    return {'rows': out, 'exception': exception, 'total': total}


def declared_total(text, card):
    """作者自报的总估时：场面轨"总估时"或各段估时之和；旧稿回退到节拍表"总窗口 ≈ N s"。"""
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


def check_picture(text, card, lines, actions, production_total=None):
    """场面轨与正文核对。status：n/a（短场且无轨）、missing、issues、excepted（单一画面已登记理由）、pass。"""
    T = THRESHOLDS
    tl = timeline(lines, actions)
    heading = next((a for a in actions if START_ACTION_RESET.match(a)), '')
    res = {'status': 'n/a', 'problems': [], 'review': [], 'estimate': tl['total'], 'segments': [],
           'declared': declared_total(text, card), 'combos': 0, 'jumps': 0}
    if res['declared'] and res['declared'] < tl['total'] * T['estimate_under']:
        res['review'].append(f"自报总估时 {res['declared']:g} s，按文本估 ≈ {tl['total']:g} s：无台词段（越过、冲刺、过线、看一眼）"
                             f"有没有算进去（文本估时误差约 ±15%，[推论]）")
    if production_total and res['declared'] and production_total > res['declared'] * T['production_over']:
        res['production_over'] = round((production_total / res['declared'] - 1) * 100)
        res['review'].insert(0, f"分镜实排 {production_total:g} s，比剧本估时 {res['declared']:g} s 多 "
                                f"{round((production_total / res['declared'] - 1) * 100)}%（≥{round((T['production_over'] - 1) * 100)}%）："
                                f"提醒——多出来的时间观众在看什么，是不是同一个画面拉长了；要不要回剧本层重核场面轨由用户定")
    if card is None:
        if tl['total'] >= T['picture_min_s']:
            res['status'] = 'missing'
            place = heading.split('·')[1].strip() if heading.count('·') >= 2 else '（标题未写地点）'
            res['place'] = place
            res['problems'].append(f'没有"## 场面轨"，按文本估 ≈ {tl["total"]:g} s，只有场景标题的地点「{place}」，'
                                   f'看不出这几十秒观众看到的地点、活动有没有变化')
        return res
    # 锚句逐字在正文动作行里、按顺序
    starts, last = [], -1
    for k, row in enumerate(card['rows'], 1):
        a = _plain(row['anchor'])
        if not a or a in EMPTY_CELL:
            res['problems'].append(f'第 {k} 段没写锚句（本段第一句动作行，逐字）')
            starts.append(None)
            continue
        hit = next((i for i, act in enumerate(actions) if a in _plain(act)), None)
        if hit is None:
            res['problems'].append(f'第 {k} 段锚句「{row["anchor"][:24]}」不在正文动作行里')
        elif hit < last:
            res['problems'].append(f'第 {k} 段锚句在正文里出现在上一段之前（场面轨顺序与正文不符）')
        starts.append(hit)
        if hit is not None:
            last = max(last, hit)
    if not card['rows']:
        res['problems'].append('"## 场面轨"是空表')
    combos = {(_combo_key(r['loc']), _combo_key(r['act'])) for r in card['rows']}
    jumps = sum(1 for r in card['rows'][1:] if _combo_key(r['time']) and r['time'].strip() not in EMPTY_CELL
                and not any(_combo_key(r['time']).startswith(c) for c in CONTINUOUS))
    res['combos'], res['jumps'] = len(combos), jumps
    # 逐段估时（锚句划界；第一段含锚句之前的开场）
    if card['rows'] and all(s is not None for s in starts) and starts == sorted(starts):
        bounds = [0] + starts[1:] + [len(actions)]
        for k in range(len(starts)):
            s, e = bounds[k], bounds[k + 1]
            secs = sum(tl['action'][s:e]) + sum(t for ln, t in zip(lines, tl['line']) if s <= ln['action_idx'] < e)
            res['segments'].append(round(secs, 1))
        longest = max(range(len(res['segments'])), key=lambda i: res['segments'][i])
        if res['segments'][longest] >= T['segment_review_s']:
            row = card['rows'][longest]
            res['review'].append(f"第 {longest + 1} 段（{row['loc']} · {row['act']}）按文本估 ≈ {res['segments'][longest]:g} s 画面不变，"
                                 f"分镜只能靠机位变化：是有意的（压迫、等待、一镜到底），还是可以让地点、活动或在场的人变一次")
    if len(combos) == 1 and not jumps and tl['total'] >= T['picture_min_s']:
        r0 = card['rows'][0]
        one = f'{PARENS.sub("", r0["loc"]).strip()} · {PARENS.sub("", r0["act"]).strip()}'
        if card['exception']:
            res['review'].insert(0, f'全场一个画面（{one}），已登记理由：{card["exception"]}——观众在这 '
                                    f'{tl["total"]:g} s 里能看见处境在变吗')
            res['status'] = 'excepted'
        else:
            res['problems'].append(f'场面轨 {len(card["rows"])} 段都是同一个地点 × 活动（{one}），没有时间跳，'
                                   f'按文本估 ≈ {tl["total"]:g} s，也没有登记"本场单一画面：理由"')
    if res['problems']:
        res['status'] = 'issues'
    elif res['status'] != 'excepted':
        res['status'] = 'pass'
    return res


# ---- 判断 --------------------------------------------------------------------
def quote(ln):
    return f"{ln['speaker']}「{ln['text']}」"


def judge(lines, actions, stats, candidates=(), planted=(), declared=(), stakes=None, picture=None):
    """返回 issues（问题）、signals（信号，不判定）、review_needed（需模型复核）。"""
    T = THRESHOLDS
    issues, signals, review = [], [], []
    n = stats['lines']
    if stakes and stakes['status'] in ('missing', 'issues'):
        # 赌注排第一：连通只说明有人接话，赌注说明这场谁要什么（3.5.0）
        issues.append({
            'key': 'stakes',
            'title': '缺本场赌注卡' if stakes['status'] == 'missing' else '人物赌注没落到台词',
            'evidence': '；'.join(stakes['problems']),
            'why': '观众不为信息收看；知道人物此刻要什么、怕失去什么才会担心。承接只约束不能抵触什么，不该占掉台词。',
            'sources': ['S6', 'S12', 'S1'],
            'basis': '三问与"fear"有来源（S6, S12）；逐字核对、"≥3 句上卡""至少一人说出口"是[推论]，可登记例外',
        })
    if stakes:
        review.extend(stakes['review'])
    if n < T['min_lines']:
        signals.append(f'台词只有 {n} 句，统计判断不适用；按安静戏人工读。')
        if picture and picture['status'] in ('missing', 'issues'):
            issues.append({'key': 'picture', 'compact': picture['status'] == 'missing', 'title': '缺场面轨' if picture['status'] == 'missing' else '画面没有推进',
                           'evidence': '；'.join(picture['problems']), 'why': '无台词场更依赖观众看见的画面在变。',
                           'sources': ['S13'], 'basis': '地点问题有来源（S13）；阈值与估时是[推论]'})
        if picture:
            review.extend(picture['review'])
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
            'why': '每句都在对谁说、下一句接不接住，是会话成立的最小条件；观众听到的是各丢一句，没人对着谁说。',
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

    # (e) 画面推进（3.6.0）：独立于对白，排在对白问题之后；状态总在总判断里报
    if picture and picture['status'] in ('missing', 'issues'):
        issues.append({
            'key': 'picture', 'compact': picture['status'] == 'missing',  # 缺轨只在总判断里报一句，不占 ≤3 个问题的位置
            'title': '缺场面轨' if picture['status'] == 'missing' else '画面没有推进',
            'evidence': '；'.join(picture['problems']),
            'why': '剧本层要交代观众在哪里看见什么、随时间怎么变；整场一个地点一种活动，分镜只能靠机位轮换补变化，时长也会被低估（EP03 场 4 v4：剧本估 57 s，分镜排出 74 s，四种跟拍轮换）。',
            'sources': ['S13'],
            'basis': '"最显而易见的地点通常最无趣"与"这场长还是短"有来源（S13）；30 s、地点×活动组合、按文本估时是[推论]，可登记"本场单一画面：理由"',
        })
    if picture:
        review.extend(picture['review'])
    # 信号（不判定）
    fresh = [e for e in planted if not e.get('stake')]
    if fresh:
        signals.append('本句明说的新设定（可作后文支点）：' + '、'.join(f"{e['quote'].split('「')[0]}—{e['refs'][0]}" for e in fresh[:4]) + '。')
    if stats['questions']:
        signals.append(f"问句 {stats['questions']} 个，被下一位接住 {stats['questions_answered']} 个。")
    else:
        signals.append('全场没有一个问句。')
    signals.append(f"犹豫 / 打断 / 口头填充标记 {stats['hesitation_marks']} 句（有无都不判错）。")
    # 需模型复核
    for e in candidates[:3]:
        review.append(f"{e['quote']}：\"{e['refs'][0]}\"是有意不交代的旧梗，还是观众需要的设定？{'（前置中文动作行：' + e['preceding_action'][:30] + '…）' if e['action_is_cjk'] else ''}")
    for e in declared[:2]:
        review.append(f"{e['quote']}：\"{e['refs'][0]}\"账本已声明不交代——确认观众只需知道'有共同过去'，不需要内容。")
    for k in stats['unknown_addressee'][:6]:
        ln = lines[k]
        act = actions[ln['action_idx']] if ln['action_idx'] >= 0 else '（无前置动作行）'
        review.append(f"{quote(ln)} 收件人不明（前置动作行「{act[:40]}…」）：对谁说、对方在不在同一画面。")
    for k, ln in enumerate(lines):
        if ln['addressee'] and ln['action_idx'] >= 0 and not ln['offscreen']:
            act = actions[ln['action_idx']]
            if ln['speaker'] not in act and ln['addressee'] not in act and not ln['is_group']:
                review.append(f"{quote(ln)} → {ln['addressee']}：最近的动作行没提到两人位置，能否同框。")
                if len(review) >= 8:
                    break
    return issues, signals, review


SOURCE_LEGEND = '来源编号 S1–S13 与[推论]阈值见 references/dialogue-review-sources.md；判为通过只表示没触发已知问题；赌注卡的语义（那句说的是不是那件事）由模型复核'


def _count(text):
    return len(re.sub(r'\s', '', text))


STAKES_TXT = {'n/a': '不适用', 'missing': '缺卡', 'issues': '有问题', 'excepted': '无人说出口（已登记例外）'}
PICTURE_TXT = {'n/a': '短场不要求场面轨', 'missing': '缺场面轨', 'issues': '有问题', 'excepted': '一个画面（已登记理由）'}


def picture_phrase(picture):
    if not picture:
        return ''
    st = picture['status']
    head = (f"{len(picture['segments']) or '?'} 段、{picture['combos']} 个地点×活动" + (f"、{picture['jumps']} 次时间跳" if picture['jumps'] else '')
            if st == 'pass' else PICTURE_TXT[st])
    place = f"「{picture['place']}」" if st == 'missing' and picture.get('place') else '按文本估'
    back = (f"；分镜实排比剧本估时多 {picture['production_over']}%（提醒，是否回剧本层由用户定）"
            if picture.get('production_over') else '')
    return f"；画面：{head}（{place} ≈ {picture['estimate']:g} s）{back}"


def render(path, stats, issues, signals, review, full=False, limit=800, stakes=None, picture=None):
    """一句总判断（对白连通 / 人物赌注分开）+ ≤3 个问题 + 信号 + 需模型复核 + 交接提示。
    默认 ≤ limit 字（不计空白）：超出先减复核条目，再减信号。"""
    n = stats['lines']
    stakes = stakes or {'status': 'n/a', 'voiced': []}
    if stakes['status'] == 'pass':
        st = '说出口——' + '、'.join(f"{v['who']}「{v['quote'].split('「', 1)[1][:36]}" + ('（有人接）' if v.get('reply') else '（没人接）')
                                  for v in stakes['voiced'][:3])
    else:
        st = STAKES_TXT[stakes['status']]
    dialogue_issues = [i for i in issues if i['key'] not in ('stakes', 'picture')]
    pic = picture_phrase(picture)
    if n < THRESHOLDS['min_lines']:
        verdict = f'{path.name}：台词 {n} 句，材料太少，不做统计判断{pic}。'
    elif not dialogue_issues:
        verdict = (f"{path.name}：对白连通通过——{n} 句 / {stats['speakers']} 人，最长来回 {stats['longest_exchange']} 轮、"
                   f"{int(stats['conversation_share'] * 100)}% 台词有人接"
                   + (f"，平均 {stats['mean_words']} 词/句" if stats['mean_words'] is not None else '')
                   + f"，画外 {len(stats['offscreen_lines'])} 句；人物赌注：{st}{pic}。")
    else:
        verdict = f"{path.name}：对白连通有问题；人物赌注：{st}{pic}。"
    if issues:
        listed = [i['title'] for i in issues if not i.get('compact')]  # 缺场面轨已在"画面："里
        verdict += f"问题：{'、'.join(listed)}。" if listed else ''
    shown = [i for i in issues if not i.get('compact')][:3]
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
    return head + ('\n' + m.group(0) if m else '')


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


def review_file(path, full=False, context=None, production_total=None):
    text = Path(path).read_text(encoding='utf-8')
    lines, actions = parse(text)
    names = sorted({ln['speaker'] for ln in lines})
    stats = analyse(lines, actions, names)
    ledger = ledger_text(text)
    stakes = check_stakes(stakes_card(text), lines, names)
    picture = check_picture(text, track_card(text), lines, actions, production_total)
    candidates, planted, declared = anchoring(lines, actions, context_text(context), ledger, stakes['terms'])
    stats['unanchored'] = [e['line'] for e in candidates]
    stats['planted'] = [e['line'] for e in planted]
    stats['declared'] = [e['line'] for e in declared]
    issues, signals, review = judge(lines, actions, stats, candidates, planted, declared, stakes, picture)
    dialogue_ok = not [i for i in issues if i['key'] not in ('stakes', 'picture')]
    return {
        'file': str(path), 'context': [str(c) for c in (context or [])],
        'stats': stats, 'issues': issues, 'signals': signals, 'review_needed': review,
        'anchoring': {'candidates': candidates, 'planted': planted, 'declared': declared},
        'verdict': 'insufficient' if stats['lines'] < THRESHOLDS['min_lines'] else ('issues' if issues else 'pass'),
        'checks': {'dialogue': 'insufficient' if stats['lines'] < THRESHOLDS['min_lines'] else ('pass' if dialogue_ok else 'issues'),
                   'stakes': stakes['status'], 'picture': picture['status']},
        'stakes': {k: v for k, v in stakes.items() if k != 'terms'},
        'picture': picture,
        'lines': [{k: v for k, v in ln.items() if k in ('speaker', 'text', 'words', 'clause', 'addressee', 'link_prev', 'offscreen', 'orphan', 'in_conversation', 'presupposed')} for ln in lines],
        'thresholds': THRESHOLDS,
        'text': render(Path(path), stats, issues, signals, review, full=full, stakes=stakes, picture=picture),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scenes', nargs='+')
    ap.add_argument('--json', action='store_true', help='输出 JSON（含逐句特征与阈值）')
    ap.add_argument('--full', action='store_true', help='不截到 800 字，复核清单全列')
    ap.add_argument('--context', nargs='*', default=[], help='前几场剧本页：只用来建立前文已出现的设定，不 review')
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
            results.append(review_file(p, full=args.full, context=args.context, production_total=args.production_total))
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
