"""
SSH命令解析模块
"""
import re
import logging
from typing import Dict, Optional
from ssh_audit_tool.ip_matcher import IPMatcher


class CommandParser:
    """SSH命令解析器"""
    
    @staticmethod
    def is_valid_ipv4(ip: str) -> bool:
        """
        验证是否为有效的IPv4地址
        
        Args:
            ip: IP地址字符串
        
        Returns:
            有效返回True，否则返回False
        """
        return IPMatcher.is_valid_ipv4(ip)
    
    @staticmethod
    def extract_account(command: str) -> Optional[str]:
        """
        从SSH命令中提取账号名
        
        支持的格式：
        - ssh user@ip
        - ssh -l user ip
        - ssh user ip
        
        Args:
            command: SSH命令字符串
        
        Returns:
            账号名，如果无法提取则返回None
            如果检测到非法用户名格式，返回特殊标记'INVALID'
        """
        if not command:
            return None
        
        command = command.strip()
        
        # 格式1: ssh user@ip（正确格式）
        # 检查是否是错误格式：ssh ip@user
        # 扩展正则以匹配可能包含非ASCII字符的用户名
        pattern1 = r'ssh\s+([^\s@]+)@([^\s@]+)'
        match = re.search(pattern1, command)
        if match:
            first_part = match.group(1)
            second_part = match.group(2)
            
            # 如果第一部分是IP，第二部分是用户名，这是错误格式
            if CommandParser.is_valid_ipv4(first_part):
                return None  # 错误格式，返回None
            
            # 检查用户名是否包含非法字符
            if CommandParser.has_invalid_username_chars(first_part):
                return 'INVALID'  # 标记为非法用户名
            
            # 正确格式：user@ip
            return first_part
        
        # 格式2: ssh -l user ip
        pattern2 = r'ssh\s+-l\s+([a-zA-Z0-9_\-]+)'
        match = re.search(pattern2, command)
        if match:
            return match.group(1)
        
        # 格式3: ssh user ip (需要确保user不是IP地址)
        pattern3 = r'ssh\s+([a-zA-Z0-9_\-]+)\s+'
        match = re.search(pattern3, command)
        if match:
            potential_user = match.group(1)
            # 确保不是IP地址或选项参数
            if not CommandParser.is_valid_ipv4(potential_user) and not potential_user.startswith('-'):
                return potential_user
        
        return None
    
    @staticmethod
    def extract_target_ip(command: str) -> Optional[str]:
        """
        从SSH命令中提取目标IP地址
        
        Args:
            command: SSH命令字符串
        
        Returns:
            目标IP地址，如果无法提取则返回None
            如果目标是localhost或127.0.0.1，返回特殊标记'localhost'
            如果检测到错误格式（ip@user），返回None
        """
        if not command:
            return None
        
        # 检查是否是错误格式：ssh ip@user
        # 正则：ssh后跟IP地址，然后是@符号
        error_pattern = r'ssh\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})@'
        if re.search(error_pattern, command):
            # 检测到错误格式，返回None
            return None
        
        # 检查是否连接到localhost或127.0.0.1（精确匹配）
        # 使用单词边界确保不会匹配localhost8等
        if re.search(r'\blocalhost\b', command.lower()) or '127.0.0.1' in command:
            return 'localhost'
        
        # IPv4地址的正则表达式
        ipv4_pattern = r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b'
        
        # 查找所有IPv4地址
        matches = re.findall(ipv4_pattern, command)
        
        # 验证并返回第一个有效的IPv4地址
        for ip in matches:
            if CommandParser.is_valid_ipv4(ip):
                return ip
        
        return None
    
    @staticmethod
    def is_ipv6(text: str) -> bool:
        """
        检查文本中是否包含IPv6地址格式
        
        Args:
            text: 待检查的文本
        
        Returns:
            包含IPv6格式返回True，否则返回False
        """
        # 简单的IPv6格式检测（包含多个冒号）
        ipv6_pattern = r'[0-9a-fA-F]*:[0-9a-fA-F]*:[0-9a-fA-F]*'
        return bool(re.search(ipv6_pattern, text))
    
    @staticmethod
    def has_invalid_username_chars(username: str) -> bool:
        """
        检查用户名是否包含非法字符
        
        Args:
            username: 用户名字符串
        
        Returns:
            包含非法字符返回True，否则返回False
        """
        if not username:
            return False
        
        # 用户名不应该以点开头
        if username.startswith('.'):
            return True
        
        # 检查是否包含非ASCII字符（中文、特殊符号等）
        try:
            username.encode('ascii')
        except UnicodeEncodeError:
            return True
        
        # 用户名应该只包含字母、数字、下划线、连字符
        # 允许点号但不能在开头
        if not re.match(r'^[a-zA-Z0-9_\-][a-zA-Z0-9_\-\.]*$', username):
            return True
        
        return False
    
    @staticmethod
    def has_shell_redirection(command: str) -> bool:
        """
        检查命令是否包含shell重定向符号
        
        Args:
            command: 命令字符串
        
        Returns:
            包含重定向符号返回True，否则返回False
        """
        # 检查常见的shell重定向符号
        redirection_patterns = [
            r'>>',  # 追加重定向
            r'>',   # 输出重定向
            r'<',   # 输入重定向
            r'\|',  # 管道
        ]
        
        for pattern in redirection_patterns:
            if re.search(pattern, command):
                return True
        
        return False
    
    @staticmethod
    def has_file_extension_before_target(command: str) -> bool:
        """
        检查SSH命令中是否在目标前有文件名（带扩展名）
        
        Args:
            command: 命令字符串
        
        Returns:
            存在文件名返回True，否则返回False
        """
        # 匹配 ssh 后跟文件名（带常见扩展名）
        # 例如：ssh file.sh, ssh script.py, ssh data.zip
        file_pattern = r'ssh\s+[a-zA-Z0-9_\-]+\.(sh|py|zip|tar|gz|txt|log|conf|cfg|json|xml|yaml|yml)\s+'
        
        if re.search(file_pattern, command, re.IGNORECASE):
            return True
        
        return False
    
    @staticmethod
    def has_malformed_l_parameter(command: str) -> bool:
        """
        检查-l参数是否格式错误（后面拼接了其他内容）
        
        Args:
            command: 命令字符串
        
        Returns:
            -l参数格式错误返回True，否则返回False
        """
        # 匹配 -l 参数后跟用户名，但用户名中包含冒号（可能是密码或密钥）
        # 正常格式：ssh -l username ip
        # 错误格式：ssh -l username:password... ip
        malformed_pattern = r'-l\s+[a-zA-Z0-9_\-]+:'
        
        if re.search(malformed_pattern, command):
            return True
        
        return False
    
    @staticmethod
    def has_chinese_period(command: str) -> bool:
        """
        检查命令是否包含中文句号
        
        Args:
            command: 命令字符串
        
        Returns:
            包含中文句号返回True，否则返回False
        """
        # 检查是否包含中文句号（。）
        return '。' in command
    
    @staticmethod
    def is_valid_ssh_command(command: str) -> bool:
        """
        判断是否是有效的SSH命令（增强验证）
        
        有效的SSH命令应该：
        1. 包含 'ssh' 关键字
        2. 能够提取出有效的IP地址
        3. 不为空或纯空格
        4. 不包含shell重定向符号
        5. 不在目标前包含文件名
        6. -l参数格式正确
        7. 用户名不包含非法字符
        8. 不包含中文句号（数据质量问题）
        
        Args:
            command: 命令字符串
        
        Returns:
            是有效SSH命令返回True，否则返回False
        """
        if not command or not command.strip():
            return False
        
        command_lower = command.lower().strip()
        
        # 必须包含ssh关键字
        if 'ssh' not in command_lower:
            return False
        
        # 检查是否包含IPv6地址，如果是则标记为无效
        if CommandParser.is_ipv6(command):
            return False
        
        # 检查是否包含中文句号（数据质量问题）
        if CommandParser.has_chinese_period(command):
            return False
        
        # 检查是否包含shell重定向符号
        if CommandParser.has_shell_redirection(command):
            return False
        
        # 检查是否在目标前有文件名
        if CommandParser.has_file_extension_before_target(command):
            return False
        
        # 检查-l参数是否格式错误
        if CommandParser.has_malformed_l_parameter(command):
            return False
        
        # 必须能提取出有效的IP地址
        target_ip = CommandParser.extract_target_ip(command)
        if not target_ip:
            return False
        
        # 如果能提取到用户名，检查用户名是否包含非法字符
        account = CommandParser.extract_account(command)
        if account == 'INVALID':
            # 检测到非法用户名
            return False
        if account and CommandParser.has_invalid_username_chars(account):
            return False
        
        return True
    
    @staticmethod
    def parse_ssh_command(command: str) -> Dict[str, Optional[str]]:
        """
        解析SSH命令，提取账号和目标IP
        
        Args:
            command: SSH命令字符串
        
        Returns:
            字典，包含以下键：
            - 'account': 账号名（可能为None）
            - 'target_ip': 目标IP（可能为None）
            - 'is_parseable': 是否可解析（bool）
        """
        result = {
            'account': None,
            'target_ip': None,
            'is_parseable': False
        }
        
        if not command:
            return result
        
        # 提取账号
        account = CommandParser.extract_account(command)
        
        # 提取目标IP
        target_ip = CommandParser.extract_target_ip(command)
        
        # 更新结果
        result['account'] = account
        result['target_ip'] = target_ip
        result['is_parseable'] = (target_ip is not None)
        
        return result
