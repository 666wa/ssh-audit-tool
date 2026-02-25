"""
日期提取模块 - 从文件名中提取日期
"""
import re
import logging
from datetime import datetime
from typing import Optional


class DateExtractor:
    """从文件名中提取日期的工具类"""
    
    @staticmethod
    def extract_date_from_filename(filename: str) -> Optional[str]:
        """
        从文件名中提取日期
        
        支持的格式：
        - 月-使用ssh命令连接其它设备-SDC数据源(每日分析)_2026-01-28_09-43-47-284_583
        - 其他包含YYYY-MM-DD格式的文件名
        
        Args:
            filename: 文件名（可以包含路径）
        
        Returns:
            提取的日期字符串（YYYY-MM-DD格式），如果提取失败返回None
        """
        if not filename:
            return None
        
        logger = logging.getLogger()
        
        # 提取文件名部分（去掉路径）
        import os
        basename = os.path.basename(filename)
        
        # 匹配YYYY-MM-DD格式的日期
        # 支持的分隔符：- 和 /
        date_patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{4}/\d{2}/\d{2})',  # YYYY/MM/DD
            r'(\d{4}\d{2}\d{2})',    # YYYYMMDD
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, basename)
            if match:
                date_str = match.group(1)
                
                # 验证日期是否有效
                try:
                    # 统一转换为YYYY-MM-DD格式
                    if '-' in date_str:
                        # 已经是YYYY-MM-DD格式
                        datetime.strptime(date_str, '%Y-%m-%d')
                        logger.debug(f"从文件名 '{basename}' 提取日期: {date_str}")
                        return date_str
                    elif '/' in date_str:
                        # YYYY/MM/DD格式，转换为YYYY-MM-DD
                        dt = datetime.strptime(date_str, '%Y/%m/%d')
                        result = dt.strftime('%Y-%m-%d')
                        logger.debug(f"从文件名 '{basename}' 提取日期: {date_str} -> {result}")
                        return result
                    else:
                        # YYYYMMDD格式，转换为YYYY-MM-DD
                        dt = datetime.strptime(date_str, '%Y%m%d')
                        result = dt.strftime('%Y-%m-%d')
                        logger.debug(f"从文件名 '{basename}' 提取日期: {date_str} -> {result}")
                        return result
                        
                except ValueError:
                    # 日期格式无效，继续尝试下一个模式
                    continue
        
        logger.warning(f"无法从文件名 '{basename}' 中提取有效日期")
        return None
    
    @staticmethod
    def parse_date_string(date_str: str) -> Optional[datetime]:
        """
        解析日期字符串为datetime对象
        
        Args:
            date_str: 日期字符串
        
        Returns:
            datetime对象，解析失败返回None
        """
        if not date_str:
            return None
        
        # 支持的日期格式
        date_formats = [
            '%Y-%m-%d',
            '%Y/%m/%d',
            '%Y-%m-%d %H:%M:%S',
            '%Y/%m/%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y/%m/%d %H:%M',
        ]
        
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    @staticmethod
    def is_date_in_range(file_date: str, start_date: str, end_date: str) -> tuple[bool, str]:
        """
        检查文件日期是否在指定范围内
        
        Args:
            file_date: 文件日期（YYYY-MM-DD格式）
            start_date: 开始日期（生效时间）
            end_date: 结束日期（失效时间）
        
        Returns:
            元组 (是否在范围内, 详细说明)
        """
        if not file_date:
            return False, "文件日期无效"
        
        file_dt = DateExtractor.parse_date_string(file_date)
        if not file_dt:
            return False, f"无法解析文件日期: {file_date}"
        
        # 解析开始日期
        start_dt = None
        if start_date and str(start_date).strip() and str(start_date).strip() != 'nan':
            start_dt = DateExtractor.parse_date_string(str(start_date).strip())
        
        # 解析结束日期
        end_dt = None
        if end_date and str(end_date).strip() and str(end_date).strip() != 'nan':
            end_dt = DateExtractor.parse_date_string(str(end_date).strip())
        
        # 检查是否早于生效时间
        if start_dt and file_dt < start_dt:
            return False, f"文件日期({file_date})早于生效时间({start_date})"
        
        # 检查是否晚于失效时间
        if end_dt and file_dt > end_dt:
            return False, f"文件日期({file_date})晚于失效时间({end_date})"
        
        # 在有效范围内
        time_range = f"{start_date or '无限制'}~{end_date or '永久'}"
        return True, f"文件日期({file_date})在有效期内({time_range})"