"""Инструмент визуализации графа зависимостей пакетов Maven."""

import argparse
import sys

from src import maven, repo_file
from src.config import MODE_TEST, ConfigError, load_config


DEFAULT_CONFIG = "config.json"
EXIT_SUCCESS = 0
EXIT_FAILURE = 1


def parse_arguments(argv=None):
    """Разбирает параметры командной строки."""
    parser = argparse.ArgumentParser(
        prog="depviz",
        description="Dependency graph visualizer for Maven packages.",
    )
    parser.add_argument(
        "-c", "--config", default=DEFAULT_CONFIG, metavar="PATH",
        help=f"path to the JSON config file (default: {DEFAULT_CONFIG})",
    )
    return parser.parse_args(argv)


def print_config_errors(path, error):
    """Выводит список ошибок конфигурации."""
    print(f"Error: invalid configuration in '{path}':")
    for message in error.messages:
        print(f"  - {message}")


def package_title(config):
    """Возвращает имя пакета с версией для заголовка вывода."""
    if config.repository_mode == MODE_TEST:
        return config.package_name
    return f"{config.package_name}:{config.version}"


def find_direct_dependencies(config):
    """Возвращает прямые зависимости пакета в виде строк для вывода."""
    if config.repository_mode == MODE_TEST:
        return repo_file.get_direct_dependencies(
            config.repository, config.package_name)
    dependencies = maven.get_direct_dependencies(
        config.repository, config.package_name, config.version)
    return [dependency.describe() for dependency in dependencies]


def print_dependencies(title, dependencies):
    """Выводит список прямых зависимостей пакета."""
    if not dependencies:
        print(f"Package {title} has no direct dependencies.")
        return
    print(f"Direct dependencies of {title}:")
    for dependency in dependencies:
        print(f"  - {dependency}")
    print(f"Total: {len(dependencies)}")


def main(argv=None):
    """Точка входа: загружает конфигурацию и выводит прямые зависимости.

    Возвращает код завершения программы.
    """
    args = parse_arguments(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print_config_errors(args.config, error)
        return EXIT_FAILURE

    try:
        dependencies = find_direct_dependencies(config)
    except (maven.MavenError, repo_file.RepoFileError) as error:
        print(f"Error: {error}")
        return EXIT_FAILURE

    print_dependencies(package_title(config), dependencies)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())