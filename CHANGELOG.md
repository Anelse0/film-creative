# Changelog

## 2.1.1 — 2026-09-15

设计表生产版补两条：**抽取顺序**（先按 `dialogue-design.md` 把交流写活成场景稿，再逐字抽表；表是交接物不是生成方法）与**生动自查**行（咬对方刚说的词 / 用当场处境 / 结巴带信息 / 让预期回应落不了地，写明用在哪几句，没用写"无"及理由；张力六源仍在 `stage-3c-script.md`）。触发：同日一张生产版设计表先画表后填句，每句合规但句与句不推，用户对照同项目金样判为不够生动。SKILL 与交接契约各补一句。不新增配额，不改方法文件。

## 2.1.0 — 2026-09-15

对白场进入生产的交接物：台词设计表增加**生产版**（每句一行、台词逐字、目的动词、听者接住什么、局面变了什么、来源标注、通用关自查、人物声音核对、情绪参考落点），交接契约与 SKILL 同步。触发：2026-09-15 一条对白场 Prompt 的台词未经本技能设计、由制作方顺手补写，成片与文本都"太平"（有台词镜 69%、每镜子标签 1.2，对照同项目金样 92% / 0.3）。2.0.0 把设计表改成按需分析容器是对的，但没有给"进入生产"这一步一个可检查的出口物，制作方契约写"默认附"、本技能写"按需"，缝隙就在这里。分析用途不变，仍不默认逐句填表、仍不进入剧本正文；不新增校验脚本，闸门由项目层自建。

## 2.0.0 — 2026-09-11

- 重构入口与方法层：按创作问题渐进加载，独立完成概念、故事、剧本、对白与节奏修订；不依赖其他 film 技能、GitHub 标签或远端版本。
- 新增19项官方一手创作来源的可追溯记录、导演方法入口与视听叙事写法。网络研究仅 search；正文片段、官方简介、课程预览明确分级，不声称通读或观看。
- 原样内置用户25条情绪参考的JSON和Markdown，附原始哈希；新增25条独立写作注记、中文索引、精确查询和一致性验证。原文、改编与原创扩展分开。
- 将情绪触发、人物理解、控制、外显、关系接收和余波接入剧本；支持强烈释放、高强度克制、混合情绪和非线性变化，不按原库标签限制人物。
- 重写台词工艺、节拍转对白、叙事节奏、系列引擎和交接规则。移除强制双语、逐句表、固定情绪阶梯、词速/对白占比和先导不得揭结果等配额。
- 旧来源索引退役为迁移指针；清理旧项目偏好污染，保留正典、范围、保存和阅读稿工具。取消读取外部技能的同文测试；新增纯资料查询路由。
- 96项unittest与shell回归通过，原文哈希及字段全量一致，官方技能校验器通过；12组作者非盲文本走查保留输入、失败初稿、修订和局限。没有独立胜率、真人或生成视频效果结论。

---

历史版本记录，仅说明当时的实现，不构成当前指令或依据。

## 1.4.0 — 2026-09-10

叙事节奏方法（节奏 ≠ 台词长短）。此前用户要求"调整节奏"时，本 skill 只有"台词预算/精简台词"这一条现成杠杆（`dialogue-craft.md` §四、`beat-to-dialogue.md`、`handoff-contract.md` §四都在讲时长适配），没有独立的叙事节奏方法，也没有把两者分开的护栏——于是"调节奏"被默认执行成"缩句"。

**根因**：①无叙事节奏方法文件；②SKILL 无对应硬规则/路由；③"台词预算=精简台词"的时长适配语汇是唯一现成杠杆，被误当成节奏杠杆。

**改动（均在 film-creative 侧文件，不动同文的 `handoff-contract.md`）**：
- 新增 `references/narrative-pacing.md`：核心结论——节奏快慢 = 观众获取新信息与张力/情绪变化的速率，由信息释放顺序、场景转折、赌注升级、节拍密度、场序、潜台词决定，**不等于单句台词字数**；放慢常是加停顿/节拍，加快常是重排信息或砍整个冗余节拍/场。给出触发→先诊断（哪层 · 慢/赶在哪 · 动哪个杠杆）、叙事节奏杠杆表、"台词只在解释/重复/离题时才动且需授权"、"台词预算 ≠ 叙事节奏"、误用信号。
- `SKILL.md`：硬规则 10（调节奏先叙事诊断，不以增删改台词为默认手段）＋快速路由"节奏太慢/太赶"条＋组件引用"调整叙事节奏时"。
- `dialogue-craft.md` §四、`beat-to-dialogue.md`：台词预算处补一句——预算是**时长适配**，与叙事节奏是两件事，"调节奏"走 `narrative-pacing.md`，不等于缩句；预算精简只在 film-director 回传超预算时做，且先重构场再考虑削句。
- 边界：画面/剪辑节奏（镜头长度、切点、一句一切）属生产侧 film-director `dialogue-pacing.md`，本文件是叙事节奏。
- 来源：Murch《In the Blink of an Eye》、McKee《Story》、Yorke《Into the Woods》、No Film School / ScreenCraft / Script Mag、TV showrunner craft（Fiveable / 《Showrunners》/ Scriptnotes 728）——经 web search 获取要点，**未通读原文**，tag 从严（`[转述]`/`[行业文]`），条件式操作为本 skill `[推论]`。
- 测试：`test_routing.py` 加 `test_pacing_routes_to_narrative_not_dialogue_trim`，并把 `narrative-pacing.md` 纳入退役门禁短语扫描；87 unittest + shell 回归通过。

## 1.3.2 — 2026-09-08

容错修复（对两个 skill 的脚本、测试与文档做一次审查后发现的问题；无新功能）。

- `scripts/canon_scan.py`：跳过 Excel 锁文件（`~$…xlsx`，主表在 Excel 里打开时必然存在）；无法读取的 xlsx（非 zip、损坏）报 `SKIP` 并继续，不再整次扫描崩溃；同一行 / 单元格里互为子串的别名（如 `Preston` 与 `Preston Vane`）只报最长匹配一次；`--ignore` 对完整原文生效（此前只对截断到 120 字的摘要匹配，标记在 120 字之后时漏过滤）。`--json` 多一个 `skipped` 数组。
- `scripts/xlsx_lite.py`、`scripts/ledger_view.py`：与 film-director 1.3.2 同文——`<row>` / `<c>` 缺 `r` 属性时按位置读；非 zip 文件抛 `ValueError`；`ledger_view` 只把时间列的小数显示为 mm:ss（词/秒等列此前会显示成 `720:00`）。
- `SKILL.md`：对白出处指向补 `craft-sources-1.3.1.md`（1.3.1 之后台词工艺的出处在该文件；`craft-sources-1.2.0.md` 只覆盖 dialogue-design 的 D1/D2 与 Fountain）。
- `scripts/validate_concept.py` 文档字符串改为 film-creative。
- 测试：`test_canon_scan.py` +3（ignore 全文匹配、别名去重、锁文件 / 损坏文件跳过）并删一行死代码；`test_collab_docs.py` 的同文检查扩到 xlsx_lite / ledger_view（与 film-director 侧新增的 `test_shared_files.py` 互为镜像）；`test_ledger_view.py` 加非时间列小数断言。86 unittest + shell 回归通过。

## 1.3.1 — 2026-09-08

按体系（好莱坞 / 欧洲 / 韩国 / 竖屏短剧）落地台词与系列方法论，并把 1.3.0 里未读原文就并入的链接逐条重新标注证据强度。

- `references/dialogue-craft.md` 重写：Mamet（三问、观众不为信息收看、沉默电影测试、删第三方讨论场）· Sorkin（意图与障碍、press on it、对白如音乐、读出声、增减一个音节）· McKee《Dialogue》（the said / the unsaid / the unsayable；characterization vs true character；言语行动）· Truby（story / moral / key words 三轨；盟友批评手段；关键词累积）· Weston（情绪不可演、动词可演；潜台词比文本响；私密 adjustment）· Snyder（Pope in the Pool）· Rhimes（听过即陈词）· Lindelof（可见物件、问题收尾）· Scriptnotes 403/609/693 · on-the-nose 先直白再潜台词 · Sciamma · Yorke（want / need、分形）· Johnstone（地位句法、跷跷板）· 金银淑（挑词、把可怕写得迷人）· 卢熹京（研究、人人为主角、克制）· 朴海英（余韵、一字不差）· 郑瑞景 · 韩剧结构 · ReelShort / 红果 / 六幕标准 · 双语坑；13 条逐句检查。
- `references/craft-sources-1.3.1.md`（取代 1.3.0）：每条来源附链接与强度；明确 M1 / P1 / KE1 / W1 作者页为已读原文，S1 / R1 / B1 / L1 等为课程页或报道摘录，Thorne / Davies 无讲稿文本故未采用。
- `references/series-engine.md`：Truby 盟友批评、Parker / Stone 原话、Yorke 分形与 want / need、§4b 每集骨架（Harmon 八步 / 短剧单集公式）、Hitchcock 原话与例外、通过行动与他人反应亮相、Lindelof 问题收尾；去掉对具体项目的指涉。
- `scripts/ledger_view.py` + `tests/test_ledger_view.py`：账本模式下按镜号范围读 xlsx 为 Markdown；`story-context.md` 加账本读取指引；`stage-3b-story.md` 多集行接 `series-engine.md`；`output-formats.md` 加"对白场交接生产"行（台词设计表为附件、不进正文）。
- `preference-ledger.md`：来源列的项目名改为泛称（公共仓库不留具体项目标识）。
- 测试：83 个 unittest 与 shell 回归通过。创意增益仍未做独立盲测。

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
