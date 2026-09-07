"""2.5.5 P0: routing invariance under paraphrase, and no leftover creative gates in the creative-layer docs."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import route_check  # noqa: E402

CREATIVE_DOCS = [
    'SKILL.md', 'references/stage-1-intake.md', 'references/stage-3a-concept.md', 'references/stage-3b-story.md',
    'references/stage-3c-script.md', 'references/concept-generation.md', 'references/character-scene-development.md',
    'references/creative-loop.md', 'references/causal-chain.md', 'references/anti-mechanical.md',
    'references/research-to-craft.md', 'references/screenwriting-traditions.md', 'references/scene-parameters.md',
    'templates/concept.md', 'templates/story.md', 'templates/script-scene.md',
]
# Phrases that turned methods into gates in ≤ 2.5.0. Any reappearance is a regression.
RETIRED_GATES = [
    '没有概念卡，不进 S3b', '必停', '写不出就换', '写不出差异的候选换掉', '字段固定', '出现即需要一行理由',
    '没有物件、没有走位', '阻力必须让人物付出', '答不出的回到候选', '5–10 个答案', '通常 2–4 个',
    '可拍——物件 + 动作 + 光', '差异必须在', '方案必须能指回项目主控句', '固定三个',
]


class CreativeGateRegressionTests(unittest.TestCase):
    def test_no_retired_gate_phrases_in_creative_docs(self):
        for name in CREATIVE_DOCS:
            text = (ROOT / name).read_text(encoding='utf-8')
            for phrase in RETIRED_GATES:
                with self.subTest(doc=name, phrase=phrase):
                    self.assertNotIn(phrase, text)

    def test_skill_routing_names_the_five_intents_and_three_axes(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        for word in ('想故事', '发展已有想法', '写完整剧本', '局部改写', '进入生产', '材料成熟度', '自主执行', '用户确认', '文件保存'):
            self.assertIn(word, text)
        self.assertIn('有台词不等于剧本已完成', text.replace('文本里有台词不等于剧本已完成', '有台词不等于剧本已完成'))

    def test_intake_entry_is_by_maturity(self):
        text = (ROOT / 'references/stage-1-intake.md').read_text(encoding='utf-8')
        self.assertIn('按材料成熟度，不按表面形式', text)
        self.assertIn('台词不等于剧本已完成', text)

    def test_skill_links_resolve(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        for ref in set(re.findall(r'`((?:references|templates|scripts|examples)/[^`]+)`', text)):
            self.assertTrue((ROOT / ref).exists(), ref)


if __name__ == '__main__':
    unittest.main()
