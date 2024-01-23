import importlib
import os
import threading
import typing
from typing import Dict, Any

import lib.pubvars
from Plugins.tools.PluginList import Pluginlist
from lib.log import logger

global_var_lock = threading.Lock()

all_events = {}


def process_event(event_key: str, event_value: Any, file_name: str, all_events: Dict[str, Dict[str, Any]]) -> None:
    """
    处理单个事件，将函数或类存储在全局字典中。

    Args:
        event_key (str): 事件的键。
        event_value (Any): 事件的值，可以是函数信息或字典信息。
        file_name (str): 插件的文件名。
        all_events (Dict[str, Dict[str, Any]]): 存储所有事件信息的全局字典。
    """

    def update_event_dict(event_key: str, module_name: str, event_object: Any):
        """更新全局事件字典"""
        if event_key not in all_events:
            all_events[event_key] = {}
        all_events[event_key][module_name] = event_object

    try:
        m = importlib.import_module("Plugins." + file_name)
        if event_value[0] == "func":
            event_func = getattr(m, event_value[1])
            if event_func:
                update_event_dict(event_key, "Plugins." + file_name, event_func)
        elif isinstance(event_value, dict) and all(k in event_value for k in ["mode", "type", "value"]):
            if event_value["type"] == "class":
                target_class = getattr(m, event_value["value"])
                if target_class:
                    update_event_dict(event_key, "Plugins." + file_name, event_value['value'])
    except ImportError as e:
        logger.error(f"无法导入模块: {e}")
    except AttributeError as e:
        logger.error(f"无法获取模块属性: {e}")


def process_plugin_args(need_args, kwargs):
    """
    处理插件需要获取的程序变量和函数。

    Args:
        need_args (Dict): 插件定义的需要的参数。
        kwargs (Dict): 包含全局变量和函数的字典。

    Returns:
        Tuple[Dict, Dict]: 包含需要的变量和函数的字典。
    """
    call_vars = {}
    if need_args is not None:
        need_vars = need_args.get('need_vars', [])
        for var_name in need_vars:
            if var_name in kwargs["global_vars"]:
                call_vars[var_name] = kwargs["global_vars"][var_name]

    return call_vars


def process_thread_class(thread_class, target_func, page, need_vars):
    """
    处理使用线程类的情况。

    Args:
        thread_class (Thread): 插件定义的线程类。
        target_func (Callable): 目标函数。
        page (Page): 插件的页面对象。
        need_vars (Dict): 需要的变量。
    """

    if not need_vars:
        if not page:
            thread_class.run(target=target_func)
        else:
            thread_class.run(target=target_func, page=page)
    else:
        if not page:
            thread_class.run(target=target_func, need_vars=need_vars)
        else:
            thread_class.run(target=target_func, need_vars=need_vars, page=page)


# def initialize_plugin(name, page, load_time, **kwargs):
def initialize_plugin(name, page, **kwargs):
    """
    初始化插件并执行相应操作。

    Args:
        name (str): 插件的名称。
        page (Page): 插件的页面对象。
        kwargs (Dict): 包含全局变量和函数的字典。
    """

    # 遍历所有可能的插件文件来使装饰器生效
    for root, _, files in os.walk("Plugins"):
        if root != "Plugins":
            break
        for file in files:
            if file.endswith(".py"):
                importlib.import_module('.' + file.split(".")[0], package="Plugins")

    # 针对单个插件信息的处理
    for plugin in Pluginlist:
        if plugin.on == name:

            load_info = f"加载插件:{plugin.name}"
            logger.info(f"{load_info:=^50}")
            logger.info(f"插件描述:{plugin.description}")
            logger.info(f"插件版本:{plugin.version}")
            logger.info(f"插件作者:{plugin.author}")
            logger.info(f"入口点文件:{plugin.file}")

            use_thread_class = False
            if isinstance(plugin.on_load, typing.Callable):
                target_func = plugin.on_load
            else:
                m = importlib.import_module('Plugins.' + os.path.basename(plugin.file).split('.')[0])
                target_func = getattr(m, plugin.on_load, None)
            target_thread_class = plugin.thread_class

            # 处理插件需要获取的程序变量和函数
            need_args = result if (result := getattr(plugin, "args")) is not None else {}
            call_vars = process_plugin_args(need_args, kwargs)
            # for event_key in ["on_load", "on_unload", "on_enable", "on_disable"]:
            #     process_event(event_key, getattr(plugin, event_key), os.path.basename(plugin.file).split('.')[0],
            #                   all_events)
            need_page = plugin.need_page
            if plugin.multi_thread:
                if hasattr(target_thread_class, "run"):
                    target_thread_class = target_thread_class
                    use_thread_class = True
                else:
                    logger.error(f"指定的对象{target_thread_class.name}({target_thread_class})没有run方法")

                    # 处理完成,准备调用
            if use_thread_class is False:
                logger.debug("没有使用thread类,将直接调用函数")
                if not need_page:
                    target_func(**call_vars)
                else:
                    target_func(page, **call_vars)
            elif use_thread_class and target_thread_class is not None:
                logger.debug("检测到使用了thread类")
                process_thread_class(target_thread_class, target_func, page, call_vars)

            logger.info(f"{load_info:=^50}")

    lib.pubvars.PubVars.plugin_list = Pluginlist
