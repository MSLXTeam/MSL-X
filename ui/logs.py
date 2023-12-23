from flet import Theme


def init_page(page):
    page.title = "MSLX | 日志"
    page.window_width = 900
    page.window_height = 550
    page.fonts = \
        {
            "SHS_TC": "fonts/SourceHanSansTC-Regular.otf",
            "SHS_SC": "fonts/SourceHanSansSC-Regular.otf"
        }
    page.theme = Theme(font_family="SHS_SC")
    page.update()
