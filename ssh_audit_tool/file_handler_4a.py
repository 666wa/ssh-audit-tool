"""
文件处理模块 - 4A绕行核实模板专用
"""
import pandas as pd
import logging
from typing import List
from ssh_audit_tool.config_4a import (
    REQUIRED_OPERATION_COLUMNS_4A,
    REQUIRED_REPORT_COLUMNS
)


class FileHandler4A:
    """4A模板文件处理器"""
    
    @staticmethod
    def read_operation_log(file_path: str) -> pd.DataFrame:
        """
        读取4A绕行核实操作记录表
        
        Args:
            file_path: 文件路径（支持.xlsx和.csv）
        
        Returns:
            DataFrame对象
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必需列
        """
        logger = logging.getLogger()
        logger.info(f"正在读取操作记录表: {file_path}")
        
        try:
            # 根据文件扩展名选择读取方式
            if file_path.endswith('.csv'):
                # 4A模板CSV有两行表头：第1行英文列名，第2行中文列名
                # 跳过第2行（中文列名），读取所有列
                for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(
                            file_path, 
                            encoding=encoding, 
                            skiprows=[1]
                        )
                        logger.info(f"使用CSV格式读取（编码: {encoding}，跳过中文表头）")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"无法识别CSV文件编码: {file_path}")
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                # Excel文件，跳过第2行（中文列名）
                df = pd.read_excel(
                    file_path, 
                    skiprows=[1]
                )
                logger.info(f"使用Excel格式读取（跳过中文表头）")
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            # 验证必需列
            missing_columns = [col for col in REQUIRED_OPERATION_COLUMNS_4A if col not in df.columns]
            if missing_columns:
                raise ValueError(f"操作记录表缺少必需列: {missing_columns}")
            
            logger.info(f"成功读取 {len(df)} 条操作记录")
            logger.info(f"列名: {list(df.columns)}")
            
            return df
            
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取操作记录表失败: {e}")
            raise
    
    @staticmethod
    def read_report_table(file_path: str) -> pd.DataFrame:
        """
        读取报备表（与原版相同）
        
        Args:
            file_path: 文件路径（支持.xlsx和.csv）
        
        Returns:
            DataFrame对象
        
        Raises:
            FileNotFoundError: 文件不存在
            ValueError: 文件格式错误或缺少必需列
        """
        logger = logging.getLogger()
        logger.info(f"正在读取报备表: {file_path}")
        
        try:
            # 根据文件扩展名选择读取方式
            if file_path.endswith('.csv'):
                # 尝试多种编码格式，读取所有列（包括时间列）
                for encoding in ['utf-8', 'gbk', 'gb2312', 'utf-8-sig']:
                    try:
                        df = pd.read_csv(
                            file_path, 
                            encoding=encoding
                        )
                        logger.info(f"使用CSV格式读取（编码: {encoding}）")
                        break
                    except UnicodeDecodeError:
                        continue
                else:
                    raise ValueError(f"无法识别CSV文件编码: {file_path}")
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pd.read_excel(file_path)
                logger.info(f"使用Excel格式读取")
            else:
                raise ValueError(f"不支持的文件格式: {file_path}")
            
            # 验证必需列
            missing_columns = [col for col in REQUIRED_REPORT_COLUMNS if col not in df.columns]
            if missing_columns:
                raise ValueError(f"报备表缺少必需列: {missing_columns}")
            
            logger.info(f"成功读取 {len(df)} 条报备记录")
            
            return df
            
        except FileNotFoundError:
            logger.error(f"文件不存在: {file_path}")
            raise
        except Exception as e:
            logger.error(f"读取报备表失败: {e}")
            raise
    
    @staticmethod
    def write_result(df: pd.DataFrame, output_path: str) -> None:
        """
        写入核查结果
        
        Args:
            df: 包含核查结果的DataFrame
            output_path: 输出文件路径
        """
        logger = logging.getLogger()
        logger.info(f"正在写入结果文件: {output_path}")
        
        try:
            # 根据文件扩展名选择写入方式
            if output_path.endswith('.csv'):
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logger.info("使用CSV格式写入")
            elif output_path.endswith('.xlsx'):
                df.to_excel(output_path, index=False, engine='openpyxl')
                logger.info("使用Excel格式写入")
            else:
                # 默认使用CSV格式
                output_path = output_path + '.csv'
                df.to_csv(output_path, index=False, encoding='utf-8-sig')
                logger.info("使用CSV格式写入（默认）")
            
            logger.info(f"结果文件写入成功: {output_path}")
            
        except Exception as e:
            logger.error(f"写入结果文件失败: {e}")
            raise
