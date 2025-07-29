from typing import Any

from pydantic import BaseModel


class McpServerModel(BaseModel):
    server_class: Any

    transport: str

    base_url: str

    mount_path: str
