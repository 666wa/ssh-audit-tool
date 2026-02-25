"""
文件处理模块 - 支持Excel和CSV格式
"""
import os
import logging
import pandas as pd
from typing import List
from ssh_audit_tool.config import (
    REQUIRED_OPERATION_COLUMNS,
    REQUIRED_REPORT_COLUMNS,
    OUTPUT_COLUMN_NAME
)


class FileHandler:
    """文件读写处理器（支持Excel和CSV）"""
    
    @staticmethod
    def validate_columns(df: pd.DataFrame, required_columns: List[str]) -> bool:
        """
        验证DataFrame是否包含所有必需的列
        
        Args:
            df: 待验证的DataFrame
            required_columns: 必需的列名列表
        
        Returns:
            包含所有必需列返回True，否则抛出ValueError
        
        Raises:
            ValueError: 当缺少必需列时
        """
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"缺少必需的列: {', '.join(missing_columns)}")
        
        return True
    
    @staticmethod
    def read_file(file_path: str, required_columns: List[str] = None) -> pd.DataFrame:
        """
        读取文件（自动识别Excel或CSV格式）
        
        Args:
            file_path: 文件路径
            required_columns: 必需的列名列表（可选）
        
        Returns:
            DataFrame
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必需列
        """
        logger = logging.getLogger()
        
        # 检查文件是否存在
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件扩展名
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        
        try:
            if ext == '.csv':
                # 读取CSV文件，自动尝试多种编码
                logger.info(f"正在读取CSV文件: {file_path}")
                try:
                    df = pd.read_csv(file_path, encoding='utf-8-sig')
                except UnicodeDecodeError:
                    logger.info("UTF-8编码读取失败，尝试GBK编码...")
                    df = pd.read_csv(file_path, encoding='gbk')
            elif ext in ['.xlsx', '.xls']:
                # 读取Excel文件
                logger.info(f"正在读取Excel文件: {file_path}")
                df = pd.read_excel(file_path)
            else:
                raise ValueError(f"不支持的文件格式: {ext}，仅支持 .xlsx, .xls, .csv")
            
            # 验证必需列
            if required_columns:
                FileHandler.validate_columns(df, required_columns)
            
            return df
            
        except PermissionError as e:
            raise PermissionError(f"无法访问文件（权限不足）: {file_path}") from e
        except Exception as e:
            raise ValueError(f"文件读取错误: {file_path}, 错误: {str(e)}") from e
    
    @staticmethod
    def read_operation_log(file_path: str) -> pd.DataFrame:
        """
        读取操作命令表
        
        Args:
            file_path: 文件路径（支持Excel和CSV）
        
        Returns:
            包含操作记录的DataFrame
        """
        logger = logging.getLogger()
        df = FileHandler.read_file(file_path, REQUIRED_OPERATION_COLUMNS)
        logger.info(f"成功读取操作记录: {len(df)} 条")
        return df
    
    @staticmethod
    def read_report_table(file_path: str) -> pd.DataFrame:
        """
        读取报备表（优化大文件读取）
        
        Args:
            file_path: 文件路径（支持Excel和CSV）
        
        Returns:
            包含报备记录的DataFrame
        """
        logger = logging.getLogger()
        
        # 读取文件
        df = FileHandler.read_file(file_path, REQUIRED_REPORT_COLUMNS)
        
        # 删除说明行和示例行（前两行数据）
        if len(df) > 0 and '允许录入多个' in str(df.iloc[0].get('访问账号', '')):
            df = df.iloc[1:]  # 跳过第一行（示例行）
        
        # 重置索引
        df = df.reset_index(drop=True)
        
        # 数据清洗：移除空行
        df = df.dropna(subset=['访问账号', '本端主机IP', '对端主机IP'], how='all')
        
        logger.info(f"成功读取报备记录: {len(df)} 条")
        return df
    
    @staticmethod
    def write_result(df: pd.DataFrame, output_path: str) -> None:
        """
        写入结果文件（自动识别格式）
        
        Args:
            df: 包含核查结果的DataFrame
            output_path: 输出文件路径
        """
        logger = logging.getLogger()
        
        try:
            logger.info(f"正在写入结果文件: {output_path}")
            
            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
                logger.info(f"创建输出目录: {output_dir}")
            
            # 检查文件是否已存在
            if os.path.exists(output_path):
                logger.warning(f"输出文件已存在，将被覆盖: {output_path}")
            
            # 获取文件扩展名
            _, ext = os.path.splitext(output_path)
            ext = ext.lower()
            
            # 根据扩展名选择写入方式
            if ext == '.csv':
                # 写入CSV文件（性能更好）
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
            elif ext in ['.xlsx', '.xls']:
                # 写入Excel文件
                df.to_excel(output_path, index=False, engine='openpyxl')
            else:
                # 默认写入CSV
                output_path = output_path + '.csv'
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logger.warning(f"未指定文件格式，默认保存为CSV: {output_path}")
            
            # 获取文件大小
            file_size = os.path.getsize(output_path)
            size_mb = file_size / (1024 * 1024)
            
            logger.info(f"结果文件已保存: {output_path}")
            logger.info(f"文件大小: {size_mb:.2f} MB ({file_size:,} 字节)")
            
        except PermissionError as e:
            logger.error(f"无法写入文件（权限不足）: {output_path}")
            logger.error("可能的原因：")
            logger.error("  1. 文件正在被其他程序（如Excel）打开")
            logger.error("  2. 没有写入权限")
            logger.error("  3. 文件被设置为只读")
            raise PermissionError(f"无法写入文件（权限不足）: {output_path}") from e
        except OSError as e:
            if "No space left" in str(e) or "磁盘空间不足" in str(e):
                logger.error(f"磁盘空间不足，无法写入文件: {output_path}")
                raise OSError(f"磁盘空间不足，无法写入文件: {output_path}") from e
            raise
