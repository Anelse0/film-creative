# 情绪索引：原始标签与写作用途分开

原文见 `../assets/emotion/prompts.json`、`../assets/emotion/mood_prompt.md`；所有“时间价值/写作辨别”均为本技能推导，完整注记见 `emotion-notes.json`。先读 `emotion-dramaturgy.md`，不按此表从表情判断心理。

| ID | 原名称 / 原类别 / 原强度 | 时间价值（推导） | 容易混淆的写作点 |
|---|---|---|---|
| 01 | Joy / Laughter / Joy / Explosive | 笑从受控转为释放，最后仍有余笑 | 角色笑不等于观众应笑；不把所有喜悦写成露齿 |
| 02 | Shock / Surprise / Explosive | 骤然张开与定住之间的停滞 | 震惊不同于逐渐想通；不能只靠瞪眼新增信息 |
| 03 | Terror / Fear / Explosive | 急促呼吸与持续无法释放 | 持续恐惧不必每拍更大；生存行动需有空间依据 |
| 04 | Rage / Anger / Explosive | 控制破口与向前施压 | 低声不是愤怒的默认终点；改编不能假称原文 |
| 05 | Disgust / Disgust / Medium | 收缩、后撤和转开形成拒绝 | 不能由皱鼻判断道德立场；生理与价值厌恶分开 |
| 06 | Crying / Sadness / Explosive | 呼吸断续后身体控制进一步失效 | 不是悲伤必哭；哭也可能是喜悦、疼痛或表演 |
| 07 | Pain / Wince / Physical / Explosive | 突然收缩后只部分缓解 | 不靠扭脸假装医学真实；无依据不诊断伤病 |
| 08 | Eye Roll / Social / Medium | 短暂撤回配合后留下平直注视 | 不是任何轻蔑的通用脸；谁看见决定关系后果 |
| 09 | Suspicion / Fear / Subtle | 注意集中却暂不判断 | 单侧眉毛不是测谎；保留猜测与事实差别 |
| 10 | Flirtation / Social / Subtle | 回望与稍作停留维持邀请 | 眼神不证明同意或爱意；不是所有亲密都调情 |
| 11 | Smug / Gloating / Social / Medium | 缓慢显露优越感并保持接触 | 与自我满足的骄傲不同；优越也可能只是他人误读 |
| 12 | Boredom / Physical / Subtle | 注意力逐渐流失，动作趋于停滞 | 不是疲惫的诊断；角色无聊不等于场景应无聊 |
| 13 | Confusion / Surprise / Medium | 寻找解释却迟迟无法收敛 | 不能为拖延让角色无故听不懂；与震惊不同 |
| 14 | Realization / Surprise / Medium | 理解落地后重新聚焦 | 领悟可以错误；不把推测悄悄写成真相 |
| 15 | Awe / Wonder / Joy / Medium | 逐渐开放、向对象靠近 | 不是瞬时惊吓；惊叹也不必增加奇观预算 |
| 16 | Determination / Drive / Medium | 呼吸与身体重新组织成行动准备 | 咬紧牙不构成选择；不能靠点头完成整个人物弧 |
| 17 | Frustration / Anger / Medium | 用力逐渐转为败意与泄气 | 不强迫立刻振作；与持续愤怒有不同方向 |
| 18 | Anxiety / Fear / Medium | 注意游移与未能安定的节律 | 小动作不证明焦虑；恐惧可能有眼前明确对象 |
| 19 | Sadness / Sadness / Subtle | 细小失守后状态仍未消散 | 不等于低强度内心；不必走向哭泣 |
| 20 | Guilt / Sadness / Subtle | 话到口边受阻，之后回避 | 低头不证明有罪；与羞耻、尴尬及恐惧要靠语境区分 |
| 21 | Embarrassment / Social / Medium | 社交自信内收，尝试维持表面 | 红脸不是普遍可见表现；不能从脸色断言内心 |
| 22 | Exhaustion / Physical / Subtle | 恢复变慢，保持清醒也费力 | 疲惫不是懒惰或不关心；不统一写成长叹 |
| 23 | Relief / Joy / Medium | 先呼出压力，笑意在其后出现 | 宽慰不等于和解；危险只暂缓时不写彻底安全 |
| 24 | Pride / Drive / Subtle | 满意逐渐稳定，身体舒展 | 与优越感区分；微笑不是每种自豪的必要动作 |
| 25 | Nervous Fake Smile / Social / Subtle | 维持笑的表面与别处紧张不同步，掉落后补回 | 不强配吞咽；假笑可出于礼貌并非欺骗 |

选择情绪时先找角色处境；混合情绪不等于把多个 prompt 连接。原文查询无需默认加载全库；按 ID 或关键词取相应条目。库外状态允许原创，不能新增到原始25条里。
