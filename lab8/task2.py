"""Лабораторная 8, часть 2. Программный Z-буфер (лекция 10, слайды 31–32)."""

import math
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "lab6"))
sys.path.insert(1, str(PROJECT_ROOT))

from lab6.main import POLYHEDRONS
from lab6 import task2
from lab6.projections import project_vertices
from lab7.task1 import load_obj


BACKGROUND = (245, 247, 250)
COLORS = ((60, 130, 215), (225, 115, 60), (65, 170, 110), (170, 95, 195))
# Фиксированный параллельный вид. Сохраняем Z после видового поворота:
# axonometric_matrix() из lab6 обнуляет Z и для Z-буфера не подходит.
# Наблюдатель со стороны отрицательной оси Z вида: меньше Z — ближе.
VIEW = task2.mat_mul(task2.rotation_y(-math.pi / 4),
                     task2.rotation_x(math.atan(1 / math.sqrt(2))))


class ZBuffer:
    """Общий буфер кадра и глубины для всех объектов сцены."""

    def __init__(self, width, height, enabled=True):
        self.width, self.height = width, height
        self.enabled = enabled
        # Шаги 1–2 лекции: фон и максимальная глубина (+бесконечность).
        self.pixels = bytearray(BACKGROUND) * (width * height)
        self.depth = [math.inf] * (width * height)

    def polygon(self, vertices, color):
        """Растеризация плоского простого многоугольника, без отсечения граней.

        Дополнение к лекции: пересекаем рёбра строкой y + 0.5 и заполняем
        интервалы между парами пересечений (правило чётности).
        Глубина из Ax + By + Cz + D = 0; dz/dx = -A/C.
        Формулы применяются к экранным X, Y и сохранённому видовому Z.
        """
        if len(vertices) < 3:
            return
        x0, y0, z0 = vertices[0]
        # Ищем невырожденную тройку, в том числе при коллинеарных первых точках.
        for i in range(1, len(vertices) - 1):
            ux, uy, uz = (vertices[i][j] - vertices[0][j] for j in range(3))
            vx, vy, vz = (vertices[i + 1][j] - vertices[0][j] for j in range(3))
            a, b, c = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            if abs(c) > 1e-12:
                break
        else:
            return  # Проекция грани выродилась в линию или точку.
        dzdx, dzdy = -a / c, -b / c
        first_y = max(0, math.ceil(min(p[1] for p in vertices) - 0.5))
        last_y = min(self.height - 1, math.ceil(max(p[1] for p in vertices) - 0.5) - 1)
        edges = list(zip(vertices, vertices[1:] + vertices[:1]))
        rgb = bytes(color)
        for y in range(first_y, last_y + 1):
            py = y + 0.5
            intersections = []
            for p, q in edges:
                # Полуоткрытые интервалы исключают двойной учёт вершин.
                if (p[1] <= py < q[1]) or (q[1] <= py < p[1]):
                    t = (py - p[1]) / (q[1] - p[1])
                    intersections.append(p[0] + t * (q[0] - p[0]))
            intersections.sort()
            for left, right in zip(intersections[::2], intersections[1::2]):
                first_x = max(0, math.ceil(left - 0.5))
                last_x = min(self.width - 1, math.ceil(right - 0.5) - 1)
                z = z0 + dzdx * (first_x + 0.5 - x0) + dzdy * (py - y0)
                offset = y * self.width + first_x
                for x in range(first_x, last_x + 1):
                    # Шаги 3–6 лекции. Порядок граней и объектов произвольный.
                    if not self.enabled or z < self.depth[offset]:
                        self.depth[offset] = z
                        self.pixels[3 * offset:3 * offset + 3] = rgb
                    z += dzdx
                    offset += 1

    def ppm(self, show_depth=False):
        pixels = self.pixels
        if show_depth:
            pixels = bytearray(BACKGROUND) * (self.width * self.height)
            finite = [z for z in self.depth if math.isfinite(z)]
            if finite:
                near, far = min(finite), max(finite)
                span = max(far - near, 1e-12)
                for i, z in enumerate(self.depth):
                    if math.isfinite(z):
                        value = round(240 - 200 * (z - near) / span)
                        pixels[3 * i:3 * i + 3] = bytes((value,) * 3)
        header = f"P6\n{self.width} {self.height}\n255\n".encode("ascii")
        return header + pixels


def render_scene(models, width, height, center=(0, 0), span=(8, 8),
                 enabled=True, reverse=False):
    """Параллельная проекция и единый Z-буфер; сортировки по глубине нет."""
    buffer = ZBuffer(width, height, enabled)
    scale = 0.85 * min(width / span[0], height / span[1])
    order = list(enumerate(models))
    if reverse:
        order.reverse()
    for model_index, model in order:
        points = project_vertices(model.vertices, VIEW)
        screen = [(width / 2 + (x - center[0]) * scale,
                   height / 2 - (y - center[1]) * scale, z)
                  for x, y, z, w in points]
        base = COLORS[model_index % len(COLORS)]
        faces = list(enumerate(model.faces))
        if reverse:
            faces.reverse()
        for face_index, face in faces:
            # Разные оттенки граней помогают видеть форму; освещение не нужно.
            factor = (0.70, 0.85, 1.0)[face_index % 3]
            color = tuple(round(channel * factor) for channel in base)
            buffer.polygon([screen[i] for i in face.indices], color)
    return buffer


def demo_scene():
    cube = POLYHEDRONS["Гексаэдр (Куб)"]
    blue = task2.scale_about_origin(cube(), 1.4, 0.55, 0.65)
    blue = task2.rotate_about_origin(blue, 10, 25, -15)
    blue = task2.translate(blue, -0.6, 0, 0)
    orange = task2.scale_about_origin(cube(), 0.65, 1.2, 0.6)
    orange = task2.rotate_about_origin(orange, 0, -20, 15)
    orange = task2.translate(orange, 0.7, 0.15, 0.2)
    green = task2.scale_about_origin(cube(), 0.8, 0.7, 0.8)
    green = task2.translate(green, 0, -0.65, 1.3)
    return [blue, orange, green]


class Application(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.models = []
        self.view_center, self.view_span = (0, 0), (8, 8)
        self.pending_draw = None
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        ttk.Label(controls, text="Объект для преобразований").pack(anchor="w")
        self.object_box = ttk.Combobox(controls, state="readonly", width=33)
        self.object_box.pack(fill="x", pady=(3, 8))
        self.figure = tk.StringVar(value="Гексаэдр (Куб)")
        ttk.Combobox(controls, textvariable=self.figure, values=list(POLYHEDRONS),
                     state="readonly").pack(fill="x")
        ttk.Button(controls, text="Добавить фигуру", command=self.add_figure).pack(fill="x", pady=3)
        ttk.Button(controls, text="Добавить OBJ...", command=self.load_model).pack(fill="x")
        ttk.Button(controls, text="Удалить выбранный", command=self.remove_model).pack(fill="x", pady=3)
        ttk.Button(controls, text="Сбросить демонстрацию", command=self.reset_scene).pack(fill="x")
        self.z_enabled = tk.BooleanVar(value=True)
        self.show_depth = tk.BooleanVar(value=False)
        self.reverse = tk.BooleanVar(value=False)
        for text, variable in (("Z-буфер", self.z_enabled),
                               ("Показать глубину (ближе — светлее)", self.show_depth),
                               ("Обратный порядок отрисовки", self.reverse)):
            ttk.Checkbutton(controls, text=text, variable=variable,
                            command=self.schedule_draw).pack(anchor="w", pady=(4, 0))
        self.transform_controls(controls, "Перенос", ("dx", "dy", "dz"),
                                (0, 0, 0), task2.translate)
        self.transform_controls(controls, "Поворот вокруг центра, X → Y → Z",
                                ("X, °", "Y, °", "Z, °"), (0, 15, 0), self.rotate_center)
        self.transform_controls(controls, "Масштаб относительно центра", ("kx", "ky", "kz"),
                                (1, 1, 1), task2.scale_about_center)
        ttk.Button(controls, text="Вписать всю сцену", command=self.fit_scene).pack(fill="x", pady=8)
        ttk.Label(controls, text="Фиксированный параллельный вид.\n"
                  "При включённом Z-буфере смена\nпорядка сохраняет видимость.\n"
                  "Цвета: синий, оранжевый, зелёный.", justify="left").pack(anchor="w")
        self.canvas = tk.Canvas(self, width=750, height=650, highlightthickness=0,
                                background="#f5f7fa")
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.status = ttk.Label(self)
        self.status.grid(row=1, column=0, columnspan=2, sticky="w", pady=(6, 0))
        self.canvas.bind("<Configure>", self.schedule_draw)
        self.reset_scene()

    def transform_controls(self, parent, title, labels, defaults, operation):
        box = ttk.LabelFrame(parent, text=title, padding=6)
        box.pack(fill="x", pady=(8, 0))
        row = ttk.Frame(box)
        row.pack(fill="x")
        variables = []
        for i, (label, default) in enumerate(zip(labels, defaults)):
            row.columnconfigure(i, weight=1)
            cell = ttk.Frame(row)
            cell.grid(row=0, column=i, sticky="ew", padx=3)
            ttk.Label(cell, text=label).pack(anchor="w")
            variable = tk.StringVar(value=str(default))
            ttk.Entry(cell, textvariable=variable, width=8).pack(fill="x")
            variables.append(variable)
        ttk.Button(box, text="Применить", command=lambda: self.apply_transform(
            operation, variables)).pack(fill="x", pady=(5, 0))

    @staticmethod
    def rotate_center(model, ax, ay, az):
        for axis, angle in zip("xyz", (ax, ay, az)):
            model = task2.rotate_about_center_axis(model, axis, angle)
        return model

    @staticmethod
    def validate_model(model):
        if not model.vertices or not model.faces:
            raise ValueError("В модели нет вершин или граней")
        if not all(math.isfinite(v) for p in model.vertices for v in (p.x, p.y, p.z)):
            raise ValueError("Координаты должны быть конечными числами")
        # Проверяем и видовые координаты, чтобы обнаружить переполнение до рисования.
        if not all(math.isfinite(v) for p in project_vertices(model.vertices, VIEW) for v in p):
            raise ValueError("Координаты вне числового диапазона")

    def apply_transform(self, operation, variables):
        index = self.object_box.current()
        if index < 0:
            return
        try:
            values = [float(v.get().replace(",", ".")) for v in variables]
            if not all(math.isfinite(v) for v in values):
                raise ValueError("Введите конечные числа")
            result = operation(self.models[index], *values)
            self.validate_model(result)
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            messagebox.showerror("Ошибка преобразования", str(error), parent=self)
            return
        self.models[index] = result
        # Не вписываем сцену автоматически: перенос и масштаб должны быть видны.
        self.schedule_draw()

    def update_list(self, selected=0):
        self.object_box["values"] = [f"{i + 1}. {m.name}" for i, m in enumerate(self.models)]
        if self.models:
            self.object_box.current(min(selected, len(self.models) - 1))
        else:
            self.object_box.set("")

    def reset_scene(self):
        self.models = demo_scene()
        self.update_list()
        self.fit_scene()

    def add_figure(self):
        self.models.append(POLYHEDRONS[self.figure.get()]())
        self.update_list(len(self.models) - 1)
        self.fit_scene()

    def load_model(self):
        filename = filedialog.askopenfilename(parent=self, initialdir=Path(__file__).parent,
                                              filetypes=[("Wavefront OBJ", "*.obj")])
        if not filename:
            return
        try:
            model = load_obj(filename)
            self.validate_model(model)
            model.name = Path(filename).stem
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка загрузки", str(error), parent=self)
            return
        self.models.append(model)
        self.update_list(len(self.models) - 1)
        self.fit_scene()

    def remove_model(self):
        index = self.object_box.current()
        if index >= 0:
            del self.models[index]
            self.update_list(index)
            self.schedule_draw()

    def fit_scene(self):
        points = [p for model in self.models for p in project_vertices(model.vertices, VIEW)]
        if points:
            xs, ys = [p[0] for p in points], [p[1] for p in points]
            self.view_center = (min(xs) / 2 + max(xs) / 2, min(ys) / 2 + max(ys) / 2)
            self.view_span = (max(max(xs) - min(xs), 1e-6), max(max(ys) - min(ys), 1e-6))
        self.schedule_draw()

    def schedule_draw(self, event=None):
        if self.pending_draw is not None:
            self.after_cancel(self.pending_draw)
        self.pending_draw = self.after(30, self.redraw)

    def redraw(self):
        self.pending_draw = None
        width, height = max(1, self.canvas.winfo_width()), max(1, self.canvas.winfo_height())
        buffer = render_scene(self.models, width, height, self.view_center, self.view_span,
                              self.z_enabled.get(), self.reverse.get())
        self.image = tk.PhotoImage(data=buffer.ppm(self.show_depth.get()), format="PPM")
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor="nw", image=self.image)
        mode = "Z-буфер включён" if self.z_enabled.get() else "Z-буфер выключен: запись поверх предыдущего"
        self.status["text"] = f"{mode} | Объектов: {len(self.models)} | {width} × {height}"


def main():
    window = tk.Tk()
    window.title("Лабораторная №8. Задание 2 — Z-буфер")
    window.geometry("1120x800")
    window.minsize(950, 760)
    Application(window)
    window.mainloop()


if __name__ == "__main__":
    main()
