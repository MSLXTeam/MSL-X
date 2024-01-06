import json
import math
import os
import subprocess as sp
import psutil
import requests


class SingleServerInfo:
    def __init__(
            self,
            type_is_java: bool = True,
            executor: str = "java",
            xms: int = 1,
            xmx: int = 4,
            server_path: str = "",
            server_file: str = "server.jar",
            descr: str = "",
            name: str = "",
            server_options: list[str] = (
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
            ),
            config_name="Default.json"
    ):
        self.server = None
        self.xmx = math.floor(psutil.virtual_memory().free / 1000000000 * 0.7)
        self.type_is_java = type_is_java
        self.executor = executor
        self.xms = xms  # G省略
        self.xmx = xmx
        self.descr = descr
        self.name = name
        self.server_path = server_path
        self.server_file = server_file
        self.server_options = server_options
        self.server_option_str = ""
        self.config_name = config_name

    def start(self):
        """
        Return 2:xms>xmx
        """
        if self.xms > self.xmx:
            return 2
        server_file_path: str = self.server_path + os.sep + self.server_file
        if ".jar" not in self.server_file and self.type_is_java:
            server_file_path += ".jar"
        args = ([self.executor, f'-Xms{self.xms}G', f'-Xmx{self.xmx}G'] + self.server_options +
                ['-jar' if self.type_is_java else '', f"{server_file_path}"])
        print(args)
        self.server = sp.Popen(
            args=args,
            cwd=self.server_path,
            text=True,
            stdin=sp.PIPE,
            stdout=sp.PIPE,
            stderr=sp.PIPE
        )

    def convert_list2str(self):
        self.server_option_str = ' '.join(self.server_options)

    def convert_str2list(self):
        self.server_options = self.server_option_str.split(' ')


class ProgramInfo:
    def __init__(self, name: str = "Default"):
        self.name = name
        self.page = "主页"
        self.hitokoto = ""
        self.title = f"MSLX | {self.name} | {self.page}"
        self.update_hitokoto()
        self.running_server_list = []

    def update_hitokoto(self):
        hitokoto_html = requests.get(
            url="https://v1.hitokoto.cn/?c=i&c=d&c=k&encode=json&charset=utf-8")
        self.hitokoto = json.loads(hitokoto_html.text)
