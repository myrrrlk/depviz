"""Загрузка и проверка конфигурационного файла в формате JSON."""

import json
import os
import re
from dataclasses import asdict, dataclass
from urllib.parse import urlparse


MODE_REMOTE = "remote"
MODE_TEST = "test"
MODES = (MODE_REMOTE, MODE_TEST)
URL_SCHEMES = ("http", "https")
IMAGE_EXTENSION = ".png"

MAVEN_NAME_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+:[A-Za-z0-9_.-]+$")
TEST_NAME_PATTERN = re.compile(r"^[A-Z]+$")
VERSION_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

PARAMETERS = (
    "package_name",
    "repository",
    "repository_mode",
    "version",
    "output_image",
    "filter_substring",
)


class ConfigError(Exception):
    """Ошибка конфигурации. Хранит список всех найденных проблем."""

    def __init__(self, messages):
        """Сохраняет список сообщений об ошибках."""
        super().__init__("; ".join(messages))
        self.messages = messages


@dataclass
class Config:
    """Параметры, которые пользователь задаёт в конфигурационном файле."""

    package_name: str
    repository: str
    repository_mode: str
    version: str
    output_image: str
    filter_substring: str

    def items(self):
        """Возвращает пары (ключ, значение) в порядке объявления полей."""
        return asdict(self).items()


def read_config_file(path):
    """Читает JSON-файл и возвращает его содержимое в виде словаря."""
    try:
        with open(path, encoding="utf-8") as config_file:
            data = json.load(config_file)
    except OSError as error:
        raise ConfigError([f"cannot read config file '{path}'."]) from error
    except ValueError as error:
        message = f"config file '{path}' is not valid JSON: {error}"
        raise ConfigError([message]) from error

    if not isinstance(data, dict):
        raise ConfigError(["config file must contain a JSON object."])
    return data


def check_keys(data):
    """Проверяет, что заданы все параметры и нет лишних."""
    errors = []
    for key in PARAMETERS:
        if key not in data:
            errors.append(f"{key}: parameter is missing.")
    for key in data:
        if key not in PARAMETERS:
            errors.append(f"{key}: unknown parameter.")
    return errors


def check_string(value, allow_empty=False):
    """Проверяет, что значение является строкой (непустой)."""
    if not isinstance(value, str):
        return "must be a string."
    if not allow_empty and not value.strip():
        return "must not be empty."
    return None


def validate_mode(value, mode):
    """Проверяет режим работы с репозиторием."""
    error = check_string(value)
    if error:
        return error
    if value not in MODES:
        return f"must be one of: {', '.join(MODES)}."
    return None


def validate_package_name(value, mode):
    """Проверяет имя пакета с учётом режима работы."""
    error = check_string(value)
    if error:
        return error
    if mode == MODE_REMOTE and not MAVEN_NAME_PATTERN.match(value):
        return "must be in Maven format groupId:artifactId."
    if mode == MODE_TEST and not TEST_NAME_PATTERN.match(value):
        return "in test mode must consist of capital Latin letters."
    return None


def validate_repository(value, mode):
    """Проверяет URL репозитория или путь к тестовому файлу."""
    error = check_string(value)
    if error:
        return error
    if mode == MODE_REMOTE:
        url = urlparse(value)
        if url.scheme not in URL_SCHEMES or not url.netloc:
            return "must be a URL starting with http:// or https://."
    if mode == MODE_TEST and not os.path.isfile(value):
        return f"test repository file '{value}' does not exist."
    return None


def validate_version(value, mode):
    """Проверяет версию пакета."""
    error = check_string(value)
    if error:
        return error
    if not VERSION_PATTERN.match(value):
        return "may contain only letters, digits, '.', '_' and '-'."
    return None


def validate_output_image(value, mode):
    """Проверяет имя файла для изображения графа."""
    error = check_string(value)
    if error:
        return error
    if not value.lower().endswith(IMAGE_EXTENSION):
        return f"file name must end with '{IMAGE_EXTENSION}'."
    folder = os.path.dirname(value)
    if folder and not os.path.isdir(folder):
        return f"folder '{folder}' does not exist."
    return None


def validate_filter_substring(value, mode):
    """Проверяет подстроку для фильтрации (может быть пустой)."""
    return check_string(value, allow_empty=True)


VALIDATORS = {
    "package_name": validate_package_name,
    "repository": validate_repository,
    "repository_mode": validate_mode,
    "version": validate_version,
    "output_image": validate_output_image,
    "filter_substring": validate_filter_substring,
}


def validate_values(data):
    """Проверяет значения всех параметров и возвращает список ошибок."""
    mode = data.get("repository_mode")
    errors = []
    for key in PARAMETERS:
        error = VALIDATORS[key](data[key], mode)
        if error:
            errors.append(f"{key}: {error}")
    return errors


def load_config(path):
    """Загружает и проверяет конфигурацию.

    Если найдены ошибки, выбрасывает ConfigError со списком всех ошибок.
    """
    data = read_config_file(path)
    errors = check_keys(data)
    if errors:
        raise ConfigError(errors)

    errors = validate_values(data)
    if errors:
        raise ConfigError(errors)
    return Config(**data)