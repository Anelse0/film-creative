#!/usr/bin/env python3
"""Assemble scene bodies in explicit order, or verify a derived reading copy."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import tempfile

START = '<!-- script-body:start -->'
END = '<!-- script-body:end -->'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def body(text):
    if START in text or END in text:
        if text.count(START) != 1 or text.count(END) != 1:
            raise ValueError('each scene needs exactly one start/end marker')
        a, b = text.index(START), text.index(END)
        if a >= b:
            raise ValueError('body markers out of order')
        result = text[a + len(START):b].strip('\r\n')
    else:
        lines = text.splitlines()
        starts = [i for i, line in enumerate(lines) if line.strip() == '## 剧本页']
        if len(starts) != 1:
            raise ValueError('no unambiguous screenplay body; add markers explicitly')
        i = starts[0] + 1
        end = next((j for j in range(i, len(lines)) if lines[j].startswith('## ')), len(lines))
        result = '\n'.join(lines[i:end]).strip()
        heading = next((line for line in lines[:i] if line.startswith('场 ')), '')
        if heading and result and result.splitlines()[0] != heading:
            result = heading + '\n\n' + result
    if not result.strip():
        raise ValueError('empty screenplay body')
    return result


def same(a, b):
    return a == b or (a.exists() and b.exists() and a.samefile(b))


def paths_for(output):
    output = Path(output).resolve()
    manifest = output.with_suffix('.sources.json')
    if output.name.endswith('.sources.json') or same(output, manifest):
        raise ValueError('output and manifest must be distinct files')
    return output, manifest


def load_manifest(manifest):
    info = json.loads(manifest.read_text(encoding='utf-8'))
    if (not isinstance(info, dict) or info.get('derived') is not True
            or info.get('schema_version', 1) not in (1, 2)
            or not isinstance(info.get('output_sha256'), str)
            or not isinstance(info.get('sources'), list) or not info['sources']):
        raise ValueError('invalid reading manifest')
    if info.get('schema_version') == 2 and info.get('path_base') != 'manifest':
        raise ValueError('unsupported manifest path base')
    for record in info['sources']:
        if (not isinstance(record, dict) or not isinstance(record.get('path'), str)
                or not record['path'] or not isinstance(record.get('sha256'), str)):
            raise ValueError('invalid source record')
        # Legacy manifests were absolute. Relative paths require a declared base.
        if info.get('schema_version', 1) == 1 and not Path(record['path']).is_absolute():
            raise ValueError('legacy source path must be absolute')
    return info


def verify(output):
    output, manifest = paths_for(output)
    info = load_manifest(manifest)
    actual = output.read_bytes()
    if digest(actual) != info['output_sha256']:
        raise ValueError('reading copy changed; reconcile edits before rebuilding')
    chunks, seen = [], []
    for record in info['sources']:
        path = (manifest.parent / record['path']).resolve()
        if same(path, output) or same(path, manifest) or any(same(path, p) for p in seen):
            raise ValueError('duplicate source or source aliases a derived file')
        seen.append(path)
        data = path.read_bytes()
        if digest(data) != record['sha256']:
            raise ValueError('source changed: ' + record['path'])
        chunks.append(body(data.decode('utf-8')))
    expected = ('\n\n'.join(chunks) + '\n').encode('utf-8')
    if actual != expected:
        raise ValueError('reading copy does not match source order and bodies')
    return info


def staged(path, data):
    """Stage bytes in the destination directory for a same-filesystem replace."""
    fd, name = tempfile.mkstemp(prefix='.' + path.name + '.', dir=str(path.parent))
    temp = Path(name)
    try:
        with os.fdopen(fd, 'wb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return temp


def write_pair(output, content, manifest, metadata):
    """Rollback ordinary replace failures; not a cross-file crash transaction."""
    temps, backups, committed = {}, {}, []
    retained = set()
    try:
        for path, data in ((output, content), (manifest, metadata)):
            temps[path] = staged(path, data)
            backups[path] = staged(path, path.read_bytes()) if path.exists() else None
        try:
            for path in (output, manifest):
                os.replace(temps[path], path)
                committed.append(path)
        except OSError as exc:
            failures = []
            for path in reversed(committed):
                try:
                    if backups[path] is None:
                        path.unlink()
                    else:
                        os.replace(backups[path], path)
                except OSError:
                    if backups[path] is not None:
                        retained.add(backups[path])
                    failures.append(str(path))
            if failures:
                raise OSError('commit and rollback failed for ' + ', '.join(failures)
                              + '; retained backups: ' + ', '.join(map(str, retained))) from exc
            raise
    finally:
        for path in list(temps.values()) + list(backups.values()):
            if path is not None and path not in retained:
                path.unlink(missing_ok=True)


def assemble(sources, output):
    sources = [Path(p).resolve() for p in sources]
    output, manifest = paths_for(output)
    if not sources:
        raise ValueError('no scenes')
    seen = []
    chunks, records = [], []
    for path in sources:
        if any(same(path, p) for p in seen) or same(path, output) or same(path, manifest):
            raise ValueError('duplicate scene or output would overwrite a source')
        seen.append(path)
        data = path.read_bytes()
        chunks.append(body(data.decode('utf-8')))
        records.append({'path': os.path.relpath(path, manifest.parent), 'sha256': digest(data)})
    # Only replace an intact, previously generated reading copy. Changed sources
    # are expected during rebuilding; edited reading copies must be reconciled.
    if output.exists() or manifest.exists():
        if not output.is_file() or not manifest.is_file():
            raise ValueError('existing output needs its original reading manifest; choose another path')
        info = load_manifest(manifest)
        if digest(output.read_bytes()) != info['output_sha256']:
            raise ValueError('reading copy changed; reconcile edits before rebuilding')
    content = ('\n\n'.join(chunks) + '\n').encode('utf-8')
    metadata = (json.dumps({'schema_version': 2, 'path_base': 'manifest',
        'derived': True, 'sources': records, 'output_sha256': digest(content)},
        ensure_ascii=False, indent=2) + '\n').encode('utf-8')
    output.parent.mkdir(parents=True, exist_ok=True)
    write_pair(output, content, manifest, metadata)
    return records


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('scenes', nargs='*', type=Path)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument('--output', type=Path)
    mode.add_argument('--verify', type=Path, metavar='READING')
    args = ap.parse_args()
    if args.verify and args.scenes:
        ap.error('--verify takes only the reading path, not scene inputs')
    try:
        if args.verify:
            verify(args.verify)
            print('OK: source hashes, reading hash and scene order match')
        else:
            assemble(args.scenes, args.output)
    except (ValueError, OSError) as exc:
        ap.error(str(exc))


if __name__ == '__main__':
    main()
