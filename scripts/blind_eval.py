#!/usr/bin/env python3
"""旧版 / 新版盲选评测工具（film-creative）。

子命令:
  pack    <evaldir> --pair N --topic T --a A.md --b B.md [--a-label 2.3.1] [--b-label 2.4.0]
          把两份输出随机映射成 pair-N-X.md / pair-N-Y.md，映射封在 key.json。
  present <evaldir> --pair N --order 1|2 --out FILE
          （4.0.0，LLM 双序评审用）把 X / Y 按顺序拼成"版本 A / 版本 B"交给评审：order 1 = X 在前，order 2 = Y 在前。
  record  <evaldir> --pair N --verdict X|Y|tie|both_bad --evidence "..."
          记录判定；证据必填。
  record  <evaldir> --pair N --order 1|2 --verdict A|B|tie|both_bad --evidence "..."
          （4.0.0）记录某一顺序下的判定，A / B 按该顺序映射回 X / Y。
  reveal  <evaldir>
          所有 pair 都有判定后揭晓版本，输出逐对结果与总计（Markdown）。双序 pair 两个顺序都判完才算判定；
          两个顺序结论一致才计胜负，不一致记"不一致（计平）"——评审顺序偏差的已知对策（Panickssery et al. 2024、
          Huot et al. 2024，见 references/context-creativity-sources.md §4.0.0）。

脚本只做隐藏、记录、揭晓；不评分，不生成样本。
"""
import argparse
import json
import secrets
import sys
from pathlib import Path

VERDICTS = ("X", "Y", "tie", "both_bad")
ORDER_VERDICTS = ("A", "B", "tie", "both_bad")
ORDER_MAP = {'1': {'A': 'X', 'B': 'Y'}, '2': {'A': 'Y', 'B': 'X'}}


def load(path, default):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def save(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def pack(args):
    d = Path(args.evaldir); d.mkdir(parents=True, exist_ok=True)
    key_path = d / "key.json"
    key = load(key_path, {})
    if args.pair in key:
        sys.exit(f"pair {args.pair} 已存在，换编号或删除后重打包")
    a_text = Path(args.a).read_text(encoding="utf-8")
    b_text = Path(args.b).read_text(encoding="utf-8")
    if a_text.strip() == b_text.strip():
        sys.exit("两份输出内容相同，无法盲选")
    flip = secrets.choice((True, False))
    x_text, y_text = (b_text, a_text) if flip else (a_text, b_text)
    (d / f"pair-{args.pair}-X.md").write_text(x_text, encoding="utf-8")
    (d / f"pair-{args.pair}-Y.md").write_text(y_text, encoding="utf-8")
    key[args.pair] = {"topic": args.topic, "X": args.b_label if flip else args.a_label, "Y": args.a_label if flip else args.b_label}
    save(key_path, key)
    print(f"pair {args.pair} 已打包：{d}/pair-{args.pair}-X.md, pair-{args.pair}-Y.md（评审不要打开 key.json）")


def present(args):
    d = Path(args.evaldir)
    if args.order not in ORDER_MAP:
        sys.exit("order 必须是 1 或 2")
    key = load(d / "key.json", {})
    if args.pair not in key:
        sys.exit(f"pair {args.pair} 未打包")
    m = ORDER_MAP[args.order]
    parts = []
    for slot in ('A', 'B'):
        text = (d / f"pair-{args.pair}-{m[slot]}.md").read_text(encoding="utf-8")
        parts.append(f"## 版本 {slot}\n\n{text.strip()}\n")
    Path(args.out).write_text('\n'.join(parts), encoding="utf-8")
    print(f"pair {args.pair} 顺序 {args.order} 已写到 {args.out}（只含版本 A / B，不含版本号）")


def record(args):
    d = Path(args.evaldir)
    if not args.evidence or len(args.evidence.strip()) < 6:
        sys.exit("必须附具体文本证据（指出句子、动作或候选）")
    key = load(d / "key.json", {})
    if args.pair not in key:
        sys.exit(f"pair {args.pair} 未打包")
    v_path = d / "verdicts.json"
    v = load(v_path, {})
    if args.order:
        if args.order not in ORDER_MAP:
            sys.exit("order 必须是 1 或 2")
        if args.verdict not in ORDER_VERDICTS:
            sys.exit(f"带 --order 时 verdict 必须是 {ORDER_VERDICTS}")
        mapped = ORDER_MAP[args.order].get(args.verdict, args.verdict)
        entry = v.setdefault(args.pair, {"orders": {}})
        if "orders" not in entry:
            sys.exit(f"pair {args.pair} 已按单次判定记录，不能再记双序")
        entry["orders"][args.order] = {"verdict": mapped, "evidence": args.evidence.strip()}
        save(v_path, v)
        print(f"pair {args.pair} 顺序 {args.order} 判定已记录：{args.verdict}（→ {mapped}）")
        return
    if args.verdict not in VERDICTS:
        sys.exit(f"verdict 必须是 {VERDICTS}")
    v[args.pair] = {"verdict": args.verdict, "evidence": args.evidence.strip()}
    save(v_path, v)
    print(f"pair {args.pair} 判定已记录：{args.verdict}")


def final(entry):
    """单次判定原样；双序判定两个顺序一致才算，不一致记 inconsistent。未判完返回 None。"""
    if "orders" not in entry:
        return entry["verdict"], entry["evidence"]
    o = entry["orders"]
    if set(o) != {"1", "2"}:
        return None
    a, b = o["1"]["verdict"], o["2"]["verdict"]
    ev = f"顺序1：{o['1']['evidence']} ／ 顺序2：{o['2']['evidence']}"
    return (a if a == b else "inconsistent"), ev


def reveal(args):
    d = Path(args.evaldir)
    key = load(d / "key.json", {})
    v = load(d / "verdicts.json", {})
    if not key:
        sys.exit("没有已打包的 pair")
    missing = [p for p in key if p not in v or final(v[p]) is None]
    if missing:
        sys.exit(f"还有 pair 未判定：{', '.join(missing)}；全部判定后再揭晓")
    tally = {}
    lines = ["| pair | 需求 | X = | Y = | 判定 | 胜出版本 | 证据 |", "|---|---|---|---|---|---|---|"]
    for p in sorted(key):
        k = key[p]
        verdict, evidence = final(v[p])
        winner = {"X": k["X"], "Y": k["Y"], "inconsistent": "不一致（计平）"}.get(verdict, verdict)
        tally[winner] = tally.get(winner, 0) + 1
        lines.append(f"| {p} | {k['topic']} | {k['X']} | {k['Y']} | {verdict} | {winner} | {evidence} |")
    lines.append("")
    lines.append("总计：" + " · ".join(f"{k} {n}" for k, n in sorted(tally.items())))
    out = "\n".join(lines)
    print(out)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack"); p.add_argument("evaldir"); p.add_argument("--pair", required=True); p.add_argument("--topic", required=True)
    p.add_argument("--a", required=True); p.add_argument("--b", required=True); p.add_argument("--a-label", default="old"); p.add_argument("--b-label", default="new")
    p.set_defaults(fn=pack)
    s = sub.add_parser("present"); s.add_argument("evaldir"); s.add_argument("--pair", required=True); s.add_argument("--order", required=True)
    s.add_argument("--out", required=True); s.set_defaults(fn=present)
    r = sub.add_parser("record"); r.add_argument("evaldir"); r.add_argument("--pair", required=True); r.add_argument("--verdict", required=True)
    r.add_argument("--evidence", required=True); r.add_argument("--order")
    r.set_defaults(fn=record)
    v = sub.add_parser("reveal"); v.add_argument("evaldir"); v.set_defaults(fn=reveal)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    main()
