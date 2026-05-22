"""Tests for envoy_local.exporter."""

from __future__ import annotations

import os
import pytest
import yaml

from envoy_local.exporter import (
    ExportResult,
    ExportError,
    export_to_file,
    export_to_directory,
    copy_export,
)


SAMPLE_BOOTSTRAP = {
    "static_resources": {
        "clusters": [{"name": "test_cluster", "connect_timeout": "0.25s"}],
        "listeners": [],
    }
}


@pytest.fixture()
def out_dir(tmp_path):
    return str(tmp_path / "output")


def test_export_to_file_creates_file(out_dir):
    dest = os.path.join(out_dir, "bootstrap.yaml")
    result = export_to_file(SAMPLE_BOOTSTRAP, dest)
    assert os.path.isfile(dest)
    assert result.bytes_written > 0
    assert result.format == "yaml"


def test_export_to_file_valid_yaml(out_dir):
    dest = os.path.join(out_dir, "bootstrap.yaml")
    export_to_file(SAMPLE_BOOTSTRAP, dest)
    with open(dest, encoding="utf-8") as fh:
        parsed = yaml.safe_load(fh)
    assert "static_resources" in parsed


def test_export_to_file_no_overwrite_raises(out_dir):
    dest = os.path.join(out_dir, "bootstrap.yaml")
    export_to_file(SAMPLE_BOOTSTRAP, dest)
    with pytest.raises(ExportError, match="overwrite=False"):
        export_to_file(SAMPLE_BOOTSTRAP, dest, overwrite=False)


def test_export_to_file_overwrites_by_default(out_dir):
    dest = os.path.join(out_dir, "bootstrap.yaml")
    export_to_file(SAMPLE_BOOTSTRAP, dest)
    result = export_to_file(SAMPLE_BOOTSTRAP, dest, overwrite=True)
    assert result.bytes_written > 0


def test_export_result_summary(out_dir):
    dest = os.path.join(out_dir, "bootstrap.yaml")
    result = export_to_file(SAMPLE_BOOTSTRAP, dest)
    summary = result.summary()
    assert "Exported" in summary
    assert dest in summary or str(result.destination) in summary


def test_export_to_directory_creates_multiple_files(tmp_path):
    out = str(tmp_path / "multi")
    configs = {
        "alpha": SAMPLE_BOOTSTRAP,
        "beta": SAMPLE_BOOTSTRAP,
    }
    results = export_to_directory(configs, out)
    assert len(results) == 2
    names = {os.path.basename(r.destination) for r in results}
    assert "alpha.yaml" in names
    assert "beta.yaml" in names


def test_export_to_directory_appends_yaml_extension(tmp_path):
    out = str(tmp_path / "ext_test")
    export_to_directory({"myconfig": SAMPLE_BOOTSTRAP}, out)
    assert os.path.isfile(os.path.join(out, "myconfig.yaml"))


def test_copy_export_copies_file(tmp_path):
    src = tmp_path / "src.yaml"
    src.write_text("static_resources: {}\n", encoding="utf-8")
    dst = str(tmp_path / "sub" / "dst.yaml")
    result = copy_export(str(src), dst)
    assert os.path.isfile(dst)
    assert result.bytes_written > 0


def test_copy_export_missing_source_raises(tmp_path):
    with pytest.raises(ExportError, match="Source file not found"):
        copy_export(str(tmp_path / "ghost.yaml"), str(tmp_path / "out.yaml"))


def test_copy_export_no_overwrite_raises(tmp_path):
    src = tmp_path / "src.yaml"
    src.write_text("static_resources: {}\n", encoding="utf-8")
    dst = tmp_path / "dst.yaml"
    dst.write_text("existing", encoding="utf-8")
    with pytest.raises(ExportError, match="overwrite=False"):
        copy_export(str(src), str(dst), overwrite=False)
