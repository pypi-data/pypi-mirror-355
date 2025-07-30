import enum

from pydantic import BaseModel

from seekrai.types.agents.tools.tool_env_types import Env


class ToolType(str, enum.Enum):
    FILE_SEARCH = "file_search"


class ToolBase(BaseModel):
    name: ToolType
    tool_env: Env
