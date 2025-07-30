import sys
import json
import asyncio
from chariot_scaffold import log, version
from chariot_scaffold.schema.base import StdinModel
from chariot_scaffold.api_server.app import  runserver
from chariot_scaffold.exceptions import SDKRuntimeError
from chariot_scaffold.tools import func_runner


class Runtime:
    def __init__(self, pack: type):
        self.pack = pack
        self.__func_types = ["action", "trigger", "alarm", "asset"]

    @staticmethod
    def init_arguments() -> StdinModel:
        """
        插件初始化运行参数

        #   此方法用于获取需要的运行数据
        #   在千乘系统中，可能并不会传入json数据文件，而是会直接传入json数据或字典数据，此时输入cmd指令长度不足（输入数据不计长度）
        #   所以使用sys.stdin.read()读取可能存在的数据
        """
        arguments = sys.stdin.read()
        if not arguments:
            raise SDKRuntimeError("未检测到初始化参数")

        data = json.loads(arguments)
        if not data:
            raise SDKRuntimeError("初始化参数, 序列化失败")

        stdin = StdinModel(**data)
        log.debug(f"接收初始化参数: {stdin}")
        return stdin

    def func_types_check(self, data) -> str:
        # 验证功能类型是否为 动作、触发器、告警接收器、情报接收器、资产接收器
        type_ = None
        for i in self.__func_types:
            if data.get(i):
                type_ = i
                break
        if not type_:
            raise SDKRuntimeError("功能类型参数非法")
        return type_

    def start(self):
        log.debug(f"启动plugin server V{version}")
        log.debug(f"获取初始化参数,{sys.argv}")

        if sys.argv.count("run"):
            asyncio.run(self.trigger())

        elif sys.argv.count("http"):
            self.action()

        else:
            raise SDKRuntimeError("参数非法")

    @staticmethod
    def action():
        workers = 4
        runserver(workers)

    async def trigger(self):
        data = self.init_arguments()

        self.pack.dispatcher_url = data.body.dispatcher.url
        self.pack.cache_url = data.body.dispatcher.cache_url
        self.pack.webhook_url = data.body.dispatcher.webhook_url

        module = self.pack()
        func_type = self.func_types_check(data.body.model_dump())

        if data.body.connection and not module.trigger_no_need_connection:
            await func_runner(module.connection, data.body.connection)
            # module.connection(**data.body.connection)

        func = module.__getattribute__(eval(f"data.body.{func_type}"))

        await func_runner(func, data.body.input)
