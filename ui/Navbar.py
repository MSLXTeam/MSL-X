from flet import \
    (
    NavigationRail,
    NavigationRailDestination,
    icons
)

nav_side = NavigationRail(
    selected_index=0,
    # label_type=None,
    # extended=True,
    height=450,
    min_width=60,
    min_extended_width=400,
    group_alignment=-0.9,
    destinations=[
        NavigationRailDestination(
            icon=icons.HOME,
            label="主页"
        ),
        NavigationRailDestination(
            icon=icons.HISTORY,
            label="日志"
        ),
        NavigationRailDestination(
            icon=icons.APPS,
            label="内网穿透"
        ),
        NavigationRailDestination(
            icon=icons.DOCUMENT_SCANNER,
            label="文档"
        ),
        NavigationRailDestination(
            icon=icons.INFO,
            label="信息"
        ),
        NavigationRailDestination(
            icon=icons.SETTINGS,
            label="设置"
        ),
        NavigationRailDestination(
            icon=icons.INSERT_DRIVE_FILE,
            label="配置文件"
        ),
        # NavigationRailDestination(
        #    icon=icons.FILE_UPLOAD_OUTLINED,
        #    label="加载配置文件"
        # ),
        # NavigationRailDestination(
        #    icon=icons.FILE_DOWNLOAD,
        #    label="保存配置文件"
        # ),
    ], )
