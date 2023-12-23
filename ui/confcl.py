from flet import \
    (
    Theme,
    ElevatedButton,
    Row,
    Column
)

from .Navbar import nav_side as navbar


def init_page(page):
    page.title = "MSLX | 配置文件"
    page.window_height = 600
    page.window_width = 900
    page.fonts = {
        "SHS_TC": "fonts/SourceHanSansTC-Regular.otf",
        "SHS_SC": "fonts/SourceHanSansSC-Regular.otf"
    }
    page.theme = Theme(font_family="SHS_SC")
    page.update()


def create_controls(page):
    btn_save_config = ElevatedButton("保存服务器配置")
    btn_load_config = ElevatedButton("加载服务器配置")
    page.add(Row(controls=[navbar, Column(controls=[btn_save_config, btn_load_config])]))
