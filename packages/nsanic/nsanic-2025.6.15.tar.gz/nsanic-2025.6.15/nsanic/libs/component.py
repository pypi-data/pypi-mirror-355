from typing import Union

from nsanic.libs.mult_log import NLogger
from nsanic.libs.tool import z_compress, z_decompress


class RdsClass:
    rds: 'RdsClient' = ...

    @classmethod
    async def set_zp(cls, name: Union[str, bytes], value, ex=None):
        data = z_compress(value)
        return await cls.rds.set_item(name, data, ex_time=ex)

    @classmethod
    async def get_zp(cls, name: Union[str, bytes], jparse=False):
        data = await cls.rds.get_item(name)
        if data:
            return z_decompress(data, jparse=jparse)
        return None

    @classmethod
    async def hset_zp(cls, name: Union[str, bytes], key: Union[str, bytes], value):
        data = z_compress(value)
        return await cls.rds.set_hash(name, key, data)

    @classmethod
    async def hget_zp(cls, name: Union[str, bytes], key: Union[str, bytes], jparse=False):
        data = await cls.rds.get_hash(name, key)
        if data:
            return z_decompress(data, jparse=jparse)
        return None

    @classmethod
    async def getnum(cls, name: Union[str, bytes], default=0):
        val = await cls.rds.get_item(name)
        if val:
            return int(float(val))
        return default

    @classmethod
    async def getfloat(cls, name: Union[str, bytes], default=0.0):
        val = await cls.rds.get_item(name)
        if val:
            return float(val)
        return default


class LogMeta:

    @classmethod
    def logerr(cls, *err: str):
        NLogger.error(*err)

    @classmethod
    def loginfo(cls, *info):
        NLogger.info(*info)

    @classmethod
    def log_err(cls, *err: str):
        NLogger.error(*err)

    @classmethod
    def log_info(cls, *info):
        NLogger.info(*info)


class ConfMeta(LogMeta):

    conf = None

    @classmethod
    def set_conf(cls, conf):
        cls.conf = conf


class RdsMeta(LogMeta):

    rds: 'RdsClient' = ...

    @classmethod
    async def set_zp(cls, name: Union[str, bytes], value, ex=None):
        data = z_compress(value)
        return await cls.rds.set_item(name, data, ex_time=ex)

    @classmethod
    async def get_zp(cls, name: Union[str, bytes], jparse=False):
        data = await cls.rds.get_item(name)
        if data:
            return z_decompress(data, jparse=jparse)
        return None

    @classmethod
    async def hset_zp(cls, name: Union[str, bytes], key: Union[str, bytes], value):
        data = z_compress(value)
        return await cls.rds.set_hash(name, key, data)

    @classmethod
    async def hget_zp(cls, name: Union[str, bytes], key: Union[str, bytes], jparse=False):
        data = await cls.rds.get_hash(name, key)
        if data:
            return z_decompress(data, jparse=jparse)
        return None

    @classmethod
    async def getnum(cls, name: Union[str, bytes], default=0):
        val = await cls.rds.get_item(name)
        if val:
            return int(float(val))
        return default

    @classmethod
    async def getfloat(cls, name: Union[str, bytes], default=0.0):
        val = await cls.rds.get_item(name)
        if val:
            return float(val)
        return default
