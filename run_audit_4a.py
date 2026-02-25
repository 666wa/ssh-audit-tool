"""
SSH命令核查工具 - 4A绕行核实模板快速运行脚本

使用默认配置运行核查工具，无需命令行参数
配置文件: ssh_audit_tool/config_4a.py
"""
import sys
from ssh_audit_tool.main_4a import main
from ssh_audit_tool.config_4a import (
    DEFAULT_OPERATION_FILE,
    DEFAULT_REPORT_FILE,
    DEFAULT_OUTPUT_DIR
)


if __name__ == '__main__':
    print("=" * 60)
    print("SSH命令核查工具 - 4A绕行核实模板")
    print("=" * 60)
    print(f"操作表: {DEFAULT_OPERATION_FILE}")
    print(f"报备表: {DEFAULT_REPORT_FILE}")
    print(f"输出目录: {DEFAULT_OUTPUT_DIR}")
    print("=" * 60)
    print()
    
    # 设置默认参数
    sys.argv = [
        'run_audit_4a.py',
        '-o', DEFAULT_OPERATION_FILE,
        '-r', DEFAULT_REPORT_FILE
    ]
    
    # 运行主程序
    sys.exit(main())
