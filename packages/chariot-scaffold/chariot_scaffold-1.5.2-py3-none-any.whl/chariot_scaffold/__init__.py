from chariot_scaffold.journal import logger, logger_fmt
from chariot_scaffold.core.config import PluginSpecYaml, DataMapping
from typing import Annotated, Literal
import os


project_path = os.path.abspath("./")
log = logger(fmt=logger_fmt, save_path=os.path.join(project_path, "plugin.log"))
# lang = "zh-CN"    废弃， 使用Lang替代
version ="1.5.2"
plugin_spec = PluginSpecYaml()
data_mapping = DataMapping()

