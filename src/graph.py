"""Построение графа зависимостей обходом в глубину (DFS) без рекурсии.

Граф строится через источник данных (source) с двумя методами:
dependencies(name) - список прямых зависимостей пакета и label(name) -
подпись пакета для вывода. Так один и тот же алгоритм работает и с
репозиторием Maven, и с тестовым репозиторием.
"""

from dataclasses import dataclass, field


IN_PROGRESS = "in progress"
DONE = "done"


class SourceError(Exception):
    """Ошибка получения зависимостей пакета из источника."""


@dataclass
class DependencyGraph:
    """Граф зависимостей и сведения, собранные при его построении."""

    root: str
    edges: dict = field(default_factory=dict)
    cycles: list = field(default_factory=list)
    skipped: list = field(default_factory=list)
    errors: dict = field(default_factory=dict)

    def edge_count(self):
        """Возвращает число рёбер (зависимостей) в графе."""
        return sum(len(children) for children in self.edges.values())


def is_filtered(name, filter_substring):
    """Проверяет, нужно ли пропустить пакет из-за подстроки фильтра."""
    return bool(filter_substring) and filter_substring in name


def load_children(graph, source, name, filter_substring):
    """Загружает зависимости пакета, учитывая фильтр и ошибки."""
    try:
        children = source.dependencies(name)
    except SourceError as error:
        graph.errors[name] = str(error)
        children = []

    kept = []
    for child in children:
        if is_filtered(child, filter_substring):
            if child not in graph.skipped:
                graph.skipped.append(child)
        elif child not in kept:
            kept.append(child)
    graph.edges[name] = kept
    return kept


def cycle_path(stack, name):
    """Возвращает путь цикла: от name по стеку и обратно к name."""
    path = [node for node, _ in stack]
    return path[path.index(name):] + [name]


def build_graph(source, root, filter_substring=""):
    """Строит граф зависимостей пакета root обходом DFS на стеке.

    Стек хранит пары (пакет, итератор по его зависимостям). Состояние
    IN_PROGRESS означает, что пакет сейчас в стеке: если встретить его
    снова, найден цикл. Состояние DONE - пакет уже полностью обработан.
    """
    graph = DependencyGraph(root)
    state = {root: IN_PROGRESS}
    children = load_children(graph, source, root, filter_substring)
    stack = [(root, iter(children))]

    while stack:
        name, remaining = stack[-1]
        child = next(remaining, None)
        if child is None:
            state[name] = DONE
            stack.pop()
        elif state.get(child) == IN_PROGRESS:
            graph.cycles.append(cycle_path(stack, child))
        elif child not in state:
            state[child] = IN_PROGRESS
            grandchildren = load_children(graph, source, child,
                                          filter_substring)
            stack.append((child, iter(grandchildren)))
    return graph