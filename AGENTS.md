# AGENTS.md — 给 AI 协作者的项目须知

> 你在这个仓库里工作时，先读这份文件。它是给 AI（Claude Code / 其他 agent）看的操作手册；人类看的总纲在 `README.md`，完整策略在 `执行手册.md`。

## 项目一句话

小红书「娱乐化性格/人格测试」变现：笔记种草 → 站内商品卡成交 → 模板化报告自动发货。AI 负责全部生产工作（题库、报告、笔记、代码、交付物），人只做发布和决策。

## 铁律（违反 = 封号风险，任何产出前先自查）

1. **内容红线**：只做性格/人格/MBTI/金钱观/爱情观/职场/社交测试。绝不出现：算命、占卜、八字、塔罗、风水、改运、招财、命理、合婚。标题必含「仅供娱乐」。不用「心理测评/心理咨询」名义（触发资质审核）。
2. **导流红线**：一切产出（笔记、评论回复话术、交付物文案）不得包含：外链、二维码、谐音暗号（薇/VX/+V）、「评论区扣1+私信」模式。CTA 只允许两种：点下方商品卡 / 搜店铺名进店。
3. **计价模型**：0.99 元引流款 + 3.8 元利润款。不要按 9.9-19.9 设计任何文案或流程。
4. **不要做的事**：不要引入第三方依赖（运行时只用 Python 标准库）；不要把 `app/data/events.jsonl` 提交进 git；不要用 `心理` `疗愈` `量表` 等词。

## 架构地图

```
app/
├── engine.py        # 打分引擎：Counter 计 A/B/C/D 最多者命中。纯函数，勿加副作用
├── server.py        # stdlib http.server。/result 只回免费字段，/report 回完整报告
├── static/index.html # H5 答题前端（预览/演示用；成交不依赖它，交付物是独立 HTML）
├── data/*.json      # ★ 唯一内容源。一个品类 = 一个文件，加文件即上架，零改代码
├── generate_deliverable.py  # 静态「试卷包」生成器 → deliverables/<id>.html
├── generate_interactive.py  # 场景互动版生成器（format=interactive 的 JSON）→ deliverables/
└── deliverables/    # 成品 HTML（自包含、零依赖、可打印）。这是发货内容，改它必须重新生成，勿手改
content/             # 小红书笔记弹药包（每品类一个 .md：题库+报告+3条笔记）
执行手册.md           # 策略总纲（v2.0）
```

## 数据契约（改 JSON 前必读）

`data/<id>.json` 字段：
- 基础：`id, title, category, subtitle, disclaimer`（disclaimer 固定「仅供娱乐」）
- `questions[]`: `{id, text, options:[{key:A|B|C|D, text}]}`
- `results[]`: `{key, type, tagline, hook, portrait, strengths[], blindspot, advice}`
  - `type/tagline/hook` = 免费层；`portrait/strengths/blindspot/advice` = 付费层
- 互动格式额外加：`format: "interactive"`、`intro`（开场旁白）、`theme:{sky1,sky2,glow,accent,text}`、每题加 `scene`（场景旁白）

## 标准工作流

**新增一个传统品类**：
1. 写 `app/data/<id>.json`（照抄 love.json 结构，12 题 × 4 类型，报告文案要「扎心 + 治愈」）
2. `cd app && python3 generate_deliverable.py` 生成交付物
3. 写 `content/<中文名>.md`（3 条笔记，CTA 用商品卡话术，参考现有文件）
4. `python3 server.py` 起服务人工过一遍，然后 `open deliverables/<id>.html` 检查
5. git commit + push

**新增一个场景互动品类**（优先方向，传播力更强）：
1. 选一个有画面感的容器隐喻（午夜列车、深夜便利店、电梯困境、荒岛……），把人格维度嵌入 8 个场景抉择
2. 写 JSON 时带 `format: "interactive"` + `intro` + `theme` + 每题 `scene`（参考 `train.json`）
3. `python3 generate_interactive.py` 生成 → 浏览器打开体验 → commit push

**质量标尺**（对标已验证的账号模型）：报告要让读者产生「这说的就是我」→ 截图发朋友圈。hook 句必须能单独当文案传播。

## 提交规范

- 直接提交到 `main`，身份：`Dameng <hgbkingcyp@gmail.com>`（仓库级 git config 已配好，勿改）
- commit message 用中文，一句话说明改了什么品类/什么层
- `deliverables/` 下的文件是生成物：改了 `data/` 必须重新生成并一起提交，保持两者同步
- 不要提交：`events.jsonl`、`__pycache__/`、本地临时文件

## 当前状态（2026-11-17）

已完成：4 传统品类 + 1 场景互动品类（train）、H5 + 埋点、双形态交付物、12 条笔记（已合规整改）。
进行中：个体户执照（店主线下办理）。
待做：小红书开店 + 商品类目实测（虚拟内容类目是已知最大不确定项，店开后立即验证）→ 上架 0.99/3.8 两档 → 场景化其余 4 品类 → 发笔记跑 P0 数据。

## 未决问题（遇到相关任务先问人，别自己拍板）

- 小红书店铺能否过「测试报告」虚拟类目审核 → 店开后实测才知道
- 笔记 CTA 里「下方商品卡」需要店铺开通后挂卡才成立；P0 阶段（未开店）发布时先删掉该句，只留话题互动钩子
