[README.md](https://github.com/user-attachments/files/28426499/README.md)
<div align="center">

# 🏠 小租同学

<p><strong>专为大学生打造的第一次租房小助手</strong></p>

📸 验房分析 · 💰 价格核验 · 📋 流程问答 · 🧮 费用全景 · 🗺️ 城市政策 · 🛡️ 女生安全

<p>
  <a href="#"><img src="https://img.shields.io/badge/版本-v5.0-4A90D9.svg?style=flat-square" alt="版本"></a>
  <a href="#"><img src="https://img.shields.io/badge/覆盖城市-全国-2ECC71.svg?style=flat-square" alt="覆盖城市"></a>
  <a href="#"><img src="https://img.shields.io/badge/评分维度-19-F39C12.svg?style=flat-square" alt="评分维度"></a>
  <a href="#"><img src="https://img.shields.io/badge/许可-MIT-27AE60.svg?style=flat-square" alt="许可"></a>
</p>

</div>

---

## 🎯 简介

第一次租房的大学生，面临巨大的信息差——中介说"精装修拎包入住"可能是甲醛超标的串串房，报价 3000/月你可能不知道同小区均价只要 2200。

**小租同学**就是帮你消除信息差的 AI 助手。七大功能模块：

| 功能 | 能做什么 |
|:--|:--|
| 📸 验房分析 | 上传照片/PDF，AI 识别 19 个问题，输出评分报告（可选 PDF 房源可租性评估报告） |
| 💰 价格核验 | 实时搜索同区域租金，判断价格合理/偏高/偏低 |
| 📋 流程问答 | 覆盖找房→签约→入住全流程，合同三级审查 |
| 🧮 费用全景 | 完整费用清单 + 自动算首月预算，隐藏费用全提醒 |
| 🗺️ 城市政策 | 实时查询目标城市租房政策、毕业生补贴 |
| 🛡️ 女生安全 | 选房/看房/入住/日常安全 + 防护设备清单 |
| ❌ 反模式与FAQ | 常见误用场景 + 11 个高频问题解答 |

---

## 🚀 快速开始

### 安装

将技能安装到 WorkBuddy 用户级技能目录：

```bash
~/.workbuddy/skills/小租同学/
```

或通过 WorkBuddy 客户端技能管理界面导入。

### 前置条件

- WorkBuddy 桌面客户端
- Python 3.8+（脚本运行时需要）
- 网络连接（价格核验和水电查询需要实时搜索）

### 首次使用

```
@小租同学 你好
```

### 常用命令

| 我想做什么 | 就这样说 |
|:--|:--|
| 分析房源 | `@小租同学` + 上传照片/PDF |
| 查租金 | `成都高新区一室一厅 2500 贵不贵？` |
| 算费用预算 | `北京朝阳区整租首月要准备多少钱？` |
| 查城市政策 | `深圳毕业生租房有补贴吗？` |
| 问安全事项 | `女生独自租房要注意什么？` |
| 审合同 | `@小租同学` + 上传合同 PDF |

---

## 📖 文档导航

| 文档 | 内容 | 面向 |
|:--|:--|:--|
| [**USER_GUIDE.md**](USER_GUIDE.md) | 完整用户手册（快速上手 + 功能详解 + 核心规则 + 能力边界） | 所有用户 |
| [SKILL.md](SKILL.md) | 技能路由入口（触发条件、模块路由、核心规则） | 开发者/AI Agent |
| [modules/](modules/) | 8 个功能模块（验房/价格核验/问答/费用/政策/安全/FAQ/对话引导） | AI Agent 按需加载 |
| [references/scoring-system.md](references/scoring-system.md) | 19 个评分维度 + 扣分/加分规则 | 了解评分体系 |
| [references/rental-guide.md](references/rental-guide.md) | 租房全流程指南（7 大主题） | 系统学习 |
| [references/contract-clauses.md](references/contract-clauses.md) | 合同条款三级审查 + 10 条必加条款 | 签约前对照 |
| [references/expense-checklist.md](references/expense-checklist.md) | 费用清单与预算计算参考 | 算预算时参考 |
| [references/xiongzhai-check.md](references/xiongzhai-check.md) | 凶宅查询方法论（内部参考） | 内部使用 |

---

## 🏗️ 项目结构

```
小租同学/
├── SKILL.md                    # 技能定义（路由入口）
├── README.md                   # 本文件
├── USER_GUIDE.md               # 用户手册（一站式指南）
├── modules/                    # 功能模块（按需加载）
│   ├── 验房.md
│   ├── 价格核验.md
│   ├── 问答.md
│   ├── 费用全景.md
│   ├── 城市政策.md
│   ├── 女生安全.md
│   ├── 反模式与FAQ.md
│   └── 对话引导.md
├── references/
│   ├── scoring-system.md       # 19 个评分维度 + 扣分/加分规则
│   ├── rental-guide.md         # 租房全流程指南（7 大主题）
│   ├── contract-clauses.md     # 合同条款三级审查 + 10 条必加条款
│   ├── expense-checklist.md    # 费用清单与预算计算参考
│   └── xiongzhai-check.md    # 凶宅历史查询方法论（内部参考）
└── scripts/
    ├── price_comparison.py     # 租金价格对比计算引擎
    └── generate_report.py      # 房源可租性评估报告 PDF 生成器
```

---

## ⚙️ 技术架构

### 数据流

```
用户输入
  ├── 照片/PDF → 格式识别 → 逐项评分 → 评分报告 → [可选] PDF报告
  ├── 价格查询 → WebSearch实时搜索 → 价格对比脚本 → 合理性判断
  └── 问答 → 知识库匹配 → [水电等需实时查询] → 结构化回答
```

### PDF 报告生成器

`scripts/generate_report.py` — 基于 ReportLab，自动检测系统中文字体：

```bash
python generate_report.py --json "@report_data.json" --output "report.pdf"
```

特性：
- 自动检测 Windows/macOS/Linux 中文字体
- ReportLab 未安装时自动静默安装
- 支持颜色分级标签（致命红/严重橙/一般黄/优势绿）
- 字体注册失败时打印明确警告

---

## 📝 更新日志

### v5.0 (2026-05-25) — 大赛优化

| 变更 | 说明 |
|:--|:--|
| 📖 文档整合 | 新增 USER_GUIDE.md 统一汇总用户可见内容（FAQ/反模式/核心规则/快速上手） |
| 🏷️ REF 摘要 | 4 个参考文档添加 100 字摘要 + 快速跳转链接 |
| 📐 README 精简 | 移除详细 FAQ/反模式，改为链接指向 USER_GUIDE.md |
| 📝 SKILL 增强 | 扩展触发词 20+ 条、新增端到端完整对话示例、房源链接解析 |
| 🔧 脚本优化 | 细化错误提示分类、完整特殊字符转义列表、重试次数增至3次 |
| 🏠 命名统一 | 统一为"房源可租性评估报告" |

### v4.0 (2026-05-22) — TRACE 评测修复

基于 SkillHub TRACE 五维评测体系全面修复：文档与实现一致性、中文字体失败警告、反模式章节、FAQ 章节、触发条件明确化、异常输入规范、对话引导视觉升级。

### v3.0 — 功能完善

新增凶宅查询、合同三级审查、水电燃气实时查询、PDF 报告生成。

### v2.0 — 基础功能

拍照验房（19 维度 + 100 分制）、价格核验（实时搜索）、租房全流程问答。

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源。

---

<div align="center">

**[📖 查看完整用户手册](USER_GUIDE.md)**  ·  **租房第一次，先问小租同学 🏠**

</div>
