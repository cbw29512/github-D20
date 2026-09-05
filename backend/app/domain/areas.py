from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

AreaShape = Literal["cone", "cube", "line", "radius"]


class AreaGeometry(BaseModel):
    """Minimal Iron Pit geometry needed to preserve RAW area coverage math."""

    shape: AreaShape
    size_ft: int = Field(gt=0, le=1000)
    width_ft: int | None = Field(default=None, gt=0, le=1000)

    @model_validator(mode="after")
    def validate_width(self) -> "AreaGeometry":
        if self.shape == "line" and self.width_ft is None:
            raise ValueError("Line areas require width_ft.")
        if self.shape != "line" and self.width_ft is not None:
            raise ValueError("Only line areas may define width_ft.")
        return self
