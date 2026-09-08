import sys, tempfile, unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from xlsx_lite import write_workbook  # noqa: E402
from ledger_view import view  # noqa: E402


class LedgerViewTests(unittest.TestCase):
    def test_range_and_columns(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'l.xlsx'
            write_workbook(p, {'分镜总表': [['t'], [], ['镜号', '入点', '出点', '台词'],
                                          ['01', 0, 3 / 86400, 'A "Hi."'], ['02', 3 / 86400, 8 / 86400, '无台词'], ['03', 8 / 86400, 12 / 86400, 'B "Go."']],
                               '台词与表演': [['台词号', '镜号']]})
            md = view(p, 2, 3, cols=['镜号', '出点', '台词'])
        self.assertIn('| 02 | 00:08 | 无台词 |', md)
        self.assertIn('| 03 | 00:12 | B "Go." |', md)
        self.assertNotIn('| 01 |', md)
        self.assertNotIn('入点', md)


if __name__ == '__main__':
    unittest.main()
