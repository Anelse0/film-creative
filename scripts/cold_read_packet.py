#!/usr/bin/env python3
"""冷读材料包：只含观众看得到的正文，交给新上下文的子代理评审（film-creative 4.0.0，可选步骤）。

用法:
  cold_read_packet.py 03_script/scene-03.md [--context scene-01.md scene-02.md] [--out packet.md]

输出一份 Markdown：固定的评审指令 + 前几场正文（按给定顺序）+ 本场正文 + 本场台词编号表。
只取 `<!-- script-body:start/end -->` 之间的正文（旧稿回退到"## 剧本页"一节）；设计卡、事件轨、
删除测试、修订账本与任何作者说明都不进材料包——冷读的意义就是评审者看不到作者的理由。
不评审、不改稿；零外部依赖。退出码：0 = 已生成，2 = 输入无法解析。
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from assemble_script import body  # noqa: E402
from review_script import parse  # noqa: E402

INSTRUCTIONS = """# 冷读材料包

你是第一次看这部剧的观众，同时是一位严格的剧本评审。你只知道下面给出的正文：前几场是观众已经看过的，
"本场"是待评的一场。不要读取任何其他文件，不要猜作者的意图，不要改写，不要写新台词——只标注。

请按下面的格式输出（中文说明，台词保持原文）：

1. 逐句标注（按"本场台词编号表"的编号）：`#n 说话人：原句 —— 标签（依据）`
   标签只取一个最主要的：
   - 新：观众第一次从这句得到的信息、要求或拒绝、关系变化、笑点或性格
   - 观众已知：前几场或本场前面已经说过、演过、画面上写着的（写出处：哪一场的哪句或哪个画面）
   - 递话：问句的答案下一句就给，问句本身不带说话人的立场，只是把话递给对方
   - 确认或接话：Okay / Right / I know 一类，或把对方的话换个说法再说一遍
   - 流程交代：日期、手续、安排、规则，观众不需要知道或已经知道
   - 把节拍说出口：人物替作者说出这场的意思或自己的心理
   - 陈词：套话、口号、谁都会说的漂亮话
2. 本场转折：一句话写"谁以为会怎样 → 实际怎样"；没有就写"无"。
3. 推动者：谁在出招（想从谁那里拿到什么、用什么办法），谁只在接收。
4. 静音测试：关掉声音，只看动作和画面，能不能看懂谁想要什么、谁赢了或输了；靠的是哪个动作。
5. 最想快进的地方：哪几句、哪段动作，为什么。
6. 一句总评：这场值不值得看，最该先改的一件事。

判断标准：观众听过一次的，不需要听第二次；简单的事说一两句就够；人物为了让观众听到信息而装糊涂追问，是在削弱人物。
回扣（有意重复并产生新意思）、讨价还价、调情可以来回很多轮——前提是每一回合有人的立场或压力在变。
"""


def scene_body(path):
    text = Path(path).read_text(encoding='utf-8')
    return text, body(text)


def packet(scene, context=()):
    parts = [INSTRUCTIONS]
    if context:
        parts.append('## 观众已经看过的前几场（按顺序）\n')
        for p in context:
            _, b = scene_body(p)
            parts.append(f'### {Path(p).stem}\n\n{b.strip()}\n')
    text, b = scene_body(scene)
    parts.append(f'## 本场（待评）：{Path(scene).stem}\n\n{b.strip()}\n')
    lines, _ = parse(text)
    if lines:
        parts.append('## 本场台词编号表\n')
        parts.extend(f"#{i} {ln['speaker']}：{ln['text']}" for i, ln in enumerate(lines, 1))
        parts.append('')
    return '\n'.join(parts)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('scene', help='本场剧本页')
    ap.add_argument('--context', nargs='*', default=[], help='前几场剧本页（按播出顺序）')
    ap.add_argument('--out', help='写到文件；不给则打印')
    args = ap.parse_args(argv)
    try:
        out = packet(args.scene, args.context)
    except (ValueError, OSError) as e:
        print(f'无法生成材料包：{e}', file=sys.stderr)
        return 2
    if args.out:
        Path(args.out).write_text(out, encoding='utf-8')
        print(f'材料包已写到 {args.out}（只含正文；把这个路径交给新上下文的子代理）')
    else:
        print(out)
    return 0


if __name__ == '__main__':
    sys.exit(main())
