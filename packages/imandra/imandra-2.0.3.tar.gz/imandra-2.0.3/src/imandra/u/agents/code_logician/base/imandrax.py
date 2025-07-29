from __future__ import annotations

from enum import Enum
from typing import Self

from imandrax_api.lib import (
    Common_Fun_decomp_t_poly,
    Common_Region_t_poly,
    read_artifact_data,
)
from pydantic import BaseModel, Field, TypeAdapter, field_validator, model_validator


class Art(BaseModel, ser_json_bytes="base64", val_json_bytes="base64"):
    kind: str = Field(description="The kind of artifact")
    data: bytes = Field(description="Serialized data, in twine")
    api_version: str = Field(
        description=(
            "Version of the API. This is mandatory and must match with the imandrax-api"
            " library version."
        )
    )


class ErrorMessage(BaseModel):
    """An error message"""

    msg: str
    locs: list[Location] | None = Field(
        default=None, description="Locations for this message"
    )
    backtrace: str | None = Field(default=None, description="Captured backtrace")


class Error(BaseModel):
    msg: ErrorMessage = Field(description="The toplevel error message")
    kind: str = Field(description="A string description of the kind of error")
    stack: list[ErrorMessage] | None = Field(
        default=None, description="Context for the error"
    )
    process: str | None = Field(default=None)


class Position(BaseModel):
    line: int
    col: int


class Location(BaseModel):
    file: str | None = Field(default=None)
    start: Position
    stop: Position


class Session(BaseModel):
    """A session identifier"""

    id: str = Field(description="The session's unique ID (e.g a uuid)")


class SessionCreate(BaseModel):
    """Create a new session"""

    po_check: bool = Field(default=True, description="Do we check Proof Obligations?")
    api_version: str = Field(description="the API types version (mandatory)")


class SessionOpen(BaseModel):
    """Reconnect to the given session"""

    id: Session = Field(description="The session's unique ID (e.g a uuid)")
    api_version: str = Field(description="the API types version (mandatory)")


class TaskKind(Enum):
    TASK_UNSPECIFIED = "TASK_UNSPECIFIED"
    TASK_EVAL = "TASK_EVAL"
    TASK_CHECK_PO = "TASK_CHECK_PO"
    TASK_PROOF_CHECK = "TASK_PROOF_CHECK"
    TASK_DECOMP = "TASK_DECOMP"


class TaskID(BaseModel):
    id: str = Field(description="The task identifier")


class Task(BaseModel):
    id: TaskID
    kind: TaskKind


class Empty(BaseModel):
    """Void type, used for messages without arguments or return value."""

    pass


class StringMsg(BaseModel):
    msg: str


class SessionCreateReq(BaseModel):
    api_version: str = Field(description="the API types version (mandatory)")


class LiftBool(Enum):
    Default = 0
    NestedEqualities = 1
    Equalities = 2
    All = 3


class DecomposeReq(BaseModel):
    session: Session
    name: str = Field(description="name of function to decompose")
    assuming: str | None = Field(description="name of side condition function")
    basis: list[str]
    rule_specs: list[str]
    prune: bool
    ctx_simp: bool
    lift_bool: LiftBool
    str: bool


class string_kv(BaseModel):
    k: str
    v: str


class RegionStr(BaseModel):
    model_eval_str: str
    constraints_str: list[str] | None = Field(default=None)
    invariant_str: str
    model_str: dict[str, str]


def sanitise_table_cell(cell: str) -> str:
    return cell.replace("\n", "\\\n").replace("|", "\\|")


class DecomposeRes(BaseModel):
    """Result of a decomposition"""

    # res: Art | Empty | None = Field(default=None)
    artifact: Art | None = Field(default=None)
    regions_str: list[RegionStr] | None = Field(
        default=None, description="None if there's decomposition error"
    )
    errors: list[Error] | None = Field(default=None)
    task: Task | None = Field(default=None)

    @model_validator(mode="after")
    def unwrap_region_str(self) -> Self:
        # Unwrap the regionsStr from the artifact to the old format
        if self.regions_str is not None:  # noqa: SIM114
            return self
        elif self.errors:
            return self
        else:
            art = read_artifact_data(data=self.artifact.data, kind=self.artifact.kind)
            match art:
                case Common_Fun_decomp_t_poly(_f_id, _f_args, regions):
                    pass
                case _:
                    raise ValueError(f"Unknown decomp artifact type: {type(art)}")

            regions_str: list[RegionStr] = []
            for region in regions:
                match region:
                    case Common_Region_t_poly(
                        constraints=_constraints,
                        invariant=_invariant,
                        meta=meta,
                        status=_status,
                    ):
                        meta_d = dict(meta)

                        # string
                        meta_str_d = dict(meta_d.get("str").arg)
                        constraints = [c.arg for c in meta_str_d.get("constraints").arg]
                        invariant = meta_str_d.get("invariant").arg
                        model = {k: v.arg for (k, v) in meta_str_d.get("model").arg}
                        model_eval = meta_str_d.get("model_eval").arg
                        region_str = RegionStr(
                            model_eval_str=model_eval,
                            invariant_str=invariant,
                            constraints_str=constraints,
                            model_str=model,
                        )
                        regions_str.append(region_str)
                    case _:
                        raise ValueError(f"Unknown region type: {type(region)}")
            return self.model_copy(update={"regions_str": regions_str})

    @property
    def model(self) -> list[dict[str, str]]:
        """[{"x": "1", "y": "2"}, {"x": "3", "y": "4"}]"""
        if not self.regions_str:
            return []
        return [r.model_str for r in self.regions_str]

    @property
    def model_eval(self) -> list[str]:
        if not self.regions_str:
            return []
        return [r.model_eval_str for r in self.regions_str]

    @property
    def iml_test_cases(self) -> list[dict[str, str]]:
        """
        [
            {"args": {"x": "1", "y": "2"}, "expected_output": "3"},
            {"args": {"x": "3", "y": "4"}, "expected_output": "7"},
        ]
        """
        if not self.regions_str:
            return []
        return list(
            map(
                lambda x: {"args": x[0], "expected_output": x[1]},
                zip(self.model, self.model_eval, strict=False),
            )
        )

    @property
    def test_docstrs(self) -> list[str]:
        docstrs = []
        for region_str in self.regions_str:
            s = ""
            if region_str.constraints_str:
                s += "Constraints:\n"
                for c in region_str.constraints_str:
                    s += f"    - `{c}`\n"
            if region_str.invariant_str:
                s += "Invariant:\n"
                s += f"    - `{region_str.invariant_str}`\n"
            docstrs.append(s)
        return docstrs


class EvalSrcReq(BaseModel):
    session: Session
    src: str = Field(description="source code to evaluate")


class EvalRes(BaseModel):
    success: bool | None = Field(default=None)
    messages: list[str] | None = Field(None, description='"normal" messages')
    errors: list[Error] | None = Field(None, description="akin to stderr")
    tasks: list[Task] | None = Field(None, description="all tasks started during eval")


class VerifySrcReq(BaseModel):
    session: Session
    src: str = Field(description="source code")
    hints: str | None


class VerifyNameReq(BaseModel):
    session: Session
    name: str = Field(description="name of the predicate to verify")
    hints: str | None


class InstanceNameReq(BaseModel):
    session: Session
    name: str = Field(description="name of the predicate to verify")
    hints: str | None


class Proved(BaseModel):
    proof_pp: str


class Unsat(BaseModel):
    proof_pp: str | None


class ModelType(Enum):
    Counter_example = "Counter_example"
    Instance = "Instance"


class Model(BaseModel):
    m_type: ModelType
    src: str = Field(description="iml source code for the model")
    artifact: Art | None = Field(description="the model as an artifact")


class Refuted(BaseModel):
    model: Model


class Sat(BaseModel):
    model: Model


class VerifyRes(BaseModel):
    proved: Proved | None = Field(None)
    errors: list[Error] | None = Field(None)
    task: Task | None = Field(None, description="the ID of the task")


class InstanceRes(BaseModel):
    res: StringMsg | Empty | Unsat | Sat | None = None
    sat: Sat | None = None
    errors: list[Error] | None = None
    task: Task | None = Field(None, description="the ID of the task")


class TypecheckReq(BaseModel):
    src: str = Field(description="source code to evaluate")


class InferredType(BaseModel):
    name: str
    ty: str = Field(description="inferred type")
    line: int = Field(description="line number")
    column: int = Field(description="column number")


InferredTypes = TypeAdapter(list[InferredType])


class TypecheckRes(BaseModel):
    success: bool
    types: list[InferredType] = Field(description="inferred types")
    errors: list[Error] | None = Field(None, description="akin to stderr")

    @field_validator("types", mode="before")
    @classmethod
    def validate_types(cls, v: str | list[InferredType]) -> list[InferredType]:
        if isinstance(v, str):
            # Parse JSON string into list of dicts and validate with pydantic
            types_list = InferredTypes.validate_json(v)
            return types_list
        return v
