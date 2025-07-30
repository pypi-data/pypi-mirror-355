class SDKError(Exception):
    """SDK所有异常类型的基类"""
    def __init__(self, message):
        self.message = message

    def __str__(self):
        # return f"{self.__class__.__name__}: {self.message}"
        return f"{self.message}"

class ActionRetry(SDKError):
    """动作重试"""

class ConfigError(SDKError):
    """配置异常"""

class ActionTaskRepetitiveError(ActionRetry):
    """任务重复校验异常"""

class SDKRuntimeError(SDKError):
    """插件启动异常"""

class TriggerError(SDKError):
    """触发器异常"""

class ActionError(SDKError):
    """动作异常"""

class PackError(SDKError):
    """插件异常"""
