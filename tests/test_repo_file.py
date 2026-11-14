"""Тесты тестового репозитория в текстовом файле."""

import os
import tempfile
import unittest

from src.repo_file import RepoFileError, get_direct_dependencies


class RepoFileTestCase(unittest.TestCase):
    """Создаёт временные файлы тестового репозитория."""

    def make_repo(self, text):
        """Сохраняет текст во временный файл и возвращает путь."""
        handle, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(handle, "w", encoding="utf-8") as repo_file:
            repo_file.write(text)
        self.addCleanup(os.remove, path)
        return path


class TestDirectDependencies(RepoFileTestCase):
    """Проверяет чтение прямых зависимостей."""

    def test_dependencies(self):
        """Проверяет пакет с несколькими зависимостями."""
        path = self.make_repo("A: B C\nB: C\nC:\n")
        self.assertEqual(get_direct_dependencies(path, "A"), ["B", "C"])

    def test_no_dependencies(self):
        """Проверяет пакет без зависимостей."""
        path = self.make_repo("A: B\nB:\n")
        self.assertEqual(get_direct_dependencies(path, "B"), [])

    def test_comments_and_empty_lines(self):
        """Проверяет пропуск комментариев и пустых строк."""
        path = self.make_repo("# graph\n\nA: B\n")
        self.assertEqual(get_direct_dependencies(path, "A"), ["B"])

    def test_example_file(self):
        """Проверяет пример из папки repos."""
        path = os.path.join("repos", "basic.txt")
        self.assertEqual(get_direct_dependencies(path, "A"), ["B", "C"])


class TestErrors(RepoFileTestCase):
    """Проверяет ошибки тестового репозитория."""

    def test_unknown_package(self):
        """Проверяет пакет, которого нет в файле."""
        path = self.make_repo("A: B\n")
        with self.assertRaisesRegex(RepoFileError, "not found"):
            get_direct_dependencies(path, "X")

    def test_missing_separator(self):
        """Проверяет строку без двоеточия."""
        path = self.make_repo("A B\n")
        with self.assertRaisesRegex(RepoFileError, "line 1"):
            get_direct_dependencies(path, "A")

    def test_invalid_name(self):
        """Проверяет имя пакета не из больших букв."""
        path = self.make_repo("A: b\n")
        with self.assertRaisesRegex(RepoFileError, "invalid package name"):
            get_direct_dependencies(path, "A")

    def test_duplicate_package(self):
        """Проверяет повторное описание пакета."""
        path = self.make_repo("A: B\nA: C\n")
        with self.assertRaisesRegex(RepoFileError, "described twice"):
            get_direct_dependencies(path, "A")

    def test_missing_file(self):
        """Проверяет отсутствующий файл."""
        with self.assertRaisesRegex(RepoFileError, "cannot read"):
            get_direct_dependencies("no_such_repo.txt", "A")


if __name__ == "__main__":
    unittest.main()