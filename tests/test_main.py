"""Тесты точки входа приложения."""

import io
import json
import os
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stdout

from src.main import EXIT_FAILURE, EXIT_SUCCESS, main, parse_arguments



def setUpModule():
    """Отключает системный прокси: тесты обращаются к 127.0.0.1."""
    no_proxy = urllib.request.ProxyHandler({})
    urllib.request.install_opener(urllib.request.build_opener(no_proxy))


def tearDownModule():
    """Возвращает обычные настройки urllib после тестов."""
    urllib.request.install_opener(None)
def run_main(argv):
    """Запускает main и возвращает код завершения и вывод."""
    output = io.StringIO()
    with redirect_stdout(output):
        code = main(argv)
    return code, output.getvalue()


class TestArguments(unittest.TestCase):
    """Проверяет разбор параметров командной строки."""

    def test_default_config(self):
        """Проверяет путь к конфигу по умолчанию."""
        self.assertEqual(parse_arguments([]).config, "config.json")

    def test_custom_config(self):
        """Проверяет путь к конфигу, заданный пользователем."""
        args = parse_arguments(["--config", "my.json"])
        self.assertEqual(args.config, "my.json")


class TestMain(unittest.TestCase):
    """Проверяет вывод зависимостей и коды завершения."""

    def test_test_mode_output(self):
        """Проверяет вывод прямых зависимостей в тестовом режиме."""
        code, output = run_main(["-c", "configs/test_mode.json"])
        self.assertEqual(code, EXIT_SUCCESS)
        self.assertIn("Direct dependencies of A:", output)
        self.assertIn("  - B", output)
        self.assertIn("Total: 2", output)

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