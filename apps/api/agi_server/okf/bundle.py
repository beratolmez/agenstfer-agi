from __future__ import annotations

import io
import re
import stat
import zipfile
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath

import yaml

from agi_server.okf.models import OKFConcept, ValidationFinding, ValidationReport

FRONTMATTER_PATTERN = re.compile(r"\A---\s*\r?\n(.*?)\r?\n---\s*(?:\r?\n|\Z)(.*)\Z", re.DOTALL)
LINK_PATTERN = re.compile(r"(?<!!)\[[^\]]+\]\(([^)\s]+)(?:\s+[^)]*)?\)")
RESERVED = {"index.md", "log.md"}
QUALITY_FIELDS = ("title", "description", "timestamp")


def parse_concept(path: str, text: str) -> OKFConcept:
    match = FRONTMATTER_PATTERN.match(text.lstrip("\ufeff"))
    if not match:
        return OKFConcept(path=path, frontmatter={}, body=text)
    raw = yaml.safe_load(match.group(1)) or {}
    if not isinstance(raw, dict):
        raise ValueError(f"{path}: YAML frontmatter mapping olmalıdır")
    return OKFConcept(path=path, frontmatter=raw, body=match.group(2).rstrip() + "\n")


def render_concept(concept: OKFConcept) -> str:
    frontmatter = yaml.safe_dump(
        concept.frontmatter,
        allow_unicode=True,
        sort_keys=False,
        default_flow_style=False,
    ).strip()
    return f"---\n{frontmatter}\n---\n\n{concept.body.lstrip()}".rstrip() + "\n"


class FileSystemOKFBundle:
    """OKF 0.1 adapter: strict producer, tolerant consumer."""

    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()

    def create(self, title: str) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        if not (self.root / "index.md").exists():
            self.write(
                OKFConcept(
                    path="index.md",
                    frontmatter={"okf_version": "0.1", "title": title},
                    body=f"# {title}\n\nTaşınabilir şirket bilgi bundle'ı.\n",
                )
            )
        if not (self.root / "log.md").exists():
            self.write(OKFConcept(path="log.md", frontmatter={}, body="# Değişiklik Günlüğü\n"))

    def _safe_path(self, relative_path: str) -> Path:
        normalized = PurePosixPath(relative_path.replace("\\", "/"))
        if normalized.is_absolute() or ".." in normalized.parts:
            raise ValueError("Bundle yolu root dışına çıkamaz")
        target = (self.root / Path(*normalized.parts)).resolve()
        if not target.is_relative_to(self.root):
            raise ValueError("Bundle yolu root dışına çıkamaz")
        return target

    def read(self, path: str) -> OKFConcept:
        target = self._safe_path(path)
        return parse_concept(path.replace("\\", "/"), target.read_text(encoding="utf-8"))

    def write(self, concept: OKFConcept) -> None:
        target = self._safe_path(concept.path)
        if target.suffix.lower() != ".md":
            raise ValueError("OKF concept UTF-8 Markdown olmalıdır")
        if target.name not in RESERVED and not concept.type:
            raise ValueError("OKF producer boş type yazamaz")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(render_concept(concept), encoding="utf-8", newline="\n")

    def list_concepts(self) -> list[OKFConcept]:
        if not self.root.exists():
            return []
        return [
            self.read(path.relative_to(self.root).as_posix())
            for path in sorted(self.root.rglob("*.md"))
            if path.is_file()
        ]

    @staticmethod
    def links(concept: OKFConcept) -> list[str]:
        return [match.group(1).split("#", 1)[0] for match in LINK_PATTERN.finditer(concept.body)]

    def _resolve_link(self, source: OKFConcept, link: str) -> str | None:
        if not link or link.startswith(("http://", "https://", "mailto:", "urn:", "#")):
            return None
        if link.startswith("/"):
            result = PurePosixPath(link.lstrip("/"))
        else:
            result = PurePosixPath(source.path).parent / link
        parts: list[str] = []
        for part in result.parts:
            if part == "..":
                if parts:
                    parts.pop()
            elif part != ".":
                parts.append(part)
        normalized = PurePosixPath(*parts).as_posix()
        return normalized if normalized.endswith(".md") else f"{normalized}.md"

    def backlinks(self) -> dict[str, list[str]]:
        result: dict[str, list[str]] = defaultdict(list)
        for concept in self.list_concepts():
            for link in self.links(concept):
                target = self._resolve_link(concept, link)
                if target:
                    result[target].append(concept.path)
        return dict(result)

    def validate(self, quality: bool = True) -> ValidationReport:
        report = ValidationReport()
        concepts = self.list_concepts()
        report.concepts_checked = len(concepts)
        existing = {concept.path for concept in concepts}
        root_index = next((item for item in concepts if item.path == "index.md"), None)
        if not root_index or str(root_index.frontmatter.get("okf_version")) != "0.1":
            report.add(
                ValidationFinding(
                    level="error",
                    code="okf.root_version",
                    path="index.md",
                    message='Root index okf_version: "0.1" içermelidir.',
                )
            )
        for concept in concepts:
            if concept.path not in RESERVED and not concept.type:
                report.add(
                    ValidationFinding(
                        level="error",
                        code="okf.type_required",
                        path=concept.path,
                        message="Concept type boş olamaz.",
                    )
                )
            if quality and concept.path not in RESERVED:
                for field in QUALITY_FIELDS:
                    if not concept.frontmatter.get(field):
                        report.add(
                            ValidationFinding(
                                level="warning",
                                code=f"agi.{field}_missing",
                                path=concept.path,
                                message=f"Quality gate '{field}' alanını önerir.",
                            )
                        )
                agi = concept.frontmatter.get("agi")
                if not isinstance(agi, dict) or not agi.get("sensitivity"):
                    report.add(
                        ValidationFinding(
                            level="warning",
                            code="agi.sensitivity_missing",
                            path=concept.path,
                            message="agi.sensitivity etiketi bulunmuyor.",
                        )
                    )
            for link in self.links(concept):
                target = self._resolve_link(concept, link)
                if target and target not in existing:
                    report.add(
                        ValidationFinding(
                            level="warning",
                            code="okf.broken_link",
                            path=concept.path,
                            message=f"Çözülemeyen link: {link}",
                        )
                    )
        return report

    def update_log(self, summary: str) -> None:
        path = self.root / "log.md"
        current = (
            self.read("log.md")
            if path.exists()
            else OKFConcept(path="log.md", frontmatter={}, body="# Değişiklik Günlüğü\n")
        )
        stamp = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
        header, *rest = current.body.splitlines()
        body = "\n".join(
            [header or "# Değişiklik Günlüğü", "", f"- {stamp} — {summary}", *rest[1:]]
        )
        self.write(current.model_copy(update={"body": body.rstrip() + "\n"}))

    def generate_index(self) -> None:
        groups: dict[str, list[OKFConcept]] = defaultdict(list)
        for concept in self.list_concepts():
            if concept.path not in RESERVED:
                groups[PurePosixPath(concept.path).parts[0]].append(concept)
        lines = ["# Company Knowledge Bundle", "", "OKF 0.1 progressive-disclosure index.", ""]
        for group, concepts in sorted(groups.items()):
            lines.extend([f"## {group.replace('-', ' ').title()}", ""])
            lines.extend(f"- [{concept.title}](/%s)" % concept.path for concept in concepts)
            lines.append("")
        index = self.read("index.md")
        self.write(index.model_copy(update={"body": "\n".join(lines)}))

    def export_zip(self) -> bytes:
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(self.root.rglob("*.md")):
                if path.is_file() and ".git" not in path.relative_to(self.root).parts:
                    archive.write(path, path.relative_to(self.root).as_posix())
        return buffer.getvalue()

    @classmethod
    def import_zip(
        cls, payload: bytes, destination: Path | str, max_bytes: int = 50_000_000
    ) -> FileSystemOKFBundle:
        if len(payload) > max_bytes:
            raise ValueError("OKF archive boyut sınırını aşıyor")
        bundle = cls(destination)
        bundle.root.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            if len(archive.infolist()) > 10_000:
                raise ValueError("OKF archive entry count limit exceeded")
            total_size = 0
            for info in archive.infolist():
                path = PurePosixPath(info.filename)
                if path.is_absolute() or ".." in path.parts:
                    raise ValueError("OKF archive path traversal içeriyor")
                if info.file_size > max_bytes:
                    raise ValueError("OKF archive entry boyut sınırını aşıyor")
                if ".git" in path.parts:
                    raise ValueError("OKF archive cannot contain Git internals")
                if stat.S_ISLNK(info.external_attr >> 16):
                    raise ValueError("OKF archive cannot contain symbolic links")
                total_size += info.file_size
                if total_size > max_bytes:
                    raise ValueError("OKF archive cumulative size limit exceeded")
                if not info.is_dir() and path.suffix.lower() != ".md":
                    raise ValueError("OKF archive can only contain Markdown concepts")
                target = bundle._safe_path(info.filename)
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(info))
        return bundle
