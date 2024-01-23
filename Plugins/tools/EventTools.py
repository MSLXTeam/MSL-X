from enum import Enum
from .InfoClasses import handlers, EventHandlerInfo


# todo
# 在这里实现关于插件注册的事件相关的代码


class EventHandler:

    def __init__(self, info: EventHandlerInfo):
        self.Event = getattr(info, "on", info)

    def __call__(self, func):
        if isinstance(self.Event, Enum):
            event = str(self.Event.value)
        else:
            event = self.Event
        handlers.get(event, []).insert(0, func)
