from Plugins.tools import InfoClasses

start_server_event = InfoClasses.EventHandlerInfo(name="Builtin StartServerEvent Handler", author="Builtin",
                                                  on=InfoClasses.MSLXEvents.StartServerEvent.value)
frpcpage_event = InfoClasses.EventHandlerInfo(name="Builtin FrpcPageEvent Handler", author="Builtin",
                                              on=InfoClasses.MSLXEvents.SelectFrpcPageEvent.value)
