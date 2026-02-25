注意事项
使用csv格式时 文本内容不要再包含英文逗号

# SSH命令核查工具

## 支持的模板

本工具支持两种操作记录模板：

### 1. 原始模板（SDC数据源）
- 文件：月-使用ssh命令连接其它设备-SDC数据源
- 列名：中文列名（操作内容、资源IP、主账号名称等）
- 运行脚本：`python run_audit.py`
- 配置文件：`ssh_audit_tool/config.py`

### 2. 4A绕行核实模板
- 文件：4A绕行核实_大数据分公司
- 列名：英文列名（op_fort_content、res_ip、main_acct_name等）
- 运行脚本：`python run_audit_4a.py`
- 配置文件：`ssh_audit_tool/config_4a.py`

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 运行工具

**原始模板：**
```bash
python run_audit.py
```

**4A模板：**
```bash
python run_audit_4a.py
```

工具会自动使用默认配置文件进行核查。

## 默认配置

默认文件路径已配置在 `ssh_audit_tool/config.py` 中（全路径）：

```python
# 默认操作命令表
DEFAULT_OPERATION_FILE = r"D:\Desktop\gaoyf工作交接\ssh绕行脚本\ssh-niu\月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2025-12-09_09-58-30-661_602.xlsx"

# 默认报备表
DEFAULT_REPORT_FILE = r"D:\Desktop\gaoyf工作交接\ssh绕行脚本\ssh-niu\主机互访报备 (12月9日).xlsx"

# 默认输出目录
DEFAULT_OUTPUT_DIR = r"D:\Desktop\gaoyf工作交接\ssh绕行脚本\ssh-niu"
```

**修改默认路径**：直接编辑 `ssh_audit_tool/config.py` 文件中的这三个配置项。

## 自定义运行

```bash
# 指定文件路径
python run_audit.py -o <操作命令表.xlsx> -r <报备表.xlsx>

# 自定义输出路径
python run_audit.py -o <操作命令表.xlsx> -r <报备表.xlsx> --output <输出文件.xlsx>
```

## 完整文档

详细使用说明请查看 `docs` 目录：

- **[完整使用文档](docs/README.md)** - 详细的功能说明和使用方法
- **[全路径运行命令](docs/运行命令-全路径.txt)** - Windows全路径命令示例
- **[文件清单](docs/文件清单.md)** - 项目文件结构说明
- **[功能总结](docs/FEATURE_SUMMARY.md)** - 功能特性总结
- **[最终总结](docs/FINAL_SUMMARY.md)** - 项目完整总结
- **[IO优化说明](docs/IO_IMPROVEMENTS.md)** - 输入输出优化详情

## 主要功能

- ✅ 自动解析SSH命令，提取访问账号和对端IP
- ✅ 支持多种SSH命令格式和IP格式
- ✅ 支持连续IP范围（如 `10.1.1.1-10.1.1.254-10.1.2.1-10.1.2.254`）
- ✅ 自动修复异常IP格式（多个点、中文句号、特殊字符）
- ✅ 显示命中的报备记录序号
- ✅ 生成详细的核查结果和统计信息
- ✅ **时间范围验证**：自动验证操作时间是否在报备有效期内（详见 [时间范围验证说明](docs/时间范围验证说明.md)）

## 输出结果

程序会在配置的输出目录生成结果文件，添加三列：
- **对比结果**: 已报备 / 未报备 / 已报备但已过期 / 异常：非有效ssh命令
- **命中序号**: 匹配的报备表序号
- **详细说明**: 详细的匹配信息（新增）
  - 已报备：显示命中序号、访问时间段、访问账号、源端IP、对端IP
  - 未报备：显示各字段是否命中（已命中/未命中）

详见：[详细输出功能说明](docs/详细输出功能说明.md)

**说明**：
- 只有包含ssh关键字且能提取出有效IP的命令才会进行比对
- 无效的SSH命令直接标记为"异常：非有效ssh命令"，不作为参考依据
- 支持 localhost 和 127.0.0.1 自动转换为本机IP

## 技术支持

如遇到问题，请查看：
1. 日志文件 `ssh_audit.log`
2. [完整文档](docs/README.md) 中的常见问题部分

## 系统要求

- Python 3.7+
- pandas >= 1.5.0
- openpyxl >= 3.0.0
- xlrd >= 2.0.0
