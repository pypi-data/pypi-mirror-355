from typing import Union

from nsanic.exception import WsRpsMsg
from nsanic import verify
from nsanic.libs.component import RdsMeta
from nsanic.libs.consts import Code, StaCode


class WsHandler(RdsMeta):
    STA_CODE = StaCode

    CMD_FUN_MAP = {}

    def __init__(self, cmd_type: Union[int, str, float]):
        self.__cmd_type = cmd_type

    @property
    def cmd_type(self):
        return self.__cmd_type

    async def funapi(self, fcmd, uinfo, data):
        fun = self.CMD_FUN_MAP.get(fcmd)
        if fun:
            try:
                await fun(uinfo, data)
            except WsRpsMsg as msg:
                return [msg.end, msg.mult, fcmd, msg.data, msg.code, msg.hint]
            else:
                return [False, False, fcmd, data, self.STA_CODE.FAIL, '']
        return [False, False, fcmd, None, self.STA_CODE.FAIL, 'unspecified message.']

    async def offline(self, ukey: Union[int, str]):
        """掉线处理逻辑"""
        pass

    def sendmsg(self, code: Code = None, data: Union[dict, list] = None, mult=False, end=False, hint=''):
        """
        消息下发
        :param code: 状态码
        :param data: 消息数据，同类多消息结构可用list 不同类消息请使用{cmd:message}映射关系
        :param mult: 是否为多重消息
        :param end: 是否终止连接
        :param hint: 提示信息转发
        """
        if not code:
            code = self.STA_CODE.PASS
        raise WsRpsMsg(code, data, mult=mult, end=end, hint=hint)

    def vf_str(self, val, require=False, default='', turn=0, minlen: int = None, maxlen: int = None, p_name=''):
        sta, val_info = verify.vstr(
            val, require=require, default=default, turn=turn, minlen=minlen, maxlen=maxlen, p_name=p_name)
        return val_info if sta else self.sendmsg(code=self.STA_CODE.ERR_ARG, hint=val_info)

    def vf_int(self, v, require=False, default=0, minval: int = None, maxval: int = None, inner=True, p_name=''):
        sta, val_info = verify.vint(
            v, require=require, default=default, minval=minval, maxval=maxval, inner=inner, p_name=p_name)
        return val_info if sta else self.sendmsg(code=self.STA_CODE.ERR_ARG, hint=val_info)

    def vf_float(self, val, require=False, default=None, keep_val=3, minval: float or int = None,
                 maxval: float or int = None, inner=True, p_name=''):
        sta, val_info = verify.vfloat(
            val, require=require, default=default, keep_val=keep_val, minval=minval, maxval=maxval,
            inner=inner, p_name=p_name)
        return val_info if sta else self.sendmsg(code=self.STA_CODE.ERR_ARG, hint=val_info)

    def vf_time(self, val, require=False, default=None, time_min=None, time_max=None, inner=True, p_name=''):
        sta, val_info = verify.vdatetime(
            val, require=require, default=default, time_min=time_min, time_max=time_max, inner=inner, p_name=p_name)
        return val_info if sta else self.sendmsg(code=self.STA_CODE.ERR_ARG, hint=val_info)
