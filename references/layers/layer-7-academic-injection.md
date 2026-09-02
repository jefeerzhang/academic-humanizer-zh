<!--
Layer 7: Academic Injection Layer (学术注入层)
Fork extension v0.5.0. Bridges natural-chinese's "破+立" 双轨 into academic-humanizer-zh,
filtered for academic register.

Scope:
  - Loaded by SKILL.md "Document-style routing" ONLY when the input matches the
    "学术 + 口语化摘要 / 科普段落" branch (社科 abstract、科普段、humanities introduction).
  - Hard academic (CS/engineering paper、grant proposal) → Layer 7 does NOT activate.

This file is loaded ON DEMAND. Do not edit SKILL.md or rules-zh.md contracts because of it.
-->

# Layer 7 · 学术注入层（Academic Injection Layer）

> **一句话**：本层只引入 `natural-chinese` 的「破+立双轨」里**学术场景合规**的子集——「认知边界留白」与「第一人称限密度」——其余人味工具在学术场景下保持关闭。**C0–C2 红线不动**。

---

## 7.0 何时启用

参考 `SKILL.md` 的 "Document-style routing" 小节。仅当以下任一条件成立时启用本层：

| 输入特征 | 启用 Layer 7 |
|---|---|
| 含 `\cite{}` / `\citep{}` / `\begin{equation}` / `p < 0.0x` / `n = xxx` / `.bib` 文件指针 | ❌ 不启用，走 Layer 1–6 |
| 含 NIH Aims / NSF Project Summary / fellowship 结构标志 | ❌ 不启用，走 Layer 6 |
| 纯中文学术摘要 / 科普段，无上述硬学术标志，但段落含「摘要」「本文提出」「研究表明」「研究方法」「政策含义」 | ✅ **启用** |
| 用户口头说「摘要松一松」「科普段落自然化」「不要太死板」 | ✅ **强制启用**，无视自动判定 |

**正交关系**：Layer 7 与 Layer 5（voice/venue matching）正交——Layer 5 是 venue 适配，Layer 7 是 venue 之内的"立人味"工具。

---

## 7.1 总纲（破+立，但学术过滤）

`sibling` skill [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese) 的总纲：「破除机器味只是手段，立起人味才是目的。」

学术场景下：

- **机器味清不掉的部分**（价值判断词饱和、排比三件套、宏大叙事、套话收尾、抽象主语堆砌、动词名词化）：照 `references/rules-zh.md` 的病灶 A–F 清掉。
- **人味立得起的部分**：仅在以下两个工具里允许注入；其余三个工具在学术场景**保持关闭**。

---

## 7.2 学术豁免密度表

| 注入工具 | 学术密度上限 | 合规句式 | 禁用场景 |
|---|---|---|---|
| **认知边界留白**（academic hedging） | 1–3 处/千字 | "样本限制使…需谨慎对待" / "目前尚不清楚" / "倾向于将…归因于" / "这一发现有待…验证" | 全文主结论段、Methods、Results |
| **第一人称限密度** | ≤1 处/全文 | "笔者认为" / "本研究倾向于" / "我们倾向于将…归因于" | 摘要主结论、Methods、Results、关键数据陈述 |
| 主观感受 | **禁用** | — | 全部学术段落 |
| 读者对话 | **禁用** | — | 全部学术段落 |
| 节制不完美 | **禁用** | — | 全部学术段落 |

**关键判据**：

1. 全文第一遍扫「机器味」，按 `rules-zh.md` 病灶 A–F 处理。
2. 全文扫完之后，看是否已破 ≥3 处；是则**就近补一处人味**（不是机械 1:1）。
3. 学术 hedging 优先落到 Discussion / Conclusion / Limitations；避免落到 Results 的事实陈述。
4. 第一人称必须用「笔者认为 / 本研究倾向于」而非裸「我认为 / 我觉得」。

---

## 7.3 认知边界留白 · 句式库

下列句式在 Discussion / Conclusion / Limitations 段合法使用：

| 句式 | 适用场景 | 示例 |
|---|---|---|
| "样本限制使…需谨慎对待" | 受样本结构约束 | "692 名大学生的样本限制使结论对全国范围的推广需谨慎对待" |
| "目前尚不清楚…" | 因果链不全 | "碳标签对偏好的具体作用机制目前尚不清楚" |
| "倾向于将…归因于" | 多因解释 | "本研究倾向于将异质性归因于环保知识水平，而非收入差异" |
| "这一发现有待…验证" | 推广性限制 | "这一发现有待跨地区样本验证" |
| "在…条件下成立" | 边界条件 | "上述结论在样本为 18–25 岁本科生的条件下成立" |
| "不能排除…" | 反例存在 | "不能完全排除社会期望偏差的影响" |

**禁用**：
- 在 Methods 段使用上述任何一句 → 写作规约禁止
- 在 Results 段使用"目前尚不清楚" → Results 段只陈述观察到的事实
- 用"倾向于"修饰数据本身（如"数据倾向于表明…"）→ 这是过度 hedge，违反 C4

---

## 7.4 第一人称限密度 · 用法

仅限以下三种学术合规句式，且全文 ≤1 处：

1. **「笔者认为」+ 明确判断对象**
   > 笔者认为，这一差异主要源于受访者对"碳标签"的认知差异，而非对环保包装本身的偏好。

2. **「本研究倾向于」+ 解释性归因**
   > 本研究倾向于将该异质性归因于环保知识水平，而非收入或性别。

3. **「我们倾向于将…归因于」**（多作者论文）
   > 我们倾向于将结果的稳健性归因于变量度量的多维交叉。

**禁用**：
- 在 Methods 段使用"我们"做主语（应改为"本研究采用"）
- 在 Results 段使用"我们发现"（应改为"回归结果显示"）
- 全文出现 ≥2 次"笔者认为 / 本研究倾向于"
- 用"我觉得 / 我感觉"等口语形式

---

## 7.5 学术场景反人味陷阱（黑名单）

`sibling` skill `natural-chinese` 列了 6 条反人味陷阱。学术场景的过滤版：

| 陷阱 | 学术版本 | 为什么禁 |
|---|---|---|
| 在不确定处强加"我认为" | 在 Results 段塞"笔者倾向于" | 学术规约：Results 段不 hedge 主结论 |
| 用 emoji 替代语气词 | 在社科摘要用「🔥 / 💡」 | 完全禁止 |
| 用"挺""蛮"插入严肃文体 | 摘要里出现"挺""蛮""相当" | 学术 register 倒退 |
| 模仿小红书体 | "绝绝子""家人们""YYDS" | 完全禁止 |
| 段尾强加"未来依然可期" | 末段"未来值得期待""前景广阔" | 抒情收尾，违反 rules-zh.md §1-A |
| 电报体 | 把所有长句切成 5–10 字短句 | 学术段落需要条件状语，强行切碎失信息密度 |

---

## 7.6 启用判据（决策树）

```
[输入段落]
    │
    ├── 含硬学术标志（cite/equation/p-value/bib）──→ ❌ Layer 7 不启用
    │                                                   仅跑 Layer 1–6 + rules-zh.md 病灶 A–F
    │
    ├── 含 grant 标志（NIH/NSF/fellowship）──→ ❌ Layer 7 不启用
    │                                              仅跑 Layer 1–6 + Layer 6 grant mode
    │
    ├── 用户口头说"摘要松一松 / 科普段落自然化" ──→ ✅ 强制启用
    │                                                       提示用户："已启用 Layer 7 学术注入层；
    │                                                       仅注入 cognitive hedging + 第一人称限密度。"
    │
    ├── 自动检测到社科/人文/科普段 ──→ ⚠️ 询问用户是否启用
    │                                              「这段含'摘要/政策含义/研究方法'等学术段标记，
    │                                               是否启用 Layer 7 注入 cognitive hedging？」
    │
    └── 其他（无学术标记、无 grant、无硬标志）──→ ❌ 默认不启用
                                                          考虑重路由到 sibling skill `natural-chinese`
```

---

## 7.7 完成判据（核对清单）

修改完成后，按本清单过一遍：

- [ ] 全文第一人称 ≤1 处，且仅在 Discussion / Conclusion / Limitations
- [ ] cognitive hedging 仅出现于 Discussion / Conclusion / Limitations，未污染 Results / Methods
- [ ] 全文未出现「我认为 / 我觉得 / 我感觉」等口语第一人称
- [ ] 全文未出现 emoji、未出现小红书体、未出现"挺 / 蛮"
- [ ] C0–C2 红线（数字、引用、命名术语）一字未动
- [ ] 跑 `scripts/validate_red_lines.py` 退出码 0（C0–C2 兜底）
- [ ] 跑 `scripts/validate_layer7_injection.py` 退出码 0（注入密度审计）

**自动化审计**：`scripts/validate_layer7_injection.py` 对 before/after 对做 5 类检测：

1. 第一人称计数（≤1）
2. cognitive hedging 密度（≤3 处/千字，建议 1–3）
3. 反人味陷阱黑名单命中（应为 0）
4. cognitive hedging 落点（仅 Discussion/Conclusion/Limitations）
5. C0–C2 红线委托 `validate_red_lines.py` 跑（退出码 0）

退出码：0 = pass；1 = 警告（hedge 密度超标但未污染 Results/Methods）；2 = 失败（第一人称滥用 / hedge 落 Results / 红线破）。

---

## 7.8 与 `natural-chinese` 的边界

| 场景 | 用这个 skill |
|---|---|
| 中文学术摘要 / 科普段落（带"研究""方法""政策含义"标记） | **本 skill（academic-humanizer-zh）** + Layer 7 |
| 中文学术论文主体（Methods / Results / 严格 grant） | **本 skill**，**不启用** Layer 7 |
| 通用中文润色（公众号 / 公文 / 商业 / 新闻 / 文学） | **sibling skill [`natural-chinese`](https://github.com/jefeerzhang/natural-chinese)** |
| 英文学术 / grant proposal | **本 skill**，默认走英文规则集（Layer 1–6） |
| 中文 + 英文混排，且主导是英文 | **本 skill**，按 Language routing 走英文 |

跨 skill 边界：自然中文的 5 条注入工具（第一人称、认知边界、主观感受、读者对话、节制不完美）在学术场景只有前两条被 Layer 7 采纳；后三条保持关闭，避免破坏学术 register。

---

*本层不替作者做判断，只暴露「破+立双轨」在学术场景下的过滤版本。*
*C0–C2 红线仍由 SKILL.md 保护；本层不修改任何数字、引用、命名术语、论断结构。*