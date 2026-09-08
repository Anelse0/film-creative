"""canon_scan: retired-term drift scan across md/xlsx project files (stdlib)."""
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from canon_scan import terms_from_ip, scan  # noqa: E402
from xlsx_lite import write_workbook  # noqa: E402

IP = """# IP
## 人物
| 角色 | 作用 |
|---|---|
| 甲 | 队长 |

## 正典变更（canon deltas）
| 旧 | 新 | 状态 | 波及 |
|---|---|---|---|
| 守门人乙 / 乙守门 | 乙＝队长 | 已废弃 | 镜37–40 |
| `丙` | 删除，功能并入乙 | 已废弃 | |
| 帽檐认人 | 靠脸认人 | 允许保留于球场段 | |

## 其他
"""


class CanonScanTests(unittest.TestCase):
    def test_terms_parse_aliases_and_skip_kept_rows(self):
        with tempfile.TemporaryDirectory() as d:
            ip = Path(d) / 'ip.md'
            ip.write_text(IP, encoding='utf-8')
            terms = terms_from_ip(ip)
        self.assertEqual(set(terms), {'守门人乙', '乙守门', '丙'})
        self.assertEqual(terms['丙'], '删除，功能并入乙')

    def test_scan_md_and_xlsx_and_skip_archive_and_ip(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            ip = root / 'ip.md'
            ip.write_text(IP, encoding='utf-8')
            (root / 'scene.md').write_text('乙守门在门口。\n丙举杯。\n干净的一行。', encoding='utf-8')
            (root / '_archive').mkdir()
            (root / '_archive' / 'old.md').write_text('守门人乙', encoding='utf-8')
            write_workbook(root / 'board.xlsx', {'分镜': [['镜号', '画面'], ['37', '守门人乙 说 Private gathering'], ['38', '无']]})
            terms = terms_from_ip(ip)
            hits = scan([root], terms, skip=[ip])
        wheres = sorted((Path(h['file']).name, h['where'], h['term']) for h in hits)
        self.assertEqual(wheres, [('board.xlsx', '分镜!B2', '守门人乙'), ('scene.md', 'line 1', '乙守门'), ('scene.md', 'line 2', '丙')])

    def test_no_hits_is_clean(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / 'a.md').write_text('全新内容', encoding='utf-8')
            self.assertEqual(scan([root], {'旧词': ''}), [])


if __name__ == '__main__':
    unittest.main()
