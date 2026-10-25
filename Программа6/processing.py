"""Лабораторная 6, вариант 8. Преобразования координат вручную."""
from math import cos, sin, radians, isfinite, floor
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw


def load_image(path):
    with Image.open(path) as image:
        if image.width * image.height > 4_000_000:
            raise ValueError("Допустимо не более 4 миллионов пикселей.")
        rgba = ImageOps.exif_transpose(image).convert("RGBA")
        result = Image.new("RGB", rgba.size, "white")
        result.paste(rgba, (0, 0), rgba.getchannel("A"))
        return result


def matrix(angle, axis="vertical"):
    """A = M R: поворот по часовой стрелке, затем отражение."""
    if not isfinite(angle):
        raise ValueError("Угол должен быть конечным числом.")
    if axis not in ("vertical", "horizontal"):
        raise ValueError("Неизвестная ось отражения.")
    c, s = cos(radians(angle % 360)), sin(radians(angle % 360))
    mx, my = (-1, 1) if axis == "vertical" else (1, -1)
    return mx*c, -mx*s, my*s, my*c


def inverse(a, b, d, e):
    determinant = a*e - b*d
    if abs(determinant) < 1e-12:
        raise ValueError("Преобразование необратимо.")
    return e/determinant, -b/determinant, -d/determinant, a/determinant


def resample(image, sampling):
    """sampling переводит координаты результата в координаты источника."""
    source = image.convert("RGB")
    w, h = source.size
    result = Image.new("RGB", (w, h), "white")
    pixels, output = source.load(), result.load()
    for j in range(h):
        for i in range(w):
            x, y = sampling(i, j)
            x, y = floor(x + 0.5), floor(y + 0.5)
            if 0 <= x < w and 0 <= y < h:
                output[i, j] = pixels[x, y]
    return result


def affine(image, angle, axis="vertical", restore=False):
    """restore=True применяет A^-1 к уже преобразованному растру."""
    a, b, d, e = matrix(angle, axis)
    # Для прямого результата выбираем источник через A^-1.
    # Для восстановления через A^-1 источником служит A.
    if not restore:
        a, b, d, e = inverse(a, b, d, e)
    cx, cy = (image.width-1)/2, (image.height-1)/2

    def sampling(i, j):
        u, v = i-cx, j-cy
        return a*u+b*v+cx, d*u+e*v+cy

    return resample(image, sampling)


def nonlinear(image, normalized=False):
    """i = x^(5/3); обратная выборка x = i^(3/5), y = j."""
    width = image.width
    scale = width-1 if normalized and width > 1 else 1
    columns = [scale * (i/scale)**(3/5) for i in range(width)]
    return resample(image, lambda i, j: (columns[i], j))


def save_image(image, path):
    if Path(path).suffix.lower() not in (".png", ".bmp"):
        raise ValueError("Используйте расширение PNG или BMP.")
    image.save(path)


def demo_image():
    """Несимметричная тестовая мишень, чтобы видеть поворот и отражение."""
    image = Image.new("RGB", (480, 320), "#f3f5f8")
    draw = ImageDraw.Draw(image)
    for x in range(0, 480, 20):
        draw.line((x, 0, x, 319), fill="#d6dee8")
    for y in range(0, 320, 20):
        draw.line((0, y, 479, y), fill="#d6dee8")
    draw.rectangle((0, 0, 479, 319), outline="#263445", width=3)
    draw.rectangle((30, 38, 185, 115), fill="#2879be")
    draw.ellipse((285, 40, 410, 165), fill="#ebad39")
    draw.polygon([(65, 155), (210, 155), (210, 125),
                  (265, 190), (210, 250), (210, 222),
                  (65, 222)], fill="#d4514b")
    draw.rectangle((330, 215, 425, 285), fill="#389b75")
    draw.text((45, 64), "TOP LEFT", fill="white", font_size=22)
    draw.text((18, 285), "LAB 6 / VARIANT 8", fill="#263445", font_size=18)
    return image
