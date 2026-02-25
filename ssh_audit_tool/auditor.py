"""
核查比对模块
"""
import logging
import pandas as pd
from datetime import datetime
from typing import Dict, Set, Tuple, Optional
from ssh_audit_tool.parser import CommandParser
from ssh_audit_tool.ip_matcher import IPMatcher
from ssh_audit_tool.date_extractor import DateExtractor
from ssh_audit_tool.config import (
    RESULT_REPORTED,
    RESULT_NOT_REPORTED,
    RESULT_INVALID_COMMAND,
    RESULT_EXPIRED
)


class Auditor:
    """SSH命令核查器"""
    
    def __init__(self, report_df: pd.DataFrame, file_date: Optional[str] = None):
        """
        初始化核查器
        
        Args:
            report_df: 报备表DataFrame
            file_date: 文件日期（YYYY-MM-DD格式），用于时间范围验证
        """
        self.report_df = report_df
        self.file_date = file_date  # 新增：文件日期
        self.parser = CommandParser()
        self.ip_matcher = IPMatcher()
        self.report_index = {}
        self.has_time_columns = False
        
        # 性能优化：时间解析缓存
        self._time_cache = {}  # 缓存已解析的时间对象
        self._file_date_dt = None  # 缓存文件日期的datetime对象
        
        self.check_time_columns()
        self.build_report_index()
        self._prepare_time_cache()
    
    def _prepare_time_cache(self):
        """预处理时间缓存"""
        if self.file_date:
            self._file_date_dt = DateExtractor.parse_date_string(self.file_date)
            
        # 预缓存报备表中的时间
        if self.has_time_columns:
            logger = logging.getLogger()
            logger.info("正在预处理时间数据...")
            
            for idx, row in self.report_df.iterrows():
                effective_time = row.get('生效时间', '')
                expiry_time = row.get('失效时间', '')
                
                if effective_time and str(effective_time).strip() and str(effective_time).strip() != 'nan':
                    time_str = str(effective_time).strip()
                    if time_str not in self._time_cache:
                        self._time_cache[time_str] = DateExtractor.parse_date_string(time_str)
                
                if expiry_time and str(expiry_time).strip() and str(expiry_time).strip() != 'nan':
                    time_str = str(expiry_time).strip()
                    if time_str not in self._time_cache:
                        self._time_cache[time_str] = DateExtractor.parse_date_string(time_str)
            
            logger.info(f"时间缓存准备完成，共缓存 {len(self._time_cache)} 个时间对象")
    
    def check_time_columns(self) -> None:
        """
        检查报备表是否包含生效时间和失效时间列
        """
        logger = logging.getLogger()
        if '生效时间' in self.report_df.columns and '失效时间' in self.report_df.columns:
            self.has_time_columns = True
            if self.file_date:
                logger.info(f"报备表包含时间范围列，将使用文件日期({self.file_date})验证是否在生效期内")
            else:
                logger.info("报备表包含时间范围列，但未提供文件日期，跳过时间验证")
        else:
            self.has_time_columns = False
            logger.info("报备表不包含时间范围列，跳过时间验证")
    
    def build_report_index(self) -> None:
        """
        构建报备表索引以提高查询效率
        
        为每个账号建立索引，加速匹配过程
        """
        logger = logging.getLogger()
        logger.info("正在构建报备表索引...")
        
        # 为每个账号建立索引
        for idx, row in self.report_df.iterrows():
            rp_account = str(row.get('访问账号', '')).strip()
            
            if not rp_account:
                continue
            
            # 处理多账号情况（兼容多种分隔符）
            # 支持的分隔符：中文逗号（，）、顿号（、）、斜杠（/）
            # 不支持英文逗号（,），避免与CSV格式冲突
            # 先统一替换为中文逗号，然后按中文逗号分割
            rp_account = rp_account.replace('、', '，').replace('/', '，')
            accounts = [a.strip() for a in rp_account.split('，')]
            
            for account in accounts:
                if account and account != 'nan':  # 过滤空账号
                    if account not in self.report_index:
                        self.report_index[account] = []
                    self.report_index[account].append(idx)
        
        logger.info(f"索引构建完成，共 {len(self.report_index)} 个账号")
        logger.info("报备表准备完成")
    
    def check_match(self, account: str, source_ip: str, target_ip: str, operation_time: Optional[str] = None) -> Tuple[Optional[str], Dict]:
        """
        检查三元组是否在报备表中匹配（优化版本：分层早期退出）
        
        Args:
            account: 访问账号
            source_ip: 本端IP
            target_ip: 对端IP
            operation_time: 操作时间（已弃用，现在使用文件日期）
        
        Returns:
            元组 (匹配序号, 匹配详情字典)
            - 匹配序号：报备表中"序号"列的值或"EXPIRED:序号"，否则返回None
            - 匹配详情：包含各字段匹配情况的字典
        """
        if not account or not source_ip or not target_ip:
            return None, self._empty_match_details()
        
        # 使用索引快速定位账号相关的记录
        if account not in self.report_index:
            return None, self._empty_match_details()
        
        # 优化策略：分层查找，优先找有效记录
        best_valid_match = None
        best_expired_match = None
        
        # 记录部分匹配情况（用于未完全匹配时的详细说明）
        any_source_ip_matched = False
        any_target_ip_matched = False
        
        # 遍历该账号相关的所有记录
        for idx in self.report_index[account]:
            row = self.report_df.iloc[idx]
            
            rp_source_ip = str(row.get('本端主机IP', '')).strip()
            rp_target_ip = str(row.get('对端主机IP', '')).strip()
            
            if not rp_source_ip or not rp_target_ip:
                continue
            
            # 检查本端IP是否匹配
            source_ip_matched = self.ip_matcher.match_ip(source_ip, rp_source_ip)
            if source_ip_matched:
                any_source_ip_matched = True
            
            # 检查对端IP是否匹配
            target_ip_matched = self.ip_matcher.match_ip(target_ip, rp_target_ip)
            if target_ip_matched:
                any_target_ip_matched = True
            
            # 只有两个IP都匹配才继续
            if not (source_ip_matched and target_ip_matched):
                continue
            
            # IP匹配成功，构建基本匹配信息
            match_info = self._build_match_info(row, account)
            
            # 如果不需要时间验证，直接返回第一个匹配的记录
            if not (self.file_date and self.has_time_columns):
                return self._format_match_result(match_info, False)
            
            # 进行时间验证
            time_status = self._check_time_validity(row)
            
            if time_status == 'valid':
                # 找到有效记录
                if best_valid_match is None or self._is_better_valid_match(match_info, best_valid_match):
                    best_valid_match = match_info
                    # 优化：如果找到有效记录且不需要找最佳的，可以立即返回
                    # 这里为了保持准确性，继续查找最佳的有效记录
            elif time_status == 'expired':
                # 记录过期记录
                if best_expired_match is None or self._is_better_expired_match(match_info, best_expired_match):
                    best_expired_match = match_info
            # time_status == 'not_effective' 的记录被跳过
        
        # 返回最佳匹配
        if best_valid_match:
            return self._format_match_result(best_valid_match, False)
        elif best_expired_match:
            return self._format_match_result(best_expired_match, True)
        
        # 未完全匹配，返回部分匹配信息
        return None, {
            'account_match': True,  # 账号匹配了（进入了索引）
            'source_ip_match': any_source_ip_matched,
            'target_ip_match': any_target_ip_matched,
            'time_match': False,
            'matched_account': account,
            'matched_source_ip': '',
            'matched_target_ip': '',
            'time_range': ''
        }
    
    def _empty_match_details(self) -> Dict:
        """返回空的匹配详情"""
        return {
            'account_match': False,
            'source_ip_match': False,
            'target_ip_match': False,
            'time_match': False,
            'matched_account': '',
            'matched_source_ip': '',
            'matched_target_ip': '',
            'time_range': ''
        }
    
    def _build_match_info(self, row, account: str) -> dict:
        """构建匹配信息对象"""
        effective_time = row.get('生效时间', '')
        expiry_time = row.get('失效时间', '')
        time_range = ''
        
        if self.has_time_columns:
            eff_str = str(effective_time).strip() if effective_time and str(effective_time).strip() != 'nan' else ''
            exp_str = str(expiry_time).strip() if expiry_time and str(expiry_time).strip() != 'nan' else ''
            if eff_str or exp_str:
                time_range = f"{eff_str or '无限制'}~{exp_str or '永久'}"
        
        return {
            'serial_number': row.get('序号', ''),
            'effective_time': effective_time,
            'expiry_time': expiry_time,
            'effective_time_dt': self._get_cached_time(effective_time),
            'expiry_time_dt': self._get_cached_time(expiry_time),
            'time_range': time_range,
            'matched_account': account,
            'matched_source_ip': str(row.get('本端主机IP', '')).strip(),
            'matched_target_ip': str(row.get('对端主机IP', '')).strip()
        }
    
    def _get_cached_time(self, time_value) -> Optional[datetime]:
        """获取缓存的时间对象"""
        if not time_value or str(time_value).strip() == 'nan':
            return None
        
        time_str = str(time_value).strip()
        return self._time_cache.get(time_str)
    
    def _check_time_validity(self, row) -> str:
        """
        检查时间有效性
        
        Returns:
            'valid': 有效期内
            'expired': 已过期
            'not_effective': 未生效
        """
        if not self._file_date_dt:
            return 'valid'
        
        effective_time = row.get('生效时间', '')
        expiry_time = row.get('失效时间', '')
        
        effective_dt = self._get_cached_time(effective_time)
        expiry_dt = self._get_cached_time(expiry_time)
        
        # 检查是否早于生效时间
        if effective_dt and self._file_date_dt < effective_dt:
            return 'not_effective'
        
        # 检查是否晚于失效时间
        if expiry_dt and self._file_date_dt > expiry_dt:
            return 'expired'
        
        return 'valid'
    
    def _is_better_valid_match(self, new_match: dict, current_best: dict) -> bool:
        """判断新的有效匹配是否比当前最佳匹配更好（生效时间更晚）"""
        new_effective = new_match['effective_time_dt']
        current_effective = current_best['effective_time_dt']
        
        if new_effective is None:
            return False
        if current_effective is None:
            return True
        
        return new_effective > current_effective
    
    def _is_better_expired_match(self, new_match: dict, current_best: dict) -> bool:
        """判断新的过期匹配是否比当前最佳匹配更好（失效时间更晚）"""
        new_expiry = new_match['expiry_time_dt']
        current_expiry = current_best['expiry_time_dt']
        
        if new_expiry is None:
            return False
        if current_expiry is None:
            return True
        
        return new_expiry > current_expiry
    
    def _format_match_result(self, match_info: dict, is_expired: bool) -> Tuple[str, Dict]:
        """格式化匹配结果"""
        match_details = {
            'account_match': True,
            'source_ip_match': True,
            'target_ip_match': True,
            'time_match': not is_expired,
            'matched_account': match_info['matched_account'],
            'matched_source_ip': match_info['matched_source_ip'],
            'matched_target_ip': match_info['matched_target_ip'],
            'time_range': match_info['time_range']
        }
        
        serial_number = match_info['serial_number']
        
        if is_expired:
            return f"EXPIRED:{serial_number}" if serial_number else "EXPIRED:", match_details
        else:
            return str(serial_number) if serial_number else None, match_details
    def _empty_match_details(self) -> Dict:
        """返回空的匹配详情"""
        return {
            'account_match': False,
            'source_ip_match': False,
            'target_ip_match': False,
            'time_match': False,
            'matched_account': '',
            'matched_source_ip': '',
            'matched_target_ip': '',
            'time_range': ''
        }

    
    def audit_record(self, operation_content: str, source_ip: str, default_account: str) -> Tuple[str, str, str]:
        """
        对单条操作记录进行核查（原始模板）
        
        Args:
            operation_content: 操作内容（SSH命令）
            source_ip: 资源IP（本端IP）
            default_account: 默认账号（优先使用从账号名称，否则使用主账号名称）
        
        Returns:
            元组 (核查结果, 命中序号, 详细说明)
            - 核查结果："已报备"、"未报备"、"已报备但已过期"或"异常：非有效ssh命令"
            - 命中序号：匹配的报备表"序号"列的值（字符串），未匹配则为空字符串
            - 详细说明：详细的匹配信息
        """
        # 首先检查是否是有效的SSH命令（包含ssh关键字且能提取出有效IP）
        if not self.parser.is_valid_ssh_command(operation_content):
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 解析SSH命令
        parsed = self.parser.parse_ssh_command(operation_content)
        
        # 如果无法解析出IP，标记为无效命令
        if not parsed['is_parseable']:
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 提取信息
        # 如果SSH命令中指定了用户，使用命令中的用户；否则使用默认账号
        account = parsed['account'] if parsed['account'] else default_account
        target_ip = parsed['target_ip']
        
        # 如果目标是localhost，将对端IP设置为资源IP（本机）
        if target_ip == 'localhost':
            target_ip = source_ip
        
        # 检查是否匹配（使用文件日期进行时间验证）
        matched_serial, match_details = self.check_match(account, source_ip, target_ip)
        
        # 构建详细说明
        if matched_serial is not None:
            # 检查是否过期
            if matched_serial.startswith('EXPIRED:'):
                serial_num = matched_serial.replace('EXPIRED:', '')
                detail = f"已报备但已过期：命中序号{serial_num}，访问时间段{match_details['time_range']}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_EXPIRED, serial_num, detail)
            else:
                detail = f"已报备：命中序号{matched_serial}，访问时间段{match_details['time_range'] or '无限制'}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_REPORTED, matched_serial, detail)
        else:
            # 构建未报备的详细说明
            detail_parts = ["未报备"]
            if not match_details['account_match']:
                detail_parts.append(f"访问账号{account}未命中")
            else:
                detail_parts.append(f"访问账号{account}已命中")
            
            if not match_details['source_ip_match']:
                detail_parts.append(f"源端IP{source_ip}未命中")
            else:
                detail_parts.append(f"源端IP{source_ip}已命中")
            
            if not match_details['target_ip_match']:
                detail_parts.append(f"对端IP{target_ip}未命中")
            else:
                detail_parts.append(f"对端IP{target_ip}已命中")
            
            detail = "，".join(detail_parts)
            return (RESULT_NOT_REPORTED, '', detail)
    
    def audit_record_4a(self, operation_content: str, source_ip: str, default_account: str, fallback_target_ip: str, operation_time: Optional[str] = None) -> Tuple[str, str]:
        """
        对单条操作记录进行核查（4A模板专用）
        
        Args:
            operation_content: 操作内容（SSH命令）
            source_ip: 源地址（本端IP，来自client_ip）
            default_account: 默认账号（优先使用从账号名称，否则使用主账号名称）
            fallback_target_ip: 备用对端IP（来自server_ip目的地址，当SSH命令无法提取IP时使用）
            operation_time: 操作时间（可选，用于验证是否在生效期内）
        
        Returns:
            元组 (核查结果, 命中序号)
            - 核查结果："已报备"、"未报备"、"已报备但已过期"或"异常：非有效ssh命令"
            - 命中序号：匹配的报备表"序号"列的值（字符串），未匹配则为空字符串
        """
        # 首先检查是否是有效的SSH命令（包含ssh关键字且能提取出有效IP）
        if not self.parser.is_valid_ssh_command(operation_content):
            return (RESULT_INVALID_COMMAND, '')
        
        # 解析SSH命令
        parsed = self.parser.parse_ssh_command(operation_content)
        
        # 提取账号
        # 如果SSH命令中指定了用户，使用命令中的用户；否则使用默认账号
        account = parsed['account'] if parsed['account'] else default_account
        
        # 提取对端IP
        # 优先从SSH命令提取，如果提取不到则使用fallback_target_ip（目的地址）
        if parsed['is_parseable'] and parsed['target_ip']:
            target_ip = parsed['target_ip']
            # 如果目标是localhost，将对端IP设置为源地址（本机）
            if target_ip == 'localhost':
                target_ip = source_ip
        else:
            # SSH命令无法提取IP，使用目的地址（server_ip）
            target_ip = fallback_target_ip
            # 如果目的地址也无效，标记为无效命令
            if not target_ip or target_ip == 'nan':
                return (RESULT_INVALID_COMMAND, '')
        
        # 检查是否匹配（传入操作时间）
        matched_serial, match_details = self.check_match(account, source_ip, target_ip, operation_time)
        
        if matched_serial is not None:
            # 检查是否过期
            if matched_serial.startswith('EXPIRED:'):
                serial_num = matched_serial.replace('EXPIRED:', '')
                return (RESULT_EXPIRED, serial_num)
            else:
                return (RESULT_REPORTED, matched_serial)
        else:
            return (RESULT_NOT_REPORTED, '')
    
    def audit_record_with_target_ip(self, operation_content: str, source_ip: str, default_account: str, target_ip: str, operation_time: Optional[str] = None) -> Tuple[str, str, str]:
        """
        对单条操作记录进行核查（直接指定对端IP）
        
        用于特殊场景：当审计说明包含"过堡垒机操作存在跳板绕行"时，
        直接使用目的地址（server_ip）作为对端IP，不从SSH命令提取
        
        Args:
            operation_content: 操作内容（SSH命令）
            source_ip: 本端IP
            default_account: 默认账号
            target_ip: 对端IP（直接使用，不从SSH命令提取）
            operation_time: 操作时间（可选，用于验证是否在生效期内）
        
        Returns:
            元组 (核查结果, 命中序号, 详细说明)
        """
        # 首先检查是否是有效的SSH命令
        if not self.parser.is_valid_ssh_command(operation_content):
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 解析SSH命令（只提取账号）
        parsed = self.parser.parse_ssh_command(operation_content)
        
        # 提取账号
        account = parsed['account'] if parsed['account'] else default_account
        
        # 直接使用传入的target_ip，不从SSH命令提取
        # 如果target_ip无效，标记为无效命令
        if not target_ip or target_ip == 'nan':
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 检查是否匹配（传入操作时间）
        matched_serial, match_details = self.check_match(account, source_ip, target_ip, operation_time)
        
        # 构建详细说明
        if matched_serial is not None:
            # 检查是否过期
            if matched_serial.startswith('EXPIRED:'):
                serial_num = matched_serial.replace('EXPIRED:', '')
                detail = f"已报备但已过期：命中序号{serial_num}，访问时间段{match_details['time_range']}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_EXPIRED, serial_num, detail)
            else:
                detail = f"已报备：命中序号{matched_serial}，访问时间段{match_details['time_range'] or '无限制'}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_REPORTED, matched_serial, detail)
        else:
            # 构建未报备的详细说明
            detail_parts = ["未报备"]
            if not match_details['account_match']:
                detail_parts.append(f"访问账号{account}未命中")
            else:
                detail_parts.append(f"访问账号{account}已命中")
            
            if not match_details['source_ip_match']:
                detail_parts.append(f"源端IP{source_ip}未命中")
            else:
                detail_parts.append(f"源端IP{source_ip}已命中")
            
            if not match_details['target_ip_match']:
                detail_parts.append(f"对端IP{target_ip}未命中")
            else:
                detail_parts.append(f"对端IP{target_ip}已命中")
            
            detail = "，".join(detail_parts)
            return (RESULT_NOT_REPORTED, '', detail)
    
    def audit_violation_record(self, source_ip: str, target_ip: str) -> Tuple[str, str, str]:
        """
        对违规使用记录进行核查（只核查IP对，不核查账号）
        
        违规使用稽核的特点：
        1. 只核查本端IP和对端IP的匹配
        2. 不核查账号信息
        3. 不核查SSH命令
        
        Args:
            source_ip: 本端IP（服务器地址）
            target_ip: 对端IP（目的地址）
        
        Returns:
            元组 (核查结果, 命中序号, 详细说明)
            - 核查结果："已报备"、"未报备"或"已报备但已过期"
            - 命中序号：匹配的报备表"序号"列的值（字符串），未匹配则为空字符串
            - 详细说明：详细的匹配信息
        """
        # 遍历所有报备记录，只匹配IP对
        best_valid_match = None
        best_expired_match = None
        
        for idx, row in self.report_df.iterrows():
            rp_source_ip = str(row.get('本端主机IP', '')).strip()
            rp_target_ip = str(row.get('对端主机IP', '')).strip()
            
            if not rp_source_ip or not rp_target_ip:
                continue
            
            # 检查本端IP是否匹配
            if not self.ip_matcher.match_ip(source_ip, rp_source_ip):
                continue
            
            # 检查对端IP是否匹配
            if not self.ip_matcher.match_ip(target_ip, rp_target_ip):
                continue
            
            # IP匹配成功，构建匹配信息（不包含账号）
            match_info = {
                'serial_number': row.get('序号', ''),
                'effective_time': row.get('生效时间', ''),
                'expiry_time': row.get('失效时间', ''),
                'effective_time_dt': self._get_cached_time(row.get('生效时间', '')),
                'expiry_time_dt': self._get_cached_time(row.get('失效时间', '')),
                'matched_source_ip': rp_source_ip,
                'matched_target_ip': rp_target_ip,
                'matched_account': str(row.get('访问账号', '')).strip()  # 仅用于显示
            }
            
            # 构建时间范围字符串
            if self.has_time_columns:
                eff_str = str(match_info['effective_time']).strip() if match_info['effective_time'] and str(match_info['effective_time']).strip() != 'nan' else ''
                exp_str = str(match_info['expiry_time']).strip() if match_info['expiry_time'] and str(match_info['expiry_time']).strip() != 'nan' else ''
                match_info['time_range'] = f"{eff_str or '无限制'}~{exp_str or '永久'}" if (eff_str or exp_str) else ''
            else:
                match_info['time_range'] = ''
            
            # 如果不需要时间验证，直接返回第一个匹配的记录
            if not (self.file_date and self.has_time_columns):
                serial_number = match_info['serial_number']
                detail = f"已报备：命中序号{serial_number}，访问时间段{match_info['time_range'] or '无限制'}，访问账号{match_info['matched_account']}，源端IP{match_info['matched_source_ip']}，对端IP{match_info['matched_target_ip']}"
                return (RESULT_REPORTED, str(serial_number) if serial_number else '', detail)
            
            # 进行时间验证
            time_status = self._check_time_validity(row)
            
            if time_status == 'valid':
                # 找到有效记录
                if best_valid_match is None or self._is_better_valid_match(match_info, best_valid_match):
                    best_valid_match = match_info
            elif time_status == 'expired':
                # 记录过期记录
                if best_expired_match is None or self._is_better_expired_match(match_info, best_expired_match):
                    best_expired_match = match_info
        
        # 返回最佳匹配
        if best_valid_match:
            serial_number = best_valid_match['serial_number']
            detail = f"已报备：命中序号{serial_number}，访问时间段{best_valid_match['time_range'] or '无限制'}，访问账号{best_valid_match['matched_account']}，源端IP{best_valid_match['matched_source_ip']}，对端IP{best_valid_match['matched_target_ip']}"
            return (RESULT_REPORTED, str(serial_number) if serial_number else '', detail)
        elif best_expired_match:
            serial_number = best_expired_match['serial_number']
            detail = f"已报备但已过期：命中序号{serial_number}，访问时间段{best_expired_match['time_range']}，访问账号{best_expired_match['matched_account']}，源端IP{best_expired_match['matched_source_ip']}，对端IP{best_expired_match['matched_target_ip']}"
            return (RESULT_EXPIRED, str(serial_number) if serial_number else '', detail)
        
        # 未匹配
        detail = f"未报备，源端IP{source_ip}未命中，对端IP{target_ip}未命中"
        return (RESULT_NOT_REPORTED, '', detail)
