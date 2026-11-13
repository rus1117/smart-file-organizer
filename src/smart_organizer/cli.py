"""Command-line interface for Smart File Organizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from smart_organizer.config import OrganizerConfig
from smart_organizer.organizer import (
    OrganizeSummary,
    organize_directory,
    undo_last_organize,
)


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI argument parser."""
    parser = argparse.ArgumentParser(
        prog="smart-organizer",
        description="Sort files in Downloads or any target directory into category folders.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        type=Path,
        default=Path.home() / "Downloads",
        help="Directory to organize (defaults to ~/Downloads).",
    )
    parser.add_argument(
        "-n",
        "--dry-run",
        action="store_true",
        help="Preview planned file moves without modifying the filesystem.",
    )
    parser.add_argument(
        "-d",
        "--by-date",
        action="store_true",
        help="Group files inside each category into YYYY-MM subfolders.",
    )
    parser.add_argument(
        "-c",
        "--config",
        type=Path,
        default=None,
        help="Path to a custom JSON configuration file.",
    )
    parser.add_argument(
        "--undo",
        action="store_true",
        help="Revert the most recent organization run in the target directory.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Print every file action and skip reason.",
    )
    return parser


def _print_summary(summary: OrganizeSummary, *, undo: bool, verbose: bool) -> None:
    if verbose or summary.dry_run:
        for record in summary.records:
            if record.status in {"moved", "planned"} and record.destination is not None:
                rel_dest = record.destination.relative_to(summary.target_dir)
                tag = "PLAN" if record.status == "planned" else "MOVE"
                print(f"[{tag}] {record.source.name} -> {rel_dest}")
            elif verbose and record.status == "skipped":
                reason = f" ({record.reason})" if record.reason else ""
                print(f"[SKIP] {record.source.name}{reason}")

    if undo:
        print(
            f"Undo complete in {summary.target_dir}: "
            f"{summary.moved_count} restored, {summary.skipped_count} skipped."
        )
        return

    if summary.dry_run:
        print(
            f"Dry run for {summary.target_dir}: "
            f"{summary.planned_count} would move, {summary.skipped_count} skipped."
        )
    else:
        print(
            f"Organized {summary.target_dir}: "
            f"{summary.moved_count} moved, {summary.skipped_count} skipped."
        )

    counts = summary.category_counts()
    if counts:
        breakdown = ", ".join(f"{name}: {count}" for name, count in counts.items())
        print(f"Categories: {breakdown}")


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point returning an exit status code."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        if args.undo:
            summary = undo_last_organize(args.target)
            _print_summary(summary, undo=True, verbose=args.verbose)
            return 0

        config = (
            OrganizerConfig.from_json_file(args.config)
            if args.config is not None
            else OrganizerConfig()
        )
        summary = organize_directory(
            args.target,
            config=config,
            by_date=args.by_date,
            dry_run=args.dry_run,
        )
        _print_summary(summary, undo=False, verbose=args.verbose)
        return 0
    except (FileNotFoundError, NotADirectoryError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
