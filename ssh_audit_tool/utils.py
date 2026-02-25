"""
工具函数模块
"""
import os
import re
import logging
from typing import Dict, Optional
from pathlib import Path
from datetime import datetime


def extract_ip_from_text(text: str) -> Optional[str]:
    """
    从文本中提取有效的IPv4地址
    
    Args:
        text: 包含IP地址的文本
    
    Returns:
        提取到的第一个有效IP地址，如果没有则返回None
    """
    if not text or text.lower() in ['localhost', '127.0.0.1', 'nan', '']:
        return None
    
    # IPv4地址的正则表达式（支持前后有非数字字符）
    ipv4_pattern = r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    
    # 查找所有IPv4地址
    matches = re.findall(ipv4_pattern, str(text))
    
    # 验证并返回第一个有效的IPv4地址
    for ip in matches:
        parts = ip.split('.')
        try:
            if all(0 <= int(part) <= 255 for part in parts):
                return ip
        except ValueError:
            continue
    
    return None


def get_source_ip(resource_ip: str, resource_name: str) -> Optional[str]:
    """
    获取本端资源IP
    
    优先级：
    1. 从资源IP获取
    2. 从资源名称获取
    3. 返回None
    
    Args:
        resource_ip: 资源IP字段的值
        resource_name: 资源名称字段的值
    
    Returns:
        有效的IP地址，如果无法获取则返回None
    """
    # 1. 尝试从资源IP获取
    ip = extract_ip_from_text(resource_ip)
    if ip:
        return ip
    
    # 2. 尝试从资源名称获取
    ip = extract_ip_from_text(resource_name)
    if ip:
        return ip
    
    # 3. 无法获取
    return None


def get_output_filename(input_filename: str, add_timestamp: bool = False) -> str:
    """
    根据输入文件名生成输出文件名
    
    Args:
        input_filename: 输入文件名（可以是完整路径或仅文件名）
        add_timestamp: 是否添加时间戳
    
    Returns:
        输出文件名，格式为"结果-" + 原文件名 [+ 时间戳]
    
    Examples:
        >>> get_output_filename("test.xlsx")
        '结果-test.xlsx'
        >>> get_output_filename("test.xlsx", add_timestamp=True)
        '结果-test_20251225_183000.xlsx'
    """
    # 提取文件名（不含路径）
    basename = os.path.basename(input_filename)
    name, ext = os.path.splitext(basename)
    
    if add_timestamp:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"结果-{name}_{timestamp}{ext}"
    else:
        return f"结果-{basename}"


def validate_file_exists(file_path: str) -> bool:
    """
    验证文件是否存在
    
    Args:
        file_path: 文件路径
    
    Returns:
        文件存在返回True，否则返回False
    """
    return os.path.isfile(file_path)


def print_statistics(results: Dict[str, int], total: int = None) -> None:
    """
    打印统计信息
    
    Args:
        results: 统计结果字典，键为结果类型，值为数量
        total: 总记录数（可选，如果不提供则从results计算）
    """
    logger = logging.getLogger()
    
    if total is None:
        total = sum(results.values())
    
    logger.info(f"核查完成，共处理 {total} 条记录")
    
    # 按照固定顺序显示结果
    result_order = ['已报备', '未报备', '异常：非有效ssh命令', '异常：无法获取有效本端IP']
    
    for result_type in result_order:
        if result_type in results:
            count = results[result_type]
            percentage = (count / total * 100) if total > 0 else 0
            logger.info(f"  {result_type}: {count} 条 ({percentage:.1f}%)")
    
    # 显示其他未预期的结果类型
    for result_type, count in results.items():
        if result_type not in result_order:
            percentage = (count / total * 100) if total > 0 else 0
            logger.info(f"  {result_type}: {count} 条 ({percentage:.1f}%)")


def get_output_path(input_path: str, add_timestamp: bool = False, output_dir: str = None) -> str:
    """
    根据输入文件路径生成输出文件路径
    
    Args:
        input_path: 输入文件的完整路径
        add_timestamp: 是否添加时间戳
        output_dir: 输出目录（可选，如果不提供则使用输入文件的目录）
    
    Returns:
        输出文件的完整路径
    """
    output_filename = get_output_filename(input_path, add_timestamp)
    
    if output_dir:
        # 使用指定的输出目录
        return os.path.join(output_dir, output_filename)
    else:
        # 使用输入文件的目录
        directory = os.path.dirname(input_path)
        if directory:
            return os.path.join(directory, output_filename)
        else:
            return output_filename


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小
    
    Args:
        size_bytes: 文件大小（字节）
    
    Returns:
        格式化后的文件大小字符串
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} TB"


def get_file_info(file_path: str) -> Dict[str, str]:
    """
    获取文件信息
    
    Args:
        file_path: 文件路径
    
    Returns:
        包含文件信息的字典
    """
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        'path': file_path,
        'size': format_file_size(stat.st_size),
        'size_bytes': stat.st_size,
        'modified': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
    }
