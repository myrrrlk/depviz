"""Порядок загрузки зависимостей (топологическая сортировка).

Пакет можно загрузить только после всех его зависимостей. Такой порядок
получается обходом графа в глубину: пакет добавляется в порядок, когда
все его зависимости уже обойдены (обратный порядок, post-order).
Обход сделан на стеке, без рекурсии.
"""


def load_order(graph):
    """Возвращает список пакетов в порядке загрузки.

    Если в графе есть цикл, строгого порядка не существует: ребро,
    которое замыкает цикл, пропускается, и пакеты цикла идут в порядке
    завершения обхода.
    """
    order = []
    visited = {graph.root}
    stack = [(graph.root, iter(graph.edges.get(graph.root, [])))]

    while stack:
        name, remaining = stack[-1]
        child = next(remaining, None)
        if child is None:
            order.append(name)
            stack.pop()
        elif child not in visited:
            visited.add(child)
            stack.append((child, iter(graph.edges.get(child, []))))
    return order