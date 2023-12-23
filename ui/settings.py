from flet import \
    (
    Theme,
    TextField,
    Switch,
    Row,
    Column
)

from .Navbar import nav_side as navbar


def init_page(page):
    page.title = "MSLX | 设置"
    page.window_height = 600
    page.window_width = 900
    page.fonts = {
        "SHS_TC": "fonts/SourceHanSansTC-Regular.otf",
        "SHS_SC": "fonts/SourceHanSansSC-Regular.otf"
    }
    page.theme = Theme(font_family="SHS_SC")
    page.update()


def create_controls(page):
    txt_download_threads = TextField(label="下载线程数", value="16")
    auto_run_server = TextField(label="启动时默认配置文件名称", value="Default")
    auto_run_selector = Switch(label="自动启动服务器开关")
    auto_run_frpc = Switch(label="自动启动frpc开关(由于frpc配置未制作完成而暂时禁用)")
    txt_cover_current_start_command = TextField(
        label="手动覆盖当前配置文件的启动命令(适用于网页端无法选择Java目录的情况,正常没有必要),留空则为不覆盖",
        width=780)
    page.add(Row(controls=[navbar, Column(
        controls=[txt_download_threads, auto_run_server, auto_run_selector, auto_run_frpc,
                  txt_cover_current_start_command])]))
