from nsanic.exception import JsonFinish
from nsanic.libs import consts
from nsanic.libs.component import ConfMeta
from nsanic.libs.consts import StaCode


class CorsMiddle(ConfMeta):

    @classmethod
    async def main(cls, req):
        """通用跨域适配"""
        if req.method == 'OPTIONS':
            # _ = req.body
            # _ = req.args
            # _ = req.files
            # _ = req.form
            # headers = HeaderSet.out(cls.conf)
            if ('*' not in cls.conf.ALLOW_ORIGIN) and (req.server_name not in cls.conf.ALLOW_ORIGIN):
                raise JsonFinish(code=StaCode.FORBID)
                # return HTTPResponse(status=403, headers=headers)
            # return HTTPResponse(status=204, headers=headers)
            raise JsonFinish(code=StaCode.ALLOW)
        if not consts.GLOBAL_SRV_STATUS:
            # return HTTPResponse('Server is not running', status=503, headers=headers)
            raise JsonFinish(code=StaCode.NO_READY)
        return None
