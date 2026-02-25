"""
公共配置模块 - 所有模板共享的常量和函数
"""
import logging
import sys


# 日志配置
LOG_LEVEL = logging.INFO
LOG_FORMAT = '[%(asctime)s] %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# 结果标记
RESULT_REPORTED = '已报备'
RESULT_NOT_REPORTED = '未报备'
RESULT_INVALID_COMMAND = '异常：非有效ssh命令'
RESULT_INVALID_SOURCE_IP = '异常：无法获取有效本端IP'
RESULT_EXPIRED = '已报备但已过期'

# 输出列名
OUTPUT_COLUMN_NAME = '对比结果'
MATCHED_ROW_COLUMN_NAME = '命中序号'
DETAIL_COLUMN_NAME = '详细说明'

# 报备表必需列名（所有模板共用）
REQUIRED_REPORT_COLUMNS = [
    '访问账号', '本端主机IP', '对端主机IP'
]

# 报备表时间范围列名（可选）
OPTIONAL_REPORT_TIME_COLUMNS = [
    '生效时间',
    '失效时间'
]

# 性能配置
USE_FAST_AUDITOR = True


def setup_logging(log_file: str = 'ssh_audit.log', log_level: int = LOG_LEVEL) -> None:
    """
    设置日志配置

    Args:
        log_file: 日志文件路径
        log_level: 日志级别
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    logger.handlers.clear()

    # 文件handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    file_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    # 控制台handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT, LOG_DATE_FORMAT))

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
