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

SIZE = 480  # размер изображения в пикселях

# Направление обзора (от объекта к наблюдателю) и оси экрана
AZIMUTH, ELEVATION = math.radians(30), math.radians(25)
VIEW = (math.cos(ELEVATION) * math.sin(AZIMUTH), math.sin(ELEVATION),
        math.cos(ELEVATION) * math.cos(AZIMUTH))
RIGHT = (math.cos(AZIMUTH), 0.0, -math.sin(AZIMUTH))
UP = (VIEW[1] * RIGHT[2] - VIEW[2] * RIGHT[1],
      VIEW[2] * RIGHT[0] - VIEW[0] * RIGHT[2],
      VIEW[0] * RIGHT[1] - VIEW[1] * RIGHT[0])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1],
            a[2] * b[0] - a[0] * b[2],
            a[0] * b[1] - a[1] * b[0])


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def xyz(p):
    return (p.x, p.y, p.z)


# --- текстура: шахматная доска, цвет зависит от (u, v), чтобы была видна ориентация ---
def make_texture(n=64):
    texture = []
    for j in range(n):
        row = []
        for i in range(n):
            k = 1.0 if (i // 8 + j // 8) % 2 == 0 else 0.55
            row.append((255 * i / (n - 1) * k, 255 * j / (n - 1) * k, 160 * k))
        texture.append(row)
    return texture


TEXTURE = make_texture()


def sample(u, v):
    """Билинейная интерполяция: смешиваем 4 ближайших текселя."""
    n = len(TEXTURE)
    x = min(1.0, max(0.0, u)) * (n - 1)
    y = min(1.0, max(0.0, v)) * (n - 1)
    x0, y0 = int(x), int(y)
    x1, y1 = min(x0 + 1, n - 1), min(y0 + 1, n - 1)
    fx, fy = x - x0, y - y0
    color = []
    for c in range(3):
        top = TEXTURE[y0][x0][c] * (1 - fx) + TEXTURE[y0][x1][c] * fx
        bottom = TEXTURE[y1][x0][c] * (1 - fx) + TEXTURE[y1][x1][c] * fx
        color.append(int(top * (1 - fy) + bottom * fy))
    return "#%02x%02x%02x" % tuple(color)


def inside(px, py, polygon):
    """Точка внутри выпуклого многоугольника: все векторные произведения одного знака."""
    signs = []
    for (x0, y0), (x1, y1) in zip(polygon, polygon[1:] + polygon[:1]):
        signs.append((x1 - x0) * (py - y0) - (y1 - y0) * (px - x0))
    return all(s >= 0 for s in signs) or all(s <= 0 for s in signs)


def draw_face(buffer, view_points, perspective, k, distance):
    """Текстурирование грани по лекции: p = a + u*e1 + v*e2.
    Вершинам соответствуют текстурные координаты: P1 -> (0,0), P2 -> (1,0),
    последняя вершина (P4 у четырёхугольника) -> (0,1), P3 -> (1,1).
    view_points - вершины в системе наблюдателя (x вправо, y вверх, z - глубина)."""
    a = view_points[0]
    e1 = sub(view_points[1], a)
    e2 = sub(view_points[-1], a)

    # положение вершин на экране
    dk = distance * k
    if perspective:
        screen = [(SIZE / 2 + x / z * dk, SIZE / 2 - y / z * dk) for x, y, z in view_points]
        n, m, l = cross(e1, e2), cross(e2, a), cross(a, e1)  # для правила Крамера
    else:
        screen = [(SIZE / 2 + x * k, SIZE / 2 - y * k) for x, y, z in view_points]
        det = e1[0] * e2[1] - e1[1] * e2[0]
        if abs(det) < 1e-9:  # грань видна ребром
            return

    xs, ys = [p[0] for p in screen], [p[1] for p in screen]
    for py in range(max(0, int(min(ys))), min(SIZE - 1, int(max(ys)) + 1) + 1):
        for px in range(max(0, int(min(xs))), min(SIZE - 1, int(max(xs)) + 1) + 1):
            if not inside(px + 0.5, py + 0.5, screen):
                continue
            if perspective:
                # X = x/z, Y = y/z - координаты пикселя на плоскости изображения
                X, Y = (px + 0.5 - SIZE / 2) / dk, (SIZE / 2 - py - 0.5) / dk
                delta = X * n[0] + Y * n[1] + n[2]
                if abs(delta) < 1e-12:
                    continue
                u = (X * m[0] + Y * m[1] + m[2]) / delta
                v = (X * l[0] + Y * l[1] + l[2]) / delta
            else:
                # параллельная проекция: решаем систему 2x2 по правилу Крамера
                dx = (px + 0.5 - SIZE / 2) / k - a[0]
                dy = (SIZE / 2 - py - 0.5) / k - a[1]
                u = (dx * e2[1] - dy * e2[0]) / det
                v = (e1[0] * dy - e1[1] * dx) / det
            buffer[py][px] = sample(u, v)


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
        self.polyhedron = task2.translate(poly, -c.x, -c.y, -c.z)  # центр в начало координат
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

        buffer = [["#ffffff"] * SIZE for _ in range(SIZE)]
        vertices = self.polyhedron.vertices
        center = xyz(self.polyhedron.get_center())
        for face in self.polyhedron.faces:
            points = [xyz(vertices[i]) for i in face.indices]
            face_center = tuple(sum(c) / len(points) for c in zip(*points))

            # Отсечение нелицевых граней (как в лабораторной 8)
            n = face.get_normal(vertices)
            if dot(n, sub(face_center, center)) < 0:
                n = (-n[0], -n[1], -n[2])
            to_viewer = sub(camera, points[0]) if perspective else VIEW
            if dot(n, to_viewer) <= 0:
                continue

            # переходим в систему наблюдателя: x вправо, y вверх, z - расстояние до камеры
            view_points = [(dot(p, RIGHT), dot(p, UP), distance - dot(p, VIEW)) for p in points]
            if perspective and any(z <= 0 for _, _, z in view_points):
                continue
            draw_face(buffer, view_points, perspective, k, distance)

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