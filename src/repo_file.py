"""Тестовый репозиторий: описание графа пакетов в текстовом файле.

Каждая строка файла имеет вид "A: B C" и означает, что пакет A зависит
от пакетов B и C. Пакеты называются большими латинскими буквами.
Пустые строки и строки, начинающиеся с "#", пропускаются.
"""

import re


COMMENT_PREFIX = "#"
SEPARATOR = ":"
NAME_PATTERN = re.compile(r"^[A-Z]+$")


class RepoFileError(Exception):
    """Ошибка чтения или формата файла тестового репозитория."""


def check_name(name, number):
    """Проверяет имя пакета в строке с номером number."""
    if not NAME_PATTERN.match(name):
        message = (f"line {number}: invalid package name '{name}' "
                   "(capital Latin letters expected).")
        raise RepoFileError(message)


def parse_line(line, number):
    """Разбирает строку "A: B C" и возвращает (имя, список зависимостей)."""
    if SEPARATOR not in line:
        raise RepoFileError(f"line {number}: ':' expected.")
    name, dependencies = line.split(SEPARATOR, 1)
    name = name.strip()
    dependencies = dependencies.split()
    for package in [name, *dependencies]:
        check_name(package, number)
    return name, dependencies


def load_repository(path):
    """Читает файл и возвращает словарь: пакет -> список зависимостей."""
    try:
        with open(path, encoding="utf-8") as repo_file:
            lines = repo_file.read().splitlines()
    except OSError as error:
        message = f"cannot read test repository '{path}'."
        raise RepoFileError(message) from error

    graph = {}
    for number, line in enumerate(lines, start=1):
        line = line.strip()
        if not line or line.startswith(COMMENT_PREFIX):
            continue
        name, dependencies = parse_line(line, number)
        if name in graph:
            raise RepoFileError(f"line {number}: package '{name}' "
                                "is described twice.")
        graph[name] = dependencies
    return graph


def get_direct_dependencies(path, package_name):
    """Возвращает прямые зависимости пакета из тестового репозитория."""
    graph = load_repository(path)
    if package_name not in graph:
        message = f"package '{package_name}' not found in '{path}'."
        raise RepoFileError(message)
    return graph[package_name]