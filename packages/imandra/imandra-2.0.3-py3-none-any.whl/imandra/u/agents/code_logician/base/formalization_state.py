import copy
from enum import Enum
from typing import TypedDict

from pydantic import BaseModel, Field
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from .context import ConversionFailureInfo, ConversionSourceInfo
from .imandrax import EvalRes
from .iml import IMLSymbol, Opaqueness
from .region_decomp import RegionDecomp
from .vg import VG


class FormalizationStatus(str, Enum):
    UNKNOWN = "unknown"
    INADMISSIBLE = "inadmissible"
    ADMITTED_WITH_OPAQUENESS = "admitted_with_opaqueness"
    EXECUTABLE_WITH_APPROXIMATION = "executable_with_approximation"
    TRANSPARENT = "transparent"

    def __rich__(self) -> Text:
        status_colors = {
            FormalizationStatus.UNKNOWN: "dim",
            FormalizationStatus.INADMISSIBLE: "bright_red",
            FormalizationStatus.ADMITTED_WITH_OPAQUENESS: "bright_cyan",
            FormalizationStatus.EXECUTABLE_WITH_APPROXIMATION: "bright_yellow",
            FormalizationStatus.TRANSPARENT: "light_green",
        }
        status_color = status_colors[self]
        return Text(self.name, style=status_color)

    def __repr__(self) -> str:
        return self.value.capitalize()


class FormalizationState(BaseModel):
    status: FormalizationStatus = Field(
        description="The status of the formalization",
        default=FormalizationStatus.UNKNOWN,
    )
    src_code: str = Field(description="Source program")
    src_lang: str = Field(description="Source language")
    refactored_code: list[tuple[str, str]] = Field(
        [], description="Refactored code. A list of (step_name, refactored_code) pairs"
    )

    conversion_source_info: ConversionSourceInfo | None = Field(
        None,
        description=(
            "Context retrieved based on the source code. "
            "Includes conversion examples for the source language, "
            "relevant examples, IML API references, and missing functions."
        ),
    )
    conversion_failures_info: list[ConversionFailureInfo] = Field(
        [],
        description=(
            "Context retrieved based on conversion failures. "
            "Used for re-try conversion. Includes evaluation errors, "
            "similar error-suggestions pairs, and additional context."
        ),
    )

    iml_code: str | None = Field(None, description="IML code")
    iml_symbols: list[IMLSymbol] = Field([], description="IML symbols in the IML code")
    opaques: list[Opaqueness] = Field(
        [], description="Opaque functions in the IML code"
    )
    eval_res: EvalRes | None = Field(None, description="Evaluation result")

    vgs: list[VG] = Field([], description="Verification goals")
    region_decomps: list[RegionDecomp] = Field([], description="Region decompositions")

    @property
    def test_cases(self) -> dict[str, dict[str, list[dict]]]:
        """
        {func_name: [{test_case_i: {args: ..., expected_output: ...}}, ...]}
        """
        region_decomps = self.region_decomps
        res = {}
        for i, decomp in enumerate(region_decomps, 1):
            func_name = decomp.data.name
            test_cases = decomp.test_cases
            if test_cases is None:
                continue
            elif "src" in test_cases:
                test_cases: list[dict] = copy.deepcopy(test_cases["src"])
            else:
                test_cases: list[dict] = copy.deepcopy(test_cases["iml"])
            for i, test_case in enumerate(test_cases, 1):
                test_case["name"] = f"test_case_{i}"
                test_case.pop("docstr", None)
            res[func_name] = test_cases
        return res

    def __rich__(self) -> Panel:
        def _truncate_code(
            code: str | None, max_lines: int = 8, max_chars: int = 200
        ) -> str:
            """Smart truncation for code that preserves readability"""
            if code is None:
                return "None"

            lines = code.split("\n")
            if len(lines) <= max_lines and len(code) <= max_chars:
                return code

            if len(lines) > max_lines:
                truncated_lines = lines[:max_lines]
                remaining_lines = len(lines) - max_lines
                return (
                    "\n".join(truncated_lines) + f"\n... ({remaining_lines} more lines)"
                )
            else:
                return code[:max_chars] + f"... ({len(code) - max_chars} more chars)"

        content_parts = []

        status_text = Text("Status: ", style="bold") + self.status.__rich__()
        content_parts.append(status_text)

        if self.src_code:
            src_truncated = _truncate_code(self.src_code)
            content_parts.append(
                Text(f"\nSource Code ({self.src_lang}):", style="bold")
            )
            content_parts.append(Text(src_truncated, style="dim"))

        if self.refactored_code:
            content_parts.append(
                Text(
                    f"\nRefactored: {len(self.refactored_code)} step(s)",
                    style="bright_cyan",
                )
            )

        content_parts.append(Text("\nIML Code:", style="bold"))
        if self.iml_code:
            iml_truncated = _truncate_code(self.iml_code)
            content_parts.append(Text(iml_truncated, style="dim"))
        else:
            content_parts.append(Text("None", style="dim"))

        eval_part = Text("\nEval: ", style="bold")
        if self.eval_res:
            if self.eval_res.errors is None or len(self.eval_res.errors) == 0:
                eval_part += Text("Success", style="light_green")
            else:
                eval_part += Text("Failed", style="red")
                eval_part += Text(f" ({len(self.eval_res.errors)})", style="red")
        else:
            eval_part += Text("None", style="dim")
        content_parts.append(eval_part)

        if self.iml_symbols:
            content_parts.append(
                Text(f"\nIML Symbols ({len(self.iml_symbols)}):", style="bold")
            )
            symbols_table = Table(show_header=False, box=None, padding=(0, 1))
            for i, sym in enumerate(self.iml_symbols[:10], 1):
                opaque_marker = (
                    "[bright_red]●[/bright_red]"
                    if sym.opaque
                    else "[bright_green]●[/bright_green]"
                )
                symbols_table.add_row(f"{i}.", f"{opaque_marker} {sym.name}")
            if len(self.iml_symbols) > 10:
                symbols_table.add_row(
                    "...", f"[dim]({len(self.iml_symbols) - 10} more)[/dim]"
                )
            content_parts.append(symbols_table)

        if self.opaques:
            content_parts.append(
                Text(f"\nOpaque Functions ({len(self.opaques)}):", style="bold")
            )
            opaques_table = Table(show_header=False, box=None, padding=(0, 1))
            for i, opa in enumerate(self.opaques[:5], 1):
                assumptions_count = (
                    len(opa.assumptions) if hasattr(opa, "assumptions") else 0
                )
                has_approx = (
                    hasattr(opa, "approximation") and opa.approximation is not None
                )
                status_icon = (
                    "[bright_green]✓[/bright_green]"
                    if has_approx
                    else "[bright_yellow]○[/bright_yellow]"
                )
                opaques_table.add_row(
                    f"{i}.",
                    f"{status_icon} {opa.opaque_func}",
                    f"({assumptions_count} assumptions)",
                )
            if len(self.opaques) > 5:
                opaques_table.add_row(
                    "...", f"[dim]({len(self.opaques) - 5} more)[/dim]", ""
                )
            content_parts.append(opaques_table)

        analysis_parts = []
        if self.vgs:
            analysis_parts.append(f"VGs: {len(self.vgs)}")
        if self.region_decomps:
            analysis_parts.append(f"Region Decomps: {len(self.region_decomps)}")

        if analysis_parts:
            content_parts.append(Text(f"\nAnalysis: {' | '.join(analysis_parts)}"))

        context_parts = []
        context_parts.append(Text("\nContext Data: ", style="bold"))
        source_info_size = (
            len(self.conversion_source_info.model_dump_json())
            if self.conversion_source_info is not None
            else 0
        )
        failures_info_size = sum(
            len(f.model_dump_json()) for f in self.conversion_failures_info
        )
        context_parts.append(Text(f"  source  : {source_info_size:>8,} bytes"))
        context_parts.append(Text(f"  failures: {failures_info_size:>8,} bytes"))
        content_parts.append(Group(*context_parts))

        content_group = Group(*content_parts)
        panel = Panel(
            content_group,
            title="Formalization State",
        )
        return panel


class FormalizationStateUpdate(TypedDict, total=False):
    status: FormalizationStatus
    src_code: str
    src_lang: str
    refactored_code: list[tuple[str, str]]

    conversion_source_info: ConversionSourceInfo | None
    conversion_failures_info: list[ConversionFailureInfo]

    iml_code: str | None
    iml_symbols: list[IMLSymbol]
    opaques: list[Opaqueness]
    eval_res: EvalRes | None

    vgs: list[VG]
    region_decomps: list[RegionDecomp]
