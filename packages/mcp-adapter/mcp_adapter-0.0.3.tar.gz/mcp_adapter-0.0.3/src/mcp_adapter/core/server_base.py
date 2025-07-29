import inspect
import logging
from abc import ABC
from typing import Optional

from docstring_parser import parse
from fastapi import FastAPI
from mcp.server import FastMCP

logger = logging.getLogger(__name__)


class McpServerAdapterBase(ABC):
    mcp_server: FastMCP

    transport: str
    '''streamable_http, sse'''

    base_url: str

    mount_path: str

    name: str

    description: str

    ignore_method = ['mount', '__init__', 'info', '_mount_tools']

    @classmethod
    def mount(cls,
        app: FastAPI,
        mount_path: str,
        base_url: Optional[str] = '',
        debug: Optional[bool] = True,
        transport: Optional[str] = 'streamable_http'
    ):
        mcp_server = FastMCP(cls.name, json_response=True)

        mcp_server.settings.debug = debug
        if debug:
            mcp_server.settings.log_level = "DEBUG" if debug else 'INFO'
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        cls.transport = transport
        if cls.transport == 'sse':
            mcp_server.settings.sse_path = '/'
            mcp_server.settings.message_path = '/messages/'
            app.mount(f'{mount_path}', app=mcp_server.sse_app(), name=f'{cls.name}')
        elif cls.transport == 'streamable_http':
            mcp_server.settings.streamable_http_path = '/'
            app.mount(f'{mount_path}', app=mcp_server.streamable_http_app(), name=f'{cls.name}')
        else:
            raise Exception(f'unknown server transport type: [{cls.transport}], must be one of ["sse", "streamable_http"]')

        service = cls(server=mcp_server, base_url=base_url, mount_path=mount_path, transport=transport)
        return service

    def __init__(self, server: FastMCP, mount_path: str, base_url: str = None, transport: str = 'streamable_http'):
        self.mcp_server = server
        self.mount_path = mount_path
        self.transport = transport
        self.base_url = base_url[:-1] if base_url.endswith('/') else base_url

        self._mount_tools()

    def info(self):
        return {
            "name": self.name,
            "transport": self.transport,
            "url": f'{self.base_url}/{self.mount_path}',
            "description": self.description,
        }

    def _mount_tools(self):
        """调用mcp sdk，添加可以被调用的tool"""
        logger.debug('=======================')
        logger.debug(f'Mount f{self.__class__} by [{self.transport}], mount at [{self.mount_path}], convert mcp tools: ')
        methods = inspect.getmembers(self.__class__, predicate=inspect.isfunction)
        for method in methods:
            method_name = method[0]
            method_fn = method[1]
            if method_name not in self.ignore_method:
                docstring = inspect.getdoc(method_fn)
                parsed = parse(docstring)
                logger.debug(f'\tAdd tool --------- {method_name}')
                for param in parsed.params:
                    logger.debug(f"\t\tParameter: {param.arg_name}, Type: {param.type_name}, Desc: {param.description}")
                if parsed.returns:
                    logger.debug(f"\t\tReturns: Type: {parsed.returns.type_name}, Desc: {parsed.returns.description}")
                self.mcp_server.add_tool(fn=method_fn, name=method_name, description=docstring)
