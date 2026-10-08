"""Графическая форма на Tkinter. Обработка изображения вынесена в processing.py."""
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, UnidentifiedImageError

from processing import (Circle, copy_circle, default_circle, draw_graph, load_image,
                        new_image, plot_box, save_image, source_preview, validate_circle)

ROOT = Path(__file__).resolve().parent


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная работа № 2 • Вариант 8")
        self.geometry("1250x880")
        self.minsize(1040, 750)
        self.configure(bg="#f3f5f8")
        self.source = None
        self.result = None
        self.copied_circle = None
        self.preview_images = []
        self.values = {key: tk.StringVar(value=value) for key, value in {
            "width": "1000", "height": "800", "cx": "75", "cy": "524",
            "radius": "75", "x_limit": "2"}.items()}
        self.status = tk.StringVar(value="Откройте изображение или загрузите пример.")
        self._build()
        self.load_source(ROOT / "examples" / "source.png")
        self.create_result()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#f3f5f8")
        style.configure("TLabel", background="#f3f5f8", font=("Segoe UI", 10))
        style.configure("TButton", padding=(9, 7), font=("Segoe UI", 10))
        header = ttk.Frame(self, padding=(20, 15))
        header.pack(fill="x")
        ttk.Label(header, text="Формирование изображений", font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(header, text="Лабораторная № 2 / Вариант 8: круг снизу слева → верхний край по центру; y = x³").pack(anchor="w", pady=(5, 0))
        controls = ttk.Frame(self, padding=(20, 0, 20, 12))
        controls.pack(fill="x")
        row1 = ttk.Frame(controls)
        row1.pack(fill="x", pady=4)
        self._entry(row1, "Ширина", "width")
        self._entry(row1, "Высота", "height")
        ttk.Button(row1, text="1. Создать", command=lambda: self.safe(self.create_result)).pack(side="left", padx=8)
        ttk.Button(row1, text="2. Открыть изображение", command=self.open_source).pack(side="left", padx=4)
        ttk.Button(row1, text="Пример", command=lambda: self.safe(lambda: self.load_source(ROOT / "examples" / "source.png"))).pack(side="left", padx=4)
        row2 = ttk.Frame(controls)
        row2.pack(fill="x", pady=4)
        self._entry(row2, "Центр X", "cx")
        self._entry(row2, "Центр Y", "cy")
        self._entry(row2, "Радиус", "radius")
        ttk.Button(row2, text="3. Копировать круг", command=lambda: self.safe(self.copy_fragment)).pack(side="left", padx=8)
        ttk.Button(row2, text="Показать выделение", command=lambda: self.safe(self.show_selection)).pack(side="left", padx=4)
        row3 = ttk.Frame(controls)
        row3.pack(fill="x", pady=4)
        self._entry(row3, "x от −a до a; a =", "x_limit")
        ttk.Button(row3, text="4. Построить y = x³", command=lambda: self.safe(self.add_graph)).pack(side="left", padx=8)
        ttk.Button(row3, text="Выполнить всё", command=lambda: self.safe(self.run_all)).pack(side="left", padx=4)
        ttk.Button(row3, text="5. Сохранить результат", command=self.save_result).pack(side="left", padx=4)
        content = ttk.Frame(self, padding=(20, 0))
        content.pack(fill="both", expand=True)
        content.columnconfigure((0, 1), weight=1)
        content.rowconfigure(1, weight=1)
        self.source_title = ttk.Label(content, text="ИСХОДНОЕ ИЗОБРАЖЕНИЕ", font=("Segoe UI", 10, "bold"))
        self.source_title.grid(row=0, column=0, sticky="w", pady=8)
        self.result_title = ttk.Label(content, text="РЕЗУЛЬТАТ", font=("Segoe UI", 10, "bold"))
        self.result_title.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=8)
        self.source_canvas = tk.Canvas(content, bg="#e4e9ef", highlightthickness=0, width=490, height=400)
        self.result_canvas = tk.Canvas(content, bg="#e4e9ef", highlightthickness=0, width=490, height=400)
        self.source_canvas.grid(row=1, column=0, sticky="nsew")
        self.result_canvas.grid(row=1, column=1, sticky="nsew", padx=(12, 0))
        self.source_canvas.bind("<Configure>", lambda event: self.refresh())
        self.result_canvas.bind("<Configure>", lambda event: self.refresh())
        ttk.Label(self, textvariable=self.status, padding=(20, 12), wraplength=1180).pack(fill="x")
        ttk.Label(self, text="Координаты и радиус задаются в пикселях оригинала. Предпросмотр масштабируется; сохранение выполняется в полном размере.", padding=(20, 0, 20, 12), foreground="#526174").pack(fill="x")

    def _entry(self, parent, title, key):
        ttk.Label(parent, text=title).pack(side="left", padx=(0, 5))
        ttk.Entry(parent, textvariable=self.values[key], width=7).pack(side="left", padx=(0, 12))

    def safe(self, action):
        try:
            action()
        except (ValueError, OSError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            messagebox.showerror("Проверьте данные", str(error), parent=self)

    def integer(self, key):
        try:
            return int(self.values[key].get())
        except ValueError as error:
            raise ValueError("Размеры, координаты и радиус должны быть целыми числами.") from error

    def circle(self):
        return Circle(self.integer("cx"), self.integer("cy"), self.integer("radius"))

    def limit(self):
        try:
            limit = float(self.values["x_limit"].get().replace(",", "."))
        except ValueError as error:
            raise ValueError("Граница аргумента должна быть числом от 0.5 до 5.") from error
        if not 0.5 <= limit <= 5:
            raise ValueError("Граница аргумента должна быть от 0.5 до 5.")
        return limit

    def load_source(self, path):
        source = load_image(path)
        self.source = source
        circle = default_circle(source)
        for key, value in (("cx", circle.x), ("cy", circle.y), ("radius", circle.radius)):
            self.values[key].set(str(value))
        self.source_title.configure(text=f"ИСТОЧНИК · {source.width} × {source.height} · {Path(path).name}")
        self.status.set("Источник загружен. Круг выбран в нижнем левом углу; можно изменить его параметры.")
        self.refresh()

    def open_source(self):
        path = filedialog.askopenfilename(parent=self, title="Выберите исходное изображение", filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp *.gif *.tif *.tiff *.webp"), ("Все файлы", "*.*")])
        if path:
            self.safe(lambda: self.load_source(path))

    def create_result(self):
        self.result = new_image(self.integer("width"), self.integer("height"))
        self.copied_circle = None
        self.status.set("Создано новое белое RGB-изображение. Теперь скопируйте круг или нажмите «Выполнить всё».")
        self.refresh()

    def show_selection(self):
        if self.source is None:
            raise ValueError("Сначала откройте исходное изображение.")
        validate_circle(self.source, self.circle())
        self.refresh()
        self.status.set("Выделение показано красным контуром. Разметка не изменяет исходный файл.")

    def copy_fragment(self):
        if self.source is None or self.result is None:
            raise ValueError("Сначала откройте источник и создайте новое изображение.")
        circle = self.circle()
        # Пересборка исключает следы старого круга после изменения радиуса.
        result = new_image(*self.result.size)
        count = copy_circle(self.source, result, circle)
        self.result, self.copied_circle = result, circle
        self.status.set(f"Попиксельно скопировано {count} пикселей. Центр результата: ({(result.width - 1) // 2}, {circle.radius}).")
        self.refresh()

    def add_graph(self):
        if self.result is None or self.copied_circle is None:
            raise ValueError("Сначала скопируйте круг в новое изображение.")
        result = self.result.copy()
        radius = self.copied_circle.radius
        limit = self.limit()
        plot_box(result, radius)
        # Стираем только область ниже круга для повторного построения.
        from PIL import ImageDraw
        ImageDraw.Draw(result).rectangle((0, 2 * radius + 1, result.width, result.height), fill="white")
        draw_graph(result, radius, limit)
        self.result = result
        self.status.set(f"Готово: круг перенесён к верхнему краю; построены оси и y = x³, x ∈ [−{limit:g}; {limit:g}]. Сохраните результат.")
        self.refresh()

    def run_all(self):
        # Проверяем все параметры прежде, чем менять готовый результат.
        if self.source is None:
            raise ValueError("Сначала откройте изображение.")
        result = new_image(self.integer("width"), self.integer("height"))
        circle, limit = self.circle(), self.limit()
        plot_box(result, circle.radius)
        count = copy_circle(self.source, result, circle)
        draw_graph(result, circle.radius, limit)
        self.result, self.copied_circle = result, circle
        self.status.set(f"Готово: скопировано {count} пикселей, добавлены оси и график y = x³. Результат можно сохранить.")
        self.refresh()

    def save_result(self):
        if self.result is None:
            messagebox.showinfo("Сохранение", "Сначала создайте изображение.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, title="Сохранить результат", initialfile="result_variant8.png", defaultextension=".png", filetypes=[("PNG без потерь", "*.png"), ("BMP без потерь", "*.bmp"), ("JPEG с потерями", "*.jpg")])
        if path:
            def save():
                save_image(self.result, path)
                self.status.set(f"Сохранено: {path}")
            self.safe(save)

    def refresh(self):
        if not hasattr(self, "source_canvas"):
            return
        source = self.source
        if source is not None:
            try:
                source = source_preview(source, self.circle())
            except ValueError:
                pass
        self.preview_images = []
        for canvas, image in ((self.source_canvas, source), (self.result_canvas, self.result)):
            canvas.delete("all")
            if image is None:
                continue
            preview = image.copy()
            preview.thumbnail((max(1, canvas.winfo_width() - 20), max(1, canvas.winfo_height() - 20)), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(preview)
            self.preview_images.append(photo)
            canvas.create_image(canvas.winfo_width() // 2, canvas.winfo_height() // 2, image=photo)
        if self.result is not None:
            self.result_title.configure(text=f"РЕЗУЛЬТАТ · {self.result.width} × {self.result.height} · RGB")
