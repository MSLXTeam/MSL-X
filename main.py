import copy
import math
import os
import subprocess as sp
import sys
import time
import webbrowser as wb
from typing import TYPE_CHECKING

import pyperclip as clip
import pytomlpp
from Crypto.PublicKey import RSA
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
    FilePickerFileType,
    FilePickerResultEvent,
)

import PluginEntry
from Plugins.tools.PluginList import Pluginlist
from Plugins.tools.EventTools import EventHandler
from Plugins.tools.InfoClasses import handlers, MSLXEvents
from lib.confctl import (
    ConfCtl,
    load_info_to_server,
    save_server_to_conf
)
from lib.crypt.AES import AES_encrypt
from lib.crypt.RSA import RSA_encrypt
from lib.info_classes import ProgramInfo
from lib.log import logger
from ui import (
    frpconfig,
    nginxconf,
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
    global available_config_list
    available_config_list = []
    for _, _, files in os.walk("Config"):
        for file in files:
            if file.endswith(".json"):
                available_config_list.append(file)
    logger.info(f"可用的配置文件列表:{','.join(available_config_list)}")
    current_server = load_info_to_server()
    current_server.convert_list2str()
    programinfo = ProgramInfo()
    hitokoto = programinfo.hitokoto
    text = hitokoto["hitokoto"][:-1]
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
            with open("Config/mslx.toml", encoding="utf-8") as f:
                data = pytomlpp.load(f)
                style = data.get("style", {})
                process_theme_config(style)
        else:
            pytomlpp.dump({},"Config/mslx.toml")
        page.update()

    @EventHandler(MSLXEvents.StartServerEvent)
    def start_server(e):
        nonlocal programinfo, current_server
        assert txt_server_name.value is not None
        assert current_server is not None
        programinfo.name = current_server.name
        page.update()
        if txt_server_name.value != "":
            current_server.server_file = txt_server_name.value
        current_server.start()
        programinfo.running_server_list.append(current_server)

    def StartServerEvent(fe):
        lst = handlers.get(MSLXEvents.StartServerEvent.value)
        for func in lst:
            try:
                func(fe)
            except Exception as e:
                logger.error(f"执行StartServerEvent时出现错误:{e}")
            else:
                break

    def create_controls():  # 设置控件

        navbar.on_change = change_navbar
        nonlocal current_server
        assert current_server is not None

        # 开启服务器摁钮
        btn_start_server = ElevatedButton(
            "开启服务器", width=700, on_click=StartServerEvent
        )
        page.add(Row(
            controls=[btn_start_server],
            alignment=MainAxisAlignment.SPACE_EVENLY
        ))

        # Java与服务端路径
        global switch_srv_opti_read_only
        switch_srv_opti_read_only = Switch(
            label="只读", on_change=change_srv_opti_read_only
        )

        global txt_server_option
        txt_server_option = TextField(
            label="服务器启动参数",
            width=300,
            value=' '.join(current_server.server_options),
            read_only=True
        )

        global dd_choose_java
        dd_choose_java = Dropdown(
            label="执行方式选择",
            options=[
                dropdown.Option("Java(Path)"),
                dropdown.Option("Binary"),
                dropdown.Option("手动选择Java"),
            ],
            on_change=change_java
        )
        global txt_server_name, btn_detect_java
        btn_detect_java = ElevatedButton(
            "检测Java", on_click=detect_java, disabled=True
        )
        btn_select_server_path = ElevatedButton(
            "选取服务端路径", on_click=select_server_path
        )
        txt_server_name = TextField(
            label="服务端名称(不需要后缀名),默认为server", width=300
        )

        global sr_ram, text_xms, text_xmx
        sr_ram = RangeSlider(
            label='{value}G',
            min=1,
            max=current_server.xmx,
            start_value=1,
            end_value=current_server.xmx,
            divisions=current_server.xmx - 1,
            width=page.width - 420,
            on_change=change_xms_and_xmx
        )

        text_xms = Text(f"最小内存:{current_server.xms}G")
        text_xmx = Text(f"最大内存:{current_server.xmx}G")

        nonlocal text
        global btn_hitokoto
        btn_hitokoto = TextButton(text, on_click=open_hitokoto)

        global drawer_options
        drawer_options = Container(Row(controls=[Divider()]))
        btn_select_config.on_click = expand_config_select
        for i in available_config_list:
            page.drawer.controls.append(NavigationDrawerDestination(label=i))
        page.drawer.controls.append(drawer_options)
        page.update()

        ui_main = Row(controls=[
            navbar,
            Column(controls=[
                Row(
                    controls=[
                        txt_server_name,
                        btn_select_server_path,

                    ],
                    alignment=MainAxisAlignment.END
                ),
                Row(
                    controls=[
                        txt_server_option,
                        switch_srv_opti_read_only,
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Row(
                    controls=[
                        dd_choose_java,
                        btn_detect_java,
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Column(controls=[
                    Row(controls=[
                        text_xms,
                        text_xmx
                    ]),
                    sr_ram
                ]),
                btn_hitokoto
            ])
        ])
        page.add(ui_main)
        page.update()

    def change_java(e):
        nonlocal current_server
        assert current_server is not None

        def get_result(e: 'FilePickerResultEvent'):
            assert e.files is not None
            assert current_server is not None
            file_result = e.files[0].path
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

        java_option = dd_choose_java.value
        if java_option == 'Java(Path)':
            current_server.executor = 'java'
        elif java_option == 'Binary':
            current_server.executor = ''
        elif java_option == '手动选择一个文件':
            picker = FilePicker(on_result=get_result)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(dialog_title="选择Java路径")
        elif java_option in java_result:
            current_server.executor = java_result[java_option]['path']
        save_server_to_conf(current_server, current_server.config_name.split('.')[0])

    def select_server_path(e):
        nonlocal current_server
        assert current_server is not None

        AlertDialog(
            title=Text("请勿选择桌面或者根目录!由此带来的任何后果请自行承担责任!"),
            modal=True,
            open=True
        )

        def get_result(e: 'FilePickerResultEvent'):
            nonlocal current_server
            assert current_server is not None
            file_result = e.path
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

    def change_srv_opti_read_only(e):

        def unlock_srv_opti(e):

            def close(e):
                nonlocal warn_change_srv_opti
                warn_finish_change.open = False
                warn_change_srv_opti.open = False
                switch_srv_opti_read_only.label = "锁定"
                txt_server_option.read_only = False
                page.update()

            warn_change_srv_opti.open = False
            warn_finish_change = AlertDialog(
                modal=False,
                title=Text("更改服务端启动选项"),
                content=Text("服务端启动选项已经解锁,请务必小心!"),
                actions=[
                    TextButton("确认", on_click=close),
                ],
                open=True
            )
            page.add(warn_finish_change)
            page.update()

        if switch_srv_opti_read_only.value:
            def close(e):
                warn_change_srv_opti.open = False
                switch_srv_opti_read_only.value = False
                switch_srv_opti_read_only.label = "锁定"
                txt_server_option.read_only = True
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

        if not switch_srv_opti_read_only.value:
            def close(e):
                warn_finish_change.open = False
                switch_srv_opti_read_only.value = False
                switch_srv_opti_read_only.label = "解锁"
                txt_server_option.read_only = True
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

    def change_xms_and_xmx(e):
        nonlocal current_server
        assert current_server is not None
        current_server.xms = math.floor(float(sr_ram.start_value))
        current_server.xmx = math.floor(float(sr_ram.end_value))
        text_xms.value = f"最小内存:{current_server.xms}G"
        text_xmx.value = f"最大内存:{current_server.xmx}G"
        page.update()

    def save_config(e):
        nonlocal current_server

        def get_result(e: FilePickerResultEvent):
            nonlocal current_server

            def close(e):
                warn_conf.open = False
                page.update()

            file_result = e.path
            if file_result:
                logger.debug(f"获取到的文件路径:{file_result}")
                if "json" not in file_result:
                    file_result += ".json"
                current_server = save_server_to_conf(current_server, full_path=file_result)
                warn_conf = AlertDialog(
                    modal=False,
                    title=Text("保存配置文件成功"),
                    actions=[
                        TextButton("确认", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_conf)
            else:
                warn_conf = AlertDialog(
                    modal=False,
                    title=Text("保存配置文件失败"),
                    actions=[
                        TextButton("确认", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_conf)

        picker = FilePicker(on_result=get_result)
        page.overlay.append(picker)
        page.update()
        picker.save_file(dialog_title="保存配置文件", file_name="Default",
                         initial_directory=os.path.abspath("Config" + os.sep), file_type=FilePickerFileType.CUSTOM,
                         allowed_extensions=["json"])
        page.update()

    def load_config(e):
        global name
        nonlocal current_server

        def get_result(e: FilePickerResultEvent):

            def close(e):
                warn_conf.open = False
                page.update()

            nonlocal current_server
            file_result = e.files
            if file_result:
                file_name = file_result[0].name
                src_path = file_result[0].path
                logger.debug(f"获取到的文件名:{file_name}")
                logger.debug(f"获取到的文件路径:{src_path}")
                current_server = load_info_to_server(full_path=src_path)
                warn_conf = AlertDialog(
                    modal=False,
                    title=Text("加载配置文件成功"),
                    actions=[
                        TextButton("确认", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_conf)
            else:
                warn_conf = AlertDialog(
                    modal=False,
                    title=Text("加载配置文件失败"),
                    actions=[
                        TextButton("确认", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_conf)

        picker = FilePicker(on_result=get_result)
        page.overlay.append(picker)
        page.update()
        picker.pick_files(dialog_title="选择配置文件", initial_directory=os.path.abspath("Config" + os.sep),
                          file_type=FilePickerFileType.CUSTOM, allowed_extensions=["json"])
        page.update()

    # noinspection PyUnusedLocal
    def detect_nginx(e):

        def close(e):
            warn_type_choose.open = False
            page.update()

        # noinspection PyShadowingNames
        def detect_ng_linux(e):

            def close(e):
                warn_result.open = False
                warn_type_choose.open = False
                page.update()

            def copy(e):
                clip.copy(f"Path:{wri}\nNginx -V Info:{ngv}")

            wri = sp.run("whereis nginx", shell=True)
            ngv = sp.run("nginx -V", shell=True)
            try:
                wri.check_returncode()
            except sp.CalledProcessError:
                warn_result = AlertDialog(
                    modal=False,
                    title=Text("检测失败"),
                    content=Text(f"未能找到nginx"),
                    actions=[
                        TextButton("确定", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_result)
                page.update()
            else:
                try:
                    ngv.check_returncode()
                except sp.CalledProcessError:
                    warn_result = AlertDialog(
                        modal=False,
                        title=Text("检测失败"),
                        content=Text(f"未能获取nginx版本(请确认已经添加至环境变量)"),
                        actions=[
                            TextButton("确定", on_click=close),
                        ],
                        open=True
                    )
                    page.add(warn_result)
                    page.update()
                else:
                    txt_pathto.value = wri.stdout.decode()
                    warn_result = AlertDialog(
                        modal=False,
                        title=Text("检测结果"),
                        content=Text(f"Path:{wri}\nNginx Info:{ngv}"),
                        actions=[
                            TextButton("确定", on_click=close),
                            TextButton("复制", on_click=copy),
                        ],
                        open=True
                    )
                    page.add(warn_result)
                    page.update()

        def detect_ng_winpath(e):

            def copy(e):
                clip.copy(f"Path:{ng_path}\nNginx -V Info:{ngv}")

            dirs = os.environ.get("Path")
            assert dirs is not None
            ng_path = ""
            for ng_dir in dirs:
                if os.path.isfile(f"{ng_dir}\\nginx.exe"):
                    ng_path = ng_dir
                    break
            if ng_path != "":
                ngv = sp.run(ng_path + "nginx.exe -V").stdout.decode()
                txt_pathto.value = ng_path
                warn_result = AlertDialog(
                    modal=False,
                    title=Text("检测结果"),
                    content=Text(f"Path:{ng_path}\nNginx Info:{ngv}"),
                    actions=[
                        TextButton("确定", on_click=close),
                        TextButton("复制", on_click=copy),
                    ],
                    open=True
                )
                page.add(warn_result)
                page.update()
            else:
                warn_result = AlertDialog(
                    modal=False,
                    title=Text("检测失败"),
                    content=Text(f"未能在环境变量中找到Nginx(请确认已添加至Path变量)"),
                    actions=[
                        TextButton("确定", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_result)
                page.update()

        warn_type_choose = AlertDialog(
            modal=False,
            title=Text("选择检测方法"),
            actions=[
                TextButton("检测Path(Linux)", on_click=detect_ng_linux),
                TextButton("检测环境变量(Windows)", on_click=detect_ng_winpath),
            ],
            open=True
        )
        page.add(warn_type_choose)
        page.update()

    def ident_path(e):
        global ngpath
        ngpath = txt_pathto.value

    def ngconfpage():
        assert page.controls is not None
        page.controls.clear()
        page.update()
        nginxconf.init_page(page)
        global txt_pathto
        txt_pathto = TextField(label="Nginx路径", height=400, multiline=True)
        btn_confirm = ElevatedButton("确认", on_click=ident_path)
        btn_auto_detect = ElevatedButton("检测", on_click=detect_nginx)
        row_top = Row(controls=[btn_confirm, btn_auto_detect])
        page.add(Row(controls=[navbar, Column(controls=[txt_pathto, row_top])]))
        page.update()

    def open_hitokoto(e):
        uuid = hitokoto["uuid"]
        wb.open(f"https://hitokoto.cn?uuid={uuid}")

    def test_aes_create(e):
        global txt_aes_key, dd_mode
        if page is None or page.controls is None or dd_mode is None:
            raise
        if dd_mode.value == 'AES' and len(page.controls) < 3:
            txt_passwd.height = 200
            txt_aes_key = TextField(label="在此输入AES将使用的key,登陆时须和您的密钥一起使用", width=850, height=200,
                                    can_reveal_password=True, multiline=True)
            global col_passwd_gen
            col_passwd_gen.controls.append(txt_aes_key)
            page.update()

        if dd_mode.value == 'RSA' and txt_aes_key in col_passwd_gen.controls:
            col_passwd_gen.controls.remove(txt_aes_key)
            page.update()

    def process_gen(e):

        assert txt_passwd is not None
        assert txt_passwd.value is not None

        def copy_rsa(e):
            content = f"[RSA Login Info]\nPrivate Key:{result}\nPublic Key:\n{second_key}"
            clip.copy(content)

        def copy_aes(e):
            content = f"[AES Login Info]\nPasswd:{result}\nKey:{second_key}"
            clip.copy(content)

        second_key = ""

        if dd_mode.value == "AES":
            aes_key = txt_aes_key.value
            result = AES_encrypt(org_str=txt_passwd.value, key=aes_key)
            second_key = aes_key
            finish = AlertDialog(title=Text("完成"), content=Text(
                f"你已经完成了AES加密密码的创建流程,信息如下:\nPasswd:{result}\nKey:{aes_key}"), actions=[
                TextButton("确认", on_click=lambda _: close_warn(finish)),
                TextButton("复制信息到剪贴板", on_click=copy_aes),
            ], open=True)
            page.add(finish)
            page.update()

        if dd_mode.value == "RSA":
            key = RSA.generate(2048)
            pri_key = key.export_key()
            with open("./Crypt/pri_key.pem", "wb") as f:
                f.write(pri_key)
            pub_key = key.public_key().export_key()
            second_key = pub_key.decode()
            with open("./Crypt/pub_key.pem", "wb") as f:
                f.write(pub_key)
            result = RSA_encrypt(text=txt_passwd.value, public_key=pub_key)
            finish = AlertDialog(title=Text("完成！"), content=Text(
                f"你已经完成了RSA加密密钥的创建流程,信息如下:\nPrivate Key:{result}\nPublic Key:\n{second_key}"),
                                 actions=[
                                     TextButton("确认", on_click=lambda _: close_warn(finish)),
                                     TextButton("复制信息到剪贴板", on_click=copy_rsa),
                                 ], open=True)
            page.add(finish)
            page.update()

    def process_login(e):
        """
        type = dd_choose_java.value
        if type == 'AES':
            AES_decrypt(txt_passwd.value, key)
        """
        pass

    def test_aes_login(e):
        assert page.controls is not None
        global txt_aes_key
        txt_aes_key = TextField()  # 避免未绑定
        if dd_mode.value == 'AES' and len(page.controls) < 3:
            txt_passwd.height = 200
            txt_aes_key = TextField(label="在此输入AES使用的key", width=850, height=200, can_reveal_password=True,
                                    multiline=True)
            global col_passwd_gen
            col_passwd_gen.controls.append(txt_aes_key)
            page.update()

        if dd_mode.value == 'RSA':
            if txt_aes_key in col_passwd_gen.controls:
                col_passwd_gen.controls.pop()
                page.update()

    def on_keyboard(e: KeyboardEvent):

        nonlocal text
        nonlocal hitokoto

        def clrpage():
            assert page.controls is not None
            page.controls.clear()
            page.update()

        key = e.key
        shift = e.shift
        ctrl = e.ctrl
        alt = e.alt
        meta = e.meta
        if key == "F5":
            nonlocal text
            nonlocal hitokoto
            programinfo.update_hitokoto()
            hitokoto = programinfo.hitokoto
            text = hitokoto["hitokoto"][:-1]
            btn_hitokoto.text = text
            page.update()
        if alt and shift:
            global txt_passwd, dd_mode
            if key == "D":  # 更新依赖项

                def poetry(e):
                    logger.info("准备更新依赖")
                    sp.run("poetry lock && poetry update", start_new_session=True)
                    sys.exit()

                def upd_global(e):
                    logger.info("准备更新依赖")
                    sp.run("pipreqs --mode no-pin ./ --encoding=utf8  --debug --force")
                    logger.info("已更新requirements.txt")
                    sp.run("pip install -r requirements.txt --upgrade", start_new_session=True)
                    sys.exit()

                warn_update = AlertDialog(
                    title=Text("是否尝试更新依赖项?"),
                    content=Text("如果选择更新依赖项,请在下面选择你运行msl-x时的方式,否则请点取消;选择后将会强制退出msl-x主程序,请确保已经关闭了所有服务器,否则可能造成数据丢失"),
                    actions=[
                        ElevatedButton("Poetry",on_click=poetry),
                        ElevatedButton("Global", on_click=upd_global),
                        ElevatedButton("取消", on_click=lambda _: close_warn(warn_update))
                    ]
                )

                page.add(warn_update)
                page.update()

            elif key == "N":  # 打开Nginx配置页面
                ngconfpage()

            elif key == "G":
                clrpage()
                txt_passwd = TextField(label="在此输入您的原始密码", width=850, height=400,
                                       can_reveal_password=True, multiline=True)

                dd_mode = Dropdown(
                    label="方法选择",
                    options=[
                        dropdown.Option("AES"),
                        dropdown.Option("RSA"),
                    ],
                    width=500,
                    autofocus=True,
                    on_change=test_aes_create
                )
                btn_gen = ElevatedButton("创建", width=100, on_click=process_gen)
                global col_passwd_gen
                col_passwd_gen = Column(controls=[dd_mode, txt_passwd])
                row_top = Row(controls=[navbar, col_passwd_gen, btn_gen])
                page.add(row_top)
                page.update()

            elif key == "L":
                clrpage()
                txt_passwd = TextField(label="在此输入您的密钥", width=850, height=400, can_reveal_password=True,
                                       multiline=True)
                dd_mode = Dropdown(
                    label="方法选择",
                    options=[
                        dropdown.Option("AES"),
                        dropdown.Option("RSA"),
                    ],
                    width=500,
                    autofocus=True,
                    on_change=test_aes_login
                )
                btn_login = ElevatedButton("登录", width=100, on_click=process_login)
                col_passwd_gen = Column(controls=[dd_mode, txt_passwd])
                row_top = Row(controls=[navbar, col_passwd_gen, btn_login])
                page.add(row_top)
                page.update()

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
        assert txt_command.value is not None
        current_server.server.communicate(input=txt_command.value)
        refresh(e)
        txt_command.value = ""
        page.update()

    def refresh(e):
        nonlocal current_server
        assert current_server is not None
        with open(f"{current_server.server_path}{os.sep}logs{os.sep}latest.log", "r", encoding="utf-8") as fr:
            out = fr.read()
        text_server_logs.value = out
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
            global txt_command, text_server_logs
            clrpage()
            programinfo.page = "日志"
            page.window_width = 900
            page.title = programinfo.title
            text_server_logs = TextField(label="服务器输出", value="Minecraft Server Logs Here...", read_only=True,
                                         multiline=True, width=page.width - 320, height=450)
            txt_command = TextField(label="在此键入向服务器发送的命令", on_submit=submit_cmd)
            btn_refresh = ElevatedButton("刷新", on_click=refresh)
            page.add(
                Row(controls=[navbar, Column(controls=[text_server_logs, Row(controls=[txt_command, btn_refresh])])]))
            page.update()

        @EventHandler(MSLXEvents.SelectFrpcPageEvent)
        def frpcpage():
            clrpage()
            programinfo.page = "Frpc设置"
            page.window_width = 700
            page.title = programinfo.title
            frpconfig.create_controls(page)
            page.update()

        def opendoc():
            wb.open("https://mslxteam.github.io/MSL-X/#/")

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
                for func in (handler := handlers.get(MSLXEvents.SelectFrpcPageEvent.value)):
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

    def detect_java(e):
        handler = handlers.get(MSLXEvents.SearchJavaEvent.value)
        if handler:
            logger.debug("准备开始搜索Java")
            global java_result
            java_result = {}
            # 调用查找Java的Handler
            for func in handler:
                try:
                    java_result = func()
                except Exception as e:
                    logger.error(f"检测Java时出现错误:{e}")
                    java_result = {}
                    continue
                else:
                    break
            if java_result != {}:
                exist_java = [item.text for item in dd_choose_java.options]
                for j in java_result.keys():
                    if j not in exist_java:
                        dd_choose_java.options.append(dropdown.Option(j))
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

    def expand_config_select(e):
        assert page is not None
        drawer_selections = set([selection.label for selection in
                                 filter(lambda x: isinstance(x, NavigationDrawerDestination), drawer.controls)])
        drawer.controls = ([Container(height=13)] + [NavigationDrawerDestination(label=i) for i in drawer_selections] +
                           [drawer_options])
        page.drawer.open = True
        page.update()

    def select_config(e):
        nonlocal current_server
        assert page is not None

        index = drawer.selected_index
        index_item = drawer.controls[index + 1]
        if isinstance(index_item, NavigationDrawerDestination):
            target_conf_name = index_item.label
        else:
            target_conf_name = available_config_list[index]
        current_conf_name = current_server.config_name
        target_server = load_info_to_server(name=target_conf_name.split('.')[0])
        if current_conf_name != target_conf_name:
            def select_to_new_config(e):
                close_warn(warn_select)
                nonlocal current_server
                current_server = target_server
                programinfo.running_server_list.append(current_server)
                programinfo.running_server_list = list(set(programinfo.running_server_list))
                txt_server_name.value = current_server.server
                current_server.convert_list2str()
                txt_server_option.value = current_server.server_option_str
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
        def change_theme(theme):
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
                            page.theme.font_family="HMOSSans"
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
        change_theme(style_light)
        change_theme(style_dark)
        match theme_config.get("default_theme_mode", "system"):
            case "system":
                page.theme_mode = ThemeMode.SYSTEM
            case "light":
                page.theme_mode = ThemeMode.LIGHT
            case "dark":
                page.theme_mode = ThemeMode.DARK
        page.update()

    init_page()
    create_controls()
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
        btn_detect_java.disabled = False
        detect_java(None)
        drawer.on_change = select_config
        page.update()
        logger.debug("所有后续工作已完成")


app(target=main, assets_dir="assets")
