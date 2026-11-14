"""Тесты загрузки и проверки конфигурации."""

import json
import os
import tempfile
import unittest

from src.config import ConfigError, load_config


VALID_REMOTE = {
    "package_name": "org.springframework:spring-core",
    "repository": "https://repo1.maven.org/maven2",
    "repository_mode": "remote",
    "version": "6.1.5",
    "output_image": "graph.png",
    "filter_substring": "",
}


class ConfigTestCase(unittest.TestCase):
    """Создаёт временные конфигурационные файлы."""

    def make_file(self, text, suffix=".json"):
        """Сохраняет текст во временный файл и возвращает путь."""
        handle, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(handle, "w", encoding="utf-8") as config_file:
            config_file.write(text)
        self.addCleanup(os.remove, path)
        return path

    def make_config(self, **changes):
        """Создаёт конфиг на основе правильного, изменяя параметры."""
        data = dict(VALID_REMOTE, **changes)
        return self.make_file(json.dumps(data))

    def make_test_config(self, **changes):
        """Создаёт правильный конфиг для тестового режима."""
        repository = self.make_file("A: B\nB:\n", suffix=".txt")
        data = dict(VALID_REMOTE, package_name="A",
                    repository=repository, repository_mode="test")
        data.update(changes)
        return self.make_file(json.dumps(data))

    def assert_error(self, path, text):
        """Проверяет, что среди ошибок есть сообщение с текстом."""
        with self.assertRaises(ConfigError) as context:
            load_config(path)
        self.assertTrue(
            any(text in message for message in context.exception.messages),
            context.exception.messages,
        )


class TestValidConfig(ConfigTestCase):
    """Проверяет загрузку правильных конфигураций."""

    def test_remote_mode(self):
        """Проверяет правильный конфиг для реального репозитория."""
        config = load_config(self.make_config())
        self.assertEqual(config.package_name, VALID_REMOTE["package_name"])
        self.assertEqual(config.repository_mode, "remote")

    def test_test_mode(self):
        """Проверяет правильный конфиг для тестового репозитория."""
        config = load_config(self.make_test_config())
        self.assertEqual(config.package_name, "A")

    def test_items_order(self):
        """Проверяет порядок параметров при выводе."""
        config = load_config(self.make_config())
        keys = [key for key, _ in config.items()]
        self.assertEqual(keys, list(VALID_REMOTE))

    def test_example_configs(self):
        """Проверяет, что примеры из репозитория загружаются."""
        load_config("config.json")
        load_config(os.path.join("configs", "test_mode.json"))


class TestFileErrors(ConfigTestCase):
    """Проверяет ошибки чтения файла."""

    def test_missing_file(self):
        """Проверяет отсутствующий файл."""
        self.assert_error("no_such_config.json", "cannot read")

    def test_invalid_json(self):
        """Проверяет файл с неверным JSON."""
        self.assert_error(self.make_file("{ broken"), "not valid JSON")

    def test_not_object(self):
        """Проверяет JSON, который не является объектом."""
        self.assert_error(self.make_file("[1, 2]"), "JSON object")

    def test_missing_parameter(self):
        """Проверяет отсутствие параметра."""
        data = dict(VALID_REMOTE)
        del data["version"]
        path = self.make_file(json.dumps(data))
        self.assert_error(path, "version: parameter is missing")

    def test_unknown_parameter(self):
        """Проверяет лишний параметр."""
        path = self.make_config(color="red")
        self.assert_error(path, "color: unknown parameter")


class TestParameterErrors(ConfigTestCase):
    """Проверяет ошибки каждого параметра."""

    def test_package_name_format(self):
        """Проверяет имя пакета без groupId."""
        path = self.make_config(package_name="spring-core")
        self.assert_error(path, "package_name: must be in Maven format")

    def test_package_name_empty(self):
        """Проверяет пустое имя пакета."""
        path = self.make_config(package_name="  ")
        self.assert_error(path, "package_name: must not be empty")

    def test_test_package_name(self):
        """Проверяет имя пакета в тестовом режиме."""
        path = self.make_test_config(package_name="a")
        self.assert_error(path, "package_name: in test mode")

    def test_repository_url(self):
        """Проверяет неверный URL репозитория."""
        path = self.make_config(repository="ftp://example.com")
        self.assert_error(path, "repository: must be a URL")

    def test_repository_file(self):
        """Проверяет отсутствующий файл тестового репозитория."""
        path = self.make_test_config(repository="no_such_repo.txt")
        self.assert_error(path, "repository: test repository file")

    def test_repository_mode(self):
        """Проверяет неизвестный режим."""
        path = self.make_config(repository_mode="online")
        self.assert_error(path, "repository_mode: must be one of")

    def test_version_format(self):
        """Проверяет версию с пробелом."""
        path = self.make_config(version="1.0 beta")
        self.assert_error(path, "version: may contain only")

    def test_version_type(self):
        """Проверяет версию, заданную числом."""
        path = self.make_config(version=1.0)
        self.assert_error(path, "version: must be a string")

    def test_output_image_extension(self):
        """Проверяет расширение файла изображения."""
        path = self.make_config(output_image="graph.jpg")
        self.assert_error(path, "output_image: file name must end")

    def test_output_image_folder(self):
        """Проверяет несуществующую папку для изображения."""
        path = self.make_config(output_image="no_such_dir/graph.png")
        self.assert_error(path, "output_image: folder")

    def test_filter_substring_type(self):
        """Проверяет подстроку фильтра, заданную числом."""
        path = self.make_config(filter_substring=42)
        self.assert_error(path, "filter_substring: must be a string")

    def test_all_errors_reported(self):
        """Проверяет, что выводятся ошибки всех параметров сразу."""
        path = self.make_config(package_name="x", version="",
                                output_image="a.jpg")
        with self.assertRaises(ConfigError) as context:
            load_config(path)
        self.assertEqual(len(context.exception.messages), 3)


if __name__ == "__main__":
    unittest.main()