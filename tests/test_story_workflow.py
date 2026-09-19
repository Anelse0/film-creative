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
        self.assertIn('修订账本', self.read('templates/script-scene.md'))

    def test_story_engine_and_episode_design_present_and_wired(self):
        skill = self.read('SKILL.md')
        for ref in ('references/story-engine.md', 'references/episode-design.md'):
            self.assertTrue((ROOT / ref).exists(), ref)
            self.assertIn(ref, skill)
        for phrase in ('核心判断', '创作取向', '任务模式与交付范围', '正文先写会发生什么', '反模式是信号'):
            self.assertIn(phrase, skill)
        engine = self.read('references/story-engine.md')
        for phrase in ('因此 / 但是', '外部剧情与私人关系互相改变', '靠近要有代价', '隐瞒、误会、退缩的三问', '删掉这个配角', '观看欲望从哪里来', '先写会发生什么'):
            self.assertIn(phrase, engine)
        episode = self.read('references/episode-design.md')
        for phrase in ('承接', '进入', '兑现', '牵引', '不像摘要', '平台公式的边界'):
            self.assertIn(phrase, episode)
        # 3.0.0 wiring into existing stage files
        self.assertIn('story-engine.md', self.read('references/stage-3b-story.md'))
        self.assertIn('episode-design.md', self.read('references/stage-3b-story.md'))
        self.assertIn('story-engine.md', self.read('references/creative-loop.md'))
        self.assertIn('隐瞒、误会、退缩要有理由与代价', self.read('references/character-scene-development.md'))

    def test_route_check_is_wired_into_skill(self):
        self.assertTrue((ROOT / 'scripts/route_check.py').exists())
        self.assertIn('scripts/route_check.py', self.read('SKILL.md'))


if __name__ == '__main__':
    unittest.main()
