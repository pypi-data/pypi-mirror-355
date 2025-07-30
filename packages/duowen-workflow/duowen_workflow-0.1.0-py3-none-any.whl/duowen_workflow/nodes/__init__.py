import importlib.util
import os
import sys
from pathlib import Path

from .builtin import *
from ..entities import NodeBase

nodes = {k: v for k, v in list(locals().items()) if
         isinstance(v, type) and issubclass(v, NodeBase) and not isinstance(v, NodeBase)}

# 动态加载plugins目录下的模块
_plugins_dir = os.getenv("WORKFLOW_NODES_PLUGINS_DIR", None)
if _plugins_dir and os.path.exists(_plugins_dir) and os.path.isdir(_plugins_dir):
    for py_file in Path(_plugins_dir).glob("*.py"):
        if py_file.name.startswith("__"):
            continue

        # 动态导入模块
        module_name = py_file.stem
        spec = importlib.util.spec_from_file_location(f"{__package__}.plugins.{module_name}", py_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module  # 注册到全局模块
            spec.loader.exec_module(module)

            # 收集当前模块中的NodeBase子类
            plugin_nodes = {name: cls for name in dir(module) if
                            isinstance((cls := getattr(module, name)), type) and issubclass(cls,
                                                                                            NodeBase) and cls is not NodeBase}
            nodes.update(plugin_nodes)
