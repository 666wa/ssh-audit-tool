#!/usr/bin/env python3
"""
SSH命令核查工具 - 统一入口

支持三种稽核模式：
  1. ssh       - 标准SSH绕行稽核
  2. 4a        - 4A绕行核实
  3. violation  - 账号违规使用

用法：
  python audit.py                          # 交互式引导
  python audit.py --mode ssh -o 操作表 -r 报备表
  python audit.py --mode 4a -o 操作表 -r 报备表
  python audit.py --mode violation -o 操作表 -r 报备表
"""
import os
import sys
import glob
import argparse
import logging

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


# ============================================================
# 交互式文件发现与选择
# ============================================================

def find_data_folders():
    """扫描当前目录下的日期文件夹（格式：YYYY-MM-DD）"""
    import re
    folders = []
    for name in sorted(os.listdir('.'), reverse=True):
        if os.path.isdir(name) and re.match(r'^\d{4}-\d{2}-\d{2}$', name):
            folders.append(name)
    return folders


def find_files_in_folder(folder):
    """在指定文件夹中查找操作表和报备表"""
    operation_files = []
    report_files = []

    for f in sorted(os.listdir(folder)):
        path = os.path.join(folder, f)
        if not os.path.isfile(path):
            continue
        lower = f.lower()
        # 跳过结果文件
        if f.startswith('结果-') or f.startswith('结果_'):
            continue
        # 报备表识别
        if '报备' in f:
            report_files.append(path)
        # 操作表识别
        elif ('ssh' in lower or 'sdc' in lower or '使用ssh' in f
              or '4a' in lower or '绕行' in f
              or '违规' in f or 'violation' in lower):
            if lower.endswith(('.csv', '.xlsx', '.xls')):
                operation_files.append(path)

    return operation_files, report_files


def detect_mode(operation_file):
    """根据操作表文件名自动推断稽核模式"""
    name = os.path.basename(operation_file).lower()
    if '4a' in name or '绕行核实' in name:
        return '4a'
    elif '违规' in name or 'violation' in name:
        return 'violation'
    else:
        return 'ssh'


def prompt_choice(prompt_text, options):
    """交互式选择"""
    print(f"\n{prompt_text}")
    for i, opt in enumerate(options, 1):
        print(f"  [{i}] {opt}")
    while True:
        try:
            choice = input(f"\n请选择 (1-{len(options)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(options):
                return options[idx]
        except (ValueError, EOFError):
            pass
        print("输入无效，请重新选择")


def interactive_mode():
    """交互式引导模式"""
    print("=" * 60)
    print("  SSH命令核查工具 - 交互式模式")
    print("=" * 60)

    # 1. 选择稽核模式
    mode = prompt_choice("请选择稽核模式:", [
        "ssh       - 标准SSH绕行稽核",
        "4a        - 4A绕行核实",
        "violation - 账号违规使用"
    ])
    mode = mode.split()[0]  # 提取模式名

    # 2. 扫描数据文件夹
    folders = find_data_folders()
    if not folders:
        print("\n未找到日期文件夹（格式：YYYY-MM-DD），请手动指定文件路径")
        return interactive_manual_input(mode)

    # 3. 选择数据文件夹
    folder = prompt_choice("请选择数据文件夹:", folders)

    # 4. 自动发现文件
    operation_files, report_files = find_files_in_folder(folder)

    # 选择操作表
    if not operation_files:
        print(f"\n在 {folder} 中未找到操作表文件")
        return interactive_manual_input(mode)
    elif len(operation_files) == 1:
        operation_file = operation_files[0]
        print(f"\n自动选择操作表: {operation_file}")
    else:
        operation_file = prompt_choice("请选择操作表:", operation_files)

    # 选择报备表
    if not report_files:
        # 在其他文件夹中搜索报备表
        print(f"\n在 {folder} 中未找到报备表，搜索其他文件夹...")
        all_reports = []
        for f in folders:
            _, reps = find_files_in_folder(f)
            all_reports.extend(reps)
        if not all_reports:
            print("未找到任何报备表文件")
            return interactive_manual_input(mode)
        report_file = prompt_choice("请选择报备表:", all_reports)
    elif len(report_files) == 1:
        report_file = report_files[0]
        print(f"自动选择报备表: {report_file}")
    else:
        report_file = prompt_choice("请选择报备表:", report_files)

    # 自动推断模式（如果用户选的文件和模式不匹配，提示一下）
    detected = detect_mode(operation_file)
    if detected != mode:
        print(f"\n提示: 根据文件名推断模式为 '{detected}'，当前选择为 '{mode}'")
        confirm = input("是否切换？(y/N): ").strip().lower()
        if confirm == 'y':
            mode = detected

    return mode, operation_file, report_file


def interactive_manual_input(mode):
    """手动输入文件路径"""
    operation_file = input("\n请输入操作表文件路径: ").strip().strip('"')
    report_file = input("请输入报备表文件路径: ").strip().strip('"')

    if not os.path.exists(operation_file):
        print(f"错误: 文件不存在 - {operation_file}")
        sys.exit(1)
    if not os.path.exists(report_file):
        print(f"错误: 文件不存在 - {report_file}")
        sys.exit(1)

    return mode, operation_file, report_file


# ============================================================
# 运行稽核
# ============================================================

def run_ssh_audit(operation_file, report_file, output=None, no_timestamp=False, log_level='INFO'):
    """运行标准SSH稽核"""
    sys.argv = ['audit.py', '-o', operation_file, '-r', report_file]
    if output:
        sys.argv.extend(['--output', output])
    if no_timestamp:
        sys.argv.append('--no-timestamp')
    sys.argv.extend(['--log-level', log_level])

    from ssh_audit_tool.main import main
    return main()


def run_4a_audit(operation_file, report_file, output=None, no_timestamp=False, log_level='INFO'):
    """运行4A绕行核实"""
    sys.argv = ['audit.py', '-o', operation_file, '-r', report_file]
    if output:
        sys.argv.extend(['--output', output])
    if no_timestamp:
        sys.argv.append('--no-timestamp')
    sys.argv.extend(['--log-level', log_level])

    from ssh_audit_tool.main_4a import main
    return main()


def run_violation_audit(operation_file, report_file, output=None, no_timestamp=False, log_level='INFO'):
    """运行账号违规使用稽核"""
    sys.argv = ['run_audit_violation.py', '-o', operation_file, '-r', report_file]
    if output:
        sys.argv.extend(['--output', output])
    if no_timestamp:
        sys.argv.append('--no-timestamp')
    sys.argv.extend(['--log-level', log_level])

    from run_audit_violation import main
    return main()


MODE_RUNNERS = {
    'ssh': run_ssh_audit,
    '4a': run_4a_audit,
    'violation': run_violation_audit,
}

MODE_NAMES = {
    'ssh': '标准SSH绕行稽核',
    '4a': '4A绕行核实',
    'violation': '账号违规使用',
}


# ============================================================
# 主入口
# ============================================================

def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='SSH命令核查工具 - 统一入口',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
模式说明:
  ssh        标准SSH绕行稽核（操作命令表含中文列名）
  4a         4A绕行核实（操作表含英文列名如op_fort_content）
  violation  账号违规使用（只核查IP对，不考虑账号）

示例:
  python audit.py                                    # 交互式引导
  python audit.py --mode ssh -o 操作表.csv -r 报备表.csv
  python audit.py --mode 4a -o 4A表.csv -r 报备表.csv
  python audit.py --mode violation -o 违规表.csv -r 报备表.csv
        """
    )

    parser.add_argument('--mode', '-m', choices=['ssh', '4a', 'violation'],
                        help='稽核模式: ssh/4a/violation')
    parser.add_argument('-o', '--operation', help='操作表文件路径')
    parser.add_argument('-r', '--report', help='报备表文件路径')
    parser.add_argument('--output', help='输出文件路径（可选）')
    parser.add_argument('--no-timestamp', action='store_true',
                        help='输出文件名不添加时间戳')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                        default='INFO', help='日志级别（默认: INFO）')

    return parser.parse_args()


def main():
    args = parse_args()

    # 判断是否进入交互式模式
    if not args.mode or not args.operation or not args.report:
        if args.mode and (not args.operation or not args.report):
            print("错误: 指定了 --mode 但缺少 -o 或 -r 参数")
            sys.exit(1)
        # 交互式模式
        mode, operation_file, report_file = interactive_mode()
    else:
        mode = args.mode
        operation_file = args.operation
        report_file = args.report

    # 验证文件存在
    if not os.path.exists(operation_file):
        print(f"错误: 操作表文件不存在 - {operation_file}")
        sys.exit(1)
    if not os.path.exists(report_file):
        print(f"错误: 报备表文件不存在 - {report_file}")
        sys.exit(1)

    # 运行
    print(f"\n模式: {MODE_NAMES.get(mode, mode)}")
    print(f"操作表: {operation_file}")
    print(f"报备表: {report_file}")
    print()

    runner = MODE_RUNNERS.get(mode)
    if not runner:
        print(f"错误: 未知模式 '{mode}'")
        sys.exit(1)

    return runner(
        operation_file, report_file,
        output=args.output,
        no_timestamp=args.no_timestamp,
        log_level=args.log_level
    )


if __name__ == '__main__':
    sys.exit(main())
