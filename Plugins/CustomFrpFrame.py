from typing import TYPE_CHECKING

from flet import (
    dropdown,
    Dropdown,
    Container
)
from loguru import logger

# from Plugins.tools.PluginList import MSLXEvents, EventHandler, PluginInfo, AddPluginInfo
from Plugins.tools.InfoClasses import UniversalInfo, InfoTypes, MSLXEvents
from Plugins.tools.PluginTools import AddPluginInfo
from Plugins.tools.EventTools import EventHandler

if TYPE_CHECKING:
    from flet import Page

title = ""
add_name = ""
custom_page = None


@AddPluginInfo(UniversalInfo(type_of_info=InfoTypes.Plugin, name="CustomFrp", author="MojaveHao",
                             description="自定义Frp的前置框架", version="0.0.1",
                             need_page=True))
def pluginload(page: 'Page'):
    logger.debug("CustomFrpFrame已加载")
    global custom_page
    custom_page = page


@EventHandler(UniversalInfo(type_of_info=InfoTypes.EventHandler, name="CustomFrp", author="MojaveHao",
                            description="自定义Frp的前置框架", version="0.0.1", on=MSLXEvents.SelectFrpcPageEvent,
                            need_page=True))
def customFrpcPage():
    logger.debug("customFrpcPage已被调用")
    global custom_page
    frpc_type = None
    main_container = None

    def init_page():
        # raise NotImplementedError
        global title
        title = "自定义Frpc[Plugin:CustomFrpFrame]"

    def create_controls():
        # raise NotImplementedError
        nonlocal frpc_type
        nonlocal main_container
        frpc_type = Dropdown(
            label="Frp服务提供商选择",
            width=150,
            options= \
                [
                    dropdown.Option("自定义"),
                ],
            on_change=change_frpc
        )
        main_container = Container(
            content=frpc_type,
            border_radius=10,
            height=200
        )
        custom_page.add(main_container)
        custom_page.update()

    def change_frpc(e):
        # raise NotImplementedError
        if frpc_type is None:
            raise
        selected_content = frpc_type

    def add_frpc_option():
        # raise NotImplementedError
        nonlocal frpc_type
        global add_name
        if frpc_type is None:
            raise
        frpc_type.options.append(dropdown.Option(add_name))
        add_name = ""
        custom_page.update()

    init_page()
    create_controls()
    custom_page.update()
