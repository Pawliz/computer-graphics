"""Лабораторная № 2, вариант 8: операции над растровым изображением."""
from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps


@dataclass(frozen=True)
class Circle:
    x: int
    y: int
    radius: int


def font(size=18):
    """Системный шрифт нужен только для подписей, не для вычислений."""
    for name in ("C:/Windows/Fonts/arial.ttf", "DejaVuSans.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default(size=size)


def new_image(width: int, height: int) -> Image.Image:
    if not (400 <= width <= 4000 and 400 <= height <= 4000):
        raise ValueError("Ширина и высота результата должны быть от 400 до 4000 пикселей.")
    return Image.new("RGB", (width, height), "white")


def load_image(path) -> Image.Image:
    with Image.open(path) as image:
        image = ImageOps.exif_transpose(image)
        if image.width < 8 or image.height < 8:
            raise ValueError("Размер исходного изображения должен быть не меньше 8 × 8.")
        # Прозрачность накладываем на белый фон перед переводом в RGB.
        rgba = image.convert("RGBA")
        background = Image.new("RGBA", rgba.size, "white")
        return Image.alpha_composite(background, rgba).convert("RGB")


def default_circle(source: Image.Image) -> Circle:
    radius = max(1, min(source.size) // 8)
    return Circle(radius, source.height - 1 - radius, radius)


def validate_circle(source: Image.Image, circle: Circle):
    cx, cy, r = circle.x, circle.y, circle.radius
    if r < 1:
        raise ValueError("Радиус должен быть положительным целым числом.")
    if cx - r < 0 or cx + r >= source.width or cy - r < 0 or cy + r >= source.height:
        raise ValueError("Круг должен целиком находиться внутри исходного изображения.")
    if cx + r > (source.width - 1) / 2 or cy - r < (source.height - 1) / 2:
        raise ValueError("По варианту 8 круг должен находиться в нижней левой четверти.")


def copy_circle(source: Image.Image, target: Image.Image, circle: Circle) -> int:
    """Копирование именно по одному пикселю, без crop/paste и масок Pillow.

    Центр приёмника: ((W - 1) // 2, r). Верхний пиксель круга лежит
    на строке 0. На чётной ширине центр округляется влево на полпикселя.
    """
    validate_circle(source, circle)
    if source.mode != "RGB" or target.mode != "RGB":
        raise ValueError("Для копирования оба изображения должны иметь формат RGB.")
    r = circle.radius
    if 2 * r + 1 > target.width or 2 * r + 1 > target.height:
        raise ValueError("Круг не помещается в новом изображении.")
    dst_x, dst_y = (target.width - 1) // 2, r
    src_pixels, dst_pixels = source.load(), target.load()
    copied = 0
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                dst_pixels[dst_x + dx, dst_y + dy] = src_pixels[circle.x + dx, circle.y + dy]
                copied += 1
    return copied


def plot_box(image: Image.Image, radius: int):
    left, right = 65, image.width - 40
    top, bottom = 2 * radius + 80, image.height - 55
    if right - left < 200 or bottom - top < 140:
        raise ValueError("Под кругом недостаточно места для графика: увеличьте высоту или уменьшите радиус.")
    return left, top, right, bottom


def graph_point(x, y, box, x_limit=2.0):
    """Математические координаты → координаты растра (ось Y направлена вниз)."""
    left, top, right, bottom = box
    y_limit = x_limit ** 3
    px = (left + right) / 2 + x * (right - left) / (2 * x_limit)
    py = (top + bottom) / 2 - y * (bottom - top) / (2 * y_limit)
    return px, py


def draw_graph(image: Image.Image, radius: int, x_limit=2.0):
    if not 0.5 <= x_limit <= 5.0:
        raise ValueError("Граница аргумента должна быть от 0.5 до 5.")
    box = plot_box(image, radius)
    left, top, right, bottom = box
    draw = ImageDraw.Draw(image)
    f = font(16)
    draw.text((left, top - 38), "y = x³", font=font(25), fill="#184c9e")
    draw.text((right, top - 30), "График функции", font=f, anchor="ra", fill="#526174")
    ox, oy = graph_point(0, 0, box, x_limit)
    for i in range(-4, 5):
        x = x_limit * i / 4
        px, _ = graph_point(x, 0, box, x_limit)
        draw.line((px, top, px, bottom), fill="#e4e9ef")
        draw.line((px, oy - 4, px, oy + 4), fill="#334155")
        if i:
            draw.text((px, oy + 9), f"{x:g}", font=f, anchor="ma", fill="#334155")
        y = x_limit ** 3 * i / 4
        _, py = graph_point(0, y, box, x_limit)
        draw.line((left, py, right, py), fill="#e4e9ef")
        draw.line((ox - 4, py, ox + 4, py), fill="#334155")
        if i:
            draw.text((ox - 9, py), f"{y:g}", font=f, anchor="rm", fill="#334155")
    draw.line((left, oy, right + 14, oy), fill="#334155", width=2)
    draw.line((ox, bottom, ox, top - 14), fill="#334155", width=2)
    draw.polygon([(right + 14, oy), (right + 6, oy - 4), (right + 6, oy + 4)], fill="#334155")
    draw.polygon([(ox, top - 14), (ox - 4, top - 6), (ox + 4, top - 6)], fill="#334155")
    draw.text((right + 10, oy + 12), "x", fill="#334155", font=f)
    draw.text((ox + 12, top - 18), "y", fill="#334155", font=f)
    draw.text((ox - 8, oy + 9), "0", fill="#334155", font=f, anchor="ra")
    # Одна точка функции на каждый столбец области графика.
    points = []
    for px in range(left, right + 1):
        x = -x_limit + 2 * x_limit * (px - left) / (right - left)
        points.append(graph_point(x, x ** 3, box, x_limit))
    draw.line(points, fill="#2365c9", width=3)


def source_preview(source: Image.Image, circle: Circle) -> Image.Image:
    """Разметка рисуется на копии и не меняет исходные пиксели."""
    preview = source.copy()
    draw = ImageDraw.Draw(preview)
    w, h = source.size
    draw.line((w // 2, 0, w // 2, h - 1), fill="white", width=2)
    draw.line((0, h // 2, w - 1, h // 2), fill="white", width=2)
    x, y, r = circle.x, circle.y, circle.radius
    draw.ellipse((x - r, y - r, x + r, y + r), outline="#ff2960", width=3)
    return preview


def make_demo() -> Image.Image:
    """Искусственный исходный рисунок, воспроизводимый без внешних файлов."""
    image = Image.new("RGB", (800, 600))
    pixels = image.load()
    for y in range(600):
        for x in range(800):
            pixels[x, y] = (35 + x * 90 // 800, 90 + y * 90 // 600, 185 + x * 45 // 800)
    draw = ImageDraw.Draw(image)
    draw.ellipse((565, 45, 705, 185), fill="#ffe391")
    draw.polygon([(0, 390), (230, 155), (475, 420)], fill="#5d769c")
    draw.polygon([(235, 420), (535, 210), (800, 415)], fill="#45658c")
    draw.polygon([(177, 210), (230, 155), (291, 219), (252, 205), (229, 230)], fill="#e5effa")
    draw.rectangle((0, 420, 800, 600), fill="#369477")
    for x in range(0, 800, 35):
        draw.line((x, 590, x + 10, 448), fill="#65b789", width=2)
    for x, y, color in [(35, 490, "#ffd36b"), (90, 548, "#ff7894"), (125, 480, "#faf3c6"), (32, 570, "#d2b5ff")]:
        draw.line((x, y, x + 5, min(y + 50, 599)), fill="#184e40", width=3)
        for dx, dy in [(-10, 0), (10, 0), (0, -10), (0, 10)]:
            draw.ellipse((x + dx - 9, y + dy - 9, x + dx + 9, y + dy + 9), fill=color)
        draw.ellipse((x - 5, y - 5, x + 5, y + 5), fill="#935237")
    return image


def save_image(image: Image.Image, path):
    path = Path(path)
    if path.suffix.lower() not in (".png", ".bmp", ".jpg", ".jpeg"):
        raise ValueError("Используйте расширение PNG, BMP или JPG.")
    if path.suffix.lower() in (".jpg", ".jpeg"):
        image.save(path, quality=95, subsampling=0)
    else:
        image.save(path)


def generate_example(directory):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    make_demo().save(directory / "source.png")
    source = load_image(directory / "source.png")
    circle = default_circle(source)
    result = new_image(1000, 800)
    count = copy_circle(source, result, circle)
    draw_graph(result, circle.radius)
    source_preview(source, circle).save(directory / "source_selection.png")
    result.save(directory / "result.png")
    result.save(directory / "result.bmp")
    return count
