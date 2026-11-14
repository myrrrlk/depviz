# depviz

Инструмент визуализации графа зависимостей для пакетов Java (Maven).
Учебный проект по дисциплине "Конфигурационное управление", вариант 9.

## Описание

Программа должна строить граф зависимостей пакета Maven и сохранять его в
виде картинки. Готовые менеджеры пакетов и библиотеки для получения
зависимостей не используются, всё делается вручную.

Сейчас сделан этап 1: минимальное консольное приложение, которое читает
настройки из конфигурационного файла JSON, проверяет их и выводит на экран
в формате "ключ: значение". Если в настройках есть ошибки, программа
выводит список всех ошибок и завершается с кодом 1.

Для работы нужен Python 3.8 или новее. Сторонние библиотеки не нужны.

## Структура

```
src/main.py        точка входа, вывод параметров
src/config.py      чтение и проверка конфигурационного файла
tests/             тесты
config.json        конфигурация по умолчанию
configs/           другие примеры конфигураций
configs/errors/    конфигурации с ошибками для демонстрации
repos/             тестовые репозитории
scripts/           скрипты для демонстрации работы
run.bat, run.sh    запуск программы
```

## Конфигурационный файл

Настройки задаются в JSON-файле. По умолчанию программа читает
`config.json` из текущей папки, другой файл можно указать параметром
`--config` (или `-c`).

Пример:

```json
{
  "package_name": "org.springframework:spring-core",
  "repository": "https://repo1.maven.org/maven2",
  "repository_mode": "remote",
  "version": "6.1.5",
  "output_image": "graph.png",
  "filter_substring": ""
}
```

Параметры (все обязательные):

- `package_name` - имя анализируемого пакета. В режиме `remote` пишется в
  формате Maven `groupId:artifactId`, например
  `org.springframework:spring-core`. В режиме `test` пакеты называются
  большими латинскими буквами, например `A`.
- `repository` - в режиме `remote` это URL репозитория Maven (должен
  начинаться с `http://` или `https://`), в режиме `test` это путь к файлу
  тестового репозитория (файл должен существовать).
- `repository_mode` - режим работы: `remote` (настоящий репозиторий) или
  `test` (тестовый файл).
- `version` - версия пакета. Можно использовать буквы, цифры и символы
  `.`, `_`, `-`, например `6.1.5` или `33.0.0-jre`.
- `output_image` - имя файла, в который потом будет сохранена картинка
  графа. Должно заканчиваться на `.png`. Если указана папка, она должна
  существовать.
- `filter_substring` - подстрока для фильтрации: пакеты, в имени которых
  она есть, не будут учитываться. Может быть пустой строкой `""`, тогда
  фильтрации нет.

Лишние параметры тоже считаются ошибкой, чтобы опечатка в имени параметра
(например, `filter` вместо `filter_substring`) не прошла незаметно.

## Обработка ошибок

Программа проверяет все параметры сразу и выводит все найденные ошибки, а
не только первую. Проверяется:

- файл существует и его можно прочитать;
- файл содержит правильный JSON, и это объект `{...}`;
- заданы все параметры и нет лишних;
- каждое значение является строкой;
- каждый параметр имеет правильный формат (см. выше).

Пример вывода:

```
Error: invalid configuration in 'configs\errors\wrong_remote.json':
  - package_name: must be in Maven format groupId:artifactId.
  - repository: must be a URL starting with http:// or https://.
  - version: may contain only letters, digits, '.', '_' and '-'.
  - output_image: file name must end with '.png'.
  - filter_substring: must be a string.
```

## Функции

### src/config.py

- `Config` - класс с параметрами из конфигурационного файла. Метод
  `items()` возвращает пары ключ-значение в том порядке, в котором
  объявлены поля.
- `ConfigError` - ошибка конфигурации, хранит список сообщений
  `messages`.
- `load_config(path)` - главная функция модуля: читает файл, проверяет
  ключи и значения, возвращает `Config` или выбрасывает `ConfigError`.
- `read_config_file(path)` - читает JSON-файл и проверяет, что это объект.
- `check_keys(data)` - ищет отсутствующие и лишние параметры.
- `validate_values(data)` - проверяет значения всех параметров через
  словарь `VALIDATORS`.
- `check_string(value, allow_empty)` - общая проверка: значение строка и
  (если нужно) не пустое.
- `validate_package_name`, `validate_repository`, `validate_mode`,
  `validate_version`, `validate_output_image`,
  `validate_filter_substring` - проверки отдельных параметров. Каждая
  возвращает текст ошибки или `None`, если всё правильно. Имя пакета и
  репозиторий проверяются по-разному в зависимости от режима.

### src/main.py

- `parse_arguments(argv)` - разбирает параметр `--config`.
- `format_value(value)` - пустую строку показывает как `""`.
- `print_config(config)` - выводит параметры в формате "ключ: значение".
- `print_config_errors(path, error)` - выводит список ошибок.
- `main(argv)` - точка входа, возвращает код завершения (0 - успех,
  1 - ошибка в конфигурации).

Константы (настройки):

- `DEFAULT_CONFIG = "config.json"` - конфиг по умолчанию;
- `EXIT_SUCCESS = 0`, `EXIT_FAILURE = 1` - коды завершения;
- `MODE_REMOTE = "remote"`, `MODE_TEST = "test"` - режимы работы;
- `URL_SCHEMES = ("http", "https")` - допустимые схемы URL;
- `IMAGE_EXTENSION = ".png"` - расширение файла картинки;
- `MAVEN_NAME_PATTERN`, `TEST_NAME_PATTERN`, `VERSION_PATTERN` - регулярные
  выражения для проверки имени пакета и версии;
- `PARAMETERS` - список всех параметров в порядке вывода.

## Запуск

Сборка не нужна. Запускать нужно из корня проекта.

```
python -m src.main
python -m src.main --config configs\test_mode.json
```

Или через скрипты:

```
run.bat --config configs\test_mode.json
./run.sh --config configs/test_mode.json
```

Демонстрация работы (есть `.bat` для Windows и `.sh` для Linux):

```
scripts\demo.bat          правильные конфигурации
scripts\demo_errors.bat   ошибки во всех параметрах
```

## Тесты

```
python -m unittest discover -s tests -v
```

Проверяются правильные конфигурации для обоих режимов, порядок вывода,
ошибки чтения файла (нет файла, неверный JSON, не объект), отсутствующие
и лишние параметры, ошибки каждого параметра по отдельности, вывод всех
ошибок сразу, вывод "ключ: значение" и коды завершения.

## Примеры

Конфигурация по умолчанию:

```
> python -m src.main
package_name: org.springframework:spring-core
repository: https://repo1.maven.org/maven2
repository_mode: remote
version: 6.1.5
output_image: graph.png
filter_substring: ""
```

Тестовый режим:

```
> python -m src.main --config configs\test_mode.json
package_name: A
repository: repos/basic.txt
repository_mode: test
version: 1.0
output_image: graph_test.png
filter_substring: D
```

Ошибки в тестовом режиме:

```
> python -m src.main --config configs\errors\wrong_test.json
Error: invalid configuration in 'configs\errors\wrong_test.json':
  - package_name: in test mode must consist of capital Latin letters.
  - repository: test repository file 'repos/missing.txt' does not exist.
  - version: must not be empty.
  - output_image: folder 'images' does not exist.
  - filter_substring: must be a string.
```

Неизвестный режим:

```
> python -m src.main --config configs\errors\wrong_mode.json
Error: invalid configuration in 'configs\errors\wrong_mode.json':
  - repository_mode: must be one of: remote, test.
```

Ошибки в именах параметров:

```
> python -m src.main --config configs\errors\wrong_keys.json
Error: invalid configuration in 'configs\errors\wrong_keys.json':
  - filter_substring: parameter is missing.
  - filter: unknown parameter.
```

Нет файла:

```
> python -m src.main --config configs\missing.json
Error: invalid configuration in 'configs\missing.json':
  - cannot read config file 'configs\missing.json'.
```