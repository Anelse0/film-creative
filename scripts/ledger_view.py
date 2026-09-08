#!/usr/bin/env python3
"""Print a 镜号 range of a storyboard ledger (.xlsx) as Markdown, so a scene can be read
in context before writing. Standard library only (uses xlsx_lite).

Usage: ledger_view.py LEDGER.xlsx [--from 30] [--to 40] [--sheet NAME] [--cols 镜号,入点,出点,场景,台词]
The sheet is found by a header row containing 「镜号」. Columns are matched by header
substring; omit --cols to print every non-empty column. Times given as Excel day
fractions are shown as mm:ss.
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from xlsx_lite import read_workbook  # noqa: E402


def fmt(value):
    if isinstance(value, float) and 0 <= value < 1:
        s = int(round(value * 86400))
        return f"{s // 60:02d}:{s % 60:02d}"
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return "" if value is None else str(value).replace("\n", " ").replace("|", "／")


def shot_key(text):
    m = re.match(r"\s*(\d+)", str(text))
    return int(m.group(1)) if m else None


def view(path, start=None, end=None, sheet=None, cols=None):
    book = read_workbook(path)
    for name, rows in book.items():
        if sheet and name != sheet:
            continue
        hdr = next((i for i, r in enumerate(rows[:15]) if any("镜号" in str(c) for c in r if c)), None)
        if hdr is None or any("台词号" in str(c) for c in rows[hdr] if c):
            continue
        header = [str(c) if c is not None else "" for c in rows[hdr]]
        idx = [i for i, h in enumerate(header) if h and (not cols or any(c in h for c in cols))]
        id_col = next(i for i, h in enumerate(header) if "镜号" in h)
        out = ["| " + " | ".join(header[i] for i in idx) + " |", "|" + "---|" * len(idx)]
        for r in rows[hdr + 1:]:
            k = shot_key(r[id_col]) if id_col < len(r) else None
            if k is None or (start is not None and k < start) or (end is not None and k > end):
                continue
            out.append("| " + " | ".join(fmt(r[i]) if i < len(r) else "" for i in idx) + " |")
        return f"### {name}\n" + "\n".join(out)
    raise ValueError("no sheet with a 「镜号」 header")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ledger")
    ap.add_argument("--from", dest="start", type=int)
    ap.add_argument("--to", dest="end", type=int)
    ap.add_argument("--sheet")
    ap.add_argument("--cols", help="comma-separated header substrings")
    a = ap.parse_args(argv[1:])
    try:
        print(view(a.ledger, a.start, a.end, a.sheet, a.cols.split(",") if a.cols else None))
    except (OSError, ValueError, KeyError) as exc:
        ap.error(str(exc))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
