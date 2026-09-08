# Changelog

## 1.3.0 — 2026-09-08

面向两天实际协作里反复出现的否决（"没有交代叙事、承上启下""太牵强、没有美剧戏剧魅力""台词没逻辑""不要说钥匙这种不知道是什么意思""缺少会长宣布赛事的戏份""需要每句台词对应的设计、情绪、语气""3.8 不是让你根据最新情况更新过一版本"）建立可执行路径与工具；同时修复 1.2.0 与 film-director 1.1.0 之间断掉的接口（创作侧不再逐句给说法，生产侧 W20 却需要〔说法〕〔情绪〕）。

- **节拍草稿 → 台词** `references/beat-to-dialogue.md`：中文节拍草稿要目标语言台词的默认路径。两行承接（上一场留下什么 / 本场交给下一场什么）；逐节拍"说者→听者 · 目的动词 · 听者接住什么 · 局面变了什么"；意图锁与台词锁分开；目标语言先写再中文对照；长发言写 3–7 步情绪阶梯；收尾句；一分钟自检；修订给整场全文。
- **台词工艺** `references/dialogue-craft.md`：逐句可检规则与"逐句检查"清单，每条带一手出处（Mamet / Sorkin / McKee / Scriptnotes / 编剧访谈 / 短剧行业资料等，见文内）；覆盖潜台词与直白、一句一个动作、比喻落地测试（用户否决过的"钥匙 / 名字敲门 / 钱比建筑老"型）、声音区分、用冲突交代世界规则、美式青春剧语域、竖屏短剧密度、中文设计→英文台词的双语坑。
- **系列引擎** `references/series-engine.md`：先导片必须立起可重复的冲突机器；每场戏"引擎在场吗"三态判断（碰到 / 仅私人线（有意）/ 两线相交）；一个事件同时支付两条线；宣布 / 候选不揭结果；人物角色改变时的波及处理。`templates/ip.md` 新增「故事引擎」与「正典变更（canon deltas）」两节。
- **协作契约** `references/handoff-contract.md`（与 film-director 1.3.0 同文）：交接物表、账本模式列所有权、正典变更五步协议、台词预算口径（英语 2.5 词/s、对白 ≤2/3 clip）、交付默认。新增 `templates/dialogue-design-sheet.md`（台词设计表：交接层材料，不进可连续阅读的剧本正文，与 1.2.0 的"正文先行"一致）。
- **工具** `scripts/canon_scan.py` + `scripts/xlsx_lite.py`（stdlib）：读取 `ip.md` 正典变更 / 已废弃表的旧词（别名 / 分隔，含"保留"的行跳过）与 `--deprecated`，扫描 md / txt / csv / fountain / json / xlsx（跳过 `_archive/`、`.git/` 与 ip.md 自身），按 file:line 或 sheet!cell 报告，命中即非零退出。只找旧词，不判断旧逻辑。
- `SKILL.md`：阅读指引加节拍草稿 / 系列 / 协作三条；意图表加"节拍草稿 → 台词"；项目目录加账本模式与 canon_scan；交接契约加台词设计表与台词预算；硬规则 8（每场接引擎）、9（改正典就扫漂移）；快速路由加四条。`stage-3c-script.md` §3c.5 接入新路径，"关键句说明"改为"关键句说明与台词设计表"。
- `references/preference-ledger.md`：记入 2026-09-07/08 用户确认的五条偏好（直给优于比喻；对白场交接附说法 / 递进 / 收尾；承上启下先于机灵；引擎优先于私人线；引荐先介绍再特写）。
- 测试：`tests/test_canon_scan.py`（3）、`tests/test_collab_docs.py`（新文件在场与 SKILL 接线）；`run_tests.sh` 加 canon_scan 夹具。创意质量仍未做独立盲测；本版只声称路径、契约与工具落地。

## 1.2.0 — 2026-09-08

- 新增对白生成与修订方法：从交流需要、人物语言经历及听者接收出发，写连续片段再定点改；保留直接表达、完整长句、喜剧与风格化声音。
- 研究 Scriptnotes 609、郑瑞景一手访谈与 Fountain 官方语法，区分来源发现和 Skill 的方法设计；新增成功后的后果与群像价值选择入口。
- 整体清理阶段冲突：素材观察与虚构分开，取消主控句字数配额、镜头套路黑名单、逐句四件套和固定交付前账本；不在故事终点强加下一阶段确认。
- 新增统一成果格式说明，精简概念/故事/场景模板，Markdown 人物与台词不再用代码缩进；提供按需使用的 Fountain 模板，未实现格式自动转换或 PDF 排版。
- 汇编器新增 --verify、可迁移的相对来源清单；校验源稿/阅读版/顺序，保护源文件与人工改动，修复旧格式重复场头与空正文误通过。
- 写入先暂存，常规失败回滚；回滚失败保留恢复备份。双文件写入不保证崩溃或并发事务性；旧绝对路径清单与正文标记继续支持。
- 验证：73 个 unittest 与 shell 回归通过；8 个合成案例非盲走查与实际多场汇编。新增 13 个汇编回归测试；移除一条强制模板携带账本的过时断言。未完成独立创意效果基准。

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
