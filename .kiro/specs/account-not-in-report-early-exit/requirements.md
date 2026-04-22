# 需求文档

## 介绍

本功能是对SSH审计工具的账号匹配逻辑进行优化，实现早期退出机制。当检测到访问账号不在报备范围内时，立即输出明确的提示信息并终止后续的IP比较逻辑，提高审计效率和结果的可读性。

## 术语表

- **Auditor**: SSH命令核查器，负责比对操作记录与报备表
- **report_index**: 报备表索引，以账号为键的字典结构，用于快速查找账号相关的报备记录
- **check_match**: 核查器的核心匹配方法，检查账号、源IP、目的IP三元组是否在报备表中匹配
- **audit_record**: 原始模板的审计方法，调用check_match进行核查
- **audit_record_4a**: 4A模板的审计方法，调用check_match进行核查
- **audit_record_with_target_ip**: 直接指定对端IP的审计方法，调用check_match进行核查
- **audit_violation_record**: 违规使用记录的审计方法，不调用check_match（只核查IP对）
- **early_exit**: 早期退出机制，在检测到不满足条件时立即返回，避免执行后续不必要的逻辑

## 需求

### 需求 1: 账号不在报备范围内的识别

**用户故事:** 作为审计人员，我希望系统能够明确识别出访问账号不在报备范围内的情况，以便快速定位问题。

#### 验收标准

1. WHEN 访问账号不在report_index中，THE check_match方法 SHALL 返回一个特殊的标识表示"账号不在报备范围内"
2. THE check_match方法 SHALL 在账号不在report_index时不执行源IP和目的IP的比较逻辑
3. THE 返回值结构 SHALL 能够区分"账号不在报备范围内"和"账号匹配但IP不匹配"两种情况

### 需求 2: 审计方法的早期退出处理

**用户故事:** 作为审计人员，我希望当账号不在报备范围内时，系统能够输出明确的提示信息，而不是模糊的"未报备"结果。

#### 验收标准

1. WHEN audit_record方法接收到"账号不在报备范围内"的标识，THE Auditor SHALL 返回明确的结果说明"该访问账号不在报备范围内"
2. WHEN audit_record_4a方法接收到"账号不在报备范围内"的标识，THE Auditor SHALL 返回明确的结果说明"该访问账号不在报备范围内"
3. WHEN audit_record_with_target_ip方法接收到"账号不在报备范围内"的标识，THE Auditor SHALL 返回明确的结果说明"该访问账号不在报备范围内"
4. THE 详细说明字段 SHALL 包含具体的账号名称，格式为"该访问账号{account}不在报备范围内"

### 需求 3: 返回值结构的向后兼容性

**用户故事:** 作为开发人员，我希望修改后的返回值结构能够与现有代码兼容，避免破坏其他功能。

#### 验收标准

1. THE check_match方法的返回值结构 SHALL 保持为元组(matched_serial, match_details)
2. WHEN 账号不在报备范围内时，THE matched_serial SHALL 为None
3. WHEN 账号不在报备范围内时，THE match_details字典 SHALL 包含account_match=False的标识
4. THE match_details字典 SHALL 新增一个字段account_not_in_report用于明确标识账号不在报备范围内的情况
5. FOR ALL 现有的调用check_match的代码，修改后的返回值 SHALL 不破坏现有逻辑

### 需求 4: 性能优化验证

**用户故事:** 作为系统管理员，我希望早期退出机制能够提高审计效率，减少不必要的计算。

#### 验收标准

1. WHEN 账号不在report_index中，THE check_match方法 SHALL 不遍历report_index中的任何记录
2. WHEN 账号不在report_index中，THE check_match方法 SHALL 不调用ip_matcher.match_ip方法
3. THE 早期退出逻辑 SHALL 在账号检查失败后立即返回，执行时间应小于完整匹配流程的10%

### 需求 5: 日志和调试信息

**用户故事:** 作为开发人员，我希望系统能够记录账号不在报备范围内的情况，便于调试和统计。

#### 验收标准

1. WHEN 账号不在report_index中，THE Auditor SHALL 记录一条DEBUG级别的日志，内容包含账号名称
2. THE 日志消息格式 SHALL 为"账号{account}不在报备范围内，跳过IP比较"
3. THE 日志 SHALL 在check_match方法中记录，而不是在调用方记录

### 需求 6: 输出结果的一致性

**用户故事:** 作为审计人员，我希望不同审计方法对"账号不在报备范围内"的输出格式保持一致。

#### 验收标准

1. THE audit_record方法 SHALL 返回核查结果为"未报备"，详细说明为"该访问账号{account}不在报备范围内"
2. THE audit_record_4a方法 SHALL 返回核查结果为"未报备"
3. THE audit_record_with_target_ip方法 SHALL 返回核查结果为"未报备"，详细说明为"该访问账号{account}不在报备范围内"
4. FOR ALL 审计方法，当账号不在报备范围内时，命中序号 SHALL 为空字符串

### 需求 7: 边界条件处理

**用户故事:** 作为开发人员，我希望系统能够正确处理各种边界条件，确保功能的健壮性。

#### 验收标准

1. WHEN 账号为空字符串，THE check_match方法 SHALL 返回空的匹配详情，不触发"账号不在报备范围内"逻辑
2. WHEN 账号为None，THE check_match方法 SHALL 返回空的匹配详情，不触发"账号不在报备范围内"逻辑
3. WHEN 账号为"nan"字符串，THE check_match方法 SHALL 将其视为有效账号进行查找
4. WHEN report_index为空字典，THE check_match方法 SHALL 正确处理所有账号为"不在报备范围内"的情况
