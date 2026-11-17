import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(project_root, 'lab6'))
sys.path.insert(1, project_root)

from lab6.main import POLYHEDRONS
from lab6 import task2
from lab7.task1 import load_obj


# Векторные функции
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


class Application(ttk.Frame):
    def __init__(self, master):
        super().__init__(master, padding=10)
        self.pack(fill="both", expand=True)
        self.figure_name = tk.StringVar(value="Гексаэдр (Куб)")
        self.projection_name = tk.StringVar(value="Параллельная")
        self.culling = tk.BooleanVar(value=True)
        self.show_normals = tk.BooleanVar(value=True)
        self.spin = tk.BooleanVar(value=True)
        self.azimuth = tk.DoubleVar(value=30)    # направление обзора: азимут
        self.elevation = tk.DoubleVar(value=25)  # направление обзора: высота
        self.polyhedron = None
        self.radius = 1.0
        self._build_interface()
        self.set_model(POLYHEDRONS[self.figure_name.get()]())
        self.animate()

    def _build_interface(self):
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        controls = ttk.Frame(self)
        controls.grid(row=0, column=0, sticky="ns", padx=(0, 10))

        ttk.Label(controls, text="Многогранник").pack(anchor="w")
        figures = ttk.Combobox(controls, textvariable=self.figure_name,
                               values=list(POLYHEDRONS), state="readonly", width=28)
        figures.pack(fill="x", pady=(3, 6))
        figures.bind("<<ComboboxSelected>>", self.select_figure)
        ttk.Button(controls, text="Загрузить OBJ...",
                   command=self.load_from_file).pack(fill="x", pady=(0, 12))

        ttk.Label(controls, text="Проекция").pack(anchor="w")
        projections = ttk.Combobox(controls, textvariable=self.projection_name,
                                   values=("Параллельная", "Перспективная"),
                                   state="readonly", width=28)
        projections.pack(fill="x", pady=(3, 12))
        projections.bind("<<ComboboxSelected>>", self.redraw)

        view = ttk.LabelFrame(controls, text="Вектор обзора", padding=8)
        view.pack(fill="x", pady=(0, 12))

        az_frame = ttk.Frame(view)
        az_frame.pack(fill="x", pady=2)
        ttk.Label(az_frame, text="Азимут, °").pack(side="left")
        az_entry = ttk.Entry(az_frame, textvariable=self.azimuth, width=6)
        az_entry.pack(side="right")
        az_entry.bind("<Return>", lambda e: self.redraw())

        ttk.Scale(view, from_=-180, to=180, variable=self.azimuth,
                  command=self.redraw).pack(fill="x", pady=(0, 8))

        el_frame = ttk.Frame(view)
        el_frame.pack(fill="x", pady=2)
        ttk.Label(el_frame, text="Высота, °").pack(side="left")
        el_entry = ttk.Entry(el_frame, textvariable=self.elevation, width=6)
        el_entry.pack(side="right")
        el_entry.bind("<Return>", lambda e: self.redraw())

        ttk.Scale(view, from_=-89, to=89, variable=self.elevation,
                  command=self.redraw).pack(fill="x")

        ttk.Checkbutton(controls, text="Отсекать нелицевые грани",
                        variable=self.culling, command=self.redraw).pack(anchor="w")
        ttk.Checkbutton(controls, text="Показывать нормали",
                        variable=self.show_normals, command=self.redraw).pack(anchor="w")
        ttk.Checkbutton(controls, text="Вращать объект",
                        variable=self.spin).pack(anchor="w")

        ttk.Button(controls, text="Сбросить поворот",
                   command=self.reset_rotation).pack(fill="x", pady=(10, 0))

        self.canvas = tk.Canvas(self, background="white", highlightthickness=1,
                                highlightbackground="#aaaaaa", width=700, height=600)
        self.canvas.grid(row=0, column=1, sticky="nsew")
        self.canvas.bind("<Configure>", self.redraw)

    def reset_rotation(self):
        self.set_model(POLYHEDRONS[self.figure_name.get()]())

    def set_model(self, model):
        """Переносит центр модели в начало координат и запоминает её размер."""
        c = model.get_center()
        model = task2.translate(model, -c.x, -c.y, -c.z)
        self.radius = max(math.sqrt(p.x ** 2 + p.y ** 2 + p.z ** 2)
                          for p in model.vertices) or 1.0
        self.polyhedron = model
        self.redraw()

    def select_figure(self, event=None):
        self.set_model(POLYHEDRONS[self.figure_name.get()]())

    def load_from_file(self):
        path = filedialog.askopenfilename(
            title="Загрузить модель",
            filetypes=[("Wavefront OBJ", "*.obj"), ("Все файлы", "*.*")])
        if not path:
            return
        try:
            model = load_obj(path)
        except (OSError, ValueError) as error:
            messagebox.showerror("Ошибка загрузки", str(error),
                                 parent=self.winfo_toplevel())
            return
        self.set_model(model)

    def animate(self):
        if self.spin.get():
            self.polyhedron = task2.rotate_about_center_axis(self.polyhedron, "y", 2)
            self.polyhedron = task2.rotate_about_center_axis(self.polyhedron, "x", 1)
            self.redraw()
        self.after(30, self.animate)

    def redraw(self, event=None):
        self.canvas.delete("all")
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        perspective = self.projection_name.get() == "Перспективная"

        az = math.radians(self.azimuth.get())
        el = math.radians(self.elevation.get())
        v = (math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az))
        right = (math.cos(az), 0.0, -math.sin(az))
        up = cross(v, right)
        distance = 4 * self.radius
        camera = (v[0] * distance, v[1] * distance, v[2] * distance)
        k = min(width, height) / (2.4 * self.radius)

        def project(p):
            s = distance / (distance - dot(p, v)) if perspective else 1.0
            return (width / 2 + dot(p, right) * s * k,
                    height / 2 - dot(p, up) * s * k)

        vertices = self.polyhedron.vertices
        center = xyz(self.polyhedron.get_center())
        drawn = 0
        for face in self.polyhedron.faces:
            points = [xyz(vertices[i]) for i in face.indices]
            face_center = tuple(sum(c) / len(points) for c in zip(*points))

            n = face.get_normal(vertices)
            if dot(n, sub(face_center, center)) < 0:
                n = (-n[0], -n[1], -n[2])

            to_viewer = sub(camera, points[0]) if perspective else v
            front = dot(n, to_viewer) > 0
            if self.culling.get() and not front:
                continue
            drawn += 1

            coords = [c for p in points for c in project(p)]
            if self.culling.get():
                light = 0.4 + 0.6 * max(0.0, dot(n, v))
                fill = "#%02x%02x%02x" % tuple(int(c * light) for c in (120, 180, 240))
            else:
                fill = ""  # без отсечения рисуем каркас, чтобы были видны все рёбра
            self.canvas.create_polygon(*coords, fill=fill, outline="#24578a", width=2)

            if self.show_normals.get():
                tip = tuple(face_center[i] + n[i] * 0.4 * self.radius for i in range(3))
                self.canvas.create_line(*project(face_center), *project(tip), fill="#cc2222", width=2, arrow=tk.LAST)

        self.canvas.create_text(10, 10, anchor="nw", text=f"Граней отрисовано: {drawn} из {len(self.polyhedron.faces)}")


def main():
    root = tk.Tk()
    root.title("Лабораторная №8. Пункт 1: отсечение нелицевых граней")
    root.geometry("1050x680")
    root.minsize(900, 600)
    Application(root)
    root.mainloop()


if __name__ == "__main__":
    main()