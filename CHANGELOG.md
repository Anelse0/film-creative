# Changelog

## 1.0.0 — 2026-09-07

从 [Film-Seedance-Director](https://github.com/Anelse0/Film-Seedance-Director) 2.6.0-alpha.3（commit 0436abd）拆分出的创意前端 Skill，首个独立版本。

- 范围：S1 资源读取、S2 需求识别、S3a 概念、S3b 故事、S3c 剧本、局部改写与创意评估。
- 生产后端（S4 表演外化、S5 分镜、S5b 参考资产、S6 Prompt 编译、S7 检查）拆至独立的 film-director Skill；本 Skill 中对生产文件的引用改为交接说明。
- 移除生产侧文件：stage-4/5/5b/6/7、emotion-performance 库、capabilities、camera-vocabulary、director-lenses、externalization-lexicon、production-workflow、performance/production 记录与模板、validate_prompt 及生产脚本、生产示例与测试。
- 共用文件（execution-contract、stage-1-intake、scene-parameters、causal-chain、anti-mechanical、genre-packs、project-state、script-scene 模板）按创意侧范围裁剪；genre-packs 保持与 film-director 相同内容。
- 历史版本记录（1.2.0–2.6.0-alpha.3）见源仓库 Film-Seedance-Director 的 CHANGELOG 与 tags。
