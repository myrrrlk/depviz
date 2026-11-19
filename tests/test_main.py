"""Тесты точки входа приложения."""

import io
import json
import os
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stdout
from unittest import mock

from src import visualize
from src.main import EXIT_FAILURE, EXIT_SUCCESS, main, parse_arguments


def setupmodule(): #noqa: N802
    """Отключает системный прокси: тесты обращаются к 127.0.0.1."""
    no_proxy = urllib.request.ProxyHandler({})
    urllib.request.install_opener(urllib.request.build_opener(no_proxy))


def teardownmodule(): #noqa: N802
    """Возвращает обычные настройки urllib после тестов."""
    urllib.request.install_opener(None)


def run_main(argv):
    """Запускает main и возвращает код завершения и вывод."""
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, output.getvalue()


class GraphTestCase(unittest.TestCase):
    """Запускает программу так, чтобы файлы писались во временную папку."""

    def setUp(self):
        """Создаёт временную папку для файлов .mmd и .png."""
        self.folder = tempfile.mkdtemp()

    def tearDown(self):
        """Удаляет временную папку."""
        for name in os.listdir(self.folder):
            os.remove(os.path.join(self.folder, name))
        os.rmdir(self.folder)

    def run_config(self, config_path, *flags):
        """Запускает main с копией конфига, где картинка во temp-папке."""
        with open(config_path, encoding="utf-8") as config_file:
            config = json.load(config_file)
        config["output_image"] = os.path.join(self.folder, "graph.png")
        path = os.path.join(self.folder, "config.json")
        with open(path, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file)
        return run_main(["-c", path, "--no-image", *flags])


class TestArguments(unittest.TestCase):
    """Проверяет разбор параметров командной строки."""

    def test_default_config(self):
        """Проверяет путь к конфигу по умолчанию."""
        self.assertEqual(parse_arguments([]).config, "config.json")

    def test_custom_config(self):
        """Проверяет путь к конфигу, заданный пользователем."""
        args = parse_arguments(["--config", "my.json"])
        self.assertEqual(args.config, "my.json")

    def test_load_order_flag(self):
        """Проверяет флаг --load-order."""
        self.assertFalse(parse_arguments([]).load_order)
        self.assertTrue(parse_arguments(["--load-order"]).load_order)

    def test_no_image_flag(self):
        """Проверяет флаг --no-image."""
        self.assertFalse(parse_arguments([]).no_image)
        self.assertTrue(parse_arguments(["--no-image"]).no_image)


class TestMain(GraphTestCase):
    """Проверяет вывод графа, визуализацию и коды завершения."""

    def test_graph_output(self):
        """Проверяет вывод графа в тестовом режиме."""
        code, output = self.run_config("configs/test_basic.json")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Dependency graph of A:", output)
        self.assertIn("  A -> B, C", output)
        self.assertIn("  D -> (none)", output)
        self.assertIn("Packages: 4, dependencies: 4", output)

    def test_filter_output(self):
        """Проверяет вывод пропущенных фильтром пакетов."""
        code, output = self.run_config("configs/test_mode.json")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Skipped by filter 'D': D", output)

    def test_cycle_output(self):
        """Проверяет вывод циклических зависимостей."""
        code, output = self.run_config("configs/test_cycle.json")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("  A -> B -> C -> A", output)

    def test_mermaid_output(self):
        """Проверяет вывод Mermaid и сохранение файла .mmd."""
        code, output = self.run_config("configs/test_basic.json")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Mermaid diagram:", output)
        self.assertIn("graph TD", output)
        self.assertTrue(os.path.isfile(os.path.join(self.folder,
                                                    "graph.mmd")))

    def test_image_is_rendered(self):
        """Проверяет вызов построения PNG без флага --no-image."""
        config = os.path.join(self.folder, "config.json")
        self.run_config("configs/test_basic.json")
        with mock.patch.object(visualize, "render_png",
                               return_value="test renderer") as render:
            code, output = run_main(["-c", config])
        self.assertEqual(code, EXIT_SUCCESS)
        render.assert_called_once()
        self.assertIn("(rendered by test renderer)", output)

    def test_image_error(self):
        """Проверяет код завершения, если PNG получить не удалось."""
        config = os.path.join(self.folder, "config.json")
        self.run_config("configs/test_basic.json")
        error = visualize.RenderError("no way to render")
        with mock.patch.object(visualize, "render_png", side_effect=error):
            code, output = run_main(["-c", config])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("Error: no way to render", output)

    def test_load_order(self):
        """Проверяет режим вывода порядка загрузки."""
        code, output = self.run_config("configs/test_basic.json",
                                       "--load-order")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Load order of A:", output)
        self.assertIn("  1. D", output)
        self.assertIn("  4. A", output)

    def test_load_order_with_cycle(self):
        """Проверяет предупреждение о цикле в порядке загрузки."""
        code, output = self.run_config("configs/test_cycle.json",
                                       "--load-order")
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Warning: the graph has cyclic dependencies", output)

    def test_unknown_root(self):
        """Проверяет пакет, которого нет в тестовом репозитории."""
        path = "configs/errors/unknown_test_package.json"
        code, output = run_main(["-c", path])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("Error: package 'Z' not found", output)

    def test_invalid_config(self):
        """Проверяет вывод ошибок конфигурации и код завершения."""
        code, output = run_main(["-c", "configs/errors/wrong_remote.json"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("Error: invalid configuration", output)
        self.assertIn("  - package_name:", output)

    def test_repository_error(self):
        """Проверяет недоступный репозиторий."""
        config = {
            "package_name": "com.example:app",
            "repository": "http://127.0.0.1:1",
            "repository_mode": "remote",
            "version": "1.0",
            "output_image": "graph.png",
            "filter_substring": "",
        }
        handle, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(handle, "w", encoding="utf-8") as config_file:
            json.dump(config, config_file)
        self.addCleanup(os.remove, path)

        code, output = run_main(["-c", path])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("Error: cannot connect to repository", output)


if __name__ == "__main__":
    unittest.main()