[English](#smart-file-organizer) | [Русский](#умный-сортировщик-файлов)

# Smart File Organizer

A lightweight Python CLI tool that sorts cluttered folders such as `Downloads` into clean category directories without external runtime dependencies.

## Features

- Categorizes files by extension (`Images`, `Documents`, `Archives`, `Audio`, `Video`, `Code`, `Installers`, and `Other`).
- Protects unfinished browser downloads (`.crdownload`, `.part`, `.tmp`, `.download`) and OS metadata files (`desktop.ini`, `.DS_Store`, `Thumbs.db`).
- Prevents accidental overwrites by renaming colliding files (`report.pdf` becomes `report (1).pdf`).
- Supports `--dry-run` previews before touching any files.
- Groups files by modification month (`YYYY-MM`) with `--by-date`.
- Reverts the previous run with `--undo` and removes empty folders created during sorting.
- Accepts custom rules via a JSON config file.

## Requirements

- Python 3.10 or newer
- `pytest` (only needed to run the test suite)

## Installation

Clone the repository and install it in editable mode:

```bash
git clone https://github.com/rus1117/smart-file-organizer.git
cd smart-file-organizer
pip install -e .
```

You can also run the tool directly without installing by pointing `PYTHONPATH=src` and executing `python -m smart_organizer`.

## Usage

Preview changes in your default `~/Downloads` folder:

```bash
smart-organizer --dry-run
```

Sort a specific folder and group files into monthly subfolders:

```bash
smart-organizer ~/Downloads --by-date --verbose
```

Use custom category rules from [config.example.json](config.example.json):

```bash
smart-organizer ~/Downloads --config config.example.json
```

Undo the last organization run in a directory:

```bash
smart-organizer ~/Downloads --undo
```

## Running tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT

# Умный сортировщик файлов

Лёгкая консольная утилита на Python для сортировки файлов в папке «Загрузки» (`Downloads`) и других директориях без внешних зависимостей для запуска.

## Возможности

- Распределяет файлы по категориям на основе расширений (`Images`, `Documents`, `Archives`, `Audio`, `Video`, `Code`, `Installers`, `Other`).
- Пропускает недокачанные файлы браузеров (`.crdownload`, `.part`, `.tmp`, `.download`) и служебные файлы системы (`desktop.ini`, `.DS_Store`, `Thumbs.db`).
- Защищает от случайной перезаписи: при совпадении имён добавляет номер (`report.pdf` становится `report (1).pdf`).
- Поддерживает режим предпросмотра `--dry-run` (`-n`) без изменения файлов на диске.
- Группирует файлы по месяцам изменения (`YYYY-MM`) с флагом `--by-date` (`-d`).
- Откатывает последний запуск командой `--undo` и удаляет созданные пустые подпапки.
- Поддерживает собственные правила сортировки через JSON-конфигурацию.

## Требования

- Python 3.10 или выше
- `pytest` (нужен только для запуска тестов)

## Установка

Клонируйте репозиторий и установите пакет локально:

```bash
git clone https://github.com/rus1117/smart-file-organizer.git
cd smart-file-organizer
pip install -e .
```

Утилиту можно запускать и без установки: укажите `PYTHONPATH=src` и выполните `python -m smart_organizer`.

## Использование

Проверить, какие перемещения планируются в папке `~/Downloads`, без изменения файлов:

```bash
smart-organizer --dry-run
```

Рассортировать папку с группировкой по месяцам и подробным выводом:

```bash
smart-organizer ~/Downloads --by-date --verbose
```

Применить свой файл конфигурации по образцу [config.example.json](config.example.json):

```bash
smart-organizer ~/Downloads --config config.example.json
```

Отменить последнюю сортировку в указанной папке:

```bash
smart-organizer ~/Downloads --undo
```

## Запуск тестов

```bash
pip install -e ".[dev]"
pytest
```

## Лицензия

MIT
