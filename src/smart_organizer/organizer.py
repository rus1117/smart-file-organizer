"""Core file organization and undo operations."""

from __future__ import annotations

import json
import shutil
from collections import Counter
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from smart_organizer.config import OrganizerConfig

HISTORY_FILENAME = ".smart_organizer_history.json"


@dataclass(frozen=True)
class MoveRecord:
    """Represents a single file operation or skip decision."""

    source: Path
    destination: Path | None
    category: str
    status: str  # "moved", "planned", or "skipped"
    reason: str | None = None


@dataclass(frozen=True)
class OrganizeSummary:
    """Aggregated outcome of an organize or undo run."""

    target_dir: Path
    dry_run: bool
    records: tuple[MoveRecord, ...]

    @property
    def moved_count(self) -> int:
        return sum(1 for r in self.records if r.status == "moved")

    @property
    def planned_count(self) -> int:
        return sum(1 for r in self.records if r.status == "planned")

    @property
    def skipped_count(self) -> int:
        return sum(1 for r in self.records if r.status == "skipped")

    def category_counts(self) -> dict[str, int]:
        """Return counts of moved or planned files grouped by category."""
        counts = Counter(
            r.category for r in self.records if r.status in {"moved", "planned"}
        )
        return dict(sorted(counts.items()))


def resolve_conflict(
    destination: Path,
    reserved_paths: set[Path] | None = None,
) -> Path:
    """Return a non-colliding file path by appending a numeric suffix if needed."""
    reserved = reserved_paths if reserved_paths is not None else set()
    if not destination.exists() and destination not in reserved:
        return destination

    stem = destination.stem
    suffix = destination.suffix
    parent = destination.parent
    counter = 1
    while True:
        candidate = parent / f"{stem} ({counter}){suffix}"
        if not candidate.exists() and candidate not in reserved:
            return candidate
        counter += 1


def _build_destination(
    file_path: Path,
    target_dir: Path,
    category: str,
    by_date: bool,
) -> Path:
    dest_dir = target_dir / category
    if by_date:
        modified = datetime.fromtimestamp(file_path.stat().st_mtime)
        dest_dir = dest_dir / modified.strftime("%Y-%m")
    return dest_dir / file_path.name


def _write_history(history_path: Path, records: list[MoveRecord]) -> None:
    moved_entries = [
        {"source": str(r.source), "destination": str(r.destination)}
        for r in records
        if r.status == "moved" and r.destination is not None
    ]
    if not moved_entries:
        return

    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "moves": moved_entries,
    }
    history_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def organize_directory(
    target_dir: Path,
    config: OrganizerConfig | None = None,
    *,
    by_date: bool = False,
    dry_run: bool = False,
) -> OrganizeSummary:
    """Sort top-level files in target_dir into category subdirectories."""
    resolved_dir = target_dir.expanduser().resolve()
    if not resolved_dir.exists():
        raise FileNotFoundError(f"Target directory does not exist: {resolved_dir}")
    if not resolved_dir.is_dir():
        raise NotADirectoryError(f"Target path is not a directory: {resolved_dir}")

    active_config = config or OrganizerConfig()
    records: list[MoveRecord] = []
    reserved_destinations: set[Path] = set()

    entries = sorted(resolved_dir.iterdir(), key=lambda p: p.name.lower())
    for entry in entries:
        if entry.is_dir() or entry.is_symlink():
            continue

        if active_config.should_ignore(entry):
            records.append(
                MoveRecord(
                    source=entry,
                    destination=None,
                    category="Ignored",
                    status="skipped",
                    reason="ignored rule",
                )
            )
            continue

        category = active_config.category_for(entry)
        raw_dest = _build_destination(entry, resolved_dir, category, by_date)
        final_dest = resolve_conflict(raw_dest, reserved_destinations)
        reserved_destinations.add(final_dest)

        if dry_run:
            records.append(
                MoveRecord(
                    source=entry,
                    destination=final_dest,
                    category=category,
                    status="planned",
                )
            )
            continue

        try:
            final_dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(entry), str(final_dest))
            records.append(
                MoveRecord(
                    source=entry,
                    destination=final_dest,
                    category=category,
                    status="moved",
                )
            )
        except OSError as exc:
            records.append(
                MoveRecord(
                    source=entry,
                    destination=final_dest,
                    category=category,
                    status="skipped",
                    reason=str(exc),
                )
            )

    if not dry_run:
        _write_history(resolved_dir / HISTORY_FILENAME, records)

    return OrganizeSummary(
        target_dir=resolved_dir,
        dry_run=dry_run,
        records=tuple(records),
    )


def _remove_empty_parents(start_dir: Path, stop_dir: Path) -> None:
    current = start_dir
    while current != stop_dir and stop_dir in current.parents:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def undo_last_organize(target_dir: Path) -> OrganizeSummary:
    """Revert the most recent organize_directory run using its history file."""
    resolved_dir = target_dir.expanduser().resolve()
    history_path = resolved_dir / HISTORY_FILENAME
    if not history_path.is_file():
        raise FileNotFoundError(f"No undo history found in: {resolved_dir}")

    try:
        payload = json.loads(history_path.read_text(encoding="utf-8"))
        moves = payload.get("moves", [])
    except (json.JSONDecodeError, AttributeError) as exc:
        raise ValueError(f"Corrupted undo history in {history_path}: {exc}") from exc

    records: list[MoveRecord] = []
    for item in reversed(moves):
        src = Path(item["destination"])
        orig = Path(item["source"])
        if not src.exists():
            records.append(
                MoveRecord(
                    source=src,
                    destination=orig,
                    category="Undo",
                    status="skipped",
                    reason="file missing",
                )
            )
            continue

        restore_target = resolve_conflict(orig)
        try:
            restore_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(restore_target))
            _remove_empty_parents(src.parent, resolved_dir)
            records.append(
                MoveRecord(
                    source=src,
                    destination=restore_target,
                    category="Undo",
                    status="moved",
                )
            )
        except OSError as exc:
            records.append(
                MoveRecord(
                    source=src,
                    destination=restore_target,
                    category="Undo",
                    status="skipped",
                    reason=str(exc),
                )
            )

    history_path.unlink(missing_ok=True)
    return OrganizeSummary(
        target_dir=resolved_dir,
        dry_run=False,
        records=tuple(records),
    )
