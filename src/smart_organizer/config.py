"""Configuration loading and validation for Smart File Organizer."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_CATEGORIES: dict[str, tuple[str, ...]] = {
    "Images": (".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg", ".bmp", ".ico", ".heic"),
    "Documents": (
        ".pdf",
        ".doc",
        ".docx",
        ".txt",
        ".md",
        ".rtf",
        ".odt",
        ".csv",
        ".xlsx",
        ".xls",
        ".pptx",
        ".ppt",
    ),
    "Archives": (".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz"),
    "Audio": (".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"),
    "Video": (".mp4", ".mkv", ".avi", ".mov", ".webm", ".wmv"),
    "Code": (
        ".py",
        ".js",
        ".ts",
        ".html",
        ".css",
        ".json",
        ".yaml",
        ".yml",
        ".xml",
        ".sql",
        ".sh",
        ".bat",
        ".ps1",
    ),
    "Installers": (".exe", ".msi", ".dmg", ".pkg", ".deb", ".rpm", ".apk"),
}

DEFAULT_IGNORE_EXTENSIONS: frozenset[str] = frozenset(
    {".crdownload", ".part", ".tmp", ".download"}
)

DEFAULT_IGNORE_NAMES: frozenset[str] = frozenset(
    {"desktop.ini", ".ds_store", "thumbs.db", ".smart_organizer_history.json"}
)


def _normalize_extension(ext: str) -> str:
    cleaned = ext.strip().lower()
    if not cleaned:
        raise ValueError("Extension must not be empty.")
    return cleaned if cleaned.startswith(".") else f".{cleaned}"


def _build_extension_index(
    categories: dict[str, tuple[str, ...]],
) -> dict[str, str]:
    index: dict[str, str] = {}
    for category, extensions in categories.items():
        for ext in extensions:
            index[ext] = category
    return index


@dataclass(frozen=True)
class OrganizerConfig:
    """Rules for categorizing and filtering files."""

    categories: dict[str, tuple[str, ...]] = field(
        default_factory=lambda: dict(DEFAULT_CATEGORIES)
    )
    ignore_extensions: frozenset[str] = DEFAULT_IGNORE_EXTENSIONS
    ignore_names: frozenset[str] = DEFAULT_IGNORE_NAMES
    fallback_category: str = "Other"
    _extension_index: dict[str, str] = field(init=False, repr=False)

    def __post_init__(self) -> None:
        normalized_categories: dict[str, tuple[str, ...]] = {}
        for category, extensions in self.categories.items():
            clean_name = category.strip()
            if not clean_name:
                raise ValueError("Category name must not be empty.")
            normalized_categories[clean_name] = tuple(
                _normalize_extension(ext) for ext in extensions
            )

        fallback = self.fallback_category.strip()
        if not fallback:
            raise ValueError("fallback_category must not be empty.")

        object.__setattr__(self, "categories", normalized_categories)
        object.__setattr__(
            self,
            "ignore_extensions",
            frozenset(_normalize_extension(ext) for ext in self.ignore_extensions),
        )
        object.__setattr__(
            self,
            "ignore_names",
            frozenset(name.strip().lower() for name in self.ignore_names if name.strip()),
        )
        object.__setattr__(self, "fallback_category", fallback)
        object.__setattr__(
            self, "_extension_index", _build_extension_index(normalized_categories)
        )

    def category_for(self, path: Path) -> str:
        """Return the target category name for a file path."""
        return self._extension_index.get(path.suffix.lower(), self.fallback_category)

    def should_ignore(self, path: Path) -> bool:
        """Return True if the file should be skipped during organization."""
        if path.name.lower() in self.ignore_names:
            return True
        if path.suffix.lower() in self.ignore_extensions:
            return True
        return False

    @classmethod
    def from_json_file(cls, path: Path) -> OrganizerConfig:
        """Load and validate an OrganizerConfig from a JSON file."""
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in config file {path}: {exc}") from exc

        if not isinstance(raw, dict):
            raise ValueError("Config root must be a JSON object.")

        categories_raw = raw.get("categories", DEFAULT_CATEGORIES)
        if not isinstance(categories_raw, dict):
            raise ValueError("'categories' must be an object mapping names to extension lists.")

        categories: dict[str, tuple[str, ...]] = {}
        for name, exts in categories_raw.items():
            if not isinstance(name, str) or not isinstance(exts, list):
                raise ValueError(f"Invalid category entry for {name!r}: expected list of extensions.")
            if not all(isinstance(item, str) for item in exts):
                raise ValueError(f"All extensions in category {name!r} must be strings.")
            categories[name] = tuple(exts)

        ignore_exts_raw = raw.get("ignore_extensions", list(DEFAULT_IGNORE_EXTENSIONS))
        if not isinstance(ignore_exts_raw, list) or not all(
            isinstance(item, str) for item in ignore_exts_raw
        ):
            raise ValueError("'ignore_extensions' must be a list of strings.")

        ignore_names_raw = raw.get("ignore_names", list(DEFAULT_IGNORE_NAMES))
        if not isinstance(ignore_names_raw, list) or not all(
            isinstance(item, str) for item in ignore_names_raw
        ):
            raise ValueError("'ignore_names' must be a list of strings.")

        # Always keep the undo history file protected from being moved.
        ignore_names = frozenset(ignore_names_raw) | {".smart_organizer_history.json"}

        fallback = raw.get("fallback_category", "Other")
        if not isinstance(fallback, str):
            raise ValueError("'fallback_category' must be a string.")

        return cls(
            categories=categories,
            ignore_extensions=frozenset(ignore_exts_raw),
            ignore_names=ignore_names,
            fallback_category=fallback,
        )
