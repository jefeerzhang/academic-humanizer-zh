<!--
Layer 7: Academic Injection Layer (学术注入层 — v0.7.0 起默认停用固定短语注入)
Fork extension v0.5.0; fixed-phrase injection disabled by default in v0.7.0.

Why disabled:
  - Injecting stock phrases ("笔者认为", "样本限制使…需谨慎对待", "目前尚不清楚")
    introduces a new template-AI tell and tempts fabricating ungrounded limitations (C1).
  - Voice calibration now uses Layer 5 + `scripts/compare_author_style.py` against
    the author's own historical writing sample.

This file remains as a legacy safety-guard reference (blacklists, forbidden sections,
meta-label leak checks) for `scripts/validate_layer7_injection.py`.
-->

# Layer 7 · 学术注入层（v0.7.0 起默认停用固定短语注入）

> **当前状态（v0.7.0）**：**默认停用固定短语注入**。向稿件塞入「笔者认为 / 样本限制使……需谨慎对待 / 目前尚不清楚」等固定短语会制造新的模板 AI 味，且容易编造原稿没有的解释与局限（违反 C1）。
> **替代方案**：按 `SKILL.md` Layer 5，用作者真实历史论文或草稿作为样本，运行 `scripts/compare_author_style.py` 对齐句长节奏、自称体系、连接词与自然限定密度。
> **本文档保留用途**：仅作为遗留稿件或显式审计时的安全防线（黑名单、禁区落点、元标签泄漏检查），配套 `scripts/validate_layer7_injection.py`。**C0–C2 红线始终最高优先级**。

---

## 7.0 状态与路由

路由决策以 `SKILL.md` 的 "Document-style routing" 为单一权威：默认不再自动加载或触发固定短语注入。作者提供历史样本时，一律走 Layer 5 + `scripts/compare_author_style.py`。

仅当需要审计遗留稿件或检查是否存在不当注入时，按以下规则运行 `scripts/validate_layer7_injection.py`：若稿件中已存在学术留白或第一人称，必须限定在 `Discussion / Conclusion / Limitations / 政策含义`，且不得出现正文元标签泄漏（如「在 Discussion 段，」）或单段堆砌固定句式。

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
| 用"挺""蛮"插入严肃文体 | 摘要里出现封闭词表中的口语强化（挺好 / 挺多 / 挺不错 / 挺不好 / 蛮好 / 蛮不错 / 蛮不好） | 学术 register 倒退；任意「挺身而出」「蛮不讲理」不在此列 |
| 模仿小红书体 | "绝绝子""家人们""YYDS" | 完全禁止 |
| 段尾强加"未来依然可期" | 末段"未来值得期待""前景广阔" | 抒情收尾，违反 rules-zh.md §1-A |
| 电报体 | 把所有长句切成 5–10 字短句 | 学术段落需要条件状语，强行切碎失信息密度 |

---

## 7.7 完成判据（核对清单）

修改完成后，按本清单过一遍：

- [ ] 全文第一人称 ≤1 处，且仅在 Discussion / Conclusion / Limitations / 政策含义
- [ ] cognitive hedging 仅出现于 Discussion / Conclusion / Limitations / 政策含义，未污染 Results / Methods / 摘要 / 引言
- [ ] 全文未出现「我认为 / 我觉得 / 我感觉」等口语第一人称
- [ ] 全文未出现 emoji、未出现小红书体、未出现口语强化封闭词表（挺好 / 挺多 / 挺不错 / 挺不好 / 蛮好 / 蛮不错 / 蛮不好）
- [ ] C0–C2 红线（数字、引用、命名术语）一字未动
- [ ] 正文未泄漏结构元标签（如「在 Discussion 段，」），单段未堆砌 ≥3 条固定模板句式
- [ ] 跑 `scripts/validate_red_lines.py` 退出码 0（C0–C2 兜底）
- [ ] 跑 `scripts/validate_layer7_injection.py` 退出码 0（遗留注入安全防线）
- [ ] 提供作者样本时，跑 `scripts/compare_author_style.py` 对齐句长节奏、自称与连接词

**自动化审计**：`scripts/validate_layer7_injection.py` 对 before/after 对做 6 类防线检测：

1. 第一人称计数（≤1）
2. cognitive hedging 密度（≤3 处/千字）
3. 反人味陷阱黑名单命中（应为 0）
4. cognitive hedging 落点（仅 Discussion / Conclusion / Limitations / 政策含义）
5. C0–C2 红线委托 `validate_red_lines.py` 跑（退出码 0）
6. 模板泄漏防线（L7.5：禁止「在 Discussion 段」类标签泄漏进正文，警告单段堆砌 ≥3 条固定句式）

退出码：0 = PASS（含默认未激活跳过）；1 = WARN（密度或模板堆砌警告）；2 = FAIL（第一人称滥用 / hedge 落禁用段 / 黑名单 / 元标签泄漏 / C0–C2 红线破）。

---

## 7.8 与 `natural-chinese` 的边界

`natural-chinese` 是本 skill 的 sibling，承担通用中文润色（公众号 / 公文 / 商业 / 新闻 / 文学）。Layer 7 仅借用其「破+立双轨」中**学术场景合规的子集**（认知边界留白 + 第一人称限密度）；后三条人味工具（主观感受 / 读者对话 / 节制不完美）在学术场景保持关闭，避免破坏学术 register。完整路由决策见 SKILL.md "Document-style routing" 与 "Language routing"。

---

*本层不替作者做判断，只暴露「破+立双轨」在学术场景下的过滤版本。*
*C0–C2 红线仍由 SKILL.md 保护；本层不修改任何数字、引用、命名术语、论断结构。*