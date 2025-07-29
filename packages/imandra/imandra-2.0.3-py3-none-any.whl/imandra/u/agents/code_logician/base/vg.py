import textwrap
from typing import Literal, Self

from pydantic import BaseModel, Field

from .imandrax import VerifyRes


class RawVerifyReq(BaseModel):
    """
    A formal specification of a property / logical statement, clause, predicate,
    or condition to verify about functions in the source code.

    Each verification pairs a natural language description with a corresponding logical
    statement that will be later used in tasks related to property-based testing and
    formal verification.
    The description is human-readable, while the logical statement is more precise,
    mathematically formal.
    """

    src_func_names: list[str] = Field(
        ...,
        description="names of the functions (including class methods) involved "
        "in the verification",
    )
    iml_func_names: list[str] = Field(
        ..., description="names of the corresponding functions in IML"
    )
    description: str = Field(
        ...,
        description="Human-readable description of the property to verify. Should "
        "clearly explain what aspect of the function's behavior is being checked. "
        "Example: 'The function always returns a value greater than or equal to 10' or "
        "'The output array is always sorted in ascending order'",
    )
    logical_statement: str = Field(
        ...,
        description="Logical statement expressing the property in a precise way. "
        "Can use plain English with logical terms like 'for all', 'there exists', "
        "'and', 'or', etc. Example: 'for all inputs x, f(x) is greater than or equal "
        "to 10' or 'for all indices i from 0 to n-2, array[i] is less than or equal "
        "to array[i+1]'",
    )

    def __repr__(self):
        s = ""
        s += f"Src func names: {self.src_func_names}\n"
        s += f"IML func names: {self.iml_func_names}\n"
        s += f"Description: {self.description}\n"
        s += f"Logical statement: {self.logical_statement}\n"
        s = "RawVerifyReq\n" + textwrap.indent(s, "  ")
        return s


class VerifyReqData(BaseModel):
    """Verify"""

    predicate: str = Field(
        description="IML code representing some logical statement using lambda"
        "functions. Eg. `fun x -> x >= 10`, `fun x -> f x <> 98`. Backticks should"
        "be omitted."
    )
    kind: Literal["verify", "instance"] = Field(
        description="""Kind of reasoning request. 
        - `verify` checks that the given predicate is always true (universal)
        - `instance` finds an example where the predicate is true (existential)
        """
    )

    def to_iml(self) -> str:
        return f"${self.kind} ({self.predicate})"

    def to_negation(self) -> Self:
        """Negate the predicate"""

        predicate = self.predicate
        arrow_idx = predicate.index("->")
        dom = predicate[:arrow_idx]
        cod = predicate[arrow_idx + 2 :]
        neg_cod = f"not ({cod.strip()})"
        neg_predicate = f"{dom}-> {neg_cod}"
        if self.kind == "verify":
            kind = "instance"
        else:
            kind = "verify"
        return self.__class__(predicate=neg_predicate, kind=kind)

    def __repr__(self):
        s = ""
        s += f"Predicate: {self.predicate}\n"
        s += f"Kind: {self.kind}\n"
        s = "VerifyReqData\n" + textwrap.indent(s, "  ")
        return s


class VG(BaseModel):
    """
    A verification goal
    """

    raw: RawVerifyReq
    data: VerifyReqData | None = Field(None)
    res: VerifyRes | None = Field(None)

    def __repr__(self):
        s = ""
        s += self.raw.__repr__() if self.raw else "None"
        s += self.data.__repr__() if self.data else "None"
        s += f"VerifyRes:\n{
            textwrap.indent(self.res.model_dump_json() if self.res else 'None', '  ')
        }"
        s = "VG\n" + textwrap.indent(s, "  ")
        return s
