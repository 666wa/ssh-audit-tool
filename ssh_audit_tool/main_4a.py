"""
SSH命令核查工具 - 4A绕行核实模板专用主程序
"""
import sys
import argparse
import logging
from collections import Counter
from ssh_audit_tool.config_4a import (
    setup_logging, 
    OUTPUT_COLUMN_NAME, 
    MATCHED_ROW_COLUMN_NAME,
    DETAIL_COLUMN_NAME,
    DEFAULT_OUTPUT_DIR,
    RESULT_INVALID_SOURCE_IP
)
from ssh_audit_tool.file_handler_4a import FileHandler4A
from ssh_audit_tool.auditor import Auditor
from ssh_audit_tool.utils import get_output_path, print_statistics, get_source_ip


def parse_arguments():
    """
    解析命令行参数
    
    Returns:
        解析后的参数对象
    """
    parser = argparse.ArgumentParser(
        description='SSH命令核查工具 - 4A绕行核实模板专用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python -m ssh_audit_tool.main_4a -o 4A绕行核实表.csv -r 报备表.csv
  python -m ssh_audit_tool.main_4a -o 4A绕行核实表.csv -r 报备表.csv --output 结果.csv
  python -m ssh_audit_tool.main_4a -o 4A绕行核实表.csv -r 报备表.csv --no-timestamp
        """
    )
    
    parser.add_argument(
        '-o', '--operation',
        required=True,
        help='4A绕行核实操作表文件路径（CSV/Excel格式）'
    )
    
    parser.add_argument(
        '-r', '--report',
        required=True,
        help='报备表文件路径（CSV/Excel格式）'
    )
    
    parser.add_argument(
        '--output',
        help='输出文件路径（可选，默认在操作表同目录生成）'
    )
    
    parser.add_argument(
        '--no-timestamp',
        action='store_true',
        help='输出文件名不添加时间戳'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='日志级别（默认: INFO）'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    # 解析命令行参数
    args = parse_arguments()
    
    # 设置日志
    log_level = getattr(logging, args.log_level)
    setup_logging(log_level=log_level)
    logger = logging.getLogger()
    
    try:
        logger.info("=" * 60)
        logger.info("SSH命令核查工具启动（4A绕行核实模板）")
        logger.info("=" * 60)
        
        # 1. 读取4A绕行核实操作表
        logger.info(f"操作表: {args.operation}")
        operation_df = FileHandler4A.read_operation_log(args.operation)
        
        # 2. 读取报备表
        logger.info(f"报备表: {args.report}")
        report_df = FileHandler4A.read_report_table(args.report)
        
        # 3. 创建核查器
        auditor = Auditor(report_df)
        
        # 4. 执行核查
        logger.info("开始核查操作记录...")
        logger.info(f"总记录数: {len(operation_df)}")
        logger.info(f"报备记录数: {len(report_df)}")
        logger.info("-" * 60)
        
        results = []
        matched_rows = []
        details = []  # 新增：详细说明列表
        
        total = len(operation_df)
        progress_interval = max(1, total // 20)  # 显示20次进度
        
        for idx, row in operation_df.iterrows():
            # 4A模板的列名映射
            audit_desc = str(row.get('audit_desc', ''))             # 审计说明
            operation_content = str(row.get('op_fort_content', ''))  # 操作内容（SSH命令）
            resource_ip = str(row.get('res_ip', ''))                 # 资源IP（本端IP）
            resource_name = str(row.get('res_name', ''))             # 资源名称（本端IP备用）
            server_ip = str(row.get('server_ip', ''))                # 目的地址（特殊情况下作为对端IP）
            main_account = str(row.get('main_acct_name', ''))        # 主账号名称
            operation_time = str(row.get('op_time', ''))             # 操作时间
            
            # 获取本端资源IP（优先从资源IP，其次从资源名称）
            source_ip = get_source_ip(resource_ip, resource_name)
            
            # 如果无法获取有效的本端IP，标记为异常
            if not source_ip:
                logger.warning(f"记录 {idx + 1}: 无法获取有效本端IP - 资源IP: {resource_ip}, 资源名称: {resource_name}")
                results.append(RESULT_INVALID_SOURCE_IP)
                matched_rows.append('')
                details.append('')
                continue
            
            # 优先使用从账号名称（如果存在）
            sub_account = str(row.get('sub_acct_name', ''))
            default_account = sub_account if sub_account and sub_account != 'nan' else main_account
            
            # 判断是否需要使用特殊逻辑（根据审计说明）
            use_server_ip_as_target = '过堡垒机操作存在跳板绕行' in audit_desc
            
            if use_server_ip_as_target:
                # 特殊情况：使用目的地址作为对端IP（传入操作时间）
                result, matched_row, detail = auditor.audit_record_with_target_ip(
                    operation_content, 
                    source_ip, 
                    default_account,
                    server_ip,  # 直接使用目的地址作为对端IP
                    operation_time  # 传入操作时间
                )
            else:
                # 正常情况：从SSH命令提取对端IP（传入操作时间）
                result, matched_row, detail = auditor.audit_record(operation_content, source_ip, default_account, operation_time)
            
            results.append(result)
            matched_rows.append(matched_row)
            details.append(detail)
            
            # 显示进度
            if (idx + 1) % progress_interval == 0 or (idx + 1) == total:
                percentage = (idx + 1) / total * 100
                logger.info(f"进度: {idx + 1}/{total} ({percentage:.1f}%)")
        
        logger.info("-" * 60)
        
        # 5. 添加结果列
        operation_df[OUTPUT_COLUMN_NAME] = results
        operation_df[MATCHED_ROW_COLUMN_NAME] = matched_rows
        operation_df[DETAIL_COLUMN_NAME] = details  # 新增：详细说明列
        
        # 6. 生成输出文件
        if args.output:
            output_path = args.output
        else:
            # 使用配置中的默认输出目录
            output_path = get_output_path(
                args.operation, 
                add_timestamp=not args.no_timestamp,
                output_dir=DEFAULT_OUTPUT_DIR
            )
        
        FileHandler4A.write_result(operation_df, output_path)
        
        # 7. 统计结果
        logger.info("-" * 60)
        result_counts = Counter(results)
        print_statistics(dict(result_counts), total)
        
        logger.info("=" * 60)
        logger.info("核查完成！")
        logger.info(f"结果文件: {output_path}")
        logger.info("=" * 60)
        
        return 0
        
    except FileNotFoundError as e:
        logger.error(f"文件错误: {e}")
        logger.error("请检查文件路径是否正确")
        return 1
    
    except ValueError as e:
        logger.error(f"数据错误: {e}")
        logger.error("请检查文件格式和必需列")
        return 1
    
    except PermissionError as e:
        logger.error(f"权限错误: {e}")
        logger.error("请检查文件访问权限")
        return 1
    
    except Exception as e:
        logger.error(f"未预期的错误: {e}", exc_info=True)
        logger.error("请联系技术支持")
        return 1


if __name__ == '__main__':
    sys.exit(main())
