"""
SSH命令核查工具 - 账号违规使用模板专用运行脚本

处理"账号违规使用_大数据分公司-策略反馈"格式的CSV文件
这个模板的特点：
1. 列名使用英文（id, audit_desc, client_ip, server_ip等）
2. 包含中文列名作为第二行
3. 操作内容在op_fort_content列
4. 源IP在client_ip列，目标IP在server_ip列
5. 账号信息在sub_acct_name列

使用方法:
    python run_audit_violation.py
"""
import os
import sys
import argparse
import logging
import pandas as pd
from collections import Counter

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ssh_audit_tool.auditor import Auditor
from ssh_audit_tool.fast_auditor import FastAuditor
from ssh_audit_tool.file_handler import FileHandler
from ssh_audit_tool.utils import get_output_path
from ssh_audit_tool.date_extractor import DateExtractor
from ssh_audit_tool.config import (
    setup_logging,
    RESULT_REPORTED,
    RESULT_NOT_REPORTED,
    RESULT_INVALID_COMMAND,
    RESULT_EXPIRED,
    RESULT_INVALID_SOURCE_IP,
    USE_FAST_AUDITOR
)


# 默认文件路径配置
DEFAULT_OPERATION_FILE = r"2026-02-03\账号违规使用_大数据分公司-策略反馈-20260203_095931.csv"
DEFAULT_REPORT_FILE = r"2026-01-29\主机互访报备-20260129.csv"  # 使用最新的报备表
DEFAULT_OUTPUT_DIR = r"2026-02-03"


def read_violation_csv(file_path: str) -> pd.DataFrame:
    """
    读取账号违规使用CSV文件
    
    特殊处理：
    1. 跳过第二行（中文列名）
    2. 使用第一行作为列名
    
    Args:
        file_path: CSV文件路径
    
    Returns:
        DataFrame对象
    """
    logger = logging.getLogger()
    logger.info(f"正在读取违规使用CSV文件: {file_path}")
    
    try:
        # 读取CSV，跳过第二行
        df = pd.read_csv(file_path, encoding='utf-8-sig', skiprows=[1])
        
        logger.info(f"成功读取记录: {len(df)} 条")
        logger.info(f"列名: {list(df.columns)}")
        
        # 验证必需的列
        required_columns = ['sub_acct_name', 'client_ip', 'server_ip', 'op_fort_content', 'op_time']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"缺少必需的列: {missing_columns}")
        
        return df
        
    except Exception as e:
        logger.error(f"读取CSV文件失败: {e}")
        raise


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='SSH命令核查工具 - 账号违规使用模板专用',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python run_audit_violation.py
  python run_audit_violation.py -o 违规使用.csv -r 报备表.csv
  python run_audit_violation.py -o 违规使用.csv -r 报备表.csv --output 结果.csv
        """
    )
    
    parser.add_argument(
        '-o', '--operation',
        help='账号违规使用CSV文件路径'
    )
    
    parser.add_argument(
        '-r', '--report',
        help='报备表文件路径'
    )
    
    parser.add_argument(
        '--output',
        help='输出文件路径（可选）'
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
        logger.info("SSH命令核查工具启动（账号违规使用模板）")
        logger.info("=" * 60)
        
        # 确定文件路径
        operation_file = args.operation if args.operation else DEFAULT_OPERATION_FILE
        report_file = args.report if args.report else DEFAULT_REPORT_FILE
        
        # 检查文件是否存在
        if not os.path.exists(operation_file):
            logger.error(f"操作文件不存在: {operation_file}")
            return 1
        
        if not os.path.exists(report_file):
            logger.error(f"报备表文件不存在: {report_file}")
            return 1
        
        # 1. 读取违规使用CSV
        logger.info(f"操作表: {operation_file}")
        operation_df = read_violation_csv(operation_file)
        
        # 1.5 从文件名提取日期
        file_date = DateExtractor.extract_date_from_filename(operation_file)
        if file_date:
            logger.info(f"从文件名提取的日期: {file_date}")
        else:
            logger.warning("无法从文件名提取日期，将跳过时间范围验证")
        
        # 2. 读取报备表（复用FileHandler）
        logger.info(f"报备表: {report_file}")
        report_df = FileHandler.read_report_table(report_file)
        
        # 3. 创建核查器
        if USE_FAST_AUDITOR:
            logger.info("使用高性能审计器")
            auditor = FastAuditor(report_df, file_date)
        else:
            logger.info("使用标准审计器")
            auditor = Auditor(report_df, file_date)
        
        # 4. 执行核查
        logger.info("开始核查操作记录...")
        logger.info(f"总记录数: {len(operation_df)}")
        logger.info(f"报备记录数: {len(report_df)}")
        logger.info("-" * 60)
        
        results = []
        matched_rows = []
        details = []
        
        total = len(operation_df)
        progress_interval = max(1, total // 20)  # 显示20次进度
        
        for idx, row in operation_df.iterrows():
            # 提取字段（使用英文列名）
            # 违规使用稽核：只核查IP对（本端IP和对端IP），不考虑账号和命令
            server_ip = str(row.get('server_ip', ''))    # 服务器地址 → 本端IP
            dst_ip = str(row.get('dst_ip', ''))          # 目的地址 → 对端IP
            
            # 检查本端IP是否有效
            if not server_ip or server_ip == 'nan' or not server_ip.strip():
                logger.warning(f"记录 {idx + 1}: 无法获取有效本端IP - server_ip: {server_ip}")
                results.append(RESULT_INVALID_SOURCE_IP)
                matched_rows.append('')
                details.append('无法获取有效本端IP（server_ip为空）')
                continue
            
            # 检查对端IP是否有效
            if not dst_ip or dst_ip == 'nan' or not dst_ip.strip():
                logger.warning(f"记录 {idx + 1}: 无法获取有效对端IP - dst_ip: {dst_ip}")
                results.append(RESULT_INVALID_SOURCE_IP)
                matched_rows.append('')
                details.append('无法获取有效对端IP（dst_ip为空）')
                continue
            
            # 违规使用稽核：只核查IP对，不核查账号
            # 直接使用IP进行匹配，不需要构造SSH命令
            result, matched_row, detail = auditor.audit_violation_record(
                server_ip.strip(),  # 本端IP（服务器地址）
                dst_ip.strip()      # 对端IP（目的地址）
            )
            results.append(result)
            matched_rows.append(matched_row)
            details.append(detail)
            
            # 显示进度
            if (idx + 1) % progress_interval == 0 or (idx + 1) == total:
                percentage = (idx + 1) / total * 100
                logger.info(f"进度: {idx + 1}/{total} ({percentage:.1f}%)")
        
        logger.info("-" * 60)
        
        # 5. 添加结果列
        operation_df['对比结果'] = results
        operation_df['命中序号'] = matched_rows
        operation_df['详细说明'] = details
        
        # 6. 生成输出文件
        if args.output:
            output_path = args.output
        else:
            output_path = get_output_path(
                operation_file,
                add_timestamp=not args.no_timestamp,
                output_dir=DEFAULT_OUTPUT_DIR
            )
        
        # 写入结果
        logger.info(f"正在写入结果文件: {output_path}")
        operation_df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"结果文件已保存: {output_path}")
        
        # 获取文件大小
        file_size = os.path.getsize(output_path)
        logger.info(f"文件大小: {file_size/1024/1024:.2f} MB ({file_size:,} 字节)")
        
        # 7. 统计结果
        logger.info("-" * 60)
        result_counts = Counter(results)
        logger.info(f"核查完成，共处理 {total} 条记录")
        
        for result, count in result_counts.items():
            percentage = count / total * 100
            logger.info(f"  {result}: {count} 条 ({percentage:.1f}%)")
        
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
        logger.error("请检查CSV文件格式和必需列")
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
