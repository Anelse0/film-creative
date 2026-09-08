"""film-creative 1.0.0: story-development workflow presence checks, carried over from the
source repo's 2.5.5 acceptance (Film-Seedance-Director). No creative quality is graded here."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class StoryWorkflowPresenceTests(unittest.TestCase):
    def read(self, name):
        return (ROOT / name).read_text(encoding='utf-8')

    def test_concept_protocol_has_comparison_dimensions_and_key_scene_first(self):
        text = self.read('references/concept-generation.md')
        for phrase in ('人物怎样理解处境', '人物之间有什么具体关系', '什么事发生，带来什么后果', '观众为什么愿意继续看', '关键场景先行', '熟悉题材可以写出好故事'):
            self.assertIn(phrase, text)

    def test_story_stage_is_prose_first_with_four_judgments(self):
        text = self.read('references/stage-3b-story.md')
        for phrase in ('故事正文优先', '短片可以围绕一个完整时刻成立', '不能冒充完整', '事情为什么发生', '前面的事怎样影响后面的可能性', '观众何时知道什么', '结尾为何在这个故事中成立', '不强制倒叙、三幕或最后反转'):
            self.assertIn(phrase, text)
        self.assertIn('## 故事正文', self.read('templates/story.md'))

    def test_dialogue_revision_targets_actual_cause(self):
        text = self.read('references/character-scene-development.md')
        for phrase in ('场景只为宣布主题而存在', '人物知道不该知道的信息', '每句话都精准接住上一句', '两人声音可以互换', '结尾总用金句总结', '用户锁定内容不能擅改', '现实事实需要可靠依据', '未锁定的虚构可以创造'):
            self.assertIn(phrase, text)

    def test_revision_ledger_and_stop_condition(self):
        text = self.read('references/creative-loop.md')
        for phrase in ('修订账本', '已确认内容', '暂定假设', '本轮问题', '需要保留的优点', '受影响部分', '达到目标就停'):
            self.assertIn(phrase, text)

    def test_route_check_is_wired_into_skill(self):
        self.assertTrue((ROOT / 'scripts/route_check.py').exists())
        self.assertIn('scripts/route_check.py', self.read('SKILL.md'))


if __name__ == '__main__':
    unittest.main()
