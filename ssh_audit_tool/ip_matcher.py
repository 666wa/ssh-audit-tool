"""
IP地址匹配模块
"""
import re
import logging
from typing import Optional, Tuple, Dict, List
from functools import lru_cache


class IPMatcher:
    """IP地址匹配器，支持多种IP格式"""
    
    # 类级别的缓存，避免重复解析相同的IP范围字符串
    _range_cache: Dict[str, List[Tuple[int, int]]] = {}
    _ip_int_cache: Dict[str, int] = {}
    
    @staticmethod
    @lru_cache(maxsize=10000)
    def is_valid_ipv4(ip: str) -> bool:
        """
        验证是否为有效的IPv4地址（带缓存）
        
        Args:
            ip: IP地址字符串
        
        Returns:
            有效返回True，否则返回False
        """
        if not ip:
            return False
        
        pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
        match = re.match(pattern, ip.strip())
        
        if not match:
            return False
        
        # 检查每个部分是否在0-255范围内
        for part in match.groups():
            if int(part) > 255:
                return False
        
        return True
    
    @staticmethod
    def ip_to_int(ip: str) -> int:
        """
        将IP地址转换为整数（带缓存）
        
        Args:
            ip: IP地址字符串（如"192.168.1.1"）
        
        Returns:
            IP地址对应的整数值
        """
        # 使用缓存避免重复计算
        if ip in IPMatcher._ip_int_cache:
            return IPMatcher._ip_int_cache[ip]
        
        parts = ip.strip().split('.')
        result = (int(parts[0]) << 24) + (int(parts[1]) << 16) + \
                (int(parts[2]) << 8) + int(parts[3])
        
        # 缓存结果
        IPMatcher._ip_int_cache[ip] = result
        return result
    
    @staticmethod
    def parse_ip_range(ip_range: str) -> Optional[Tuple[int, int]]:
        """
        解析IP段格式（如"192.168.1.1-192.168.1.20"）
        
        Args:
            ip_range: IP段字符串
        
        Returns:
            (起始IP整数, 结束IP整数) 或 None（如果格式无效）
        """
        if '-' not in ip_range:
            return None
        
        parts = ip_range.split('-')
        if len(parts) != 2:
            return None
        
        start_ip = parts[0].strip()
        end_ip = parts[1].strip()
        
        if not IPMatcher.is_valid_ipv4(start_ip) or not IPMatcher.is_valid_ipv4(end_ip):
            return None
        
        return (IPMatcher.ip_to_int(start_ip), IPMatcher.ip_to_int(end_ip))
    
    @staticmethod
    def parse_ip_mask(ip_mask: str) -> Optional[Tuple[int, int]]:
        """
        解析IP掩码格式（如"192.168.1.0/24"）
        
        Args:
            ip_mask: CIDR格式的IP掩码字符串
        
        Returns:
            (网络起始IP整数, 网络结束IP整数) 或 None（如果格式无效）
        """
        if '/' not in ip_mask:
            return None
        
        parts = ip_mask.split('/')
        if len(parts) != 2:
            return None
        
        ip = parts[0].strip()
        try:
            mask_bits = int(parts[1].strip())
        except ValueError:
            return None
        
        if not IPMatcher.is_valid_ipv4(ip) or mask_bits < 0 or mask_bits > 32:
            return None
        
        # 计算网络地址和广播地址
        ip_int = IPMatcher.ip_to_int(ip)
        mask = (0xFFFFFFFF << (32 - mask_bits)) & 0xFFFFFFFF
        network = ip_int & mask
        broadcast = network | (~mask & 0xFFFFFFFF)
        
        return (network, broadcast)
    
    @staticmethod
    def is_ip_in_range(ip: str, start_ip: str, end_ip: str) -> bool:
        """
        判断IP是否在指定范围内
        
        Args:
            ip: 目标IP地址
            start_ip: 起始IP地址
            end_ip: 结束IP地址
        
        Returns:
            在范围内返回True，否则返回False
        """
        if not all([IPMatcher.is_valid_ipv4(ip), 
                   IPMatcher.is_valid_ipv4(start_ip), 
                   IPMatcher.is_valid_ipv4(end_ip)]):
            return False
        
        ip_int = IPMatcher.ip_to_int(ip)
        start_int = IPMatcher.ip_to_int(start_ip)
        end_int = IPMatcher.ip_to_int(end_ip)
        
        return start_int <= ip_int <= end_int
    
    @staticmethod
    def is_ip_in_subnet(ip: str, subnet: str) -> bool:
        """
        判断IP是否在指定子网内
        
        Args:
            ip: 目标IP地址
            subnet: CIDR格式的子网（如"192.168.1.0/24"）
        
        Returns:
            在子网内返回True，否则返回False
        """
        if not IPMatcher.is_valid_ipv4(ip):
            return False
        
        subnet_range = IPMatcher.parse_ip_mask(subnet)
        if not subnet_range:
            return False
        
        ip_int = IPMatcher.ip_to_int(ip)
        network_start, network_end = subnet_range
        
        return network_start <= ip_int <= network_end
    
    @staticmethod
    def parse_multiple_ip_ranges(ip_range_str: str) -> List[Tuple[int, int]]:
        """
        解析连续用"-"分隔的多个IP范围（带缓存优化）
        如: "10.230.72.1-10.230.72.254-10.230.73.1-10.230.73.254"
        
        使用智能配对：只有当两个相邻IP能组成有效范围时才配对，否则当作单独IP处理
        
        Args:
            ip_range_str: 包含多个IP范围的字符串
        
        Returns:
            IP范围列表，每个元素是(起始IP整数, 结束IP整数)的元组
        """
        # 使用缓存避免重复解析相同的字符串
        if ip_range_str in IPMatcher._range_cache:
            return IPMatcher._range_cache[ip_range_str]
        
        ranges = []
        parts = ip_range_str.split('-')
        
        # 如果只有2个部分，是标准的单个IP范围
        if len(parts) == 2:
            start_ip = parts[0].strip()
            end_ip = parts[1].strip()
            if IPMatcher.is_valid_ipv4(start_ip) and IPMatcher.is_valid_ipv4(end_ip):
                start_int = IPMatcher.ip_to_int(start_ip)
                end_int = IPMatcher.ip_to_int(end_ip)
                if start_int <= end_int:
                    ranges.append((start_int, end_int))
                else:
                    # 如果起始IP > 结束IP，当作两个单独的IP处理
                    ranges.append((start_int, start_int))
                    ranges.append((end_int, end_int))
        
        # 如果有多个部分，使用智能配对
        elif len(parts) > 2:
            i = 0
            while i < len(parts):
                if i + 1 < len(parts):
                    ip1 = parts[i].strip()
                    ip2 = parts[i + 1].strip()
                    
                    if IPMatcher.is_valid_ipv4(ip1) and IPMatcher.is_valid_ipv4(ip2):
                        ip1_int = IPMatcher.ip_to_int(ip1)
                        ip2_int = IPMatcher.ip_to_int(ip2)
                        
                        # 如果能组成有效范围，配对处理
                        if ip1_int <= ip2_int:
                            ranges.append((ip1_int, ip2_int))
                            i += 2  # 跳过两个IP
                        else:
                            # 否则当作单独IP处理
                            ranges.append((ip1_int, ip1_int))
                            i += 1  # 只跳过一个IP
                    else:
                        # 如果IP无效，跳过
                        i += 1
                else:
                    # 最后一个IP，当作单独IP处理
                    ip = parts[i].strip()
                    if IPMatcher.is_valid_ipv4(ip):
                        ip_int = IPMatcher.ip_to_int(ip)
                        ranges.append((ip_int, ip_int))
                    i += 1
        
        # 缓存结果（限制缓存大小避免内存泄漏）
        if len(IPMatcher._range_cache) < 50000:  # 限制缓存大小
            IPMatcher._range_cache[ip_range_str] = ranges
        
        return ranges
    
    @staticmethod
    def match_ip(target_ip: str, report_ip_str: str) -> bool:
        """
        匹配目标IP与报备表中的IP（支持多种格式，优化版本）
        
        Args:
            target_ip: 目标IP地址
            report_ip_str: 报备表中的IP字符串（可能包含多个IP，以顿号分隔）
        
        Returns:
            匹配成功返回True，否则返回False
        """
        if not target_ip or not report_ip_str:
            return False
        
        if not IPMatcher.is_valid_ipv4(target_ip):
            return False
        
        # 快速路径：如果是精确匹配
        if target_ip == report_ip_str.strip():
            return True
        
        target_int = IPMatcher.ip_to_int(target_ip)
        
        # 以顿号分隔多个IP格式
        ip_formats = report_ip_str.split('、')
        
        for ip_format in ip_formats:
            ip_format = ip_format.strip()
            
            if not ip_format:
                continue
            
            # 1. 尝试精确匹配（快速路径）
            if target_ip == ip_format:
                return True
            
            # 2. 检查是否是单个IP（避免不必要的解析）
            if IPMatcher.is_valid_ipv4(ip_format):
                continue  # 已经在上面检查过精确匹配了
            
            # 3. 尝试IP段匹配（支持单个范围和多个连续范围）
            elif '-' in ip_format and '/' not in ip_format:
                # 解析可能包含多个范围的字符串（使用缓存）
                ranges = IPMatcher.parse_multiple_ip_ranges(ip_format)
                for start_int, end_int in ranges:
                    if start_int <= target_int <= end_int:
                        return True
            
            # 4. 尝试子网掩码匹配（如192.168.1.0/24）
            elif '/' in ip_format:
                if IPMatcher.is_ip_in_subnet(target_ip, ip_format):
                    return True
        
        return False
    
    @staticmethod
    def clear_cache():
        """清空缓存（用于内存管理）"""
        IPMatcher._range_cache.clear()
        IPMatcher._ip_int_cache.clear()
        # 清空lru_cache
        IPMatcher.is_valid_ipv4.cache_clear()
