"""
配置模块 - 4A绕行核实模板专用配置
"""
from ssh_audit_tool.config_base import (
    # 重新导出共享常量，保持向后兼容
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_DATE_FORMAT,
    RESULT_REPORTED,
    RESULT_NOT_REPORTED,
    RESULT_INVALID_COMMAND,
    RESULT_INVALID_SOURCE_IP,
    RESULT_EXPIRED,
    OUTPUT_COLUMN_NAME,
    MATCHED_ROW_COLUMN_NAME,
    DETAIL_COLUMN_NAME,
    REQUIRED_REPORT_COLUMNS,
    OPTIONAL_REPORT_TIME_COLUMNS,
    USE_FAST_AUDITOR,
    setup_logging,
)


# 默认文件路径配置
DEFAULT_OPERATION_FILE = r"2026-01-09\4A绕行核实_大数据分公司.csv"
DEFAULT_REPORT_FILE = r"2026-01-09\主机互访报备-20260109.csv"
DEFAULT_OUTPUT_DIR = r"2026-01-09"

# 日志文件名（4A模板专用）
LOG_FILE = 'ssh_audit_4a.log'

# 4A模板的必需列名（英文列名）
REQUIRED_OPERATION_COLUMNS_4A = [
    'op_fort_content',   # 操作内容（SSH命令）
    'res_ip',            # 资源IP（本端IP）
    'main_acct_name'     # 主账号名称
]

# 4A模板的可选列名
OPTIONAL_OPERATION_COLUMNS_4A = [
    'sub_acct_name',     # 从账号名称（如果存在，优先使用）
    'res_name'           # 资源名称（如果资源IP无效，从资源名称提取本端IP）
]
