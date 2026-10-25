"""Лабораторная 5, вариант 8: баланс белого по блику и осветление."""
from pathlib import Path
from PIL import Image, ImageOps


def load_image(path):
    """Чтение RGB; прозрачность накладывается на белый фон."""
    with Image.open(path) as source:
        if source.width * source.height > 16_000_000:
            raise ValueError("Допустимо не более 16 миллионов пикселей.")
        rgba = ImageOps.exif_transpose(source).convert("RGBA")
        result = Image.new("RGB", rgba.size, "white")
        result.paste(rgba, (0, 0), rgba.getchannel("A"))
        return result


def brightest_pixel(image):
    """Y = 0.2125R + 0.7154G + 0.0721B; при равенстве — первый пиксель."""
    rgb = image.convert("RGB")
    best, location = -1, (0, 0)
    for index, (r, g, b) in enumerate(rgb.getdata()):
        brightness = 2125 * r + 7154 * g + 721 * b
        if brightness > best:
            best, location = brightness, (index % rgb.width, index // rgb.width)
    return location


def white_balance(image, point=None):
    """C' = round(C * min(Rh,Gh,Bh) / Ch), как в методичке."""
    rgb = image.convert("RGB")
    x, y = brightest_pixel(rgb) if point is None else point
    if not (isinstance(x, int) and isinstance(y, int)
            and 0 <= x < rgb.width and 0 <= y < rgb.height):
        raise ValueError("Координаты блика выходят за границы изображения.")
    reference = rgb.getpixel((x, y))
    minimum = min(reference)
    if minimum == 0:
        if rgb.getbbox() is None:
            return rgb.copy(), (x, y), reference, (1.0, 1.0, 1.0)
        raise ValueError("В выбранном блике есть нулевой канал. Выберите светлый нейтральный участок щелчком по первому изображению.")
    factors = tuple(minimum / channel for channel in reference)
    result = Image.new("RGB", rgb.size)
    # Целочисленное округление половины вверх без ошибок float.
    target = result.load()
    for index, pixel in enumerate(rgb.getdata()):
        target[index % rgb.width, index // rgb.width] = tuple(
            (2 * c * minimum + ref) // (2 * ref)
            for c, ref in zip(pixel, reference))
    return result, (x, y), reference, factors


def lighten(first, second):
    """Покомпонентный максимум RGB: результат не темнее обоих входов."""
    if first.size != second.size:
        raise ValueError("Размеры изображений различаются. Приведите второе к размеру первого отдельной кнопкой.")
    a, b = first.convert("RGB"), second.convert("RGB")
    result = Image.new("RGB", a.size)
    target = result.load()
    for index, (p, q) in enumerate(zip(a.getdata(), b.getdata())):
        target[index % a.width, index // a.width] = tuple(
            max(x, y) for x, y in zip(p, q))
    return result


def save_image(image, path):
    if Path(path).suffix.lower() not in (".png", ".bmp"):
        raise ValueError("Выберите расширение PNG или BMP для сохранения без потерь.")
    image.save(path)
