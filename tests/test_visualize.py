"""Тесты визуализации графа (Mermaid и PNG)."""

import os
import tempfile
import unittest
from unittest import mock

from src import visualize
from src.graph import DependencyGraph


class NameSource:
    """Источник подписей для тестов: подпись совпадает с именем."""

    def label(self, name):
        """Возвращает подпись пакета."""
        return name


def make_graph(edges, cycles=None):
    """Создаёт граф с корнем A."""
    return DependencyGraph("A", edges=edges, cycles=cycles or [])


class TestMermaid(unittest.TestCase):
    """Проверяет текст на языке Mermaid."""

    def test_nodes_and_edges(self):
        """Проверяет узлы и рёбра."""
        text = visualize.to_mermaid(
            make_graph({"A": ["B", "C"], "B": [], "C": []}), NameSource())
        lines = text.splitlines()
        self.assertEqual(lines[0], "graph TD")
        self.assertIn('    n0["A"]', lines)
        self.assertIn("    n0 --> n1", lines)
        self.assertIn("    n0 --> n2", lines)

    def test_root_style(self):
        """Проверяет, что корневой пакет выделен."""
        text = visualize.to_mermaid(make_graph({"A": []}), NameSource())
        self.assertIn(f"style n0 {visualize.ROOT_STYLE}", text)

    def test_cycle_edges_are_red(self):
        """Проверяет, что рёбра цикла выделены красным."""
        graph = make_graph({"A": ["B", "C"], "B": ["A"], "C": []},
                           cycles=[["A", "B", "A"]])
        text = visualize.to_mermaid(graph, NameSource())
        self.assertIn(f"linkStyle 0,2 {visualize.CYCLE_STYLE}", text)

    def test_no_cycles_no_link_style(self):
        """Проверяет граф без циклов."""
        text = visualize.to_mermaid(make_graph({"A": ["B"], "B": []}),
                                    NameSource())
        self.assertNotIn("linkStyle", text)

    def test_quotes_are_escaped(self):
        """Проверяет замену кавычек в подписи."""
        self.assertEqual(visualize.escape_label('a"b'), "a#quot;b")


class TestFiles(unittest.TestCase):
    """Проверяет сохранение файлов."""

    def setUp(self):
        """Создаёт временную папку."""
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        """Удаляет временную папку."""
        for name in os.listdir(self.folder):
            os.remove(os.path.join(self.folder, name))
        os.rmdir(self.folder)

    def test_mermaid_path(self):
        """Проверяет имя файла .mmd."""
        self.assertEqual(visualize.mermaid_path("out/graph.png"),
                         "out/graph.mmd")

    def test_save_png(self):
        """Проверяет сохранение PNG."""
        path = os.path.join(self.folder, "graph.png")
        visualize.save_png(visualize.PNG_SIGNATURE + b"data", path)
        self.assertTrue(os.path.isfile(path))

    def test_not_png(self):
        """Проверяет, что ответ не в формате PNG отклоняется."""
        path = os.path.join(self.folder, "graph.png")
        with self.assertRaisesRegex(visualize.RenderError, "not a PNG"):
            visualize.save_png(b"<html>error</html>", path)


class TestRender(unittest.TestCase):
    """Проверяет выбор способа получения PNG."""

    @staticmethod
    def failing(text, path):
        """Способ, который всегда завершается ошибкой."""
        raise visualize.RenderError("does not work")

    @staticmethod
    def working(text, path):
        """Способ, который всегда работает."""

    def test_first_working_method(self):
        """Проверяет, что используется первый сработавший способ."""
        renderers = (("bad", self.failing), ("good", self.working))
        with mock.patch.object(visualize, "RENDERERS", renderers):
            self.assertEqual(visualize.render_png("graph TD", "g.png"),
                             "good")

    def test_all_methods_fail(self):
        """Проверяет ошибку, если ни один способ не сработал."""
        renderers = (("first", self.failing), ("second", self.failing))
        with mock.patch.object(visualize, "RENDERERS", renderers):
            with self.assertRaises(visualize.RenderError) as context:
                visualize.render_png("graph TD", "g.png")
        self.assertIn("first: does not work", str(context.exception))
        self.assertIn("second: does not work", str(context.exception))

    def test_mmdc_not_installed(self):
        """Проверяет сообщение, если mmdc не установлен."""
        with mock.patch.object(visualize.shutil, "which", return_value=None):
            with self.assertRaisesRegex(visualize.RenderError,
                                        "not installed"):
                visualize.render_with_mmdc("graph TD", "g.png")


if __name__ == "__main__":
    unittest.main()