#!/usr/bin/env python3
"""Scan project files for retired canon terms after a story/character change.

Usage: canon_scan.py --ip ip.md [--deprecated 旧词,旧词2] PATH... [--json]

Terms come from a Markdown table in ip.md under a heading that contains
「正典变更」 or 「已废弃」 (first column = retired term, aliases separated by
「/」; second = replacement; a row whose third column contains 「允许保留」 or
「保留」 is skipped), plus any --deprecated terms. Every .md / .txt / .prompt.md
/ .csv / .xlsx file in PATH (files or directories, recursive) is scanned; matches
are reported as file:line (or sheet!cell) with the surrounding text. The ip.md
itself is skipped — the change table legitimately names the old term.

A match whose line/cell also carries an explanatory marker (作废 / 已删 /
已废弃 / 待重写 / 留空 / 原为 / 改为 / 不再 / 旧的 / 版本记录 …) is reported as
NOTE — the text is *talking about* the retirement, as the handoff contract
asks for in blanked-out rows — and does not count toward the exit code unless
--strict is given. --ignore REGEX drops lines/cells entirely (e.g. version logs).

Excel lock files (~$name.xlsx) are ignored; an .xlsx that cannot be read
(not a zip, truncated) is reported as SKIP and the scan continues. When two
aliases match the same line/cell and one is a substring of the other
(Preston / Preston Vane) only the longer one is reported.

Exit 1 when any HIT remains, 0 when clean. Matching is literal and
case-insensitive; it finds stale words, not stale logic — a scene can still
carry an outdated premise without using a retired word.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_lite import read_workbook, column_letter  # noqa: E402

TEXT_SUFFIXES = {".md", ".txt", ".csv", ".fountain", ".json"}
HEADING_RE = re.compile(r"^#{1,6}\s*.*(正典变更|已废弃|canon.?delta|deprecated).*$", re.I | re.M)
MENTION_RE = re.compile(r"作废|已删|已废弃|删除|待重写|留空|原为|改为|不再|旧的|旧分镜|旧稿|版本记录|变更表|canon.?delta|deprecated|retired", re.I)


def terms_from_ip(ip_path):
    text = Path(ip_path).read_text(encoding="utf-8")
    terms = {}
    for heading in HEADING_RE.finditer(text):
        rest = text[heading.end():]
        nxt = re.search(r"^#{1,6}\s", rest, re.M)
        block = rest[: nxt.start()] if nxt else rest
        rows = [l for l in block.splitlines() if l.strip().startswith("|")]
        for line in rows[2:] if len(rows) > 2 else []:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or not cells[0] or set(cells[0]) <= set("-: "):
                continue
            status = cells[2] if len(cells) > 2 else ""
            if "保留" in status:
                continue
            replacement = cells[1] if len(cells) > 1 else ""
            for alias in re.split(r"\s*/\s*|／", cells[0]):
                alias = alias.strip("`* ")
                if alias:
                    terms[alias] = replacement
    return terms


def iter_files(paths):
    for raw in paths:
        p = Path(raw)
        if p.is_dir():
            for f in sorted(p.rglob("*")):
                if f.is_file() and (f.suffix.lower() in TEXT_SUFFIXES or f.suffix.lower() == ".xlsx"):
                    if "_archive" in f.parts or ".git" in f.parts or f.name.startswith("~$"):
                        continue
                    yield f
        elif p.is_file():
            yield p


def _matches(text, terms, file, where):
    found = [t for t in terms if re.search(re.escape(t), text, re.I)]
    # An alias contained in a longer matched alias is the same drift, not a second one.
    found = [t for t in found if not any(o != t and t.lower() in o.lower() for o in found)]
    kind = "note" if MENTION_RE.search(text) else "hit"
    return [{"file": file, "where": where, "term": t, "replacement": terms[t],
             "text": text.strip().replace("\n", " ")[:120], "kind": kind} for t in found]


def scan_text(path, terms, ignore=None):
    hits = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return hits
    for no, line in enumerate(lines, 1):
        if ignore and re.search(ignore, line):
            continue
        hits.extend(_matches(line, terms, str(path), f"line {no}"))
    return hits


def scan_xlsx(path, terms, ignore=None):
    try:
        book = read_workbook(path)
    except (ValueError, KeyError, ET.ParseError) as exc:
        return [{"file": str(path), "where": "-", "term": "", "replacement": "",
                 "text": str(exc)[:120], "kind": "skip"}]
    hits = []
    for sheet, rows in book.items():
        for r, row in enumerate(rows, 1):
            for c, value in enumerate(row, 1):
                if not isinstance(value, str) or (ignore and re.search(ignore, value)):
                    continue
                hits.extend(_matches(value, terms, str(path), f"{sheet}!{column_letter(c)}{r}"))
    return hits


def scan(paths, terms, skip=(), ignore=None):
    """Return hit/note/skip records; `ignore` is matched against the full line or cell text."""
    skip = {Path(s).resolve() for s in skip}
    hits = []
    for f in iter_files(paths):
        if f.resolve() in skip:
            continue
        hits.extend(scan_xlsx(f, terms, ignore) if f.suffix.lower() == ".xlsx" else scan_text(f, terms, ignore))
    return hits


def main(argv):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("paths", nargs="+")
    parser.add_argument("--ip", help="ip.md holding the 正典变更 / 已废弃 table")
    parser.add_argument("--deprecated", default="", help="extra retired terms, comma separated")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true", help="count explanatory NOTE mentions as hits too")
    parser.add_argument("--ignore", help="regex; drop lines/cells matching it (e.g. version logs)")
    args = parser.parse_args(argv[1:])
    terms = {}
    skip = []
    if args.ip:
        try:
            terms.update(terms_from_ip(args.ip))
        except OSError as exc:
            parser.error(str(exc))
        skip.append(args.ip)
    for t in filter(None, (s.strip() for s in args.deprecated.split(","))):
        terms.setdefault(t, "")
    if not terms:
        parser.error("no retired terms: give --ip with a 正典变更/已废弃 table or --deprecated")
    hits = scan(args.paths, terms, skip, args.ignore)
    real = [h for h in hits if h["kind"] == "hit" or (args.strict and h["kind"] == "note")]
    notes = [h for h in hits if h["kind"] == "note" and not args.strict]
    skipped = [h for h in hits if h["kind"] == "skip"]
    if args.json:
        print(json.dumps({"terms": terms, "hits": real, "notes": notes, "skipped": skipped}, ensure_ascii=False, indent=2))
    else:
        print(f"== canon_scan: {len(terms)} retired term(s): {', '.join(terms)}")
        for h in real:
            repl = f" → {h['replacement']}" if h["replacement"] else ""
            print(f"HIT  {h['file']} [{h['where']}] 「{h['term']}」{repl}: {h['text']}")
        for h in notes:
            print(f"NOTE {h['file']} [{h['where']}] 「{h['term']}」 说明性提及（作废/留空/版本记录），不计入")
        for h in skipped:
            print(f"SKIP {h['file']}: 无法读取（{h['text']}），未扫描")
        print(f"== {len(real)} hit(s), {len(notes)} note(s), {len(skipped)} skipped")
    return 1 if real else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
