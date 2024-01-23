import inspect
from typing import Optional

from lib.log import logger
from .Exceptions import NullEntrypointError
from .InfoClasses import PluginInfo
from .PluginList import Pluginlist


class AddPluginInfo:
    def __init__(self, plugin_info: PluginInfo):
        self.plugin_info = plugin_info

    def __call__(self, func: Optional[callable]):
        self.plugin_info.on_load = func
        self.plugin_info.file = inspect.stack()[1].filename if inspect.stack()[1].frame else ""
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
