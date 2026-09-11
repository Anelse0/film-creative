# film-creative 2.0.0

独立的影视创意与剧本开发技能。入口是 `SKILL.md`；可构思、发展故事、写剧本、改台词、调整节奏，并将视听方法和表演参考转成场景。不依赖其他 film 技能或远程仓库。

方法根据具体问题选择，不要求固定三幕、双语、情绪阶梯或每集留钩。官方一手研究的实际访问范围与迁移边界见 `references/craft-evidence.md`；导演方法不是模仿预设。

25 条用户情绪原文完整保存在 `assets/emotion/`。检索：

```sh
python3 scripts/emotion_lookup.py --id 20 25
python3 scripts/emotion_lookup.py --query 内疚
python3 scripts/emotion_lookup.py --id 4 --raw
python3 scripts/emotion_lookup.py --verify
```

改编与原文分离；原库分类仅作为原始标签。日常创作不需要联网或安装额外 Python 包。

验证：`bash tests/run_tests.sh`。程序验证数据、边界、资源和项目工具；创作能力由实际正文审阅，不能用测试通过率代替。2.0.0 的场景走查见 `tests/acceptance-2.0.0/`，为本次作者自检，并非独立盲评。
