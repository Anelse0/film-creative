# 出稿后剧本 review（对白连通 · 台词经济 · 事件轨）的一手来源与阈值

`scripts/review_script.py` 每条判断引用的来源编号（S1–S13）在此登记。访问核对：2026-09-21 两次（建档 + 逐条复核）；2026-09-23 重读 S6 并新增 S12（人物赌注检查）；同日重读 John August 2007 并登记为 S13（画面推进检查）；2026-09-24 重读 S5 官方文字稿全文，补登它反对重复与接话的后半（台词经济检查）。S1–S6、S8–S11 为本次实际读取的原文（PDF / PMC 全文 / 官方文字稿 / 转载全文）；S7 本次访问被拒（HTTP 403），沿用 `context-creativity-sources.md` 3.0.0 的登记，标 `[本次未重读]`。未读到原文的书目不列入。来源只支撑"这项检查为什么值得做"，不提供可机械套用的对错标准；具体人物、语域与用户锁定内容始终优先。

## 一、来源清单

| 编号 | 来源（可回访） | 可信范围 | 支持哪条检查 |
|---|---|---|---|
| S1 | Sacks, Schegloff & Jefferson, "A Simplest Systematics for the Organization of Turn-Taking for Conversation", *Language* 50(4), 1974, pp. 696–735。[JSTOR 412243](https://www.jstor.org/stable/412243)；[MPG 开放 PDF](https://pure.mpg.de/rest/items/item_2376846/component/file_2376845/content) `[一手 / 会话分析奠基论文]` | 基于英语电话与面对面录音的会话结构描述。pp. 700–701 列出会话的 14 条可观察事实（说话人轮换、一次一人说、轮次长短不固定、内容不预定）；§4.6 p. 709：轮次单位可以是一个词、一个短语、一个从句或一个句子，长短由说话人当场选择；§4.8 p. 710："next turns can … be constrained by prior turns"，即下一轮受上一轮约束（相邻对第一部分选定回应）；§4.12 p. 716：被点名的提问选定被点名者下一个说话（"an addressed question selects its addressee to speak next"）；§5 p. 727 "recipient design"：说话的措辞、选题都"display an orientation and sensitivity to the particular other(s) who are the co-participants"。 | **(a) 来回**：每句有收件人、下一句是否受上一句约束——`link_prev`、`conversation_share`、两人来回轮数、点名 / 提问选定下一位说话人。**反向保护**：短句、单词回答、长句都是合法轮次单位，句长本身不判错。**(d) 潜台词支点**：人物的省略是为在场对方设计的，不是为观众——观众不在这层"co-participants"里 `[推论：从会话到观众]`。 |
| S2 | Stivers et al., "Universals and cultural variation in turn-taking in conversation", *PNAS* 106(26), 2009, pp. 10587–10592。[PMC2705608](https://pmc.ncbi.nlm.nih.gov/articles/PMC2705608/) `[一手 / 十种语言的问答语料]` | 十种语言的自然会话中，问句之后的回应里"answers"占 64%（韩语）到 87%（荷兰语、Yélî Dnye）；所有语言都避免重叠、把轮次间沉默压到最短；9/10 种语言里提问者看着对方时回应更快。 | **(a)** 问句默认得到回答——`questions` / `questions_answered`；问了没人接是需要理由的例外。**(c-画外)** 面对面提问与回应的默认是看着对方——支持"说话人与听者能否同框"作为检查项 `[推论：从面对面语料到镜头语言]`。 |
| S3 | Levinson & Torreira, "Timing in turn-taking and its implications for processing models of language", *Frontiers in Psychology* 6:731, 2015。[PMC4464110](https://pmc.ncbi.nlm.nih.gov/articles/PMC4464110/) `[一手 / 综述 + Switchboard 语料数据]` | Switchboard 语料的平均轮次（按停顿间单位近似）约 1680 ms；轮次间隔平均约 200 ms；30.1% 的换手带有重叠；日常说话是"phrasal or clausal unit"的短爆发，可长可短。 | **(b) 标语化**：平均句长基线——1.7 s 一轮，按 4 词/s 约 6–7 词 `[推论：语速换算]`；重叠 / 打断在真实会话里常见，因此"被打断"是自然特征（信号），但不是必需。 |
| S4 | LDC, Switchboard-1 Release 2 目录页（含 Switchboard Dialog Act Corpus 统计：1155 段 5 分钟对话，205,000 个话语单位，1.4 百万词）。[catalog.ldc.upenn.edu/LDC97S62](https://catalog.ldc.upenn.edu/LDC97S62) `[官方 / 语料统计]` | 1.4M / 205k ≈ 6.8 词 / 话语单位 `[推论：由官方数字相除]`；这是对话行为标注的"utterance"，切分比说话轮更细，按轮算的均值只会更高；电话闲聊语料，不是剧本；分布很宽，均值只是参照。 | **(b)** `mean_words_min` 阈值的锚点：屏幕对白比闲聊更紧，取 4 词为下限 `[推论]`。 |
| S5 | John August & Craig Mazin, *Scriptnotes* Episode 609 "Dialogue and Character Voice" 官方文字稿，2023-09-06。[johnaugust.com](https://johnaugust.com/2023/scriptnotes-episode-609-dialogue-and-character-voice-transcript) `[一手 / 职业编剧方法]` | 对白的第一要求是"characters talking to each other, with each other, and not just intersecting monologues"；好对白像 Velcro，两片是为彼此设计的；"The thing I say influences the thing that you say back to me"；写台词要"说一句，立刻跳到对方身上去听"；"what's more / so"这类连接词是接住上一句的痕迹——Mazin 的原意是"agreeing with it, tacitly. And now you're adding"，接住**并往上加**；有强烈风格的作者（Mamet、Tarantino、Sorkin）仍为不同人物分出差异。**同一期的后半（2026-09-24 逐字核对，3.3.0 建档时漏取）**：Mazin "Simple rule of thumb is if the audience hears it once, don't make them hear it twice"，"certainly you don't want to repeat anything ever"；"if you have any sense that thoughts or lines are vaguely repeating, that's a writing problem for sure. And you have to eliminate those"；August 说 uh-huh / yeah 这类 acknowledgment "that's rare"，"you may not put every utterance of a person in the dialogue of your script"，每句台词"should only kind of be possible in that one moment"。 | **(a)** "交错独白"就是本次 v1 的病名——`orphan_runs`、`link_prev` 里的回应词起句与词汇回声直接对应"Velcro"。**反向保护**：风格化 ≠ 错误。**(g) 台词经济**（3.8.0）："接住"只是前半；听过一次的不再说、重复的删、接话很少——删除测试与压缩测试的依据。3.3.0–3.7.0 只取了前半，`link_prev` 把回应词起句与词汇回声直接当成"接住"，又没有任何一项问这句带来了什么，是"设计废话"的来源之一。 |
| S6 | David Mamet 致 *The Unit* 编剧备忘录（2005），No Film School 转载全文。[nofilmschool.com](https://nofilmschool.com/2010/10/david-mamet-drama-a-memo-the-unit-writers) `[一手备忘录 / 第三方转载，本次已读转载页；无官方原件]` | 每场三问："1) WHO WANTS WHAT? 2) WHAT HAPPENS IF [THEY] DON'T GET IT? 3) WHY NOW?"；"THE AUDIENCE WILL NOT TUNE IN TO WATCH INFORMATION."（2026-09-23 重读转载页逐字核对）；不同时推进剧情又自身成立的场 "IS EITHER SUPERFLUOUS, OR INCORRECTLY WRITTEN."（2026-09-23 第二次读转载页核对） | **需模型复核**清单的判断框架：一句短话成不成立，看他要什么、对谁、为什么此刻（对应 SKILL.md 取向 6）。**(e) 人物赌注**（3.5.0）：三问成为剧本页"本场赌注"卡的三栏（此刻向谁要什么 / 怕失去什么 / 为什么是现在）；"观众不为信息收看"是"承接与埋点不该占掉整场台词"的依据。**(g) 事件轨**（3.7.0）："不推进剧情的场是多余的"是事件轨"每行一次变化、删掉损失必填"的依据；原话管的是整场，挪到场内每一行是本 skill 的 `[推论]`。备忘录语气绝对，只取三问与这两句，不采用其禁令。 |
| S7 | Céline Sciamma, BAFTA Screenwriters' Lecture 2019 官方文字稿。[bafta.org](https://www.bafta.org/media-centre/press-releases/screenwriters-lecture-series-2019-celine-sciamma/) `[一手讲稿 / 本次未重读：403]` | "没有冲突不等于没有张力"；想拍的场景与剧情需要的场景。 | **反向保护**：安静戏、少台词、靠近型场景不因台词少或短被判错——`min_lines` 以下不做统计判断；短句有理由（回答、喊名、齐喊）就豁免。 |
| S8 | David Bordwell, "Where did the two-shot go? Here." *Observations on film art*, 2013-10-07。[davidbordwell.net](https://www.davidbordwell.net/blog/2013/10/07/where-did-the-two-shot-go-here/) `[一手 / 电影学者博客]` | 主流美国片的常见做法是"Cut a lot and move the camera instead of moving the actors"；持续的双人镜头可以承载长段对白，让"action and reaction"在同一固定机位里完成；双人镜头常只用来引出正反打。 | **(c) 一句一镜**：连续台词若在同一画面里的两个人之间来回，分镜可以用双人镜头或正反打承载；每句换到互不接话的第三个人，就只能一句一镜 `[推论：从调度观察到剧本层代理量 third_party_jump_share]`。 |
| S9 | Tim J. Smith, "The Attentional Theory of Cinematic Continuity", *Projections* 6(1), 2012, doi:10.3167/proj.2012.060102；本次读的是作者预印本（[UAL 开放 PDF](https://ualresearchonline.arts.ac.uk/id/eprint/21187/2/6679.pdf)，页码与期刊版不同）`[一手 / 眼动实验 + 理论]` | 无剪辑长镜头里，"Shifts in conversation are followed by clustering gaze on the speaker's face then gradual shifts back to the listener"；正反打序列先用建立镜头交代所有人位置，再"alternates between shots favoring each character in turn, typically while they are speaking"；视线不匹配时观众要反向搜索说话人。 | **(c) 画外句配在别人脸上**：观众的注意力默认落在说话人的脸上，画外句叠在第三人脸上与这一默认相反——`offscreen_lines` 判为问题的依据；同框 / 收件人不明的句子列为需模型复核。 |
| S10 | Clark & Brennan, "Grounding in Communication", in Resnick, Levine & Teasley (eds.), *Perspectives on Socially Shared Cognition*, APA, 1991, pp. 127–149。[Stanford 开放 PDF](https://web.stanford.edu/~clark/1990s/Clark,%20H.H.%20_%20Brennan,%20S.E.%20_Grounding%20in%20communication_%201991.pdf) `[一手 / 心理语言学]` | p. 127：协作者"cannot even begin to coordinate on content without assuming a vast amount of shared information or common ground—that is, mutual knowledge, mutual beliefs, and mutual assumptions"；共同基础逐句累积更新。 | **(d) 潜台词支点**：一句话省略得掉的部分，是说者假定在双方共同基础里的；观众的共同基础只来自已播出的文本，所以省略句依赖的设定必须在前文建立过 `[推论：把"共同基础"从对话双方移到观众]`。脚本用"前文（本场 + `--context` 前几场）出现过"近似"在观众的共同基础里"。 |
| S12 | Craig Mazin, *Scriptnotes* Episode 403 "How to Write a Movie" 官方文字稿，2019。[johnaugust.com](https://johnaugust.com/2019/scriptnotes-ep-403-how-to-write-a-movie-transcript) `[一手 / 职业编剧方法；2026-09-23 已读]` | "Fear is our connection to a character."；"I feel for characters when I fear with them. It is vulnerability."；人物要自己做选择——"They have to make the choices or you're making it for them." 讲的是整部电影的人物弧，不是单场对白规则。 | **(e) 人物赌注**：卡上"怕失去什么"一栏的依据——观众与人物的连接来自他怕什么；从整片人物弧移到单场一栏是 `[推论]`。 |
| S13 | John August, "How to write a scene", johnaugust.com, 2007。[johnaugust.com/2007/write-scene](https://johnaugust.com/2007/write-scene) `[一手 / 职业编剧方法；2026-09-23 重读]` | 十一步清单：第 1 步本场必须发生什么、第 3 步谁该在场、第 5 步这场戏里最出人意料的事是什么（2026-09-26 补读：还写到"如果让人物自己掌控场面，多数人会选择回避冲突"）、**第 4 步 "Where could the scene take place?"——"The most obvious setting for a scene is generally the least interesting."**，同一段父子对白放在屠宰场和放在草地滚球赛上演出来不一样；**第 6 步 "Is this a long scene or a short scene?"**；第 8 步在脑子里放映这场戏。是写作方法，不是检查标准；没有给出任何时长或换景的数字。 | **(f) 画面推进**（3.6.0，3.7.0 并入事件轨）："先问地点、再问长短"的依据；地点与活动改变这场戏怎么演——August 的例子是同一段对白放在不同地点**演出来不一样**，不是换一个地点就多了一段戏，所以 3.7.0 起地点只作变化的属性。"≥30 s 至少两次变化""观众等一次变化 ≥40 s 复核"、按文本估时的系数都是本 skill 的 `[推论]`。skill 早在 `screenwriting-traditions.md` §五引过这篇，但只取了进入方式与脑内排演，第 4、6 步没接进流程——这是本次核查找到的原因之一。 |
| S11 | John August & Craig Mazin, *Scriptnotes* Episode 693 "Setups That Don't Feel Like Setups" 官方文字稿，2025。[johnaugust.com](https://johnaugust.com/2025/scriptnotes-episode-693-setups-that-dont-feel-like-setups-transcript) `[一手 / 职业编剧方法]` | 设定"just out of the blue … is going to feel weird and forced"；铺垫的做法是找"the present-tense need of the scene that brings up this idea"，让信息"is the point of a moment"（Mazin：像魔术师手里真的握着一枚硬币）；另一种"not objectionable"的做法是让人物当场问一句（"What happened to that church?"）。 | **(d)** 三种改法的来源：用当场需要 / 动作引出（Mazin 首选）、让第三人替观众问（"not objectionable"）、直说来历（本 skill 补的第三项，`[推论]`）。改法只作选项，按 SKILL.md"批评已有稿、改法未定"契约交付，不改稿。 |
| S14 | Robert McKee 官网：[《Do Your Scenes Turn?》](https://mckeestory.com/do-your-scenes-turn/)（《Story》节选）、[《Mary Queen of Scots》评析](https://mckeestory.com/mary-queen-of-scots-2018/)、[《Four Traps New Screenwriters Fall Into》](https://mckeestory.com/four-traps-new-screenwriters-fall-into/)、[*Dialogue* 书页](https://mckeestory.com/dialogue/) `[一手 / 作者官网；2026-09-26 子代理取全文，主会话抽查引文]`；《Story》的节拍与缺口定义只读到 [Goodreads 读者标注](https://www.goodreads.com/notes/40389794-story/29634010-william-c-woodard) `[二手]` | 人物处境的价值从头到尾没变，这场 "has activity … but nothing changes in value. It is a nonevent"；只为交代信息存在的场应删掉、把信息织进别处；两个人互相说彼此都知道的事，警报应一直响到这场被重新发明；理想的做法是先想这场能不能不用台词写出来，台词是 "the regretful second choice"；*Dialogue* 书页：说话就是在做事。二手：节拍是一次动作 / 反应的交换，转折点是预期与结果之间的缺口；"Convert exposition to ammunition"。 | **(h) 复述**（4.0.0）："互相说都知道的事"是复述检查的依据，修法是重建场而不是改句子。**设计卡**：转折（预期 → 结果、非事件）、弹药、静音测试（先想无台词怎么写）。二手的节拍定义只作写法说明，不作检查依据。 |
| S15 | Alexander Mackendrick《On Film-Making》（Faber 2004）：[Criterion 官方节选《Mackendrick and Odets》](https://www.criterion.com/current/posts/1762-mackendrick-and-odets)；编者 Paul Cronin 网站的 [《Slogans for the Screenwriter's Wall》](https://www.thestickingplace.com/alexander-mackendrick/slogans-for-the-screenwriters-wall/) 与 [《Step Outlines》](https://www.thestickingplace.com/alexander-mackendrick/step-outlines/) `[一手节选；2026-09-26 子代理取全文，主会话抽查引文]` | Odets：每个走进对峙的人物都带着弹药，一方缺的信息到了另一方手里就是王牌；改台词的检查是"他说不出这句，因为她不会让他轻易过关"；台词不变、换个好看的背景（"opening it out"）不会让戏更像电影；"Play the situations, not the words"；叮嘱演员别让人物舒服地坐下。Slogans："PASSIVITY is a capital crime in drama."；聪明的人物会预判并备好反招；说明性的内容除非处在当下的戏剧张力里否则无聊；好电影把对白换成外语仍能看懂六到八成。Step Outlines：每一场读起来是因果链上的一步，"所以结果是……"。 | **设计卡**：推动者与战术（被动是死罪）、阻力（对手不让他轻易过关）、弹药、静音测试（外语测试）、演处境不演台词。**`story-engine.md` §一**：剧情靠宣布推进、步进大纲的"所以结果是"。Criterion 节选也说 Odets 常写三到五人互动——与 THE ORDER"一条 clip 三个角色"的生产约束不同，那是生产层的事，本 skill 不改。 |
| S16 | John August & Craig Mazin, *Scriptnotes* Episode 728 "Beats to Scenes"（嘉宾 Drew Goddard）官方文字稿，2026。[johnaugust.com](https://johnaugust.com/2026/scriptnotes-episode-728-beats-to-scenes-with-drew-goddard) `[一手；2026-09-26 子代理取全文，主会话抽查引文]` | August 转述 Sorkin："when there's an obstacle that forces a new tactic, that's a beat"；场景是人物在做的事、遇到的障碍、怎样越过、做出的选择。 | **写法第 1 条**：一个节拍 = 一次出招 + 一次回应，障碍逼出新战术才进下一拍；同一战术换句话再说不是新节拍（据此把"复述、确认"判为不推进是 `[推论]`）。 |
| S17 | *Scriptnotes* Episode 357（讲 exposition）官方文字稿，2018。[johnaugust.com](https://johnaugust.com/2018/scriptnotes-ep-357-this-title-is-an-example-of-exposition-transcript) `[一手；2026-09-26 子代理取全文，主会话抽查引文]` | Mazin："As you and I both know"——那为什么还要说；让人物突然装糊涂好把事实讲出来，是在削弱人物；要想清楚为什么这个人此刻把信息告诉那个人、它让双方有什么感受；被演出来的说明不只是信息，是人物的证据。 | **(h) 复述**与**写法第 2、3 条**：信息当弹药、对手不配合、不为观众递话。把递话问句（"And Rhett?"）判为削弱人物是 `[推论]`。 |
| S18 | *Scriptnotes* Episode 735 "The Flashforward Fallback" 官方文字稿，2026。[johnaugust.com](https://johnaugust.com/2026/scriptnotes-episode-735-the-flashforward-fallback-transcript) `[一手；2026-09-26 子代理取全文，主会话抽查引文]` | August 把 agency 定义为人物采取行动、朝自己想去的方向推进的能力；Mazin：人物不能只被推着走、没有目标地反应；用人物走出去收场是 "shoe leather"。 | **设计卡推动者**、**写法第 4、6 条**（人物主动；晚进早出）。 |
| S19 | Variety《Global microdrama boom》，2025-11-13。[variety.com](https://variety.com/2025/tv/news/global-microdrama-boom-1236560947/) `[行业报道中的写作者原话；2026-09-26 子代理已读]` | 受访写作团队：写竖屏就是一门识别不必要的东西并删掉它的速成课。同期 THR（2025-12-23）转述课程要求"一个地点、每场多个角色" `[二手转述]`；Deadline（2025-09）受访经理说现行竖屏对白 "very two-dimensional"——描述现状，不是目标。 | 竖屏短剧对台词经济的要求与 S5 一致；不采用平台公式（`episode-design.md` §四）。 |

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
| 潜台词支点 | `presupposed`、`anchoring.candidates / planted / declared` | S10（共同基础）、S1 p.727（收件人设计）、S11（凭空出现 / 当场需要 / 当场问） | "省略句 + 当作已知的新指称（你的 X / 那个 X / 你有 X / 还 X）+ 接下来没人问"作为"看不懂"的代理量是 `[推论]`；指称抽取是英文启发式；中文动作行无法与英文指称对齐，只能引用交模型复核；`this / these`、"right here"视为指画面里的东西；账本（模板头部与"上下文承接"）里声明过的指称降为复核项。三种改法的措辞是模板，具体改什么由模型按本场填 |
| 事件轨（3.7.0，合并 3.5.0 人物赌注与 3.6.0 画面推进） | `checks.events`、`events.voiced / changes / places / jumps / linger_s / longest_gap / ends / estimate / declared` | S6（三问；不推进剧情的场是多余的）、S12（fear）、S13（先问地点、再问长短）、S1 / S2（说出口后有没有人接） | 脚本**不判**一句话有没有欲望、一个画面有没有意义（那需要关键词表，会误报）；只核对作者写正文前填的事件轨：人物清单齐不齐（说 ≥3 句的人 `stake_min_lines = 3`，以及每行变化的主体，含不说话的人）；锚句与说出口的句子逐字在正文、顺序一致、本人说、下一句有没有接；不说的有没有"理由""代价"；每行"谁：进 → 出"——进出相同、同一人的"出"重演判问题；**换了地点或跳了时间的行标为余韵或没有变化判问题**；删掉损失空判问题；≥30 s 少于 `min_changes = 2` 次变化且未登记"本场静止：理由"（3.6 的"本场单一画面：理由"仍认）判问题；全场无人说出口且未登记"本场不说出口：理由"判问题。**推进只数变化，不数地点**：全场一个地点只列复核（先诊断缺什么）。换地点 / 跳时间 / 无台词且覆盖 ≥`silent_review_s = 8` s / 只改变观众所知的行，列出变化、删掉损失、同一人上一次的状态、同一对象上一行，交模型做删除测试；余韵合计 ≥`linger_review_s = 10` s、观众等一次变化 ≥`gap_review_s = 40` s、自报总估时 < 文本估时 × 0.85（`estimate_under`）列复核；`--production-total` 比剧本估时多 20% 以上（`production_over`）在总判断里提醒（不退回）。文本估时：台词按语速（`wps` 4 词/秒；中文 4.5 字/秒），无台词段每句 `action_s` 1.5 秒，台词之间 ≤2 句的反应插入不另计。人物清单声明过的赌注词不再报"潜台词无支点"。全部阈值 `[推论]`，校准见 §三 |
| 台词经济（3.8.0） | `checks.economy`、`economy.candidates / runs / record` | S5 后半（听过一次不再听第二次；重复要删；接话很少；不是每句该说的都写进对白） | 脚本**不判**一句是不是废话——10 场盲评标注上，表面规则（全是已出现过的实词 / 回应词起句且新词 ≤1 / ≤5 词无新词 / 答案下一句就给的短问句 / 被截断的半句）精确率 0.32、召回 0.68，讨价还价、回扣、嘴硬、调情都长得像接话。所以候选只附证据列复核：前文哪里说过（本场、`--context` 前几场，按具体词、不按 know / look 这类常用词）、后文哪里回扣（`--later`，可能是铺垫）。判为问题的只有两种：缺删除测试记录（只在总判断里报一句）、记录与正文不符（记为删 / 并的还在正文、记为留的不在正文或没写带来什么）。低信息段（≥4 句、平均每句新实词 ≤0.75）交压缩测试。总判断不再报"有人接的台词占比""最长来回""平均词数"，不再输出"全场没有一个问句""口头填充 N 句"，说出口的行不再标"（没人接）"——它们推着作者补接话和问句；数值仍在 JSON。潜台词无支点的第三种改法从"让第三人替观众问"改为"让在场的人带着自己的立场问" |
| 复述（4.0.0） | `checks.repeat`、`repeat.lines / facts` | S5（听过一次不再听第二次）、S14（互相说都知道的事要重新发明这场）、S17（As you and I both know） | 与 `--context` 前几场（台词 + 英文画面文字）重合的三词短语（至少含一个实词，词干比较）、钟点与"明天 / 今晚"（只和紧挨着的上一场比）算复述；只重合一个星期几不算（反复提到的期限是在施压）；同一事实在本场 ≥3 句台词里出现算反复（连着几句的一轮来回——施压、讨价还价——只列复核）；≥2 句复述或一次事实反复判问题，1 句列复核；删除测试写明"回扣 / 铺垫 / 锁定"的"留"不计入但列复核——全部是 `[推论]`，校准见 §三 4.0.0 表 |
| 设计卡（4.0.0） | `checks.design`、`design.card / missing` | S14（转折、非事件、先想无台词怎么写）、S15（弹药、被动是死罪、外语测试）、S16（障碍逼出新战术） | 只查"## 设计"在不在、五格与观众已知、三种发生方式齐不齐；只在总判断里报，不改变结论（写作步骤不靠脚本判）；第一种或选中的一种是传话、转折没写成"预期 → 结果"列复核 |
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
| 潜台词无支点（场 3 v2 钥匙段 → 改法 C 后） | 1 句（key） | 0 句 | 省略句 ≤5 词或截断 ≤8 词或回应词起句 | 正例 `theorder-ep02-s03-v2-key-unanchored.md`；反例 场 1 v3 "Sloane, you might want to step back."（无当作已知的指称）、场 2 v2 "Nothing." / "Everything."（回答问句）、场 3 修复稿（Mack 问了） |

两版之间空隙很大，阈值放在中间偏保守一侧；只有两组样本，不能声称阈值有普遍性。改阈值在 `scripts/review_script.py` 的 `THRESHOLDS`。

人物赌注（3.5.0）用 THE ORDER EP03 场 4 v3（用户 2026-09-23 否决："没有突出人物自身的压力和希望'出道'的情绪，更多是在平铺说话"）校准：

| 样本 | 3.4.0 结论 | 3.5.0 结论 |
|---|---|---|
| `theorder-ep03-s04-v3.md`（原稿，无卡） | 只报"潜台词无支点"（"That's the job." 的 job，属误报） | 人物赌注：缺卡（Diego 4 句、Isa 3 句）排第一 |
| `theorder-ep03-s04-v3-card.md`（3.5.0；3.7.0 起转写为 `theorder-ep03-s04-v3-events.md`，结论不变）（按原稿自己的"两侧 / 上下文承接"栏如实回填一张卡，正文不动） | 同上 | Isa 上卡（全额奖学金、Cup 先发）却没有说出口的台词、也没写不说的理由与代价 → 问题；Diego 那句逐字在正文、本人说 → 兑现，但说完无人接 → 复核；Isa 场末"推迟"无代价 → 复核 |
| 探针：原稿 "That's fair." 换成 Isa「Not my scholarship.」 | 判"潜台词无支点"，改法是"直说来历 / 第三人问"——把人物的表态推回解释 | 卡上有出处时不报；无卡时仍报（观众确实不知道那份奖学金） |

只有一个真实否决样本加合成正反例，阈值没有普遍性；"效果提升"须用重写后的场 4 与原稿对照才能说。

画面推进（3.6.0）。**估时**用 THE ORDER 已出分镜的 5 场校准（剧本页"总窗口" vs 分镜方案"合计"，2026-09-23 读取；文本估时 = 台词词数 ÷ 4 + 无台词段动作句 × 1.5 s，用 `timeline()` 实算）：

| 场 | 剧本自报 s | 分镜实排 s | 自报 / 实排 | 文本估时 s | 文本 / 实排 |
|---|---|---|---|---|---|
| EP02 场 1 | 111 | 118 | 0.94 | 118.8 | 1.01 |
| EP03 场 1 | 140 | 158 | 0.89 | 162.2 | 1.03 |
| EP03 场 2 | 80 | 82 | 0.98 | 94.5 | 1.15 |
| EP03 场 3 | 46 | 52 | 0.88 | 51.2 | 0.98 |
| EP03 场 4 v4.1 | 69 | 88 | **0.78** | 74.5 | 0.85 |
| EP03 场 4 v4（重建样本） | 57 | 74 | **0.77** | 62.5 | 0.84 |

文本估时误差约 ±15%，只够当复核提示，不够判问题；试过"每个动作句都计时"（2 s/句：EP03 场 1 估 218 s，高估 38%）——台词之间的反应与台词同步，不能相加。真正把场 4 与其他场分开的是**分镜实排 / 剧本自报 > 1.2**：只有场 4 的两版超出（1.28 / 1.30），其余四场 1.02–1.13——这就是交接时长提醒 `production_over = 1.2` 的依据（3.6.1 起为提醒，不是退回条件）。系数只拟合了 5 场、同一项目、同一语速，换项目要重校。

**事件轨**（3.7.0）用场 4 四份样本校准（`tests/fixtures/review/*-events.md`；事件轨由维护者按各版原稿自己的赌注卡与场面轨如实转写，正文不动，**非盲**）：

| 样本 | 变化 | 地点 / 时间跳 | 3.6.0 画面结论 | 3.7.0 事件轨结论 |
|---|---|---|---|---|
| `theorder-ep03-s04-v3-events.md` | 6 | 1 / 0 | 画面没有推进（问题） | 问题：Isa 在清单上却哪一行都没说出口、也没写不说的理由（与 3.5.0 同一结论）；全场一个地点只列复核 |
| `theorder-ep03-s04-v4-events.md`（重建） | 9 | 1 / 0 | 画面没有推进（问题） | 通过；复核"全场一个地点、一种活动：变化看得见还是都在台词里" |
| `theorder-ep03-s04-v4.1-events.md`（采用稿） | 9 + 牛棚余韵 | 2 / 1 | **通过** | **问题：第 11 行换了地点（牛棚）、跳了时间，没有变化**；余韵合计 ≈ 15 s 复核 |
| `theorder-ep03-s04-v4.1-cut-events.md`（v4.1 删牛棚，对照） | 9 | 1 / 0 | —— | 通过 |

3.6 的"地点 × 活动"判据把问题标错了位置：v4 行行有事却被判问题，v4.1 加了一段没有事件的新地点反而通过，改法于是落到了"加地点"上（用户看成片："这 16 s 存在的意义是？"）。牛棚段按 v4.1 自己的卡回填是余韵——Isa 场末仍是"推迟"，卡上只在后面接了"Diego 在牛棚里蹲着等他，他还坐着"这个画面。**已知边界**：作者若为牛棚写出一个变化（如"Diego：绑护腿 → 蹲在本垒板后等 Isa"并把 Diego 加进人物清单），脚本放行，只把这一行连同"Isa 作为对象的上一行"交模型做删除测试（`test_bullpen_with_stated_change_goes_to_deletion_test_with_evidence`）——"这个变化是不是前面已经给过"是语义判断，脚本不猜。只有一个真实反例；"效果提升"要等新流程写出的场与旧稿对照、最好盲评才能说。

台词经济（3.8.0）用 `tests/fixtures/economy/` 的 10 场（2026-09-24 快照）与 `labels-2026-09-24.json` 校准。标注者是不知道假设的独立子代理，对每句做删除测试，标签 信息 / 要或拒 / 关系 / 笑点或性格 / 纯接话 / 功能性调度；不是用户标注，也不是改稿前后的盲评对照。

| 样本 | 台词 | 纯接话（标注） | 脚本候选 | 其中命中 | 低信息段 |
|---|---|---|---|---|---|
| THE ORDER EP02 场 1 | 39 | 9 | 11 | 6 | 0 |
| EP02 场 2 | 19 | 3 | 10 | 2 | 1 |
| EP02 场 3 | 17 | 0 | 4 | 0 | 0 |
| EP03 场 1 | 53 | 9 | 17 | 6 | 3 |
| EP03 场 2 | 26 | 5 | 12 | 5 | 1 |
| EP03 场 3 | 11 | 3 | 5 | 2 | 1 |
| EP03 场 4（写于赌注卡之后） | 13 | **0** | 4 | 0 | 1 |
| reckless EP02 场 1 | 8 | 2 | 1 | 1 | 0 |
| reckless EP02 场 2 | 12 | **0** | 2 | 0 | 0 |
| reckless EP02 场 3 | 21 | 3 | 5 | 1 | 1 |

合计 219 句、纯接话 34 句（15.5%，占台词词数 9.2%）；候选 71 句，命中 23：精确率 0.32、召回 0.68。漏掉的多是"复述画面刚演过的事"（"She's not picking up." / "Round two. Marsh." / "You're late."），动作行是中文，脚本对不上，只能靠模型的删除测试。标注者同时列出"看似废话其实有作用"的句子（讨价还价 "Candles are at half past." / "Lena." / "Five."，回扣 "It's her cake."，信条 "I don't throw a curve with a guy on second."，嘴硬 "I know where it is."）——这些都会进候选，由"留：带来什么"放行。场 4 与 reckless 场 2 为 0，说明问题不在"对话多"，而在没有一项要求每句带来东西；阈值 `run_min` 4、`run_new_max` 0.75 是 `[推论]`。

### 4.0.0 复述校准（非盲，维护者对照删除测试标注与剧情；样本小，只作复核线索）

| 样本（--context 前几场） | 脚本结果 | 对照 |
|---|---|---|
| Offset EP01 s06（s04、s05） | 问题：2 句——"the rest of the press tour"←s05 Hollis、"tomorrow"←s05 Hollis | s05 刚让观众知道打包宣传与明天碰面；s06 的删除测试 9 句全"留"，3.8.0 判"删除测试已做（留 9）"放行 |
| THE ORDER EP04 场 2（场 1） | 问题："wednesday" ×3 | 教练、Cole 在一场里三次报周三；场 3 Cole 又报一次（场 3 列 1 句复核） |
| reckless EP02 场 3（场 1、2） | 1 句复核："forty minutes out"←场 2 代客泊车 | 队友复述观众一分钟前看过的修车；其余复述是改写的说法（"It wouldn't start. He was walking past."），三词短语对不上——语义复述交冷读 |
| THE ORDER EP02 场 2–3、reckless 场 2（前几场） | 未见 | 这几场的纯接话是场内确认（"Monday. Okay."），不是跨场复述，归台词经济候选 |
| THE ORDER EP03 场 1（EP02 场 1–3） | 1 句复核："coaches see it monday"←EP02 场 2 Beckett | 标注为"要 / 拒"：Beckett 被追问时重复自己的话——列复核不判问题。修正前"monday""tonight"单独重合报了 5 句，改为星期几单独重合不算、"明天 / 今晚"只比上一场后降到 1 句；场内三句连着的"Monday"（Beckett / Diego 的施压来回）按"一轮来回"只列复核 |
| THE ORDER EP03 场 2（EP02 场 1–3、EP03 场 1） | 问题：2 句——Isa 两次引用自己场 1 的"you can walk out to it" | 标注一句"纯接话"、一句"笑点"：有意的自我引用，作者可在删除测试写"留：……——回扣"豁免 |
| THE ORDER EP03 场 3、场 4 | 各 1 句复核 | 场 3"He said five minutes"标注纯接话；场 4 Beckett 重提侦察表，标注"关系" |

已知边界：改写过的复述（换了说法）脚本对不上；中文动作行里的画面与英文台词对不上；有意的回扣与复述字面相同，只能靠作者写明或冷读判断。

## 四、复核记录（2026-09-21 第二次）

逐条复核结论——按"可回访 / 一手 / 本次已读 / 支持的检查是否直接"四项：

| 编号 | 可回访 | 性质 | 本次已读 | 支持是否直接 | 处理 |
|---|---|---|---|---|---|
| S1 | JSTOR + MPG 开放 PDF | 一手研究 | 是（PDF 全文，页码核对） | 直接：相邻对、点名选下一位、轮次长短不固定 | 保留 |
| S2 | PMC 开放全文 | 一手研究 | 是 | 直接：问句得到回答；**间接**：面对面注视 → 同框（`[推论]`） | 同框部分降为推论，脚本输出已标 |
| S3 | PMC 开放全文 | 一手数据 + 综述 | 是 | 直接：平均轮次时长、重叠比例；**间接**：秒 → 词换算（`[推论]`） | 保留，换算标推论 |
| S4 | LDC 官方目录 | 官方统计 | 是 | 间接：utterance ≠ turn；只作阈值锚点 | 降为锚点，不作判据 |
| S5 | 官方文字稿 | 一手创作方法 | 是 | 直接：交错独白 / Velcro | 保留 |
| S5（2026-09-24 重读） | 官方文字稿（johnaugust.com，curl 取全文逐字检索） | 一手创作方法 | 是 | 直接：听过一次不再听第二次、重复要删、接话很少、不是每句都写进对白、"what's more"是接住并往上加；**间接**：→ 候选规则与低信息段阈值（`[推论]`） | 补登后半，3.3.0 漏取 |
| S6 | 第三方转载 | 一手备忘录 | 是（转载页） | 间接：只作复核框架，不进脚本判定 | 保留为框架 |
| S7 | 官方页（本次 403） | 一手讲稿 | **否** | 间接：安静戏不判错已由 S1 覆盖 | 降为旁证 |
| S8 | 作者博客 | 一手观察（学者） | 是 | 间接：调度观察 → 剧本层代理量（`[推论]`） | 保留，代理量标推论 |
| S9 | UAL 开放预印本 | 一手研究 | 是 | 直接：视线跟说话人；**间接**：→ 画外句判为问题（`[推论]`） | 保留，推论部分标注 |
| S10 | Stanford 开放 PDF | 一手研究 | 是（p. 127 核对） | 直接：共同基础定义；**间接**：→ 观众的共同基础（`[推论]`） | 保留，推论部分标注 |
| S11 | 官方文字稿 | 一手创作方法 | 是 | 直接：凭空出现生硬、当场需要、当场问 | 保留；"直说来历"为本 skill 补项 |
| S6（2026-09-23 重读） | 第三方转载 | 一手备忘录 | 是（转载页，三问、"information"句与"SUPERFLUOUS"句核对） | 直接：三问 → 人物清单三栏；"不推进剧情的场是多余的"→ 删除测试；**间接**：从整场挪到每一行、与正文逐字核对（`[推论]`） | 由复核框架升为事件轨结构依据 |
| S12 | 官方文字稿 | 一手创作方法 | 是（2026-09-23） | 间接：整片人物弧 → 单场"怕失去什么"栏（`[推论]`） | 新增 |
| S13 | 作者本人网站 | 一手创作方法 | 是（2026-09-23 重读，第 4、6、8 步核对） | 直接：写一场戏要先问地点与长短；**间接**：→ 地点作为变化的属性、"≥30 s 至少两次变化"（`[推论]`；3.6 的"全场一个画面须登记理由"已撤） | 新增 |
| S14–S19（2026-09-26） | 官网 / 官方文字稿 / 官方节选；《Story》节拍定义为 Goodreads 标注 | 一手（《Story》标注为二手） | 是：子代理取全文（WebFetch 失败处用 curl 取 HTML），主会话对 Criterion 节选、Slogans、McKee 三页、Scriptnotes 357 / 609 / 728 / 735 的关键句逐句 grep 核对 | 直接：非事件、互相说都知道的事、弹药、被动、外语测试、障碍逼出新战术、shoe leather；**间接**：→ 设计卡五格与复述阈值（`[推论]`） | 新增 |


脚本输出（终端与 `--json` 的 `basis` 字段）对每个问题同步标注：判断依据哪几条来源、阈值与代理量属于 `[推论]`。

## 五、未采用 / 未读到

- Robert McKee, *Dialogue* (2016)：3.3.0 时只找到第三方转载页且访问被拒；2026-09-26 读到官方书页（见 S14 与下文），书中正文仍未读。
- Grice, "Logic and Conversation" (1975)：公开 PDF 访问失败，本次未读；"下一句与上一句相关"已由 S1 §4.8 覆盖。
- Clark & Marshall 1981（定语指称与共有知识）、Levinson 1983 *Pragmatics* 第 4 章（预设触发语）：未读原文；"你的 X / 那个 X / 还"这组触发语只按 S10 的共同基础原理列为 `[推论]`，不引用这两本。
- BBC Writersroom 格式指南：未取得官方 PDF；O.S. / 画外标注按剧本页模板的括号约定识别，不引用格式规范。
- S2–S4 是真实会话语料（电话闲聊、日常问答）：只用来防"一人一句人设短句"这一头，不作屏幕对白的目标——真实会话满是接话与复述，屏幕对白要压缩（S5 后半）。
- 没有中文会话语料的句长数据；中文台词只做来回 / 收件人 / 画外统计，句长与主谓宾指标不计算（脚本会在信号里说明）。
- Mackendrick《On Film-making》的"Activity versus Action"一章与"dialogue as action"原文：只找到盗版 PDF，未打开；"活动与行动"的区分在 `scene-design.md` 里用 McKee"有活动但没有价值变化"（S14）与 Odets"演处境"（S15）表达，不引用该章。
- McKee *Dialogue* (2016)：官方书页已读（S14），书中样章嵌在页面里取不到；该书编者之外，Mackendrick 的编者 Paul Cronin 建议学生远离此书——只引书页一句，不引书中方法。
- UCB《Comedy Improvisation Manual》："game of the scene / heightening"只读到课程页与第三方访谈，未读原书，不引用。
- Hitchcock / Truffaut"photographs of people talking"：只见 Goodreads 引语页，书页扫描不可取，不引用。
- BBC Writersroom、Vulture、NYT、Guardian：本次检索工具无法访问，未读。
- Scriptnotes 753（Aaron Sorkin，2026-09-22，"写冲突"专题）：文字稿尚未发布，只读到节目页，不引用。
