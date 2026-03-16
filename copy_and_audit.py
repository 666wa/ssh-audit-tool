#!/usr/bin/env python3
"""
复制文件并执行SSH绕行稽核
"""
import os
import sys
import shutil
import subprocess

def main():
    """主函数"""
    # 源文件路径
    source_dir = r"d:\DeskTop\gaoyf工作交接\ssh绕行脚本\2026-03-16\11\ssh-audit-tool\0316"
    operation_file = "月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2026-03-13_18-02-53-859_243.csv"
    report_file = "主机互访报备-2026-03-16.csv"
    
    source_operation = os.path.join(source_dir, operation_file)
    source_report = os.path.join(source_dir, report_file)
    
    print("🔄 正在复制文件到工作区...")
    
    try:
        # 复制操作记录文件
        if os.path.exists(source_operation):
            shutil.copy2(source_operation, operation_file)
            print(f"✅ 已复制: {operation_file}")
        else:
            print(f"❌ 源文件不存在: {source_operation}")
            return 1
        
        # 复制报备表文件
        if os.path.exists(source_report):
            shutil.copy2(source_report, report_file)
            print(f"✅ 已复制: {report_file}")
        else:
            print(f"❌ 源文件不存在: {source_report}")
            return 1
        
        print("\n🚀 开始SSH绕行稽核...")
        print("-" * 60)
        
        # 运行稽核
        cmd = [sys.executable, "run_audit.py", "-o", operation_file, "-r", report_file]
        result = subprocess.run(cmd, check=True)
        
        print("\n✅ 稽核完成！")
        return 0
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())