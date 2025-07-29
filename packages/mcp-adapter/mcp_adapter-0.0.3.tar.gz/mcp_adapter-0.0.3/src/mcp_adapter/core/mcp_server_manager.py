from typing import List

from fastapi import FastAPI

from .schema import McpServerModel
from .server_base import McpServerAdapterBase


class McpServerManager:

    mcp_adapters: dict[McpServerAdapterBase]

    @classmethod
    def load_mcp_servers(cls, fastapi_app: FastAPI, mcp_servers: list[McpServerModel]):
        mcp_manager = cls(fastapi_app=fastapi_app, mcp_servers=mcp_servers)
        return mcp_manager

    def __init__(self, fastapi_app: FastAPI, mcp_servers: List[McpServerModel]):
        self.mcp_adapters = {}
        self._load_mcp_servers(fastapi_app=fastapi_app, mcp_servers=mcp_servers)

    def _load_mcp_servers(self, fastapi_app: FastAPI, mcp_servers: List[McpServerModel]):
        for mcp_server in mcp_servers:
            try:
                cls = mcp_server.server_class
                server_adapter = cls.mount(app=fastapi_app, base_url=mcp_server.base_url, mount_path=mcp_server.mount_path, transport=mcp_server.transport)
                self.mcp_adapters[cls.name] = server_adapter
            except Exception as e:
                pass

    def get_mcp_servers(self, info_only: bool = False):
        if info_only:
            return [adapter.info() for adapter in self.mcp_adapters.values()]
        else:
            return self.mcp_adapters.values()
