import asyncio
import os
import signal
import time
from typing import Union

import websockets

from nsanic.libs.mult_log import NLogger
from nsanic.libs.tool import json_encode, json_parse


class BaseWsSrv:
    loop = None
    def __init__(self, log=None):
        self.srv_status = 0
        self.run_status = 0
        self.clients = {}
        self.srv_task = None

    @staticmethod
    async def __heartbeat(ws, _: dict):
        await ws.send(json_encode({'cmd': 'beat', 'data': int(time.time())}))

    async def __auth_check(self, ws, msg: dict):
        if not msg and msg.get('tk') != 'qwer442211':
            await ws.send(json_encode({'cmd': 'auth', 'data': 'auth error.'}))
            await self.close_client(ws)
            return

    async def handle_msg(self, ws, msg: Union[dict, str]):
        handler_map = {
            'auth': self.__auth_check,
            'beat': self.__heartbeat,
        }
        cmd = msg.pop('cmd')
        if cmd not in handler_map:
            return None
        return await handler_map[cmd](ws, msg)

    async def client_connection(self, ws, path):
        NLogger.info('当前websocket连接', ws, path, len(self.clients))
        if self.srv_status != 1:
            await ws.send(json_encode({'cmd': 'sys', 'msg': 'server is not running.'}))
            await self.close_client(ws)
            return
        self.clients[ws.id] = ws
        try:
            async for message in ws:
                msg = json_parse(message)
                if not msg:
                    return
                await self.handle_msg(ws, msg)
        except websockets.exceptions.ConnectionClosed:
            NLogger.warning(f"Client disconnected: {len(self.clients)}",)
        finally:
            await self.close_client(ws)

    async def close_client(self, ws):
        try:
            await ws.close()
            (ws.id in self.clients) and self.clients.pop(ws.id)
        except Exception as err:
            NLogger.warning(f'ws 关闭出错：{err}')

    async def broadcast(self, msg: str):
        if self.clients:
            await asyncio.gather(*[client.send(msg) for client in self.clients.values() if client])

    def handle_exit(self, signum):
        NLogger.info('检测到服务终止信号', signum)
        try:
            self.loop.run_until_complete(self.__cleanup(signum))
        except Exception as err:
            _ = err
        self.loop.close()

    async def __cleanup(self, signum):
        NLogger.info(f'服务结束信号{signum}的清理操作...')
        self.srv_status = 2
        for ws_id in list(self.clients.keys()):
            ws = (ws_id in self.clients) and self.clients.pop(ws_id)
            try:
                ws and (await ws.close())
            except Exception as err:
                NLogger.info(f'服务关闭出错:{err}')
        NLogger.info(f'执行队列清理...')
        await self.before_close()
        self.run_status = 2
        self.srv_task and self.srv_task.cancel()

    async def before_start(self):
        pass

    async def before_close(self):
        pass

    async def start(self, host='0.0.0.0', port=6890):
        self.loop = asyncio.get_event_loop()
        self.srv_status = self.run_status = 1
        await self.before_start()
        try:
            async with websockets.serve(self.client_connection, host=host, port=port):
                if os.name == 'posix':
                    self.loop.add_signal_handler(signal.SIGINT, self.handle_exit, signal.SIGINT)
                    self.loop.add_signal_handler(signal.SIGTERM, self.handle_exit, signal.SIGTERM)
                NLogger.info(f"WebSocket server running on ws://{host}:{port}")
                self.srv_task = asyncio.Future()
                await self.srv_task
        except asyncio.exceptions.CancelledError:
            NLogger.warning('服务终止 asyncio.exceptions.CancelledError')
            await self.__cleanup(2)
        except Exception as err:
            NLogger.warning(f'服务终止 其它事件{err}')
            await self.__cleanup(2)

    @classmethod
    def run(cls, host='0.0.0.0', port=6890):
        if os.name == 'posix':
            import uvloop
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
        srv = cls()
        asyncio.run(srv.start(host=host, port=port))
