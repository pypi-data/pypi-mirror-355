import uuid
from typing import Annotated
from pydantic import BaseModel, field_validator, Field
from chariot_scaffold.tools import timestamp_to_utc_format_date_string


class AlarmModel(BaseModel):
    uid: Annotated[str, "告警唯一id"] = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Annotated[str, "告警名称"] = None
    alarm_ip: Annotated[str, "告警IP"] = None
    alarm_type: Annotated[str, "告警类型"] = None
    sip: Annotated[str, "主体, 即源IP"] = None
    tip: Annotated[str, "客体, 即目的IP"] = None
    cve: Annotated[str, "cev编号"] = None
    source: Annotated[str, "告警源"] = None
    type: Annotated[str, "告警数据类型"] = "json"
    reputation: Annotated[str, "风险等级"] = "good"
    status: Annotated[bool, "处置状态"] = False
    raw: Annotated[str, "告警的原始数据, 优先使用json"] = None
    alarm_at: Annotated[str, "告警触发的时间"] = Field(default_factory=timestamp_to_utc_format_date_string)

    @field_validator("reputation")  # noqa
    @classmethod
    def reputation_value_check(cls, v):
        reputation_enum = ['good', 'bad', 'suspicious', 'urgent']
        if v not in reputation_enum:
            raise ValueError("参数非法")
        return v
