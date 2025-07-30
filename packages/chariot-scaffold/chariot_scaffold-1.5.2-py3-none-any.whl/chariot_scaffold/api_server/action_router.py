import time
import importlib
from fastapi import APIRouter

from chariot_scaffold import log
from chariot_scaffold.core.config import PluginSpecYaml
from chariot_scaffold.tools import clean_logs, read_logs, func_runner
from chariot_scaffold.exceptions import ActionTaskRepetitiveError
from chariot_scaffold.schema.base import ActionOutputModel, ActionOutputBodyModel, StdinModel


class ActionTasks:
    def __init__(self,  expired: int = 3600):
        self.__tasks = {}
        self.__expired = expired

    def create_task(self, tid: str, action):
        if not self.__tasks.get(tid):
            self.__tasks[tid] = {"output": None, "expired": int(time.time()), "action": action}
            return True
        else:
            return False

    def verify_multi_ident_tid(self, tid):
        tid_output = self.__tasks[tid]["output"]
        if not tid_output:
            time.sleep(30)      # todo 等待时间, 待优化
            raise ActionTaskRepetitiveError("任务正在运行中, 请勿重复下发")
        else:
            return tid_output

    def expired_check(self):
        for k in list(self.__tasks.keys()):
            nts = int(time.time())
            if nts - self.__tasks[k]["expired"] >= self.__expired:
                del self.__tasks[k]

    def task_done(self, tid, output: ActionOutputModel):
        self.__tasks[tid]["output"] = output

    def get_tasks(self):
        return self.__tasks


action_router = APIRouter()
plugin_spec = PluginSpecYaml()
plugin_spec.deserializer()
action_task_manager = ActionTasks()

# 为了持久化连接器, 降低会话开销, 全局加载插件.
module = importlib.import_module(plugin_spec.entrypoint)
pack = module.__getattribute__(plugin_spec.module)()


@action_router.post("/actions/{action_name}", response_model=ActionOutputModel, name="执行动作")
async def actions(action_name: str, plugin_stdin: StdinModel):
    """
    执行一个动作并将运行结果返回
    """
    # log.info(f"获取初始化参数, {plugin_stdin}")
    output = ActionOutputModel(body=ActionOutputBodyModel())

    # multi identical tid check
    if plugin_stdin.tid:
        action_task_manager.expired_check()
        if not action_task_manager.create_task(plugin_stdin.tid, action_name):
            tid_output = action_task_manager.verify_multi_ident_tid(plugin_stdin.tid)
            return tid_output

    # import module
    # module = importlib.import_module(plugin_spec.entrypoint)
    # pack = module.__getattribute__(plugin_spec.module)()

    # connection
    if plugin_stdin.body.connection:
        await func_runner(pack.connection, plugin_stdin.body.connection)

    # action running
    res = await func_runner(pack.__getattribute__(action_name), plugin_stdin.body.input)
    output.body.log = read_logs()

    # check output
    if plugin_spec.actions.get(action_name):
        if plugin_spec.actions[action_name]["output"].get("output"):
            output.body.output["output"] = res
        else:
            output.body.output = res

    # multi identical tid check
    if plugin_stdin.tid:
        action_task_manager.task_done(plugin_stdin.tid, output)

    clean_logs()
    pack.after_closing()
    return output


@action_router.get("/manager/tasks", name="** 查看任务")
def manager_action_tasks():
    """
    查看当前插件执行过多少任务
    """
    return action_task_manager.get_tasks()
