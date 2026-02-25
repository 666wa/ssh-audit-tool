"""
SSH命令核查工具 - 启动脚本

使用方法:
    python run_audit.py
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ssh_audit_tool.main import main
from ssh_audit_tool.config import DEFAULT_OPERATION_FILE, DEFAULT_REPORT_FILE

if __name__ == '__main__':
    # 如果没有提供命令行参数，使用默认文件
    if len(sys.argv) == 1:
        # 检查文件是否存在
        if os.path.exists(DEFAULT_OPERATION_FILE) and os.path.exists(DEFAULT_REPORT_FILE):
            print(f"使用默认文件:")
            print(f"  操作命令表: {DEFAULT_OPERATION_FILE}")
            print(f"  报备表: {DEFAULT_REPORT_FILE}")
            print()
            
            # 设置命令行参数
            sys.argv = [
                sys.argv[0],
                '-o', DEFAULT_OPERATION_FILE,
                '-r', DEFAULT_REPORT_FILE
            ]
        else:
            print("错误: 未找到默认文件")
            print()
            print("请使用以下格式运行:")
            print("  python run_audit.py -o <操作命令表.xlsx> -r <报备表.xlsx>")
            print()
            print("示例:")
            print("  python run_audit.py -o 操作命令表.xlsx -r 报备表.xlsx")
            sys.exit(1)
    
    sys.exit(main())
