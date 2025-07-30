import json
import yaml
import typing
from chariot_scaffold.schema.config_model import PluginSpecYamlModel


# Lang类的星光版
class Lang:
    def __init__(self, *texts: str, languages: list[str] = None):
        """🌈 多语言精灵的星光口袋"""
        self.languages = languages or ["zh-CN", "en"]
        self.texts = texts

        if not texts:
            raise ValueError("需要传入翻译文本哦～例：Lang('你好', 'Hello')")
        if len(self.languages) < len(self.texts):
            raise ValueError(f"需要 {len(self.texts)} 种语言配置，当前只有 {len(self.languages)} 种")

    def convert(self) -> dict[str, str]:
        """✨ 启动语言转换魔法阵"""
        return {
            lang: self.texts[i] if i < len(self.texts) else self.texts[-1]
            for i, lang in enumerate(self.languages)
        }


class LangFast:
    def __init__(self, content: list[list]):
        self.content = content
        self.parse()

    def parse(self):
        for i in self.content:
            param = i[0]
            title = i[1]
            desc = i[2]
            new_type = type(param, (), {"title": title, "desc": desc})
            setattr(self, param, new_type)

    # 魔法少女の修正咒语
    def __getattr__(self, item):
        """✨ 动态属性查找の星光通道"""
        if hasattr(self, item):
            return super().__getattribute__(item)
        return None  # 找不到就返回None，不会报错啦


class PluginSpecYaml(PluginSpecYamlModel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __str__(self):
        return self.model_dump()

    def deserializer(self, yml=None):
        if yml:
            stream = open(yml, 'r', encoding='utf8').read()
        else:
            stream = open('plugin.spec.yaml', 'r', encoding='utf8').read()
        plugin_spec = yaml.safe_load(stream)
        PluginSpecYamlModel(**plugin_spec)
        self.__init__(**plugin_spec)


class DataMapping:
    def __init__(self):
        self.__data_mapping = {
            "<class 'int'>": Datatypes.integer,
            "<class 'float'>": Datatypes.float_,
            "<class 'str'>": Datatypes.string,
            "<class 'list'>": Datatypes.array,
            "<class 'dict'>": Datatypes.object_,
            "<class 'bool'>": Datatypes.boolean,
            "<built-in function any>": Datatypes.any_,
            "list[str]": Datatypes.array_str,
            "list[dict]": Datatypes.array_obj,
            "dist[str]": Datatypes.object_,
            "dist[int]": Datatypes.object_,
            "dist[float]": Datatypes.object_,
            "dist[list]": Datatypes.object_,
            "list[int]": Datatypes.array_int,
        }

    def __getitem__(self, item):
        return self.__data_mapping.get(item, Datatypes.any_).__name__

    def __setitem__(self, key, value):
        self.__data_mapping[key] = value

    def __delitem__(self, key):
        self.__data_mapping.pop(key)

    def __repr__(self):
        return json.dumps(self.__data_mapping, ensure_ascii=False)


class Datatypes:
    object_ = typing.NewType("object", dict[any])
    array = typing.NewType("array", list[any])
    integer = typing.NewType("integer", int)
    float_ = typing.NewType("float", float)
    boolean = typing.NewType("boolean", bool)
    string = typing.NewType("string", str)
    any_ = typing.NewType("any", typing.Any)
    array_str = typing.NewType("[]string", list[str])
    array_obj = typing.NewType("[]object", list[dict])
    array_int = typing.NewType("[]integer", list[int])
    array_float = typing.NewType("[]float", list[int])
    array_bool = typing.NewType("[]boolean", list[int])
    text = typing.NewType("text", str)
    password = typing.NewType("password", str)
    date = typing.NewType("date", str)
    file = typing.NewType("file", dict)
    code = typing.NewType("code", str)
    python = typing.NewType("python", str)
    java = typing.NewType("java", str)
    bytes_ = typing.NewType("bytes", str)
