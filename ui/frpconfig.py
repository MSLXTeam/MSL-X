import platform
import random

import requests
from flet import \
    (
    Theme,
    Dropdown,
    dropdown,
    TextField,
    ElevatedButton,
    Row,
    Column
)

from .Navbar import nav_side as navbar

node = ''
port = 25565
user = ''
protocol = "tcp"
remote_port = random.randint(20000, 60000)


def create_controls(page):
    def start_frpc(e):

        node_list = {
            '上海1': 'sh1',
            '香港': 'hk',
            '北京[付费]': 'bj',
            '广州[付费]': 'gz',
            '上海2[付费]': 'sh2',
        }
        if dd_node.value is None:
            raise
        node = node_list[dd_node.value]

        protocol_list = ["tcp", "udp", "tcp+udp", "kcp", "quic"]

        frpc_config = f'''
        [common]
        server_port=7000
        server_addr={node}.qwq.one
        user={user}
        meta_token=20021120
        protocol={protocol}

        [TCP]
        type=tcp
        local_ip=127.0.0.1
        local_port={port}
        remote_port={remote_port}

        [UDP]
        type=udp
        local_ip=127.0.0.1
        local_port={port}
        remote_port={remote_port}
    '''

    def download_frpc(e):

        sys_type = platform.system()

        url = 'https://api.github.com/repos/fatedier/frp/releases/latest'
        response_data = requests.get(url)
        response_dict = response_data.json()
        assets_list = response_dict["assets"]
        resource_list = []

        for items in assets_list:
            name = items["name"]
            browser_download_url = items["browser_download_url"]
            tmp_dict = {"name": name, "url": browser_download_url}
            resource_list.append(tmp_dict)

        for current_dict in resource_list:
            if sys_type.lower() in current_dict["name"] and "amd64" in current_dict["name"]:
                download_url = current_dict["url"]
                download_name = current_dict["name"]

                print(
                    f'''Donwload file name:{download_name}
                    Download file URL:{download_url}'''
                )
        # download(down_url=download_url, down_name=download_name)

    dd_node = Dropdown(
        label="节点选择",
        options=[
            dropdown.Option("上海1"),
            dropdown.Option("香港"),
            dropdown.Option("北京[付费]"),
            dropdown.Option("广州[付费]"),
            dropdown.Option("上海2[付费]"),
        ],
        width=500
    )
    txt_port = TextField(
        label="服务器端口",
        value='25565'
    )
    txt_user = TextField(
        label="在此输入您的QQ号(请勿乱输)",
        width=300
    )
    dd_protocol = Dropdown(
        label="协议选择",
        width=200,
        options=[
            dropdown.Option("TCP(Java)"),
            dropdown.Option("UDP(Bedrock)"),
            dropdown.Option("TCP+UDP(互通服用)"),
            dropdown.Option("KCP(仅付费节点可用)"),
            dropdown.Option("QUIC(仅付费节点可用)")
        ]
    )
    btn_start_frpc = ElevatedButton("启动映射", on_click=start_frpc)
    btn_download_frpc = ElevatedButton("下载最新版frpc", on_click=download_frpc)
    ctrls_bottom = Row(controls=[btn_start_frpc, btn_download_frpc])

    page.add(Row(controls=[navbar, Column(controls=[
        dd_node,
        txt_port,
        txt_user,
        dd_protocol,
        ctrls_bottom])
                           ]))
    page.update()
