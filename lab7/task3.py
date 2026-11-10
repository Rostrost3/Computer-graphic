import math
import sys
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Модель и матричные преобразования из лабораторной №6.
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "lab6"))
sys.path.insert(1, str(project_root))

from lab6.main import Point3D, Polygon, Polyhedron
from lab6 import task2
from lab6.projections import axonometric_matrix, project_vertices
from lab7.task1 import load_obj, save_obj


FUNCTIONS = {
    "sin(x) * cos(y)": lambda x, y: math.sin(x) * math.cos(y),
    "x² + y²": lambda x, y: x * x + y * y,
    "x² - y²": lambda x, y: x * x - y * y,
}


def build_surface(function, x0, x1, y0, y1, nx, ny):
    """Сетка из (nx+1)*(ny+1) вершин и nx*ny четырёхугольных граней."""
    if not all(math.isfinite(v) for v in (x0, x1, y0, y1)):
        raise ValueError("Границы должны быть конечными числами")
    if x0 >= x1 or y0 >= y1:
        raise ValueError("Начало диапазона должно быть меньше конца")
    if any(type(n) is not int or n < 1 for n in (nx, ny)):
        raise ValueError("Число разбиений должно быть положительным целым")

    vertices = []
    for i in range(nx + 1):
        x = x0 * (1 - i / nx) + x1 * (i / nx)
        for j in range(ny + 1):
            y = y0 * (1 - j / ny) + y1 * (j / ny)
            z = function(x, y)
            if not math.isfinite(z):
                raise ValueError("Функция принимает неконечное значение")
            vertices.append(Point3D(x, y, z))

    faces = []
    stride = ny + 1
    for i in range(nx):
        for j in range(ny):
            a = i * stride + j
            faces.append(Polygon([a, a + stride, a + stride + 1, a + 1]))
    return Polyhedron(vertices, faces, name="Поверхность")


class Application(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self.polyhedron = None
        self.view_center = (0, 0)
        self.view_span = (1, 1)
        self.projection = axonometric_matrix()

        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))
        surface = ttk.LabelFrame(controls, text="z = f(x, y)", padding=8)
        surface.pack(fill="x")
        self.function_name = tk.StringVar(value=next(iter(FUNCTIONS)))
        ttk.Combobox(surface, textvariable=self.function_name,
                     values=list(FUNCTIONS), state="readonly").pack(fill="x")
        self.x_range = self.entries(surface, ("X от", "X до"), (-3, 3))
        self.y_range = self.entries(surface, ("Y от", "Y до"), (-3, 3))
        self.subdivisions = self.entries(surface, ("Разбиения X", "Разбиения Y"), (30, 30))
        ttk.Button(surface, text="Построить", command=self.build_model).pack(fill="x")
        files = ttk.Frame(surface)
        files.pack(fill="x", pady=(5, 0))
        ttk.Button(files, text="Сохранить OBJ", command=self.save_to_file).pack(
            side="left", fill="x", expand=True)
        ttk.Button(files, text="Загрузить OBJ", command=self.load_from_file).pack(
            side="left", fill="x", expand=True, padx=(5, 0))

        self.transform_controls(controls, "Смещение", ("dx", "dy", "dz"),
                                (0, 0, 0), task2.translate)
        self.transform_controls(controls, "Поворот вокруг OX, OY, OZ",
                                ("X, °", "Y, °", "Z, °"), (0, 0, 0),
                                task2.rotate_about_origin)
        self.transform_controls(controls, "Масштабирование относительно начала",
                                ("kx", "ky", "kz"), (1, 1, 1), task2.scale_about_origin)
        mirror = ttk.LabelFrame(controls, text="Отражение", padding=8)
        mirror.pack(fill="x", pady=(8, 0))
        self.plane = tk.StringVar(value="XY")
        ttk.Combobox(mirror, textvariable=self.plane, values=("XY", "XZ", "YZ"),
                     state="readonly").pack(fill="x")
        ttk.Button(mirror, text="Применить", command=lambda: self.apply_transform(
            task2.reflect, extra=(self.plane.get(),))).pack(fill="x", pady=(5, 0))

        self.canvas = tk.Canvas(self, background="white", width=700, height=600)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.bind("<Configure>", self.redraw)
        self.build_model()

    @staticmethod
    def entries(parent, labels, defaults):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        variables = []
        for column, (label, default) in enumerate(zip(labels, defaults)):
            cell = ttk.Frame(row)
            cell.grid(row=0, column=column, padx=3, sticky="ew")
            row.columnconfigure(column, weight=1)
            ttk.Label(cell, text=label).pack(anchor="w")
            variable = tk.StringVar(value=str(default))
            ttk.Entry(cell, textvariable=variable, width=9).pack(fill="x")
            variables.append(variable)
        return variables

    def transform_controls(self, parent, title, labels, defaults, operation):
        box = ttk.LabelFrame(parent, text=title, padding=8)
        box.pack(fill="x", pady=(8, 0))
        variables = self.entries(box, labels, defaults)
        ttk.Button(box, text="Применить", command=lambda: self.apply_transform(
            operation, variables)).pack(fill="x")

    @staticmethod
    def numbers(variables):
        values = [float(v.get().replace(",", ".")) for v in variables]
        if not all(math.isfinite(v) for v in values):
            raise ValueError("Введите конечные числа")
        return values

    def build_model(self):
        try:
            bounds = self.numbers(self.x_range + self.y_range)
            nx, ny = (int(v.get()) for v in self.subdivisions)
            model = build_surface(FUNCTIONS[self.function_name.get()], *bounds, nx, ny)
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            messagebox.showerror("Ошибка параметров", str(error), parent=self)
            return
        self.set_model(model)

    def set_model(self, model):
        self.polyhedron = model
        # Масштаб вида подбирается при построении и загрузке модели.
        points = project_vertices(model.vertices, self.projection)
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        self.view_center = (min(xs) / 2 + max(xs) / 2, min(ys) / 2 + max(ys) / 2)
        self.view_span = (max(max(xs) - min(xs), 1e-9),
                          max(max(ys) - min(ys), 1e-9))
        self.redraw()

    def save_to_file(self):
        path = filedialog.asksaveasfilename(
            parent=self, title="Сохранить модель", defaultextension=".obj",
            filetypes=[("Wavefront OBJ", "*.obj")])
        if not path:
            return
        try:
            save_obj(self.polyhedron, path)
        except OSError as error:
            messagebox.showerror("Ошибка сохранения", str(error), parent=self)

    def load_from_file(self):
        path = filedialog.askopenfilename(
            parent=self, title="Загрузить модель",
            filetypes=[("Wavefront OBJ", "*.obj")])
        if not path:
            return
        try:
            model = load_obj(path)
            if not all(math.isfinite(v) for p in model.vertices for v in (p.x, p.y, p.z)):
                raise ValueError("Координаты модели должны быть конечными числами")
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка загрузки", str(error), parent=self)
            return
        self.set_model(model)

    def apply_transform(self, operation, variables=(), extra=()):
        try:
            model = operation(self.polyhedron, *extra, *self.numbers(variables))
            if not all(math.isfinite(v) for p in model.vertices for v in (p.x, p.y, p.z)):
                raise ValueError("Результат преобразования вне числового диапазона")
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            messagebox.showerror("Ошибка параметров", str(error), parent=self)
            return
        self.polyhedron = model
        self.redraw()

    def redraw(self, event=None):
        self.canvas.delete("all")
        if self.polyhedron is None:
            return
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        scale = 0.85 * min(width / self.view_span[0], height / self.view_span[1])
        cx, cy = self.view_center
        # Видовая и проекционная матрицы: лекция 9, аксонометрическая проекция.
        points = project_vertices(self.polyhedron.vertices, self.projection)
        screen = [(width / 2 + (x / w - cx) * scale,
                   height / 2 - (y / w - cy) * scale) for x, y, z, w in points]
        for a, b in self.polyhedron.edges:
            self.canvas.create_line(*screen[a], *screen[b], fill="#24578a")


def main():
    root = tk.Tk()
    root.title("Лабораторная №7. Задание 3")
    root.geometry("1100x750")
    root.minsize(950, 750)
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
