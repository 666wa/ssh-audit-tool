# Implementation Plan

- [x] 1. 设置项目结构和依赖


  - 创建项目目录结构（ssh_audit_tool/）
  - 创建requirements.txt文件，包含pandas、openpyxl、xlrd、hypothesis、pytest
  - 创建__init__.py文件使其成为Python包
  - 设置日志配置
  - _Requirements: 1.1, 1.2_



- [ ] 2. 实现工具函数模块（utils.py）
  - 实现日志设置函数setup_logging()
  - 实现文件名处理函数get_output_filename()
  - 实现文件存在性验证函数validate_file_exists()
  - 实现统计信息打印函数print_statistics()
  - _Requirements: 4.3, 6.1, 6.2_

- [ ]* 2.1 编写utils模块的单元测试
  - 测试文件名格式转换
  - 测试文件存在性验证
  - _Requirements: 4.3_

- [ ]* 2.2 编写属性测试：输出文件名格式
  - **Property 15: 输出文件名格式**


  - **Validates: Requirements 4.3**

- [ ] 3. 实现IP匹配模块（ip_matcher.py）
  - 实现IPMatcher类
  - 实现ip_to_int()函数，将IP地址转换为整数
  - 实现is_valid_ipv4()函数，验证IPv4格式
  - 实现parse_ip_range()函数，解析IP段格式（如192.168.1.1-192.168.1.20）
  - 实现parse_ip_mask()函数，解析CIDR格式（如192.168.1.0/24）
  - 实现is_ip_in_range()函数，判断IP是否在范围内
  - 实现is_ip_in_subnet()函数，判断IP是否在子网内
  - 实现match_ip()函数，处理多种IP格式混合（以顿号分隔）
  - _Requirements: 3.4, 3.5, 3.6, 5.1, 5.2, 5.3, 5.4_

- [ ]* 3.1 编写IP匹配模块的单元测试
  - 测试精确IP匹配
  - 测试IP段边界值
  - 测试各种子网掩码长度
  - 测试多IP格式混合
  - 测试无效IP格式处理
  - _Requirements: 3.4, 3.5, 3.6, 5.1_

- [ ]* 3.2 编写属性测试：IP段范围匹配
  - **Property 10: IP段范围匹配**
  - **Validates: Requirements 3.4, 5.2**

- [ ]* 3.3 编写属性测试：子网掩码匹配
  - **Property 11: 子网掩码匹配**
  - **Validates: Requirements 3.5, 5.3**

- [ ]* 3.4 编写属性测试：精确IP匹配
  - **Property 17: 精确IP匹配**
  - **Validates: Requirements 5.1**



- [ ]* 3.5 编写属性测试：多IP匹配
  - **Property 12: 多IP匹配**
  - **Validates: Requirements 3.6, 5.4**

- [ ] 4. 实现SSH命令解析模块（parser.py）
  - 实现CommandParser类
  - 实现is_valid_ipv4()函数，验证IPv4格式
  - 实现extract_account()函数，从SSH命令中提取账号名
  - 实现extract_target_ip()函数，从SSH命令中提取目标IP
  - 实现parse_ssh_command()函数，解析完整的SSH命令
  - 支持多种SSH命令格式：ssh user@ip, ssh -l user ip, ssh user ip
  - 处理IPv6地址，标记为无法解析
  - _Requirements: 2.1, 2.2, 2.4, 2.5, 5.5_

- [ ]* 4.1 编写命令解析模块的单元测试
  - 测试各种SSH命令格式
  - 测试边界情况（空字符串、特殊字符）
  - 测试无效命令处理
  - 测试IPv6地址处理
  - _Requirements: 2.1, 2.2, 2.4, 2.5_

- [ ]* 4.2 编写属性测试：SSH命令账号解析
  - **Property 4: SSH命令账号解析**
  - **Validates: Requirements 2.1, 2.5**

- [ ]* 4.3 编写属性测试：IPv4地址提取
  - **Property 5: IPv4地址提取**
  - **Validates: Requirements 2.2**

- [ ]* 4.4 编写属性测试：无效IP标记
  - **Property 6: 无效IP标记**


  - **Validates: Requirements 2.4**

- [ ]* 4.5 编写属性测试：IPv6地址忽略
  - **Property 18: IPv6地址忽略**
  - **Validates: Requirements 5.5**

- [ ] 5. 实现文件处理模块（file_handler.py）
  - 实现FileHandler类
  - 实现validate_columns()函数，验证必需列是否存在
  - 实现read_operation_log()函数，读取操作命令表
  - 实现read_report_table()函数，读取报备表
  - 实现write_result()函数，写入结果文件
  - 支持.xlsx和.xls两种格式
  - 实现错误处理（文件不存在、格式错误、权限错误等）
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 4.1, 4.2, 4.4, 4.5_

- [ ]* 5.1 编写文件处理模块的单元测试
  - 测试读取有效的.xlsx和.xls文件
  - 测试文件不存在错误处理
  - 测试缺少必需列错误处理
  - 测试输出文件生成
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [ ]* 5.2 编写属性测试：Excel文件读取完整性
  - **Property 1: Excel文件读取完整性**
  - **Validates: Requirements 1.1, 1.2**

- [ ]* 5.3 编写属性测试：文件不存在错误处理
  - **Property 2: 文件不存在错误处理**
  - **Validates: Requirements 1.3**

- [ ]* 5.4 编写属性测试：缺少必需列错误处理
  - **Property 3: 缺少必需列错误处理**
  - **Validates: Requirements 1.4**

- [ ]* 5.5 编写属性测试：输出列完整性
  - **Property 13: 输出列完整性**
  - **Validates: Requirements 4.1**



- [ ]* 5.6 编写属性测试：数据保留完整性
  - **Property 14: 数据保留完整性**
  - **Validates: Requirements 4.2**

- [ ]* 5.7 编写属性测试：输出文件路径
  - **Property 16: 输出文件路径**
  - **Validates: Requirements 4.5**

- [ ] 6. 实现核查模块（auditor.py）
  - 实现Auditor类
  - 实现__init__()方法，接收报备表DataFrame
  - 实现build_report_index()方法，构建报备表索引以提高查询效率
  - 实现check_match()方法，检查三元组是否在报备表中
  - 实现audit_record()方法，对单条记录进行核查
  - 集成CommandParser和IPMatcher
  - 返回核查结果："已报备"、"未报备"、"-"
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 6.1 编写核查模块的单元测试
  - 测试已报备情况
  - 测试未报备情况
  - 测试无法解析情况
  - 测试报备表索引构建
  - _Requirements: 3.1, 3.2, 3.3_

- [ ]* 6.2 编写属性测试：三元组匹配-已报备
  - **Property 7: 三元组匹配-已报备**


  - **Validates: Requirements 3.1**

- [ ]* 6.3 编写属性测试：三元组匹配-未报备
  - **Property 8: 三元组匹配-未报备**
  - **Validates: Requirements 3.2**

- [ ]* 6.4 编写属性测试：无法解析标记
  - **Property 9: 无法解析标记**
  - **Validates: Requirements 3.3**

- [ ] 7. 实现主程序（main.py）
  - 实现命令行参数解析（操作命令表路径、报备表路径）
  - 实现主处理流程：
    1. 读取两个Excel文件
    2. 创建Auditor实例
    3. 遍历操作记录，调用audit_record()
    4. 将结果添加到DataFrame的"对比结果"列

    5. 生成输出文件
  - 实现进度显示



  - 实现统计信息输出（已报备、未报备、无法解析的数量）
  - 实现异常处理和错误提示
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 6.1, 6.2_

- [ ]* 7.1 编写主程序的集成测试
  - 使用真实示例数据测试完整流程
  - 验证输出文件正确性
  - 验证统计信息准确性
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 8. Checkpoint - 确保所有测试通过
  - 确保所有测试通过，如有问题请询问用户

- [ ] 9. 创建使用文档和示例
  - 编写README.md，包含安装说明、使用方法、示例
  - 创建示例配置文件config.json
  - 添加命令行帮助信息
  - _Requirements: 6.1, 6.2, 6.3_

- [ ] 10. 性能优化和最终测试
  - 优化报备表索引结构
  - 测试大文件处理性能
  - 优化内存使用
  - 进行最终的端到端测试
  - _Requirements: All_
