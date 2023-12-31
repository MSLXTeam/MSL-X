import json
from os import sep
from typing import Any

import pytoml

from .info_classes import SingleServerInfo
from .log import logger


class ConfCtl:

    def __init__(self, name: str = "Default", full_path=""):
        self.name = name
        self.xms = 1
        self.xmx = 4
        self.java = "java"
        self.server = "server"
        self.server_path = ""
        self.description = ""
        self.name = "Default"
        self.process_options = \
            [
                "-XX:+UnlockExperimentalVMOptions",
                "-XX:MaxGCPauseMillis=100",
                "-XX:+DisableExplicitGC",
                "-XX:TargetSurvivorRatio=90",
                "-XX:G1NewSizePercent=50",
                "-XX:G1MaxNewSizePercent=80",
                "-XX:G1MixedGCLiveThresholdPercent=35",
                "-XX:+AlwaysPreTouch",
                "-XX:+ParallelRefProcEnabled",
                "-Dusing.aikars.flags=mcflags.emc.gs"
            ]
        self.options_str = ""
        if full_path == "":
            self.path = f'Config{sep}{name}.json'
        else:
            self.path = full_path

    @logger.catch
    def load_config(self):
        with open(self.path, 'r', encoding='utf-8') as fl:
            conf_dict = json.load(fl)
            try:
                self.xms = conf_dict["xms"]
                self.xmx = conf_dict["xmx"]
                self.java = conf_dict["java"]
                self.server = conf_dict["server"]
                self.server_path = conf_dict["path"]
                self.description = conf_dict["description"]
                self.process_options = conf_dict["jvm_options"]
                self.name = conf_dict["name"]
            except KeyError:
                self.save_config()
                logger.warning("检测到配置文件损坏,已写入默认设置")

    @logger.catch
    def save_config(self):
        with open(self.path, 'w', encoding='utf-8') as fl:
            conf_dict: Any = \
                {
                    "xms": self.xms,
                    "xmx": self.xmx,
                    "java": self.java,
                    "server": self.server,
                    "path": self.server_path,
                    "description": self.description,
                    "jvm_options": self.process_options,
                    "name": self.name
                }
            json.dump(conf_dict, fl)


def load_info_to_server(name: str = "Default", full_path=""):
    cfctl = ConfCtl(name=name, full_path=full_path)
    cfctl.load_config()
    server = SingleServerInfo(executor=cfctl.java, xms=cfctl.xms, xmx=cfctl.xmx, server_path=cfctl.server_path,
                              server_file=cfctl.server, descr=cfctl.description, name=cfctl.name,
                              server_options=cfctl.process_options)
    return server


def save_server_to_conf(class_server: SingleServerInfo, name: str = "Default", full_path: str = ""):
    cfctl = ConfCtl(name=name, full_path=full_path)
    cfctl.xms = class_server.xms
    cfctl.xmx = class_server.xmx
    cfctl.java = class_server.executor
    cfctl.process_options = class_server.server_options
    cfctl.server = class_server.server_file
    cfctl.server_path = class_server.server_path
    cfctl.description = class_server.descr
    cfctl.name = class_server.name
    cfctl.save_config()


def read_software_settings():
    with open("../Config/mslx.toml", encoding="utf-8", mode="rb") as f:
        data = pytoml.load(f)
        style = data.get("style")
