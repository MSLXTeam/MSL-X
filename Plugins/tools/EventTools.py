from functools import wraps
from typing import Optional, Callable

from .Exceptions import WrongInfoTypeError
from .InfoClasses import handlers, UniversalInfo, InfoTypes


# todo
# 在这里实现关于插件注册的事件相关的代码


class EventHandler:

    def __init__(self, info: UniversalInfo):
        if info.type == "EventHandler" or info.type == InfoTypes.EventHandler:
            self.Event = info.on
        else:
            raise WrongInfoTypeError(info.name, info.type, "EventHandler")

    def __call__(self, func):
        if isinstance(self.Event, InfoTypes):
            event = str(self.Event.value)
        else:
            event = self.Event
        handlers.get(event, []).insert(0, func)


class CustomEvent:

    def __init__(self, info: UniversalInfo):
        if info.type == "EventHandler":
            self.Event = info.on
        else:
            raise WrongInfoTypeError(info.name, info.type, "EventHandler")
        self.HandlerList = []

    def AddHandler(self, name: str, func: Optional[Callable] = None):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.HandlerList.append(func)
            result = func(*args, **kwargs)
            return result

        return wrapper
