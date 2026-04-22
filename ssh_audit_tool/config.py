"""
配置模块 - 标准SSH绕行稽核模板配置
"""
import logging
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
DEFAULT_OPERATION_FILE = r"2026-03-19\月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2026-03-19_15-03-58-572_167.csv"
DEFAULT_REPORT_FILE = r"2026-03-19\主机互访报备-20260319.csv"
DEFAULT_OUTPUT_DIR = r"2026-03-19"

# 日志文件名（本模板专用）
LOG_FILE = 'ssh_audit.log'

# 标准模板的必需操作列名
REQUIRED_OPERATION_COLUMNS = [
    '操作时间', '资源IP', '操作内容', '主账号名称'
]

# 标准模板的可选操作列名
OPTIONAL_OPERATION_COLUMNS = [
    '从账号名称',  # 如果存在，优先使用从账号
    '资源名称'     # 如果资源IP无效，从资源名称提取IP
]
