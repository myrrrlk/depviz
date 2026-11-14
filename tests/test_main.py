"""Тесты точки входа приложения."""

import io
import unittest
from contextlib import redirect_stdout

from src.main import EXIT_FAILURE, EXIT_SUCCESS, main, parse_arguments


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
    """Проверяет вывод параметров и коды завершения."""

    def test_key_value_output(self):
        """Проверяет вывод всех параметров в формате ключ-значение."""
        code, output = run_main(["-c", "config.json"])
        self.assertEqual(code, EXIT_SUCCESS)
        lines = output.splitlines()
        self.assertEqual(len(lines), 6)
        self.assertIn("package_name: org.springframework:spring-core",
                      lines)
        self.assertIn('filter_substring: ""', lines)

    def test_invalid_config(self):
        """Проверяет вывод ошибок и код завершения."""
        code, output = run_main(["-c", "configs/errors/wrong_remote.json"])
        self.assertEqual(code, EXIT_FAILURE)
        self.assertIn("Error: invalid configuration", output)
        self.assertIn("  - package_name:", output)


if __name__ == "__main__":
    unittest.main()