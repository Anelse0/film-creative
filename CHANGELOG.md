# Changelog

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
