from Plugins.tools.InfoClasses import PluginInfo
from Plugins.tools.PluginTools import AddPluginInfo

info = PluginInfo(name="ExamplePlugin", author="MojaveHao",
                  description="Nope,Happy coding! =)", version="1.0.0")


@AddPluginInfo(info)
def foo():
    print("Example Plugin Loaded!")
