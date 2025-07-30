import asyncio
from typing import Union

from sanic import Request
from sanic.exceptions import WebsocketClosed
from sanic.server.protocols.websocket_protocol import WebSocketProtocol
from websockets.protocol import State

from nsanic.libs import tool_ws
from nsanic.libs.component import ConfMeta
from nsanic.libs.consts import StaCode
from nsanic.libs.manager import WsConnector
from nsanic.libs.mult_log import NLogger


class BaseWebsocket(ConfMeta):
    STA_CODE = StaCode
    CMD_MAP = {}
    '''服务命令映射'''
    ws_manager = WsConnector

    dft_type: Union[int, str] = 1
    '''系统默认消息类型'''
    beat_code: Union[int, str] = 1
    '''心跳消息标码'''
    reject_code: Union[int, str] = 2
    '''弹回消息标码'''
    delay_fail = 10
    '''授权或无效连接响应延时（秒）'''

    def __init__(self):
        self.fun_pack_msg: callable = tool_ws.pack_msg
        self.fun_parse_msg: callable = tool_ws.parse_msg
        self.delay_pre = round(self.delay_fail * 0.6, 2)
        self.delay_aft = round(self.delay_fail * 0.4, 2)
        for v in self.CMD_MAP.values():
            v.STA_CODE = self.STA_CODE

    @classmethod
    def init(cls):
        return cls()

    @staticmethod
    def get_ukey(uinfo):
        return uinfo.get('uid') or uinfo.get('id') or uinfo.get('userid') if isinstance(uinfo, dict) else uinfo

    async def init_offline_queue(self):
        while 1:
            off_ws = await self.ws_manager.OFFLINE_QUEUE.get()
            if off_ws:
                ukey = getattr(off_ws, 'ukey', None)
                if not ukey:
                    continue
                cur_ws = self.ws_manager.get_ws(ukey)
                if cur_ws and (cur_ws.ws_proto.id == off_ws.ws_proto.id):
                    await self.on_offline(ukey)
                for k, v in self.CMD_MAP.items():
                    try:
                        await v.offline(ukey)
                    except Exception as err:
                        NLogger.error(f'用户掉线处理出错：{ukey}, {err}')

    async def client_listen(self, ws, uinfo):
        ukey = self.get_ukey(uinfo)
        while ws.ws_proto.state == State.OPEN:
            cmd, fcmd, data, extra = self.fun_parse_msg(await ws.recv())
            if cmd and (cmd == self.dft_type) and (fcmd == self.beat_code):
                await ws.send(self.fun_pack_msg(
                    self.dft_type, self.beat_code, data=data, code=self.STA_CODE.PASS, req=extra))
                continue
            fun = self.CMD_MAP.get(cmd)
            if fun and fun.funapi:
                mlist, is_end, in_send = [], False, False
                try:
                    msg_arg = await fun.funapi(fcmd, uinfo, data)
                    is_end = msg_arg.pop(0)
                    is_mult = msg_arg.pop(0)
                    if not is_mult:
                        mlist = [self.fun_pack_msg(cmd, *msg_arg, req=extra)]
                    else:
                        if isinstance(msg_arg[1], dict):
                            mlist = [self.fun_pack_msg(cmd, c, d, msg_arg[2], req=extra) for c, d in msg_arg[1].items()]
                        elif isinstance(msg_arg[1], list):
                            mlist = [self.fun_pack_msg(cmd, msg_arg[0], d, msg_arg[2], req=extra) for d in msg_arg[1]]
                    in_send = True
                    for msg in mlist:
                        msg and (await ws.send(msg))
                    if is_end:
                        return await self.on_offline(ukey)
                except WebsocketClosed:
                    if (not is_end) and mlist and hasattr(self.ws_manager, 'save_to_histories'):
                        await self.ws_manager.save_to_histories(ukey, mlist)
                    return await self.on_offline(ukey)
                except Exception as err:
                    NLogger.error(f'处理消息出错：{err}')
                    if (not is_end) and mlist and in_send and hasattr(self.ws_manager, 'save_to_histories'):
                        await self.ws_manager.save_to_histories(ukey, mlist)
                    await ws.send(self.fun_pack_msg(
                        cmd, fcmd, code=self.STA_CODE.FAIL, req=extra, hint='A error cause failed'))
            else:
                await ws.send(self.fun_pack_msg(
                    self.dft_type, self.reject_code, code=self.STA_CODE.FAIL, hint='Unspecified message'))
        return None

    async def wsrouter(self, req: Request, ws):
        """Websocket路由服务"""
        uinfo = await self.wsauth(req, ws)
        if not uinfo:
            self.delay_aft and (await asyncio.sleep(self.delay_aft))
            return await ws.close()
        key_info = await self.check_ws_conn(uinfo, req, ws)
        if not key_info:
            self.delay_aft and (await asyncio.sleep(self.delay_aft))
            return await ws.close()
        await self.update_status(uinfo)
        ukey = self.get_ukey(uinfo)
        await self.ws_manager.send_histories(ukey)
        setattr(ws, 'ukey', ukey)
        setattr(ws, 'connector_name', self.ws_manager.__name__)
        isinstance(key_info, str) and (await self.ws_manager.set_ws(ukey, ws, key_info=key_info))
        await self.client_listen(ws, uinfo)

    async def check_ws_conn(self, uinfo, req, ws) -> Union[bool, str, None]:
        timestamp = req.headers.get('Timestamp') or req.args.get('Timestamp')
        if not timestamp:
            self.delay_pre and (await asyncio.sleep(self.delay_pre))
            await ws.send(self.fun_pack_msg(
                self.dft_type, self.reject_code, code=self.STA_CODE.FAIL, hint='missing params,reject'))
            return None
        ukey = self.get_ukey(uinfo)
        timestamp = int(timestamp)
        if hasattr(self.ws_manager, 'WS_ONLINE_KEY'):
            old_info = await self.ws_manager.check_old_ws(ukey)
            if old_info:
                old_arr = old_info.split(b'--' if isinstance(old_info, bytes) else '--')
                if int(old_arr[1]) >= timestamp:
                    self.delay_pre and (await asyncio.sleep(self.delay_pre))
                    await ws.send(self.fun_pack_msg(
                        self.dft_type, self.reject_code, code=self.STA_CODE.FAIL, hint='invalid connection,reject'))
                    return None
        key_info = None
        if hasattr(self.ws_manager, 'MAIN_CHANNEL'):
            key_info = f"{self.ws_manager.MAIN_CHANNEL}--{timestamp}"
        return key_info or True

    async def update_status(self, uinfo):
        """更新用户监听的频道信息 更新连接状态等相关内容写在这里"""
        pass

    async def wsauth(self, req, ws) -> (object, dict, str, int):
        """基础接口认证处理 接入/认证等"""
        print(ws, req)
        raise Exception('接口未指定授权，不允许访问')

    async def on_offline(self, ukey):
        return await self.ws_manager.offline(ukey)


class WsProtocol(WebSocketProtocol):
    connector_map = {}

    def connection_lost(self, exc):
        async def to_queue(ws, conn_name):
            connector = self.connector_map.get(conn_name)
            connector and (await connector.OFFLINE_QUEUE.put(ws))

        super(WsProtocol, self).connection_lost(exc)
        if self.websocket is not None:
            u_key, name = getattr(self.websocket, 'ukey', None), getattr(self.websocket, 'connector_name', None)
            if (not u_key) or (not name):
                return
            loop = asyncio.get_running_loop()
            loop.create_task(to_queue(self.websocket, name))
