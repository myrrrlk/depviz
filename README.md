# depviz

Инструмент визуализации графа зависимостей для пакетов Java (Maven).
Учебный проект по дисциплине "Конфигурационное управление", вариант 9.

## Описание

Программа должна строить граф зависимостей пакета Maven и сохранять его в
виде картинки. Готовые менеджеры пакетов и библиотеки для получения
зависимостей не используются, всё делается вручную.

Сделано два этапа:

- этап 1: консольное приложение читает настройки из конфигурационного
  файла JSON и проверяет их. Если в настройках есть ошибки, программа
  выводит список всех ошибок и завершается с кодом 1. На этом этапе
  программа выводила все параметры в формате "ключ: значение";
- этап 2: программа скачивает POM-файл пакета нужной версии из
  репозитория Maven, сама разбирает его и выводит прямые зависимости
  пакета. Менеджеры пакетов и сторонние библиотеки не используются,
  только стандартная библиотека Python (`urllib` и `xml.etree`).

Для работы нужен Python 3.8 или новее. Сторонние библиотеки не нужны.

## Структура

```
src/main.py        точка входа, вывод зависимостей
src/config.py      чтение и проверка конфигурационного файла
src/maven.py       скачивание и разбор POM-файлов Maven
src/repo_file.py   тестовый репозиторий в текстовом файле
tests/             тесты
tests/data/maven/  POM-файлы для тестов (маленький репозиторий Maven)
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

## Как ищутся зависимости (Maven)

Каждый пакет Maven описывается POM-файлом в формате XML. В репозитории он
лежит по адресу, который строится из имени и версии пакета:

```
{repository}/{groupId с / вместо .}/{artifactId}/{version}/{artifactId}-{version}.pom
```

Например, для `org.springframework:spring-core` версии `6.1.5`:

```
https://repo1.maven.org/maven2/org/springframework/spring-core/6.1.5/spring-core-6.1.5.pom
```

Программа скачивает этот файл и берёт из него список `<dependencies>`.
Чтобы версии зависимостей получились правильными, учитывается то же, что
учитывает Maven:

- родительский POM (`<parent>`): программа скачивает всю цепочку
  родителей, берёт из них свойства, `dependencyManagement` и
  зависимости, которые наследуются;
- свойства вида `${spring.version}` из `<properties>`, а также
  `${project.version}`, `${project.groupId}` и т.п.;
- `<dependencyManagement>`: если у зависимости не указана версия, она
  берется оттуда;
- импорт BOM (`<scope>import</scope>` в `dependencyManagement`).

Для каждой зависимости выводится `groupId:artifactId:version` и в скобках
scope (`compile`, `runtime`, `test`, `provided`), а для необязательных
зависимостей ещё `optional`.

## Тестовый репозиторий

В режиме `test` вместо Maven используется текстовый файл, где пакеты
называются большими латинскими буквами. Каждая строка описывает один
пакет и его зависимости:

```
A: B C
B: D
C: D
D:
```

Здесь A зависит от B и C, B и C зависят от D, у D зависимостей нет.
Пустые строки и строки, начинающиеся с `#`, пропускаются.

## Обработка ошибок

Программа проверяет все параметры сразу и выводит все найденные ошибки, а
не только первую. Проверяется:

- файл существует и его можно прочитать;
- файл содержит правильный JSON, и это объект `{...}`;
- заданы все параметры и нет лишних;
- каждое значение является строкой;
- каждый параметр имеет правильный формат (см. выше).

Ошибки при получении зависимостей (программа тоже завершается с кодом 1):

- POM-файл не найден (нет такого пакета или такой версии);
- нет связи с репозиторием или ошибка HTTP;
- POM-файл не является правильным XML;
- в тестовом репозитории нет нужного пакета, строка без `:`, имя пакета
  не из больших букв, пакет описан два раза.

Пример вывода ошибок конфигурации:

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

### src/maven.py

- `Dependency` - зависимость: `group_id`, `artifact_id`, `version`,
  `scope`, `optional`. Свойство `name` дает `groupId:artifactId`, метод
  `describe()` - строку для вывода.
- `Pom` - нужные данные из POM-файла: имя, версия, родитель, свойства,
  `dependencyManagement` и зависимости.
- `MavenError` - ошибка получения или разбора POM.
- `get_direct_dependencies(repository, package_name, version)` - главная
  функция модуля: возвращает список прямых зависимостей.
- `pom_url(...)` - строит адрес POM-файла.
- `download(url)` - скачивает файл через `urllib`.
- `parse_pom(data)` - разбирает XML через `xml.etree.ElementTree`.
- `load_pom(...)` - скачивает и разбирает POM.
- `load_parent_chain(repository, pom)` - скачивает всех родителей (циклом,
  без рекурсии, с защитой от зацикливания).
- `collect_properties(chain)` - собирает свойства (свойства потомка
  важнее свойств родителя).
- `collect_managed_versions(...)` - собирает версии из
  `dependencyManagement`, включая импортированные BOM.
- `collect_dependency_entries(chain)` - собирает зависимости пакета и
  унаследованные от родителей.
- `substitute(value, properties)` - подставляет `${...}`.
- `make_dependency(...)` - создает `Dependency` с готовой версией.

### src/repo_file.py

- `load_repository(path)` - читает файл и возвращает словарь
  "пакет -> список зависимостей".
- `parse_line(line, number)` - разбирает строку `A: B C`.
- `check_name(name, number)` - проверяет имя пакета.
- `get_direct_dependencies(path, package_name)` - прямые зависимости
  пакета.
- `RepoFileError` - ошибка тестового репозитория.

### src/main.py

- `parse_arguments(argv)` - разбирает параметр `--config`.
- `print_config_errors(path, error)` - выводит список ошибок конфигурации.
- `find_direct_dependencies(config)` - выбирает Maven или тестовый
  репозиторий в зависимости от режима и возвращает зависимости.
- `package_title(config)` - имя пакета с версией для заголовка.
- `print_dependencies(title, dependencies)` - выводит список зависимостей.
- `main(argv)` - точка входа, возвращает код завершения (0 - успех,
  1 - ошибка).

Константы (настройки):

- `DEFAULT_CONFIG = "config.json"` - конфиг по умолчанию;
- `EXIT_SUCCESS = 0`, `EXIT_FAILURE = 1` - коды завершения;
- `MODE_REMOTE = "remote"`, `MODE_TEST = "test"` - режимы работы;
- `URL_SCHEMES = ("http", "https")` - допустимые схемы URL;
- `IMAGE_EXTENSION = ".png"` - расширение файла картинки;
- `MAVEN_NAME_PATTERN`, `TEST_NAME_PATTERN`, `VERSION_PATTERN` - регулярные
  выражения для проверки имени пакета и версии;
- `PARAMETERS` - список всех параметров;
- `REQUEST_TIMEOUT = 15` - сколько секунд ждать ответа репозитория;
- `USER_AGENT` - как программа представляется серверу;
- `DEFAULT_SCOPE = "compile"` - scope, если он не указан в POM;
- `MAX_SUBSTITUTIONS = 10` - сколько раз подряд подставлять `${...}`
  (если одно свойство ссылается на другое).

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

Для работы с Maven Central нужен интернет.

Демонстрация работы (есть `.bat` для Windows и `.sh` для Linux):

```
scripts\demo.bat          зависимости spring-core, commons-text, guava
                          и пакета A из тестового репозитория
scripts\demo_errors.bat   ошибки конфигурации и ошибки получения данных
```

## Тесты

```
python -m unittest discover -s tests -v
```

Тесты не обращаются к интернету: для проверки работы с Maven они
запускают локальный HTTP-сервер, который отдает POM-файлы из
`tests/data/maven`. В этих файлах есть родитель, свойства,
`dependencyManagement`, импорт BOM, зависимости с `test` и `optional`.

Проверяются конфигурация (оба режима, все ошибки), построение адреса
POM-файла, поиск прямых зависимостей с учетом родителя, свойств и BOM,
ошибки (нет версии, плохой XML, нет связи), тестовый репозиторий и его
ошибки, вывод и коды завершения.

## Примеры

Тестовый репозиторий:

```
> python -m src.main --config configs\test_mode.json
Direct dependencies of A:
  - B
  - C
Total: 2
```

Пакет из Maven Central (вывод зависит от пакета, здесь показан формат):

```
> python -m src.main
Direct dependencies of org.springframework:spring-core:6.1.5:
  - groupId:artifactId:version (scope)
  - groupId:artifactId:version (scope, optional)
  ...
Total: N
```

Версии нет в репозитории:

```
> python -m src.main --config configs\errors\version_not_found.json
Error: POM file not found: https://repo1.maven.org/maven2/org/springframework/spring-core/0.0.1/spring-core-0.0.1.pom
```

Пакета нет в тестовом репозитории:

```
> python -m src.main --config configs\errors\unknown_test_package.json
Error: package 'Z' not found in 'repos/basic.txt'.
```

Ошибки в конфигурации:

```
> python -m src.main --config configs\errors\wrong_test.json
Error: invalid configuration in 'configs\errors\wrong_test.json':
  - package_name: in test mode must consist of capital Latin letters.
  - repository: test repository file 'repos/missing.txt' does not exist.
  - version: must not be empty.
  - output_image: folder 'images' does not exist.
  - filter_substring: must be a string.
```