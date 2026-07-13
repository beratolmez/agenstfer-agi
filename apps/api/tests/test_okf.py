import io
import stat
import zipfile
from pathlib import Path

import pytest
from agi_server.okf import FileSystemOKFBundle, OKFConcept


def concept(path: str = "accounts/atlas.md") -> OKFConcept:
    return OKFConcept(
        path=path,
        frontmatter={
            "type": "VendorSpecificAccount",
            "title": "Atlas",
            "description": "Unknown type test.",
            "timestamp": "2026-07-13T12:00:00Z",
            "vendor_extension": {"keep": True, "nested": [1, 2]},
            "agi": {"sensitivity": "internal"},
        },
        body="# Atlas\n\n[Missing](/references/missing.md)\n",
    )


def test_unknown_type_and_metadata_round_trip(tmp_path: Path):
    bundle = FileSystemOKFBundle(tmp_path / "bundle")
    bundle.create("Test")
    bundle.write(concept())
    loaded = bundle.read("accounts/atlas.md")
    assert loaded.type == "VendorSpecificAccount"
    assert loaded.frontmatter["vendor_extension"] == {"keep": True, "nested": [1, 2]}


def test_broken_link_is_warning_not_conformance_error(tmp_path: Path):
    bundle = FileSystemOKFBundle(tmp_path / "bundle")
    bundle.create("Test")
    bundle.write(concept())
    report = bundle.validate()
    assert report.valid
    assert any(item.code == "okf.broken_link" for item in report.warnings)


def test_empty_type_is_rejected_by_strict_producer(tmp_path: Path):
    bundle = FileSystemOKFBundle(tmp_path / "bundle")
    bundle.create("Test")
    with pytest.raises(ValueError, match="type"):
        bundle.write(OKFConcept(path="bad.md", frontmatter={}, body="bad"))


def test_zip_export_import_preserves_concepts_and_blocks_traversal(tmp_path: Path):
    bundle = FileSystemOKFBundle(tmp_path / "bundle")
    bundle.create("Test")
    bundle.write(concept())
    payload = bundle.export_zip()
    imported = FileSystemOKFBundle.import_zip(payload, tmp_path / "imported")
    assert [item.model_dump() for item in imported.list_concepts()] == [
        item.model_dump() for item in bundle.list_concepts()
    ]


def test_zip_import_rejects_cumulative_limit_and_symlinks(tmp_path: Path):
    cumulative = io.BytesIO()
    with zipfile.ZipFile(cumulative, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("one.md", "a" * 120)
        archive.writestr("two.md", "b" * 120)
    with pytest.raises(ValueError, match="cumulative"):
        FileSystemOKFBundle.import_zip(cumulative.getvalue(), tmp_path / "too-large", 220)

    symlink = io.BytesIO()
    with zipfile.ZipFile(symlink, "w") as archive:
        info = zipfile.ZipInfo("link.md")
        info.create_system = 3
        info.external_attr = (stat.S_IFLNK | 0o777) << 16
        archive.writestr(info, "target.md")
    with pytest.raises(ValueError, match="symbolic"):
        FileSystemOKFBundle.import_zip(symlink.getvalue(), tmp_path / "symlink")
