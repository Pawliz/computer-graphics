"""Лабораторная № 3, вариант 8. Геометрия и алгоритмы растеризации."""
from math import floor, hypot, isfinite

from PIL import Image, ImageDraw

NAMES = ("ЦДА", "Брезенхем (вещественный)", "Брезенхем (целочисленный)", "Pillow: ImageDraw.line")


def pixel_round(value):
    """Округление к ближайшему пикселю; половины округляются вверх."""
    return floor(value + 0.5)


def trapezoid(a, b, c, middle):
    """A, B, C идут по контуру; AB || CD, |CD| = 2m - |AB|."""
    if not all(isfinite(v) for p in (a, b, c) for v in p) or not isfinite(middle):
        raise ValueError("Координаты и средняя линия должны быть конечными числами.")
    ux, uy = b[0] - a[0], b[1] - a[1]
    length = hypot(ux, uy)
    if length < 1e-9:
        raise ValueError("A и B должны быть разными точками.")
    other = 2 * middle - length
    if other <= 1e-9:
        raise ValueError("Средняя линия должна быть больше половины длины AB.")
    height = abs(ux * (c[1] - a[1]) - uy * (c[0] - a[0])) / length
    if height < 1e-9:
        raise ValueError("Точки A, B, C не должны лежать на одной прямой.")
    d = (c[0] - other * ux / length, c[1] - other * uy / length)
    return (a, b, c, d)


def dda(a, b):
    """Цифровой дифференциальный анализатор, все октанты."""
    x, y = a
    dx, dy = b[0] - x, b[1] - y
    steps = max(abs(dx), abs(dy))
    if steps == 0:
        return [a]
    sx, sy = dx / steps, dy / steps
    points = []
    for _ in range(steps + 1):
        points.append((pixel_round(x), pixel_round(y)))
        x += sx
        y += sy
    # Конечная точка задаётся точно, независимо от накопленной погрешности.
    points[-1] = b
    return points


def bresenham_float(a, b):
    """Брезенхем с вещественной ошибкой f = minor / major - 0.5."""
    x, y = a
    dx, dy = abs(b[0] - x), abs(b[1] - y)
    sx, sy = (1 if b[0] > x else -1), (1 if b[1] > y else -1)
    steep = dy > dx
    if steep:
        dx, dy = dy, dx
    if dx == 0:
        return [a]
    slope = dy / dx
    error = slope - 0.5
    points = []
    for _ in range(dx + 1):
        points.append((x, y))
        if error >= 0:
            if steep:
                x += sx
            else:
                y += sy
            error -= 1.0
        if steep:
            y += sy
        else:
            x += sx
        error += slope
    return points


def bresenham_int(a, b):
    """Брезенхем с целочисленной ошибкой f = 2 * minor - major."""
    x, y = a
    dx, dy = abs(b[0] - x), abs(b[1] - y)
    sx, sy = (1 if b[0] > x else -1), (1 if b[1] > y else -1)
    steep = dy > dx
    if steep:
        dx, dy = dy, dx
    points = []
    error = 2 * dy - dx
    for _ in range(dx + 1):
        points.append((x, y))
        if error >= 0:
            if steep:
                x += sx
            else:
                y += sy
            error -= 2 * dx
        if steep:
            y += sy
        else:
            x += sx
        error += 2 * dy
    return points


def render_all(vertices, size):
    """Одинаковые округлённые вершины и толщина 1 пиксель для всех методов."""
    width, height = size
    if not 32 <= width <= 2048 or not 32 <= height <= 2048:
        raise ValueError("Размер изображения: от 32 до 2048 пикселей по каждой оси.")
    if any(not (0 <= x <= width - 1 and 0 <= y <= height - 1) for x, y in vertices):
        raise ValueError("Все четыре вершины должны находиться внутри изображения.")
    points = tuple((pixel_round(x), pixel_round(y)) for x, y in vertices)
    if len(set(points)) != 4:
        raise ValueError("После округления вершины совпадают. Увеличьте фигуру.")
    turns = []
    for i in range(4):
        a, b, c = points[i], points[(i + 1) % 4], points[(i + 2) % 4]
        turns.append((b[0] - a[0]) * (c[1] - b[1]) - (b[1] - a[1]) * (c[0] - b[0]))
    if not (all(t > 0 for t in turns) or all(t < 0 for t in turns)):
        raise ValueError("Трапеция вырождается на пиксельной сетке. Увеличьте фигуру.")
    edges = list(zip(points, points[1:] + points[:1]))
    masks = []
    for algorithm in (dda, bresenham_float, bresenham_int):
        mask = Image.new("L", size, 0)
        pixels = mask.load()
        for a, b in edges:
            for x, y in algorithm(a, b):
                pixels[x, y] = 255
        masks.append(mask)
    mask = Image.new("L", size, 0)
    painter = ImageDraw.Draw(mask)
    for a, b in edges:
        painter.line((a, b), fill=255, width=1)
    masks.append(mask)
    return points, masks


def composite(background, mask):
    result = background.copy().convert("RGB")
    result.paste((26, 55, 91), (0, 0), mask)
    return result


def compare_masks(first, second):
    """Серый = общие; красный = только первый; синий = только второй."""
    from PIL import ImageChops
    common = ImageChops.darker(first, second)
    only_first = ImageChops.subtract(first, second)
    only_second = ImageChops.subtract(second, first)
    image = Image.new("RGB", first.size, "white")
    for mask, color in ((common, (175, 181, 190)), (only_first, (220, 45, 55)),
                        (only_second, (0, 104, 225))):
        image.paste(color, (0, 0), mask)
    count_first = only_first.histogram()[255]
    count_second = only_second.histogram()[255]
    return image, count_first, count_second
