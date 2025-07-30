import abc
import inspect
import asyncio
import functools
from enum import Enum
from typing import get_args, get_origin, Annotated, Literal, NewType

from pydantic import BaseModel

from chariot_scaffold import data_mapping
from chariot_scaffold.core.config import Lang
from chariot_scaffold.exceptions import PackError



@functools.lru_cache(maxsize=128)
def get_cached_signature(func):
    """🛸 量子签名加速器 | 缓存星舰操作员的灵魂印记

    通过量子纠缠技术缓存函数签名，为超光速参数解析提供动力！

    Args:
        func (Callable): 星舰操作员的手部动作捕捉（函数对象）

    Returns:
        inspect.Signature: 经过量子压缩的操作员灵魂波形图
    """
    return inspect.signature(func)


def lang_checking(param):
    """🌌 银河翻译核心 | 跨维度语言谐振装置

        将单一语言输入转化为星际联邦标准双语格式，支持137种外星语实时互译

        Args:
            param (str | Lang): 需要翻译的原始语言信号

        Returns:
            dict: 经过虫洞压缩的双语字典，包含zh-CN和en两种文明编码

        Raises:
            CosmicStatic: 当接收到碳基生物无法理解的频率时触发
        """
    if isinstance(param, str):
        return {"zh-CN": param, "en": param}    # 🐲 双龙谐振场启动
    elif isinstance(param, Lang):
        return param.convert()                  # 🧚♀️ 调用仙女座翻译协议


def match_param(name, anno, param=None):
    """🌌 量子态参数装配器 | 将原始数据流转化为星舰可识别的能量形态

    通过超弦振动识别参数类型，自动装配默认能量容器，并为特殊参数加载星际枚举协议

    Args:
        name (str): 参数在三维世界的原始名称（如'warp_speed'）
        anno (Type): 经过超弦编码的参数类型信号
        param (Optional[inspect.Parameter]): 来自地球程序的原始参数样本

    Returns:
        dict: 装配完成的参数能量包，包含类型/默认值/校验规则三重维度

    Note:
        当检测到暗物质参数时，会自动启动反物质防护罩[2,5](@ref)
    """
    tp = match_datatype(match_annotated_type(anno))
    title_description_enum = match_title_description_enum(anno)
    literal = title_description_enum["enum"]
    title = title_description_enum["title"]
    description = title_description_enum["description"]
    display = title_description_enum["display"]

    res = {
        "title": lang_checking(title) if title is not None else lang_checking(name),
        "description": lang_checking(description) if description is not None else lang_checking(name),
        "type": tp,
    }

    if param is not None:
        default_require = match_default_require(param)
        default = default_require.get("default", None)
        require = default_require.get("require", None)
        enum_ = default_require.get("enum", None)

        if require:
            res["require"] = require

        if default is not None:
            res["default"] = default

        if tp == "[]string" and default is None:
            res["default"] = []  # 🧺 换上干净篮子
        if tp == "[]object" and default is None:
            res["default"] = {}  # 🗃️ 准备魔法柜子
        if enum_ is not None:
            res["enum"] = enum_

    if literal is not None:
        res["enum"] = get_args(literal)

    if display:
        res["print"] = True

    return res


def match_model(signature, direction):
    """🪐 曲速引擎蓝图生成器 | 将函数签名转化为星舰能量回路设计图

    通过捕获函数签名的量子纠缠态，自动生成输入/输出端口的超维度连接方案

    Args:
        signature (inspect.Signature): 来自地球函数的原始能量波形
        direction (str): 能量流动方向（'input'输入端口/'output'推进器）

    Returns:
        dict: 符合星际航行标准的能量回路拓扑图[4,6](@ref)

    Example:
        》》》 当direction='input'时，会过滤掉驾驶员座位参数(self)
    """
    parameters = signature.parameters
    res = {}
    if direction == "input":
        for name, param in parameters.items():
            if name != "self":
                res[name] = match_param(name, param.annotation, param)
    elif direction == "output":
        res = match_return_annotation(signature.return_annotation)
    return res


def match_annotated_type(anno):
    """🔭 超维度注解望远镜 | 穿透Annotated的量子迷雾

    从多重注解的量子叠加态中，精准捕捉基础数据类型的引力波纹

    Args:
        anno (Annotated): 被多重元数据包裹的量子纠缠态

    Returns:
        Type: 剥离后的纯净数据类型信号

    Note:
        当遇到未被注解包裹的类型时，会直接启动曲速引擎返航[1](@ref)
    """
    origin = get_origin(anno)
    if origin is Annotated:
        args = get_args(anno)
        return args[0]
    else:
        return anno


def match_datatype(anno):
    """🔮 维度类型转换器 | 跨宇宙数据类型翻译官

    将地球程序员理解的类型，转化为星舰核心能处理的超弦振动模式

    Args:
        anno (Type): 三维世界的数据类型信号

    Returns:
        str: 经过超弦理论编码的跨维度类型标识

    Note:
        当检测到暗物质类型时会自动启动量子退相干保护罩
    """

    origin = match_annotated_type(anno)

    if isinstance(origin, BaseModel.__class__):
        tp = origin.__name__
    elif isinstance(origin, NewType):
        tp = origin.__name__
    else:
        tp = data_mapping[str(origin)]
    return tp


def match_title_description_enum(anno):
    """🌠 超弦信息解码头盔 | 从量子纠缠态中提取星舰参数元数据

    解析Annotated类型的超弦振动波纹，提取标题/描述/枚举等星际航行必要参数

    Args:
        anno (Annotated): 携带多维元数据的量子包裹

    Returns:
        dict: 解码后的星图数据包（含标题/描述/枚举等导航信息）

    Raises:
        PackError: 当检测到不完整的量子纠缠态时触发超新星警报💥
    """
    literal = None
    display = False
    title = None
    description = None

    origin = get_origin(anno)
    if origin is Annotated:
        args = get_args(anno)
        if len(args) < 3:
            raise PackError("❌ 量子纠缠态不稳定！需要type/title/description三体共振")

        title = args[1]
        description = args[2]

        # 🔍 寻找Literal藏宝图
        if len(args) > 3:
            literal = next(filter(lambda x: get_origin(x) is Literal, args), None)
            if "print" in args:
                display = True

    res = {"title": title, "description": description, "enum": literal, "display": display}
    return res


def match_default_require(param):
    """⚡ 暗物质能量校准装置 | 调节参数的量子波动阈值

    为星舰参数配置默认能量容器，并激活参数必填校验场的引力波

    Args:
        param (inspect.Parameter): 来自地球程序的原始参数样本

    Returns:
        dict: 包含默认值/必填规则/枚举限制的三相能量场

    Example:
        >> 当检测到Enum型能量时，自动生成星舰级选项列表[1](@ref)
    """
    res = {}
    if param.default == inspect.Parameter.empty:
        res['require'] = True
    elif param.default != inspect.Parameter.empty:
        if param.default is not None:
            res['default'] = param.default
        if isinstance(param.default, Enum):
            res["enum"] = [i.value for i in param.default.__class__._member_map_.values()]
            res['default'] = param.default.value
    return res


def match_return_annotation(anno):
    """🛰️ 超光速返回舱装配系统 | 将函数返回值封装成星际邮包

    自动识别返回值的量子态特征，为不同维度数据配备对应的曲速推进装置

    Args:
        anno (Type): 返回值的超弦编码类型信号

    Returns:
        dict: 装配完成的星际邮包，内置维度稳定器和多语言导航系统[1,3](@ref)
    """
    output = {}
    # 注解不为空
    if anno != inspect.Parameter.empty:
        # 有注解默认输出
        if get_origin(anno) is Annotated:
            output["output"] = match_param("output", anno)

        # 注解为字典
        if isinstance(anno, dict):
            for name, param in anno.items():
                output[name] = match_param(name, param)
        # 注解为正常类型
        elif isinstance(anno, type):
            # 注解为model
            if isinstance(anno, BaseModel.__class__):
                signature = get_cached_signature(anno)
                output = match_model(signature, "input")

            else:
                # 没注解默认输出
                output["output"] = {
                    "type": match_datatype(anno),
                    "title": Lang("输出", "output").convert(),  # 🌐 多语言宝石
                    "description": Lang("默认输出", "Default Output").convert()
                }
    return output


class Base(metaclass=abc.ABCMeta):
    """🚀 星舰核心基类 | 曲速引擎的元契约之书

    作为所有星舰子系统的量子纠缠基点，负责将普通代码改造成超维度存在

    Attributes:
        _func_name (str): 绑定操作员的灵魂代号（函数名称）
        model (Type[BaseModel]): 反物质参数约束场模型
        title (Optional[str]): 星舰子系统的全息投影名称
        description (Optional[str]): 超弦理论级别的系统描述
        input (dict): 超空间参数装配站
        output (dict): 曲速引擎输出端口
    """
    def __init__(self, title=None, description=None, model=None):
        # 💎 灵魂绑定数据区
        self._func_name = None  # 契约者真名

        # 🎀 外观属性
        self.model = model  # 参数守卫模型
        self.title = title  # 契约标题
        self.description = description  # 契约描述

        # 📦 输入输出装备库
        self.input = {}  # 参数装备展示架
        self.output = {}  # 返回值王冠陈列台

    def __call__(self, func):
        """🎇 量子态绑定仪式 | 将碳基代码升维成星舰组件

        通过四维空间包裹技术，为普通函数注入曲速引擎能量核心

        Args:
            func (Callable): 待改造的原始地球级函数

        Returns:
            Union[wrapper, async_wrapper]: 搭载了曲速引擎的星舰级函数

        Examples:
            >> @EngineCore
            ... def warp_drive(...):
            ...     # 此刻开始成为光年级存在！
        """
        self._func_name = func.__name__
        signature = inspect.signature(func)
        self.input = match_model(signature, direction="input")
        self.output = match_model(signature, direction="output")
        self.hook()

        # 🌈 同步/异步双重形态切换
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if self.model:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                bound_args.arguments.pop('self')
                self.model(**bound_args.arguments)
            return func(*args, **kwargs)

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            """🪐 超光速异步推进器 | 处理跨维度异步请求

            专为处理量子纠缠态异步调用设计的曲速引擎，内置时空锁防止维度撕裂

            Features:
                - ⏳ 时间晶体加速模块
                - 🌐 跨维度参数验证场
                - 🌀 异步能量流稳定器

            Warning:
                禁止在未启动量子护盾的情况下直接调用！
            """
            if self.model:
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                bound_args.arguments.pop('self')
                self.model(**bound_args.arguments)
            return await func(*args, **kwargs)

            # 🔄 形态选择器
        return async_wrapper if asyncio.iscoroutinefunction(func) else wrapper

    @abc.abstractmethod
    def hook(self):
        """🎇 曲速引擎定制接口 | 留给子类舰长的私人改造舱
        在此处接入：
        - 暗物质推进器 🚀
        - 量子护盾发生器 🛡️
        - 跨维度通讯阵列 📡

        Warning:
            请勿在此处修改主引擎参数，否则可能引发维度撕裂[5,6](@ref)
        """
        ...
