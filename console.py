import sys
import os
import cmd2 as cmd
from cmd2 import with_argparser, ansi, plugin
from rich.tree import Tree
from rich import console, print
from lib.pubvars import PubVars

console = console.Console()


def gen_tree(data: dict, tree: Tree = Tree("Plugins")):
    for key, value in data.items():
        if isinstance(value, dict):
            branch = tree.add(key)
            gen_tree(value, branch)
        else:
            tree.add(f"{key}: {value}")
    return tree


def get_plugin_data():
    plugin_data = {}
    for item in PubVars.plugin_list:
        dict_attr = dict(
            location=item.get("Location", "Unknown"),
            entrypoint=item.get("EntryPoint", "Unknown"),
            file=item.get("File", "Unknown"), )
        final_dict = dict(name=item.get("Name", "Unknown"), attributes=dict_attr)
        plugin_data = {**final_dict, **plugin_data}
    return plugin_data


class MSLXConsole(cmd.Cmd):

    def __init__(self):
        super().__init__()
        self.cwd = ""
        self.prompt = ansi.style(f'[MSLXConsole{self.cwd}]$', fg=ansi.Fg.BLUE)
        self.register_postcmd_hook(self.refresh_prompt)

    available_configs = list(filter(None, [
        (file.split('.')[0] if (("." in file) and (file.split('.')[1] == 'json')) else None) for file in
        os.listdir("Config")])) + ["root", "/", "global"]

    argparse_plugin = cmd.Cmd2ArgumentParser()
    argparse_cd = cmd.Cmd2ArgumentParser()
    argparse_cd.add_argument("server", nargs=1, choices=available_configs)
    argparse_plugin.add_argument("-t", "--tree", action="store_true", help="Display tree of plugins")

    def refresh_prompt(self, data: plugin.PostcommandData) -> plugin.PostcommandData:
        self.prompt = ansi.style(f'[MSLXConsole{self.cwd}]$', fg=ansi.Fg.BLUE)
        return data

    @with_argparser(argparse_plugin)
    def do_plugin(self, opt):
        """MSLX Plugin Control"""
        if opt.tree is True:
            data = get_plugin_data()
            if data != {}:
                tree = gen_tree(data)
                print(tree)
            else:
                print("请先运行MSLX")

    @staticmethod
    def do_exit(opt):
        """Exit Console"""
        quit()

    @with_argparser(argparse_cd)
    def do_cd(self, opt):
        """Change working config file"""
        if opt.server[0] in ["root", "/", "global"]:
            self.cwd = ""
        elif opt.server[0] in self.available_configs:
            self.cwd = f"/{opt.server[0]}"
        else:
            print(f"配置文件{opt.server[0]}不存在")

    def do_ls(self, opt):
        """List available config files"""
        for i in self.available_configs:
            if i not in ["root", "/", "global"]:
                print(f"- {i}")


if __name__ == "__main__":
    sys.exit(MSLXConsole().cmdloop())
