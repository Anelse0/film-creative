"""1.3.0: collaboration-contract files exist and are wired into SKILL.md (presence only)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEW_FILES = ['references/beat-to-dialogue.md', 'references/dialogue-craft.md', 'references/series-engine.md',
             'references/handoff-contract.md', 'templates/dialogue-design-sheet.md', 'scripts/canon_scan.py',
             'scripts/xlsx_lite.py']


class CollabDocsTests(unittest.TestCase):
    def test_files_exist_and_are_referenced(self):
        skill = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        for name in NEW_FILES:
            with self.subTest(file=name):
                self.assertTrue((ROOT / name).exists(), name)
                if name.startswith(('references', 'templates')) or name.endswith('canon_scan.py'):
                    self.assertIn(name, skill)

    def test_shared_files_are_identical_to_film_director_copies_when_present(self):
        sibling = ROOT.parent / 'film-director'
        if not sibling.is_dir():
            self.skipTest('sibling film-director checkout not present')
        for name in ('references/handoff-contract.md', 'scripts/xlsx_lite.py', 'scripts/ledger_view.py'):
            with self.subTest(file=name):
                self.assertEqual((ROOT / name).read_bytes(), (sibling / name).read_bytes(),
                                 f'{name} differs from the film-director copy; update both in the same change')

    def test_ip_template_has_engine_and_canon_delta_sections(self):
        text = (ROOT / 'templates/ip.md').read_text(encoding='utf-8')
        self.assertIn('## 故事引擎', text)
        self.assertIn('## 正典变更', text)
        self.assertIn('| 旧', text)

    def test_design_sheet_is_handoff_layer_not_script_body(self):
        text = (ROOT / 'templates/dialogue-design-sheet.md').read_text(encoding='utf-8')
        for col in ('目的动词', '潜台词', '说法', '听者可见反应', '递进', '收尾'):
            self.assertIn(col, text)
        self.assertIn('不进入可连续阅读的剧本正文', text)


if __name__ == '__main__':
    unittest.main()
