# plugin.py
from typing import Any

from fastpluggy.core.module_base import FastPluggyBaseModule


def get_debug_router():
    from .router import debug_plugin_router
    return debug_plugin_router


class DebugToolsPlugin(FastPluggyBaseModule):
    module_name: str = "debug_tools"
    module_version: str = "0.0.2"
    module_menu_name: str = "Debug Tools"
    module_menu_icon: str = "fas fa-tools"
    module_menu_type: str = "admin"

    module_router: Any = get_debug_router
