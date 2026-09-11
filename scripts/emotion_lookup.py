#!/usr/bin/env python3
"""Retrieve immutable user references; never transform original prompt text."""
import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_library(root=ROOT):
    raw = json.loads((root / 'assets/emotion/prompts.json').read_text(encoding='utf-8'))
    notes = json.loads((root / 'references/emotion-notes.json').read_text(encoding='utf-8'))
    return raw, {x['id']: x for x in notes['entries']}

def verify(root=ROOT):
    errors = []
    folder = root / 'assets/emotion'
    manifest = json.loads((folder / 'provenance.json').read_text(encoding='utf-8'))
    for name in ('prompts.json', 'mood_prompt.md'):
        if hashlib.sha256((folder / name).read_bytes()).hexdigest() != manifest['files'][name]['sha256']:
            errors.append(f'{name}: checksum mismatch')
    raw, notes = load_library(root)
    if len(raw) != 25 or [x['id'] for x in raw] != list(range(1, 26)):
        errors.append('original IDs must be exactly 1..25 in source order')
    note_entries = json.loads((root / 'references/emotion-notes.json').read_text(encoding='utf-8'))['entries']
    if len(note_entries) != 25 or set(notes) != set(range(1, 26)):
        errors.append('derived notes must cover exactly the original 25 IDs')
    md = (folder / 'mood_prompt.md').read_text(encoding='utf-8')
    sections = re.findall(r'^## (\d+)\. ([^\n]+)\n(.*?)(?=^## |\Z)', md, re.M | re.S)
    if len(sections) != 25:
        errors.append('Markdown must contain exactly 25 sections')
    expected_keys = {'id','name','family','intensity','direction','prompt'}
    for index, record in enumerate(raw):
        if set(record) != expected_keys or any(not isinstance(record[k], str) or not record[k] for k in expected_keys - {'id'}):
            errors.append(f'ID {record.get("id")}: invalid original fields')
        if index >= len(sections):
            continue
        ident, name, body = sections[index]
        fields = dict(re.findall(r'^- (Family|Intensity|Direction|Prompt): (.*)$', body, re.M))
        reconstructed = {'id':int(ident),'name':name, **{k.lower():v for k,v in fields.items()}}
        if reconstructed != record:
            errors.append(f'ID {record["id"]}: JSON/Markdown content differs')
    return errors

def select(raw, notes, ids=None, query=None, family=None):
    if ids:
        wanted = set(ids)
        unknown = wanted - {r['id'] for r in raw}
        if unknown:
            raise ValueError('Unknown emotion ID(s): ' + ', '.join(map(str, sorted(unknown))))
    else:
        wanted = None
    selected = []
    for r in raw:
        if wanted is not None and r['id'] not in wanted:
            continue
        if family and r['family'].casefold() != family.casefold():
            continue
        searchable = json.dumps(r, ensure_ascii=False) + ' ' + json.dumps(notes[r['id']], ensure_ascii=False)
        if query and query.casefold() not in searchable.casefold():
            continue
        selected.append(r)
    return selected

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--id',type=int,nargs='+')
    parser.add_argument('--query')
    parser.add_argument('--family')
    parser.add_argument('--raw',action='store_true')
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args(argv)
    if not (args.verify or args.id or args.query or args.family):
        parser.error('choose --id, --query, --family or --verify')
    try:
        errors=verify()
        if errors:
            print(json.dumps({'ok':False,'errors':errors},ensure_ascii=False,indent=2))
            return 1
        if args.verify:
            print(json.dumps({'ok':True,'records':25,'checks':['sha256','json_markdown_equivalence','derived_note_coverage']}))
            return 0
        raw,notes=load_library()
        found=select(raw,notes,args.id,args.query,args.family)
        if args.raw:
            output=found
        else:
            output={'matches':[{'original':r,'derived_notes':notes[r['id']]} for r in found],
                    'notice':'Derived notes are creative options, not original text or psychological evidence.'}
        print(json.dumps(output,ensure_ascii=False,indent=2))
        if not found:
            print('No matching emotion reference; no substitute selected.',file=sys.stderr)
            return 3
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'Error: {exc}',file=sys.stderr)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
