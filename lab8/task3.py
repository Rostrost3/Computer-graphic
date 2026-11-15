import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root_dir, 'lab6'))
sys.path.insert(1, root_dir)

from lab6.main import Point3D, Polygon, Polyhedron, POLYHEDRONS
from lab6 import task2
from lab6.projections import project_edge, project_vertices

poly = None
normals = []
target = (0, 0, 0)
axis_len = 1.0
camera = {"pos": (0, 0, 5), "dir": (0, 0, -1), "fov": 60, "near": 0.1, "far": 100.0, "view": None, "proj": None}



def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(a):
    length = math.sqrt(dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length)



def view_matrix(pos, direction, up=(0, 1, 0)):
    f = normalize(direction)
    r = normalize(cross(f, up))
    u = cross(r, f)
    return [[r[0], u[0], -f[0], 0],
            [r[1], u[1], -f[1], 0],
            [r[2], u[2], -f[2], 0],
            [-dot(pos, r), -dot(pos, u), dot(pos, f), 1]]


def projection_matrix(fov_deg, aspect, near, far):
    t = 1 / math.tan(math.radians(fov_deg) / 2)
    return [[t / aspect, 0, 0, 0],
            [0, t, 0, 0],
            [0, 0, (far + near) / (near - far), -1],
            [0, 0, 2 * far * near / (near - far), 0]]


def update_camera(aspect):
    az, el, d = math.radians(az_var.get()), math.radians(el_var.get()), dist_var.get()
    offset = (d * math.cos(el) * math.sin(az), d * math.sin(el), d * math.cos(el) * math.cos(az))
    pos = (target[0] + offset[0], target[1] + offset[1], target[2] + offset[2])
    direction = normalize(sub(target, pos))
    camera.update(pos=pos, dir=direction, fov=fov_var.get(), view=view_matrix(pos, direction), proj=projection_matrix(fov_var.get(), aspect, camera["near"], camera["far"]))



def set_model(figure):
    global poly, normals, target, axis_len
    c = figure.get_center()
    target = (c.x, c.y, c.z)
    r = max(math.sqrt((p.x - c.x) ** 2 + (p.y - c.y) ** 2 + (p.z - c.z) ** 2) for p in figure.vertices)

    for f in figure.faces:
        p = figure.vertices[f.indices[0]]
        if dot(f.get_normal(figure.vertices), (p.x - c.x, p.y - c.y, p.z - c.z)) < 0:
            f.indices.reverse()

    normals = [f.get_normal(figure.vertices) for f in figure.faces]
    poly = figure
    axis_len = 1.3 * r
    camera.update(near=0.05 * r, far=30 * r)
    dist_scale.config(from_=1.3 * r, to=8 * r, resolution=r / 100)
    dist_var.set(3.5 * r)
    draw()


def load_obj(path):
    verts, faces = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if t and t[0] == "v":
                verts.append(Point3D(*map(float, t[1:4])))
            elif t and t[0] == "f":
                faces.append(Polygon([int(s.split("/")[0]) - 1 for s in t[1:]]))
    if not verts or not faces or any(not 0 <= i < len(verts) for f in faces for i in f.indices):
        raise ValueError("Некорректный OBJ-файл")
    return Polyhedron(verts, faces, "Загруженная модель")



def draw_segment(p, q, w, h, color):
    seg = project_edge(p, q, camera["near"])     # отсекает часть позади камеры, делит на w
    if seg:
        (x0, y0), (x1, y1) = seg
        canvas.create_line((x0 + 1) / 2 * w, (1 - y0) / 2 * h,
                           (x1 + 1) / 2 * w, (1 - y1) / 2 * h, fill=color, width=2)


def draw(_=None):
    canvas.delete("all")
    if poly is None:
        return
    w, h = canvas.winfo_width(), canvas.winfo_height()
    update_camera(w / h)
    matrix = task2.mat_mul(camera["view"], camera["proj"])

    L = axis_len
    ends = project_vertices([Point3D(0, 0, 0), Point3D(L, 0, 0),
                             Point3D(0, L, 0), Point3D(0, 0, L)], matrix)
    for i, color in ((1, "red"), (2, "green"), (3, "blue")):
        draw_segment(ends[0], ends[i], w, h, color)

    points = project_vertices(poly.vertices, matrix)
    if hide_var.get():
        edges = set()
        for f, n in zip(poly.faces, normals):
            p = poly.vertices[f.indices[0]]
            if dot(n, sub(camera["pos"], (p.x, p.y, p.z))) > 0:
                k = len(f.indices)
                for i in range(k):
                    a, b = f.indices[i], f.indices[(i + 1) % k]
                    edges.add((min(a, b), max(a, b)))
    else:
        edges = poly.edges
    for a, b in edges:
        draw_segment(points[a], points[b], w, h, "#24578a")

    fmt = lambda v: "(%.2f, %.2f, %.2f)" % v
    canvas.create_text(10, 10, anchor="nw",
                       text=f"Камера: позиция {fmt(camera['pos'])}\n"
                            f"направление {fmt(camera['dir'])}\n"
                            f"угол обзора {camera['fov']:.0f}°, near {camera['near']:.2f}, "
                            f"far {camera['far']:.0f}")


def tick():
    if auto_var.get():
        az_var.set((az_var.get() + 2) % 360)
        draw()
    window.after(30, tick)


def safe(fn):
    def wrapper(*args):
        try:
            fn()
        except (ValueError, OSError) as e:
            messagebox.showerror("Ошибка", str(e))
    return wrapper


def on_load():
    path = filedialog.askopenfilename(filetypes=[("OBJ", "*.obj")])
    if path:
        set_model(load_obj(path))
        figure_box.set("")



window = tk.Tk()
window.title("Лаба 8. Камера")
window.geometry("1000x700")
left = ttk.Frame(window, padding=8)
left.pack(side="left", fill="y")
canvas = tk.Canvas(window, width=700, height=600, bg="white")
canvas.pack(side="right", fill="both", expand=True)

az_var = tk.DoubleVar(value=30)
el_var = tk.DoubleVar(value=20)
dist_var = tk.DoubleVar(value=5)
fov_var = tk.DoubleVar(value=60)
auto_var = tk.BooleanVar(value=True)
hide_var = tk.BooleanVar(value=True)

ttk.Label(left, text="Объект").pack(anchor="w")
figure_box = ttk.Combobox(left, values=list(POLYHEDRONS), state="readonly", width=28)
figure_box.set("Гексаэдр (Куб)")
figure_box.pack(pady=(2, 6))
figure_box.bind("<<ComboboxSelected>>", lambda e: set_model(POLYHEDRONS[figure_box.get()]()))
ttk.Button(left, text="Загрузить OBJ...", command=safe(on_load)).pack(fill="x", pady=(0, 8))


def slider(text, var, low, high, resolution=1):
    s = tk.Scale(left, label=text, variable=var, from_=low, to=high, resolution=resolution, orient="horizontal", command=draw)
    s.pack(fill="x")
    return s


slider("Азимут камеры, °", az_var, 0, 360)
slider("Высота камеры, °", el_var, -89, 89)
dist_scale = slider("Расстояние до объекта", dist_var, 2, 15, 0.05)
slider("Угол обзора (FOV), °", fov_var, 20, 120)
ttk.Checkbutton(left, text="Автовращение камеры", variable=auto_var).pack(anchor="w", pady=(8, 0))
ttk.Checkbutton(left, text="Скрывать нелицевые грани", variable=hide_var, command=draw).pack(anchor="w")

canvas.bind("<Configure>", draw)
set_model(POLYHEDRONS["Гексаэдр (Куб)"]())
tick()
window.mainloop()