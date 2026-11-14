"""Инструмент визуализации графа зависимостей пакетов Maven."""

import argparse
import sys

from src.config import ConfigError, load_config


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


def format_value(value):
    """Готовит значение параметра для вывода на экран."""
    return '""' if value == "" else value


def print_config(config):
    """Выводит все параметры в формате ключ-значение."""
    for key, value in config.items():
        print(f"{key}: {format_value(value)}")


def print_config_errors(path, error):
    """Выводит список ошибок конфигурации."""
    print(f"Error: invalid configuration in '{path}':")
    for message in error.messages:
        print(f"  - {message}")


def main(argv=None):
    """Точка входа: загружает конфигурацию и выводит параметры.

    Возвращает код завершения программы.
    """
    args = parse_arguments(argv)
    try:
        config = load_config(args.config)
    except ConfigError as error:
        print_config_errors(args.config, error)
        return EXIT_FAILURE

    print_config(config)
    return EXIT_SUCCESS


if __name__ == "__main__":
    sys.exit(main())