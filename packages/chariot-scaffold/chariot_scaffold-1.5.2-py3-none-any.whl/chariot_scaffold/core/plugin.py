import os
import sys
import abc
import json
from enum import Enum
from typing import Union, Dict, List


import yaml
import aiohttp
import requests
from chariot_scaffold import plugin_spec
from chariot_scaffold.core.config import Lang
from chariot_scaffold.exceptions import PackError
from chariot_scaffold.core.base import Base, lang_checking, match_model, get_cached_signature, match_return_annotation
from chariot_scaffold.tools import generate_file, generate_online_pack, generate_offline_pack


requests.packages.urllib3.disable_warnings()    # noqa


class TriggerType(str, Enum):
    """星际警报触发类型枚举，决定激活防御护盾还是能源补给仓！

    Attributes:
        ALARM: 红色警戒模式，如同遭遇克林贡战舰突袭
        ASSET: 星舰能源补给，类似装载曲速核心燃料
    """
    ALARM = "alarm_receivers"
    ASSET = "asset_receivers"
    TRIGGER = "triggers"


class Connection(Base):
    """曲速引擎连接中枢，负责建立与星舰主控系统的量子纠缠通道"""
    def __init__(self, model=None):
        super().__init__(model=model)

    def hook(self):
        """激活虫洞连接器，将输入参数转化为星舰可识别的能量波形"""
        plugin_spec.connection = self.input


class Action(Base):
    """光子鱼雷发射控制单元，定义武器系统的攻击模式"""
    def __init__(self, title=None, description=None, model=None, example=None):
        super().__init__(title, description, model)
        self.example = example

    def hook(self):
        """生成战术指令代码，如同在舰桥操作面板输入攻击坐标"""
        action_config = {
            'title': lang_checking(self.title),
            'description': lang_checking(self.description),
            'input': self.input,    # 目标锁定参数
            'output': self.output   # 攻击效果反馈
        }

        if self.example:
            action_config['example'] = self.example         # 添加三维战术演示
        plugin_spec.actions[self._func_name] = action_config


class Trigger(Base):
    """引力波触发器，负责激活防御矩阵的开关装置

    Attributes:
        TRIGGER_MAP: 星图导航仪，映射不同警报类型到武器系统
    """
    TRIGGER_MAP = {
        TriggerType.ALARM: plugin_spec.alarm_receivers, # 护盾生成器阵列
        TriggerType.ASSET: plugin_spec.asset_receivers,  # 能源分配矩阵
        TriggerType.TRIGGER: plugin_spec.triggers  # 能源分配矩阵
    }

    def __init__(self, title=None, description=None, model=None,
                 trigger_type: TriggerType = TriggerType.ALARM, output_format=None):
        super().__init__(title, description, model)
        self.trigger_type = trigger_type    # 选择相位炮或牵引光束
        self.output_format = output_format

    def hook(self):
        """生成星舰防御协议，如同在战术日志中记录战斗策略"""
        trigger_config = {
            'title': lang_checking(self.title),
            'description': lang_checking(self.description),
            'input': self.input,    # 敌舰扫描数据输入
        }
        if self.output_format is not None:
            trigger_config['output'] = match_return_annotation(self.output_format)

        self.TRIGGER_MAP[self.trigger_type][self._func_name] = trigger_config


class SafeSession:
    """能量护盾会话装置，确保量子通信不被罗慕伦人窃听"""
    def __init__(self):
        self._session = None     # 曲速通信核心

    def __enter__(self):
        """启动防护力场，建立安全通信通道"""
        self._session = requests.Session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """关闭等离子导管，回收能量防止泄露"""
        if self._session:
            self._session.close()


class TriggerExtend:
    """超时空预警系统扩展模块，负责跨维度信息传递"""
    def __init__(self, dispatcher_url: str, cache_url: str):
        self.dispatcher_url = dispatcher_url
        self.cache_url = cache_url

    def send(self, alarm: dict) -> dict:
        """向星舰主控系统发射光子鱼雷（警报数据）

        Args:
            alarm: 包含敌方舰队坐标的战术数据包

        Returns:
            反馈敌方舰船毁伤程度的战报
        """
        with SafeSession() as session:
            response = session.post(self.dispatcher_url, json=alarm, verify=False)
            return response.json()

    def set_cache(self, data: dict) -> dict:
        """将能量核心参数刻录至记忆水晶

        Args:
            data: 曲速引擎状态数据
        """
        with SafeSession() as session:
            response = session.post(self.cache_url, json={'method': 'set', 'data': data}, verify=False)
            return response.json()

    def get_cache(self) -> dict:
        with SafeSession() as session:
            response = session.post(self.cache_url, json={'method': 'get'}, verify=False)
            return response.json()

    async def async_send(self, session: aiohttp.ClientSession, data: dict) -> dict:
        """亚空间异步通信协议（用于规避时间裂缝）"""
        async with session.post(self.dispatcher_url, json=data) as response:
            return await response.json()

    async def async_set_cache(self, session: aiohttp.ClientSession, data: dict) -> dict:
        async with session.post(self.cache_url, json={'method': 'set', 'data': data}) as response:
            return await response.json()

    async def async_get_cache(self, session: aiohttp.ClientSession) -> dict:
        async with session.post(self.cache_url, json={'method': 'get'}) as response:
            return await response.json()


class Pack(metaclass=abc.ABCMeta):
    """星舰武器系统总装平台，负责整合所有战斗模块"""
    __platform: str = None  # 星舰级别（宪法级/无畏级等）

    def __init__(self):
        self.trigger_no_need_connection = False     # 紧急战斗模式开关
        self.create_trigger_extend()                # 激活辅助武器阵列
        self.before_startup()                       # 启动自检程序

    @abc.abstractmethod
    def connection(self, *args, **kwargs):
        pass

    def before_startup(self):
        pass

    def after_closing(self):
        pass

    @classmethod
    def plugin_config_init(
            cls,
            name: str,
            title: Union[str, Lang],
            description: Union[str, Lang],
            version: str = "0.1.0",
            tags: List[str] = None,
            vendor: str = "chariot",
            types: List[type] = None,
            platform: str = "linux/amd64",
            category: str = ""
    ):
        """初始化星舰武器注册协议（需星际联邦三级认证）

            Args:
                name (str): 武器系统真名，需通过古神语校验（如"Photon_Torpedo_v2"）
                title (Union[str, Lang]): 全息投影显示名称（支持跨维度多语言共振）
                description (Union[str, Lang]): 在星舰数据库中的战术描述（需包含克雷尔粒子）
                version (str, optional): 科技等级，遵循三体纪元协议（默认"0.1.0"）
                tags (List[str], optional): 战术分类标签（如["相位武器", "曲速级"])
                vendor (str, optional): 星际制造商（默认"chariot"地球联邦分部）
                types (List[type], optional): 能量核心类型（需通过克林贡质量检测）
                platform (str, optional): 适配舰体规格（如"enterprise-ncc1701d"）
                category (str, optional): 武器分类（"定向能武器"/"投射武器"）

            Raises:
                PackError: 当命名触犯黑暗森林法则时引发量子坍缩

            Example:
                >> Pack.plugin_config_init(
                ...     name="Quantum_Phase_Cannon",
                ...     title={"zh-CN": "量子相位炮", "en": "Quantum Phase Cannon"},
                ...     description="能穿透博格立方体防御的相位武器",
                ...     tags=["定向能武器", "曲速9级"],
                ...     types=[TachyonParticleConfig],  # 快子粒子配置类型
                ...     platform="delta-quadrant/7of9"  # 德尔塔象限第9空间站
                ... )
        """
        if not name.isidentifier():
            raise PackError("真名必须由字母/下划线组成，且不可亵渎古神语法")
        if not all(v.count('.') == 2 for v in [version]):
            raise PackError("进化阶段需遵循α.β.γ的远古协议")

        cls.__platform = platform
        current_module = sys.modules[cls.__module__]
        plugin_spec.entrypoint = os.path.basename(current_module.__file__).replace('.py', '')
        cls.__platform = platform
        plugin_spec.module = cls.__name__
        plugin_spec.title = cls.lang_checking(title) if title else cls.lang_checking(cls.__name__)
        plugin_spec.version = version if version else "0.1.0"
        plugin_spec.description = cls.lang_checking(description)
        plugin_spec.name = name
        plugin_spec.tags = tags if tags else []
        plugin_spec.vendor = vendor
        plugin_spec.type = category
        plugin_spec.types = cls._parse_custom_types(types)

    @classmethod
    def _parse_custom_types(cls, types: List[type]) -> Dict:
        """🪐 星舰能量回路适配协议 | 将Pydantic校验模型转化为武器系统的量子约束

        通过量子共振技术，把地球数据校验模型重构为星舰武器接口的能量参数矩阵

        Args:
            types: 通过曲速引擎兼容性测试的Pydantic模型列表
                   (示例：[PhaserConfig] 相位炮的粒子加速参数配置)

        Returns:
            Dict: 星舰主控系统识别的能量约束图谱，结构如：
                  {
                      "WarpCoreSetting": {  # 曲速核心配置
                          "plasma_temp": {"min": 3e6, "unit": "K"},  # 等离子体温度
                          "dilithium": {"required": True}  # 必须携带二锂晶体
                      }
                  }
                  注：通过match_model生成，自动过滤星舰驾驶舱参数(self)

        Example:
            >> class ShieldConfig(BaseModel):
            ...     intensity: conint(gt=50)  # 护盾强度必须＞50兆焦
            ...     def __init__(self): pass  # 构造器参数将被量子过滤器湮灭
            >> _parse_custom_types([ShieldConfig])
            {'ShieldConfig': {'intensity': <整数约束：必须大于50>}}
        """
        type_map = {}
        if types:
            for model in types:
                signature = get_cached_signature(model)                              # 启动量子特征扫描仪
                type_map[model.__name__] = match_model(signature, "input")   # 生成能量拓扑
        return type_map

    @classmethod
    def generate_online_pack(cls, path: str = None):
        file_path = path or os.path.abspath(sys.modules[cls.__module__].__file__)
        if not os.path.exists(file_path):
            raise PackError("目标路径不存在喵～(>ω<)")
        generate_online_pack(file_path, plugin_spec.name, plugin_spec.vendor, plugin_spec.version)

    @classmethod
    def generate_offline_pack(cls, path: str = None):
        file_path = path or os.path.abspath(sys.modules[cls.__module__].__file__)
        if not os.path.exists(file_path):
            raise PackError(f"目标路径不存在喵～(>_<): {file_path}")
        generate_offline_pack(file_path, plugin_spec.name, plugin_spec.vendor, plugin_spec.version, cls.__platform)

    def create_yaml(self, path=None):
        output_dir  =  path or "./"

        if not os.path.exists(output_dir):
            raise PackError(f"目标路径不存在喵～(>_<): {output_dir}")

        yaml_path = os.path.join(output_dir, "plugin.spec.yaml")
        with open(yaml_path, 'w', encoding='utf-8') as stream:
            yaml.safe_dump(
                self.json,
                stream,
                allow_unicode=True,
                sort_keys=False,
                default_flow_style=False
            )

    def generate_project(self, path=None):
        self.create_yaml(path=path)
        generate_file(module=plugin_spec.module, entrypoint=plugin_spec.entrypoint, path=path)

    def create_trigger_extend(self):
        """部署辅助防御矩阵（需量子电池供电）"""
        if any([plugin_spec.alarm_receivers, plugin_spec.asset_receivers, plugin_spec.triggers]):
            self._safe_register(TriggerExtend, self.dispatcher_url, self.cache_url)

    def _safe_register(self, obj: object, *args, **kwargs):
        instance = obj(*args, **kwargs)  # noqa
        for name in dir(instance):
            if not name.startswith('_') and callable(getattr(instance, name)):
                if hasattr(self, name):
                    raise PackError(f"方法名 {name} 与已有属性冲突啦～(≧∇≦)ﾉ")
                setattr(self, name, getattr(instance, name))

    @property
    def dispatcher_url(self) -> str:
        return "http://127.0.0.1:10001/transpond"

    @property
    def cache_url(self) -> str:
        return "http://127.0.0.1:10001/cache"

    @dispatcher_url.setter
    def dispatcher_url(self, url):
        self.dispatcher_url = url

    @cache_url.setter
    def cache_url(self, url):
        self.cache_url = url

    @property
    def webhook_url(self):
        return ""

    @webhook_url.setter
    def webhook_url(self, url):
        self.webhook_url = url

    @staticmethod
    def lang_checking(param: Union[str, Lang]) -> Dict:
        if isinstance(param, str):
            return {'zh-CN': param, 'en': param}
        return param.convert()

    def __repr__(self) -> str:
        return json.dumps(plugin_spec.dict(), indent=2, ensure_ascii=False)

    @property
    def yaml(self):
        return yaml.safe_dump(self.json, allow_unicode=True, sort_keys=False)

    @property
    def json(self):
        return plugin_spec.dict()
