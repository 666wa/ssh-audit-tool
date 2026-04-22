"""
高性能审计器 - 进一步优化版本
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


class FastAuditor:
    """高性能SSH命令核查器"""
    
    def __init__(self, report_df: pd.DataFrame, file_date: Optional[str] = None):
        """
        初始化高性能核查器
        
        Args:
            report_df: 报备表DataFrame
            file_date: 文件日期（YYYY-MM-DD格式），用于时间范围验证
        """
        self.report_df = report_df
        self.file_date = file_date
        self.parser = CommandParser()
        self.ip_matcher = IPMatcher()
        self.has_time_columns = False
        
        # 性能优化数据结构
        self.report_index = {}  # 账号索引
        self.time_cache = {}    # 时间解析缓存
        self.file_date_dt = None  # 文件日期datetime对象
        self.ip_cache = {}      # IP匹配结果缓存
        
        # 快速路径：预分类的记录
        self.valid_records = {}    # 有效期内的记录
        self.expired_records = {}  # 已过期的记录
        
        self._initialize()
    
    def _initialize(self):
        """初始化所有优化数据结构"""
        logger = logging.getLogger()
        logger.info("正在初始化高性能审计器...")
        
        self._check_time_columns()
        self._prepare_file_date()
        
        # 对于大数据集，使用更激进的优化策略
        total_rows = len(self.report_df)
        if total_rows > 100000:
            logger.info(f"检测到大数据集({total_rows:,}条记录)，启用高性能模式...")
            self._build_large_dataset_index()
        else:
            self._build_optimized_index()
        
        logger.info("高性能审计器初始化完成")
    
    def _check_time_columns(self):
        """检查时间列"""
        if '生效时间' in self.report_df.columns and '失效时间' in self.report_df.columns:
            self.has_time_columns = True
    
    def _prepare_file_date(self):
        """准备文件日期"""
        if self.file_date:
            self.file_date_dt = DateExtractor.parse_date_string(self.file_date)
    
    def _build_optimized_index(self):
        """构建优化的索引结构（标准模式）"""
        self._build_index_common(use_numpy=False)

    def _parse_accounts(self, account_str: str) -> list:
        """解析账号字符串，支持多种分隔符"""
        if not account_str or account_str == 'nan':
            return []
        if '、' in account_str or '/' in account_str or '，' in account_str:
            account_str = account_str.replace('、', '，').replace('/', '，')
            return [a.strip() for a in account_str.split('，') if a.strip() and a.strip() != 'nan']
        return [account_str] if account_str != 'nan' else []

    def _index_record(self, accounts: list, record_info: dict, time_status: str):
        """将记录按账号和时间状态加入索引"""
        for account in accounts:
            if account not in self.report_index:
                self.report_index[account] = []
            self.report_index[account].append(record_info)

            if time_status == 'valid':
                if account not in self.valid_records:
                    self.valid_records[account] = []
                self.valid_records[account].append(record_info)
            elif time_status == 'expired':
                if account not in self.expired_records:
                    self.expired_records[account] = []
                self.expired_records[account].append(record_info)

    def _build_index_common(self, use_numpy: bool = False):
        """
        构建索引的核心逻辑
        
        Args:
            use_numpy: 是否使用numpy数组访问（大数据集模式）
        """
        logger = logging.getLogger()
        mode_name = "大数据集高性能" if use_numpy else "优化"
        logger.info(f"正在构建{mode_name}索引...")

        self.report_index = {}
        self.valid_records = {}
        self.expired_records = {}

        total_rows = len(self.report_df)
        # 大数据集模式日志间隔更大
        log_interval = 100000 if use_numpy else 50000

        # 预提取numpy数组（大数据集模式）
        if use_numpy:
            account_values = self.report_df['访问账号'].values
            serial_values = self.report_df['序号'].values
            source_ip_values = self.report_df['本端主机IP'].values
            target_ip_values = self.report_df['对端主机IP'].values
            effective_values = self.report_df['生效时间'].values if self.has_time_columns else None
            expiry_values = self.report_df['失效时间'].values if self.has_time_columns else None

        for idx in range(total_rows):
            if idx % log_interval == 0:
                logger.info(f"已处理 {idx:,}/{total_rows:,} 条记录")

            # 根据模式获取字段值
            if use_numpy:
                account_str = str(account_values[idx]).strip()
                serial_number = serial_values[idx]
                source_ip = str(source_ip_values[idx]).strip()
                target_ip = str(target_ip_values[idx]).strip()
                effective_time = effective_values[idx] if effective_values is not None else ''
                expiry_time = expiry_values[idx] if expiry_values is not None else ''
            else:
                row = self.report_df.iloc[idx]
                account_str = str(row.get('访问账号', '')).strip()
                serial_number = row.get('序号', '')
                source_ip = str(row.get('本端主机IP', '')).strip()
                target_ip = str(row.get('对端主机IP', '')).strip()
                effective_time = row.get('生效时间', '')
                expiry_time = row.get('失效时间', '')

            # 解析账号
            accounts = self._parse_accounts(account_str)
            if not accounts:
                continue

            # 处理时间状态
            effective_dt = None
            expiry_dt = None
            time_status = 'valid'
            if self.has_time_columns and self.file_date_dt:
                effective_dt = self._get_or_cache_time(effective_time)
                expiry_dt = self._get_or_cache_time(expiry_time)
                time_status = self._determine_time_status(effective_dt, expiry_dt)

            # 构建记录信息
            record_info = {
                'idx': idx,
                'serial_number': serial_number,
                'source_ip': source_ip,
                'target_ip': target_ip,
                'effective_time': effective_time,
                'expiry_time': expiry_time,
                'effective_dt': effective_dt,
                'expiry_dt': expiry_dt,
                'time_range': None  # 延迟构建
            }

            # 加入索引
            self._index_record(accounts, record_info, time_status)

        logger.info("索引构建完成，开始排序...")
        self._sort_classified_records()
        logger.info(f"{mode_name}索引构建完成：{len(self.report_index)}个账号，{len(self.time_cache)}个时间缓存")
    
    
    def _get_or_cache_time(self, time_value) -> Optional[datetime]:
        """获取或缓存时间对象"""
        if not time_value or str(time_value).strip() == 'nan':
            return None
        
        time_str = str(time_value).strip()
        if time_str not in self.time_cache:
            self.time_cache[time_str] = DateExtractor.parse_date_string(time_str)
        
        return self.time_cache[time_str]
    
    def _build_time_range(self, effective_time, expiry_time) -> str:
        """构建时间范围字符串（延迟构建版本）"""
        if not self.has_time_columns:
            return ''
        
        eff_str = str(effective_time).strip() if effective_time and str(effective_time).strip() != 'nan' else ''
        exp_str = str(expiry_time).strip() if expiry_time and str(expiry_time).strip() != 'nan' else ''
        
        if eff_str or exp_str:
            return f"{eff_str or '无限制'}~{exp_str or '永久'}"
        return ''
    
    def _get_time_range(self, record: dict) -> str:
        """获取时间范围（延迟构建）"""
        if record['time_range'] is None:
            record['time_range'] = self._build_time_range(record['effective_time'], record['expiry_time'])
        return record['time_range']
    
    def _determine_time_status(self, effective_dt: Optional[datetime], expiry_dt: Optional[datetime]) -> str:
        """确定时间状态"""
        if not self.file_date_dt or not self.has_time_columns:
            return 'valid'
        
        if effective_dt and self.file_date_dt < effective_dt:
            return 'not_effective'
        
        if expiry_dt and self.file_date_dt > expiry_dt:
            return 'expired'
        
        return 'valid'
    
    def _build_large_dataset_index(self):
        """为大数据集构建高性能索引（使用numpy数组访问）"""
        self._build_index_common(use_numpy=True)
    
    def _sort_classified_records(self):
        """对分类记录进行排序"""
        # 对有效记录按生效时间倒序排序（最新的在前）
        for account in self.valid_records:
            self.valid_records[account].sort(
                key=lambda x: x['effective_dt'] or datetime.min,
                reverse=True
            )
        
        # 对过期记录按失效时间倒序排序（最近过期的在前）
        for account in self.expired_records:
            self.expired_records[account].sort(
                key=lambda x: x['expiry_dt'] or datetime.min,
                reverse=True
            )
    
    def check_match_fast(self, account: str, source_ip: str, target_ip: str) -> Tuple[Optional[str], Dict]:
        """
        快速匹配检查
        
        Args:
            account: 访问账号
            source_ip: 本端IP
            target_ip: 对端IP
        
        Returns:
            元组 (匹配序号, 匹配详情字典)
        """
        if not account or not source_ip or not target_ip:
            return None, self._empty_match_details()
        
        # 快速路径1：检查账号是否存在
        if account not in self.report_index:
            return None, self._empty_match_details()
        
        # 记录部分匹配情况
        any_source_ip_matched = False
        any_target_ip_matched = False
        
        # 快速路径2：优先检查有效记录
        if account in self.valid_records:
            for record in self.valid_records[account]:
                # 使用优化的IP匹配检查
                source_match, target_match = self._is_ip_match_optimized(source_ip, target_ip, record)
                
                if source_match:
                    any_source_ip_matched = True
                if target_match:
                    any_target_ip_matched = True
                
                # 只有两个IP都匹配才返回成功
                if source_match and target_match:
                    return self._format_result(record, account, False)
        
        # 快速路径3：检查过期记录
        if account in self.expired_records:
            for record in self.expired_records[account]:
                # 使用优化的IP匹配检查
                source_match, target_match = self._is_ip_match_optimized(source_ip, target_ip, record)
                
                if source_match:
                    any_source_ip_matched = True
                if target_match:
                    any_target_ip_matched = True
                
                # 只有两个IP都匹配才返回成功
                if source_match and target_match:
                    return self._format_result(record, account, True)
        
        # 如果在有效和过期记录中都没有找到IP匹配，检查所有记录（包括未生效的）
        if not any_source_ip_matched and not any_target_ip_matched:
            for record in self.report_index[account]:
                # 使用优化的IP匹配检查
                source_match, target_match = self._is_ip_match_optimized(source_ip, target_ip, record)
                
                if source_match:
                    any_source_ip_matched = True
                if target_match:
                    any_target_ip_matched = True
                
                # 不返回未生效的记录，只记录匹配情况
        
        # 没有找到完全匹配，返回部分匹配信息
        return None, {
            'account_match': True,
            'source_ip_match': any_source_ip_matched,
            'target_ip_match': any_target_ip_matched,
            'time_match': False,
            'matched_account': account,
            'matched_source_ip': '',
            'matched_target_ip': '',
            'time_range': ''
        }
    
    def _is_ip_match_optimized(self, source_ip: str, target_ip: str, record: dict) -> Tuple[bool, bool]:
        """
        优化的IP匹配检查，返回源IP和目标IP的匹配结果
        
        Returns:
            (源IP匹配结果, 目标IP匹配结果)
        """
        # 分别缓存源IP和目标IP的匹配结果
        source_cache_key = f"src|{source_ip}|{record['source_ip']}"
        target_cache_key = f"tgt|{target_ip}|{record['target_ip']}"
        
        # 检查源IP匹配
        if source_cache_key in self.ip_cache:
            source_match = self.ip_cache[source_cache_key]
        else:
            source_match = self.ip_matcher.match_ip(source_ip, record['source_ip'])
            # 限制缓存大小
            if len(self.ip_cache) < 100000:
                self.ip_cache[source_cache_key] = source_match
        
        # 检查目标IP匹配
        if target_cache_key in self.ip_cache:
            target_match = self.ip_cache[target_cache_key]
        else:
            target_match = self.ip_matcher.match_ip(target_ip, record['target_ip'])
            # 限制缓存大小
            if len(self.ip_cache) < 100000:
                self.ip_cache[target_cache_key] = target_match
        
        return source_match, target_match
    
    def _format_result(self, record: dict, account: str, is_expired: bool) -> Tuple[str, Dict]:
        """格式化结果"""
        match_details = {
            'account_match': True,
            'source_ip_match': True,
            'target_ip_match': True,
            'time_match': not is_expired,
            'matched_account': account,
            'matched_source_ip': record['source_ip'],
            'matched_target_ip': record['target_ip'],
            'time_range': self._get_time_range(record)  # 使用延迟构建
        }
        
        serial_number = record['serial_number']
        
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
        对单条操作记录进行核查（高性能版本）
        """
        # 首先检查是否是有效的SSH命令
        if not self.parser.is_valid_ssh_command(operation_content):
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 解析SSH命令
        parsed = self.parser.parse_ssh_command(operation_content)
        
        if not parsed['is_parseable']:
            return (RESULT_INVALID_COMMAND, '', '')
        
        # 提取信息
        account = parsed['account'] if parsed['account'] else default_account
        target_ip = parsed['target_ip']
        
        if target_ip == 'localhost':
            target_ip = source_ip
        
        # 使用快速匹配
        matched_serial, match_details = self.check_match_fast(account, source_ip, target_ip)
        
        # 构建详细说明
        if matched_serial is not None:
            if matched_serial.startswith('EXPIRED:'):
                serial_num = matched_serial.replace('EXPIRED:', '')
                detail = f"已报备但已过期：命中序号{serial_num}，访问时间段{match_details['time_range']}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_EXPIRED, serial_num, detail)
            else:
                detail = f"已报备：命中序号{matched_serial}，访问时间段{match_details['time_range'] or '无限制'}，访问账号{match_details['matched_account']}，源端IP{match_details['matched_source_ip']}，对端IP{match_details['matched_target_ip']}"
                return (RESULT_REPORTED, matched_serial, detail)
        else:
            # 构建未报备的详细说明
            # 如果账号未命中，直接说明该账号不在报备表内，不再检查IP
            if not match_details['account_match']:
                detail = f"未报备，该访问账号{account}不在报备表内"
                return (RESULT_NOT_REPORTED, '', detail)
            
            # 账号已命中，继续检查IP
            detail_parts = ["未报备", f"访问账号{account}已命中"]
            
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
    
    def _is_ip_match(self, source_ip: str, target_ip: str, record: dict) -> bool:
        """
        检查IP是否匹配（用于违规使用稽核）
        
        Returns:
            True if both source and target IPs match
        """
        source_match = self.ip_matcher.match_ip(source_ip, record['source_ip'])
        target_match = self.ip_matcher.match_ip(target_ip, record['target_ip'])
        return source_match and target_match
    
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
        """
        best_valid_match = None
        best_expired_match = None
        
        # 遍历所有账号的记录（因为不核查账号，需要检查所有记录）
        # 优先检查有效记录
        for account, records in self.valid_records.items():
            for record in records:
                if self._is_ip_match(source_ip, target_ip, record):
                    # 找到有效匹配
                    if best_valid_match is None or record['effective_dt'] > best_valid_match['effective_dt']:
                        best_valid_match = record
                        best_valid_match['matched_account'] = account
                    break  # 已排序，找到第一个就是最佳的
        
        # 如果没有有效记录，检查过期记录
        if best_valid_match is None:
            for account, records in self.expired_records.items():
                for record in records:
                    if self._is_ip_match(source_ip, target_ip, record):
                        # 找到过期匹配
                        if best_expired_match is None or record['expiry_dt'] > best_expired_match['expiry_dt']:
                            best_expired_match = record
                            best_expired_match['matched_account'] = account
                        break  # 已排序，找到第一个就是最佳的
        
        # 返回最佳匹配
        if best_valid_match:
            serial_number = best_valid_match['serial_number']
            detail = f"已报备：命中序号{serial_number}，访问时间段{self._get_time_range(best_valid_match) or '无限制'}，访问账号{best_valid_match.get('matched_account', '')}，源端IP{best_valid_match['source_ip']}，对端IP{best_valid_match['target_ip']}"
            return (RESULT_REPORTED, str(serial_number) if serial_number else '', detail)
        elif best_expired_match:
            serial_number = best_expired_match['serial_number']
            detail = f"已报备但已过期：命中序号{serial_number}，访问时间段{self._get_time_range(best_expired_match)}，访问账号{best_expired_match.get('matched_account', '')}，源端IP{best_expired_match['source_ip']}，对端IP{best_expired_match['target_ip']}"
            return (RESULT_EXPIRED, str(serial_number) if serial_number else '', detail)
        
        # 未匹配
        detail = f"未报备，源端IP{source_ip}未命中，对端IP{target_ip}未命中"
        return (RESULT_NOT_REPORTED, '', detail)