"""Unit and CLI tests for Smart File Organizer."""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from smart_organizer.cli import main
from smart_organizer.config import OrganizerConfig
from smart_organizer.organizer import (
    HISTORY_FILENAME,
    organize_directory,
    undo_last_organize,
)


def test_organize_sorts_known_and_unknown_extensions(tmp_path: Path) -> None:
    (tmp_path / "photo.JPG").write_bytes(b"img")
    (tmp_path / "report.pdf").write_bytes(b"pdf")
    (tmp_path / "archive.zip").write_bytes(b"zip")
    (tmp_path / "notes.unknownext").write_text("misc", encoding="utf-8")

    summary = organize_directory(tmp_path)

    assert summary.moved_count == 4
    assert summary.skipped_count == 0
    assert (tmp_path / "Images" / "photo.JPG").is_file()
    assert (tmp_path / "Documents" / "report.pdf").is_file()
    assert (tmp_path / "Archives" / "archive.zip").is_file()
    assert (tmp_path / "Other" / "notes.unknownext").is_file()
    assert (tmp_path / HISTORY_FILENAME).is_file()


def test_organize_ignores_partial_downloads_and_directories(tmp_path: Path) -> None:
    (tmp_path / "movie.mp4.crdownload").write_bytes(b"partial")
    (tmp_path / "setup.part").write_bytes(b"partial")
    (tmp_path / "desktop.ini").write_text("win", encoding="utf-8")
    existing_dir = tmp_path / "MyProject"
    existing_dir.mkdir()
    (existing_dir / "main.py").write_text("print(1)", encoding="utf-8")

    summary = organize_directory(tmp_path)

    assert summary.moved_count == 0
    assert summary.skipped_count == 3
    assert (tmp_path / "movie.mp4.crdownload").exists()
    assert (tmp_path / "setup.part").exists()
    assert (tmp_path / "desktop.ini").exists()
    assert (existing_dir / "main.py").exists()


def test_organize_resolves_filename_collisions(tmp_path: Path) -> None:
    docs_dir = tmp_path / "Documents"
    docs_dir.mkdir()
    (docs_dir / "invoice.pdf").write_text("old", encoding="utf-8")
    (tmp_path / "invoice.pdf").write_text("new", encoding="utf-8")

    summary = organize_directory(tmp_path)

    assert summary.moved_count == 1
    assert (docs_dir / "invoice.pdf").read_text(encoding="utf-8") == "old"
    assert (docs_dir / "invoice (1).pdf").read_text(encoding="utf-8") == "new"


def test_dry_run_does_not_modify_files_and_plans_collisions(tmp_path: Path) -> None:
    docs_dir = tmp_path / "Documents"
    docs_dir.mkdir()
    (docs_dir / "plan.txt").write_text("existing", encoding="utf-8")
    (tmp_path / "plan.txt").write_text("incoming", encoding="utf-8")

    summary = organize_directory(tmp_path, dry_run=True)

    assert summary.dry_run is True
    assert summary.planned_count == 1
    assert summary.moved_count == 0
    assert (tmp_path / "plan.txt").is_file()
    assert not (docs_dir / "plan (1).txt").exists()
    assert not (tmp_path / HISTORY_FILENAME).exists()
    assert summary.records[0].destination == docs_dir / "plan (1).txt"


def test_organize_by_date_groups_into_year_month(tmp_path: Path) -> None:
    sample = tmp_path / "song.mp3"
    sample.write_bytes(b"audio")
    target_ts = datetime(2025, 4, 15, 12, 0, 0).timestamp()
    os.utime(sample, (target_ts, target_ts))

    summary = organize_directory(tmp_path, by_date=True)

    assert summary.moved_count == 1
    assert (tmp_path / "Audio" / "2025-04" / "song.mp3").is_file()


def test_undo_restores_files_and_cleans_empty_folders(tmp_path: Path) -> None:
    (tmp_path / "script.py").write_text("x = 1", encoding="utf-8")
    (tmp_path / "logo.png").write_bytes(b"png")

    organize_directory(tmp_path, by_date=True)
    assert not (tmp_path / "script.py").exists()

    undo_summary = undo_last_organize(tmp_path)

    assert undo_summary.moved_count == 2
    assert (tmp_path / "script.py").read_text(encoding="utf-8") == "x = 1"
    assert (tmp_path / "logo.png").read_bytes() == b"png"
    assert not (tmp_path / "Code").exists()
    assert not (tmp_path / "Images").exists()
    assert not (tmp_path / HISTORY_FILENAME).exists()


def test_custom_config_loading_and_validation(tmp_path: Path) -> None:
    cfg_file = tmp_path / "custom.json"
    cfg_file.write_text(
        json.dumps(
            {
                "categories": {"Models": ["stl", ".obj"]},
                "ignore_extensions": [".bak"],
                "fallback_category": "Misc",
            }
        ),
        encoding="utf-8",
    )

    config = OrganizerConfig.from_json_file(cfg_file)
    assert config.category_for(Path("part.STL")) == "Models"
    assert config.category_for(Path("readme.txt")) == "Misc"
    assert config.should_ignore(Path("data.bak")) is True
    assert config.should_ignore(Path(HISTORY_FILENAME)) is True

    bad_cfg = tmp_path / "bad.json"
    bad_cfg.write_text("{not valid json", encoding="utf-8")
    with pytest.raises(ValueError):
        OrganizerConfig.from_json_file(bad_cfg)


def test_cli_end_to_end(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    (tmp_path / "notes.md").write_text("# Hi", encoding="utf-8")

    exit_code = main([str(tmp_path), "--dry-run"])
    out = capsys.readouterr().out
    assert exit_code == 0
    assert "[PLAN] notes.md" in out
    assert (tmp_path / "notes.md").exists()

    exit_code = main([str(tmp_path)])
    assert exit_code == 0
    assert (tmp_path / "Documents" / "notes.md").is_file()

    exit_code = main([str(tmp_path), "--undo"])
    assert exit_code == 0
    assert (tmp_path / "notes.md").is_file()


def test_cli_returns_nonzero_for_missing_directory(tmp_path: Path) -> None:
    missing = tmp_path / "does_not_exist"
    assert main([str(missing)]) == 1
