import math
import os
import sys
import tkinter as tk
from tkinter import messagebox, ttk

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'lab6'))
sys.path.insert(1, project_root)

from lab6.main import POLYHEDRONS
from lab6 import task2

SIZE = 480

AZIMUTH, ELEVATION = math.radians(30), math.radians(25)
VIEW = (math.cos(ELEVATION) * math.sin(AZIMUTH), math.sin(ELEVATION),
        math.cos(ELEVATION) * math.cos(AZIMUTH))
RIGHT = (math.cos(AZIMUTH), 0.0, -math.sin(AZIMUTH))
UP = (VIEW[1] * RIGHT[2] - VIEW[2] * RIGHT[1],
      VIEW[2] * RIGHT[0] - VIEW[0] * RIGHT[2],
      VIEW[0] * RIGHT[1] - VIEW[1] * RIGHT[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def xyz(p):
    return (p.x, p.y, p.z)


def make_texture(n=64):
    texture = []
    for j in range(n):
        row = []
        for i in range(n):
            k = 1.0 if (i // 8 + j // 8) % 2 == 0 else 0.55
            r, g, b = 255 * i / (n - 1), 255 * j / (n - 1), 160
            row.append("#%02x%02x%02x" % (int(r * k), int(g * k), int(b * k)))
        texture.append(row)
    return texture


TEXTURE = make_texture()


def sample(u, v):
    n = len(TEXTURE)
    return TEXTURE[min(n - 1, max(0, int(v * n)))][min(n - 1, max(0, int(u * n)))]


def assign_uv(poly):
    for face in poly.faces:
        n = len(face.indices)
        if n == 3:
            uvs = [(0, 0), (1, 0), (0.5, 1)]
        elif n == 4:
            uvs = [(0, 0), (1, 0), (1, 1), (0, 1)]
        else:  # остальные многоугольники: вписываем в окружность
            uvs = [(0.5 + 0.5 * math.cos(2 * math.pi * i / n),
                    0.5 + 0.5 * math.sin(2 * math.pi * i / n)) for i in range(n)]
        face.uv = dict(zip(face.indices, uvs))


def draw_triangle(buffer, a, b, c):
    (x0, y0, s0, us0, vs0), (x1, y1, s1, us1, vs1), (x2, y2, s2, us2, vs2) = a, b, c
    den = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
    if abs(den) < 1e-9:
        return
    for y in range(max(0, int(min(y0, y1, y2))), min(SIZE - 1, int(max(y0, y1, y2)) + 1) + 1):
        for x in range(max(0, int(min(x0, x1, x2))), min(SIZE - 1, int(max(x0, x1, x2)) + 1) + 1):
            px, py = x + 0.5, y + 0.5
            la = ((y1 - y2) * (px - x2) + (x2 - x1) * (py - y2)) / den
            lb = ((y2 - y0) * (px - x2) + (x0 - x2) * (py - y2)) / den
            lc = 1 - la - lb
            if la < -1e-9 or lb < -1e-9 or lc < -1e-9:
                continue
            s = la * s0 + lb * s1 + lc * s2
            u = (la * us0 + lb * us1 + lc * us2) / s
            v = (la * vs0 + lb * vs1 + lc * vs2) / s
            buffer[y][x] = sample(u, v)


class Application(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.figure_name = tk.StringVar(value="Гексаэдр (Куб)")
        self.projection_name = tk.StringVar(value="Параллельная")
        self.polyhedron = None
        self.radius = 1.0
        self.image = None
        self._build_interface()
        self.select_figure()

    def _build_interface(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Label(controls, text="Многогранник").pack(anchor="w")
        figures = ttk.Combobox(controls, textvariable=self.figure_name,
                               values=list(POLYHEDRONS), state="readonly", width=28)
        figures.pack(fill="x", pady=(3, 10))
        figures.bind("<<ComboboxSelected>>", self.select_figure)

        ttk.Label(controls, text="Проекция").pack(anchor="w")
        projections = ttk.Combobox(controls, textvariable=self.projection_name,
                                   values=("Параллельная", "Перспективная"),
                                   state="readonly", width=28)
        projections.pack(fill="x", pady=(3, 10))
        projections.bind("<<ComboboxSelected>>", self.redraw)

        move = self._group(controls, "Смещение")
        self.shift = self._entries(move, ("dx", "dy", "dz"), (0, 0, 0))
        self._button(move, lambda: self.apply(task2.translate, self.shift))

        rotate = self._group(controls, "Поворот вокруг OX, OY, OZ")
        self.angles = self._entries(rotate, ("X, °", "Y, °", "Z, °"), (0, 0, 0))
        self._button(rotate, lambda: self.apply(task2.rotate_about_origin, self.angles))

        scale = self._group(controls, "Масштаб относительно центра")
        self.scale = self._entries(scale, ("kx", "ky", "kz"), (1, 1, 1))
        self._button(scale, lambda: self.apply(task2.scale_about_center, self.scale))

        mirror = self._group(controls, "Отражение")
        self.plane = tk.StringVar(value="XY")
        ttk.Combobox(mirror, textvariable=self.plane, values=("XY", "XZ", "YZ"),
                     state="readonly", width=8).pack(anchor="w")
        self._button(mirror, lambda: self.apply(task2.reflect, extra=(self.plane.get(),)))

        ttk.Button(controls, text="Сбросить", command=self.select_figure).pack(fill="x")

        self.canvas = tk.Canvas(self, background="white", highlightthickness=1,
                                highlightbackground="#aaaaaa", width=700, height=600)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.bind("<Configure>", self.redraw)

    @staticmethod
    def _group(parent, title):
        frame = ttk.LabelFrame(parent, text=title, padding=6)
        frame.pack(fill="x", pady=(0, 8))
        return frame

    @staticmethod
    def _entries(parent, labels, defaults):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=3)
        variables = []
        for column, (label, default) in enumerate(zip(labels, defaults)):
            row.columnconfigure(column, weight=1)
            cell = ttk.Frame(row)
            cell.grid(row=0, column=column, sticky="ew", padx=3)
            ttk.Label(cell, text=label).pack(anchor="w")
            variable = tk.StringVar(value=str(default))
            ttk.Entry(cell, textvariable=variable, width=7).pack(fill="x")
            variables.append(variable)
        return variables

    @staticmethod
    def _button(parent, command):
        ttk.Button(parent, text="Применить", command=command).pack(anchor="e", pady=(3, 0))

    @staticmethod
    def _numbers(variables):
        try:
            values = [float(v.get().replace(",", ".")) for v in variables]
        except ValueError:
            raise ValueError("Введите числовые значения параметров") from None
        if not all(math.isfinite(x) for x in values):
            raise ValueError("Параметры должны быть конечными числами")
        return values

    def select_figure(self, event=None):
        poly = POLYHEDRONS[self.figure_name.get()]()
        c = poly.get_center()
        self.polyhedron = task2.translate(poly, -c.x, -c.y, -c.z)
        assign_uv(self.polyhedron)
        self.radius = max(math.sqrt(p.x ** 2 + p.y ** 2 + p.z ** 2)
                          for p in self.polyhedron.vertices)
        self.redraw()

    def apply(self, operation, variables=(), extra=()):
        try:
            result = operation(self.polyhedron, *extra, *self._numbers(variables))
            if not all(math.isfinite(x) for p in result.vertices for x in xyz(p)):
                raise ValueError("Результат вне числового диапазона")
        except (ValueError, OverflowError, ZeroDivisionError) as error:
            messagebox.showerror("Ошибка параметров", str(error), parent=self.winfo_toplevel())
            return
        self.polyhedron = result
        self.redraw()

    def redraw(self, event=None):
        perspective = self.projection_name.get() == "Перспективная"
        distance = 4 * self.radius
        camera = tuple(c * distance for c in VIEW)
        k = SIZE / (2.4 * self.radius)

        def project(p, uv):
            depth = distance - dot(p, VIEW)
            if perspective and depth <= 0:
                return None
            s = distance / depth if perspective else 1.0
            return (SIZE / 2 + dot(p, RIGHT) * s * k, SIZE / 2 - dot(p, UP) * s * k,
                    s, uv[0] * s, uv[1] * s)

        buffer = [["#ffffff"] * SIZE for _ in range(SIZE)]
        vertices = self.polyhedron.vertices
        center = xyz(self.polyhedron.get_center())
        for face in self.polyhedron.faces:
            points = [xyz(vertices[i]) for i in face.indices]
            face_center = tuple(sum(c) / len(points) for c in zip(*points))

            n = face.get_normal(vertices)
            if dot(n, sub(face_center, center)) < 0:
                n = (-n[0], -n[1], -n[2])
            to_viewer = sub(camera, points[0]) if perspective else VIEW
            if dot(n, to_viewer) <= 0:
                continue

            projected = [project(p, face.uv[i]) for p, i in zip(points, face.indices)]
            if None in projected:
                continue
            for i in range(1, len(projected) - 1):
                draw_triangle(buffer, projected[0], projected[i], projected[i + 1])

        self.image = tk.PhotoImage(width=SIZE, height=SIZE)
        self.image.put(" ".join("{" + " ".join(row) + "}" for row in buffer))
        self.canvas.delete("all")
        self.canvas.create_image(self.canvas.winfo_width() / 2,
                                 self.canvas.winfo_height() / 2, image=self.image)


def main():
    root = tk.Tk()
    root.title("Лабораторная №9. Текстурирование")
    root.geometry("1000x680")
    root.minsize(900, 640)
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()