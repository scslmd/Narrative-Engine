from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class StrictSchemaModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        populate_by_name=True,
        use_enum_values=True,
    )


class StrictModel(StrictSchemaModel):
    pass