from typing import Annotated
from pydantic import BaseModel, Field
from chariot_scaffold.core.config import Lang, Datatypes

"""
action plugin stdin:
{'version': 'v1', 'type': 'action_start', 'body': {'action': 'empty_action', 'meta': {}, 'connection': {}, 'dispatcher': {}, 'input': {'whatever': '123123'}, 'enable_web': False, 'shared_dir': False}, 'tid': 'HsCagrqyieyvrabe57BSAK'}
{"version": "v1", "type": "action_start", "body": {"action": "empty_action", "meta": {}, "connection": {}, "dispatcher": {}, "input": {"whatever": "123123"}, "enable_web": false, "shared_dir": false}, "tid": "HsCagrqyieyvrabe57BSAK"}

trigger plugin stdin:
{'version': 'v1', 'type': 'alarm_receiver_start', 'body': {'alarm': 'foo', 'meta': None, 'connection': {}, 'dispatcher': {'cache_url': 'https://10.1.40.20:8080/api/v2/plugin_cache/5/alarm_receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f', 'url': 'https://10.1.40.20:8080/api/v2/alarm/default/5/receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f', 'webhook_url': 'https://10.1.40.20:8080/api/v2/alarm/default/5/receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f'}, 'input': {'bootstrap_servers': ['172.36.0.1'], 'group_id': 'test', 'topic': 'kafka_test'}, 'enable_web': False, 'shared_dir': False}, 'tid': ''}
{"version": "v1", "type": "alarm_receiver_start", "body": {"alarm": "foo", "meta": null, "connection": {}, "dispatcher": {"cache_url": "https://10.1.40.20:8080/api/v2/plugin_cache/5/alarm_receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f", "url": "https://10.1.40.20:8080/api/v2/alarm/default/5/receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f", "webhook_url": "https://10.1.40.20:8080/api/v2/alarm/default/5/receiver?api_key=440a9484-2f8e-4cda-afe4-528159e0da2f"}, "input": {"bootstrap_servers": ["172.36.0.1"], "group_id": "test", "topic": "kafka_test"}, "enable_web": false, "shared_dir": false}, "tid": ""}

action output:
{'version': 'v1', 'type': 'action', 'body': {'output': {}, 'status': 'True', 'log': '暂时没日志', 'error_trace': ''}}
{"version": "v1", "type": "action", "body": {"output": {}, "status": "True", "log": "暂时没日志", "error_trace": ""}}
"""


class StdinBodyDispatcherModel(BaseModel):
    url: Annotated[str, "dispatcher_url, 与千乘引擎交互的地址"] = ""
    cache_url: Annotated[str, "缓存地址"] = ""
    webhook_url: Annotated[str, "已弃用"] = ""


class StdinBodyModel(BaseModel):
    asset: Annotated[str, "资产"] = None
    action: Annotated[str, "动作"] = None
    alarm: Annotated[str, "告警"] = None
    trigger: Annotated[str, "触发器"] = None
    meta: Annotated[dict | None, "已弃用"] = None
    connection: Annotated[dict, "连接器"] = Field(default_factory=dict)
    dispatcher: Annotated[StdinBodyDispatcherModel, "调度员, 包含dispatcher_url, cache_url, webhook_url"] = Field(default_factory=dict)
    input: Annotated[dict, "插件入参"] = Field(default_factory=dict)
    enable_web: Annotated[bool, "被动触发的触发器, 对外提供一个 api 地址，引擎可以去触发这个地址"] = False
    shared_dir: Annotated[bool, "共享目录, 给插件容器挂载容器卷"] = False


class StdinModel(BaseModel):
    version: Annotated[str, "版本"]
    type: Annotated[str, "类型"]
    tid: Annotated[str, "任务id"] = ""
    body: Annotated[StdinBodyModel, "任务情况"]


class ActionOutputBodyModel(BaseModel):
    output: Annotated[dict, "动作输出"] = Field(default_factory=dict)
    status: Annotated[str, "动作运行状态"] = "ok"  # 成功为ok, 失败用error, 引擎会在该字段判断是否动作存在异常
    log: Annotated[str, "动作日志, 插件运行过程中的日志, 异常日志也可以放在这里"] = ""
    error_trace: Annotated[str, "动作异常日志"] = ""  # 不参与校验


class ActionOutputModel(BaseModel):
    # code: Annotated[int, "状态"] = 200    #  http状态码为201即可, 不再需要手动添加业务状态码
    # message: Annotated[str, "内容"] = "success"  # 可不填
    version: Annotated[str, "版本"] = "v1"
    type: Annotated[str, "类型"] = "action"
    body: Annotated[ActionOutputBodyModel, "动作运行情况"]

class StandardOutput(BaseModel):
    success: Annotated[
        bool,
        Lang("执行状态", "Execution Status"),
        Lang("""True表示业务逻辑执行成功，False表示业务逻辑执行失败""",
             "True indicates business logic success"
             "False indicates business failure"
             )
    ] = True

    data: Annotated[
        Datatypes.any_,
        Lang("响应数据", "Response Data"),
        Lang("""成功时返回业务数据实体，失败时可能返回错误详情或null""",
             "Business data entity on success, "
             "error details or None on failure"
             ),
        "print"
    ] = None

    error: Annotated[
        str,
        Lang("错误信息", "Error Message"),
        Lang(
            "业务逻辑执行失败时返回的错误详情，成功时为null",
            "Error details when operation failed, null on success"
        )
    ] = None

    message: Annotated[
        str,
        Lang("信息提示", "User Message"),
        Lang("""人类可读的执行结果说明，可用于界面直接展示""",
             "Human-readable execution result description, "
             "suitable for direct UI display"
             )
    ] = None

