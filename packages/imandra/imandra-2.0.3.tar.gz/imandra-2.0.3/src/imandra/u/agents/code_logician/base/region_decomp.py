from typing import Any

from pydantic import BaseModel, Field

from .imandrax import DecomposeRes


class RawDecomposeReq(BaseModel):
    """
    A function to decompose in source code and its corresponding function in IML.
    """

    description: str = Field(
        description="Human-readable description of the function to decompose"
    )
    src_func_name: str = Field(
        description="name of function to decompose in source code"
    )
    iml_func_name: str = Field(description="name of function to decompose in IML")


class DecomposeReqData(BaseModel):
    name: str
    assuming: list[str] | None = Field(None)
    basis: list[str] | None = Field(None)
    rule_specs: list[str] | None = Field(None)
    prune: bool | None = Field(True)
    ctx_simp: bool | None = Field(True)
    lift_bool: Any | None = Field(None)
    timeout: float | None = Field(None)
    str_: bool | None = Field(True)


class RegionDecomp(BaseModel):
    """
    A region decomposition
    """

    raw: RawDecomposeReq
    data: DecomposeReqData | None = Field(None)
    res: DecomposeRes | None = Field(None)

    test_cases: dict[str, list[dict]] | None = Field(None)

    def __repr__(self):
        s = ""
        s += "RawDecomposeReq:\n"
        s += f"  Src func name: {self.raw.src_func_name}\n"
        s += f"  IML func name: {self.raw.iml_func_name}\n"
        s += f"  Description: {self.raw.description}\n"
        s += "DecomposeReqData:\n"
        s += f"  {self.data.model_dump_json() if self.data else 'None'}\n"
        s += "DecomposeRes:\n"
        s += f"  {str(len(self.res.__repr__())) + ' bytes' if self.res else 'None'}\n"
        s += (
            "Test cases: "
            f"({len(self.test_cases['iml']) if self.test_cases else 'None'})"
        )
        return s
