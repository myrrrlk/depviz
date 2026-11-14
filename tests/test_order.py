"""Тесты порядка загрузки зависимостей."""

import unittest

from src.graph import DependencyGraph
from src.order import load_order


def make_graph(edges, root="A", cycles=None):
    """Создаёт граф из словаря пакет -> список зависимостей."""
    return DependencyGraph(root, edges=edges, cycles=cycles or [])


class TestLoadOrder(unittest.TestCase):
    """Проверяет порядок загрузки."""

    def assert_dependencies_first(self, graph, order):
        """Проверяет, что каждый пакет идёт после своих зависимостей."""
        position = {name: index for index, name in enumerate(order)}
        for name, children in graph.edges.items():
            for child in children:
                self.assertLess(position[child], position[name],
                                f"{child} must be loaded before {name}")

    def test_single_package(self):
        """Проверяет пакет без зависимостей."""
        self.assertEqual(load_order(make_graph({"A": []})), ["A"])

    def test_chain(self):
        """Проверяет цепочку A -> B -> C."""
        graph = make_graph({"A": ["B"], "B": ["C"], "C": []})
        self.assertEqual(load_order(graph), ["C", "B", "A"])

    def test_diamond(self):
        """Проверяет ромб: общий пакет загружается один раз и первым."""
        graph = make_graph({"A": ["B", "C"], "B": ["D"], "C": ["D"],
                            "D": []})
        self.assertEqual(load_order(graph), ["D", "B", "C", "A"])

    def test_layers(self):
        """Проверяет граф из нескольких уровней без циклов."""
        graph = make_graph({
            "A": ["B", "C", "D"], "B": ["E"], "C": ["E", "F"],
            "D": ["F"], "E": ["G"], "F": ["G"], "G": [],
        })
        order = load_order(graph)
        self.assertEqual(len(order), 7)
        self.assert_dependencies_first(graph, order)

    def test_root_is_last(self):
        """Проверяет, что корневой пакет загружается последним."""
        graph = make_graph({"A": ["B", "C"], "B": [], "C": []})
        self.assertEqual(load_order(graph)[-1], "A")

    def test_cycle(self):
        """Проверяет, что при цикле каждый пакет есть ровно один раз."""
        graph = make_graph({"A": ["B"], "B": ["C"], "C": ["A"]},
                           cycles=[["A", "B", "C", "A"]])
        order = load_order(graph)
        self.assertEqual(sorted(order), ["A", "B", "C"])
        self.assertEqual(order, ["C", "B", "A"])

    def test_self_dependency(self):
        """Проверяет пакет, зависящий от самого себя."""
        graph = make_graph({"A": ["A"]}, cycles=[["A", "A"]])
        self.assertEqual(load_order(graph), ["A"])


if __name__ == "__main__":
    unittest.main()