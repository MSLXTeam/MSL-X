import sys

from flet import Page, Theme

sys.path.append("..")


# from lib.crypt import AES_encrypt,AES_decrypt
# from lib.crypt import RSA_encrypt,RSA_decrypt

def init_page(page: Page):
    page.title = "MSLX | Panel Password Genrate"
    page.window_height = 550
    page.window_width = 900
    page.fonts = {
        "SHS_TC": "fonts/SourceHanSansTC-Regular.otf",
        "SHS_SC": "fonts/SourceHanSansSC-Regular.otf"
    }
    page.theme = Theme(font_family="SHS_SC")
    page.update()
