"""Получение прямых зависимостей пакета из репозитория Maven.

POM-файлы скачиваются по HTTP и разбираются вручную, без Maven и без
сторонних библиотек.
"""

import functools
import re
import urllib.error
import urllib.request
import xml.etree.ElementTree as element_tree
from dataclasses import dataclass, field

from src.graph import SourceError


REQUEST_TIMEOUT = 15
USER_AGENT = "depviz/1.0"
HTTP_NOT_FOUND = 404
MAX_SUBSTITUTIONS = 10
DEFAULT_SCOPE = "compile"
IMPORT_SCOPE = "import"
TRANSITIVE_SCOPES = ("compile", "runtime")
PROPERTY_PATTERN = re.compile(r"\$\{([^}]+)\}")


class MavenError(SourceError):
    """Ошибка получения или разбора POM-файла."""


@dataclass(frozen=True)
class Dependency:
    """Прямая зависимость пакета."""

    group_id: str
    artifact_id: str
    version: str
    scope: str = DEFAULT_SCOPE
    optional: bool = False

    @property
    def name(self):
        """Имя пакета в формате groupId:artifactId."""
        return f"{self.group_id}:{self.artifact_id}"

    def describe(self):
        """Возвращает строку для вывода на экран."""
        details = self.scope + (", optional" if self.optional else "")
        return f"{self.name}:{self.version} ({details})"


@dataclass
class Pom:
    """Содержимое POM-файла, нужное для поиска зависимостей."""

    group_id: str
    artifact_id: str
    version: str
    parent: tuple = None
    properties: dict = field(default_factory=dict)
    managed: list = field(default_factory=list)
    dependencies: list = field(default_factory=list)


def split_package_name(package_name):
    """Делит имя groupId:artifactId на две части."""
    group_id, artifact_id = package_name.split(":")
    return group_id, artifact_id


def pom_url(repository, group_id, artifact_id, version):
    """Строит URL POM-файла по правилам раскладки репозитория Maven."""
    group_path = group_id.replace(".", "/")
    file_name = f"{artifact_id}-{version}.pom"
    return "/".join([repository.rstrip("/"), group_path, artifact_id,
                     version, file_name])


@functools.lru_cache(maxsize=None)
def download(url):
    """Скачивает файл по URL и возвращает его содержимое в байтах.

    Результат запоминается (кэш), чтобы не скачивать один файл дважды.
    """
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as answer:
            return answer.read()
    except urllib.error.HTTPError as error:
        if error.code == HTTP_NOT_FOUND:
            raise MavenError(f"POM file not found: {url}") from error
        raise MavenError(f"HTTP error {error.code}: {url}") from error
    except (urllib.error.URLError, OSError) as error:
        raise MavenError(f"cannot connect to repository: {url}") from error


def strip_namespaces(root):
    """Убирает пространство имён из тегов, чтобы искать их по имени."""
    for element in root.iter():
        element.tag = element.tag.split("}")[-1]


def text_of(element, tag, default=None):
    """Возвращает текст дочернего тега или значение по умолчанию."""
    child = element.find(tag)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def read_dependency_list(element):
    """Читает список тегов dependency внутри element."""
    if element is None:
        return []
    return [{
        "group_id": text_of(item, "groupId"),
        "artifact_id": text_of(item, "artifactId"),
        "version": text_of(item, "version"),
        "scope": text_of(item, "scope", DEFAULT_SCOPE),
        "optional": text_of(item, "optional", "false") == "true",
    } for item in element.findall("dependency")]


def read_parent(root):
    """Возвращает (groupId, artifactId, version) родителя или None."""
    parent = root.find("parent")
    if parent is None:
        return None
    return (text_of(parent, "groupId"), text_of(parent, "artifactId"),
            text_of(parent, "version"))


def parse_pom(data):
    """Разбирает POM-файл и возвращает объект Pom."""
    try:
        root = element_tree.fromstring(data)
    except element_tree.ParseError as error:
        raise MavenError(f"invalid POM file: {error}") from error
    strip_namespaces(root)

    parent = read_parent(root)
    parent_group, _, parent_version = parent or (None, None, None)
    properties_tag = root.find("properties")
    properties = {}
    if properties_tag is not None:
        properties = {item.tag: (item.text or "").strip()
                      for item in properties_tag}
    return Pom(
        group_id=text_of(root, "groupId", parent_group),
        artifact_id=text_of(root, "artifactId"),
        version=text_of(root, "version", parent_version),
        parent=parent,
        properties=properties,
        managed=read_dependency_list(
            root.find("dependencyManagement/dependencies")),
        dependencies=read_dependency_list(root.find("dependencies")),
    )


def load_pom(repository, group_id, artifact_id, version):
    """Скачивает и разбирает POM-файл пакета."""
    return parse_pom(download(pom_url(repository, group_id, artifact_id,
                                      version)))


def substitute(value, properties):
    """Подставляет значения свойств вида ${name} в строку."""
    if value is None:
        return None
    for _ in range(MAX_SUBSTITUTIONS):
        new_value = PROPERTY_PATTERN.sub(
            lambda match: properties.get(match.group(1), match.group(0)),
            value)
        if new_value == value:
            break
        value = new_value
    return value


def builtin_properties(pom):
    """Возвращает встроенные свойства проекта (project.version и др.)."""
    return {
        "project.groupId": pom.group_id,
        "project.artifactId": pom.artifact_id,
        "project.version": pom.version,
        "pom.version": pom.version,
        "version": pom.version,
        "project.parent.version": pom.parent[2] if pom.parent else None,
    }


def load_parent_chain(repository, pom):
    """Возвращает список POM: сам пакет и всех его родителей."""
    chain = [pom]
    seen = set()
    while chain[-1].parent and chain[-1].parent not in seen:
        seen.add(chain[-1].parent)
        chain.append(load_pom(repository, *chain[-1].parent))
    return chain


def collect_properties(chain):
    """Собирает свойства из цепочки POM (свойства потомка важнее)."""
    properties = {}
    for pom in chain:
        for key, value in pom.properties.items():
            properties.setdefault(key, value)
    properties.update({key: value for key, value
                       in builtin_properties(chain[0]).items() if value})
    return properties


def collect_managed_versions(repository, chain, properties):
    """Собирает версии из dependencyManagement, включая импорт BOM."""
    versions = {}
    pending = [(entry, properties) for pom in chain for entry in pom.managed]
    seen_boms = set()
    while pending:
        entry, props = pending.pop(0)
        name = (substitute(entry["group_id"], props),
                substitute(entry["artifact_id"], props))
        version = substitute(entry["version"], props)
        if entry["scope"] != IMPORT_SCOPE:
            versions.setdefault(name, version)
        elif (*name, version) not in seen_boms:
            seen_boms.add((*name, version))
            bom_chain = load_parent_chain(
                repository, load_pom(repository, *name, version))
            bom_props = collect_properties(bom_chain)
            pending.extend((item, bom_props) for pom in bom_chain
                           for item in pom.managed)
    return versions


def make_dependency(entry, properties, managed):
    """Создаёт Dependency, подставляя свойства и версию из management."""
    group_id = substitute(entry["group_id"], properties)
    artifact_id = substitute(entry["artifact_id"], properties)
    version = substitute(entry["version"], properties)
    if version is None:
        version = managed.get((group_id, artifact_id), "unknown")
    return Dependency(group_id, artifact_id, version, entry["scope"],
                      entry["optional"])


def collect_dependency_entries(chain):
    """Собирает зависимости пакета и унаследованные от родителей."""
    entries = {}
    for pom in chain:
        for entry in pom.dependencies:
            key = (entry["group_id"], entry["artifact_id"])
            entries.setdefault(key, entry)
    return list(entries.values())


def get_direct_dependencies(repository, package_name, version):
    """Возвращает список прямых зависимостей пакета заданной версии."""
    group_id, artifact_id = split_package_name(package_name)
    pom = load_pom(repository, group_id, artifact_id, version)
    chain = load_parent_chain(repository, pom)
    properties = collect_properties(chain)
    managed = collect_managed_versions(repository, chain, properties)
    return [make_dependency(entry, properties, managed)
            for entry in collect_dependency_entries(chain)]


def is_transitive(dependency):
    """Проверяет, идёт ли зависимость дальше по графу (как в Maven)."""
    return dependency.scope in TRANSITIVE_SCOPES and not dependency.optional


class MavenSource:
    """Источник зависимостей для построения графа: репозиторий Maven.

    Пакеты в графе называются groupId:artifactId, а их версии хранятся
    в словаре versions. Дальше по графу идут только зависимости со scope
    compile или runtime и без optional, как это делает Maven.
    """

    def __init__(self, repository, package_name, version):
        """Запоминает адрес репозитория и версию корневого пакета."""
        self.repository = repository
        self.versions = {package_name: version}

    def dependencies(self, name):
        """Возвращает имена зависимостей пакета, которые идут дальше."""
        found = get_direct_dependencies(self.repository, name,
                                        self.versions[name])
        names = []
        for dependency in found:
            if is_transitive(dependency):
                self.versions.setdefault(dependency.name, dependency.version)
                names.append(dependency.name)
        return names

    def label(self, name):
        """Возвращает подпись пакета: имя и версию."""
        return f"{name}:{self.versions[name]}"