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
            write_workbook(p, {'分镜总表': [['t'], [], ['镜号', '入点', '出点', '台词', '词/秒'],
                                          ['01', 0, 3 / 86400, 'A "Hi."', 0.5], ['02', 3 / 86400, 8 / 86400, '无台词', 2.4], ['03', 8 / 86400, 12 / 86400, 'B "Go."', 0.75]],
                               '台词与表演': [['台词号', '镜号']]})
            md = view(p, 2, 3, cols=['镜号', '出点', '台词'])
            full = view(p)
        self.assertIn('| 02 | 00:08 | 无台词 |', md)
        self.assertIn('| 03 | 00:12 | B "Go." |', md)
        self.assertNotIn('| 01 |', md)
        self.assertNotIn('入点', md)
        # Only time columns are formatted as mm:ss; a 词/秒 fraction stays a number.
        self.assertIn('| 0.5 |', full)
        self.assertNotIn('720:00', full)


if __name__ == '__main__':
    unittest.main()
