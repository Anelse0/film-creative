# 1.1.0 方法研究与迁移边界

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
