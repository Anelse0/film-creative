# Changelog

## 3.0.0 — 2026-09-19

直接基于 1.1.0（2026-09-17 回滚点）。版本号跳过 1.2.0–2.1.2：这些标签属于已回滚的存档线（`archive/pre-rollback-2026-09-17-main-at-v2.1.2`），本版不继承其文件（设计表、情绪资产、handoff-contract、canon_scan 等），只恢复其中用户已确认的偏好记录。

**诊断依据**：一季故事 v1 → v2 的用户反馈（空间单一、球员魅力不足、人设不讨喜、感情幼稚无事件推动）与 v2 文本本身——分集框架写成"空间 / 事件 → 选择与变化 → 结尾"的抽象陈述，充满"没有……也没有……"，中段连续多集换景不换机制；1.1.0 没有任何文件判断"概念能否持续产生事件""两线是否互改""观众为什么在乎"，对白只有诊断规则没有正向工艺，"诊断 / 单集 / 单场 / 对白"没有各自的交付范围。

- `SKILL.md`：核心判断；十条默认创作取向（任务中用户明确要求优先）；任务模式与交付范围表；S3b / S3c 读取项接新文件；硬规则 8（正文先写会发生什么，否定句留在自检）、9（反模式是信号不是判决）；快速路由三条。
- 新增 `references/story-engine.md`（§一 概念→机制三判断 · §二 两线互改 · §三 吸引 / 交集 / 代价与确认后的张力 · §四 触发链与隐瞒三问 · §五 配角与场景 · §六 观看欲望 · §七 正面写法 · §八 误用信号）。
- 新增 `references/episode-design.md`（§一 一集四件事 · §二 分集框架不像摘要 · §三 单集分场步骤 · §四 平台公式边界 · §五 诊断）。
- `stage-3b-story.md`：正文写会发生什么；四判断之外的两项引擎检查；多集行改指向 episode-design；常见失败加四行。`stage-3c-script.md` §3c.5b 任务范围提醒。`character-scene-development.md`：隐瞒 / 误会 / 退缩三问；潜台词有动机、直说有资格（Mamet 三问、Birch）。`creative-loop.md` §二 加四行诊断。`templates/story.md` 加"机制与两线"按需段。
- `preference-ledger.md`：2026-09-19 十条取向与"正文写发生了什么"；恢复 1.3.x 的三条用户已确认偏好（直给优于比喻、承上启下先于机灵、外部机制不能消失——按 09-19 表述修正）。
- `context-creativity-sources.md` §3.0.0：Parker & Stone、Mazin 403、Gilligan 2014、Scriptnotes 478、Mamet 备忘录、Tierney × 2、Birch、August 2025 微短剧、中文短剧培训文（作为不采用的对照）、郑瑞景重读；未读到 Curtis / BBC Writersroom 并如实标注。
- 测试：`test_story_workflow.py` 加新文件在场与 SKILL 接线检查；`test_routing.py` 把新文件纳入退役门禁短语扫描。
- 验证（`tests/acceptance-3.0.0/`）：六个固定任务，新旧版各在独立会话运行，盲序评审（评审者为维护 Agent，非用户）：3.0.0 胜 3（诊断 / 单集 / 一季骨架）、1.1.0 胜 1（对白）、平 2（两个过拟合检查项）。对白项复测两轮一致偏"表态"，根因是"直说也有资格"被读成可直接表态，已改措辞并把规则里取自测试原文的示例换成中性句，复跑后与旧版持平。**工程完成；效果提升为非盲呈现改善，未经用户盲选。**

## 1.1.0 — 2026-09-07

- 新增故事上下文协议：写前读取整体/本场/远处依赖，区分故事事实、人物所知与观众所知，保护后续兑现；采用后更新变化量，跨轮恢复回读原文。
- 新增创意开发操作：在已有边界内探索人物理解、关系、选择与后果，实际写出差异，按收益与修订代价选择。
- 提炼好莱坞与韩国编剧一手资料为 H1–H3 / K1–K4 七项方法，覆盖 August、Gilroy、Mazin、奉俊昊、朴赞郁、郑瑞景、李沧东；接入故事/剧本开发，记录方法适用条件和来源。
- 接入 intake、概念、故事、剧本、重写、恢复及可选场景摘记；不强制用户填表，不新增保存或确认门槛。
- 修复路由检查器错误接受 S4–S7/performance/raw；生产阶段仍可作为排除/交接信息，执行范围与独立创意 Skill 对齐。旧错误的生产执行记录现会返回错误。
- 清理悬空生产模板，修正“本场用不到就删正典”、非因果画面一律淘汰和靠拆 clip 增加总时长的冲突规则。
- 验证：60 个 unittest 与 shell 回归通过；13 个合成案例非盲文本走查。未进行独立创意盲测或长上下文效果基准，不宣称已证明创意增益。详见 `tests/acceptance-1.1.0/review.md`。

## 1.0.0 — 2026-09-07

从 [Film-Seedance-Director](https://github.com/Anelse0/Film-Seedance-Director) 2.6.0-alpha.3（commit 0436abd）拆分出的创意前端 Skill，首个独立版本。

- 范围：S1 资源读取、S2 需求识别、S3a 概念、S3b 故事、S3c 剧本、局部改写与创意评估。
- 生产后端（S4 表演外化、S5 分镜、S5b 参考资产、S6 Prompt 编译、S7 检查）拆至独立的 film-director Skill；本 Skill 中对生产文件的引用改为交接说明。
- 移除生产侧文件：stage-4/5/5b/6/7、emotion-performance 库、capabilities、camera-vocabulary、director-lenses、externalization-lexicon、production-workflow、performance/production 记录与模板、validate_prompt 及生产脚本、生产示例与测试。
- 共用文件（execution-contract、stage-1-intake、scene-parameters、causal-chain、anti-mechanical、genre-packs、project-state、script-scene 模板）按创意侧范围裁剪；genre-packs 保持与 film-director 相同内容。
- 历史版本记录（1.2.0–2.6.0-alpha.3）见源仓库 Film-Seedance-Director 的 CHANGELOG 与 tags。
