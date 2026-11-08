import math
import tkinter as tk
from tkinter import messagebox, ttk

from main import POLYHEDRONS
import task2
from projections import (axonometric_matrix, perspective_matrix,
                         project_edge, project_vertices)


class Application(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.figure_name = tk.StringVar(value="Гексаэдр (Куб)")
        self.projection_name = tk.StringVar(value="Аксонометрическая")
        self.polyhedron = POLYHEDRONS[self.figure_name.get()]()
        self._build_interface()
        self.redraw()

    def _build_interface(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Label(controls, text="Многогранник").pack(anchor="w")
        figures = ttk.Combobox(controls, textvariable=self.figure_name,
                               values=list(POLYHEDRONS), state="readonly", width=31)
        figures.pack(fill="x", pady=(3, 12))
        figures.bind("<<ComboboxSelected>>", self.select_figure)

        ttk.Label(controls, text="Проекция").pack(anchor="w")
        projections = ttk.Combobox(controls, textvariable=self.projection_name,
                                   values=("Аксонометрическая", "Перспективная"),
                                   state="readonly", width=31)
        projections.pack(fill="x", pady=(3, 12))
        projections.bind("<<ComboboxSelected>>", self.redraw)

        notebook = ttk.Notebook(controls)
        notebook.pack(fill="both", expand=True)
        origin = ttk.Frame(notebook, padding=8)
        center = ttk.Frame(notebook, padding=8)
        line = ttk.Frame(notebook, padding=8)
        notebook.add(origin, text="Начало координат")
        notebook.add(center, text="Центр")
        notebook.add(line, text="Прямая")

        move = self._group(origin, "Смещение")
        self.shift = self._entries(move, ("dx", "dy", "dz"), (0, 0, 0))
        self._button(move, lambda: self.apply(task2.translate, self.shift))

        rotate = self._group(origin, "Поворот вокруг осей OX, OY, OZ")
        self.angles = self._entries(rotate, ("X, °", "Y, °", "Z, °"), (0, 0, 0))
        ttk.Label(rotate, text="Порядок: X → Y → Z").pack(anchor="w")
        self._button(rotate, lambda: self.apply(task2.rotate_about_origin, self.angles))

        scale = self._group(origin, "Масштабирование")
        self.origin_scale = self._entries(scale, ("kx", "ky", "kz"), (1, 1, 1))
        self._button(scale, lambda: self.apply(task2.scale_about_origin, self.origin_scale))

        mirror = self._group(origin, "Отражение относительно плоскости")
        self.plane = tk.StringVar(value="XY")
        ttk.Combobox(mirror, textvariable=self.plane, values=("XY", "XZ", "YZ"),
                     state="readonly", width=8).pack(anchor="w")
        self._button(mirror, lambda: self.apply(task2.reflect, extra=(self.plane.get(),)))

        scale_center = self._group(center, "Масштабирование относительно центра")
        self.center_scale = self._entries(scale_center, ("kx", "ky", "kz"), (1, 1, 1))
        self._button(scale_center, lambda: self.apply(task2.scale_about_center, self.center_scale))

        rotate_center = self._group(center, "Вращение через центр")
        ttk.Label(rotate_center, text="Ось, параллельная прямой вращения").pack(anchor="w")
        self.axis = tk.StringVar(value="X")
        ttk.Combobox(rotate_center, textvariable=self.axis, values=("X", "Y", "Z"),
                     state="readonly", width=8).pack(anchor="w", pady=4)
        self.center_angle = self._entries(rotate_center, ("Угол, °",), (0,))
        self._button(rotate_center, lambda: self.apply(
            task2.rotate_about_center_axis, self.center_angle, (self.axis.get(),)))

        arbitrary = self._group(line, "Прямая через две точки")
        ttk.Label(arbitrary, text="Первая точка").pack(anchor="w")
        self.line_start = self._entries(arbitrary, ("x1", "y1", "z1"), (0, 0, 0))
        ttk.Label(arbitrary, text="Вторая точка").pack(anchor="w")
        self.line_end = self._entries(arbitrary, ("x2", "y2", "z2"), (0, 1, 0))
        self.line_angle = self._entries(arbitrary, ("Угол, °",), (0,))
        self._button(arbitrary, self.rotate_line)

        self.canvas = tk.Canvas(self, background="white", highlightthickness=1,
                                highlightbackground="#aaaaaa", width=700, height=600)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.bind("<Configure>", self.redraw)

    @staticmethod
    def _group(parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=8)
        frame.pack(fill="x", pady=(0, 10))
        return frame

    @staticmethod
    def _entries(parent, labels, defaults):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=5)
        variables = []
        for column, (label, default) in enumerate(zip(labels, defaults)):
            row.columnconfigure(column, weight=1)
            cell = ttk.Frame(row)
            cell.grid(row=0, column=column, sticky="ew", padx=3)
            ttk.Label(cell, text=label).pack(anchor="w")
            variable = tk.StringVar(value=str(default))
            ttk.Entry(cell, textvariable=variable, width=8).pack(fill="x")
            variables.append(variable)
        return variables

    @staticmethod
    def _button(parent, command):
        ttk.Button(parent, text="Применить", command=command).pack(anchor="e", pady=(5, 0))

    @staticmethod
    def _numbers(variables):
        try:
            values = [float(variable.get().replace(",", ".")) for variable in variables]
        except ValueError:
            raise ValueError("Введите числовые значения параметров") from None
        if not all(math.isfinite(value) for value in values):
            raise ValueError("Параметры должны быть конечными числами")
        return values

    def _update_polyhedron(self, operation):
        try:
            result = operation()
            if not all(math.isfinite(value) for point in result.vertices
                       for value in (point.x, point.y, point.z)):
                raise ValueError("Результат преобразования выходит за числовой диапазон")
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            messagebox.showerror("Ошибка параметров", str(error), parent=self.winfo_toplevel())
            return
        self.polyhedron = result
        self.redraw()

    def apply(self, operation, variables=(), extra=()):
        self._update_polyhedron(lambda: operation(
            self.polyhedron, *extra, *self._numbers(variables)))

    def rotate_line(self):
        self._update_polyhedron(lambda: task2.rotate_about_line(
            self.polyhedron, self._numbers(self.line_start),
            self._numbers(self.line_end), self._numbers(self.line_angle)[0]))

    def select_figure(self, event=None):
        self.polyhedron = POLYHEDRONS[self.figure_name.get()]()
        self.redraw()

    def redraw(self, event=None):
        self.canvas.delete("all")
        matrix = (perspective_matrix() if self.projection_name.get() == "Перспективная"
                  else axonometric_matrix())
        points = project_vertices(self.polyhedron.vertices, matrix)
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        # Фиксированный масштаб относительно окна сохраняет видимость смещения
        # и изменения размеров: фигура не центрируется после преобразования.
        scale = min(width, height) / 8
        for a, b in self.polyhedron.edges:
            edge = project_edge(points[a], points[b])
            if edge is not None:
                coordinates = [coordinate for x, y in edge
                               for coordinate in (width / 2 + x * scale,
                                                  height / 2 - y * scale)]
                self.canvas.create_line(*coordinates, fill="#24578a", width=2)


def main():
    root = tk.Tk()
    root.title("Лабораторная №6. Аффинные преобразования и проекции")
    root.geometry("1120x720")
    root.minsize(1000, 680)
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()
