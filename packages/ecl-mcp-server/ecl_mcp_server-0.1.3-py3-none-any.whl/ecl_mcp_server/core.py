#  Copyright © 2025 China Mobile (SuZhou) Software Technology Co.,Ltd
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from typing import Any, List

from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel

from ecl_mcp_server import constants, singleton


class Module(singleton.SingletonBase):
    """Controls which ecl_mcp_server.tools modules to import"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.modules: dict[str, FastMCP] = {}

    def add_module(self, module_name: str) -> FastMCP:
        """Adds and initializes a new module

        Args:
            module_name: Name of the module to add

        Returns:
            Initialized FastMCP instance

        Raises:
            AssertionError: If module_name is empty
        """
        assert module_name, "module name must be provided"
        if module_name not in self.modules:
            self.modules[module_name] = FastMCP(module_name)
        return self.modules[module_name]

    def load(self, modules: List[str]) -> FastMCP:
        """Loads specified modules and returns an integrated FastMCP instance

        Args:
            modules: List of module names to load, supports special value 'all' to load all modules

        Returns:
            FastMCP instance containing all loaded module tools

        Example:
            >>> module = Module()
            >>> mcp = module.load(['module1', 'module2'])
            >>> # Or load all modules
            >>> mcp = module.load(['all'])
        """
        import importlib

        mcp = FastMCP("ecl-server", instructions="提供一组工具，用以操作日志相关服务。")
        modules = set(modules)
        if "all" in modules:
            modules.update(constants.MODULES)
            modules.remove("all")

        for module in modules:
            importlib.import_module(f"ecl_mcp_server.tools.{module}")

            server = self.modules.get(module)

            tools = server._tool_manager.list_tools()
            for tool in tools:
                mcp.add_tool(
                    fn=tool.fn,
                    name=tool.name,
                    description=tool.description,
                    annotations=tool.annotations,
                )

        return mcp


def model_dump(model: BaseModel) -> dict[str, Any]:
    return model.model_dump(mode="json")
