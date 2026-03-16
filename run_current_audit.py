#!/usr/bin/env python3
"""
SSH绕行稽核运行脚本 - 2026-03-16
处理指定的操作记录和报备表文件
"""
import os
import sys
import subprocess
from pathlib import Path

def main():
    """主函数"""
    # 文件路径配置
    base_path = r"d:\DeskTop\gaoyf工作交接\ssh绕行脚本\2026-03-16\11\ssh-audit-tool\0316"
    operation_file = os.path.join(base_path, "月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2026-03-13_18-02-53-859_243.csv")
    report_file = os.path.join(base_path, "主机互访报备-2026-03-16.csv")
    
    # 检查文件是否存在
    if not os.path.exists(operation_file):
        print(f"❌ 操作记录文件不存在: {operation_file}")
        print("请将文件复制到当前目录")
        return 1
    
    if not os.path.exists(report_file):
        print(f"❌ 报备表文件不存在: {report_file}")
        print("请将文件复制到当前目录")
        return 1
    
    print("🚀 开始SSH绕行稽核...")
    print(f"📄 操作记录: {operation_file}")
    print(f"📋 报备表: {report_file}")
    print("-" * 60)
    
    # 构建运行命令
    cmd = [
        sys.executable, 
        "run_audit.py",
        "-o", operation_file,
        "-r", report_file,
        "--log-level", "INFO"
    ]
    
    try:
        # 运行稽核
        result = subprocess.run(cmd, check=True, capture_output=False)
        print("\n✅ 稽核完成！")
        return result.returncode
    
    except subprocess.CalledProcessError as e:
        print(f"\n❌ 稽核失败: {e}")
        return e.returncode
    
    except Exception as e:
        print(f"\n❌ 运行错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())