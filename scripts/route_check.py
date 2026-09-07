#!/usr/bin/env python3
"""Validate interpreted execution records, never keyword-classify natural language.
Usage: route_check.py --record route.json [--json]
Exit 0 = consistent; 1 = invalid; 2 = raw input needs semantic interpretation.
"""
import argparse
import json
from pathlib import Path

STAGES = ['S3a', 'S3b', 'S3c', 'S4', 'S5', 'S5b', 'S6', 'S7']
TARGETS = STAGES + ['performance', 'raw', 'save_only']


def validate(record):
    errors = []
    if not isinstance(record, dict) or type(record.get('version')) is not int or record['version'] != 1:
        return {'errors': ['R01 record version must be 1'], 'semantic_match': 'not_verified'}
    req = record.get('request')
    history = record.get('history', {})
    conf = record.get('confirmation', {'confirmed': False, 'evidence': ''})
    if not all(isinstance(x, dict) for x in (req, history, conf)):
        return {'errors': ['R01 request/history/confirmation must be objects'], 'semantic_match': 'not_verified'}
    if not isinstance(record.get('source'), str) or not record['source'].strip():
        errors.append('R01 original source required')
    target, entry = req.get('target'), req.get('entry')
    if target not in TARGETS or entry not in TARGETS:
        errors.append('R02 unknown target/entry')
    excluded, plan = req.get('excluded', []), record.get('planned_stages')
    if not isinstance(excluded, list) or any(s not in TARGETS for s in excluded):
        errors.append('R02 invalid exclusions'); excluded = []
    if not isinstance(plan, list) or any(s not in TARGETS for s in plan):
        errors.append('R03 invalid plan'); plan = []
    if any(s in excluded for s in plan) or target in excluded:
        errors.append('R03 plan/target enters excluded stage')
    if target == 'save_only':
        if plan or entry != 'save_only':
            errors.append('R03 save_only must not start creative work')
    elif target in STAGES and entry in STAGES:
        indexes = [STAGES.index(s) for s in plan if s in STAGES]
        if (not plan or plan[0] != entry or plan[-1] != target or len(indexes) != len(plan)
                or indexes != sorted(set(indexes))
                or any(i < STAGES.index(entry) or i > STAGES.index(target) for i in indexes)):
            errors.append('R03 plan must run in order from entry to target only')
    elif target in ('performance', 'raw'):
        if entry != target or plan != [target]:
            errors.append('R03 independent performance/raw route required')
    else:
        errors.append('R03 incompatible entry and target')
    save, policy = req.get('save', 'unspecified'), history.get('save_policy', 'on_request')
    autonomy, prior = req.get('autonomy', 'unspecified'), history.get('autonomy', 'guided')
    if save not in ('yes', 'no', 'unspecified') or policy not in ('never', 'on_request', 'after_confirmation', 'always'):
        errors.append('R04 unknown saving directive')
    if autonomy not in ('guided', 'autonomous', 'unspecified') or prior not in ('guided', 'autonomous'):
        errors.append('R04 unknown autonomy')
    confirmed = conf.get('confirmed', False)
    if type(confirmed) is not bool:
        errors.append('R05 confirmed must be boolean')
    if confirmed and (not isinstance(conf.get('evidence'), str) or not conf['evidence'].strip()):
        errors.append('R05 attributable confirmation evidence required')
    write = save == 'yes' or (save == 'unspecified' and (policy == 'always' or (policy == 'after_confirmation' and confirmed is True)))
    if target == 'save_only' and not write:
        errors.append('R04 save_only needs saving authorization')
    units = req.get('units', {})
    if not isinstance(units, dict) or any(k not in ('scenes', 'shots', 'clips') for k in units):
        errors.append('R06 unknown unit'); units = {}
    if any(v is not None and (type(v) is not int or v < 1) for v in units.values()):
        errors.append('R06 units must be positive integers or null')
    locks = record.get('hard_locks', [])
    if not isinstance(locks, list) or any(not isinstance(s, str) or not s.strip() for s in locks):
        errors.append('R05 hard locks must be concrete strings')
    decision = {'target': target, 'write_files': write, 'autonomy': prior if autonomy == 'unspecified' else autonomy,
                'confirmed': confirmed is True, 'units': units}
    if 'decision' in record and record['decision'] != decision:
        errors.append('R07 decision contradicts explicit directives/history')
    return {'errors': errors, 'decision': decision, 'semantic_match': 'not_verified'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path)
    parser.add_argument('--json', action='store_true')
    args, extra = parser.parse_known_args()
    if not args.record or extra:
        print('需要先结合原文与历史做语义理解，再用 --record 校验；不再按关键词猜测范围或保存。')
        return 2
    try:
        result = validate(json.loads(args.record.read_text(encoding='utf-8')))
    except (ValueError, OSError, TypeError) as exc:
        result = {'errors': [f'R01 {exc}'], 'semantic_match': 'not_verified'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result['errors'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
