# 实现计划：账号不在报备范围内的早期退出

## 概述

本功能优化SSH审计工具的账号匹配逻辑，实现早期退出机制。当检测到访问账号不在报备范围内时，立即返回明确的提示信息并终止后续的IP比较逻辑，提高审计效率和结果的可读性。

核心改动集中在`ssh_audit_tool/auditor.py`文件的`Auditor`类中，主要涉及`check_match`方法和三个审计方法（`audit_record`、`audit_record_4a`、`audit_record_with_target_ip`）。

## 任务

- [ ] 1. 修改check_match方法实现早期退出逻辑
  - [ ] 1.1 在check_match方法中添加账号不在报备范围内的早期退出逻辑
    - 在账号索引查找失败时，立即返回特殊标识
    - 在match_details字典中添加account_not_in_report字段
    - 添加DEBUG级别日志记录账号不在报备范围内的情况
    - _需求: 1.1, 1.2, 3.2, 3.4, 5.1, 5.2_
  
  - [ ] 1.2 确保返回值结构的向后兼容性
    - 验证返回值仍为元组(matched_serial, match_details)
    - 确保matched_serial为None时不影响现有逻辑
    - 确保match_details包含所有必需字段
    - _需求: 3.1, 3.2, 3.3, 3.5_

- [ ] 2. 修改audit_record方法处理账号不在报备范围内的情况
  - [ ] 2.1 在audit_record方法中检测account_not_in_report标识
    - 检查match_details中的account_not_in_report字段
    - 返回"未报备"结果和明确的详细说明
    - 详细说明格式为"该访问账号{account}不在报备范围内"
    - _需求: 2.1, 2.4, 6.1, 6.4_

- [ ] 3. 修改audit_record_4a方法处理账号不在报备范围内的情况
  - [ ] 3.1 在audit_record_4a方法中检测account_not_in_report标识
    - 检查match_details中的account_not_in_report字段
    - 返回"未报备"结果
    - 命中序号为空字符串
    - _需求: 2.2, 6.2, 6.4_

- [ ] 4. 修改audit_record_with_target_ip方法处理账号不在报备范围内的情况
  - [ ] 4.1 在audit_record_with_target_ip方法中检测account_not_in_report标识
    - 检查match_details中的account_not_in_report字段
    - 返回"未报备"结果和明确的详细说明
    - 详细说明格式为"该访问账号{account}不在报备范围内"
    - _需求: 2.3, 2.4, 6.3, 6.4_

- [ ] 5. 边界条件处理和验证
  - [ ] 5.1 添加边界条件处理逻辑
    - 处理账号为空字符串的情况
    - 处理账号为None的情况
    - 处理账号为"nan"字符串的情况
    - 处理report_index为空字典的情况
    - _需求: 7.1, 7.2, 7.3, 7.4_
  
  - [ ]* 5.2 编写单元测试验证边界条件
    - 测试账号为空字符串时的行为
    - 测试账号为None时的行为
    - 测试账号为"nan"时的行为
    - 测试report_index为空时的行为
    - _需求: 7.1, 7.2, 7.3, 7.4_

- [ ] 6. 性能验证
  - [ ]* 6.1 验证早期退出机制的性能提升
    - 测量账号不在报备范围内时的执行时间
    - 测量完整匹配流程的执行时间
    - 验证早期退出时间小于完整流程的10%
    - _需求: 4.1, 4.2, 4.3_

- [ ] 7. 检查点 - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

## 注意事项

- 标记为`*`的任务为可选任务，可跳过以加快MVP交付
- 每个任务都引用了具体的需求编号以确保可追溯性
- 核心改动集中在`ssh_audit_tool/auditor.py`文件
- `audit_violation_record`方法不需要修改，因为它不调用`check_match`方法
- 保持返回值结构的向后兼容性是关键约束
