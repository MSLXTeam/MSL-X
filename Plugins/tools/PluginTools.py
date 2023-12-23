from typing import Optional

from lib.log import logger
from .Exceptions import WrongInfoTypeError, NullEntrypointError
from .InfoClasses import UniversalInfo, InfoTypes
from .PluginList import Pluginlist


class AddPluginInfo:  # 接受通用信息类的新版修饰器
    def __init__(self, plugin_info: UniversalInfo):
        if plugin_info.type == "Plugin" or plugin_info.type == InfoTypes.Plugin:
            self.plugin_info = plugin_info
        else:
            raise WrongInfoTypeError(plugin_info.name, plugin_info.type, "Plugin")

    def __call__(self, func: Optional[callable]):
        target = {
            "Name": self.plugin_info.name,
            "Location": self.plugin_info.on,
            "EntryPoint": func if func is not None else self.check_entrypoint,
            'version': self.plugin_info.version,
            'author': self.plugin_info.author,
            'need_page': self.plugin_info.need_page,
            'file': self.plugin_info.file,
            'class': self.plugin_info
        }
        if self.plugin_info.args is not None:
            target["args"] = self.plugin_info.args
        Pluginlist.append(target)
        name = self.plugin_info.name
        location = self.plugin_info.on
        logger.info(f"已在{location}注册插件{name}")

    @property
    def check_entrypoint(self):
        if self.plugin_info.on_load is not None:
            return self.plugin_info.on_load
        else:
            raise NullEntrypointError


class RegisterPlugin(object):  # 接受字典的老版本修饰器
    def __init__(self, plugin_info: dict):
        process_location = plugin_info["location"]
        logger.debug(f"装饰器被init了一次:{process_location},{plugin_info}")
        self.process_location = process_location
        self.plugin_info = plugin_info

    def __call__(self, func):
        logger.debug(f"装饰器被{func}Call了一次")
        target = {
            "Name": self.plugin_info["name"],
            "Location": self.plugin_info["location"],
            "EntryPoint": func,
            'need_page': self.plugin_info["need_page"],
            'file': self.plugin_info['file'],
        }
        if args := self.plugin_info.get('args') is not None:
            target["args"] = self.plugin_info['args']
        Pluginlist.append(target)
        name = target["Name"]
        location = target["Location"]
        logger.info(f"已注册插件{name},位置为{location}")
