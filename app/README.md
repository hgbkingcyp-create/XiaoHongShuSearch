# 测试产品（闭环骨架）

「小红书·性格测试变现」的核心产品层：答题 → 打分 → 出报告。零依赖，纯 Python 标准库。

## 目录结构

```
app/
├── engine.py          # 打分引擎（纯函数，零依赖）
├── server.py          # HTTP 服务（标准库 http.server）
├── data/              # 结构化题库 + 报告（JSON）
│   ├── love.json      #   爱情观测试
│   └── career.json    #   职场潜力测试
└── static/
    └── index.html     # 答题前端（单文件）
```

## 运行

```bash
cd /Users/admin/xiaohongshu-ceshi/app
python3 server.py
# 浏览器打开 http://localhost:8000
```

## 接口

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/api/tests` | 列出所有测试 |
| GET | `/api/test/<id>` | 返回题库（不含结果）；记 start 事件 |
| POST | `/api/test/<id>/result` | 提交答案 → 返回**免费**结果（type/tagline/hook）；记 complete |
| POST | `/api/test/<id>/report` | 提交答案 → 返回**完整报告**；记 unlock |
| GET | `/api/stats` | 漏斗统计（start/complete/unlock + 转化率） |

## 如何新增一个测试品类

在 `data/` 下加一个 JSON，格式照抄 `love.json`：
- `questions`：每题一个 `{id, text, options:[{key,text}...]}`，key 用 A/B/C/D
- `results`：每个 key 对应一个结果，含 `type/tagline/hook/portrait/strengths/blindspot/advice`
- 计分规则：选 A/B/C/D 最多的一项命中（见 `engine.score`）

## 免费/付费拆分（已实现）

- `/result` 只返回免费的 `type/tagline/hook`
- 完整报告（`portrait/strengths/blindspot/advice`）在 `/report`
- 接微信虚拟支付时，只需在 `/report` 处加支付鉴权，前端「解锁」按钮先调起支付

## 埋点（已实现）

事件写入 `data/events.jsonl`，`GET /api/stats` 返回漏斗：start → complete → unlock + 转化率。

## 下一步（外部依赖）

- [ ] 部署到服务器（需 ICP 备案）+ 微信小程序外壳 + 虚拟支付（需个体户执照）
- [ ] 新增品类：直接跟 Claude 说，产出题库写进 `data/*.json`、笔记写进 `content/*.md`
