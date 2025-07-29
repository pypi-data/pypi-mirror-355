# mcp-adapter
* 对mcp sdk的二次封装 
* 以python类继承的方式，非侵入式封装function到mcp tool的转化
* FastAPI支持，快速挂载在FastAPI服务中


## Getting started
### 1. 继承`McpServerAdapterBase`，实现功能
```python
from mcp_adapter.core.server_base import McpServerAdapterBase


class MockMcpServerSse(McpServerAdapterBase):

    name = 'MockMcpServerSse'

    description = 'MockMcpServerSse Service'

    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    @staticmethod
    def sub(a: int, b: int) -> int:
        """Sub two numbers"""
        return a - b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b


class MockMcpServerHttpStreamable(McpServerAdapterBase):

    name = 'MockMcpServerHttpStreamable'

    description = 'MockMcpServerHttpStreamable Service'

    @staticmethod
    def add(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    @staticmethod
    def sub(a: int, b: int) -> int:
        """Sub two numbers"""
        return a - b

    @staticmethod
    def multiply(a: int, b: int) -> int:
        """Multiply two numbers"""
        return a * b

```

### 2. 在FastAPI项目中加载mcp server
请参考： [脚手架项目](https://gitlab.aimanthor.com/shared/mcp/mcp-server-scaffold)
