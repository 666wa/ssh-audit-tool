# Design Document

## Overview

SSH命令核查工具是一个Python脚本，用于自动化验证SSH操作命令是否已完成报备。系统读取两个Excel文件（操作命令表和报备表），通过解析SSH命令提取关键信息（访问账号、本端IP、对端IP），与报备表进行比对，最终生成包含核查结果的输出文件。

核心处理流程：
1. 读取并解析两个Excel文件
2. 从操作命令内容中提取访问账号和对端IP
3. 将提取的信息与报备表进行三元组匹配（访问账号+本端IP+对端IP）
4. 生成包含"对比结果"列的输出Excel文件

## Architecture

系统采用模块化设计，分为以下主要模块：

```
ssh_audit_tool/
├── main.py              # 主程序入口
├── file_handler.py      # Excel文件读写模块
├── parser.py            # SSH命令解析模块
├── ip_matcher.py        # IP地址匹配模块
├── auditor.py           # 核查比对模块
└── utils.py             # 工具函数模块
```

**数据流向：**
```
操作命令表(Excel) → 文件读取 → 命令解析 → 核查比对 ← 报备表(Excel)
                                              ↓
                                        结果输出(Excel)
```

## Components and Interfaces

### 1. FileHandler (file_handler.py)

负责Excel文件的读取和写入操作。

**接口：**
```python
class FileHandler:
    def read_operation_log(file_path: str) -> pd.DataFrame
    def read_report_table(file_path: str) -> pd.DataFrame
    def write_result(df: pd.DataFrame, output_path: str) -> None
    def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> bool
```

**职责：**
- 读取.xlsx和.xls格式的Excel文件
- 验证必需列是否存在
- 写入包含核查结果的输出文件
- 处理文件读写异常

### 2. CommandParser (parser.py)

负责从操作命令内容中解析访问账号和对端IP。

**接口：**
```python
class CommandParser:
    def parse_ssh_command(command: str) -> Dict[str, Optional[str]]
    def extract_account(command: str) -> Optional[str]
    def extract_target_ip(command: str) -> Optional[str]
    def is_valid_ipv4(ip: str) -> bool
```

**职责：**
- 识别SSH命令格式（ssh user@ip, ssh -l user ip, ssh user ip等）
- 提取访问账号名称
- 提取对端IP地址
- 验证IP地址格式

**支持的SSH命令格式：**
- `ssh cmhop@10.187.245.250`
- `ssh -l cmhop 10.187.245.250`
- `ssh cmhop 10.187.245.250`

### 3. IPMatcher (ip_matcher.py)

负责处理报备表中的复杂IP格式并进行匹配。

**接口：**
```python
class IPMatcher:
    def match_ip(target_ip: str, report_ip_str: str) -> bool
    def parse_ip_range(ip_range: str) -> Tuple[int, int]
    def parse_ip_mask(ip_mask: str) -> Tuple[int, int]
    def ip_to_int(ip: str) -> int
    def is_ip_in_range(ip: str, start_ip: str, end_ip: str) -> bool
    def is_ip_in_subnet(ip: str, subnet: str) -> bool
```

**职责：**
- 解析特定IP格式（192.168.1.1）
- 解析IP段格式（192.168.1.1-192.168.1.20）
- 解析IP掩码格式（192.168.1.1/16）
- 处理多个IP混合格式（以顿号分隔）
- 判断IP是否匹配

### 4. Auditor (auditor.py)

负责核心的比对逻辑。

**接口：**
```python
class Auditor:
    def __init__(report_df: pd.DataFrame)
    def audit_record(account: str, source_ip: str, target_ip: str) -> str
    def build_report_index() -> None
    def check_match(account: str, source_ip: str, target_ip: str) -> bool
```

**职责：**
- 构建报备表索引以提高查询效率
- 执行三元组匹配（访问账号+本端IP+对端IP）
- 返回核查结果（"已报备"/"未报备"/"-"）

### 5. Utils (utils.py)

提供通用工具函数。

**接口：**
```python
def setup_logging() -> None
def get_output_filename(input_filename: str) -> str
def print_statistics(results: Dict[str, int]) -> None
def validate_file_exists(file_path: str) -> bool
```

## Data Models

### OperationRecord (操作命令记录)

```python
@dataclass
class OperationRecord:
    operation_time: str          # 操作时间
    external_log_id: str         # 外部应用日志ID
    operation_log_id: str        # 操作日志ID
    session_id: str              # 会话ID
    domain: str                  # 归属域
    main_account: str            # 主账号名称
    operator: str                # 主账号操作人
    account_type: str            # 主账号类型
    responsible_person: str      # 主账号责任人
    organization: str            # 主账号组织机构
    org_full_path: str           # 组织机构全路径
    account_validity: str        # 主账号有效性
    account_status: str          # 主账号在当前域的状态
    vendor: str                  # 主账号所属厂商
    project_group: str           # 主账号所属项目组
    sub_account: str             # 从账号名称
    sub_account_status: str      # 从账号状态
    sub_account_type: str        # 从账号类型
    resource_ip: str             # 资源IP（本端IP）
    resource_name: str           # 资源名称
    resource_responsible: str    # 资源责任人
    resource_system: str         # 资源归属系统
    resource_department: str     # 资源归属部门
    operation_command: str       # 操作命令
    operation_content: str       # 操作内容
    operation_result: str        # 操作结果
    audit_result: str = ""       # 对比结果（新增）
```

### ReportRecord (报备记录)

```python
@dataclass
class ReportRecord:
    department: str              # 申请部门
    system_name: str             # 系统名称
    access_account: str          # 访问账号
    source_location: str         # 本端位置
    source_pod: str              # 本端POD
    source_ip: str               # 本端IP
    source_network: str          # 本端网络类型
    source_port: str             # 本端端口
    target_location: str         # 对端位置
    target_pod: str              # 对端POD
    target_ip: str               # 对端IP
    target_network: str          # 对端网络类型
    target_port: str             # 对端端口
    access_type: str             # 访问类型
    access_time_type: str        # 访问时间类型
    access_time_range: str       # 访问时间段
    start_date: str              # 开始日期
    end_date: str                # 结束日期
    applicant: str               # 申请人
    contact: str                 # 联系方式
    reason: str                  # 申请原因
    approver: str                # 审批人
```

### ParsedCommand (解析后的命令)

```python
@dataclass
class ParsedCommand:
    account: Optional[str]       # 访问账号
    target_ip: Optional[str]     # 对端IP
    is_parseable: bool           # 是否可解析
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*


### Property Reflection

经过对所有可测试属性的分析，识别出以下冗余：
- 属性5.2（IP段格式判断）与属性3.4重复
- 属性5.3（IP掩码格式判断）与属性3.5重复
- 属性5.4（多IP格式混合）与属性3.6重复
- 属性1.1和1.2可以合并为一个通用的Excel读取属性

消除冗余后，保留以下核心属性：

### Property 1: Excel文件读取完整性
*For any* 有效的Excel文件路径和必需列列表，读取文件后返回的DataFrame应该包含所有必需的列
**Validates: Requirements 1.1, 1.2**

### Property 2: 文件不存在错误处理
*For any* 不存在的文件路径，系统应该抛出明确的文件不存在异常
**Validates: Requirements 1.3**

### Property 3: 缺少必需列错误处理
*For any* 缺少必需列的Excel文件，系统应该返回具体的缺失列信息
**Validates: Requirements 1.4**

### Property 4: SSH命令账号解析
*For any* 包含有效SSH命令格式的字符串，解析器应该正确提取访问账号名称
**Validates: Requirements 2.1, 2.5**

### Property 5: IPv4地址提取
*For any* 包含有效IPv4地址的SSH命令，解析器应该正确提取对端IP地址
**Validates: Requirements 2.2**

### Property 6: 无效IP标记
*For any* 不包含有效IP地址的操作内容，系统应该标记为无法解析
**Validates: Requirements 2.4**

### Property 7: 三元组匹配-已报备
*For any* 在报备表中存在的（访问账号、本端IP、对端IP）三元组，核查结果应该为"已报备"
**Validates: Requirements 3.1**

### Property 8: 三元组匹配-未报备
*For any* 不在报备表中的（访问账号、本端IP、对端IP）三元组，核查结果应该为"未报备"
**Validates: Requirements 3.2**

### Property 9: 无法解析标记
*For any* 无法从操作内容中解析出有效IP的记录，核查结果应该为"-"
**Validates: Requirements 3.3**

### Property 10: IP段范围匹配
*For any* IP地址和IP段（格式：start-end），判断结果应该正确反映IP是否在该范围内
**Validates: Requirements 3.4, 5.2**

### Property 11: 子网掩码匹配
*For any* IP地址和CIDR格式的子网（如192.168.1.0/24），判断结果应该正确反映IP是否在该网段内
**Validates: Requirements 3.5, 5.3**

### Property 12: 多IP匹配
*For any* 目标IP和包含多个IP的报备记录（以顿号分隔），如果目标IP匹配其中任意一个，应该返回匹配成功
**Validates: Requirements 3.6, 5.4**

### Property 13: 输出列完整性
*For any* 输入DataFrame，输出DataFrame应该包含所有原始列加上"对比结果"列
**Validates: Requirements 4.1**

### Property 14: 数据保留完整性
*For any* 输入DataFrame的原始列，输出DataFrame中对应列的数据应该完全一致
**Validates: Requirements 4.2**

### Property 15: 输出文件名格式
*For any* 输入文件名，输出文件名应该为"结果-" + 原文件名
**Validates: Requirements 4.3**

### Property 16: 输出文件路径
*For any* 输入文件路径，输出文件应该保存在相同的目录中
**Validates: Requirements 4.5**

### Property 17: 精确IP匹配
*For any* 两个IP地址字符串，当且仅当它们完全相同时，精确匹配应该返回True
**Validates: Requirements 5.1**

### Property 18: IPv6地址忽略
*For any* 包含IPv6地址格式的操作内容，系统应该将其标记为无法解析或忽略
**Validates: Requirements 5.5**

## Error Handling

系统应该优雅地处理以下错误情况：

### 文件相关错误
- **文件不存在**: 抛出`FileNotFoundError`，提示用户检查文件路径
- **文件格式错误**: 抛出`ValueError`，说明期望的文件格式
- **文件权限错误**: 抛出`PermissionError`，提示用户检查文件权限
- **Excel格式损坏**: 捕获pandas异常，提示文件可能已损坏

### 数据验证错误
- **缺少必需列**: 抛出`ValueError`，列出所有缺失的列名
- **数据类型错误**: 记录警告日志，尝试类型转换或使用默认值
- **空数据文件**: 抛出`ValueError`，提示文件不包含数据行

### 解析错误
- **无法识别的SSH命令格式**: 记录到日志，标记为无法解析
- **无效的IP格式**: 记录到日志，标记为无法解析
- **编码错误**: 尝试多种编码方式，失败则记录错误

### 运行时错误
- **内存不足**: 建议分批处理或增加系统内存
- **磁盘空间不足**: 检查输出目录的可用空间
- **意外异常**: 记录完整的堆栈跟踪，提示用户报告问题

所有错误信息应该：
- 使用中文描述，便于用户理解
- 包含具体的错误原因
- 提供可能的解决方案
- 记录到日志文件以便排查

## Testing Strategy

系统将采用双重测试策略：单元测试和基于属性的测试（Property-Based Testing）。

### 单元测试

使用`pytest`框架编写单元测试，覆盖以下方面：

**文件处理模块测试：**
- 测试读取有效的.xlsx和.xls文件
- 测试文件不存在的错误处理
- 测试缺少必需列的错误处理
- 测试输出文件生成

**命令解析模块测试：**
- 测试各种SSH命令格式的解析
  - `ssh user@ip`
  - `ssh -l user ip`
  - `ssh user ip`
- 测试边界情况（空字符串、特殊字符等）
- 测试无效命令的处理

**IP匹配模块测试：**
- 测试精确IP匹配
- 测试IP段匹配（边界值）
- 测试子网掩码匹配（各种掩码长度）
- 测试多IP格式混合

**核查模块测试：**
- 测试已报备情况
- 测试未报备情况
- 测试无法解析情况
- 测试报备表索引构建

### 基于属性的测试（Property-Based Testing）

使用`hypothesis`库进行基于属性的测试，每个测试至少运行100次迭代。

**测试库选择：** Python的`hypothesis`库

**配置要求：**
- 每个属性测试至少运行100次迭代
- 使用`@given`装饰器定义输入生成策略
- 使用`@settings(max_examples=100)`确保足够的测试覆盖

**属性测试标注格式：**
每个属性测试必须使用以下格式的注释标注：
```python
# Feature: ssh-audit-tool, Property 1: Excel文件读取完整性
```

**核心属性测试：**

1. **Property 1: Excel文件读取完整性** - 生成随机的有效DataFrame，写入Excel，读取后验证列完整性
2. **Property 4: SSH命令账号解析** - 生成随机的SSH命令格式，验证账号提取的正确性
3. **Property 5: IPv4地址提取** - 生成随机的IPv4地址嵌入SSH命令，验证IP提取的正确性
4. **Property 7: 三元组匹配-已报备** - 生成随机的报备记录和匹配的操作记录，验证返回"已报备"
5. **Property 8: 三元组匹配-未报备** - 生成随机的报备记录和不匹配的操作记录，验证返回"未报备"
6. **Property 10: IP段范围匹配** - 生成随机的IP和IP段，验证范围判断的正确性
7. **Property 11: 子网掩码匹配** - 生成随机的IP和子网，验证网段判断的正确性
8. **Property 13: 输出列完整性** - 生成随机的输入DataFrame，验证输出包含所有原始列加新列
9. **Property 14: 数据保留完整性** - 生成随机的输入数据，验证输出数据在原始列上完全一致
10. **Property 15: 输出文件名格式** - 生成随机的文件名，验证输出文件名符合"结果-"前缀规则

**测试数据生成策略：**
- 使用`hypothesis.strategies`生成各种格式的SSH命令
- 生成有效和无效的IPv4地址
- 生成各种IP格式（特定IP、IP段、子网掩码）
- 生成边界情况（空字符串、极长字符串、特殊字符）

**测试执行要求：**
- 所有属性测试必须在实现对应功能后立即编写
- 测试失败时，hypothesis会自动缩小失败案例，帮助定位问题
- 每个属性测试必须明确标注其验证的需求编号

### 集成测试

编写端到端的集成测试：
- 使用真实的示例数据文件
- 验证完整的处理流程
- 检查输出文件的正确性
- 验证统计信息的准确性

### 测试覆盖率目标

- 代码覆盖率：≥ 85%
- 分支覆盖率：≥ 80%
- 核心模块（parser, ip_matcher, auditor）：≥ 95%

## Implementation Notes

### 性能考虑

1. **报备表索引**: 构建基于（访问账号、本端IP）的哈希索引，加速查询
2. **批量处理**: 使用pandas的向量化操作，避免逐行循环
3. **内存管理**: 对于大文件，考虑分块读取和处理
4. **缓存**: 缓存IP匹配结果，避免重复计算

### 依赖库

```
pandas>=1.5.0
openpyxl>=3.0.0
xlrd>=2.0.0
hypothesis>=6.0.0
pytest>=7.0.0
```

### 配置文件

可选的配置文件`config.json`：
```json
{
  "required_operation_columns": [
    "操作时间", "资源IP", "操作内容", "操作结果"
  ],
  "required_report_columns": [
    "访问账号", "本端IP", "对端IP"
  ],
  "log_level": "INFO",
  "log_file": "ssh_audit.log"
}
```

### 日志格式

```
[2025-12-25 10:30:45] INFO - 开始处理文件: 月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2025-12-09_09-58-30-661_602.xlsx
[2025-12-25 10:30:46] INFO - 读取操作记录: 1250条
[2025-12-25 10:30:46] INFO - 读取报备记录: 350条
[2025-12-25 10:30:47] INFO - 解析SSH命令: 1250/1250
[2025-12-25 10:30:48] INFO - 核查完成: 已报备=980, 未报备=220, 无法解析=50
[2025-12-25 10:30:48] INFO - 输出文件: 结果-月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2025-12-09_09-58-30-661_602.xlsx
```

## Future Enhancements

1. **IPv6支持**: 扩展IP匹配模块以支持IPv6地址
2. **Web界面**: 提供基于Web的用户界面
3. **定时任务**: 支持定时自动执行核查
4. **报表生成**: 生成可视化的统计报表
5. **多线程处理**: 对于超大文件，使用多线程加速处理
6. **数据库支持**: 支持从数据库读取报备数据
7. **规则引擎**: 支持自定义匹配规则
