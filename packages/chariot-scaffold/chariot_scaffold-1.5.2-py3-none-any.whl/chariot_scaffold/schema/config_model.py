from typing import Annotated
from pydantic import BaseModel, Field


class PluginSpecYamlModel(BaseModel):
    plugin_spec_version:  Annotated[str, ""] = "v2"
    extension: Annotated[str, "plugin"] = "plugin"
    entrypoint: Annotated[str, "程序入口"] = None
    module: Annotated[str, "模块名称"] = None
    name: Annotated[str, "插件id, 唯一id"] = None
    title: Annotated[str | dict, "插件名称"] = None
    description: Annotated[str | dict, "插件描述"] = None
    version: Annotated[str, "插件版本"] = "0.1.0"
    vendor: Annotated[str, "插件作者"] = "chariot"
    tags: Annotated[list, "插件标签"] = Field(default_factory=list)
    type: Annotated[str, "插件类型(分类名称)"] = ""
    types: Annotated[dict, "自定义类型"] = Field(default_factory=dict)
    connection: Annotated[dict, "插件连接器"] = Field(default_factory=dict)
    actions: Annotated[dict, "插件动作"] = Field(default_factory=dict)
    alarm_receivers: Annotated[dict, "告警接收器"] = Field(default_factory=dict)
    asset_receivers: Annotated[dict, "资产接收器"] = Field(default_factory=dict)
    triggers: Annotated[dict, "触发器"] = Field(default_factory=dict)

