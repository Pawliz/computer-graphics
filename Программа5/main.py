"""Графическая программа для лабораторной 5, вариант 8."""
import os
import sys
from pathlib import Path

if sys.platform == "win32":
    for key, name in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
        folder = Path(sys.base_prefix) / "tcl" / name
        if folder.is_dir() and key not in os.environ:
            os.environ[key] = os.path.relpath(folder)

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
from processing import load_image, white_balance, lighten, save_image

ROOT = Path(__file__).resolve().parent


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная № 5 — Вариант 8")
        self.geometry("1180x860")
        self.minsize(1040, 760)
        self.images = [None] * 4
        self.photos = [None] * 4
        self.transforms = [None] * 4
        self.point = None
        self.status = tk.StringVar(value="Откройте два изображения или нажмите «Пример».")
        self.reference = tk.StringVar(value="Блик: автоматический поиск самой яркой точки.")
        self._build()

    def _build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", padding=6, font=("Segoe UI", 10))
        style.configure("TLabel", font=("Segoe UI", 10))
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text="Попиксельные преобразования",
                  font=("Segoe UI", 19, "bold")).pack(anchor="w")
        ttk.Label(header, text="Лабораторная № 5 / Вариант 8: баланс белого по блику и осветление").pack(anchor="w")
        controls = ttk.Frame(self, padding=(16, 0, 16, 8))
        controls.pack(fill="x")
        for label, action in (("Открыть первое…", lambda: self.open_file(0)),
                              ("Открыть второе…", lambda: self.open_file(1)),
                              ("Пример", self.demo), ("Сбросить", self.reset)):
            ttk.Button(controls, text=label, command=action).pack(side="left", padx=(0, 8))
        row = ttk.Frame(self, padding=(16, 0, 16, 8))
        row.pack(fill="x")
        for label, action in (("1. Баланс белого", self.balance),
                              ("2. Осветление", self.blend),
                              ("Блик автоматически", self.auto_point),
                              ("Размер второго = первому", self.resize_second)):
            ttk.Button(row, text=label, command=lambda f=action: self.safe(f)).pack(side="left", padx=(0, 8))
        ttk.Label(self, textvariable=self.reference, padding=(16, 0, 16, 3)).pack(anchor="w")
        ttk.Label(self, text="Для ручного выбора блика щёлкните по первому изображению. Осветление объединяет исправленное первое и второе.",
                  padding=(16, 0, 16, 8)).pack(anchor="w")
        grid = ttk.Frame(self, padding=(16, 0, 16, 0))
        grid.pack(fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1, uniform="column")
        grid.rowconfigure((0, 1), weight=1, uniform="row")
        self.canvases, self.titles = [], []
        labels = ("Первое изображение", "Второе изображение", "После баланса белого", "Осветление")
        for i, label in enumerate(labels):
            box = ttk.Frame(grid, padding=(0, 0, 8 if i % 2 == 0 else 0, 8))
            box.grid(row=i // 2, column=i % 2, sticky="nsew")
            bar = ttk.Frame(box)
            bar.pack(fill="x")
            title = ttk.Label(bar, text=label, font=("Segoe UI", 10, "bold"))
            title.pack(side="left")
            if i >= 2:
                ttk.Button(bar, text="Сохранить…", command=lambda n=i: self.save(n)).pack(side="right")
            canvas = tk.Canvas(box, bg="#e5eaf0", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            canvas.bind("<Configure>", lambda _, n=i: self.draw(n))
            self.canvases.append(canvas)
            self.titles.append(title)
        self.canvases[0].bind("<Button-1>", self.pick_point)
        ttk.Label(self, textvariable=self.status, wraplength=1100,
                  padding=(16, 6, 16, 12)).pack(fill="x")

    def safe(self, action):
        try:
            action()
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            messagebox.showerror("Проверьте данные", str(error), parent=self)

    def open_file(self, index):
        path = filedialog.askopenfilename(parent=self, title="Открыть изображение",
                                         filetypes=[("Изображения", "*.png *.bmp *.jpg *.jpeg *.tif *.tiff")])
        if path:
            self.safe(lambda: self.load(index, path))

    def load(self, index, path):
        self.images[index] = load_image(path)
        self.images[3] = None
        if index == 0:
            self.images[2], self.point = None, None
            self.reference.set("Блик: автоматический поиск самой яркой точки.")
        self.status.set(f"Загружено: {Path(path).name}. Размер: {self.images[index].size}.")
        self.refresh()

    def demo(self):
        self.safe(lambda: self.load(0, ROOT / "examples" / "source.png"))
        self.safe(lambda: self.load(1, ROOT / "examples" / "second.png"))

    def reset(self):
        self.images, self.point = [None] * 4, None
        self.reference.set("Блик: автоматический поиск самой яркой точки.")
        self.status.set("Откройте два изображения или нажмите «Пример».")
        self.refresh()

    def auto_point(self):
        self.point = None
        self.images[2:] = [None, None]
        self.reference.set("Блик: автоматический поиск самой яркой точки.")
        self.refresh()

    def pick_point(self, event):
        image, transform = self.images[0], self.transforms[0]
        if image is None or transform is None:
            return
        left, top, width, height = transform
        if not (left <= event.x < left + width and top <= event.y < top + height):
            return
        self.point = (int((event.x-left)*image.width/width),
                      int((event.y-top)*image.height/height))
        self.images[2:] = [None, None]
        self.reference.set(f"Выбран блик {self.point}, RGB = {image.getpixel(self.point)}.")
        self.refresh()

    def balance(self):
        if self.images[0] is None:
            raise ValueError("Сначала откройте первое изображение.")
        result, point, rgb, factors = white_balance(self.images[0], self.point)
        self.images[2], self.images[3] = result, None
        self.reference.set(f"Блик {point}; RGB = {rgb}; коэффициенты: "
                           + ", ".join(f"{v:.4f}" for v in factors))
        self.status.set(f"Баланс белого выполнен. Блик после обработки: {result.getpixel(point)}. Размер сохранён.")
        self.refresh()

    def blend(self):
        if self.images[2] is None or self.images[1] is None:
            raise ValueError("Сначала выполните баланс белого и откройте второе изображение.")
        self.images[3] = lighten(self.images[2], self.images[1])
        self.status.set("Осветление выполнено: каждый канал результата равен максимуму соответствующих каналов двух изображений.")
        self.refresh()

    def resize_second(self):
        if self.images[0] is None or self.images[1] is None:
            raise ValueError("Сначала откройте оба изображения.")
        self.images[1] = self.images[1].resize(self.images[0].size, Image.Resampling.LANCZOS)
        self.images[3] = None
        self.status.set("Второе изображение приведено к размеру первого. Пропорции могут измениться.")
        self.refresh()

    def save(self, index):
        if self.images[index] is None:
            messagebox.showinfo("Сохранение", "Сначала получите результат обработки.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self, defaultextension=".png",
                                          filetypes=[("PNG", "*.png"), ("BMP", "*.bmp")])
        if path:
            self.safe(lambda: save_image(self.images[index], path))

    def refresh(self):
        for i in range(4):
            self.draw(i)

    def draw(self, index):
        canvas, source = self.canvases[index], self.images[index]
        canvas.delete("all")
        if source is None:
            self.transforms[index] = None
            canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2,
                               text="Изображение не загружено" if index < 2 else "Результат ещё не получен",
                               fill="#62748b", font=("Segoe UI", 11))
            return
        preview = source.copy()
        preview.thumbnail((max(1, canvas.winfo_width()-12), max(1, canvas.winfo_height()-12)))
        left = (canvas.winfo_width()-preview.width)//2
        top = (canvas.winfo_height()-preview.height)//2
        self.transforms[index] = left, top, preview.width, preview.height
        self.photos[index] = ImageTk.PhotoImage(preview, master=self)
        canvas.create_image(left, top, anchor="nw", image=self.photos[index])
        if index == 0 and self.point is not None:
            x = left + (self.point[0]+0.5)*preview.width/source.width
            y = top + (self.point[1]+0.5)*preview.height/source.height
            canvas.create_oval(x-5, y-5, x+5, y+5, outline="#ef4444", width=2)


if __name__ == "__main__":
    Application().mainloop()
