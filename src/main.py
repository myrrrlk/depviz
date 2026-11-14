"""Инструмент визуализации графа зависимостей пакетов Maven."""

import argparse
import sys

from src import maven, repo_file, visualize
from src.config import MODE_TEST, ConfigError, load_config
from src.graph import build_graph
from src.order import load_order


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
    parser.add_argument(
        "--load-order", action="store_true",
        help="print the order in which dependencies are loaded",
    )
    parser.add_argument(
        "--no-image", action="store_true",
        help="print the Mermaid diagram but do not create the PNG image",
    )
    return parser.parse_args(argv)


def print_config_errors(path, error):
    """Выводит список ошибок конфигурации."""
    print(f"Error: invalid configuration in '{path}':")
    for message in error.messages:
        print(f"  - {message}")


def create_source(config):
    """Создаёт источник зависимостей в зависимости от режима работы."""
    if config.repository_mode == MODE_TEST:
        return repo_file.RepoFileSource(config.repository)
    return maven.MavenSource(config.repository, config.package_name,
                             config.version)


def print_edges(graph, source):
    """Выводит каждый пакет графа и его зависимости."""
    print(f"Dependency graph of {source.label(graph.root)}:")
    for name, children in graph.edges.items():
        targets = ", ".join(source.label(child) for child in children)
        print(f"  {source.label(name)} -> {targets or '(none)'}")


def print_details(graph, filter_substring):
    """Выводит пропущенные пакеты, циклы, ошибки и итоговые числа."""
    if graph.skipped:
        print(f"Skipped by filter '{filter_substring}': "
              f"{', '.join(graph.skipped)}")
    if graph.cycles:
        print("Cyclic dependencies:")
        for cycle in graph.cycles:
            print(f"  {' -> '.join(cycle)}")
    if graph.errors:
        print("Could not load:")
        for name, message in graph.errors.items():
            print(f"  {name}: {message}")
    print(f"Packages: {len(graph.edges)}, "
          f"dependencies: {graph.edge_count()}")


def print_load_order(graph, source):
    """Выводит порядок загрузки: каждый пакет после его зависимостей."""
    print(f"Load order of {source.label(graph.root)}:")
    for number, name in enumerate(load_order(graph), start=1):
        print(f"  {number}. {source.label(name)}")
    if graph.cycles:
        print("Warning: the graph has cyclic dependencies, so a strict "
              "order does not exist.")
        print("The edge that closes each cycle is ignored:")
        for cycle in graph.cycles:
            print(f"  {' -> '.join(cycle)}")


def show_visualization(graph, source, config, create_image):
    """Выводит граф на языке Mermaid, сохраняет его в .mmd и в PNG.

    Возвращает код завершения программы.
    """
    text = visualize.to_mermaid(graph, source)
    print("Mermaid diagram:")
    print(text, end="")
    text_path = visualize.mermaid_path(config.output_image)
    visualize.save_text(text, text_path)
    print(f"Mermaid diagram saved to {text_path}")
    if not create_image:
        return EXIT_SUCCESS
    try:
        method = visualize.render_png(text, config.output_image)
    except visualize.RenderError as error:
        print(f"Error: {error}")
        return EXIT_FAILURE
    print(f"Image saved to {config.output_image} (rendered by {method})")
    return EXIT_SUCCESS


def main(argv=None):
    """Точка входа: строит граф, выводит его и сохраняет изображение.

    Возвращает код завершения программы.
    """
    args = parse_arguments(argv)
    try:
        config = load_config(args.config)
        source = create_source(config)
    except ConfigError as error:
        print_config_errors(args.config, error)
        return EXIT_FAILURE
    except repo_file.RepoFileError as error:
        print(f"Error: {error}")
        return EXIT_FAILURE

    graph = build_graph(source, config.package_name,
                        config.filter_substring)
    if config.package_name in graph.errors:
        print(f"Error: {graph.errors[config.package_name]}")
        return EXIT_FAILURE

    if args.load_order:
        print_load_order(graph, source)
        return EXIT_SUCCESS
    print_edges(graph, source)
    print_details(graph, config.filter_substring)
    print()
    return show_visualization(graph, source, config, not args.no_image)


if __name__ == "__main__":
    sys.exit(main())