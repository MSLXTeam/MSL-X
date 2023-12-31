import json
import math
import os
import subprocess as sp

import psutil
import requests


class SingleServerInfo:
    def __init__ \
                    (
                    self,
                    use_java: str = "java",
                    xms: int = 1,
                    xmx: int = 4,
                    server_path: str = "",
                    server_file: str = "server.jar",
                    descr: str = "",
                    name: str = "",
                    server_options: list[str] = \
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
            ):
        self.server = None
        vsmem = psutil.virtual_memory()
        self.xmx = math.floor(vsmem.free / 1000000000 * 0.7)
        self.use_java = use_java  # 保存Java路径，为"JAVA"时使用环境变量(默认)
        self.xms = xms  # G省略
        self.xmx = xmx
        self.descr = descr
        self.name = name
        self.server_path = server_path
        self.server_file = server_file
        self.server_options = server_options
        self.server_option_str = ""
        for item in self.server_options:
            self.server_option_str += item

    def start(self):
        """
        Return 2:xms>xmx
        """
        if self.xms > self.xmx:
            return 2
        server_file_path: str = self.server_path + os.sep + self.server_file
        if ".jar" not in self.server_file:
            server_file_path += ".jar"
        server_options_str = ""
        for index in self.server_options:
            server_options_str += f"{index} "
        self.server = sp.Popen \
                (
                args=f"{self.use_java} -Xms{self.xms}G -Xmx{self.xmx}G {server_options_str} -jar {server_file_path}",
                cwd=self.server_path,
                text=True,
                stdin=sp.PIPE,
            )

    def convert_list2str(self):
        self.server_option_str = ""
        for i in self.server_options:
            self.server_option_str += i

    def convert_str2list(self):
        self.server_options = self.server_option_str.split(' ')


class ProgramInfo:
    def __init__(self, name: str = "Default"):
        self.name = name
        self.page = "主页"
        self.title = f"MSLX | {self.name} | {self.page}"
        self.update_hitokoto()
        self.running_server_list = []

    def update_hitokoto(self):
        hitokoto_html = requests.get(
            url="https://v1.hitokoto.cn/?c=i&encode=json&charset=utf-8")
        self.hitokoto = json.loads(hitokoto_html.text)
