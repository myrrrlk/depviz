"""Визуализация графа: текст на языке Mermaid и изображение PNG.

Mermaid - язык описания диаграмм. Чтобы получить из него картинку,
программа по очереди пробует три способа: Mermaid CLI (mmdc), если он
установлен, и веб-сервисы mermaid.ink и kroki.io.
"""

import base64
import os
import shutil
import subprocess
import tempfile
import urllib.error
import urllib.request


MERMAID_INK_URL = "https://mermaid.ink/img/{}?type=png"
KROKI_URL = "https://kroki.io/mermaid/png"
USER_AGENT = "depviz/1.0"
RENDER_TIMEOUT = 60
MAX_MESSAGE_LENGTH = 200
PNG_SIGNATURE = b"\x89PNG"
MERMAID_EXTENSION = ".mmd"
ROOT_STYLE = "fill:#ffe9a8,stroke:#b8860b,stroke-width:2px"
CYCLE_STYLE = "stroke:#d62728,stroke-width:2px"


class RenderError(Exception):
    """Ошибка получения изображения графа."""


def escape_label(text):
    """Заменяет кавычки, которые нельзя использовать в подписи Mermaid."""
    return text.replace('"', "#quot;")


def cycle_edges(graph):
    """Возвращает множество рёбер (откуда, куда), входящих в циклы."""
    edges = set()
    for cycle in graph.cycles:
        edges.update(zip(cycle, cycle[1:]))
    return edges


def to_mermaid(graph, source):
    """Строит текстовое описание графа на языке Mermaid.

    Пакеты получают короткие идентификаторы n0, n1, ..., потому что в
    именах Maven есть символы ':' и '.', а подпись пишется в кавычках.
    Корневой пакет выделяется цветом, рёбра циклов - красным.
    """
    ids = {name: f"n{index}" for index, name in enumerate(graph.edges)}
    lines = ["graph TD"]
    for name, node_id in ids.items():
        lines.append(f'    {node_id}["{escape_label(source.label(name))}"]')

    in_cycle = cycle_edges(graph)
    red_edges = []
    edge_number = 0
    for name, children in graph.edges.items():
        for child in children:
            lines.append(f"    {ids[name]} --> {ids[child]}")
            if (name, child) in in_cycle:
                red_edges.append(str(edge_number))
            edge_number += 1

    lines.append(f"    style {ids[graph.root]} {ROOT_STYLE}")
    if red_edges:
        lines.append(f"    linkStyle {','.join(red_edges)} {CYCLE_STYLE}")
    return "\n".join(lines) + "\n"


def mermaid_path(image_path):
    """Возвращает имя файла .mmd рядом с файлом изображения."""
    return os.path.splitext(image_path)[0] + MERMAID_EXTENSION


def save_text(text, path):
    """Сохраняет текст в файл в кодировке UTF-8."""
    with open(path, "w", encoding="utf-8") as text_file:
        text_file.write(text)


def save_png(data, path):
    """Проверяет, что данные - это PNG, и сохраняет их в файл."""
    if not data.startswith(PNG_SIGNATURE):
        raise RenderError("the answer is not a PNG image.")
    with open(path, "wb") as image_file:
        image_file.write(data)


def download(request):
    """Выполняет HTTP-запрос и возвращает ответ в байтах."""
    try:
        with urllib.request.urlopen(request,
                                    timeout=RENDER_TIMEOUT) as answer:
            return answer.read()
    except (urllib.error.URLError, OSError) as error:
        raise RenderError(f"request failed: {error}") from error


def render_with_mmdc(text, path):
    """Рисует PNG программой Mermaid CLI (mmdc), если она установлена."""
    mmdc = shutil.which("mmdc")
    if mmdc is None:
        raise RenderError("mmdc is not installed.")
    with tempfile.TemporaryDirectory() as folder:
        source_path = os.path.join(folder, "graph" + MERMAID_EXTENSION)
        save_text(text, source_path)
        try:
            result = subprocess.run(
                [mmdc, "-i", source_path, "-o", os.path.abspath(path)],
                capture_output=True, text=True, timeout=RENDER_TIMEOUT,
                check=False)
        except (subprocess.TimeoutExpired, OSError) as error:
            raise RenderError(f"mmdc failed: {error}") from error
    if result.returncode:
        message = result.stderr.strip()[:MAX_MESSAGE_LENGTH]
        raise RenderError(f"mmdc failed: {message}")


def render_with_mermaid_ink(text, path):
    """Рисует PNG сервисом mermaid.ink (текст передаётся в base64)."""
    encoded = base64.urlsafe_b64encode(text.encode("utf-8")).decode("ascii")
    request = urllib.request.Request(MERMAID_INK_URL.format(encoded),
                                     headers={"User-Agent": USER_AGENT})
    save_png(download(request), path)


def render_with_kroki(text, path):
    """Рисует PNG сервисом kroki.io (текст передаётся в теле запроса)."""
    request = urllib.request.Request(
        KROKI_URL, data=text.encode("utf-8"),
        headers={"Content-Type": "text/plain", "User-Agent": USER_AGENT})
    save_png(download(request), path)


RENDERERS = (
    ("Mermaid CLI (mmdc)", render_with_mmdc),
    ("mermaid.ink", render_with_mermaid_ink),
    ("kroki.io", render_with_kroki),
)


def render_png(text, path):
    """Сохраняет граф в PNG первым сработавшим способом.

    Возвращает название способа. Если ни один не сработал, выбрасывает
    RenderError со списком причин.
    """
    problems = []
    for name, renderer in RENDERERS:
        try:
            renderer(text, path)
            return name
        except RenderError as error:
            problems.append(f"{name}: {error}")
    raise RenderError("could not create PNG image:\n  "
                      + "\n  ".join(problems))