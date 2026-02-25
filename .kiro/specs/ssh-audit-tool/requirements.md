# Requirements Document

## Introduction

本系统是一个SSH命令核查工具，用于验证实际执行的SSH操作命令是否在报备表中存在记录。系统通过比对操作命令表和报备表中的关键信息（访问账号、本端IP、对端IP），自动判断每条SSH操作是否已完成报备，并生成包含核查结果的输出文件。

## Glossary

- **操作命令表（F1）**: 记录实际执行的SSH操作命令的Excel文件，包含操作时间、账号信息、资源IP、操作命令等字段
- **报备表（F2）**: 记录已报备的主机互访信息的Excel文件，包含访问账号、本端IP、对端IP、端口、时间范围等字段
- **访问账号**: SSH命令中使用的用户名（如cmhop、omm等）
- **本端IP**: 发起SSH连接的源IP地址（资源IP）
- **对端IP**: SSH连接的目标IP地址，从操作命令内容中解析
- **核查结果**: 比对后的判定结果，包括"已报备"、"未报备"、"-"（无法解析IP）
- **System**: SSH命令核查系统

## Requirements

### Requirement 1

**User Story:** 作为数据分析人员，我希望系统能够读取Excel格式的操作命令表和报备表，以便进行后续的数据比对分析。

#### Acceptance Criteria

1. WHEN 用户提供操作命令表文件路径 THEN THE System SHALL 读取Excel文件并解析所有必需字段
2. WHEN 用户提供报备表文件路径 THEN THE System SHALL 读取Excel文件并解析所有必需字段
3. WHEN Excel文件不存在或无法访问 THEN THE System SHALL 返回明确的错误信息并终止处理
4. WHEN Excel文件格式不正确或缺少必需列 THEN THE System SHALL 返回具体的错误描述
5. THE System SHALL 支持.xlsx和.xls两种Excel文件格式

### Requirement 2

**User Story:** 作为数据分析人员，我希望系统能够从操作命令内容中准确解析出访问账号和对端IP，以便进行准确的比对。

#### Acceptance Criteria

1. WHEN 操作内容包含SSH命令格式 THEN THE System SHALL 解析出访问账号名称
2. WHEN 操作内容包含有效的IPv4地址 THEN THE System SHALL 提取对端IP地址
3. WHEN 操作内容包含IPv4地址段格式 THEN THE System SHALL 提取所有相关IP地址
4. WHEN 操作内容不包含有效IP地址 THEN THE System SHALL 标记该记录为无法解析
5. WHEN 操作内容包含多种SSH命令格式 THEN THE System SHALL 正确识别所有支持的格式

### Requirement 3

**User Story:** 作为数据分析人员，我希望系统能够将操作命令表中的记录与报备表进行比对，以便识别哪些操作已报备、哪些未报备。

#### Acceptance Criteria

1. WHEN 访问账号、本端IP和对端IP三者均在报备表中匹配 THEN THE System SHALL 标记为"已报备"
2. WHEN 访问账号、本端IP和对端IP三者无法在报备表中完全匹配 THEN THE System SHALL 标记为"未报备"
3. WHEN 操作内容中无法解析出有效IP地址 THEN THE System SHALL 标记为"-"
4. WHEN 报备表中IP以IP段格式存储 THEN THE System SHALL 正确判断IP是否在该范围内
5. WHEN 报备表中IP以掩码格式存储 THEN THE System SHALL 正确判断IP是否在该网段内
6. WHEN 报备表中包含多个IP地址（以顿号分隔） THEN THE System SHALL 检查是否匹配任意一个IP

### Requirement 4

**User Story:** 作为数据分析人员，我希望系统能够生成包含核查结果的输出文件，以便查看和分析核查结果。

#### Acceptance Criteria

1. WHEN 核查完成 THEN THE System SHALL 在原操作命令表基础上添加"对比结果"列
2. WHEN 生成输出文件 THEN THE System SHALL 保留原始数据的所有列和内容
3. WHEN 生成输出文件 THEN THE System SHALL 使用"结果-"前缀加原文件名作为输出文件名
4. WHEN 生成输出文件 THEN THE System SHALL 保存为Excel格式
5. THE System SHALL 将输出文件保存在与输入文件相同的目录中

### Requirement 5

**User Story:** 作为数据分析人员，我希望系统能够处理报备表中的复杂IP格式，以便准确匹配各种IP表示方式。

#### Acceptance Criteria

1. WHEN 报备表IP为特定IP格式 THEN THE System SHALL 进行精确匹配
2. WHEN 报备表IP为IP段格式（如192.168.1.1-192.168.1.20） THEN THE System SHALL 判断目标IP是否在该范围内
3. WHEN 报备表IP为IP掩码格式（如192.168.1.1/16） THEN THE System SHALL 判断目标IP是否在该网段内
4. WHEN 报备表包含多个IP格式混合（以顿号分隔） THEN THE System SHALL 逐一检查每种格式
5. THE System SHALL 忽略IPv6地址格式的处理

### Requirement 6

**User Story:** 作为系统用户，我希望系统能够提供清晰的执行反馈和错误处理，以便了解处理进度和问题所在。

#### Acceptance Criteria

1. WHEN 系统开始处理 THEN THE System SHALL 显示正在处理的文件名称
2. WHEN 系统完成处理 THEN THE System SHALL 显示处理的记录总数和各类结果的统计信息
3. WHEN 发生错误 THEN THE System SHALL 提供具体的错误描述和建议的解决方案
4. WHEN 处理大量数据 THEN THE System SHALL 显示处理进度信息
5. THE System SHALL 记录详细的日志信息以便问题排查
