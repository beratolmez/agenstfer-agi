from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class OKFConcept(BaseModel):
    path: str
    frontmatter: dict[str, Any]
    body: str = ""

    @property
    def concept_id(self) -> str:
        return self.path.removesuffix(".md").replace("\\", "/")

    @property
    def type(self) -> str | None:
        value = self.frontmatter.get("type")
        return str(value).strip() if value is not None else None

    @property
    def title(self) -> str:
        return str(self.frontmatter.get("title") or self.concept_id.rsplit("/", 1)[-1])


class ValidationFinding(BaseModel):
    level: Literal["error", "warning"]
    code: str
    path: str
    message: str


class ValidationReport(BaseModel):
    okf_version: str = "0.1"
    concepts_checked: int = 0
    errors: list[ValidationFinding] = Field(default_factory=list)
    warnings: list[ValidationFinding] = Field(default_factory=list)

    @property
    def valid(self) -> bool:
        return not self.errors

    def add(self, finding: ValidationFinding) -> None:
        (self.errors if finding.level == "error" else self.warnings).append(finding)
