# -*- coding:utf-8 -*-
import datetime
import warnings
import pymysql
import pandas as pd
from decimal import Decimal
from contextlib import closing
from mdbq.log import mylogger
import os
from mdbq.config import config
from typing import Optional, Dict, List, Set, Tuple, Union, Any, Literal
from dbutils.pooled_db import PooledDB
import time
from functools import wraps

warnings.filterwarnings('ignore')
logger = mylogger.MyLogger(
    logging_mode='file',
    log_level='info',
    log_format='json',
    max_log_size=50,
    backup_count=5,
    enable_async=False,  # 是否启用异步日志
    sample_rate=1,  # 采样DEBUG/INFO日志
    sensitive_fields=[],  #  敏感字段过滤
    enable_metrics=False,  # 是否启用性能指标
)


class QueryDatas:
    """
    专门用来查询数据库, 不做清洗数据操作。
    支持表结构检查、条件查询、数据导出为DataFrame、列名和类型获取等。
    支持分页查询和上下文管理。
    """

    def __init__(self, username: str, password: str, host: str, port: int, charset: str = 'utf8mb4',
                 maxconnections: int = 20, mincached: int = 2, maxcached: int = 5,
                 connect_timeout: int = 10, read_timeout: int = 30, write_timeout: int = 30,
                 max_retries: int = 3, retry_waiting_time: int = 5, collation: str = 'utf8mb4_0900_ai_ci') -> None:
        """
        初始化数据库连接配置和连接池。
        
        Args:
            username: 数据库用户名
            password: 数据库密码
            host: 数据库主机
            port: 数据库端口
            charset: 字符集，默认utf8mb4
            maxconnections: 最大连接数，默认20
            mincached: 最小缓存连接数，默认2
            maxcached: 最大缓存连接数，默认5
            connect_timeout: 连接超时时间，默认10秒
            read_timeout: 读取超时时间，默认30秒
            write_timeout: 写入超时时间，默认30秒
            max_retries: 最大重试次数，默认3次
            retry_waiting_time: 重试等待时间，默认5秒
            collation: 排序规则，默认utf8mb4_0900_ai_ci
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.charset = charset
        self.collation = collation
        self.max_retries = max_retries
        self.retry_waiting_time = retry_waiting_time
        self.connect_timeout = connect_timeout
        self.read_timeout = read_timeout
        self.write_timeout = write_timeout
        
        # 连接池状态监控
        self._pool_stats = {
            'last_health_check': None,
            'health_check_interval': 300,  # 5分钟检查一次
            'consecutive_failures': 0,  # 连续失败次数
            'max_consecutive_failures': 3  # 最大连续失败次数
        }
        
        self.base_config = {
            'host': self.host,
            'port': int(self.port),
            'user': self.username,
            'password': self.password,
            'charset': charset,
            'collation': self.collation,
            'cursorclass': pymysql.cursors.DictCursor,
            'connect_timeout': connect_timeout,
            'read_timeout': read_timeout,
            'write_timeout': write_timeout,
            'autocommit': True
        }
        
        # 创建连接池
        self.pool = self._create_connection_pool(maxconnections, mincached, maxcached)

    def _create_connection_pool(self, maxconnections: int, mincached: int, maxcached: int) -> PooledDB:
        """
        创建数据库连接池
        
        Args:
            maxconnections: 最大连接数
            mincached: 最小缓存连接数
            maxcached: 最大缓存连接数
            
        Returns:
            PooledDB连接池实例
            
        Raises:
            ConnectionError: 当连接池创建失败时抛出
        """
        if hasattr(self, 'pool') and self.pool is not None and self._check_pool_health():
            return self.pool
            
        self.pool = None
        
        # 连接参数 - 这些参数会传递给底层的连接创建函数
        connection_params = {
            'host': self.host,
            'port': int(self.port),
            'user': self.username,
            'password': self.password,
            'charset': self.charset,
            'collation': self.collation,
            'cursorclass': pymysql.cursors.DictCursor,
            'connect_timeout': self.connect_timeout,
            'read_timeout': self.read_timeout,
            'write_timeout': self.write_timeout,
            'autocommit': True
        }
        
        # 连接池参数
        pool_params = {
            'creator': pymysql,
            'maxconnections': maxconnections,
            'mincached': mincached,
            'maxcached': maxcached,
            'blocking': True,
            'maxusage': 2000,  # 每个连接最多使用次数
            'setsession': [],
            'ping': 7
        }
        
        try:
            # 创建连接池，将连接参数作为kwargs传递
            pool = PooledDB(**pool_params, **connection_params)
            logger.debug('连接池创建成功', {
                '连接池大小': maxconnections,
                '最小缓存': mincached,
                '最大缓存': maxcached,
                '主机': self.host,
                '端口': self.port
            })
            return pool
        except Exception as e:
            self.pool = None
            logger.error('连接池创建失败', {
                '错误': str(e),
                '主机': self.host,
                '端口': self.port
            })
            raise ConnectionError(f'连接池创建失败: {str(e)}')

    def _check_pool_health(self) -> bool:
        """
        检查连接池健康状态
        
        Returns:
            bool: 连接池是否健康
        """
        if not self.pool:
            return False
            
        current_time = time.time()
        # 检查是否需要执行健康检查
        if (self._pool_stats['last_health_check'] is None or 
            current_time - self._pool_stats['last_health_check'] > self._pool_stats['health_check_interval']):
            
            try:
                # 更新健康检查时间
                self._pool_stats['last_health_check'] = current_time
                
                # 检查连接是否可用
                with self.pool.connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute('SELECT 1')
                        result = cursor.fetchone()
                        if not result or result.get('1') != 1:
                            self._pool_stats['consecutive_failures'] += 1
                            if self._pool_stats['consecutive_failures'] >= self._pool_stats['max_consecutive_failures']:
                                logger.error('连接池健康检查连续失败', {
                                    '连续失败次数': self._pool_stats['consecutive_failures']
                                })
                            return False
                
                # 重置连续失败计数
                self._pool_stats['consecutive_failures'] = 0
                logger.debug('连接池健康检查通过')
                return True
                
            except Exception as e:
                self._pool_stats['consecutive_failures'] += 1
                if self._pool_stats['consecutive_failures'] >= self._pool_stats['max_consecutive_failures']:
                    logger.error('连接池健康检查失败', {
                        '错误类型': type(e).__name__,
                        '错误信息': str(e),
                        '连续失败次数': self._pool_stats['consecutive_failures']
                    })
                return False
                
        return True

    @staticmethod
    def _execute_with_retry(func):
        """
        带重试机制的装饰器，用于数据库操作
        
        Args:
            func: 被装饰的函数
            
        Returns:
            装饰后的函数
        """
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            last_exception = None
            operation = func.__name__
            
            for attempt in range(self.max_retries):
                try:
                    result = func(self, *args, **kwargs)
                    if attempt > 0:
                        logger.info('操作成功(重试后)', {
                            '操作': operation,
                            '重试次数': attempt + 1
                        })
                    return result
                except (pymysql.OperationalError, pymysql.err.MySQLError) as e:
                    last_exception = e
                    error_details = {
                        '操作': operation,
                        '错误代码': e.args[0] if e.args else None,
                        '错误信息': e.args[1] if len(e.args) > 1 else None,
                        '尝试次数': attempt + 1,
                        '最大重试次数': self.max_retries
                    }
                    
                    if attempt < self.max_retries - 1:
                        wait_time = self.retry_waiting_time * (attempt + 1)
                        error_details['等待时间'] = wait_time
                        logger.warning('数据库操作失败，准备重试', error_details)
                        time.sleep(wait_time)
                        try:
                            self.pool = self._create_connection_pool(
                                maxconnections=self.pool._maxconnections,
                                mincached=self.pool._mincached,
                                maxcached=self.pool._maxcached
                            )
                            logger.info('成功重新建立数据库连接')
                        except Exception as reconnect_error:
                            logger.error('重连失败', {'错误': str(reconnect_error)})
                    else:
                        logger.error('操作最终失败', error_details)
                except Exception as e:
                    last_exception = e
                    logger.error('发生意外错误', {
                        '操作': operation,
                        '错误类型': type(e).__name__,
                        '错误信息': str(e)
                    })
                    break
                    
            raise last_exception if last_exception else Exception('发生未知错误')
        return wrapper

    # @_execute_with_retry
    def _get_connection(self, db_name: Optional[str] = None) -> pymysql.connections.Connection:
        """
        从连接池获取数据库连接
        
        Args:
            db_name: 可选的数据库名，如果提供则会在连接后选择该数据库
            
        Returns:
            数据库连接对象
            
        Raises:
            ConnectionError: 当获取连接失败时抛出
        """
        try:
            # 只在连续失败次数达到阈值时检查健康状态
            if self._pool_stats['consecutive_failures'] >= self._pool_stats['max_consecutive_failures']:
                if not self._check_pool_health():
                    logger.warning('连接池不健康，尝试重新创建')
                    # 使用默认值重新创建连接池
                    self.pool = self._create_connection_pool(10, 2, 5)
                    # 重置连续失败计数
                    self._pool_stats['consecutive_failures'] = 0
            
            conn = self.pool.connection()
            if db_name:
                # 使用原生pymysql连接来选择数据库
                with conn.cursor() as cursor:
                    cursor.execute(f"USE `{db_name}`")
            return conn
        except pymysql.OperationalError as e:
            error_code = e.args[0] if e.args else None
            if error_code in (2003, 2006, 2013):  # 连接相关错误
                logger.error('数据库连接错误', {
                    '错误代码': error_code,
                    '错误信息': str(e),
                    '数据库': db_name
                })
                # 使用默认值重新创建连接池
                self.pool = self._create_connection_pool(10, 2, 5)
                # 重置连续失败计数
                self._pool_stats['consecutive_failures'] = 0
                raise ConnectionError(f'数据库连接错误: {str(e)}')
            else:
                raise
        except Exception as e:
            logger.error('从连接池获取数据库连接失败', {
                '错误': str(e),
                '数据库': db_name
            })
            raise ConnectionError(f'连接数据库失败: {str(e)}')

    # @_execute_with_retry
    def _execute_query(self, sql: str, params: tuple = None, db_name: str = None) -> Optional[List[Dict[str, Any]]]:
        """
        执行SQL查询的通用方法。
        
        Args:
            sql: SQL查询语句
            params: 查询参数
            db_name: 数据库名
            
        Returns:
            查询结果列表，如果查询失败返回None
        """
        try:
            with closing(self._get_connection(db_name)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(sql, params)
                    return cursor.fetchall()
        except Exception as e:
            logger.error('执行SQL查询失败', {
                'SQL': sql,
                '参数': params,
                '数据库': db_name,
                '错误类型': type(e).__name__,
                '错误信息': str(e)
            })
            return None

    def check_condition(self, db_name: str, table_name: str, condition: str, columns: str = '更新时间') -> Optional[List[Dict[str, Any]]]:
        """
        按指定条件查询数据库表，返回满足条件的指定字段数据。
        
        Args:
            db_name: 数据库名
            table_name: 表名
            condition: SQL条件字符串（不含WHERE）
            columns: 查询字段字符串或以逗号分隔的字段名，默认'更新时间'
            
        Returns:
            查询结果列表，如果查询失败返回None
        """
        if not self.check_infos(db_name, table_name):
            return None
            
        sql = f"SELECT {columns} FROM `{table_name}` WHERE {condition}"
        logger.debug('执行SQL查询', {'库': db_name, '表': table_name, 'SQL': sql})
        return self._execute_query(sql, db_name=db_name)

    def validate_and_format_date(self, date_str: Optional[str], default_date: str) -> str:
        """
        验证并格式化日期字符串。
        
        Args:
            date_str: 日期字符串，支持多种格式
            default_date: 默认日期，当date_str无效时使用
            
        Returns:
            格式化后的日期字符串 'YYYY-MM-DD'
            
        Raises:
            ValueError: 当日期格式无法解析时
        """
        if not date_str:
            return default_date
            
        # 记录尝试的日期格式
        attempted_formats = []
        try:
            # 尝试多种日期格式
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y%m%d', '%Y.%m.%d']:
                try:
                    attempted_formats.append(fmt)
                    return pd.to_datetime(date_str, format=fmt).strftime('%Y-%m-%d')
                except ValueError:
                    continue
                    
            # 如果所有格式都失败，使用pandas的自动解析
            attempted_formats.append('auto')
            return pd.to_datetime(date_str).strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.warning('日期格式转换失败', {
                '输入日期': date_str,
                '尝试的格式': attempted_formats,
                '错误信息': str(e),
                '使用默认日期': default_date
            })
            return default_date

    def _validate_date_range(self, start_date: Optional[str], end_date: Optional[str], 
                           db_name: str, table_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        验证并处理日期范围。
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            db_name: 数据库名
            table_name: 表名
            
        Returns:
            处理后的日期范围元组 (start_date, end_date)，如果处理失败返回 (None, None)
        """
        try:
            # 如果两个日期都未提供，返回None表示不进行日期过滤
            if start_date is None and end_date is None:
                return None, None
            
            # 如果只提供了开始日期，结束日期设为今天
            if start_date is not None and end_date is None:
                end_date = datetime.datetime.today().strftime('%Y-%m-%d')
                logger.debug('未提供结束日期，使用当前日期', {'库': db_name, '表': table_name, '结束日期': end_date})
            
            # 如果只提供了结束日期，开始日期设为1970年
            if start_date is None and end_date is not None:
                start_date = '1970-01-01'
                logger.debug('未提供开始日期，使用默认日期', {'库': db_name, '表': table_name, '开始日期': start_date})
            
            # 格式化日期
            original_start = start_date
            original_end = end_date
            start_date = self.validate_and_format_date(start_date, '1970-01-01')
            end_date = self.validate_and_format_date(end_date, datetime.datetime.today().strftime('%Y-%m-%d'))
            
            # 如果日期格式被修改，记录日志
            if original_start != start_date:
                logger.debug('开始日期格式已调整', {
                    '库': db_name,
                    '表': table_name, 
                    '原始日期': original_start,
                    '调整后日期': start_date
                })
            if original_end != end_date:
                logger.debug('结束日期格式已调整', {
                    '库': db_name,
                    '表': table_name, 
                    '原始日期': original_end,
                    '调整后日期': end_date
                })
            
            # 检查日期顺序
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)
            if start_dt > end_dt:
                logger.debug('日期范围调整', {'库': db_name, '表': table_name, '原开始日期': start_date, '原结束日期': end_date})
                start_date, end_date = end_date, start_date
                
            # # 只在两个日期都是用户明确提供的情况下检查日期范围
            # if original_start != '1970-01-01' and original_end != datetime.datetime.today().strftime('%Y-%m-%d'):
            #     if (end_dt - start_dt).days > 365 * 10:
            #         logger.debug('日期范围过大，已限制为10年', {'库': db_name, '表': table_name, '开始日期': start_date, '结束日期': end_date})
            #         end_date = (start_dt + pd.Timedelta(days=365*10)).strftime('%Y-%m-%d')
                
            return start_date, end_date
            
        except Exception as e:
            logger.error('日期处理失败', {
                '库': db_name, 
                '表': table_name, 
                '开始日期': start_date, 
                '结束日期': end_date, 
                '错误': str(e)
            })
            return None, None

    def _detect_date_field(self, cols_exist: Set[str], date_field: Optional[str] = None) -> Optional[str]:
        """
        检测或验证日期字段。
        
        Args:
            cols_exist: 存在的列名集合
            date_field: 用户指定的日期字段名
            
        Returns:
            有效的日期字段名，如果未找到则返回None
        """
        if date_field:
            if date_field not in cols_exist:
                logger.debug('指定的日期字段不存在', {
                    '指定的日期字段': date_field,
                    '可用的列': list(cols_exist)
                })
                return None
            logger.debug('使用指定的日期字段', {'日期字段': date_field})
            return date_field
        
        # 自动检测可能的日期字段
        possible_date_fields = {'日期', 'date', 'create_time', 'update_time', 'created_at', 'updated_at', '更新时间', '创建时间'}
        detected_field = next((field for field in possible_date_fields if field in cols_exist), None)
        if detected_field:
            logger.debug('自动检测到日期字段', {
                '检测到的日期字段': detected_field,
                '可用的列': list(cols_exist),
                '尝试匹配的字段': list(possible_date_fields)
            })
        else:
            logger.debug('未检测到日期字段', {
                '可用的列': list(cols_exist),
                '尝试匹配的字段': list(possible_date_fields)
            })
        return detected_field

    def _get_selected_columns(self, cols_exist: Set[str], projection: Optional[Dict[str, int]] = None) -> List[str]:
        """
        获取要查询的列名列表。
        
        Args:
            cols_exist: 存在的列名集合
            projection: 列筛选字典，key为列名，value为1表示选中
                      - 如果为None、空字典{}或空列表[]，则返回所有列
                      - 如果为字典，则根据value值筛选列
            
        Returns:
            选中的列名列表
        """
        if not cols_exist:
            logger.warning('表没有可用列')
            return []
            
        # 如果 projection 为 None、空字典或空列表，返回所有列
        if projection is None or projection == {} or projection == []:
            return list(cols_exist)
            
        # 验证列名是否包含特殊字符
        invalid_chars = set('`\'"\\')
        selected_columns = []
        for col in projection:
            if any(char in col for char in invalid_chars):
                logger.warning('列名包含特殊字符，已跳过', {'列名': col})
                continue
            if col in cols_exist and projection[col]:
                selected_columns.append(col)
                
        if not selected_columns:
            logger.info('参数不匹配，返回所有列', {'参数': projection})
            return list(cols_exist)
            
        return selected_columns

    def _build_query_sql(self, db_name: str, table_name: str, selected_columns: List[str], 
                        date_field: Optional[str] = None, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None, limit: Optional[int] = None) -> Tuple[str, List[Any]]:
        """
        构建SQL查询语句和参数。
        
        Args:
            db_name: 数据库名
            table_name: 表名
            selected_columns: 选中的列名列表
            date_field: 日期字段名
            start_date: 开始日期
            end_date: 结束日期
            limit: 限制返回行数，None表示不限制
            
        Returns:
            SQL语句和参数列表的元组
            
        Raises:
            ValueError: 当参数无效时
        """
        if not selected_columns:
            raise ValueError("没有可查询的列")
            
        # 验证数据库名和表名
        if not db_name or not table_name:
            raise ValueError("数据库名和表名不能为空")
            
        # 验证列名
        invalid_chars = set('`\'"\\')
        for col in selected_columns:
            if any(char in col for char in invalid_chars):
                raise ValueError(f"列名包含特殊字符: {col}")
                
        # 使用参数化查询防止SQL注入
        quoted_columns = [f'`{col}`' for col in selected_columns]
        base_sql = f"SELECT {', '.join(quoted_columns)} FROM `{db_name}`.`{table_name}`"
        params = []
        param_names = []  # 用于记录参数名称
        
        # 如果有日期字段，添加日期过滤条件
        if date_field:
            conditions = []
            if start_date is not None:
                conditions.append(f"`{date_field}` >= %s")
                params.append(start_date)
                param_names.append('开始日期')
            if end_date is not None:
                conditions.append(f"`{date_field}` <= %s")
                params.append(end_date)
                param_names.append('结束日期')
            
            if conditions:
                base_sql += " WHERE " + " AND ".join(conditions)
            
        # 只在显式指定limit时添加限制
        if limit is not None:
            if not isinstance(limit, int) or limit <= 0:
                raise ValueError("limit必须是正整数")
            base_sql += f" LIMIT %s"
            params.append(limit)
            param_names.append('限制行数')
            
        return base_sql, params, param_names

    def _convert_decimal_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        将DataFrame中的Decimal类型列转换为float类型。
        
        Args:
            df: 原始DataFrame
            
        Returns:
            转换后的DataFrame
        """
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, Decimal)).any():
                df[col] = df[col].astype(float)
        return df

    # @_execute_with_retry
    def columns_to_list(self, db_name, table_name, columns_name, where: str = None) -> list:
        """
        获取数据表的指定列, 支持where条件筛选, 返回列表字典。
        :param db_name: 数据库名
        :param table_name: 表名
        :param columns_name: 需要获取的列名列表
        :param where: 可选，SQL条件字符串（不含WHERE）
        :return: [{列1:值, 列2:值, ...}, ...]
        """
        if not self.check_infos(db_name, table_name):
            return []
            
        try:
            with closing(self._get_connection(db_name)) as connection:
                with closing(connection.cursor()) as cursor:
                    sql = 'SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = %s AND table_name = %s'
                    cursor.execute(sql, (db_name, table_name))
                    cols_exist = [col['COLUMN_NAME'] for col in cursor.fetchall()]
                    columns_name = [item for item in columns_name if item in cols_exist]
                    if not columns_name:
                        logger.info('未找到匹配的列名', {'库': db_name, '表': table_name, '请求列': columns_name})
                        return []
                    columns_in = ', '.join([f'`{col}`' for col in columns_name])
                    sql = f"SELECT {columns_in} FROM `{db_name}`.`{table_name}`"
                    if where:
                        sql += f" WHERE {where}"
                    logger.debug('执行列查询', {'库': db_name, '表': table_name, 'SQL': sql})
                    cursor.execute(sql)
                    column_values = cursor.fetchall()
            return column_values
        except Exception as e:
            logger.error('列查询失败', {'库': db_name, '表': table_name, '列': columns_name, '错误': str(e)})
            return []

    # @_execute_with_retry
    def dtypes_to_list(self, db_name, table_name, columns_name=None) -> list:
        """
        获取数据表的列名和类型, 支持只返回部分字段类型。
        :param db_name: 数据库名
        :param table_name: 表名
        :param columns_name: 可选，字段名列表，仅返回这些字段的类型
        :return: [{'COLUMN_NAME': ..., 'COLUMN_TYPE': ...}, ...]
        """
        if not self.check_infos(db_name, table_name):
            return []
            
        try:
            with closing(self._get_connection(db_name)) as connection:
                with closing(connection.cursor()) as cursor:
                    sql = 'SELECT COLUMN_NAME, COLUMN_TYPE FROM information_schema.columns WHERE table_schema = %s AND table_name = %s'
                    cursor.execute(sql, (db_name, table_name))
                    column_name_and_type = cursor.fetchall()
                    if columns_name:
                        columns_name = set(columns_name)
                        column_name_and_type = [row for row in column_name_and_type if row['COLUMN_NAME'] in columns_name]
            return column_name_and_type
        except Exception as e:
            logger.error('获取列类型失败', {'库': db_name, '表': table_name, '列': columns_name, '错误': str(e)})
            return []

    # @_execute_with_retry
    def check_infos(self, db_name, table_name) -> bool:
        """
        检查数据库和数据表是否存在。
        :param db_name: 数据库名
        :param table_name: 表名
        :return: 存在返回True，否则False
        """
        try:
            # 检查数据库是否存在
            result = self._execute_query("SHOW DATABASES LIKE %s", (db_name,))
            if not result:
                logger.info('数据库不存在', {'库': db_name})
                return False
                
            # 检查表是否存在
            result = self._execute_query("SHOW TABLES LIKE %s", (table_name,), db_name=db_name)
            if not result:
                logger.info('表不存在', {'库': db_name, '表': table_name})
                return False
            return True
            
        except Exception as e:
            logger.error('检查数据库或表失败', {
                '库': db_name,
                '表': table_name,
                '错误类型': type(e).__name__,
                '错误信息': str(e)
            })
            return False

    def __enter__(self):
        """上下文管理器入口"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出，确保资源被正确释放"""
        self.close()

    def close(self):
        """显式关闭连接池，释放资源"""
        if hasattr(self, 'pool') and self.pool is not None:
            try:
                self.pool.close()
                logger.info('连接池已关闭', {
                    '主机': self.host,
                    '端口': self.port
                })
            except Exception as e:
                logger.error('关闭连接池失败', {
                    '错误': str(e),
                    '主机': self.host,
                    '端口': self.port
                })
            finally:
                self.pool = None

    def _adjust_page_size(self, last_duration, current_page_size, min_size=1000, max_size=10000, target_time=2.0):
        """
        根据上一次批次耗时自动调整下一次的 page_size。
        - last_duration: 上一批次查询耗时（秒）
        - current_page_size: 当前批次大小
        - min_size, max_size: 允许的最小/最大批次
        - target_time: 期望每批耗时（秒）
        """
        if last_duration < target_time / 2 and current_page_size < max_size:
            return min(current_page_size * 2, max_size)
        elif last_duration > target_time * 2 and current_page_size > min_size:
            return max(current_page_size // 2, min_size)
        else:
            return current_page_size

    def data_to_df(
            self, 
            db_name: str, 
            table_name: str,
            start_date: Optional[str] = None, 
            end_date: Optional[str] = None, 
            projection: Optional[Dict[str, int]] = None, 
            limit: Optional[int] = None,
            page_size: Optional[int] = None,
            date_field: Optional[str] = None,
            return_format: Literal['df', 'list_dict'] = 'df'
            ) -> Union[pd.DataFrame, List[Dict[str, Any]]]:
        """
        从数据库表获取数据，支持列筛选、日期范围过滤和行数限制。
        支持两种查询模式：
        1. 使用limit参数进行简单查询
        2. 使用page_size参数进行分页查询
        
        Args:
            db_name: 数据库名
            table_name: 表名
            start_date: 起始日期（包含），支持多种日期格式，如'YYYY-MM-DD'、'YYYY/MM/DD'等
            end_date: 结束日期（包含），支持多种日期格式，如'YYYY-MM-DD'、'YYYY/MM/DD'等
            projection: 列筛选字典，用于指定要查询的列
                      - 键为列名（字符串）
                      - 值为1表示选中该列，0表示不选中该列
                      - 例如：{'日期': 1, '场景名字': 1} 表示只查询这两列
                      - 如果为None、空字典{}或空列表[]，则查询所有列
            limit: 限制返回的最大行数，None表示不限制
            page_size: 分页查询时每页的数据量，None表示不使用分页
            date_field: 日期字段名，如果为None则使用默认的"日期"字段
            return_format: 返回数据格式
                         - 'df': 返回pandas DataFrame（默认）
                         - 'list_dict': 返回列表字典格式 [{列1:值, 列2:值, ...}, ...]
            
        Returns:
            根据return_format参数返回不同格式的数据：
            - 当return_format='df'时，返回DataFrame
            - 当return_format='list_dict'时，返回列表字典
            - 如果查询失败，返回空的DataFrame或空列表
        """
        if not db_name or not table_name:
            logger.error('数据库名和表名不能为空', {'库': db_name, '表': table_name})
            return [] if return_format == 'list_dict' else pd.DataFrame()
            
        # 验证return_format参数
        valid_formats = {'df', 'list_dict'}
        if return_format not in valid_formats:
            logger.error('无效的return_format值', {'库': db_name, '表': table_name, '指定返回数据格式, 有效值应为: ': ', '.join(valid_formats)})
            return [] if return_format == 'list_dict' else pd.DataFrame()

        # 验证日期范围
        start_date, end_date = self._validate_date_range(start_date, end_date, db_name, table_name)
        
        # 检查数据库和表是否存在
        if not self.check_infos(db_name, table_name):
            return [] if return_format == 'list_dict' else pd.DataFrame()
        try:
            with closing(self._get_connection(db_name)) as connection:
                with closing(connection.cursor()) as cursor:
                    # 获取表的所有列
                    cursor.execute(
                        """SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = %s AND table_name = %s""",
                        (db_name, table_name)
                    )
                    cols_exist = {col['COLUMN_NAME'] for col in cursor.fetchall()} - {'id'}
                    
                    # 设置日期字段
                    if start_date is not None and end_date is not None:
                        # 如果未指定日期字段，使用默认的"日期"字段
                        if date_field is None:
                            date_field = "日期"
                        
                        # 检查指定的日期字段是否存在
                        if date_field not in cols_exist:
                            logger.warning('指定的日期字段不存在，将返回所有数据', {
                                '库': db_name, 
                                '表': table_name, 
                                '指定日期字段': date_field
                            })
                            start_date = None
                            end_date = None
                            date_field = None
                    
                    # 获取选中的列
                    selected_columns = self._get_selected_columns(cols_exist, projection)
                    if not selected_columns:
                        logger.info('未找到可用字段', {'库': db_name, '表': table_name, '字段': selected_columns})
                        return [] if return_format == 'list_dict' else pd.DataFrame()

                    # 构建基础SQL
                    base_sql, params, param_names = self._build_query_sql(
                        db_name, table_name, selected_columns, 
                        date_field, start_date, end_date, None
                    )

                    # 如果指定了limit且没有指定page_size，使用简单查询
                    if limit is not None and page_size is None:
                        sql = f"{base_sql} LIMIT %s"
                        params = list(params) + [limit]
                        cursor.execute(sql, tuple(params))
                        result = cursor.fetchall()
                        
                        if result:
                            if return_format == 'list_dict':
                                return result
                            else:
                                df = pd.DataFrame(result)
                                df = self._convert_decimal_columns(df)
                                return df
                        return [] if return_format == 'list_dict' else pd.DataFrame()

                    # 使用分页查询
                    # 获取总记录数
                    count_sql = f"SELECT COUNT(*) as total FROM ({base_sql}) as t"
                    cursor.execute(count_sql, tuple(params))
                    total_count = cursor.fetchone()['total']
                    
                    if total_count == 0:
                        return [] if return_format == 'list_dict' else pd.DataFrame()

                    # 设置默认分页大小
                    if page_size is None:
                        page_size = 1000

                    # 分页查询
                    offset = 0
                    all_results = []
                    min_size, max_size = 1000, 10000
                    target_time = 1.0  # 期望每批1秒

                    while offset < total_count:
                        start_time = time.time()
                        # 添加分页参数
                        page_sql = f"{base_sql} LIMIT %s OFFSET %s"
                        page_params = list(params) + [page_size, offset]
                        cursor.execute(page_sql, tuple(page_params))
                        page_results = cursor.fetchall()

                        if not page_results:
                            break

                        if return_format == 'list_dict':
                            all_results.extend(page_results)
                        else:
                            if len(all_results) == 0:
                                all_results = pd.DataFrame(page_results)
                            else:
                                all_results = pd.concat([all_results, pd.DataFrame(page_results)], ignore_index=True)

                        duration = time.time() - start_time
                        page_size = self._adjust_page_size(duration, page_size, min_size, max_size, target_time)
                        offset += len(page_results)
                        logger.debug('分页查询进度', {
                            '库': db_name,
                            '表': table_name,
                            # '当前偏移量': offset,
                            '总记录数': total_count,
                            '已获取记录数': len(all_results) if return_format == 'list_dict' else len(all_results.index),
                            '本批耗时': f'{duration:.2f}',
                            '下批page_size': page_size
                        })

                    if return_format == 'df' and isinstance(all_results, pd.DataFrame) and not all_results.empty:
                        all_results = self._convert_decimal_columns(all_results)
                    return all_results

        except Exception as e:
            logger.error('数据查询失败', {
                '库': db_name,
                '表': table_name,
                '错误类型': type(e).__name__,
                '错误信息': str(e)
            })
            return [] if return_format == 'list_dict' else pd.DataFrame()


def main():
    dir_path = os.path.expanduser("~")
    my_cont = config.read_config(file_path=os.path.join(dir_path, 'spd.txt'))
    username, password, host, port = my_cont['username'], my_cont['password'], my_cont['host'], int(my_cont['port'])
    host = 'localhost'
    
    # 创建QueryDatas实例
    qd = QueryDatas(username=username, password=password, host=host, port=port)
    
    # 执行查询
    df = qd.data_to_df('聚合数据', '店铺流量来源构成', limit=10)
    print(df)


if __name__ == '__main__':
    main()
    pass