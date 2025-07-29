# -*- coding:utf-8 -*-
import datetime
import warnings
import pymysql
import pandas as pd
from decimal import Decimal
import logging
from contextlib import closing

warnings.filterwarnings('ignore')
"""
程序专门用来下载数据库数据, 并返回 df, 不做清洗数据操作;
"""
logger = logging.getLogger(__name__)


class QueryDatas:
    """
    数据库查询工具类。
    用于连接MySQL数据库，支持表结构检查、条件查询、数据导出为DataFrame、列名和类型获取等功能。
    """

    def __init__(self, username: str, password: str, host: str, port: int, charset: str = 'utf8mb4'):
        """
        初始化数据库连接配置。
        :param username: 数据库用户名
        :param password: 数据库密码
        :param host: 数据库主机
        :param port: 数据库端口
        :param charset: 字符集，默认utf8mb4
        """
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.config = {
            'host': self.host,
            'port': int(self.port),
            'user': self.username,
            'password': self.password,
            'charset': charset,  # utf8mb4 支持存储四字节的UTF-8字符集
            'cursorclass': pymysql.cursors.DictCursor,
        }

    def check_condition(self, db_name, table_name, condition, columns='更新时间'):
        """
        按指定条件查询数据库表，返回满足条件的指定字段数据。
        :param db_name: 数据库名
        :param table_name: 表名
        :param condition: SQL条件字符串（不含WHERE）
        :param columns: 查询字段字符串或以逗号分隔的字段名，默认'更新时间'
        :return: 查询结果列表或None
        """
        if not self.check_infos(db_name, table_name):
            return None
        self.config.update({'database': db_name})
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    sql = f"SELECT {columns} FROM `{table_name}` WHERE {condition}"
                    logger.debug(f"check_condition SQL: {sql}")
                    cursor.execute(sql)
                    result = cursor.fetchall()
                    return result
        except Exception as e:
            logger.error(f"check_condition error: {e}")
            return None

    def data_to_df(self, db_name, table_name, start_date, end_date, projection: dict = None, limit: int = None):
        """
        从数据库表获取数据到DataFrame，支持列筛选、日期范围过滤和行数限制。
        :param db_name: 数据库名
        :param table_name: 表名
        :param start_date: 起始日期（包含）
        :param end_date: 结束日期（包含）
        :param projection: 列筛选字典，e.g. {'日期': 1, '场景名字': 1}
        :param limit: 限制返回的最大行数
        :return: 查询结果的DataFrame
        """
        projection = projection or {}
        df = pd.DataFrame()
        try:
            start_date = pd.to_datetime(start_date or '1970-01-01').strftime('%Y-%m-%d')
            end_date = pd.to_datetime(end_date or datetime.datetime.today()).strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"日期格式错误: {e}")
            return df
        if not self.check_infos(db_name, table_name):
            return df
        self.config['database'] = db_name
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(
                        """SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = %s AND table_name = %s""",
                        (db_name, table_name)
                    )
                    cols_exist = {col['COLUMN_NAME'] for col in cursor.fetchall()} - {'id'}
                    if projection:
                        selected_columns = [k for k, v in projection.items() if v and k in cols_exist]
                        if not selected_columns:
                            logger.info("Warning: Projection 参数不匹配任何数据库字段")
                            return df
                    else:
                        selected_columns = list(cols_exist)
                    if not selected_columns:
                        logger.info("未找到可用字段")
                        return df
                    quoted_columns = [f'`{col}`' for col in selected_columns]
                    base_sql = f"SELECT {', '.join(quoted_columns)} FROM `{db_name}`.`{table_name}`"
                    params = []
                    if '日期' in cols_exist:
                        base_sql += f" WHERE 日期 BETWEEN %s AND %s"
                        params.extend([start_date, end_date])
                    if limit is not None and isinstance(limit, int) and limit > 0:
                        base_sql += f" LIMIT %s"
                        params.append(limit)
                    logger.debug(f"data_to_df SQL: {base_sql}, params: {params}")
                    cursor.execute(base_sql, tuple(params))
                    result = cursor.fetchall()
                    if result:
                        df = pd.DataFrame(result)
                        for col in df.columns:
                            if df[col].apply(lambda x: isinstance(x, Decimal)).any():
                                df[col] = df[col].astype(float)
        except Exception as e:
            logger.error(f"data_to_df error: {e}")
        return df

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
        self.config.update({'database': db_name})
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    sql = 'SELECT COLUMN_NAME FROM information_schema.columns WHERE table_schema = %s AND table_name = %s'
                    cursor.execute(sql, (db_name, table_name))
                    cols_exist = [col['COLUMN_NAME'] for col in cursor.fetchall()]
                    columns_name = [item for item in columns_name if item in cols_exist]
                    if not columns_name:
                        logger.info("columns_to_list: 未找到匹配的列名")
                        return []
                    columns_in = ', '.join([f'`{col}`' for col in columns_name])
                    sql = f"SELECT {columns_in} FROM `{db_name}`.`{table_name}`"
                    if where:
                        sql += f" WHERE {where}"
                    logger.debug(f"columns_to_list SQL: {sql}")
                    cursor.execute(sql)
                    column_values = cursor.fetchall()
            return column_values
        except Exception as e:
            logger.error(f"columns_to_list error: {e}")
            return []

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
        self.config.update({'database': db_name})
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    sql = 'SELECT COLUMN_NAME, COLUMN_TYPE FROM information_schema.columns WHERE table_schema = %s AND table_name = %s'
                    cursor.execute(sql, (db_name, table_name))
                    column_name_and_type = cursor.fetchall()
                    if columns_name:
                        columns_name = set(columns_name)
                        column_name_and_type = [row for row in column_name_and_type if row['COLUMN_NAME'] in columns_name]
            return column_name_and_type
        except Exception as e:
            logger.error(f"dtypes_to_list error: {e}")
            return []

    def check_infos(self, db_name, table_name) -> bool:
        """
        检查数据库和数据表是否存在。
        :param db_name: 数据库名
        :param table_name: 表名
        :return: 存在返回True，否则False
        """
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(f"SHOW DATABASES LIKE %s", (db_name,))
                    database_exists = cursor.fetchone()
                    if not database_exists:
                        logger.info(f"Database <{db_name}>: 数据库不存在")
                        return False
        except Exception as e:
            logger.error(f"check_infos-db error: {e}")
            return False
        self.config.update({'database': db_name})
        try:
            with closing(pymysql.connect(**self.config)) as connection:
                with closing(connection.cursor()) as cursor:
                    cursor.execute(f"SHOW TABLES LIKE %s", (table_name,))
                    if not cursor.fetchone():
                        logger.info(f'{db_name} -> <{table_name}>: 表不存在')
                        return False
                    return True
        except Exception as e:
            logger.error(f"check_infos-table error: {e}")
            return False


if __name__ == '__main__':
    pass