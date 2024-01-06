from flet import (
    NavigationRail,
    NavigationRailDestination,
    FloatingActionButton,
    icons
)

btn = FloatingActionButton(icon=icons.VIEW_LIST_OUTLINED,)

nav_side = NavigationRail(
    selected_index=0,
    leading=btn,
    height=450,
    min_width=60,
    min_extended_width=400,
    elevation=0.6,
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
    ], )
