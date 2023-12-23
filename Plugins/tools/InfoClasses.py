import inspect
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
    MSLXEvents.SearchJavaEvent.value: []
}


class UniversalInfo:  # 通用信息类
    def __init__(self, type_of_info: Union[str, InfoTypes], name: str = "Anonymous", author: str = "Anonymous",
                 description: str = "",
                 on: Union[str, MSLXEvents] = "main",
                 version: str = "1.0.0", need_page: Optional[bool] = False, args: Optional[dict] = {},
                 multi_thread: Optional[bool] = False, thread_class: Optional[Thread] = None,
                 file: Optional[str] = inspect.currentframe().f_back.f_code.co_filename,
                 events: Optional[dict] = {}):
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
        if isinstance(type_of_info, MSLXEvents):
            self.type = type_of_info.value
        else:
            self.type = type_of_info
        if self.type == "Plugin":
            self.events = events
            self.on_load = None
            self.on_enable = None
            self.on_disable = None
            if "need_vars" in args.keys():
                self.need_args = args["need_args"]
            if "on_load" in events.keys():
                self.on_load = events["on_load"]
            if "on_unload" in events.keys():
                self.on_unload = events["on_unload"]
            if "on_enable" in events.keys():
                self.on_enable = events["on_enable"]
            if "on_disable" in events.keys():
                self.on_disable = events["on_disable"]
