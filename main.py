import copy
import math
import os
import subprocess as sp
import sys
import time
import webbrowser as wb
from typing import TYPE_CHECKING

import pytomlpp
from flet import (
    app,
    Row,
    Text,
    Theme,
    Column,
    Switch,
    Divider,
    Dropdown,
    Markdown,
    Container,
    TextField,
    TextButton,
    FilePicker,
    RangeSlider,
    ThemeMode,
    Segment,
    dropdown,
    AlertDialog,
    ElevatedButton,
    SegmentedButton,
    ScrollMode,
    MainAxisAlignment,
    KeyboardEvent,
    NavigationDrawer,
    NavigationDrawerDestination,
    FilePickerResultEvent,
)

import PluginEntry
import default_info
from Plugins.tools.EventTools import EventHandler
from Plugins.tools.InfoClasses import handlers, MSLXEvents
from Plugins.tools.PluginList import Pluginlist
from lib.pubvars import PubVars
from lib.confctl import (
    ConfCtl,
    load_info_to_server,
    save_server_to_conf
)
from lib.info_classes import ProgramInfo
from lib.log import logger
from ui import (
    frpconfig,
)
from ui.Navbar import nav_side as navbar, btn as btn_select_config

if TYPE_CHECKING:
    from flet import Page


@logger.catch
def main(page: 'Page'):
    create_dirs = ["Config", "Logs", "Crypt"]
    for dir_name in create_dirs:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)
    if not os.path.exists("Config/Default.json"):  # 如果默认配置不存在就保存默认配置
        conf = ConfCtl("Default")
        conf.save_config()
        logger.info("已保存默认配置")
    PubVars.available_config_list = []
    for _, _, files in os.walk("Config"):
        for file in files:
            if file.endswith(".json"):
                PubVars.available_config_list.append(file)
    logger.info(f"可用的配置文件列表:{','.join(PubVars.available_config_list)}")
    current_server = load_info_to_server()
    current_server.convert_list2str()
    programinfo = ProgramInfo()
    PubVars.hitokoto = programinfo.hitokoto
    PubVars.text = PubVars.hitokoto.get("hitokoto", ["", "获取失败"])[:-1]
    drawer = NavigationDrawer(controls=[Container(height=13)])

    def init_page():

        nonlocal current_server, programinfo
        page.window_height = 600
        page.window_width = 1050
        page.fonts = dict(HMOSSans="fonts/HarmonyOS_Sans_SC_Regular.ttf", SHS_SC="fonts/SourceHanSansSC-Regular.otf")
        theme_dark = Theme(font_family="HMOSSans", color_scheme_seed="#1f1e33")
        theme_day = Theme(font_family="HMOSSans")
        page.theme = theme_day
        page.dark_theme = theme_dark
        page.on_keyboard_event = on_keyboard
        page.scroll = ScrollMode.AUTO
        page.drawer = drawer
        programinfo.update_hitokoto()
        if programinfo.title != "":
            page.title = programinfo.title
        if os.path.exists("Config/mslx.toml"):
            with open("Config/mslx.toml", encoding="utf-8") as _f:
                _data = pytomlpp.load(_f)
                style = _data.get("style", {})
                process_theme_config(style)
        else:
            pytomlpp.dump({}, "Config/mslx.toml")
        page.update()

    @EventHandler(default_info.start_server_event)
    def start_server(_e):
        nonlocal programinfo, current_server
        assert PubVars.txt_server_name.value is not None
        assert current_server is not None
        programinfo.name = current_server.name
        page.update()
        if PubVars.txt_server_name.value != "":
            current_server.server_file = PubVars.txt_server_name.value
        current_server.start()
        programinfo.running_server_list.append(current_server)

    def start_server_event(fe):
        lst = handlers.get(MSLXEvents.StartServerEvent.value)
        for func in lst:
            try:
                func(fe)
            except Exception as e:
                logger.error(f"执行StartServerEvent时出现错误:{e}")
            else:
                break

    def create_controls(set_attr: bool = False):  # 设置控件

        navbar.on_change = change_navbar
        nonlocal current_server
        assert current_server is not None

        # 开启服务器摁钮
        btn_start_server = ElevatedButton(
            "开启服务器", width=700, on_click=start_server_event
        )
        page.add(Row(
            controls=[btn_start_server],
            alignment=MainAxisAlignment.SPACE_EVENLY
        ))

        # Java与服务端路径
        PubVars.switch_srv_opti_read_only = Switch(
            label="只读", on_change=change_srv_opti_read_only
        )

        PubVars.txt_server_option = TextField(
            label="服务器启动参数",
            width=300,
            value=' '.join(current_server.server_options),
            read_only=True
        )

        if set_attr:
            PubVars.dd_choose_java = Dropdown(
                label="执行方式选择",
                options=[
                    dropdown.Option("Java(Path)"),
                    dropdown.Option("Binary"),
                    dropdown.Option("手动选择Java"),
                ],
                on_change=change_java
            )

        PubVars.btn_detect_java = ElevatedButton(
            "检测Java", on_click=detect_java
        )
        btn_select_server_path = ElevatedButton(
            "选取服务端路径", on_click=select_server_path
        )
        PubVars.txt_server_name = TextField(
            label="服务端名称(不需要后缀名),默认为server", width=300
        )

        PubVars.sr_ram = RangeSlider(
            label='{value}G',
            min=1,
            max=current_server.xmx,
            start_value=1,
            end_value=current_server.xmx,
            divisions=current_server.xmx - 1,
            width=page.width - 420,
            on_change=change_xms_and_xmx
        )

        PubVars.text_xms = Text(f"最小内存:{current_server.xms}G")
        PubVars.text_xmx = Text(f"最大内存:{current_server.xmx}G")

        PubVars.btn_hitokoto = TextButton(PubVars.text, on_click=open_hitokoto)

        PubVars.drawer_options = Container(Row(controls=[Divider()]))
        btn_select_config.on_click = expand_config_select
        for i in PubVars.available_config_list:
            page.drawer.controls.append(NavigationDrawerDestination(label=i))
        page.drawer.controls.append(PubVars.drawer_options)
        page.update()

        if set_attr:
            PubVars.btn_detect_java.disabled = True

        ui_main = Row(controls=[
            navbar,
            Column(controls=[
                Row(
                    controls=[
                        PubVars.txt_server_name,
                        btn_select_server_path,
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Row(
                    controls=[
                        PubVars.txt_server_option,
                        PubVars.switch_srv_opti_read_only,
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Row(
                    controls=[
                        PubVars.dd_choose_java,
                        PubVars.btn_detect_java,
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Column(controls=[
                    Row(controls=[
                        PubVars.text_xms,
                        PubVars.text_xmx
                    ]),
                    PubVars.sr_ram
                ]),
                PubVars.btn_hitokoto
            ])
        ])
        page.add(ui_main)
        page.update()

    def change_java(_e):
        nonlocal current_server
        assert current_server is not None

        def get_result(_e: 'FilePickerResultEvent'):
            assert _e.files is not None
            assert current_server is not None
            file_result = _e.files[0].path
            if file_result:
                current_server.executor = file_result
            else:
                alert_warn_not_chosed_java = AlertDialog(
                    title=Text("选择Java失败,请重新选择"),
                    modal=True,
                    open=True
                )
                page.add(alert_warn_not_chosed_java)
                page.update()
                time.sleep(3)
                alert_warn_not_chosed_java.open = False
                page.update()

        java_option = PubVars.dd_choose_java.value
        if java_option == 'Java(Path)':
            current_server.executor = 'java'
        elif java_option == 'Binary':
            current_server.executor = ''
        elif java_option == '手动选择一个文件':
            picker = FilePicker(on_result=get_result)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(dialog_title="选择Java路径")
        elif java_option in PubVars.java_result:
            current_server.executor = PubVars.java_result[java_option]['path']
        save_server_to_conf(current_server, current_server.config_name.split('.')[0])

    def select_server_path(_e):
        nonlocal current_server
        assert current_server is not None

        AlertDialog(
            title=Text("请勿选择桌面或者根目录!由此带来的任何后果请自行承担责任!"),
            modal=True,
            open=True
        )

        def get_result(_e: 'FilePickerResultEvent'):
            nonlocal current_server
            assert current_server is not None
            file_result = _e.path
            if file_result:
                current_server.server_path = file_result
                save_server_to_conf(current_server, current_server.config_name.split('.')[0])
            else:
                alert_warn_not_chosed_java = AlertDialog(
                    title=Text("选择服务端路径失败,请重新选择"),
                    modal=True,
                    open=True
                )
                page.add(alert_warn_not_chosed_java)
                page.update()
                time.sleep(3)
                alert_warn_not_chosed_java.open = False
                page.update()

        picker = FilePicker(on_result=get_result)
        page.overlay.append(picker)
        page.update()
        picker.get_directory_path(dialog_title="选择服务端路径")

    def change_srv_opti_read_only(_e):

        def unlock_srv_opti(_e):

            def _close(_e):
                nonlocal warn_change_srv_opti
                _warn_finish_change.open = False
                warn_change_srv_opti.open = False
                PubVars.switch_srv_opti_read_only.label = "锁定"
                PubVars.txt_server_option.read_only = False
                page.update()

            warn_change_srv_opti.open = False
            _warn_finish_change = AlertDialog(
                modal=False,
                title=Text("更改服务端启动选项"),
                content=Text("服务端启动选项已经解锁,请务必小心!"),
                actions=[
                    TextButton("确认", on_click=_close),
                ],
                open=True
            )
            page.add(_warn_finish_change)
            page.update()

        if PubVars.switch_srv_opti_read_only.value:
            def close(_e):
                warn_change_srv_opti.open = False
                PubVars.switch_srv_opti_read_only.value = False
                PubVars.switch_srv_opti_read_only.label = "锁定"
                PubVars.txt_server_option.read_only = True
                page.update()

            warn_change_srv_opti = AlertDialog(
                title=Text("更改服务端启动选项"),
                content=Text(
                    "如果您知道自己正在做什么,并且自行承担此操作带来的所有责任,请点击'继续更改';否则,请点击'取消'"
                ),
                actions=[
                    TextButton("继续更改", on_click=unlock_srv_opti),
                    TextButton("取消", on_click=close),
                ],
                modal=False,
                open=True,
            )
            page.add(warn_change_srv_opti)
            page.update()

        if not PubVars.switch_srv_opti_read_only.value:
            def close(_e):
                warn_finish_change.open = False
                PubVars.switch_srv_opti_read_only.value = False
                PubVars.switch_srv_opti_read_only.label = "解锁"
                PubVars.txt_server_option.read_only = True
                page.update()

            warn_finish_change = AlertDialog(
                modal=False,
                title=Text("更改服务端启动选项"),
                content=Text("服务端启动选项已经锁定"),
                actions=[
                    TextButton("确认", on_click=close),
                ],
                open=True
            )
            page.add(warn_finish_change)
            page.update()

    def change_xms_and_xmx(_e):
        nonlocal current_server
        assert current_server is not None
        current_server.xms = math.floor(float(PubVars.sr_ram.start_value))
        current_server.xmx = math.floor(float(PubVars.sr_ram.end_value))
        PubVars.text_xms.value = f"最小内存:{current_server.xms}G"
        PubVars.text_xmx.value = f"最大内存:{current_server.xmx}G"
        page.update()

    def open_hitokoto(_e):
        uuid = PubVars.hitokoto["uuid"]
        wb.open(f"https://hitokoto.cn?uuid={uuid}")

    def on_keyboard(e: KeyboardEvent):

        key = e.key
        shift = e.shift
        ctrl = e.ctrl
        alt = e.alt
        meta = e.meta

        if key == "F5":
            programinfo.update_hitokoto()
            PubVars.hitokoto = programinfo.hitokoto
            text = PubVars.hitokoto["hitokoto"][:-1]
            PubVars.btn_hitokoto.text = text
            page.update()

        if alt and shift:
            if key == "D":  # 更新依赖项

                def poetry(_e):
                    close_warn(warn_update)
                    logger.info("准备更新依赖")
                    sp.run("poetry lock && poetry update", start_new_session=True)
                    logger.info("更新完成")
                    sys.exit()

                def upd_global(_e):
                    close_warn(warn_update)
                    logger.info("准备更新依赖")
                    sp.run("pipreqs --mode compat ./ --encoding=utf8  --debug --force")
                    logger.info("已更新requirements.txt")
                    sp.run("pip install -r requirements.txt --upgrade", start_new_session=True)
                    logger.info("更新完成")
                    sys.exit()

                warn_update = AlertDialog(
                    title=Text("是否尝试更新依赖项?"),
                    content=Text(
                        "如果选择更新依赖项,请在下面选择你运行msl-x时的方式,否则请点取消;选择后将会强制退出msl-x主程序,请确保已经关闭了所有服务器,否则可能造成数据丢失"),
                    actions=[
                        ElevatedButton("Poetry", on_click=poetry),
                        ElevatedButton("Global", on_click=upd_global),
                        ElevatedButton("取消", on_click=lambda _: close_warn(warn_update))
                    ],
                    open=True,
                )

                page.add(warn_update)
                page.update(warn_update)

            elif key == "R":
                logger.debug("准备开始重载配置文件")

        else:  # 开始调用KeyboardShortcutEvent
            handler = handlers.get(MSLXEvents.KeyboardShortcutEvent.value)
            if handler:
                for func in handler:
                    try:
                        func(dict(key=key, shift=shift, ctrl=ctrl, alt=alt, meta=meta))
                    except Exception as e:
                        logger.error(f"执行KeyboardShortcutEvent时出现错误:{e}")

    def submit_cmd(e):
        nonlocal current_server
        assert current_server is not None
        assert PubVars.txt_command.value is not None
        current_server.server.communicate(input=PubVars.txt_command.value)
        refresh(e)
        PubVars.txt_command.value = ""
        page.update()

    def refresh(_e):
        nonlocal current_server
        assert current_server is not None
        with open(f"{current_server.server_path}{os.sep}logs{os.sep}latest.log", "r", encoding="utf-8") as fr:
            out = fr.read()
        PubVars.text_server_logs.value = out
        page.update()

    def change_navbar(e):

        nonlocal submit_cmd, refresh

        def clrpage():
            assert page.controls is not None
            page.controls.clear()
            page.update()

        def mainpage():
            clrpage()
            init_page()
            create_controls()
            page.update()

        def logspage():
            nonlocal submit_cmd, refresh
            clrpage()
            programinfo.page = "日志"
            page.window_width = 900
            page.title = programinfo.title
            PubVars.text_server_logs = TextField(label="服务器输出", value="Minecraft Server Logs Here...",
                                                 read_only=True,
                                                 multiline=True, width=page.width - 320, height=450)
            txt_command = TextField(label="在此键入向服务器发送的命令", on_submit=submit_cmd)
            btn_refresh = ElevatedButton("刷新", on_click=refresh)
            page.add(
                Row(controls=[navbar,
                              Column(controls=[PubVars.text_server_logs, Row(controls=[txt_command, btn_refresh])])]))
            page.update()

        @EventHandler(default_info.frpcpage_event)
        def frpcpage():
            clrpage()
            programinfo.page = "Frpc设置"
            page.window_width = 700
            page.title = programinfo.title
            frpconfig.create_controls(page)
            page.update()

        def opendoc():
            wb.open("https://mslx.fun")

        def showinfo():

            installed_plugin = ""

            for i in Pluginlist:
                text = (f"\n ## {i.name}\n\n"
                        f"### {i.description}\n\n"
                        f"作者:{i.author}\n\n"
                        f"版本:{i.version}\n\n")
                installed_plugin += text
            message = Markdown(f"[Repository Here]("
                               f"https://github.com/MSLXTeam/MSL-X)\n\nCopyleft MojaveHao and all"
                               f"contributors")
            if installed_plugin:
                message.value += f"\n\n# 安装的插件:\n{installed_plugin}"
            about = AlertDialog(
                title=Text("MSL-X 0.1.2b"),
                content=message,
                actions=[TextButton("确认", on_click=lambda _: close_warn(about))],
                modal=True,
                open=True,
            )
            page.add(about)
            page.update()

        def settingspage():
            clrpage()
            programinfo.page = "设置"
            page.window_width = 900
            switch_theme = SegmentedButton(
                on_change=change_theme,
                selected={"跟随系统"},
                allow_empty_selection=False,
                allow_multiple_selection=False,
                segments=[
                    Segment("跟随系统", label=Text("跟随系统")), Segment("明亮", label=Text("明亮")),
                    Segment("黑暗", label=Text("黑暗"))
                ]
            )
            txt_download_threads = TextField(label="下载线程数", value="16")
            page.add(Row(controls=[navbar, Column(controls=[txt_download_threads, switch_theme])]))
            page.update()

        index = e.control.selected_index

        match index:
            case 0:
                mainpage()
            case 1:
                logspage()
            case 2:
                # frpcpage()
                for func in (handlers.get(MSLXEvents.SelectFrpcPageEvent.value)):
                    try:
                        func()
                    except Exception as e:
                        logger.error(f"执行SelectFrpcPageEvents时出现错误:{e}")
                    else:
                        break
            case 3:
                opendoc()
            case 4:
                showinfo()
            case 5:
                settingspage()

    def detect_java(_e):
        handler = handlers.get(MSLXEvents.SearchJavaEvent.value)
        if handler:
            logger.debug("准备开始搜索Java")
            PubVars.java_result = {}
            # 调用查找Java的Handler
            for func in handler:
                try:
                    PubVars.java_result = func()
                except Exception as e:
                    logger.error(f"检测Java时出现错误:{e}")
                    PubVars.java_result = {}
                    continue
                else:
                    break
            if PubVars.java_result != {}:
                exist_java = [item.key for item in PubVars.dd_choose_java.options]
                for j in PubVars.java_result.keys():
                    if j not in exist_java:
                        PubVars.dd_choose_java.options.append(dropdown.Option(j))
                page.update()

    def change_theme(e):
        assert page is not None
        mode = str(e.data).split('"')[1]
        match mode:
            case "跟随系统":
                page.theme_mode = ThemeMode.SYSTEM
            case "明亮":
                page.theme_mode = ThemeMode.LIGHT
            case "黑暗":
                page.theme_mode = ThemeMode.DARK
        page.update()

    def close_warn(obj: AlertDialog):
        obj.open = False
        page.update(obj)

    def expand_config_select(_e):
        assert page is not None
        drawer_selections = set([selection.label for selection in
                                 filter(lambda x: isinstance(x, NavigationDrawerDestination), drawer.controls)])
        drawer.controls = ([Container(height=13)] + [NavigationDrawerDestination(label=i) for i in drawer_selections] +
                           [PubVars.drawer_options])
        page.drawer.open = True
        page.update()

    def select_config(_e):
        nonlocal current_server
        assert page is not None

        index = drawer.selected_index
        index_item = drawer.controls[index + 1]
        if isinstance(index_item, NavigationDrawerDestination):
            target_conf_name = index_item.label
        else:
            target_conf_name = PubVars.available_config_list[index]
        current_conf_name = current_server.config_name
        target_server = load_info_to_server(name=target_conf_name.split('.')[0])
        if current_conf_name != target_conf_name:
            def select_to_new_config(_e):
                close_warn(warn_select)
                nonlocal current_server
                current_server = target_server
                programinfo.running_server_list.append(current_server)
                programinfo.running_server_list = list(set(programinfo.running_server_list))
                PubVars.txt_server_name.value = current_server.server
                current_server.convert_list2str()
                PubVars.txt_server_option.value = current_server.server_option_str
                page.update()

            warn_select = AlertDialog(
                modal=False,
                open=True,
                title=Text("是否切换到新的配置文件?"),
                content=Markdown(
                    f"## {target_server.name}\n\n"
                    f"{target_server.descr}\n\n"
                    f"配置文件:{target_conf_name}\n\n"),
                actions=[
                    ElevatedButton("确定切换", on_click=select_to_new_config),
                    TextButton("取消", on_click=lambda _: close_warn(warn_select))
                ]
            )

            page.add(warn_select)
            page.update()

    def process_theme_config(theme_config: dict):
        def _change_theme(theme):
            match theme.get("mode", "default"):
                case "seed":
                    result = theme.get("seed", "")
                    if result != "":
                        page.theme = Theme(color_scheme_seed=result, font_family="HMOSSans")
                        page.update()
                case "full":
                    result = theme.get("config", {})
                    if result != {}:
                        page.theme = Theme(**result)
                        if "font_family" not in result:
                            page.theme.font_family = "HMOSSans"
                        page.update()

        def change_font(origin_theme):
            theme = copy.deepcopy(origin_theme)
            if general := (theme.get("general", "")):
                page.fonts["general"] = general
                page.theme.font_family = general
                page.dark_theme.font_family = general
                page.update()
                del theme["general"]

        style_light = theme_config.get("light", {})
        style_dark = theme_config.get("dark", {})
        font = theme_config.get("font", {})
        change_font(font)
        _change_theme(style_light)
        _change_theme(style_dark)
        match theme_config.get("default_theme_mode", "system"):
            case "system":
                page.theme_mode = ThemeMode.SYSTEM
            case "light":
                page.theme_mode = ThemeMode.LIGHT
            case "dark":
                page.theme_mode = ThemeMode.DARK
        page.update()

    init_page()
    create_controls(True)
    page.update()
    page.update()
    with open("Config/mslx.toml", encoding="utf-8") as f:
        data = pytomlpp.load(f)
        options = data.get("options", {})
        enable_plugin = options.get("is_plugin_enabled", True)
    if enable_plugin:
        logger.debug("页面完成初始化,准备开始加载插件系统")
        PluginEntry.initialize_plugin("main", page)
        logger.debug("插件系统加载完毕,准备进行后续操作")
        PubVars.btn_detect_java.disabled = False
        detect_java(None)
        drawer.on_change = select_config
        page.update()
        logger.debug("所有后续工作已完成")


app(target=main, assets_dir="assets")
