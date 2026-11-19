"""Тесты получения прямых зависимостей из репозитория Maven.

Вместо настоящего Maven Central тесты запускают локальный HTTP-сервер,
который отдаёт POM-файлы из папки tests/data/maven.
"""

import functools
import os
import threading
import unittest
import urllib.request
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

from src import maven
from src.graph import build_graph


DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "data", "maven")



def setupmodule(): 
    """Отключает системный прокси: тесты обращаются к 127.0.0.1."""
    no_proxy = urllib.request.ProxyHandler({})
    urllib.request.install_opener(urllib.request.build_opener(no_proxy))


def teardownmodule(): 
    """Возвращает обычные настройки urllib после тестов."""
    urllib.request.install_opener(None)

class QuietHandler(SimpleHTTPRequestHandler):
    """Обработчик HTTP-запросов, который не печатает журнал."""

    def log_message(self, *args):
        """Отключает вывод журнала запросов."""


class LocalRepository:
    """Локальный HTTP-сервер с тестовым репозиторием Maven."""

    def __init__(self):
        """Запускает сервер на свободном порту."""
        handler = functools.partial(QuietHandler, directory=DATA_DIR)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        self.url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(target=self.server.serve_forever,
                                       daemon=True)
        self.thread.start()

    def stop(self):
        """Останавливает сервер."""
        self.server.shutdown()
        self.server.server_close()


class RepositoryTestCase(unittest.TestCase):
    """Запускает локальный репозиторий на время тестов класса."""

    @classmethod
    def setUpClass(cls):
        """Запускает сервер перед тестами."""
        cls.repository = LocalRepository()

    @classmethod
    def tearDownClass(cls):
        """Останавливает сервер после тестов."""
        cls.repository.stop()

    def dependencies(self, package_name, version):
        """Возвращает зависимости в виде словаря имя -> Dependency."""
        found = maven.get_direct_dependencies(
            self.repository.url, package_name, version)
        return {dependency.name: dependency for dependency in found}


class TestPomUrl(unittest.TestCase):
    """Проверяет построение URL POM-файла."""

    def test_url(self):
        """Проверяет раскладку groupId по папкам."""
        url = maven.pom_url("https://repo1.maven.org/maven2/",
                            "org.springframework", "spring-core", "6.1.5")
        self.assertEqual(
            url, "https://repo1.maven.org/maven2/org/springframework/"
            "spring-core/6.1.5/spring-core-6.1.5.pom")


class TestDirectDependencies(RepositoryTestCase):
    """Проверяет поиск прямых зависимостей."""

    def test_all_dependencies_found(self):
        """Проверяет, что найдены все зависимости, включая наследуемые."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(len(found), 7)
        self.assertIn("com.example:logging", found)

    def test_version_from_property(self):
        """Проверяет подстановку свойства ${lib.version}."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(found["com.example:lib"].version, "2.0")

    def test_version_from_parent_management(self):
        """Проверяет версию из dependencyManagement родителя."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(found["com.example:util"].version, "3.1")

    def test_project_properties(self):
        """Проверяет ${project.groupId} и ${project.version}."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(found["com.example:core"].version, "1.0")

    def test_version_from_imported_bom(self):
        """Проверяет версию из импортированного BOM."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(found["com.example:managed-by-bom"].version, "5.0")

    def test_scope_and_optional(self):
        """Проверяет scope и признак optional."""
        found = self.dependencies("com.example:app", "1.0")
        self.assertEqual(found["junit:junit"].scope, "test")
        self.assertTrue(found["com.example:extras"].optional)

    def test_no_dependencies(self):
        """Проверяет пакет без зависимостей и POM без namespace."""
        self.assertEqual(self.dependencies("com.example:lib", "2.0"), {})


class TestErrors(RepositoryTestCase):
    """Проверяет ошибки получения POM-файла."""

    def test_unknown_version(self):
        """Проверяет несуществующую версию пакета."""
        with self.assertRaisesRegex(maven.MavenError, "not found"):
            self.dependencies("com.example:app", "9.9")

    def test_invalid_pom(self):
        """Проверяет повреждённый POM-файл."""
        with self.assertRaisesRegex(maven.MavenError, "invalid POM"):
            self.dependencies("com.example:broken", "1.0")

    def test_no_connection(self):
        """Проверяет недоступный репозиторий."""
        with self.assertRaisesRegex(maven.MavenError, "cannot connect"):
            maven.get_direct_dependencies(
                "http://127.0.0.1:1", "com.example:app", "1.0")


class TestMavenGraph(RepositoryTestCase):
    """Проверяет построение графа по репозиторию Maven."""

    def build(self):
        """Строит граф для com.example:app версии 1.0."""
        source = maven.MavenSource(self.repository.url, "com.example:app",
                                   "1.0")
        return source, build_graph(source, "com.example:app")

    def test_only_transitive_dependencies(self):
        """Проверяет, что test и optional зависимости не идут в граф."""
        _, graph = self.build()
        children = graph.edges["com.example:app"]
        self.assertIn("com.example:lib", children)
        self.assertNotIn("junit:junit", children)
        self.assertNotIn("com.example:extras", children)

    def test_cycle(self):
        """Проверяет цикл app -> core -> app."""
        _, graph = self.build()
        self.assertIn(["com.example:app", "com.example:core",
                       "com.example:app"], graph.cycles)

    def test_missing_pom_is_reported(self):
        """Проверяет, что отсутствующий POM попадает в список ошибок."""
        _, graph = self.build()
        self.assertIn("com.example:util", graph.errors)

    def test_labels_with_versions(self):
        """Проверяет подписи пакетов с версиями."""
        source, _ = self.build()
        self.assertEqual(source.label("com.example:lib"),
                         "com.example:lib:2.0")
        

if __name__ == "__main__":
    unittest.main()