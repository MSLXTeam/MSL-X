import gc
import importlib
import threading
from typing import Callable, Dict, Any

import lib.pubvars
from Plugins import *  # type: ignore
from Plugins.tools.PluginList import Pluginlist
from lib.log import logger

global_var_lock = threading.Lock()

# 定义运行中保存的字典
on_load_func_dict: Dict[str, Callable] = {}
on_enable_func_dict: Dict[str, Callable] = {}
on_disable_func_dict: Dict[str, Callable] = {}
on_load_classes_dict: Dict[str, Any] = {}
on_enable_classes_dict: Dict[str, Any] = {}
on_disable_classes_dict: Dict[str, Any] = {}


def process_event(event_key: str, event_value: Any, file_name: str, event_dict: Dict[str, Any]) -> None:
    """
    处理单个事件，将函数或类存储在全局字典中。

    Args:
        event_key (str): 事件的键。
        event_value (Any): 事件的值，可以是函数信息或字典信息。
        file_name (str): 插件的文件名。
        event_dict (Dict[str, Any]): 存储事件信息的全局字典。
    """
    m = importlib.import_module("Plugins." + file_name)

    if event_value[0] == "func":
        # 如果事件值是函数信息，获取函数对象并存储在全局字典中
        event_func = getattr(m, event_value[1])
        if event_func is not None:
            event_dict["Plugins." + file_name] = event_func
            if event_key == "on_load":
                global on_load_func_dict
                on_load_func_dict = {**on_load_func_dict, **event_dict}
            elif event_key == "on_enable":
                global on_enable_func_dict
                on_enable_func_dict = {**on_enable_func_dict, **event_dict}
            elif event_key == "on_disable":
                global on_disable_func_dict
                on_disable_func_dict = {**on_disable_func_dict, **event_dict}

    elif isinstance(event_value, dict):
        # 如果事件值是字典信息，检查是否包含必要的键
        dict_keys = event_value.keys()
        if "mode" in dict_keys and "type" in dict_keys and "value" in dict_keys:
            match event_value["type"]:
                case "class":
                    # 如果是合法的字典信息，获取类对象并存储在全局字典中
                    target_class = getattr(m, event_value["value"])
                    if target_class is not None:
                        event_dict["Plugins." + file_name] = event_value['value']
                        if event_key == "on_load":
                            global on_load_classes_dict
                            on_load_classes_dict = {**on_load_classes_dict, **event_dict}
                        elif event_key == "on_enable":
                            global on_enable_classes_dict
                            on_enable_classes_dict = {**on_enable_classes_dict, **event_dict}
                        elif event_key == "on_disable":
                            global on_disable_classes_dict
                            on_disable_classes_dict = {**on_disable_classes_dict, **event_dict}


def process_plugin_events(events: Dict[str, Any], file_name: str) -> None:
    """
    处理插件的事件部分，将需要执行的函数或类存储在全局字典中。

    Args:
        events (Dict[str, Any]): 插件定义的事件。
        file_name (str): 插件的文件名。
    """

    for event_key, event_value in events.items():
        if event_key == "on_load":
            # 处理 on_load 事件并存储到对应的全局字典中
            process_event(event_key, event_value, file_name, on_load_func_dict)
        elif event_key == "on_enable":
            # 处理 on_enable 事件并存储到对应的全局字典中
            process_event(event_key, event_value, file_name, on_enable_func_dict)
        elif event_key == "on_disable":
            # 处理 on_disable 事件并存储到对应的全局字典中
            process_event(event_key, event_value, file_name, on_disable_func_dict)


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
    call_funcs = {}
    need_vars = need_args.get('need_vars', [])
    need_funcs = need_args.get('need_funcs', [])

    for var_name in need_vars:
        if var_name in kwargs["global_vars"]:
            call_vars[var_name] = kwargs["global_vars"][var_name]

    for func_name in need_funcs:
        if func_name in kwargs["funcs"]:
            call_funcs[func_name] = kwargs["funcs"][func_name]

    return call_vars, call_funcs


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

    # 针对单个插件信息的处理
    for plugin in Pluginlist:
        # if plugin["Loadtime"] == load_time and plugin["Location"] == name:
        if plugin["Location"] == name:

            load_info = f"正在加载{plugin['Name']}"
            logger.info(f"{load_info:=^30}")
            logger.info(f"插件信息:")
            logger.info(f"插件版本:{plugin['version']}")
            logger.info(f"插件作者:{plugin['author']}")
            logger.info(f"入口点文件:{plugin['file']}")

            use_thread_class = False
            target_func = plugin["EntryPoint"]
            target_thread_class = None
            # need_funcs = []
            need_page = False

            # 处理插件需要获取的程序变量和函数
            need_args = plugin.get("args", {})
            call_vars, call_funcs = process_plugin_args(need_args, kwargs)

            for key, value in plugin.items():
                if key == "events":
                    process_plugin_events(value, plugin["File"])
                elif key == "unsafe":
                    unsafe = value
                elif key == "need_page":
                    need_page = value
                elif key == "multi_thread":
                    if "thread_class" in plugin and plugin["thread_class"]:
                        m = importlib.import_module("Plugins." + plugin["File"])
                        if hasattr(m, plugin["thread_class"]):
                            thread_class = getattr(m, plugin["thread_class"])
                            if hasattr(thread_class, "run"):
                                target_thread_class = thread_class
                                use_thread_class = True
                            else:
                                logger.critical("指定的对象没有run方法", 2)
                    else:
                        logger.critical("指定的对象不存在", 2)
                    gc.collect()

            # 处理完成,准备调用
            if use_thread_class is False:
                logger.debug("没有使用thread类,将直接调用函数")
                '''
                if not need_funcs:
                    if not need_page:
                        target_func(**call_vars)
                    else:
                        target_func(page, **call_vars)
                else:
                '''
                if not need_page:
                    target_func(**call_vars)
                else:
                    target_func(page, **call_vars)
            else:
                logger.debug("检测到使用了thread类")
                process_thread_class(target_thread_class, target_func, page, call_vars)

    lib.pubvars.PubVars.plugin_list = Pluginlist

'''
def before_run(name, page, **kwargs):
    """
    在插件初始化之前调用总入口点。

    Args:
        name (str): 插件的名称。
        page (Page): 插件的页面对象。
        kwargs (Dict): 包含全局变量和函数的字典。
    """
    initialize_plugin(name, page, 'before', **kwargs)


def after_run(name, page, **kwargs):
    """
    在插件初始化之后调用总入口点。

    Args:
        name (str): 插件的名称。
        page (Page): 插件的页面对象。
        kwargs (Dict): 包含全局变量和函数的字典。
    """
    initialize_plugin(name, page, 'after', **kwargs)

'''


def enable_plugin(name):
    """
    启用插件时调用的函数。

    Args:
        name (str): 插件的名称。
    """
    if name in on_enable_func_dict:
        on_enable_func_dict[name]()
    elif name in on_enable_classes_dict:
        pass
    else:
        logger.error(f"没有找到{name}的开启时方法")


def disable_plugin(name):
    """
    禁用插件时调用的函数。

    Args:
        name (str): 插件的名称。
    """
    if name in on_disable_func_dict:
        on_disable_func_dict[name]()
    elif name in on_disable_classes_dict:
        pass
    else:
        logger.error(f"没有找到{name}的禁用时方法")
