from typing import Optional

from lib.log import logger
from .Exceptions import WrongInfoTypeError, NullEntrypointError
from .InfoClasses import UniversalInfo, InfoTypes
from .PluginList import Pluginlist


class AddPluginInfo:
    def __init__(self, plugin_info: UniversalInfo):
        if plugin_info.type == "Plugin" or plugin_info.type == InfoTypes.Plugin:
            self.plugin_info = plugin_info
        else:
            raise WrongInfoTypeError(plugin_info.name, plugin_info.type, "Plugin")

    def __call__(self, func: Optional[callable]):
        self.plugin_info.on_load = func
        Pluginlist.append(self.plugin_info)
        name = self.plugin_info.name
        location = self.plugin_info.on
        logger.info(f"已在{location}注册插件{name}")

    @property
    def check_entrypoint(self):
        if self.plugin_info.on_load is not None:
            return self.plugin_info.on_load
        else:
            raise NullEntrypointError
