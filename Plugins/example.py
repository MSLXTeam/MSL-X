from Plugins.tools.InfoClasses import UniversalInfo, InfoTypes
from Plugins.tools.PluginTools import AddPluginInfo

info = UniversalInfo(type_of_info=InfoTypes.Plugin, name="ExamplePlugin", author="MojaveHao",
                     description="Nope,Happy coding! =)", version="1.0.0", need_page=False)


@AddPluginInfo(info)
def foo():
    print("Example Plugin Loaded!")
