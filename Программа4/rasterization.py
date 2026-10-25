"""Лабораторная №4, вариант 8: растеризация дуг треугольника Рёло."""
from dataclasses import dataclass
from math import atan2, ceil, cos, degrees, floor, isfinite, pi, radians, sin, sqrt, tau

from PIL import Image, ImageChops, ImageDraw

NAMES = ("Уравнение окружности", "Параметрическое уравнение", "Алгоритм Брезенхема", "Pillow: ImageDraw.arc")


def pixel_round(value):
    return floor(value + 0.5)


@dataclass(frozen=True)
class Arc:
    center: tuple
    radius: int
    start: float
    sweep: float
    first: tuple
    last: tuple


def reuleaux(cx, cy, width, rotation=0):
    """Радиус каждой дуги равен ширине; центры образуют равносторонний треугольник.

    Центр фигуры — центр исходного равностороннего треугольника.
    Возвращаются точные вершины и общие для всех методов растровые параметры.
    """
    if not all(isfinite(v) for v in (cx, cy, width, rotation)):
        raise ValueError("Все параметры должны быть конечными числами.")
    if not float(width).is_integer() or not 4 <= width <= 2000:
        raise ValueError("Ширина (радиус дуг) должна быть целым числом от 4 до 2000 пикселей.")
    if abs(cx) > 10000 or abs(cy) > 10000:
        raise ValueError("Координаты центра слишком велики.")
    radius = int(width)
    angle = radians(rotation % 360) - pi / 2
    vertices = tuple((cx + width / sqrt(3) * cos(angle + i * tau / 3),
                      cy + width / sqrt(3) * sin(angle + i * tau / 3)) for i in range(3))
    raster = tuple(tuple(pixel_round(v) for v in p) for p in vertices)
    arcs = []
    for i in range(3):
        center = raster[i]
        first, last = raster[(i + 1) % 3], raster[(i + 2) % 3]
        start = atan2(first[1] - center[1], first[0] - center[0]) % tau
        end = atan2(last[1] - center[1], last[0] - center[0]) % tau
        arcs.append(Arc(center, radius, start, (end - start) % tau, first, last))
    return vertices, tuple(arcs)


def symmetric_points(x, y):
    return {(x, y), (y, x), (-x, y), (-y, x), (x, -y), (y, -x), (-x, -y), (-y, -x)}


def circle_equation(radius):
    """x² + y² = R². Одна восьмая окружности и восемь отражений.

    Ограничение октантом предотвращает пропуски возле вертикальной касательной.
    """
    result = set()
    for x in range(pixel_round(radius / sqrt(2)) + 1):
        y = pixel_round(sqrt(radius * radius - x * x))
        result.update(symmetric_points(x, y))
    return result


def circle_bresenham(radius):
    """Целочисленный Брезенхем: горизонтальный, вертикальный или диагональный шаг."""
    x, y = 0, radius
    delta = 2 * (1 - radius)
    result = set()
    while x <= y:
        result.update(symmetric_points(x, y))
        d1 = 2 * (delta + y) - 1
        d2 = 2 * (delta - x) - 1
        if delta < 0 and d1 <= 0:
            x += 1
            delta += 2 * x + 1
        elif delta > 0 and d2 > 0:
            y -= 1
            delta += 1 - 2 * y
        else:
            x += 1
            y -= 1
            # +2 следует из delta = (x+1)² + (y-1)² - R².
            # В кратком псевдокоде методички этот член пропущен.
            delta += 2 * (x - y + 1)
    return result


def segment(a, b):
    """Короткое пиксельное соединение соседних отсчётов или концов дуг."""
    x, y = a
    dx, dy = abs(b[0] - x), -abs(b[1] - y)
    sx, sy = (1 if x < b[0] else -1), (1 if y < b[1] else -1)
    error = dx + dy
    points = {(x, y)}
    while (x, y) != b:
        doubled = 2 * error
        if doubled >= dy:
            error += dy
            x += sx
        if doubled <= dx:
            error += dx
            y += sy
        points.add((x, y))
    return points


def on_arc(angle, start, sweep):
    delta = (angle - start) % tau
    return delta <= sweep + 1e-10 or tau - delta < 1e-10


def cut_arc(circle, arc):
    cx, cy = arc.center
    return {(cx + x, cy + y) for x, y in circle
            if on_arc(atan2(y, x), arc.start, arc.sweep)}


def arc_parametric(arc):
    """x = cx + R cos(t), y = cy + R sin(t), шаг t не больше 1/R."""
    steps = max(1, ceil(arc.radius * arc.sweep))
    result = set()
    previous = None
    for i in range(steps + 1):
        angle = arc.start + arc.sweep * i / steps
        point = (arc.center[0] + pixel_round(arc.radius * cos(angle)),
                 arc.center[1] + pixel_round(arc.radius * sin(angle)))
        if previous is not None:
            result.update(segment(previous, point))
        result.add(point)
        previous = point
    return result


def join_endpoints(points, arc):
    """Привязываем концы к общим вершинам после округления геометрии.

    Коррекция одинакова у всех методов и ограничена двумя пикселями;
    внутренние пиксели дуги не заменяются результатом другого алгоритма.
    """
    result = set(points)
    if not points:
        raise ValueError("Для этой ширины не удалось получить дугу.")
    for endpoint in (arc.first, arc.last):
        closest = min(points, key=lambda p: ((p[0]-endpoint[0])**2 + (p[1]-endpoint[1])**2, p))
        if max(abs(closest[0]-endpoint[0]), abs(closest[1]-endpoint[1])) > 2:
            raise ValueError("Ошибка растеризации конца дуги.")
        result.update(segment(closest, endpoint))
    return result


def arc_builtin(arc):
    """Встроенная функция рисования дуги Pillow на локальном холсте."""
    r = arc.radius
    image = Image.new("L", (2*r + 3, 2*r + 3), 0)
    ImageDraw.Draw(image).arc((1, 1, 2*r + 1, 2*r + 1), degrees(arc.start),
                              degrees(arc.start + arc.sweep), fill=255, width=1)
    box = image.getbbox()
    if box is None:
        return set()
    pixels = image.load()
    return {(arc.center[0] + x - r - 1, arc.center[1] + y - r - 1)
            for y in range(box[1], box[3]) for x in range(box[0], box[2]) if pixels[x, y]}


def arc_bounds(arc):
    """Экстремумы дуги, включая выпуклую часть между вершинами."""
    angles = [arc.start, arc.start + arc.sweep]
    angles.extend(a for a in (0, pi/2, pi, 3*pi/2) if on_arc(a, arc.start, arc.sweep))
    return [(arc.center[0] + arc.radius*cos(a), arc.center[1] + arc.radius*sin(a)) for a in angles]


def render_all(arcs, size):
    w, h = size
    if not all(isinstance(v, int) and 32 <= v <= 2048 for v in size):
        raise ValueError("Размер холста: целые числа от 32 до 2048 пикселей.")
    for arc in arcs:
        if any(not (0 <= x <= w-1 and 0 <= y <= h-1) for x, y in arc_bounds(arc) + [arc.first, arc.last]):
            raise ValueError("Фигура выходит за границы холста. Измените центр, ширину или размер холста.")
    equation = circle_equation(arcs[0].radius)
    bresenham = circle_bresenham(arcs[0].radius)
    masks = []
    for method in range(4):
        mask = Image.new("L", size, 0)
        pixels = mask.load()
        for arc in arcs:
            if method == 0:
                points = cut_arc(equation, arc)
            elif method == 1:
                points = arc_parametric(arc)
            elif method == 2:
                points = cut_arc(bresenham, arc)
            else:
                points = arc_builtin(arc)
            for x, y in join_endpoints(points, arc):
                if not (0 <= x < w and 0 <= y < h):
                    raise ValueError("Растровый контур выходит за границы холста.")
                pixels[x, y] = 255
        masks.append(mask)
    return masks


def composite(background, mask):
    result = background.convert("RGB")
    result.paste((26, 55, 91), (0, 0), mask)
    return result


def compare_masks(first, second):
    common = ImageChops.darker(first, second)
    only_first = ImageChops.subtract(first, second)
    only_second = ImageChops.subtract(second, first)
    image = Image.new("RGB", first.size, "white")
    for mask, color in ((common, (175, 181, 190)), (only_first, (220, 45, 55)),
                        (only_second, (0, 104, 225))):
        image.paste(color, (0, 0), mask)
    return image, only_first.histogram()[255], only_second.histogram()[255]
