#!/usr/bin/env python3
"""Read-only version and dependency checks for an already-saved story project."""
import argparse
import hashlib
import json
from pathlib import Path


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inspect(path):
    path = Path(path).resolve()
    state = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(state, dict) or state.get('version') != 1 or not isinstance(state.get('artifacts'), dict):
        raise ValueError('version 1 and artifacts object required')
    errors, stale, current = [], set(), {}
    artifacts = state['artifacts']

    def check_file(ref, label):
        if not isinstance(ref, dict) or not isinstance(ref.get('path'), str) or not isinstance(ref.get('sha256'), str):
            errors.append(f'{label}: path/hash required'); return False
        file = (path.parent / ref['path']).resolve()
        if not file.is_file() or sha(file) != ref['sha256']:
            errors.append(f'{label}: missing or changed file'); return False
        return True

    for ident, item in artifacts.items():
        if not isinstance(item, dict):
            errors.append(f'{ident}: invalid artifact'); stale.add(ident); continue
        cur = item.get('current')
        if check_file(cur, f'{ident}/current'):
            current[ident] = cur['sha256']
        else:
            stale.add(ident)
        approved = item.get('approved')
        if approved is not None:
            if not check_file(approved, f'{ident}/approved'):
                stale.add(ident)
            if not isinstance(approved.get('evidence'), str) or not approved['evidence'].strip():
                errors.append(f'{ident}/approved: user evidence required')
            if isinstance(cur, dict) and approved.get('path') == cur.get('path'):
                errors.append(f'{ident}/approved: confirmation must point to immutable snapshot')
        for kind in ('history', 'drafts'):
            refs = item.get(kind, [])
            if not isinstance(refs, list):
                errors.append(f'{ident}/{kind}: list required'); continue
            for ref in refs:
                check_file(ref, f'{ident}/{kind}')
        deps = item.get('depends_on', {})
        if not isinstance(deps, dict):
            errors.append(f'{ident}: depends_on object required'); stale.add(ident)
    # Validate DAG independently of hashes, then propagate all stale dependencies.
    visiting, visited = set(), set()

    def visit(ident):
        if ident in visiting:
            errors.append(f'{ident}: dependency cycle'); stale.update(visiting); return
        if ident in visited or ident not in artifacts:
            return
        visiting.add(ident)
        item = artifacts[ident]
        deps = item.get('depends_on', {}) if isinstance(item, dict) else {}
        if isinstance(deps, dict):
            for dep, expected in deps.items():
                if dep not in artifacts:
                    errors.append(f'{ident}: unknown dependency {dep}'); stale.add(ident)
                elif current.get(dep) != expected:
                    stale.add(ident)
                visit(dep)
        visiting.remove(ident); visited.add(ident)
    for ident in artifacts:
        visit(ident)
    while True:
        previous = set(stale)
        for ident, item in artifacts.items():
            deps = item.get('depends_on', {}) if isinstance(item, dict) else {}
            if isinstance(deps, dict) and any(dep in stale for dep in deps):
                stale.add(ident)
        if previous == stale:
            break
    return {'errors': errors, 'stale': sorted(stale), 'current': current,
            'pending': state.get('pending', []), 'quality': 'not_evaluated'}


def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('state', type=Path)
    args=ap.parse_args()
    try:
        result=inspect(args.state)
    except (ValueError, OSError, TypeError, AttributeError) as exc:
        result={'errors':[str(exc)],'stale':[]}
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return 1 if result['errors'] or result['stale'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
