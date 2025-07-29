from pydantic import BaseModel, Field

from .imandrax import InferredType

Loc = tuple[int, int]


class IMLCode(BaseModel):
    iml_code: str = Field(description="IML code", strict=True)


class IMLSymbol(InferredType):
    opaque: bool


class Opaqueness(BaseModel):
    """Existence of opaque function and its possible solutions"""

    opaque_func: str = Field(description="The opaque function")
    assumptions: list[str] = Field(
        [],
        description=(
            "Assumptions about the opaque function. Each assumption is an axiom. "
            "For example, `axiom boo x = f x > 0`"
        ),
    )
    approximation: str | None = Field(
        None, description="An approximation of the opaque function"
    )
    assumption_candidates: list[str] = Field([], description="Assumption candidates")
    approximation_candidates: list[str] = Field(
        [], description="Approximation candidates"
    )
