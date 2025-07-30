import multiprocessing
from asyncio import AbstractEventLoop, Protocol
from socket import socket
from ssl import SSLContext
from typing import Optional, Union

from sanic import Sanic
from sanic.http.constants import HTTP
from sanic.mixins.startup import HTTPVersion

from nsanic.base_conf import BaseConf
from nsanic.libs import consts
from nsanic.libs.mk_random import RngMaker
from nsanic.libs.rds_client import RdsClient
from nsanic.libs.tool import is_await_fun


class InitServer:

    def __init__(
            self,
            conf,
            middlewares: (list, tuple) = None,
            bp_arr: (list, tuple) = None,
            exceptions: (list, tuple) = None,
            forbid_before_evt=True,
            start_evt: list = None,
            stop_evt: list = None):
        """
        :param conf: BaseConf 对象
        :param middlewares: middleware 对象列表或元组
        :param bp_arr: 蓝图元组或集合
        :param exceptions: 全局异常捕获器
        :param forbid_before_evt: 是否在启动事件完成前进行接口拦截
        :param start_evt: 启动需要注册的事件 可选参数 **_
        :param stop_evt: 服务结束前的注册事件 可选参数 **_
        """
        self.__conf: BaseConf = conf
        consts.GLOBAL_TZ = conf.TIME_ZONE
        RngMaker.init(pre_str=self.__conf.SERVER_ID)
        name = multiprocessing.current_process().name
        name_arr = name.split('-')
        proc_name = f"{name_arr[-2]}{name_arr[-1]}" if len(name_arr) >= 2 else name
        self.proc_name = proc_name
        if not forbid_before_evt:
            consts.GLOBAL_SRV_STATUS = True
        self.__evt_start = start_evt or []
        self.__evt_stop = stop_evt or []
        self.__srv = Sanic(self.__conf.SERVER_NAME, log_config=self.__conf.log_conf())
        self.__srv.update_config(self.__conf)
        for mdw_fun in middlewares or []:
            mdw_fun.set_conf(self.__conf)
            self.__srv.middleware(mdw_fun.main)
        self.ws_offline_listen = []
        for bp_cls in bp_arr:
            bp_cls.init(self.__conf.SERVER_NAME, version=self.__conf.VER_CODE)
            bp_cls.load_default_api()
            self.__srv.blueprint(bp_cls.bpo)
            self.ws_offline_listen.extend(bp_cls.ws_handlers)
            bp_cls.ws_handlers.clear()
            bp_cls.DEFAULT_APIS.clear()
        for expt_fun in exceptions or []:
            expt_fun.set_conf(self.__conf)
            self.__srv.error_handler.add(Exception, expt_fun.catch_req)
        self.__srv.register_listener(self.__after_server_start, 'after_server_start')
        self.__srv.register_listener(self.__before_server_stop, 'before_server_stop')

    async def __after_server_start(self, app, loop):
        if self.__conf.CONF_RDS:
            for k, cnf in self.__conf.CONF_RDS.items():
                RdsClient.init(cnf, name=k)
            self.__conf.rds = RdsClient.clt()
        listen_set = set()
        for ws_hd in self.ws_offline_listen:
            loop.create_task(ws_hd.init_offline_queue())
            if hasattr(ws_hd.ws_manager, 'init_loop') and (ws_hd.ws_manager.__name__ not in listen_set):
                ws_hd.ws_manager.set_conf(f"{self.__conf.SERVER_NAME}_{self.__conf.SERVER_ID}", self.proc_name)
                ws_hd.ws_manager.init_loop(rds=RdsClient.clt(), loop=loop)
                listen_set.add(ws_hd.ws_manager.__name__)
        listen_set.clear()
        for fun in self.__evt_start:
            (await fun(**{'app': app, 'loop': loop})) if is_await_fun(fun) else fun(**{'app': app, 'loop': loop})
        self.__evt_start.clear()
        self.ws_offline_listen.clear()
        consts.GLOBAL_SRV_STATUS = True

    async def __before_server_stop(self, app, loop):
        consts.GLOBAL_SRV_STATUS = False
        for fun in self.__evt_stop:
            (await fun(**{'app': app, 'loop': loop})) if is_await_fun(fun) else fun(**{'app': app, 'loop': loop})
        self.__evt_stop.clear()

    @property
    def main(self):
        return self.__srv

    def add_signal(self, signal_map: dict):
        """信号注册"""
        if not signal_map:
            return
        for k, v in signal_map.items():
            callable(v) and self.__srv.add_signal(v, k)

    def add_start_event(self, events):
        if callable(events):
            self.__evt_start.append(events)
        if isinstance(events, (list, tuple)):
            self.__evt_start.extend(events)

    def add_stop_event(self, events):
        if callable(events):
            self.__evt_stop.append(events)
        if isinstance(events, (list, tuple)):
            self.__evt_stop.extend(events)

    def run(self,
            protocol: Optional[type[Protocol]] = None,
            auto_reload: bool=None,
            version: HTTPVersion = HTTP.VERSION_1,
            ssl: Union[None, SSLContext, dict, str, list, tuple] = None,
            sock: Optional[socket] = None,
            backlog: int = 100,
            register_sys_signals: bool = True,
            unix: Optional[str] = None,
            loop: Optional[AbstractEventLoop] = None,
            reload_dir: Optional[Union[list[str], str]] = None,
            noisy_exceptions: Optional[bool] = None,
            motd: bool = True,
            verbosity: int = 0,
            motd_display: Optional[dict[str, str]] = None,
            auto_tls: bool = False,
            single_process: bool = False,
            ):
        """
        Args:

            auto_reload (Optional[bool]): Reload app whenever its source code is changed.
                Enabled by default in debug mode.
            version (HTTPVersion): HTTP Version.
            ssl (Union[None, SSLContext, dict, str, list, tuple]): SSLContext, or location of certificate and key
                for SSL encryption of worker(s).
            sock (Optional[socket]): Socket for the server to accept connections from.
            protocol (Optional[Type[Protocol]]): Subclass of asyncio Protocol class.
            backlog (int): A number of unaccepted connections that the system will allow
                before refusing new connections.
            register_sys_signals (bool): Register SIG* events.
            unix (Optional[str]): Unix socket to listen on instead of TCP port.
            loop (Optional[AbstractEventLoop]): AsyncIO event loop.
            reload_dir (Optional[Union[List[str], str]]): Directory to watch for code changes, if auto_reload is True.
            noisy_exceptions (Optional[bool]): Log exceptions that are normally considered to be quiet/silent.
            motd (bool): Display Message of the Day.
            verbosity (int): Verbosity level.
            motd_display (Optional[Dict[str, str]]): Customize Message of the Day display.
            auto_tls (bool): Enable automatic TLS certificate handling.
            single_process (bool): Enable single process mode.

        Returns:
            None

        Raises:
            RuntimeError: Raised when attempting to serve HTTP/3 as a secondary server.
            RuntimeError: Raised when attempting to use both `fast` and `workers`.
            RuntimeError: Raised when attempting to use `single_process` with `fast`, `workers`, or `auto_reload`.
            TypeError: Raised when attempting to use `loop` with `create_server`.
            ValueError: Raised when `PROXIES_COUNT` is negative.
        """
        self.__srv.run(
            host=self.__conf.HOST,
            port=self.__conf.RUN_PORT,
            workers=self.__conf.RUN_WORKER if not self.__conf.RUN_FAST else 1,
            fast=self.__conf.RUN_FAST,
            debug=self.__conf.DEBUG_MODE,
            dev=self.__conf.DEBUG_MODE,
            access_log=self.__conf.ACCESS_LOG,
            protocol=protocol,
            auto_reload=auto_reload,
            version=version,
            ssl=ssl,
            sock=sock,
            backlog=backlog,
            register_sys_signals=register_sys_signals,
            unix=unix,
            loop=loop,
            reload_dir=reload_dir,
            noisy_exceptions=noisy_exceptions,
            motd=motd,
            motd_display=motd_display,
            verbosity=verbosity,
            auto_tls=auto_tls,
            single_process=single_process,
        )
