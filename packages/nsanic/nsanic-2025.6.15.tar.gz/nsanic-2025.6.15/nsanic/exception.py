import traceback
from dataclasses import dataclass
from typing import Union

from sanic import Request, response

from nsanic.libs.consts import Code
from nsanic.libs.manager import HeaderSet
from nsanic.libs.mult_log import NLogger
from nsanic.libs.rds_client import RdsError


@dataclass
class JsonFinish(Exception):
    """完成请求状态异常"""
    code: Code
    '''状态码'''
    data: Union[dict, list, str, int, float] = None
    '''响应数据'''
    total: int = 0
    '''针对于分页数据响应的总数量'''
    hint: str = ''
    '''响应消息提示'''
    headers: dict = None
    '''附加响应头'''


@dataclass
class WsRpsMsg(Exception):
    """websocket消息响应"""
    code: Code
    '''状态码'''
    data: Union[dict, list, str, int, float] = None
    '''响应数据'''
    hint: str = ''
    '''响应消息提示'''
    mult: bool = False
    '''是否为多重消息模式'''
    end: bool = False
    '''是否终止连接'''


class CatchExpt:

    code_map = {
        400: '请求结构错误,无法解析的结构',
        404: 'API接口不存在',
        500: '出错啦，请稍后再试或联系管理员检查',
        403: '请求结构不支持'
    }

    @classmethod
    def set_conf(cls, conf):
        cls.conf = conf

    @classmethod
    def __loger(cls, req: Request, err_info: str):
        NLogger.error(
            f"请求异常信息:\n接口--{req.path}\n方法--{req.method}\n头部--{req.headers.items()}\nquery参数--{req.args}\n"
            f"body--{req.body}\n错误信息--{err_info}")

    @classmethod
    def catch_req(cls, req: Request, expt):
        headers = HeaderSet.out(cls.conf)
        hasattr(expt, 'headers') and expt.headers and headers.update(expt.headers)
        if isinstance(expt, RdsError):
            body = {'code': 500, 'data': None, 'msg': 'Invalid Cache Server. Please contact administrator.'}
            return response.json(body, status=500, headers=headers)
        if isinstance(expt, JsonFinish):
            if expt.code.http == 204:
                headers['Content-Length'] = 0
                headers['Content-Type'] = 'text/plain charset=UTF-8'
                return response.HTTPResponse('OK', status=200, headers=headers)
            body = {'code': expt.code.val, 'data': expt.data, 'msg': expt.hint or expt.code.msg}
            return response.json(body, status=expt.code.http, headers=headers)
        body = {'code': 500, 'data': None, 'msg': 'There are some error, please connect administrator to check.'}
        if hasattr(expt, 'status_code'):
            hint = cls.code_map.get(expt.status_code)
            body = {'code': expt.status_code, 'data': None, 'msg': hint}
            if expt.status_code == 500:
                cls.__loger(req, traceback.format_exc())
            return response.json(body, headers=headers)
        cls.__loger(req, traceback.format_exc())
        return response.json(body, status=500)
