import asyncio
import datetime
import time
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, Sequence, Set, Union
from uuid import UUID

from aiomysql import create_pool

from nsanic.libs.mult_log import NLogger
from nsanic.libs.tool import json_encode
from nsanic.libs.tool_dt import dt_str, check_leap, month_days

_escape_table = [chr(x) for x in range(128)]
_escape_table[0] = "\\0"
_escape_table[ord("\\")] = "\\\\"
_escape_table[ord("\n")] = "\\n"
_escape_table[ord("\r")] = "\\r"
_escape_table[ord("\032")] = "\\Z"
_escape_table[ord('"')] = '\\"'
_escape_table[ord("'")] = "\\'"


def _escape_unicode(value: str, mapping=None) -> str:
    """escapes *value* without adding quote.

    Value should be Unicode
    """
    return value.translate(_escape_table)


escape_string = _escape_unicode


def escape_item(val: Any, charset, mapping=None) -> str:
    if mapping is None:
        mapping = encoders
    encoder = mapping.get(type(val))

    # Fallback to default when no encoder found
    if not encoder:
        try:
            encoder = mapping[str]
        except KeyError:
            raise TypeError("no default type converter defined")

    if encoder in (escape_dict, escape_sequence):
        val = encoder(val, charset, mapping)
    else:
        val = encoder(val, mapping)
    return val


def escape_dict(val: Dict, charset, mapping=None) -> dict:
    n = {}
    for k, v in val.items():
        quoted = escape_item(v, charset, mapping)
        n[k] = quoted
    return n


def escape_sequence(val: Sequence, charset, mapping=None) -> str:
    n = []
    for item in val:
        quoted = escape_item(item, charset, mapping)
        n.append(quoted)
    return "(" + ",".join(n) + ")"


def escape_set(val: Set, charset, mapping=None) -> str:
    return ",".join([escape_item(x, charset, mapping) for x in val])


def escape_bool(value: bool, mapping=None) -> str:
    return str(int(value))


def escape_object(value: Any, mapping=None) -> str:
    return str(value)


def escape_int(value: int, mapping=None) -> str:
    return str(value)


def escape_float(value: float, mapping=None) -> str:
    return "%.15g" % value


def escape_unicode(value: str, mapping=None) -> str:
    return "'%s'" % _escape_unicode(value)


def escape_str(value: str, mapping=None) -> str:
    return "'%s'" % escape_string(str(value), mapping)


def escape_null(value: None, mapping=None) -> str:
    return "NULL"


def escape_timedelta(obj: datetime.timedelta, mapping=None) -> str:
    seconds = int(obj.seconds) % 60
    minutes = int(obj.seconds // 60) % 60
    hours = int(obj.seconds // 3600) % 24 + int(obj.days) * 24
    if obj.microseconds:
        fmt = "'{0:02d}:{1:02d}:{2:02d}.{3:06d}'"
    else:
        fmt = "'{0:02d}:{1:02d}:{2:02d}'"
    return fmt.format(hours, minutes, seconds, obj.microseconds)


def escape_time(obj: datetime.datetime, mapping=None) -> str:
    if obj.microsecond:
        fmt = "'{0.hour:02}:{0.minute:02}:{0.second:02}.{0.microsecond:06}'"
    else:
        fmt = "'{0.hour:02}:{0.minute:02}:{0.second:02}'"
    return fmt.format(obj)


def escape_datetime(obj: datetime.datetime, mapping=None) -> str:
    return f"'{obj.isoformat()}'"


def escape_date(obj: datetime.date, mapping=None) -> str:
    fmt = "'{0.year:04}-{0.month:02}-{0.day:02}'"
    return fmt.format(obj)


def escape_struct_time(obj: time.struct_time, mapping=None) -> str:
    return escape_datetime(datetime.datetime(*obj[:6]))


def _convert_second_fraction(s) -> int:
    if not s:
        return 0
    # Pad zeros to ensure the fraction length in microseconds
    s = s.ljust(6, "0")
    return int(s[:6])


encoders = {
    bool: escape_bool,
    int: escape_int,
    float: escape_float,
    str: escape_str,
    tuple: escape_sequence,
    list: escape_sequence,
    set: escape_sequence,
    frozenset: escape_sequence,
    dict: escape_dict,
    type(None): escape_null,
    datetime.date: escape_date,
    datetime.datetime: escape_datetime,
    datetime.timedelta: escape_timedelta,
    datetime.time: escape_time,
    time.struct_time: escape_struct_time,
    Decimal: escape_object,
}


class DBClient:
    _DB_CLIENT_MAP = {}
    _SPLIT_SUFFIX = {1: 'str', 2: '_y%Y', 3: '_y%Ym%m', 4: '_y%Yw%w', 5: '_y%Ym%md%d'}
    '''分表模式'''
    _DB_TYPE_MAP = {
        1: 'BIGINT', 2: 'INT', 3: 'SMALLINT', 4: 'TINYINT', 5: 'VARCHAR', 6: 'TEXT', 7: 'LONGTEXT', 8: 'DATE',
        9: 'FLOAT', 10: 'DECIMAL(10,2)'}
    _ju_map = {'eq': ' = ', 'lt': " < ", 'gt': " > ", 'lte': " <= ", 'gte': ' >= '}

    def __init__(self, conf: dict):
        if 'database' in conf:
            conf['db'] = conf.pop('database')
        self.__conf = conf
        self.run_status = 0
        '''连接状态 1 已连接 0 未连接'''
        self.__ping_stak = None
        self.__db_pool = None

    @property
    def db_pool(self):
        return self.__db_pool

    @classmethod
    def clt(cls, name='default') -> 'DBClient':
        if name not in cls._DB_CLIENT_MAP:
            raise Exception(f"当前连接配置未初始化: {name}")
        return cls._DB_CLIENT_MAP[name]

    @classmethod
    def init(cls, conf: dict, name: Union[str, int, float, bytes] = None):
        """单例模型请用该方法进行初始化(请在事件循环里调用该方法)"""
        if not all(key in conf for key in ['host', 'port', 'db']):
            raise Exception('Redis连接配置错误,缺少必要的连接配置项')
        clt = cls._DB_CLIENT_MAP.get(name)
        if not clt:
            clt = cls(conf)
            cls._DB_CLIENT_MAP[name] = clt
        return clt

    def init_loop(self, **_):
        loop = asyncio.get_event_loop()
        if self.__ping_stak:
            self.stop_loop()
        self.run_status = 1
        self.__ping_stak = loop.create_task(self.__db_loop_ping())

    def stop_loop(self):
        self.__ping_stak and self.__ping_stak.cancel()
        self.__ping_stak = None

    @staticmethod
    def check_val(val, field, column_map: dict[str: tuple]):
        if val is not None:
            if isinstance(val, UUID):
                val = str(val)
            elif isinstance(val, Enum):
                val = val.val if hasattr(val, 'val') else val.value
            return encoders.get(type(val))(val)
        if field not in column_map:
            raise Exception(f'表不包含指定的字段{field}')
        v = column_map.get(field)[5]
        return (f"'{v}'" if isinstance(v, str) else str(v)) if (v is not None) else 'NULL'

    async def __create_db_conn(self):
        self.run_status = 1
        self.__db_pool = await create_pool(**self.__conf)

    async def _get_connection(self):
        if not self.__db_pool:
            await self.__create_db_conn()
        conn = await self.__db_pool.acquire()
        return conn

    async def _release_connection(self, conn):
        if not self.__db_pool:
            await self.__create_db_conn()
        await self.__db_pool.release(conn)

    async def exec_sql(self, sql: Union[str, list], with_transaction=False):
        if isinstance(sql, str):
            sql = [sql]
        if not self.__db_pool:
            await self.__create_db_conn()
        async with self.__db_pool.acquire() as conn:
            try:
                if not with_transaction:
                    async with conn.cursor() as cursor:
                        for sql in sql:
                            await cursor.execute(sql)
                else:
                    await conn.begin()
                    async with conn.cursor() as cursor:
                        for sql in sql:
                            await cursor.execute(sql)
                await conn.commit()
                sta = True
            except Exception as err:
                with_transaction and (await conn.rollback())
                if str(err).find('Lost connection'):
                    self.__db_pool = None
                NLogger.error(f'执行sql出错: {err} \n{sql}')
                sta = False
            # await self._release_connection(conn)
        return sta

    async def exec_query(self, sql: str, with_rows=False) -> Union[list, bool, None]:
        # conn = await self._get_connection()
        if not self.__db_pool:
            await self.__create_db_conn()
        async with self.__db_pool.acquire() as conn:
            try:
                async with conn.cursor() as cursor:
                    await cursor.execute(sql)
                    res = await cursor.fetchall()
                    if not with_rows:
                        dlist = [dict(zip([column[0] for column in cursor.description], row)) for row in res]
                    else:
                        dlist = res
            except Exception as err:
                if str(err).find('Lost connection'):
                    self.__db_pool = None
                NLogger.error(f'执行sql出错: {err} \n{sql}')
                dlist = False
            # await self._release_connection(conn)
            return dlist

    async def __db_loop_ping(self):
        while self.run_status == 1:
            if not self.__db_pool:
                await self.__create_db_conn()
            try:
                await self.exec_query('SELECT 1')
            except Exception as err:
                NLogger.error(f'数据库ping出错：{err}')
                self.__db_pool = None
                await self.__create_db_conn()
            await asyncio.sleep(60)

    @classmethod
    def get_split_suffix(cls, split, split_val: Union[str, int, float, datetime.datetime, datetime.date] = None,
                         tz='America/Sao_Paulo'):
        if not split:
            return ''
        if split not in cls._SPLIT_SUFFIX:
            raise Exception('Invalid split table type.')
        if split == 1:
            return f'{split_val}'
        return f'{dt_str(split_val, fmt=cls._SPLIT_SUFFIX.get(split), tz=tz)}'

    @classmethod
    def _create_tb(
            cls,
            column_map: dict[str: tuple],
            tb_name: str,
            split_suffix="",
            union_idx_arr: Union[tuple[tuple[str]], list[list[str]]] = None):
        tb_name = cls._tb_name(tb_name, split_suffix=split_suffix)
        if not union_idx_arr:
            union_idx_arr = []
        tb_param, pk_arr, idx_arr = [], [], []
        for k, v in column_map.items():
            if v[0]:
                pk_arr.append(k)
            elif v[3]:
                idx_arr.append(k)
            len_str = f"({v[2]})" if v[2] else ""
            if v[1] not in {6, 7}:
                dft_str = (f"DEFAULT '{v[5]}'" if isinstance(v[5], str) else f"DEFAULT {v[5]}") if (
                            v[5] is not None) else ""
            else:
                dft_str = ""
            null_str = f"NULL" if v[4] else ""
            cmt_str = f"COMMENT '{v[6]}'" if v[6] else ""
            auto_str = "AUTO_INCREMENT" if v[0] else ""
            tb_param.append(f"`{k}` {cls._DB_TYPE_MAP.get(v[1])} {len_str} {dft_str} {null_str} {auto_str} {cmt_str}")
        for ite in pk_arr:
            tb_param.append(f" PRIMARY KEY (`{ite}`)")
        for ite in idx_arr:
            tb_param.append(f"INDEX idx_{ite} (`{ite}`)")
        for item in union_idx_arr:
            if not item:
                raise Exception('无效的唯一索引设置')
            for ite in item:
                if ite not in column_map:
                    raise Exception(f'当前表未包含的字段：{ite}')
            tb_param.append(f"union_idx_{'_'.join(item)}")
        tb_sql = f"CREATE TABLE IF NOT EXISTS `{tb_name}` ({','.join(tb_param)}) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        return tb_sql

    @classmethod
    def gen_insertup_sql_old(
            cls,
            tb_name: str,
            column_map: dict[str, tuple],
            dlist: list[dict],
            split_suffix="",
            up_field: list[str] = None,
            add_field: list[str] = None,
            mult_field: list[str] = None,
            max_field: list[str] = None,
            min_field: list[str] = None,
    ):
        v_list = []
        for item in dlist:
            if not isinstance(item, dict):
                raise Exception(f'读到不符合规范的数据结构：{item}, {type(item)}, {dlist}')
            arr = [cls.check_val(item.get(k), k, column_map) for k in column_map]
            v_list.append("({})".format(','.join(arr)))
        tb_name = cls._tb_name(tb_name, split_suffix=split_suffix)
        sql = F"INSERT INTO `{tb_name}`({','.join([f'`{f}`' for f in column_map])}) VALUES "
        sql += ",".join(v_list)
        if not any((up_field, add_field, mult_field, max_field, min_field)):
            return sql
        sql += " ON DUPLICATE KEY UPDATE "
        if up_field:
            sql += f'{",".join(["{0}=VALUES({0})".format(field) for field in up_field if field in column_map])},'
        if add_field:
            sql += f'{",".join(["{0}={0}+VALUES({0})".format(field) for field in add_field if field in column_map])},'
        if mult_field:
            sql += f'{",".join(["{0}={0}*VALUES({0})".format(field) for field in mult_field if field in column_map])},'
        if max_field:
            sql += f'{",".join(["{0}=GREATEST({0},VALUES({0}))".format(field) for field in max_field if field in column_map])},'
        if min_field:
            sql += f'{",".join(["{0}=LEAST({0},VALUES({0}))".format(field) for field in min_field if field in column_map])},'
        sql = sql[:-1]
        return sql

    @classmethod
    def gen_insertup_sql(
            cls,
            tb_name: str,
            column_map: dict[str, tuple],
            dlist: list[dict],
            split_suffix="",
            up_field: list[str] = None,
            add_field: list[str] = None,
            mult_field: list[str] = None,
            max_field: list[str] = None,
            min_field: list[str] = None,
    ):
        v_list = []
        for item in dlist:
            if not isinstance(item, dict):
                raise Exception(f'读到不符合规范的数据结构：{item}, {type(item)}, {dlist}')
            arr = [cls.check_val(item.get(k), k, column_map) for k in column_map]
            v_list.append("({})".format(','.join(arr)))
        tb_name = cls._tb_name(tb_name, split_suffix=split_suffix)
        sql = F"INSERT INTO `{tb_name}`({','.join([f'`{f}`' for f in column_map])}) VALUES "
        sql += ",".join(v_list)
        if not any((up_field, add_field, mult_field, max_field, min_field)):
            return sql
        sql += " AS up_rows ON DUPLICATE KEY UPDATE "
        if up_field:
            sql += f'{",".join(["{0}=up_rows.{0}".format(field) for field in up_field if field in column_map])},'
        if add_field:
            sql += f'{",".join(["{0}={0}+up_rows.{0}".format(field) for field in add_field if field in column_map])},'
        if mult_field:
            sql += f'{",".join(["{0}={0}*up_rows.{0}".format(field) for field in mult_field if field in column_map])},'
        if max_field:
            sql += f'{",".join(["{0}=GREATEST({0},VALUES({0}))".format(field) for field in max_field if field in column_map])},'
        if min_field:
            sql += f'{",".join(["{0}=LEAST({0},VALUES({0}))".format(field) for field in min_field if field in column_map])},'
        sql = sql[:-1]
        return sql

    @classmethod
    def _gen_cond(cls, cond: dict):
        if not cond:
            return ""
        sql_c = []
        for k, v in cond.items():
            karr = k.split('__')
            if isinstance(v, datetime.date):
                v = v.strftime('%Y-%m-%d')
            if isinstance(v, datetime.datetime):
                v = v.strftime('%Y-%m-%d %H:%M:%S')
            if len(karr) < 2:
                sql_c.append(f"`{k}`={v}") if isinstance(v, (int,float)) else sql_c.append(f"`{k}`='{v}'")
                continue
            juk = karr[1].lower()
            ju_v = cls._ju_map.get(juk)
            if ju_v:
                sql_c.append(f"`{karr[0]}`{ju_v}{v}" if isinstance(v, (int, float)) else f"`{karr[0]}`{ju_v}'{v}'")
                continue
            if juk in ('in', 'notin'):
                if isinstance(v[0], datetime.date):
                    v = [t.strftime('%Y-%m-%d') for t in v]
                if isinstance(v[0], datetime.datetime):
                    v = [t.strftime('%Y-%m-%d %H:%M:%S') for t in v]
                v_str = ""
                if isinstance(v[0], str):
                    v_str = ("'{}',"*len(v)).format(*v)[:-1]
                if isinstance(v[0], (int, float)):
                    v_str = ','.join(list(map(str, v)))
                v_str and sql_c.append(f"`{karr[0]}` IN ({v_str})" if juk == 'in' else f"`{karr[0]}` NOT IN ({v_str})")
                continue
            if juk == 'isnull':
                sql_c.append(f"{karr[0]} IS NULL" if ju_v else f"{karr[0]} IS NOT NULL")
                continue
            if juk == 'between':
                if (not v) or (not isinstance(v, (list, tuple))) or (not  len(v) != 2):
                    raise Exception('between必须指定首尾区间范围')
                sql_c.append(f"{karr[0]} BETWEEN {v[0]} AND {v[1]}")
        if sql_c:
            return  f" WHERE {' AND '.join(sql_c)}"
        return ""

    @classmethod
    def _tb_name(cls, tb_name: str, split_suffix="", cond: dict = None, split:int=0, split_key: str = None, tz: str=None):
        if not split:
            return tb_name
        if split_suffix:
            return f"{tb_name}{split_suffix}"
        if split and (not split_key or not cond):
            raise Exception('分表模式必须指定分表字段以及分表查询条件')
        kval = (cond.get(split_key) or cond.get(f'{split_key}__gte') or cond.get(f'{split_key}__lte')
                or cond.get(f'{split_key}__gt') or cond.get(f'{split_key}__lt')) or int(time.time())
        return f"{tb_name}{cls.get_split_suffix(split, kval, tz=tz)}"

    @classmethod
    def gen_query_sql(
            cls,
            tb_name: str,
            cond: dict = None,
            field: Union[tuple, list, set] = None,
            sumfield: Union[tuple, list, set] = None,
            avgfield: Union[tuple, list, set] = None,
            countfield: Union[tuple, list, set] = None,
            distinct: Union[list[str], tuple[str]] = None,
            havings: Union[list[str], tuple[str], str] = None,
            offset: int = None,
            limit: int = None,
            groups: Union[str, list, tuple] = None,
            orders: Union[str, list, tuple] = None,
            split_suffix="",
            split=0,
            split_key: str = None,
            tz: str=None):
        str_group = ','.join(groups) if groups else ''
        str_sum = ','.join([f'SUM({f}) AS {f}_sum' for f in sumfield]) if sumfield else ''
        str_avg = ','.join([f'AVG({f}) AS {f}_avg' for f in avgfield]) if avgfield else ''
        str_count = ','.join([f'COUNT({f}) AS {f}_count' for f in countfield]) if countfield else ''
        str_com = ','.join([f'{f} AS {f}' for f in field]) if field else '*'
        distinct_str = f" COUNT(DISTINCT {','.join(list(distinct))}) AS _count" if distinct else ""
        sql, tag_f, fields = "SELECT", 0, []
        if str_group:
            sql += (str_group + ',')
            tag_f = 1
            group_by = f" GROUP BY {str_group}"
            fields.extend(groups)
        else:
            group_by = " "
        if str_sum:
            sql += f" {str_sum},"
            tag_f = 1
            fields.extend(sumfield)
        if str_avg:
            sql += f" {str_avg},"
            tag_f = 1
            fields.extend(avgfield)
        if str_count:
            sql += f" {str_count},"
            tag_f = 1
            fields.extend(countfield)
        if str_com:
            sql += f" {str_com},"
            tag_f = 1
            fields.extend(field)
        if distinct_str:
            sql += f" {distinct_str},"
            tag_f = 1
            fields.extend('_count')
        tb_name = cls._tb_name(tb_name, split_suffix=split_suffix, cond=cond, split=split, split_key=split_key, tz=tz)
        sql = f"{sql[0: -1]} FROM `{tb_name}` " if tag_f else f"{sql} * FROM `{tb_name}` "
        cond_str = cls._gen_cond(cond)
        sql += cond_str
        sql += f"{group_by}"
        if havings:
            sql += f" HAVING {' AND '.join(havings)} " if isinstance(havings, list) else f" HAVING {havings}"
        if orders:
            if isinstance(orders, str):
                od_s = orders[0]
                order_str = f"{orders[1:]} DESC" if od_s=='-'  else (f"{orders[1:]} ASC" if od_s=='+' else f"{orders}")
            else:
                order_list = [f"{f[1:]} DESC" if f[0]=='-'  else (f"{f[1:]} ASC" if f[0]=='+' else f"{f}") for f in orders]
                order_str = ','.join(order_list)
            sql += f" ORDER BY {order_str}"
        if limit is not None:
            sql += f" LIMIT {limit}"
        if offset is not None:
            sql += f" OFFSET {offset}"
        return sql, fields

    async def get_count(self, tb_name: str, cond: dict=None, distinct: Union[list[str], tuple[str]]=None,
                        split_suffix="", split=0, split_key: str = None, tz: str=None):
        tb_name = self._tb_name(tb_name, split_suffix=split_suffix, cond=cond, split=split, split_key=split_key, tz=tz)
        sql = f"SELECT COUNT(DISTINCT {','.join(list(distinct))}) AS _count" if distinct else "SELECT COUNT(1) AS _count"
        sql += f" FROM {tb_name}"
        sql += self._gen_cond(cond)
        s = await self.exec_query(sql, with_rows=True)
        if s:
            return s[0][0]
        return 0

    async def query_on_page(
            self, tb_name: str, cond: dict, field: Union[tuple, list, set] = None, page=1, size=20,
            sumfield: Union[tuple, list, set] = None, avgfield: Union[tuple, list, set] = None,
            countfield: Union[tuple, list, set] = None, distinct: Union[list[str], tuple[str]] = None,
            groups: Union[str, list, tuple] = None, orders: Union[str, list, tuple] = None,
            split=0, split_key: str = None, tz: str=None, split_count=1):
        if page < 1:
            page = 1
        offset = (page - 1) * size
        if split:
            if split == 1:
                split_count = 1
            # f_dt = to_datetime(cond.get(split_key, int(time.time())), fmt='%Y-%m-%d', tz=tz)
            f_dt = (cond.get(split_key) or cond.get(f'{split_key}__gte') or cond.get(f'{split_key}__lte')
                    or cond.get(f'{split_key}__gt') or cond.get(f'{split_key}__lt')) or int(time.time())
            darr = []
            for i in range(split_count):
                darr.append(self.get_split_suffix(split, f_dt, tz))
                if split == 2:
                    f_dt = f_dt - datetime.timedelta(days=365 if not check_leap(f_dt.year) else 366)
                elif split == 3:
                    f_dt = f_dt - datetime.timedelta(days=month_days(f_dt.year, f_dt.month))
                elif split == 4:
                    f_dt = f_dt - datetime.timedelta(days=7)
                elif split == 5:
                    f_dt = f_dt - datetime.timedelta(days=1)
            count_map, scount, cur_count = {}, 0, 0
            for suffix in darr:
                try:
                    count = await self.get_count(
                        tb_name, cond=cond, distinct=distinct, split_suffix=suffix, split=split, split_key=split_key, tz=tz)
                except Exception as err:
                    NLogger.error(f'{tb_name}查询数量出错: {err}')
                    count = 0
                if not count:
                    continue
                scount += count
                if (cur_count < size) and (scount > offset):
                    if not cur_count:
                        pos = offset - scount + count
                    else:
                        pos = 0
                    size = (size - cur_count) if ((count - pos) >= size) else count - pos
                    count_map[suffix] = (size, pos)
                    cur_count += size
            dlist = []
            for suffix, v in count_map.items():
                lmt = round(v[0])
                dsql, fields = self.gen_query_sql(
                    tb_name, cond=cond, groups=groups, sumfield=sumfield, countfield=countfield, avgfield=avgfield,
                    field=field, distinct=distinct, offset=round(v[1]), limit=lmt, orders=orders,
                    split_suffix=suffix, split=split, split_key=split_key, tz=tz)
                data = await self.exec_query(dsql, with_rows=True)
                if lmt == 1:
                    data = [data] if data else []
                dlist.extend(self.row_list_out(data or [], fields))
            return dlist, scount
        try:
            count = await self.get_count(tb_name, cond=cond, distinct=distinct)
            sql, fields = self.gen_query_sql(
                tb_name, cond=cond, field=field, sumfield=sumfield, avgfield=avgfield, countfield=countfield,
                distinct=distinct, limit=size, offset=offset, groups=groups, orders=orders)
            dlist = await self.exec_query(sql, with_rows=True)
            return self.row_list_out(dlist, fields), count
        except Exception as err:
            NLogger.error(f'{tb_name}查询数量出错: {err}')
            return [], 0

    @classmethod
    def row_list_out(cls, dlist: Union[list, tuple, dict], fields: Union[list, tuple], num_keep=2):
        """
        查询数据格式化映射输出
        :param dlist: 查询原数组数据
        :param fields: 字段顺序
        :param num_keep: 浮点或decimal保留的小数位
        """
        data_list = []
        for item in dlist or []:
            info = {}
            for index, value in enumerate(fields):
                info[value] = cls.fmt_row(item[index], num_keep=num_keep)
            data_list.append(info)
        return data_list

    @staticmethod
    def fmt_row(val, num_keep=2):
        if isinstance(val, datetime.date):
            return val.strftime('%Y-%m-%d')
        if isinstance(val, datetime.datetime):
            return val.strftime('%Y-%m-%d %H:%M:%S')
        if isinstance(val, Decimal):
            return round(float(val), num_keep)
        if isinstance(val, float):
            return round(val, num_keep)
        if isinstance(val, bytes):
            return val.decode('utf-8')
        if isinstance(val, (list, dict, tuple)):
            return json_encode(val)
        return val
