#!/usr/bin/env python3
"""出稿后的剧本对白 review（film-creative 3.3.0）。

用法:
  review_script.py 03_script/scene-01.md [scene-02.md ...] [--json] [--full]

读 `templates/script-scene.md` 格式的剧本页（`<!-- script-body:start/end -->` 之间；
台词块为 `**NAME**` 或独立一行的角色名，下一行台词；括号行是表演/声音提示），
只做可量化的部分：收件人链、来回（exchange）、句长分布、短句占比、连续无人接的句子、
主谓宾完整度、画外标注、每句换人（一句一镜代理量）。语义判断不冒充已判定，
列为"需模型复核"的证据清单。阈值全部是 `[推论]`（按 THE ORDER EP02 场 1 v1/v3 校准），
在 THRESHOLDS 里改。每条判断引用的一手来源见 references/dialogue-review-sources.md（S1–S9）。

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


# ---- 判断 --------------------------------------------------------------------
def quote(ln):
    return f"{ln['speaker']}「{ln['text']}」"


def judge(lines, actions, stats):
    """返回 issues（问题）、signals（信号，不判定）、review_needed（需模型复核）。"""
    T = THRESHOLDS
    issues, signals, review = [], [], []
    n = stats['lines']
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
            'why': '每句都在对谁说、下一句接不接住，是会话成立的最小条件；观众听到的是各丢一句，没人对着谁说。',
            'sources': ['S1', 'S5'],
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
        }
        if len(off) >= 2 and issues:
            # 与来回问题同根因（没人对着谁说），合并进第一条，不另立
            issues[0]['evidence'] += f'；其中 {len(off)} 句标为画外（{ev}）'
            issues[0]['sources'] = sorted(set(issues[0]['sources']) | {'S9'})
        else:
            issues.append(item)
    elif no_pair or weak_link:
        signals.append(f"两人来回最长 {stats['longest_exchange']} 轮、有人接的台词 {int(stats['conversation_share'] * 100)}%：多人场可以成立，读一遍确认谁在回应谁。")
    # 信号（不判定）
    if stats['questions']:
        signals.append(f"问句 {stats['questions']} 个，被下一位接住 {stats['questions_answered']} 个。")
    else:
        signals.append('全场没有一个问句。')
    signals.append(f"犹豫 / 打断 / 口头填充标记 {stats['hesitation_marks']} 句（有无都不判错）。")
    # 需模型复核
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


SOURCE_LEGEND = '来源编号 S1–S9 见 references/dialogue-review-sources.md'


def _count(text):
    return len(re.sub(r'\s', '', text))


def render(path, stats, issues, signals, review, full=False, limit=800):
    """一句总判断 + ≤3 个问题 + 信号 + 需模型复核 + 交接提示。默认 ≤ limit 字（不计空白）：超出先减复核条目，再减信号。"""
    n = stats['lines']
    if n < THRESHOLDS['min_lines']:
        verdict = f'{path.name}：台词 {n} 句，材料太少，不做统计判断。'
    elif not issues:
        verdict = (f"{path.name}：通过——{n} 句 / {stats['speakers']} 人，最长来回 {stats['longest_exchange']} 轮、"
                   f"{int(stats['conversation_share'] * 100)}% 台词有人接"
                   + (f"，平均 {stats['mean_words']} 词/句" if stats['mean_words'] is not None else '')
                   + f"，画外 {len(stats['offscreen_lines'])} 句。")
    else:
        verdict = f"{path.name}：有问题——{'、'.join(i['title'] for i in issues)}。"
    head = [verdict] + [f"{i}. {it['title']}：{it['evidence']}。{it['why']}（{', '.join(it['sources'])}）" for i, it in enumerate(issues[:3], 1)]
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
        else:
            return text


def review_file(path, full=False):
    text = Path(path).read_text(encoding='utf-8')
    lines, actions = parse(text)
    names = sorted({ln['speaker'] for ln in lines})
    stats = analyse(lines, actions, names)
    issues, signals, review = judge(lines, actions, stats)
    return {
        'file': str(path), 'stats': stats, 'issues': issues, 'signals': signals, 'review_needed': review,
        'verdict': 'insufficient' if stats['lines'] < THRESHOLDS['min_lines'] else ('issues' if issues else 'pass'),
        'lines': [{k: v for k, v in ln.items() if k in ('speaker', 'text', 'words', 'clause', 'addressee', 'link_prev', 'offscreen', 'orphan', 'in_conversation')} for ln in lines],
        'thresholds': THRESHOLDS,
        'text': render(Path(path), stats, issues, signals, review, full=full),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scenes', nargs='+')
    ap.add_argument('--json', action='store_true', help='输出 JSON（含逐句特征与阈值）')
    ap.add_argument('--full', action='store_true', help='不截到 800 字，复核清单全列')
    args = ap.parse_args(argv)
    results = []
    for p in args.scenes:
        try:
            results.append(review_file(p, full=args.full))
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
