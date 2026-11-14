"""Тесты построения графа зависимостей."""

import unittest

from src.graph import SourceError, build_graph


class DictSource:
    """Источник зависимостей для тестов: граф задан словарём."""

    def __init__(self, edges):
        """Сохраняет словарь пакет -> список зависимостей."""
        self.edges = edges

    def dependencies(self, name):
        """Возвращает зависимости пакета или выбрасывает SourceError."""
        if name not in self.edges:
            raise SourceError(f"package '{name}' not found.")
        return self.edges[name]

    def label(self, name):
        """Возвращает подпись пакета."""
        return name


def graph_of(edges, root="A", filter_substring=""):
    """Строит граф по словарю."""
    return build_graph(DictSource(edges), root, filter_substring)


class TestTraversal(unittest.TestCase):
    """Проверяет обход графа."""

    def test_transitive_dependencies(self):
        """Проверяет, что найдены зависимости зависимостей."""
        graph = graph_of({"A": ["B"], "B": ["C"], "C": []})
        self.assertEqual(list(graph.edges), ["A", "B", "C"])

    def test_dfs_order(self):
        """Проверяет порядок обхода в глубину."""
        graph = graph_of({"A": ["B", "C"], "B": ["D"], "C": [], "D": []})
        self.assertEqual(list(graph.edges), ["A", "B", "D", "C"])

    def test_shared_dependency_once(self):
        """Проверяет, что общий пакет (ромб) обрабатывается один раз."""
        graph = graph_of({"A": ["B", "C"], "B": ["D"], "C": ["D"], "D": []})
        self.assertEqual(len(graph.edges), 4)
        self.assertEqual(graph.edge_count(), 4)
        self.assertEqual(graph.cycles, [])

    def test_deep_chain_without_recursion(self):
        """Проверяет цепочку длиннее предела рекурсии Python."""
        length = 5000
        edges = {f"P{i}": [f"P{i + 1}"] for i in range(length)}
        edges[f"P{length}"] = []
        graph = graph_of(edges, root="P0")
        self.assertEqual(len(graph.edges), length + 1)


class TestCycles(unittest.TestCase):
    """Проверяет обработку циклических зависимостей."""

    def test_simple_cycle(self):
        """Проверяет цикл A -> B -> C -> A."""
        graph = graph_of({"A": ["B"], "B": ["C"], "C": ["A"]})
        self.assertEqual(graph.cycles, [["A", "B", "C", "A"]])
        self.assertEqual(graph.edges["C"], ["A"])

    def test_self_dependency(self):
        """Проверяет пакет, зависящий от самого себя."""
        graph = graph_of({"A": ["A"]})
        self.assertEqual(graph.cycles, [["A", "A"]])

    def test_several_cycles(self):
        """Проверяет граф с несколькими циклами."""
        graph = graph_of({"A": ["B", "C"], "B": ["A"], "C": ["C"]})
        self.assertEqual(len(graph.cycles), 2)


class TestFilterAndErrors(unittest.TestCase):
    """Проверяет фильтр по подстроке и ошибки источника."""

    def test_filter(self):
        """Проверяет, что пакеты с подстрокой пропускаются вместе с их
        зависимостями."""
        edges = {"A": ["B", "XC"], "B": [], "XC": ["D"], "D": []}
        graph = graph_of(edges, filter_substring="X")
        self.assertEqual(list(graph.edges), ["A", "B"])
        self.assertEqual(graph.skipped, ["XC"])

    def test_empty_filter(self):
        """Проверяет, что пустая подстрока ничего не фильтрует."""
        graph = graph_of({"A": ["B"], "B": []}, filter_substring="")
        self.assertEqual(graph.skipped, [])

    def test_filter_breaks_cycle(self):
        """Проверяет, что фильтр может разорвать цикл."""
        graph = graph_of({"A": ["B"], "B": ["A"]}, filter_substring="B")
        self.assertEqual(graph.cycles, [])

    def test_unknown_dependency(self):
        """Проверяет, что ошибка загрузки пакета не прерывает обход."""
        graph = graph_of({"A": ["B", "C"], "C": []})
        self.assertIn("B", graph.errors)
        self.assertIn("C", graph.edges)


if __name__ == "__main__":
    unittest.main()