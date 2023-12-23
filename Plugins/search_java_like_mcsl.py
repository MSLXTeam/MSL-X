import json
import subprocess
import sys
from os import listdir
from os.path import isfile, join, exists
from platform import system
from re import search
from typing import List, Optional

from Plugins.tools.InfoClasses import MSLXEvents
from Plugins.tools.EventTools import EventHandler
from Plugins.tools.InfoClasses import UniversalInfo, InfoTypes
from Plugins.tools.PluginTools import AddPluginInfo

sys.path.append("..")
from lib.log import logger

plugin_info = UniversalInfo(type_of_info=InfoTypes.Plugin, name="search_java_like_mcsl", author="MojaveHao",
                            description="Allows use of MCSL-style Java detectors via this plugin", version="1.0.0",
                            need_page=False)

handler_info = UniversalInfo(type_of_info=InfoTypes.EventHandler, name="search_java_like_mcsl", author="MojaveHao",
                             description="Allows use of MCSL-style Java detectors via this plugin", version="1.0.0",
                             need_page=False, on=MSLXEvents.SearchJavaEvent)

# 定义关键词和排除关键词集合，便于快速查找
matchKeywords = {
    '1.', 'bin', 'cache', 'client', 'corretto', 'craft', 'data', 'download', 'eclipse',
    'env', 'ext', 'file', 'forge', 'fabric', 'game', 'hmcl', 'hotspot', 'java', 'jdk', 'jre',
    'zulu', 'dragonwell', 'jvm', 'launch', 'mc', 'microsoft', 'mod', 'mojang', 'net', 'netease',
    'optifine', 'oracle', 'path', 'program', 'roaming', 'run', 'runtime', 'server', 'software',
    'temp', 'users', 'users', 'x64', 'x86', 'lib', 'usr',
    '世界', '前置', '原版', '启动', '启动', '国服', '官启', '官方', '客户', '应用', '整合',
    '新建文件夹', '服务', '游戏', '环境', '程序', '网易', '软件', '运行', '高清'
}
excludedKeywords = {
    "$", "{", "}", "__"
}


# 使用类型注解和属性定义Java类
class Java:
    def __init__(self, path: str, ver: str):
        self._path = path
        self._version = ver

    @property
    def path(self) -> str:
        return self._path

    @property
    def version(self) -> str:
        return self._version

    @property
    def json(self) -> dict:
        return {"Path": self.path, "Version": self.version}

    def __hash__(self) -> int:
        return hash((self._path, self._version))

    def __str__(self) -> str:
        return json.dumps(self.json)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, Java):
            return self._path == other._path and self._version == other._version


# 定义获取Java版本的函数
def get_java_version(file: str) -> str:
    try:
        output = subprocess.check_output([file, "-version"], stderr=subprocess.STDOUT, timeout=3)
        version_pattern = r"(\d+)(?:\.(\d+))?(?:\.(\d+))?(?:[._](\d+))?(?:-(.+))?"
        version_match = search(version_pattern, output.decode('utf-8'))
        if version_match:
            return ".".join(filter(None, version_match.groups()))
    except subprocess.CalledProcessError as e:
        logger.warning(f"获取Java版本失败: {e}")
    except subprocess.TimeoutExpired:
        logger.warning("检测版本超时,已跳过")
    return ""


# 定义搜索文件的函数
def search_file(path: str, keyword: str, ext: str, f_search: bool, match_func: callable) -> List[Java]:
    found_java = []
    if f_search:
        if isfile(path) or "x86_64-linux-gnu" in path:
            return found_java
        try:
            for file in listdir(path):
                full_path = join(path, file)
                if isfile(full_path):
                    if match_func(path, file):
                        logger.info(f"已匹配到:{full_path}")
                        version = get_java_version(full_path)
                        if version:
                            found_java.append(Java(full_path, version))
                elif find_str(file.lower()):
                    found_java.extend(search_file(full_path, keyword, ext, f_search, match_func))
        except PermissionError:
            pass
        except FileNotFoundError:
            pass
    return found_java


# 定义字符串查找函数
def find_str(s: str) -> bool:
    for excluded in excludedKeywords:
        if excluded in s:
            return False
    for match in matchKeywords:
        if match in s:
            return True
    return False


# 定义检查Java可用性的函数
def check_java_availability(java: Java) -> bool:
    if exists(java.path):
        try:
            version = get_java_version(java.path)
            return version == java.version
        except subprocess.CalledProcessError:
            pass
    return False


# 定义对Java列表进行排序的函数
def sort_java_list(list_: List[Java], reverse: bool = False) -> None:
    list_.sort(key=lambda x: x.version, reverse=reverse)


# 定义返回排序后的Java列表的函数
def sorted_java_list(list_: List[Java], reverse: bool = False) -> List[Java]:
    return sorted(list_, key=lambda x: x.version, reverse=reverse)


# 定义合并两个Java列表的函数
def combine_java_list(original: List[Java], list_: List[Java], invalid: Optional[List[Java]], check: bool = True) -> \
        List[Java]:
    s1 = set(original)
    s2 = set(list_)
    s = s1.union(s2)
    if check:
        for e in s1 - s2:
            if not check_java_availability(e):
                s.remove(e)
                logger.warning(f"{e}已失效")
                if isinstance(invalid, list):
                    invalid.append(e)
    return list(s)


@AddPluginInfo(plugin_info)
def print_loaded():
    logger.debug("已加载MCSL风格的Java搜索器")


@EventHandler(handler_info)  # 注册为EventHandler
def detect_java(f_search: bool = True):  # 定义检测Java的函数
    java_path_list = []
    if "windows" in system().lower():
        for i in range(65, 91):
            path = chr(i) + ":\\"
            if exists(path):
                java_path_list.extend(search_file(path, "java", "exe", f_search, lambda p, f: f.endswith('java.exe')))
    else:
        java_path_list.extend(search_file("/usr/lib", "java", "", f_search, lambda p, f: f.endswith('java')))
    java_list = {}
    for obj in java_path_list:
        java_list[f'{obj.version}({obj.path})'] = {"path": obj.path, "ver": obj.version}
    logger.info("Java检测完成")
    return java_list
