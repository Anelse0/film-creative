#!/usr/bin/env python3
"""Assemble a read-only derived screenplay in explicit scene order; never rewrite sources."""
import argparse
import hashlib
import json
from pathlib import Path

START = '<!-- script-body:start -->'
END = '<!-- script-body:end -->'


def body(text):
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError('each scene needs exactly one start/end marker')
        a, b = text.index(START), text.index(END)
        if a >= b:
            raise ValueError('body markers out of order')
        result = text[a + len(START):b].strip()
    else:
        # Legacy template: preserve prose, add its existing scene heading if external.
        lines = text.splitlines()
        starts = [i for i, line in enumerate(lines) if line.strip() == '## 剧本页']
        if len(starts) != 1:
            raise ValueError('no unambiguous screenplay body; add markers explicitly')
        i = starts[0] + 1
        end = next((j for j in range(i, len(lines)) if lines[j].startswith('## ')), len(lines))
        result = '\n'.join(lines[i:end]).strip()
        heading = next((line for line in lines[:i] if line.startswith('场 ')), '')
        if heading:
            result = heading + '\n\n' + result
    if not result:
        raise ValueError('empty screenplay body')
    return result


def assemble(sources, output):
    sources = [Path(p).resolve() for p in sources]
    output = Path(output).resolve()
    manifest = output.with_suffix('.sources.json')
    if len(set(sources)) != len(sources) or output in sources or manifest in sources:
        raise ValueError('duplicate scene or output would overwrite a source')
    chunks, records = [], []
    for path in sources:
        data = path.read_bytes()
        chunks.append(body(data.decode('utf-8')))
        records.append({'path': str(path), 'sha256': hashlib.sha256(data).hexdigest()})
    if not chunks:
        raise ValueError('no scenes')
    text = '\n\n'.join(chunks) + '\n'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding='utf-8')
    manifest.write_text(json.dumps({'derived': True, 'sources': records,
        'output_sha256': hashlib.sha256(text.encode()).hexdigest()}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenes', nargs='+', type=Path)
    ap.add_argument('--output', required=True, type=Path)
    args = ap.parse_args()
    try:
        assemble(args.scenes, args.output)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
