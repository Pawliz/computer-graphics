"""Графическая программа: python main.py."""
import os
import sys
from pathlib import Path

# Путь Tcl должен корректно обрабатываться и в папках с кириллицей.
if sys.platform == "win32":
    for key, name in (("TCL_LIBRARY", "tcl8.6"), ("TK_LIBRARY", "tk8.6")):
        folder = Path(sys.base_prefix) / "tcl" / name
        if folder.is_dir() and key not in os.environ:
            os.environ[key] = os.path.relpath(folder)

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
from processing import load_image, affine, nonlinear, save_image, demo_image


class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Лабораторная № 6 — Вариант 8")
        self.geometry("1060x760")
        self.minsize(940, 680)
        self.images = [None]*4
        self.photos = [None]*4
        self.used = None
        self.angle = tk.StringVar(value="30")
        self.axis = tk.StringVar(value="Вертикальная ось")
        self.normalized = tk.BooleanVar(value=False)
        self.status = tk.StringVar(value="Откройте изображение или нажмите «Пример».")
        self.build()
        self.angle.trace_add("write", self.invalidate_affine)
        self.axis.trace_add("write", self.invalidate_affine)
        self.normalized.trace_add("write", self.invalidate_nonlinear)

    def build(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 10), padding=5)
        style.configure("TLabel", font=("Segoe UI", 10))
        top = ttk.Frame(self, padding=12)
        top.pack(fill="x")
        ttk.Label(top, text="Геометрические преобразования",
                  font=("Segoe UI", 18, "bold")).pack(anchor="w")
        ttk.Label(top, text="Лабораторная № 6 • Вариант 8 • Поворот, отражение и i = x′^(5/3)").pack(anchor="w")
        row = ttk.Frame(top)
        row.pack(fill="x", pady=(8, 6))
        for text, action in (("Открыть…", self.open_file),
                             ("Пример", self.demo), ("Сбросить", self.reset)):
            ttk.Button(row, text=text, command=action).pack(side="left", padx=(0, 6))
        ttk.Label(row, text="Угол, °:").pack(side="left", padx=(12, 4))
        ttk.Entry(row, textvariable=self.angle, width=7).pack(side="left")
        ttk.Combobox(row, textvariable=self.axis, state="readonly", width=22,
                     values=("Вертикальная ось", "Горизонтальная ось")).pack(side="left", padx=8)
        ttk.Label(row, text="+ угол: по часовой стрелке").pack(side="left")
        row = ttk.Frame(top)
        row.pack(fill="x")
        for text, action in (("1. Поворот и отражение", self.transform),
                             ("2. Восстановить", self.restore),
                             ("3. Нелинейное", self.warp)):
            ttk.Button(row, text=text,
                       command=lambda f=action: self.safe(f)).pack(side="left", padx=(0, 6))
        ttk.Checkbutton(row, text="Нормировать x в [0, 1]",
                        variable=self.normalized).pack(side="left", padx=6)
        ttk.Label(top, text="Нелинейное: без флажка — координаты пикселей; с флажком — весь кадр. Размер холста сохраняется.").pack(anchor="w", pady=(6, 0))
        grid = ttk.Frame(self, padding=(12, 0))
        grid.pack(fill="both", expand=True)
        grid.columnconfigure((0, 1), weight=1, uniform="col")
        grid.rowconfigure((0, 1), weight=1, uniform="row")
        self.canvases = []
        names = ("Исходное изображение", "Поворот → отражение",
                 "Обратное аффинное", "Нелинейное преобразование")
        for i, name in enumerate(names):
            panel = ttk.Frame(grid, padding=(0, 0, 8 if i % 2 == 0 else 0, 8))
            panel.grid(row=i//2, column=i % 2, sticky="nsew")
            bar = ttk.Frame(panel)
            bar.pack(fill="x")
            ttk.Label(bar, text=name, font=("Segoe UI", 10, "bold")).pack(side="left")
            if i:
                ttk.Button(bar, text="Сохранить…",
                           command=lambda n=i: self.save(n)).pack(side="right")
            canvas = tk.Canvas(panel, width=320, height=160,
                               bg="#e5eaf0", highlightthickness=0)
            canvas.pack(fill="both", expand=True)
            canvas.bind("<Configure>", lambda _, n=i: self.draw(n))
            self.canvases.append(canvas)
        ttk.Label(self, textvariable=self.status, wraplength=1000,
                  padding=(12, 4, 12, 10)).pack(fill="x")

    def safe(self, action):
        try:
            action()
        except (ValueError, OSError, Image.DecompressionBombError) as error:
            messagebox.showerror("Проверьте данные", str(error), parent=self)

    def open_file(self):
        path = filedialog.askopenfilename(parent=self,
            filetypes=[("Изображения", "*.png *.bmp *.jpg *.jpeg *.tif *.tiff")])
        if path:
            self.safe(lambda: self.set_source(load_image(path)))

    def set_source(self, image):
        self.images = [image, None, None, None]
        self.used = None
        self.status.set(f"Загружено: {image.width} × {image.height} пикселей.")
        self.refresh()

    def demo(self):
        self.set_source(demo_image())

    def reset(self):
        self.images, self.used = [None]*4, None
        self.status.set("Откройте изображение или нажмите «Пример».")
        self.refresh()

    def invalidate_affine(self, *_):
        self.images[1:3], self.used = [None, None], None
        self.status.set("Параметры изменены. Выполните поворот и отражение заново.")
        self.refresh()

    def invalidate_nonlinear(self, *_):
        self.images[3] = None
        self.status.set("Режим изменён. Нажмите «3. Нелинейное».")
        self.refresh()

    def require_source(self):
        if self.images[0] is None:
            raise ValueError("Сначала загрузите исходное изображение.")

    def transform(self):
        self.require_source()
        try:
            angle = float(self.angle.get().replace(",", "."))
        except ValueError:
            raise ValueError("Введите угол числом, например 30 или -45,5.") from None
        axis = "vertical" if self.axis.get() == "Вертикальная ось" else "horizontal"
        result = affine(self.images[0], angle, axis)
        self.images[1:3], self.used = [result, None], (angle, axis)
        self.status.set(f"Поворот {angle:g}° и отражение выполнены. За пределами исходного кадра — белый фон.")
        self.refresh()

    def restore(self):
        if self.images[1] is None or self.used is None:
            raise ValueError("Сначала выполните поворот и отражение.")
        self.images[2] = affine(self.images[1], *self.used, restore=True)
        self.status.set("Обратное преобразование выполнено из результата. Обрезанные области и потери округления не восстанавливаются.")
        self.refresh()

    def warp(self):
        self.require_source()
        self.images[3] = nonlinear(self.images[0], self.normalized.get())
        mode = "нормированные координаты" if self.normalized.get() else "координаты пикселей"
        self.status.set(f"i = x′^(5/3), j = y′; выборка x′ = i^(3/5). Режим: {mode}.")
        self.refresh()

    def save(self, index):
        if self.images[index] is None:
            messagebox.showinfo("Сохранение", "Сначала получите результат.", parent=self)
            return
        path = filedialog.asksaveasfilename(parent=self,
            defaultextension=".png", filetypes=[("PNG", "*.png"), ("BMP", "*.bmp")])
        if path:
            self.safe(lambda: save_image(self.images[index], path))

    def refresh(self):
        for i in range(4):
            self.draw(i)

    def draw(self, index):
        canvas, image = self.canvases[index], self.images[index]
        canvas.delete("all")
        if image is None:
            canvas.create_text(canvas.winfo_width()/2, canvas.winfo_height()/2,
                text="Изображение не загружено" if index == 0 else "Результат ещё не получен",
                fill="#65758a", font=("Segoe UI", 11))
            return
        preview = image.copy()
        preview.thumbnail((max(1, canvas.winfo_width()-8),
                           max(1, canvas.winfo_height()-8)))
        self.photos[index] = ImageTk.PhotoImage(preview, master=self)
        canvas.create_image(canvas.winfo_width()/2, canvas.winfo_height()/2,
                            image=self.photos[index])


if __name__ == "__main__":
    Application().mainloop()
