from typing import Annotated

from pydantic import Field

from seekrai.types.agents.tools.schemas.file_search import FileSearch


Tool = Annotated[
    FileSearch, Field(discriminator="name")
]  # will be a Union of tools when more are added
