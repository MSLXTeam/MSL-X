import typing
from enum import Enum
from threading import Thread
from typing import Optional, Union


class MSLXEvents(Enum):  # 事件类型枚举
    # 切换页面的事件
    SelectHomepageEvent = "SelectHomepageEvent"
    SelectFrpcPageEvent = "SelectFrpcPageEvent"
    SelectAboutPageEvent = "SelectAboutPageEvent"

    # 一些函数的事件
    StartServerEvent = "StartServerEvent"
    CloseWindowEvent = "CloseWindowEvent"
    SearchJavaEvent = "SearchJavaEvent"

    # 其他事件
    KeyboardShortcutEvent = "KeyboardShortcutEvent"
    UnexpectedServerStoppedEvent = "UnexpectedServerStoppedEvent"


class InfoTypes(Enum):  # 信息类型枚举
    Plugin = "Plugin"
    EventHandler = "EventHandler"
    Event = "Event"
    Command = "Command"


handlers = {
    MSLXEvents.StartServerEvent.value: [],
    MSLXEvents.SelectHomepageEvent.value: [],
    MSLXEvents.SelectFrpcPageEvent.value: [],
    MSLXEvents.SelectAboutPageEvent.value: [],
    MSLXEvents.SearchJavaEvent.value: [],
    MSLXEvents.KeyboardShortcutEvent.value: [],
    MSLXEvents.UnexpectedServerStoppedEvent.value: [],
}


class UniversalInfo:  # 通用信息类
    def __init__(self, type_of_info: Union[str, InfoTypes], name: str = "Anonymous", author: str = "Anonymous",
                 description: str = "",
                 on: Union[str, MSLXEvents] = "main",
                 version: str = "1.0.0", need_page: Optional[bool] = False, args: Optional[dict] = None):
        self.type = ""
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.need_page = need_page
        self.args = args
        self.on = on
        self.need_args = []
        if isinstance(type_of_info, MSLXEvents):
            self.type = type_of_info.value
        else:
            self.type = type_of_info


class PluginInfo(UniversalInfo):  # 插件信息类,继承自通用信息类
    def __init__(self, name: str = "Anonymous", author: str = "Anonymous",
                 description: str = "", on: Union[str, MSLXEvents] = "main", version: str = "1.0.0",
                 need_page: Optional[bool] = False, args: Optional[dict] = None, multi_thread: Optional[bool] = False,
                 thread_class: Optional[Thread] = None,
                 file: Optional[str] = "",
                 on_enable: Union[str, typing.Callable] = "", on_disable: Union[str, typing.Callable] = "",
                 on_load: Union[str, typing.Callable] = "", on_unload: Union[str, typing.Callable] = ""):
        super().__init__(InfoTypes.Plugin, name, author, description, on, version, need_page, args)
        self.type = ""
        self.name = name
        self.author = author
        self.description = description
        self.version = version
        self.need_page = need_page
        self.args = args
        self.multi_thread = multi_thread
        self.thread_class = thread_class
        self.on = on
        self.file = file
        self.need_args = []
        self.on_load = on_load
        self.on_unload = on_unload
        self.on_enable = on_enable
        self.on_disable = on_disable
        if args is not None and "need_vars" in args.keys():
            self.need_args = args["need_args"]


class EventHandlerInfo(UniversalInfo):
    def __init__(self, name: str = "Anonymous", author: str = "Anonymous",
                 on: Union[str, MSLXEvents] = "main",
                 need_page: Optional[bool] = False, args: Optional[dict] = None):
        super().__init__(InfoTypes.EventHandler.value, name, author, "EventHandler", on,
                         "Unavailable", need_page, args)
        self.type = ""
        self.name = name
        self.author = author
        self.need_page = need_page
        self.args = args
        self.on = on
        self.need_args = []