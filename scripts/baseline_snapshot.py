#!/usr/bin/env python3
"""Create/verify a portable skill snapshot; a checksum is integrity, not authorship."""
import argparse
import hashlib
import json
import shutil
from pathlib import Path

IGNORED = {'.git', '__pycache__', '.DS_Store'}
MANIFEST = 'baseline-manifest.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*'))
            if p.is_file() and not any(part in IGNORED for part in p.relative_to(root).parts)
            and p.name != MANIFEST}


def create(source, destination):
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists() or destination == source or source in destination.parents:
        raise ValueError('destination must be new and outside source')
    if not (source/'SKILL.md').is_file() or not (source/'VERSION').is_file():
        raise ValueError('source must contain SKILL.md and VERSION')
    files = inventory(source)
    destination.mkdir(parents=True)
    for name in files:
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(source/name,target)
    manifest={'version':1,'skill_version':(source/'VERSION').read_text().strip(),'files':files}
    target=destination/MANIFEST
    target.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    result=verify(destination)
    if result['errors']:
        raise ValueError('source changed during snapshot; snapshot is invalid')
    return {'manifest_sha256':digest(target),'skill_version':manifest['skill_version']}


def verify(root, expected=None):
    root=Path(root).resolve(); path=root/MANIFEST
    manifest=json.loads(path.read_text())
    if manifest.get('version') != 1 or not isinstance(manifest.get('files'),dict):
        raise ValueError('invalid manifest')
    actual=inventory(root); errors=[]
    if expected and digest(path)!=expected:
        errors.append('manifest differs from independently recorded digest')
    for name in sorted(set(actual)|set(manifest['files'])):
        if actual.get(name)!=manifest['files'].get(name):
            errors.append(f'changed/missing/extra: {name}')
    return {'errors':errors,'provenance':'external_digest_checked' if expected else 'internal_integrity_only'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='cmd',required=True)
    c=sub.add_parser('create');c.add_argument('source');c.add_argument('destination')
    v=sub.add_parser('verify');v.add_argument('root');v.add_argument('--manifest-sha256')
    args=ap.parse_args()
    try:
        result=create(args.source,args.destination) if args.cmd=='create' else verify(args.root,args.manifest_sha256)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        result={'errors':[str(exc)]}
    print(json.dumps(result,ensure_ascii=False,indent=2));return 1 if result.get('errors') else 0


if __name__=='__main__':
    raise SystemExit(main())
