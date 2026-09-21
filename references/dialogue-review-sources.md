# 出稿后对白 review 的一手来源与阈值

`scripts/review_script.py` 每条判断引用的来源编号（S1–S9）在此登记。访问核对：2026-09-21 两次（建档 + 逐条复核）。S1–S6、S8、S9 为本次实际读取的原文（PDF / PMC 全文 / 官方文字稿 / 转载全文）；S7 本次访问被拒（HTTP 403），沿用 `context-creativity-sources.md` 3.0.0 的登记，标 `[本次未重读]`。未读到原文的书目不列入。来源只支撑"这项检查为什么值得做"，不提供可机械套用的对错标准；具体人物、语域与用户锁定内容始终优先。

## 一、来源清单

| 编号 | 来源（可回访） | 可信范围 | 支持哪条检查 |
|---|---|---|---|
| S1 | Sacks, Schegloff & Jefferson, "A Simplest Systematics for the Organization of Turn-Taking for Conversation", *Language* 50(4), 1974, pp. 696–735。[JSTOR 412243](https://www.jstor.org/stable/412243)；[MPG 开放 PDF](https://pure.mpg.de/rest/items/item_2376846/component/file_2376845/content) `[一手 / 会话分析奠基论文]` | 基于英语电话与面对面录音的会话结构描述。pp. 700–701 列出会话的 14 条可观察事实（说话人轮换、一次一人说、轮次长短不固定、内容不预定）；§4.6 p. 709：轮次单位可以是一个词、一个短语、一个从句或一个句子，长短由说话人当场选择；§4.8 p. 710："next turns can … be constrained by prior turns"，即下一轮受上一轮约束（相邻对第一部分选定回应）；§4.12 p. 716：被点名的提问选定被点名者下一个说话（"an addressed question selects its addressee to speak next"）。 | **(a) 来回**：每句有收件人、下一句是否受上一句约束——`link_prev`、`conversation_share`、两人来回轮数、点名 / 提问选定下一位说话人。**反向保护**：短句、单词回答、长句都是合法轮次单位，句长本身不判错。 |
| S2 | Stivers et al., "Universals and cultural variation in turn-taking in conversation", *PNAS* 106(26), 2009, pp. 10587–10592。[PMC2705608](https://pmc.ncbi.nlm.nih.gov/articles/PMC2705608/) `[一手 / 十种语言的问答语料]` | 十种语言的自然会话中，问句之后的回应里"answers"占 64%（韩语）到 87%（荷兰语、Yélî Dnye）；所有语言都避免重叠、把轮次间沉默压到最短；9/10 种语言里提问者看着对方时回应更快。 | **(a)** 问句默认得到回答——`questions` / `questions_answered`；问了没人接是需要理由的例外。**(c-画外)** 面对面提问与回应的默认是看着对方——支持"说话人与听者能否同框"作为检查项 `[推论：从面对面语料到镜头语言]`。 |
| S3 | Levinson & Torreira, "Timing in turn-taking and its implications for processing models of language", *Frontiers in Psychology* 6:731, 2015。[PMC4464110](https://pmc.ncbi.nlm.nih.gov/articles/PMC4464110/) `[一手 / 综述 + Switchboard 语料数据]` | Switchboard 语料的平均轮次（按停顿间单位近似）约 1680 ms；轮次间隔平均约 200 ms；30.1% 的换手带有重叠；日常说话是"phrasal or clausal unit"的短爆发，可长可短。 | **(b) 标语化**：平均句长基线——1.7 s 一轮，按 4 词/s 约 6–7 词 `[推论：语速换算]`；重叠 / 打断在真实会话里常见，因此"被打断"是自然特征（信号），但不是必需。 |
| S4 | LDC, Switchboard-1 Release 2 目录页（含 Switchboard Dialog Act Corpus 统计：1155 段 5 分钟对话，205,000 个话语单位，1.4 百万词）。[catalog.ldc.upenn.edu/LDC97S62](https://catalog.ldc.upenn.edu/LDC97S62) `[官方 / 语料统计]` | 1.4M / 205k ≈ 6.8 词 / 话语单位 `[推论：由官方数字相除]`；这是对话行为标注的"utterance"，切分比说话轮更细，按轮算的均值只会更高；电话闲聊语料，不是剧本；分布很宽，均值只是参照。 | **(b)** `mean_words_min` 阈值的锚点：屏幕对白比闲聊更紧，取 4 词为下限 `[推论]`。 |
| S5 | John August & Craig Mazin, *Scriptnotes* Episode 609 "Dialogue and Character Voice" 官方文字稿，2023-09-06。[johnaugust.com](https://johnaugust.com/2023/scriptnotes-episode-609-dialogue-and-character-voice-transcript) `[一手 / 职业编剧方法]` | 对白的第一要求是"characters talking to each other, with each other, and not just intersecting monologues"；好对白像 Velcro，两片是为彼此设计的；"The thing I say influences the thing that you say back to me"；写台词要"说一句，立刻跳到对方身上去听"；"what's more / so"这类连接词是接住上一句的痕迹；有强烈风格的作者（Mamet、Tarantino、Sorkin）仍为不同人物分出差异。 | **(a)** "交错独白"就是本次 v1 的病名——`orphan_runs`、`link_prev` 里的回应词起句与词汇回声直接对应"Velcro"。**反向保护**：风格化 ≠ 错误。 |
| S6 | David Mamet 致 *The Unit* 编剧备忘录（2005），No Film School 转载全文。[nofilmschool.com](https://nofilmschool.com/2010/10/david-mamet-drama-a-memo-the-unit-writers) `[一手备忘录 / 第三方转载，本次已读转载页；无官方原件]` | 每场三问：WHO WANTS WHAT? WHAT HAPPENS IF THEY DON'T GET IT? WHY NOW?；观众不为信息收看。 | **需模型复核**清单的判断框架：一句短话成不成立，看他要什么、对谁、为什么此刻（对应 SKILL.md 取向 6）。备忘录语气绝对，只取三问，不采用其禁令。 |
| S7 | Céline Sciamma, BAFTA Screenwriters' Lecture 2019 官方文字稿。[bafta.org](https://www.bafta.org/media-centre/press-releases/screenwriters-lecture-series-2019-celine-sciamma/) `[一手讲稿 / 本次未重读：403]` | "没有冲突不等于没有张力"；想拍的场景与剧情需要的场景。 | **反向保护**：安静戏、少台词、靠近型场景不因台词少或短被判错——`min_lines` 以下不做统计判断；短句有理由（回答、喊名、齐喊）就豁免。 |
| S8 | David Bordwell, "Where did the two-shot go? Here." *Observations on film art*, 2013-10-07。[davidbordwell.net](https://www.davidbordwell.net/blog/2013/10/07/where-did-the-two-shot-go-here/) `[一手 / 电影学者博客]` | 主流美国片的常见做法是"Cut a lot and move the camera instead of moving the actors"；持续的双人镜头可以承载长段对白，让"action and reaction"在同一固定机位里完成；双人镜头常只用来引出正反打。 | **(c) 一句一镜**：连续台词若在同一画面里的两个人之间来回，分镜可以用双人镜头或正反打承载；每句换到互不接话的第三个人，就只能一句一镜 `[推论：从调度观察到剧本层代理量 third_party_jump_share]`。 |
| S9 | Tim J. Smith, "The Attentional Theory of Cinematic Continuity", *Projections* 6(1), 2012, doi:10.3167/proj.2012.060102；本次读的是作者预印本（[UAL 开放 PDF](https://ualresearchonline.arts.ac.uk/id/eprint/21187/2/6679.pdf)，页码与期刊版不同）`[一手 / 眼动实验 + 理论]` | 无剪辑长镜头里，"Shifts in conversation are followed by clustering gaze on the speaker's face then gradual shifts back to the listener"；正反打序列先用建立镜头交代所有人位置，再"alternates between shots favoring each character in turn, typically while they are speaking"；视线不匹配时观众要反向搜索说话人。 | **(c) 画外句配在别人脸上**：观众的注意力默认落在说话人的脸上，画外句叠在第三人脸上与这一默认相反——`offscreen_lines` 判为问题的依据；同框 / 收件人不明的句子列为需模型复核。 |

## 二、哪些检查有来源、哪些是本 skill 的推论

| 检查项 | 脚本字段 | 来源支撑 | 本 skill 的 `[推论]` 部分 |
|---|---|---|---|
| 每句有收件人；下一句受上一句约束 | `addressee`、`link_prev`、`conversation_share`、`orphan_runs` | S1（相邻对、点名选定下一位）、S5（Velcro / 交错独白）、S2（问句得到回答） | 用"回答问句 / 点名 / 词汇回声 / 回应词起句 / 追问"五种可见痕迹近似"受上一句约束"；没有痕迹只说明脚本看不出，不等于没接——所以判定要同时满足"最长两人来回 < 3 轮"和"有人接的台词 < 50%" |
| 两人来回的轮数 | `longest_exchange`、`exchange_coverage` | S1（轮换是会话基本事实） | "至少 A→B→A 三轮才算来回"是本 skill 的操作定义；多人对话（A 问 B 答 C 补）不在此计，靠 `conversation_share` 兜底 |
| 句长与短句占比 | `mean_words`、`short_unexcused_share` | S3（平均轮次 ≈ 1.7 s）、S4（≈ 6.8 词/话语） | 4 词/s 换算、`mean_words_min = 4`、`short_words = 4`、`short_unexcused_max = 0.45`；豁免规则（回答问句、喊名、齐喊、≤2 词感叹、明显接住上一句）依据 S1 "轮次单位可以是一个词" |
| 主谓宾完整度 | `clause`、`fragment_unexcused_share` | S1 §4.6（单位类型：词 / 短语 / 从句 / 句子） | 只对英文实现的启发式分类（full / imperative / fragment / vocative）；`fragment_unexcused_max = 0.4`；不作为独立问题，只作标语化的证据 |
| 每句换人、无人接 | `third_party_jump_share` | S8（双人镜头 / 正反打承载来回）、S9（注意力跟随说话人） | 把"换到第三个人说且不接前句"当作"必须一句一镜"的剧本层代理量；`third_party_jump_max = 0.4`，且只在没有来回时触发 |
| 画外句 | `offscreen_lines` | S9（视线落在说话人脸上）、S2（面对面提问看着对方） | 只识别括号里的画外 / O.S. / V.O. 标注；剧本没标但分镜会变画外的句子，脚本判不了，交给"需模型复核"与 film-director |
| 自然会话特征（犹豫、打断、口头填充、追问） | `hesitation_marks`、`questions` | S3（重叠 30.1%）、S5（连接词是听见的痕迹） | 只作信号不判错：没有这些不等于不自然（`character-scene-development.md` §七 误用信号：不为自然强制"嗯、那个"） |
| 安静戏保护 | `min_lines` | S1（轮次长短不固定）；S7 只作旁证（本次未重读） | `min_lines = 4` 以下不做统计判断；是否"有理由的短句"最终由模型按上下文判（SKILL.md 取向 6） |

## 三、阈值校准（全部 `[推论]`，请用户调）

用 THE ORDER EP02 场 1 的两版校准（`tests/fixtures/review/`）：

| 指标 | v1（用户否决） | v3（用户采用） | 阈值 | 触发条件 |
|---|---|---|---|---|
| 最长两人来回（轮） | 0 | 7 | < 3 | 与下一行同时成立 → "没有形成来回" |
| 有人接 / 在接别人的台词 | 40% | 87% | < 50% | 同上 |
| 平均词 / 句 | 3.0 | 6.0 | < 4 | 只在来回也不成立时算证据（句长本身不判错） |
| 无理由的 ≤4 词短句 | 40% | 8% | > 45% | 独立触发（v1 未触发，由平均句长触发） |
| 无主谓的碎句（无理由） | 10% | 3% | > 40% | 独立触发，只作标语化证据 |
| 换到第三人且不接前句 | 40% | 15% | > 40% | 只在没有来回时触发（v1 恰在边界，未触发） |
| 画外标注 | 3 句 | 0 句 | ≥ 1 | 有来回问题时并入该问题，否则独立成条 |

两版之间空隙很大，阈值放在中间偏保守一侧；只有两组样本，不能声称阈值有普遍性。改阈值在 `scripts/review_script.py` 的 `THRESHOLDS`。

## 四、复核记录（2026-09-21 第二次）

逐条复核结论——按"可回访 / 一手 / 本次已读 / 支持的检查是否直接"四项：

| 编号 | 可回访 | 性质 | 本次已读 | 支持是否直接 | 处理 |
|---|---|---|---|---|---|
| S1 | JSTOR + MPG 开放 PDF | 一手研究 | 是（PDF 全文，页码核对） | 直接：相邻对、点名选下一位、轮次长短不固定 | 保留 |
| S2 | PMC 开放全文 | 一手研究 | 是 | 直接：问句得到回答；**间接**：面对面注视 → 同框（`[推论]`） | 同框部分降为推论，脚本输出已标 |
| S3 | PMC 开放全文 | 一手数据 + 综述 | 是 | 直接：平均轮次时长、重叠比例；**间接**：秒 → 词换算（`[推论]`） | 保留，换算标推论 |
| S4 | LDC 官方目录 | 官方统计 | 是 | 间接：utterance ≠ turn；只作阈值锚点 | 降为锚点，不作判据 |
| S5 | 官方文字稿 | 一手创作方法 | 是 | 直接：交错独白 / Velcro | 保留 |
| S6 | 第三方转载 | 一手备忘录 | 是（转载页） | 间接：只作复核框架，不进脚本判定 | 保留为框架 |
| S7 | 官方页（本次 403） | 一手讲稿 | **否** | 间接：安静戏不判错已由 S1 覆盖 | 降为旁证 |
| S8 | 作者博客 | 一手观察（学者） | 是 | 间接：调度观察 → 剧本层代理量（`[推论]`） | 保留，代理量标推论 |
| S9 | UAL 开放预印本 | 一手研究 | 是 | 直接：视线跟说话人；**间接**：→ 画外句判为问题（`[推论]`） | 保留，推论部分标注 |

脚本输出（终端与 `--json` 的 `basis` 字段）对每个问题同步标注：判断依据哪几条来源、阈值与代理量属于 `[推论]`。

## 五、未采用 / 未读到

- Robert McKee, *Dialogue* (2016)：只找到第三方转载页且访问被拒，未读原文，不引用。
- Grice, "Logic and Conversation" (1975)：公开 PDF 访问失败，本次未读；"下一句与上一句相关"已由 S1 §4.8 覆盖。
- BBC Writersroom 格式指南：未取得官方 PDF；O.S. / 画外标注按剧本页模板的括号约定识别，不引用格式规范。
- 没有中文会话语料的句长数据；中文台词只做来回 / 收件人 / 画外统计，句长与主谓宾指标不计算（脚本会在信号里说明）。
