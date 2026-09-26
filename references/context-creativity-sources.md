# 方法研究与迁移边界（1.1.0 · 3.0.0）

检索与访问：2026-09-07。以下只转述与本次设计直接有关的发现，不复刻原作者故事，也不把研究结果等同于此 Skill 的效果。日常创作按缺口读取，无需每次打开本文件。

| 来源与已读范围 | 专业发现 | 本地实现（设计推论） | 局限/反例 |
|---|---|---|---|
| [John August, How to write a scene (2007)](https://johnaugust.com/2007/write-scene)，正文第 1、2、5、7–10 步 | 场景应联系全片需要；进入方式承接前场，也允许探索意外与先写草稿 | `story-context.md` 开写前定位作用与前后文；`creative-search.md` 以实际片段探索选择 | 原文删除标准不直接变成硬门槛；观察、韵律与关系积累也可成立。意外不能破坏本片硬锁 |
| [Céline Sciamma, BAFTA Screenwriters’ Lecture (2019)](https://www.bafta.org/media-centre/press-releases/screenwriters-lecture-series-2019-celine-sciamma/)，官方文字稿 wanted/needed 场景、无冲突张力与叙事连接段 | 必要场景也应有创作者想拍的体验；欲望与关系可以承载张力 | `creative-search.md` 把过桥信息发展成具体交流与体验；同时检验全片作用与局部吸引力 | 作者实践不等于所有类型通则；允许强冲突、商业叙事和直白表达 |
| [Yang et al., Re3 (EMNLP 2022)](https://aclanthology.org/2022.emnlp-main.296/)，摘要及[论文](https://aclanthology.org/2022.emnlp-main.296.pdf)方法部分 | 生成长故事时反复引入整体计划与当前故事状态，再检查续文相关性和事实一致性 | `story-context.md` 每场重建有效依据，写后核后果，采用后保留变化量 | 原研究是特定模型的英文长故事生成系统；这里没有复现其控制器，不引用原研究增益作为版本成绩 |
| [Yang et al., DOC (ACL 2023)](https://aclanthology.org/2023.acl-long.190/)，仅摘要；PDF 本次读取失败 | 更细的层级大纲与生成控制共同服务长程情节一致性 | 区分整体承诺、本场任务、后续依赖；有复杂因果时细化，不要求每场先写完整大纲 | 摘要不能支持实现细节；本 Skill 保留片段先行与授权回流，不把大纲当永不可变的事实 |
| [Liu et al., Lost in the Middle (TACL 2024)](https://aclanthology.org/2024.tacl-1.9/)，摘要及[论文](https://aclanthology.org/2024.tacl-1.9.pdf)§2–4 的任务与位置效应 | 在多文档问答与键值检索实验中，相关信息的位置会影响使用效果 | 按当前场所需检索远处依据，压缩时保留限定词、来源和状态，恢复时回读原文 | 不是剧本实验，也不是当前所有模型的性能结论；摘要或把规则再放一次不能保证不遗忘 |

研究转化为两项可检查行为：**动笔前能指出本场依赖什么；新增戏份能在正文中体现收益且不破坏依赖。** 自动测试只负责代码与资源契约；非盲走查记录在 `../tests/acceptance-1.1.0/`，独立创意比较沿用 `../tests/creative-eval.md`，不能混称。

## 好莱坞与韩国编剧实践：新增落地来源

以下均于 2026-09-07 读取。访谈中的作者发言作为一手材料，采访者的概括不冒充作者原话；译文只用于理解方法，不直接充当中文对白。方法步骤是本地推论，见 `screenwriting-methods.md`，不代表该地区的普遍规则。

| 编号 / 来源 | 已读定位与发现 | 进入方法及边界 |
|---|---|---|
| H1 [John August, How to write a scene](https://johnaugust.com/2007/write-scene) | 第 1、2、5、7–10 步，场景作用与入口探索；同上表已读正文 | 全片作用与本场体验共同判断；不照搬固定数量或严格删除标准 |
| H2 [Tony Gilroy, BAFTA 2013 官方讲稿](https://www.bafta.org/media-centre/press-releases/screenwriters-lecture-series-2013-tony-gilroy/) | human behaviour、empathy、journalism 及 outline 段：理解各角色的行为复杂性、深入具体处境 | 从每个人的处境理解选择；不把研究当作证明虚构人物存在，也不强制其大纲流程 |
| H3 [Craig Mazin, Scriptnotes 403 (2019)](https://johnaugust.com/2019/scriptnotes-ep-403-how-to-write-a-movie-transcript) | structure、central dramatic argument、internal/interpersonal/external 段：人物对核心问题的关系影响结构 | 让选择后果改变后续行动；不采纳每部作品必须论辩或成长的普遍断言 |
| K1 [奉俊昊 / Alex Rose, Cult MTL 访谈 (2019)](https://cultmtl.com/2019/10/bong-joon-ho-parasite-interview/) | 正文中生活条件、人物灰度、房屋视线与偷听位置的作者回答 | 空间/资源参与因果，日常不对等产生不同后果；不照搬原片空间或人物阶层符号 |
| K2 [朴赞郁 / Hans Ulrich Obrist, MUBI Notebook 访谈 (2023)](https://mubi.com/en/notebook/posts/combining-the-past-and-the-future-a-conversation-with-park-chan-wook) | detective/love/responsibility 回答：感情与职业责任的牵引 | 同一任务承担关系与事件；不是对原作爱情/案件设计的复刻 |
| K2/K3 [郑瑞景 / KIM Subin, KOFIC 访谈 (2022)](https://www.koreanfilm.or.kr/eng/news/interview.jsp?blbdComCd=601019&mode=INTERVIEW_VIEW&pageRowSize=10&seq=439) | 读取官方英文正文：melodrama/investigation、literary style、12-episode drama 回答；网页工具失败后用 HTTP 读取原页成功 | 同一工作过程传递理解，措辞由语言经历与语境决定；不把个体观察外推为警察或非母语者通则，也不把长片时长公式放大成剧集 |
| K4 [李沧东 / Dennis Lim, Film Comment Cannes 访谈 (2018)](https://www.filmcomment.com/cannes-interview-lee-chang-dong/) | 已读公开问答中 ambiguity/internal motivations、dusk/uncertain line 段 | 未定事实不擅自落定，人物仍有行动依据；不以“暧昧”掩盖遗漏因果 |

未采用：RogerEbert.com 的奉俊昊访谈本次返回 403，改用可读的一手访谈核对；没有据搜索摘要补写该访谈观点。没有观看采访视频，不声称验证语速、停顿或表演效果。


## 3.0.0 新增来源（2026-09-19）

围绕实际观测到的问题检索：一季故事与分集框架中段换景不换机制、分集像摘要、正文否定句多于事件、隐瞒 / 误会缺理由、对白只有诊断没有正向工艺。以下均为本次直接访问；`[一手]` 指作者本人文字或访谈原话，`[第三方]` 指媒体或行业文章；转成条件式操作是本 Skill 的设计推论 `[推论]`。

| 来源与已读范围 | 来源原意（近原话） | 本地采用 | 局限 / 不采用 |
|---|---|---|---|
| [Trey Parker & Matt Stone, NYU 写作课，Speakola 文字稿](https://speakola.com/arts/matt-stone-trey-parker-nyu-writing-class-2014) `[一手文字稿]` | 大纲的 beats 之间若是 "and then" 就完了；应是 "therefore" 或 "but"；他们会把 beats 写出来检查因果 | `story-engine.md` §一 第三行、`episode-design.md` §二 集内集间检查 | 原话针对喜剧动画的大纲；不推为每场必须有转折 |
| [Craig Mazin, Scriptnotes 403 文字稿](https://johnaugust.com/2019/scriptnotes-ep-403-how-to-write-a-movie-transcript) `[一手文字稿]` | "Fear is our connection to a character"；每场从一个真相开始、发生事、以新真相结束 | `story-engine.md` §六 期待的建立 | 1.1.0 已用其 central dramatic argument；本次只取观众连接一段 |
| [Vince Gilligan / Neil Landau, Filmmaker Magazine 2014](https://filmmakermagazine.com/84504-its-better-to-be-somebody-negative-than-nobody-breaking-bads-vince-gilligan-on-walter-white/) `[一手访谈]` | 编剧室问 "Where is Walt's head at? What does he want right now? What is he afraid of?"；不按 A/B/C 线想；"give the audience just enough… keep them right on the edge" | `story-engine.md` §四 触发链、§六 信息刚够 | 长剧编剧室经验；不推为短剧不能有 B 线 |
| [Scriptnotes 478 The One Hour Drama 文字稿](https://johnaugust.com/2020/scriptnotes-episode-478-the-one-hour-drama-transcript) `[一手文字稿]` | Creasey："what is episode 100?"——很多 pilot 是好电影不是剧；段落结尾落在问题上，下一段回答 | `story-engine.md` §一 第二行、`episode-design.md` §四 | 商业电视的 act 长度规则不采用 |
| [David Mamet 致 The Unit 编剧备忘录，No Film School 转载全文](https://nofilmschool.com/2010/10/david-mamet-drama-a-memo-the-unit-writers) `[一手备忘录 / 转载]` | "WHO WANTS WHAT? WHAT HAPPENS IF THEY DON'T GET IT? WHY NOW?"；观众不为信息收看 | `character-scene-development.md` §五 潜台词段、`episode-design.md` §一 进入 | 备忘录语气绝对（"两人谈第三人即烂场"）；本 Skill 只取三问作检查，不采用其禁令 |
| [Jacob Tierney / Brendan Brady, TheWrap 季终访谈](https://www.thewrap.com/creative-content/tv-shows/heated-rivalry-episode-6-jacob-tierney-brendan-brady-interview/) 与 [Collider 访谈](https://collider.com/heated-rivalry-finale-episode-6-explained-book-changes-season-2-creator-jacob-tierney/) `[一手访谈]` | 末集无冰球，"if these two have chemistry, I can just point a camera"；亲密里保留竞争与玩笑；"you're doing a disservice… endlessly trafficking the will-they-or-won't-they"；最后四分钟不给 logistical information | `story-engine.md` §三 确认后的张力、`episode-design.md` §一 牵引行 | 单一作品的选择；不推为所有爱情剧都该早确认或末集都无类型戏 |
| [Alice Birch, Awards Daily 访谈](https://www.awardsdaily.com/2020/08/22/alice-birch/) `[一手访谈]` + [The Ringer 分析](https://www.theringer.com/2020/04/29/tv/normal-people-hulu-bbc-sally-rooney) `[第三方]` | 保留 miscommunication 而不解释；"everyone always has a reason to speak"；亲密场面要具体 | `story-engine.md` §四 隐瞒需要理由、`character-scene-development.md` §五 | 该剧的不沟通有阶层与羞耻作依据，是分析推断；不推为"误会都可以" |
| [John August, Writing for microdramas (2025-09-24)](https://johnaugust.com/2025/writing-for-microdramas-aka-verticals) `[一手匿名投稿]` | 微短剧写作被"reverse-engineered around data-driven formulas… fill-in-the-blanks puzzle"；前十章反复改到失去乐趣 | `episode-design.md` §四 平台公式的边界 | 两位匿名写手的经历，不代表全行业 |
| 中文短剧培训文章（如[网易号"单集万能节奏公式"](https://www.163.com/dy/article/L30RCS1005340TH8.html)）`[行业文]` | 3 秒钩子、每集卡点、爽点间隔 | 作为**不采用**的对照写入 `episode-design.md` §四 | 平台付费转化习惯，非叙事规律；数字会变 |
| [郑瑞景 KOFIC 访谈](https://www.koreanfilm.or.kr/eng/news/interview.jsp?blbdComCd=601019&mode=INTERVIEW_VIEW&pageRowSize=10&seq=439) `[一手访谈]`（重读） | 12 集剧起初只想成两集就写完了；12 小时"可以写一个季节"；调查过程本身产生感情 | `story-engine.md` §二 一个选择支付两条线 | 1.1.0 已引 K2/K3；本次只补长度感 |

未读到 / 未采用：Richard Curtis BAFTA 2013 讲座（bafta.org 返回 403，未读原文，不引用其观点）；BBC Writersroom 连续剧写作指南（未找到公开文本）；Harmon story circle、Truby、Yorke 等在已回滚的 1.3.x 中引用过的方法本次未重新核实，不写入正文。

内部证据：一季故事 v1 → v2 的用户反馈表（空间单一、球员魅力不足、人设不讨喜、身份与生活薄、感情幼稚无事件推动、调研没转为创作）与 v2 分集框架文本中"没有……也没有……"密度，是 `story-engine.md` §七、硬规则 8 与 `episode-design.md` §二 的直接依据；项目正文不进公共仓库。

## 4.0.0 新增来源（2026-09-26）

触发：用户"台词重复、无意义对白多、剧本剧情设计能力弱、画面单调；非常严重"。对照 Offset EP01、THE ORDER EP04、reckless EP02 的实际剧本后，问题定位为流程：强制的是记账（事件轨、删除测试、review），造戏的方法全是可选项，而且由写稿的同一上下文自评。下列研究由调研子代理读 arXiv HTML 全文（PDF 抓取失败），主会话对关键句逐句 grep 核对；结论搬到剧本写作一律是 `[推论]`。编剧方法类来源登记在 `dialogue-review-sources.md` S14–S19。

| 来源与已读范围 | 来源原意（近原话） | 本地采用 | 局限 / 不采用 |
|---|---|---|---|
| [Chakrabarty et al., "Art or Artifice? Large Language Models and the False Promise of Creativity", CHI 2024](https://arxiv.org/abs/2309.14556)（HTML 全文） | 专家设计的 TTCW 测试上，LLM 故事通过的项目比职业作家少 3–10 倍；专家评语：AI 对白缺潜台词，靠直接的、交代性的对白，人物过度解释处境与情绪；LLM 当评审时与专家评估的相关"close to zero" | `cold-read.md`：自评不能当验收；冷读只作线索；验收用双序配对（`scripts/blind_eval.py`） | 小说短篇、2023 年的模型；不是剧本 |
| [Chakrabarty, Laban & Wu, "Can AI writing be salvaged?", CHI 2025](https://arxiv.org/abs/2409.14509)（HTML 全文） | LLM 写作七类毛病（陈词、不必要 / 冗余的交代、紫色文风、句式差、缺具体、措辞别扭、时态不一）；即使提示里明确要求避免陈词，每隔一篇仍满是陈词；检测问题片段不是瓶颈，重写才是；"不必要的交代"一类更大的问题是把潜台词说破，多句片段 LLM 改不到作家的水平；先检测再重写的独立一轮能把平均名次从 2.51 提到 1.99（作家改稿 1.5） | `scene-design.md` 开头：禁令写进提示挡不住，结构在写之前定；冷读后只定点改被标出的片段；潜台词问题回设计卡而不是逐句润色 | 段落级写作；排名由专家给出，样本为 GPT-4o 段落 |
| [Mirowski et al., "Co-Writing Screenplays and Theatre Scripts with Language Models" (Dramatron), CHI 2023](https://arxiv.org/abs/2209.14958)（ar5iv 全文） | 分层生成 logline → 人物 → 情节节拍 → 地点 → 对白；业内评审：只是在"告诉"，像即兴里说的"do not mention the thing"；要找的是主角的目标和阻碍那股推动力；人物一上场就把想要的直说出来；各场对白并行生成，不知道上一场说过什么，出现对白循环 | 设计卡写推动者、阻力、转折，而不是"这场要交代什么"；观众账本与 `review_script.py --context` 复述检查：写本场前看前几场说过什么 | 2022 年的模型；评审是 15 位业内人士的访谈，不是盲测 |
| [Huot et al., "Agents' Room: Narrative Generation through Multi-step Collaboration", ICLR 2025](https://arxiv.org/abs/2410.02603)（HTML 全文） | 冲突 / 人物 / 场景 / 情节四个规划代理写进共享草稿，再分段写作；人评在各维度都偏好这种写法；只做规划、最后由一个简单代理收尾的变体效果不好；单次调用里先规划或先反思的基线表现较差；LLM 评审用配对比较，交换顺序后 90.2% 仍选同一篇，与人评显著相关；人写的故事仍胜过所有系统 | 设计卡是规划，正文按设计写；验收用配对比较并交换顺序（`creative-eval.md` §八） | 规划与写作分给多个代理的结构本 skill 未照搬（一个会话写）——`[推论]`：至少让规划先写下来、约束后面的正文 |
| [Huang et al., "Large Language Models Cannot Self-Correct Reasoning Yet", ICLR 2024](https://arxiv.org/abs/2310.01798)（HTML 全文） | 没有外部反馈时，LLM 很难自我纠正，纠正后有时更差；把反馈直接放进最初的指令，效果比事后纠正好 | 硬规则 10：写之前先设计（要求放进规划，而不是写完再改）；自检只是线索 | 研究的是推理任务；局限一节也提到自我纠正对改文风有效 |
| [Panickssery, Bowman & Feng, "LLM Evaluators Recognize and Favor Their Own Generations", NeurIPS 2024](https://arxiv.org/abs/2404.13076)（HTML 全文） | LLM 评审给自己的输出打分更高，而人工标注认为质量相当；自我识别能力与自我偏好强度线性相关；交换选项顺序后，GPT-4 / GPT-3.5 / Llama 有 25% / 58% / 89% 会改判 | 冷读用新上下文、看不到作者理由；配对评审必须正反两序、两次一致才计胜负 | 摘要任务，不是小说或剧本 |
| [Zhang et al., "Verbalized Sampling", 2025](https://arxiv.org/abs/2510.01171)（HTML 全文）；[Padmakumar & He, ICLR 2024](https://arxiv.org/abs/2309.05196)（仅摘要） | 传统单实例提示的众数回答趋向刻板；让模型先列出多个回答及其概率，创意写作多样性提高 1.6–2.1 倍、人评提高 25.7%；与指令微调模型合写会降低内容多样性 | 核心一步三选一：第一稿是最典型的写法（"主角收到消息"），先列三种再选 | 会议信息按子代理核对为 ICML 2026，本会话未另核；Padmakumar & He 只读了摘要 |
| [Tian et al., "Are Large Language Models Capable of Generating Human-Level Narratives?", EMNLP 2024](https://arxiv.org/abs/2407.13248)（HTML 全文） | LLM 故事同质地偏正面、缺张力；转折点来得早，悬念与挫折少；把转折点与故事弧的特征明确写进提示，多样性、悬念与唤起度提高 40% 以上 | 设计卡"转折：预期 → 结果"；`story-engine.md` §一"剧情靠宣布推进"一行 | 叙事层面的分析，不是单场 |
| [Chakrabarty, Laban & Wu, "AI-Slop to AI-Polish?", 2025](https://arxiv.org/abs/2504.07532)（HTML 全文） | 零样本 LLM 判断写作质量接近随机（50% 基线上下几个百分点）；推理模型不显著更好；从多个候选里用训练过的奖励模型选最好的一个，专家排名优于随机选与初稿 | 不把 LLM 打分当效果证据；双序配对只作辅助，用户在生产中终审（用户 2026-09-26 定） | 会议信息未核实（arXiv 标"Under Submission"） |
| [Chen et al., "HoLLMwood", Findings of EMNLP 2024](https://aclanthology.org/2024.findings-emnlp.474/)（HTML 全文） | 基线对白"robotic and boring"；让不同 LLM 分别扮演各个人物对趣味性贡献最大 | 只作旁证：对手不配合（每个人带自己的算盘） | 评估只有 GPT-4 配对比较，没有人评——证据弱 |
| [EQ-Bench Creative Writing v3 方法页](https://eqbench.com/about.html) `[基准方法说明，非同行评审]` | LLM 评审在配对判断里强烈偏好更长的输出；容易被词汇炫技和表面的精致打动；按评分表打分偏差少但区分度低 | 双序配对评审指令里写明"长度不是优点"，并要求引原句为证 | 实践者说明 |

未读 / 未核实：Pan et al. 关于迭代自我修订中奖励投机的论文（只见引用）；Padmakumar & He 全文；AI-Slop 的会议信息。

