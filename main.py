import math
import os
import subprocess as sp
import time
import webbrowser as wb
from typing import TYPE_CHECKING

import pyperclip as clip
from Crypto.PublicKey import RSA
from flet import (
    app,
    Row,
    Text,
    Theme,
    Column,
    Slider,
    Switch,
    dropdown,
    Dropdown,
    TextField,
    TextButton,
    FilePicker,
    FilePickerFileType,
    FilePickerResultEvent,
    KeyboardEvent,
    AlertDialog,
    ElevatedButton,
    MainAxisAlignment,
)

import PluginEntry
from lib.Decorators import (
    MSLXEvents,
    EventHandler,
    GetEventHandlers,
    handlers as program_handlers
)
from lib.confctl import (
    ConfCtl,
    LoadServerInfoToServer,
    SaveServerInfoToConf
)
from lib.crypt.AES import AES_encrypt
from lib.crypt.RSA import RSA_encrypt
from lib.info_classes import ProgramInfo
from lib.log import logger
from ui import (
    confcl,
    frpconfig,
    logs,
    nginxconf,
    settings
)
from ui.Navbar import nav_side as navbar

if TYPE_CHECKING:
    from flet import Page


@logger.catch
def main(page: 'Page'):
    # PluginEntry.before_run("main", page)
    if not os.path.exists("Config/Default.json"):  # 如果默认配置不存在就保存默认配置
        conf = ConfCtl("Default")
        conf.Save_Config()
    current_server = LoadServerInfoToServer()
    programinfo = ProgramInfo()
    hitokoto = programinfo.hitokoto
    text = hitokoto["hitokoto"][:-1]

    create_dirs = ["Config", "Logs", "Crypt"]
    for dir_name in create_dirs:
        if not os.path.exists(dir_name):
            os.mkdir(dir_name)

    def init_page():

        nonlocal current_server, programinfo
        page.window_height = 600
        page.window_width = 1350
        page.fonts = dict(SHS_TC="fonts/SourceHanSansTC-Regular.otf", SHS_SC="fonts/SourceHanSansSC-Regular.otf")
        theme_dark = Theme(font_family="SHS_SC", color_scheme_seed="#1f1e33")
        theme_day = Theme(font_family="SHS_SC")
        page.theme = theme_day
        page.dark_theme = theme_dark
        page.on_keyboard_event = on_keyboard
        programinfo.update_hitokoto()
        if programinfo.title != "":
            page.title = programinfo.title

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
        lst = GetEventHandlers(MSLXEvents.StartServerEvent.value)
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
        current_server.convert_list2str()
        txt_server_option = TextField(
            label="服务器启动参数",
            width=300,
            value=current_server.server_option_str,
            read_only=True
        )

        global dd_choose_java
        dd_choose_java = Dropdown(
            label="Java选择",
            width=150,
            options=[
                dropdown.Option("Path"),
                dropdown.Option("Choose Java File"),
            ],
            on_change=change_java
        )
        global txt_server_name
        btn_show_java_path = ElevatedButton(
            "显示Java路径", on_click=show_java_path
        )
        btn_select_server_path = ElevatedButton(
            "选取服务端路径", on_click=select_server_path
        )
        txt_server_name = TextField(
            label="服务端名称(不需要.jar后缀),默认为server", width=300
        )

        global xms, sli_xms, sli_xmx
        sli_xms = Slider(
            label="最小内存(G)", width=500,
            divisions=current_server.xmx - 1, min=1, max=current_server.xmx, on_change=change_xms
        )
        sli_xmx = Slider(
            label="最大内存(G)", width=500,
            divisions=current_server.xmx - current_server.xms, min=1, max=current_server.xmx, on_change=change_xmx
        )

        global xmx, text_xms, text_xmx
        text_xms = Text(f"最小内存:{current_server.xms}G")
        text_xmx = Text(f"最大内存:{current_server.xmx}G")

        nonlocal text
        btn_hitokoto = TextButton(text, on_click=open_hitokoto)

        ui_main = Row(controls=[
            navbar,
            Column(controls=[
                Row(
                    controls=[
                        switch_srv_opti_read_only,
                        txt_server_option,
                        txt_server_name,
                        btn_select_server_path,
                        dd_choose_java,
                        btn_show_java_path
                    ],
                    alignment=MainAxisAlignment.END
                ),
                Column(controls=[
                    Row(controls=[
                        text_xms,
                        text_xmx
                    ]),
                    Row(controls=[
                        sli_xms,
                        sli_xmx
                    ])
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
                current_server.use_java = file_result
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
        if java_option == 'Path':
            current_server.use_java = 'java'
        else:
            picker = FilePicker(on_result=get_result)
            page.overlay.append(picker)
            page.update()
            picker.pick_files(dialog_title="选择Java路径")

    def show_java_path(e):
        assert current_server is not None
        alert_show_java_path = AlertDialog(
            title=Text(f"Java路径(若为java则使用环境变量):{current_server.use_java}"),
            modal=True,
            open=True
        )
        page.add(alert_show_java_path)
        page.update()
        time.sleep(3)
        alert_show_java_path.open = False
        page.update()

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

    def change_xms(e):
        nonlocal current_server
        assert current_server is not None
        assert sli_xms.value is not None
        current_server.xms = math.floor(sli_xms.value)
        text_xms.value = f"最小内存:{current_server.xms}G"
        page.update()

    def change_xmx(e):
        nonlocal current_server
        assert current_server is not None
        assert sli_xmx.value is not None
        xmx = math.floor(sli_xmx.value)
        current_server.xmx = xmx
        text_xmx.value = f"最大内存:{xmx}G"
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
                current_server = SaveServerInfoToConf(current_server, full_path=file_result)
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

            file_result = e.files
            if file_result:
                file_name = file_result[0].name
                src_path = file_result[0].path
                logger.debug(f"获取到的文件名:{file_name}")
                logger.debug(f"获取到的文件路径:{src_path}")
                current_server = LoadServerInfoToServer(full_path=src_path)
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

            nonlocal close

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

        def close(e):
            finish.open = False
            page.update()

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
                TextButton("确认", on_click=close),
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
                                     TextButton("确认", on_click=close),
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
            page.update()
        if alt and shift:
            global txt_passwd, dd_mode
            if key == "D":  # 更新依赖项
                def close(e):
                    warn_ok.open = False
                    page.update()

                logger.info("准备更新依赖")
                sp.run("pipreqs --mode no-pin ./ --encoding=utf8  --debug --force")
                logger.info("已更新requirements.txt")
                sp.run("pip install -r requirements.txt --upgrade")
                logger.info("已下载/更新了所有MSLX所依赖的包")
                warn_ok = AlertDialog(
                    modal=False,
                    title=Text("更新完成"),
                    content=Text(f"已完成依赖项的检测和下载/更新工作"),
                    actions=[
                        TextButton("确定", on_click=close),
                    ],
                    open=True
                )
                page.add(warn_ok)
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
            logs.init_page(page)
            text_server_logs = TextField(label="服务器输出", value="Minecraft Server Logs Here...", read_only=True,
                                         multiline=True, width=750, height=500)
            txt_command = TextField(label="在此键入向服务器发送的命令", on_submit=submit_cmd)
            btn_refresh = ElevatedButton("刷新", on_click=refresh)
            page.add(
                Row(controls=[navbar, Column(controls=[text_server_logs, Row(controls=[txt_command, btn_refresh])])]))
            page.update()

        @EventHandler(MSLXEvents.SelectFrpcPageEvent)
        def frpcpage():
            clrpage()
            frpconfig.init_page(page)
            frpconfig.create_controls(page)
            page.update()

        def opendoc():
            wb.open("https://mojavehao.github.io/MSL-X/#/")

        def showinfo():
            def close(e):
                about.open = False
                page.update()

            about = AlertDialog(
                title=Text("MSLX Beta 0.08(0.0.8b)"),
                actions=[TextButton("确认", on_click=close)],
                modal=True,
                open=True,
            )
            page.add(about)
            page.update()

        def settingspage():
            clrpage()
            settings.init_page(page)
            settings.create_controls(page)
            page.update()

        def cconfigpage():
            clrpage()
            confcl.init_page(page)
            btn_save_config = ElevatedButton("保存服务器配置", on_click=save_config)
            btn_load_config = ElevatedButton("加载服务器配置", on_click=load_config)
            page.add(
                Row(controls=[navbar, Column(controls=[btn_save_config, btn_load_config])]))
            page.update()

        index = e.control.selected_index

        match index:
            case 0:
                mainpage()
            case 1:
                logspage()
            case 2:
                # frpcpage()
                for func in (handler := GetEventHandlers(MSLXEvents.SelectFrpcPageEvent.value)):
                    logger.debug(handler)
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
            case 6:
                cconfigpage()

    init_page()
    create_controls()
    page.update()
    logger.debug("页面完成初始化,准备开始加载插件系统")

    # 初始化各个插件
    PluginEntry.initialize_plugin("main", page)
    logger.debug("插件系统加载完毕")
    # 把插件注册的事件加入到MSLX的事件列表中
    logger.debug("准备合并Handlers")
    # logger.debug(f"插件注册的Handler:{Plugins.PluginList.handlers}")
    # logger.debug(f"程序内的的Handler:{Decorators.handlers}")
    PluginEntry.merge_events()
    logger.debug(f"合并Handlers完成,现在的Handler:{program_handlers}")


app(target=main, assets_dir="assets")
