"""Запуск: python main.py. Требуется Pillow; интерфейс написан на tkinter."""
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    for variable, folder in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
        library = Path(sys.base_prefix) / "tcl" / folder
        if library.is_dir() and variable not in os.environ:
            try:
                os.environ[variable] = os.path.relpath(library)
            except ValueError:
                pass

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from math import isfinite
from PIL import Image, ImageOps, ImageTk, UnidentifiedImageError

from rasterization import NAMES, reuleaux, render_all, composite, compare_masks


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная № 4 · Вариант 8 · Треугольник Рёло")
        self.geometry("1160x820")
        self.minsize(1000, 780)
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=7)
        style.configure("Title.TLabel", font=("Segoe UI", 17, "bold"))
        self.option_add("*Font", "{Segoe UI} 10")
        self.background = Image.new("RGB", (640, 480), "white")
        self.masks = []
        self.images = []
        self.points = []
        self.vars = {}
        self.zoom = tk.StringVar(value="1")
        self.first = tk.StringVar(value=NAMES[0])
        self.second = tk.StringVar(value=NAMES[2])
        self.info = tk.StringVar()
        self.status = tk.StringVar()
        self._build_ui()
        self.build()

    def _build_ui(self):
        outer = ttk.Frame(self, padding=16)
        outer.pack(fill="both", expand=True)
        ttk.Label(outer, text="Треугольник Рёло", style="Title.TLabel").pack(anchor="w")
        ttk.Label(outer, text="Лабораторная работа № 4  /  Вариант 8").pack(anchor="w", pady=(2, 12))
        body = ttk.Frame(outer)
        body.pack(fill="both", expand=True)
        left = ttk.Frame(body, width=270)
        left.pack(side="left", fill="y", padx=(0, 16))
        params = ttk.LabelFrame(left, text="Исходные данные", padding=12)
        params.pack(fill="x")
        ttk.Label(params, text="Три дуги окружностей радиуса R.\nНачало координат — слева сверху.\nX растёт вправо, Y — вниз.", justify="left").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        fields = (("r", "Ширина / радиус дуг", 260),
                  ("cx", "Центр фигуры X", 320), ("cy", "Центр фигуры Y", 235),
                  ("angle", "Поворот, градусы", 0),
                  ("w", "Ширина холста", 640), ("h", "Высота холста", 480))
        for row, (key, label, value) in enumerate(fields, 1):
            ttk.Label(params, text=label).grid(row=row, column=0, columnspan=2, sticky="w", pady=5)
            self.vars[key] = tk.StringVar(value=str(value))
            ttk.Entry(params, textvariable=self.vars[key], width=9).grid(row=row, column=2, padx=3)
        ttk.Button(left, text="Построить / обновить", command=self.build).pack(fill="x", pady=(12, 6))
        ttk.Button(left, text="Открыть изображение…", command=self.open_image).pack(fill="x", pady=3)
        ttk.Button(left, text="Белый фон", command=self.white_background).pack(fill="x", pady=3)
        ttk.Button(left, text="Сохранить текущую вкладку…", command=self.save_image).pack(fill="x", pady=3)
        ttk.Label(left, textvariable=self.info, wraplength=270, justify="left").pack(fill="x", pady=(14, 6))
        ttk.Label(left, text="Ширина фигуры = радиус каждой дуги.\nЦентры дуг — вершины равностороннего треугольника; угол дуги — 60°.\n\nЦентры округляются до пикселей одинаково для всех методов.", wraplength=270, foreground="#586579").pack(anchor="w", pady=8)
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True)
        bar = ttk.Frame(right)
        bar.pack(fill="x", pady=(0, 8))
        ttk.Label(bar, text="Масштаб:").pack(side="left")
        zoom_box = ttk.Combobox(bar, textvariable=self.zoom, values=("1", "2", "4", "8", "16"), state="readonly", width=4)
        zoom_box.pack(side="left", padx=8)
        zoom_box.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        ttk.Label(bar, text="×   •   Перетаскивайте изображение мышью").pack(side="left")
        self.notebook = ttk.Notebook(right)
        self.notebook.pack(fill="x")
        for name in ("По уравнению", "Параметрический", "Брезенхем", "Встроенный", "Различия"):
            self.notebook.add(ttk.Frame(self.notebook, height=1), text=name)
        self.notebook.bind("<<NotebookTabChanged>>", lambda _: self.refresh())
        self.comparison_bar = ttk.Frame(right)
        self.comparison_bar.pack(fill="x", pady=6)
        for var, color in ((self.first, "#dc2d37"), (self.second, "#0068e1")):
            ttk.Label(self.comparison_bar, text="■", foreground=color).pack(side="left", padx=(0, 3))
            combo = ttk.Combobox(self.comparison_bar, textvariable=var, values=NAMES, state="readonly", width=26)
            combo.pack(side="left", padx=(0, 8))
            combo.bind("<<ComboboxSelected>>", lambda _: self.refresh())
        frame = ttk.Frame(right)
        frame.pack(fill="both", expand=True)
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(frame, background="#e5e9f0", highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
        vertical = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        horizontal.grid(row=1, column=0, sticky="ew")
        vertical.grid(row=0, column=1, sticky="ns")
        self.canvas.configure(xscrollcommand=horizontal.set, yscrollcommand=vertical.set)
        self.canvas.bind("<ButtonPress-1>", lambda e: self.canvas.scan_mark(e.x, e.y))
        self.canvas.bind("<B1-Motion>", lambda e: self.canvas.scan_dragto(e.x, e.y, gain=1))
        self.canvas.bind("<Configure>", lambda _: self.draw_view())
        # Рендерим только видимую область: даже 2048 × 2048 при 16× не расходует гигабайты.
        self.canvas.configure(xscrollcommand=lambda *args: self._scroll_changed(horizontal, args),
                              yscrollcommand=lambda *args: self._scroll_changed(vertical, args))
        ttk.Label(right, textvariable=self.status, wraplength=760, justify="left").pack(fill="x", pady=(8, 0))
        self.bind("<Return>", lambda _: self.build())

    def _scroll_changed(self, scrollbar, args):
        scrollbar.set(*args)
        self.draw_view()

    def number(self, key):
        try:
            value = float(self.vars[key].get().replace(",", "."))
            if not isfinite(value):
                raise ValueError
            return value
        except ValueError:
            raise ValueError(f"Поле {key}: введите число.") from None

    def build(self):
        try:
            w, h = self.number("w"), self.number("h")
            if not w.is_integer() or not h.is_integer():
                raise ValueError("Ширина и высота должны быть целыми числами.")
            size = (int(w), int(h))
            vertices, arcs = reuleaux(self.number("cx"), self.number("cy"),
                                      self.number("r"), self.number("angle"))
            masks = render_all(arcs, size)
            points = [arc.center for arc in arcs]
            if self.background.size != size:
                # Смена размера не масштабирует загруженный фон: обрезка или белые поля.
                bg = Image.new("RGB", size, "white")
                bg.paste(self.background, (0, 0))
            else:
                bg = self.background
        except (ValueError, OverflowError) as error:
            messagebox.showerror("Проверьте исходные данные", str(error), parent=self)
            return False
        self.background, self.points, self.masks = bg, points, masks
        self.images = [composite(bg, mask) for mask in masks]
        self.info.set("Центры дуг (пиксели):\n" + "\n".join(
            f"{name} = ({p[0]}; {p[1]})" for name, p in zip("ABC", points))
            + f"\nR = {arcs[0].radius} пикс.\nКонтур: 3 дуги по 60° до округления")
        self.refresh()
        return True

    def current_image(self):
        index = self.notebook.index("current")
        if index < 4:
            return self.images[index]
        return compare_masks(self.masks[NAMES.index(self.first.get())], self.masks[NAMES.index(self.second.get())])[0]

    def refresh(self):
        if not self.images:
            return
        self.display_image = self.current_image()
        zoom = int(self.zoom.get())
        w, h = self.display_image.size
        self.canvas.configure(scrollregion=(0, 0, w * zoom, h * zoom))
        if self.notebook.index("current") == 4:
            _, n1, n2 = compare_masks(self.masks[NAMES.index(self.first.get())], self.masks[NAMES.index(self.second.get())])
            conclusion = "Результаты совпадают." if n1 + n2 == 0 else f"Различаются {n1 + n2} пикселей."
            self.status.set(f"{conclusion} Красные: {n1} — только первый метод; синие: {n2} — только второй. Серые — общие пиксели. Сравнение контуров не зависит от фона.")
        else:
            index = self.notebook.index("current")
            self.status.set(f"{NAMES[index]}  •  {w} × {h}  •  Пикселей контура: {self.masks[index].histogram()[255]}\nВкладка «Различия» сравнивает любую пару методов. Подписи вершин в файл не записываются.")
        self.draw_view()

    def draw_view(self):
        if not hasattr(self, "display_image"):
            return
        zoom = int(self.zoom.get())
        left = max(0, int(self.canvas.canvasx(0)) // zoom)
        top = max(0, int(self.canvas.canvasy(0)) // zoom)
        right = min(self.display_image.width, left + self.canvas.winfo_width() // zoom + 2)
        bottom = min(self.display_image.height, top + self.canvas.winfo_height() // zoom + 2)
        self.canvas.delete("all")
        if right > left and bottom > top:
            tile = self.display_image.crop((left, top, right, bottom))
            tile = tile.resize((tile.width * zoom, tile.height * zoom), Image.Resampling.NEAREST)
            self.photo = ImageTk.PhotoImage(tile, master=self)
            self.canvas.create_image(left * zoom, top * zoom, image=self.photo, anchor="nw")
        if self.notebook.index("current") < 4:
            for name, (x, y) in zip("ABC", self.points):
                self.canvas.create_text((x + .5) * zoom + 7, (y + .5) * zoom - 9, text=name, anchor="sw", fill="#315276", font=("Segoe UI", 10, "bold"))

    def open_image(self):
        path = filedialog.askopenfilename(parent=self, title="Открыть фон", filetypes=[("Изображения", "*.png *.bmp *.jpg *.jpeg *.tif *.tiff"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            with Image.open(path) as source:
                if not all(32 <= side <= 2048 for side in source.size):
                    raise ValueError("Размер фона должен быть от 32 до 2048 пикселей по каждой оси.")
                rgba = ImageOps.exif_transpose(source).convert("RGBA")
                image = Image.new("RGB", rgba.size, "white")
                image.paste(rgba, (0, 0), rgba.getchannel("A"))
        except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as error:
            messagebox.showerror("Не удалось открыть изображение", str(error), parent=self)
            return
        old_bg = self.background
        old_w, old_h = self.vars["w"].get(), self.vars["h"].get()
        self.background = image
        self.vars["w"].set(str(image.width))
        self.vars["h"].set(str(image.height))
        if not self.build():
            self.background = old_bg
            self.vars["w"].set(old_w)
            self.vars["h"].set(old_h)

    def white_background(self):
        if self.build():
            self.background = Image.new("RGB", self.background.size, "white")
            self.images = [composite(self.background, mask) for mask in self.masks]
            self.refresh()

    def save_image(self):
        # Сохраняется именно отображаемый результат последнего построения.
        path = filedialog.asksaveasfilename(parent=self, title="Сохранить текущую вкладку", defaultextension=".png", filetypes=[("PNG без потерь", "*.png"), ("BMP", "*.bmp")])
        if path:
            try:
                self.current_image().save(path)
            except (OSError, ValueError) as error:
                messagebox.showerror("Не удалось сохранить", str(error), parent=self)


if __name__ == "__main__":
    Application().mainloop()
