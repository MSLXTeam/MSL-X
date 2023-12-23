# MSLX开发文档

## 插件部分

### 配置用于插件信息的UniversalInfo

#### 使用

```python
from .InfoClasses import InfoTypes, UniversalInfo
info = UniversalInfo(...) # 按照下文的参数说明填写
```

#### 参数说明

- ```type_of_info```用于UniversalInfo的信息内容识别，在用于插件信息的情况下必须为```InfoClasses.InfoTypes.Plugin```
- ```name ```是插件的名称
- ```author ```是插件的作者
- ```description``` 是插件的描述
- ```version ```是插件的版本
- ```on``` 表示插件加载的位置
- ```args``` 表示插件需要在运行时获取的变量
- ```multi_thread``` 如果程序需要经过threading的特殊处理可将此项设为True
- ```thread_class``` 在指定上一个参数为True的情况下**必须**指定此项为继承了Thread类的子类的类名
- ```events``` 表示插件在发生指定事件时需要执行的特殊动作
    - ```on_load``` 当插件被检测到的时候运行的函数名称，无论插件是否启用
    - ```on_enable``` 当插件被启用时运行的函数名称，插件的初始化函数应该写在这里而不是on_load处
    - ```on_disable``` 当插件被关闭时运行的函数名称，需要注意的是如果主程序启动时插件已经被禁用，则这里的函数不会被运行

#### 后续操作

- 使用```@PluginTools.AddPluginInfo```来注册插件的入口点

### 注册插件的入口点

#### 使用

假设你有以下代码:

```python
def fool():
    print("WTF is this")
```

则首先按照上面的说明配置UniversalInfo，然后使用```@PluginTools.AddPluginInfo```来注册这个函数为插件的入口点:

```python
from .InfoClasses import InfoTypes, UniversalInfo
from .PluginTools import AddPluginInfo
info = UniversalInfo(type_of_info=InfoTypes.Plugin, name="WTFPlugin", author="You")
@AddPluginInfo(info)
def fool():
    print("WTF is this")
```

就这样，你写出了你的第一个插件。

## 事件部分

咕~

## 命令部分

咕~