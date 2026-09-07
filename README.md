# film-creative

版本 **1.1.0**。影视创意与剧本开发 Skill：概念构思、故事发展、完整剧本与台词、人物与场景发展、局部改写与创意评估。调用：`/film-creative` 或在对话中描述任务（想故事、发展想法、写剧本、改台词）。

生产后端（表演外化、分镜、参考资产、Seedance 2.5 Prompt 编译与质量检查）由独立的 [film-director](https://github.com/Anelse0/film-director) Skill 承担。本 Skill 派生自 [Film-Seedance-Director](https://github.com/Anelse0/Film-Seedance-Director) 2.6.0-alpha.3（commit 0436abd）的创作前端。

## 一句话

从故事整体找到本场依据，在边界内发展新意，交付完整故事与场景。

## 流水线

```
S1 资源读取 → S2 需求识别 → 故事开发（S3a 概念 ↔ S3b 故事 ↔ S3c 剧本）→ 有针对性地修订 → 交接生产（film-director）
```

创作允许迭代（概念 ↔ 故事 ↔ 剧本，允许关键场景先行）。入口由创作意图与材料成熟度决定（`SKILL.md` §需求识别）。范围、自主、确认与保存统一见 `references/execution-contract.md`。默认对话交付；明确保存要求或已有项目约定才写文件。用户要故事就交故事，要剧本就交剧本；分镜与 Prompt 由 film-director 承接，不按关键词扩大范围。

## 1.1.0 更新

- 接已有故事时，开写前读取整体、当前场、远处依赖和后文边界；区分故事事实、人物所知与观众所知，采用后记录变化量，恢复时不混入否定分支。
- 创意从人物选择、关系、日常条件与后果中发展，实际比较正文收益与修改代价；不把加戏自动变成新灾难、新反派或规则例外。
- 提炼好莱坞与韩国创作者的七项方法：场景作用、行为处境、选择后果、空间因果、事件与关系共用行动、语言来源、有依据的歧义。全部注明一手出处与适用边界，不按地域套公式。
- 修复独立 Skill 的路由边界与残留生产模板；默认对话交付、已有保存约定及用户新授权仍沿用。

[审查与验证记录](tests/acceptance-1.1.0/review.md)：60 个 unittest 与 shell 回归通过，13 个合成案例非盲文本走查。**尚未做独立创意盲测，不宣称质量增益已被证明。**

## 文件地图

| 文件 | 何时读 |
|---|---|
| `SKILL.md` | 入口：路由、硬规则、输出契约、交接契约 |
| `references/execution-contract.md` | S2 唯一决策源：范围 / 自主 / 确认 / 保存 |
| `references/stage-1-intake.md` | S1 / S2：材料登记、创作意图与三轴、按材料成熟度的入口表、项目目录 |
| `references/concept-generation.md` | S3a 概念模式契约：创作判断 / 默认地图 / 入口 / 研究服务缺口 / 候选比较维度 / 关键场景先行 |
| `references/stage-3a-concept.md` | S3a 概念长什么样：素材入口 / 候选弱点 / 可选的主控句、三问与默认画面地图 / 交付格式 |
| `references/stage-3b-story.md` | S3b 故事开发：故事正文优先 / 叙事组织四判断 / 世界观与人物按需 / 温度表与场景清单按需 |
| `references/stage-3c-script.md` | S3c：多种试写入口 / 连续交流诊断 / 节拍估时 / 物件状态 / 定点重写 |
| `references/story-context.md` | 续写/改写开写前：整体/本场/远处依据、人物知识、后续边界、变化量与恢复 |
| `references/creative-search.md` | 从已有关系与选择发展新意，写实际片段，比较收益和修订代价 |
| `references/screenwriting-methods.md` | 好莱坞/韩国一手实践提炼的七项操作：按创作问题选用 |
| `references/context-creativity-sources.md` | 本版专业资料、长故事生成研究、已读范围、实现对应与局限 |
| `templates/scene-context.md` | 可选本场依据摘记；不新设审批/保存要求，不替代原文 |
| `references/story-development.md` | 试写、跨场发展与信息排序操作 |
| `references/character-scene-development.md` | S3b–S3c 共用：人物与观众责任、交流处境、声音的基础/对象/当下、分层诊断 |
| `references/dialogue-observations.md` | 语言或人物有缺口时：中文交流材料、创作者方法及迁移边界 |
| `references/dialogue-diagnostics.md` | 具体诊断困难时：局部改稿得失与反例，不是台词答案库 |
| `references/creative-loop.md` | 允许的回流、收到批评后先诊断层级、修订账本与停止条件、场景写作可选步骤 |
| `references/preference-ledger.md` | 用户确认过的偏好：喜欢哪种效果 / 在哪类作品适用 / 反例；重写前先查 |
| `references/scene-parameters.md` | 场景参数卡：六参数及其在台词 / 结构中的取值；预设只是参数组合 |
| `references/screenwriting-traditions.md` | 基于第一手编剧/导演资料，按场景问题选方法，不按地区或配额套写 |
| `references/research-to-craft.md` | 研究材料如何进入创作（缺口 → 发现 / 可信范围 / 影响的决定） |
| `references/causal-chain.md` | 剧情因果三测："每句都对但不推动"时用 |
| `references/anti-mechanical.md` | 机械感诊断：特征齐全但没有生命时用 |
| `references/genre-packs.md` | 基调为动作 / 悬疑恐怖 / UGC 广告 / 蒙太奇时叠加（生产用法交 film-director） |
| `references/project-state.md` + `scripts/project_check.py` | 已保存项目：版本、恢复、依赖失效、正典 |
| `templates/*.md` | 概念 / 故事 / 剧本页 / ip 骨架 |
| `scripts/validate_concept.py` | 概念选定落盘后跑；只查格式与完整性，不判断创意 |
| `scripts/route_check.py` | S2 结构化决策校验：仅执行 S3a–S3c/save_only；不解释自然语言，旧自由文本 CLI 返回 2 |
| `scripts/blind_eval.py` + `tests/creative-eval.md` | 旧版 / 新版盲选评测：打包、记录判定、揭晓 |
| `scripts/baseline_snapshot.py` | Git / 非 Git 版本目录的归档与完整性检查 |
| `examples/concept-worked-examples.md` | 概念协议跑出来长什么样（概念模式默认不读，禁止复用候选） |

## 常用脚本

```bash
cd <实际安装的Skill目录>
python3 scripts/validate_concept.py <01_concept.md>
python3 scripts/route_check.py --record <语义判断记录.json> --json
python3 scripts/assemble_script.py 03_script/scene-01.md 03_script/scene-02.md --output 03_script/reading.md
```

自动检查负责约束与交付完整性；创意与编剧质量由用户盲选、具体文本证据和 `references/preference-ledger.md` 判断（`scripts/blind_eval.py`，协议见 `tests/creative-eval.md`）。

## 项目目录约定

```
<workspace>/<ip-slug>/ip.md · <story-slug>/{00_brief, 01_concept, 02_story, 03_script/}
```

同一项目的 04_shots 及之后的子目录由 film-director 生成。

## 版本管理

- 语义化版本，记录在 `VERSION` 与 `CHANGELOG.md`。
- 每次改动跑 `bash tests/run_tests.sh`；GitHub Actions 在 push 与 PR 时自动跑。

## 安装

```bash
git clone https://github.com/Anelse0/film-creative.git <skills目录>/film-creative
```
