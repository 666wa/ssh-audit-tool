---
name: ssh-audit
description: "SSH绕行稽核工具的开发、调试和使用指南。当需要进行SSH操作命令与报备表比对、IP匹配核查、调试匹配逻辑、性能优化、修改配置、新增模板或运行稽核任务时使用。触发关键词：SSH稽核、绕行核查、报备比对、IP匹配、4A绕行、账号违规、操作命令表、报备表。"
---

# SSH 绕行稽核工具

## 项目概述

Python 实现的 SSH 操作命令核查工具，将操作命令表与报备表进行三元组匹配（访问账号 + 本端IP + 对端IP），判断每条 SSH 操作是否已报备。

## 项目结构

```
ssh_audit_tool/
├── main.py           # 标准SSH稽核主程序
├── main_4a.py        # 4A绕行核实模板主程序
├── config.py         # 标准模板配置（文件路径、列名）
├── config_4a.py      # 4A模板配置
├── config_base.py    # 公共配置（结果标记、日志、共享常量）
├── fast_auditor.py   # 高性能审计器（默认使用）
├── auditor.py        # 标准审计器
├── parser.py         # SSH命令解析（CommandParser）
├── ip_matcher.py     # IP匹配（精确/IP段/CIDR/多IP混合）
├── file_handler.py   # 标准模板文件读写
├── file_handler_4a.py# 4A模板文件读写
├── date_extractor.py # 从文件名提取日期
└── utils.py          # 工具函数

run_audit.py           # 标准SSH稽核入口
run_audit_4a.py        # 4A绕行核实入口
run_audit_violation.py # 账号违规使用入口
```

## 三种稽核模板

### 1. 标准SSH绕行稽核（run_audit.py）
- 配置：`config.py`
- 操作表列名：`操作时间`、`资源IP`、`操作内容`、`主账号名称`
- 可选列：`从账号名称`（优先使用）、`资源名称`（备用IP来源）
- 匹配逻辑：解析SSH命令提取账号+对端IP，与报备表三元组比对

### 2. 4A绕行核实（run_audit_4a.py）
- 配置：`config_4a.py`
- 操作表列名（英文）：`op_fort_content`、`res_ip`、`main_acct_name`
- 可选列：`sub_acct_name`、`res_name`

### 3. 账号违规使用（run_audit_violation.py）
- 只核查IP对（本端IP + 对端IP），不考虑账号
- 操作表列名：`server_ip`（本端）、`dst_ip`（对端）
- 调用 `auditor.audit_violation_record()`

## 运行方式

```bash
# 标准SSH稽核
python run_audit.py -o 操作命令表.csv -r 报备表.csv

# 4A绕行核实
python run_audit_4a.py

# 账号违规使用
python run_audit_violation.py

# 通用参数
--output 指定输出路径
--no-timestamp 文件名不加时间戳
--log-level DEBUG|INFO|WARNING|ERROR
```

## 核心匹配逻辑

### FastAuditor（默认，config_base.py 中 USE_FAST_AUDITOR=True）
- 构建基于账号的哈希索引，按时间状态分类（有效/过期）
- `check_match_fast(account, source_ip, target_ip)` → (结果, 详情dict)
- `audit_record(operation_content, source_ip, default_account)` → (结果, 命中序号, 详细说明)
- `audit_violation_record(source_ip, target_ip)` → (结果, 命中序号, 详细说明)

### IP匹配（IPMatcher）
- 精确匹配：`target_ip == report_ip`
- IP段：`10.1.1.1-10.1.1.254`，支持多段连续 `-` 分隔
- CIDR：`192.168.1.0/24`
- 多IP混合：以中文顿号 `、` 分隔
- 内置 LRU 缓存和范围缓存

### SSH命令解析（CommandParser）
- `ssh user@ip`、`ssh -l user ip`、`ssh user ip`
- 检测无效格式：`ssh ip@user`、IPv6、中文句号、shell重定向
- `parse_ssh_command(command)` → `{account, target_ip, is_parseable}`

## 结果标记

| 标记 | 含义 |
|------|------|
| `已报备` | 三元组匹配成功且在有效期内 |
| `未报备` | 无法匹配 |
| `已报备但已过期` | 匹配成功但报备已过期 |
| `异常：非有效ssh命令` | 无法解析SSH命令 |
| `异常：无法获取有效本端IP` | 资源IP无效 |

## 输出列

原始数据 + 三列：`对比结果`、`命中序号`、`详细说明`

## 配置修改指南

修改默认文件路径：编辑对应模板的 `config.py` / `config_4a.py` 中的 `DEFAULT_*` 变量。

新增模板时：
1. 创建 `config_xxx.py` 继承 `config_base.py` 的共享常量
2. 如需特殊文件读取，创建 `file_handler_xxx.py`
3. 创建 `main_xxx.py` 和 `run_audit_xxx.py`
4. 复用 `FastAuditor`/`Auditor`、`CommandParser`、`IPMatcher`

## 调试技巧

调试单条记录匹配问题时，参考 `debug_record.py` 的模式：
```python
from ssh_audit_tool.fast_auditor import FastAuditor
from ssh_audit_tool.file_handler import FileHandler

report_df = FileHandler.read_report_table('报备表.csv')
auditor = FastAuditor(report_df, '2026-02-25')
result, details = auditor.check_match_fast('账号', '本端IP', '对端IP')
print(result, details)
```

## 性能优化要点

- FastAuditor 使用账号哈希索引 + 时间分类，优先匹配有效记录
- IPMatcher 使用 `lru_cache` 和类级别缓存
- 时间解析结果缓存避免重复解析
- 大数据集可考虑：分层早期退出、并行处理
