import asyncio
import random
import re
import string
import time

from nsanic.libs.tool_dt import cur_dt


class RngMaker:
    """随机数生成模型"""
    _STR_LIST = set()
    _PRE_STR = ''
    _PRE_NUM = ''
    _DEF_LEN = 32
    _PRE_LEN = 0
    _PRE_NUM_LEN = 0

    @classmethod
    def init(cls, pre_str='', default_len=32):
        cls._PRE_STR = pre_str
        cls._DEF_LEN = default_len
        cls._PRE_NUM = "".join([num for num in re.findall(r'\d+',  cls._PRE_STR)])
        cls._PRE_LEN = len(cls._PRE_STR)
        cls._PRE_NUM_LEN = len(cls._PRE_NUM)

    @staticmethod
    def __date_str(fmt='%Y%m%d%H%M%S%f'):
        """日期时间模式"""
        return cur_dt().strftime(fmt)

    @staticmethod
    def __tamp_int():
        """时间戳毫秒秒模式"""
        return int(time.time() * 1000)

    @staticmethod
    def __hex_num(num: int):
        """转16进制"""
        return hex(num)[2:]

    @classmethod
    def __lower_hex(cls, str_len: int, is_stamp=True):
        """全小写字母随机"""
        hstr = cls.__hex_num(cls.__tamp_int() if is_stamp else int(cls.__date_str()))
        _len = str_len - len(hstr)
        if _len > cls._PRE_LEN:
            _len -= cls._PRE_LEN
        return f"{cls._PRE_STR.lower()}{hstr}{''.join(random.sample(string.ascii_lowercase + string.digits, _len))}"

    @classmethod
    def __letters_hex(cls, str_len: int, is_stamp=True):
        """全字母随机"""
        h_str = cls.__hex_num(cls.__tamp_int() if is_stamp else int(cls.__date_str()))
        length = str_len - len(h_str)
        if length > cls._PRE_LEN:
            length -= cls._PRE_LEN
        return f"{cls._PRE_STR}{h_str}{''.join(random.sample(string.ascii_letters + string.digits, length))}"

    @classmethod
    def __all_num(cls, str_len: int, is_stamp=True):
        """纯数字随机"""
        gen_str = str(cls.__tamp_int()) if is_stamp else cls.__date_str()
        length = str_len-len(gen_str)
        if length > cls._PRE_NUM_LEN:
            length -= cls._PRE_NUM_LEN
        return f"{cls._PRE_NUM}{gen_str}{''.join(random.sample(string.digits, length))}"

    @classmethod
    async def __creator(cls, str_len: int, create_random, is_stamp=True) -> str:
        while True:
            if len(cls._STR_LIST) > 20000:
                await asyncio.sleep(0.002)
                cls._STR_LIST.clear()
            r_str = create_random(str_len, is_stamp)
            if r_str not in cls._STR_LIST:
                cls._STR_LIST.add(r_str)
                return r_str

    @classmethod
    async def gen_str(cls, str_len=30, short_mode=True):
        """
        (不重复)按时间生成指定长度不重复的字符串，默认长度30，短模式最短15 最长46 非短模式最短21 最长50 不在该的长度范围取默认值

        :param str_len: 生成字符串长度. 默认长度30
        :param short_mode: 是否使用短模式 默认 是
        """
        if short_mode and (15 <= str_len <= 46):
            return await cls.__creator(str_len, cls.__lower_hex, short_mode)
        if 21 <= str_len <= 50:
            return await cls.__creator(str_len, cls.__lower_hex, False)
        return await cls.__creator(cls._DEF_LEN, cls.__lower_hex, short_mode)

    @classmethod
    async def gen_num(cls, str_len=18, is_stamp=True):
        """
        (不重复)按时间生成指定长度不重复的数字单号，默认长度18，时间戳模式最短18 最长26 非时间戳模式最短18 最长32 不在该的长度范围取默认值

        :param str_len: 生成字符串长度. 默认长度18
        :param is_stamp: 是否使用时间戳模式 默认 是
        """
        if is_stamp and (18 <= str_len <= 26):
            return await cls.__creator(str_len, cls.__all_num, is_stamp)
        if 18 <= str_len <= 32:
            return await cls.__creator(str_len, cls.__all_num, False)
        return await cls.__creator(18, cls.__all_num, is_stamp)

    @staticmethod
    def mk_int(min_num: int, max_num: int, ji_shu=0):
        """
        (允许重复)按最大值最小值范围取随机数

        :param min_num: 最小值
        :param max_num: 最大值
        :param ji_shu: 取值基数 该参数不为0时 取到的值会对对该值取整再乘以该值
        """
        res = random.randint(min_num, max_num)
        if ji_shu:
            return (res // ji_shu) * ji_shu
        return res

    @staticmethod
    def mk_num(length=5):
        """(允许重复)取指定数量级范围内的随机数"""
        return random.randint(10 ** (length - 1), 10 ** length - 1)

    @staticmethod
    def mk_str(length: int = 16, use_caps=False):
        """随机字符串 默认16位"""
        if use_caps:
            return ''.join(random.sample(string.ascii_lowercase + string.ascii_uppercase + string.digits, length))
        return ''.join(random.sample(string.ascii_lowercase + string.digits, length))

    @staticmethod
    def mk_arr_one(item_list: (list, tuple), weights: (list, tuple) = None):
        """list随机筛选某项, 带权重的话权重配置长度必须等于列表或元组长度"""
        if item_list and isinstance(item_list, list or tuple):
            if weights and (len(item_list) != len(weights)):
                return None
            return random.choices(item_list, weights=weights)
        return None
