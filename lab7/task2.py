import math
import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root_dir, 'lab6'))
sys.path.insert(1, root_dir)

from lab6.main import Point3D, Polygon, Polyhedron
from lab6 import task2
from lab6.projections import axonometric_matrix, perspective_matrix, project_edge, project_vertices

poly = None
base = None
size = 1.0
zoom = 1.0



def rotate_point(p, axis, a):
    x, y, z = p
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return (x, y * c - z * s, y * s + z * c)
    if axis == "y":
        return (x * c + z * s, y, -x * s + z * c)
    return (x * c - y * s, x * s + y * c, z)


def parse_profile(text):
    points = []
    for line in text.splitlines():
        if line.strip():
            try:
                r, h = map(float, line.replace(",", ".").split())
            except ValueError:
                raise ValueError(f"Строка '{line}': нужно два числа")
            points.append((r, h))
    return points


def build_revolution(profile, axis, n):
    if len(profile) < 2:
        raise ValueError("В образующей минимум 2 точки")
    if n < 3:
        raise ValueError("Разбиений минимум 3")

    step = math.radians(360 / n)
    verts = []
    table = []
    for r, h in profile:
        p = {"x": (h, r, 0), "y": (r, h, 0), "z": (r, 0, h)}[axis]
        if abs(r) < 1e-9:
            verts.append(Point3D(*p))
            table.append([len(verts) - 1] * n)
        else:
            row = []
            for k in range(n):
                row.append(len(verts))
                verts.append(Point3D(*rotate_point(p, axis, step * k)))
            table.append(row)

    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        for i in range(len(profile) - 1):
            quad = [table[i][k], table[i + 1][k], table[i + 1][k2], table[i][k2]]
            face = [v for j, v in enumerate(quad) if v != quad[j - 1]]
            if len(face) >= 3:
                faces.append(Polygon(face))

    figure = Polyhedron(verts, faces, f"Фигура вращения ({axis}, {n})")

    c = figure.get_center()
    s = 0
    for f in faces:
        nx, ny, nz = f.get_normal(verts)
        p = verts[f.indices[0]]
        s += nx * (p.x - c.x) + ny * (p.y - c.y) + nz * (p.z - c.z)
    if s < 0:
        for f in faces:
            f.indices.reverse()
    return figure



def save_obj(figure, path):
    with open(path, "w", encoding="utf-8") as f:
        for p in figure.vertices:
            f.write(f"v {p.x:.6f} {p.y:.6f} {p.z:.6f}\n")
        for face in figure.faces:
            f.write("f " + " ".join(str(i + 1) for i in face.indices) + "\n")


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



def draw(_=None):
    canvas.delete("all")
    if poly is None:
        return
    if projection_box.get() == "Перспективная":
        matrix = perspective_matrix(6.0 * size)
    else:
        matrix = axonometric_matrix()
    points = project_vertices(poly.vertices, matrix)
    w, h = canvas.winfo_width(), canvas.winfo_height()
    scale = min(w, h) / 8 / size * zoom
    for a, b in poly.edges:
        edge = project_edge(points[a], points[b])
        if edge:
            (x0, y0), (x1, y1) = edge
            canvas.create_line(w / 2 + x0 * scale, h / 2 - y0 * scale, w / 2 + x1 * scale, h / 2 - y1 * scale, fill="#24578a", width=2)
    canvas.create_text(10, 10, anchor="nw", text=f"вершин: {len(poly.vertices)}, граней: {len(poly.faces)}")


def set_model(new):
    global poly, base, size, zoom
    poly = base = new
    r = max(math.sqrt(p.x ** 2 + p.y ** 2 + p.z ** 2) for p in new.vertices)
    size = max(r, 0.1) / 1.7
    zoom = 1.0
    draw()


def numbers(entry_list):
    try:
        return [float(e.get().replace(",", ".")) for e in entry_list]
    except ValueError:
        raise ValueError("Введите числа")


def safe(fn):
    def wrapper():
        try:
            fn()
        except (ValueError, OSError, ZeroDivisionError, OverflowError) as e:
            messagebox.showerror("Ошибка", str(e))
    return wrapper


def apply(operation, *args):
    global poly
    if poly is None:
        raise ValueError("Сначала постройте или загрузите модель")
    poly = operation(poly, *args)
    draw()


def on_build():
    axis = axis_box.get()
    set_model(build_revolution(parse_profile(profile_text.get("1.0", "end")), axis, int(numbers([n_entry])[0])))


def on_save():
    if poly is None:
        raise ValueError("Нечего сохранять")
    path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("OBJ", "*.obj")])
    if path:
        save_obj(poly, path)


def on_load():
    path = filedialog.askopenfilename(filetypes=[("OBJ", "*.obj")])
    if path:
        set_model(load_obj(path))


def on_reset():
    global poly
    if base is not None:
        poly = base
        draw()


def change_zoom(k):
    global zoom
    zoom *= k
    draw()



def entries(parent, labels, defaults):
    row = ttk.Frame(parent)
    row.pack(fill="x", pady=2)
    result = []
    for label, default in zip(labels, defaults):
        cell = ttk.Frame(row)
        cell.pack(side="left", padx=3)
        ttk.Label(cell, text=label).pack(anchor="w")
        e = ttk.Entry(cell, width=6)
        e.insert(0, str(default))
        e.pack()
        result.append(e)
    return result


def combo(parent, values, default, width=6):
    cb = ttk.Combobox(parent, values=values, width=width, state="readonly")
    cb.set(default)
    cb.pack(anchor="w", pady=2)
    return cb


def button(parent, text, command):
    ttk.Button(parent, text=text, command=safe(command)).pack(fill="x", pady=2)


def group(parent, title):
    frame = ttk.LabelFrame(parent, text=title, padding=6)
    frame.pack(fill="x", pady=4)
    return frame


window = tk.Tk()
window.title("Лаба 7. Фигура вращения")
window.geometry("1100x720")
left = ttk.Frame(window, padding=8)
left.pack(side="left", fill="y")
canvas = tk.Canvas(window, width=700, height=600, bg="white")
canvas.pack(side="right", fill="both", expand=True)

tabs = ttk.Notebook(left)
tabs.pack(fill="both", expand=True)
tab_build = ttk.Frame(tabs, padding=6)
tab_move = ttk.Frame(tabs, padding=6)
tab_line = ttk.Frame(tabs, padding=6)
tabs.add(tab_build, text="Фигура")
tabs.add(tab_move, text="Преобразования")
tabs.add(tab_line, text="Прямая")
button(left, "Сбросить к исходной", on_reset)

# вкладка "Фигура"
ttk.Label(tab_build, text="Образующая (точка в строке):").pack(anchor="w")
ttk.Label(tab_build, foreground="gray",
          text="два числа: расстояние от оси, высота").pack(anchor="w")
profile_text = tk.Text(tab_build, width=24, height=6)
profile_text.insert("1.0", "0 -1\n1 -1\n1.5 0\n1 1\n0 1")
profile_text.pack(pady=4)
ttk.Label(tab_build, text="Ось вращения").pack(anchor="w")
axis_box = combo(tab_build, ["x", "y", "z"], "y")
n_entry, = entries(tab_build, ["Разбиений"], [24])
ttk.Label(tab_build, text="Проекция").pack(anchor="w")
projection_box = combo(tab_build, ["Аксонометрическая", "Перспективная"], "Аксонометрическая", 20)
projection_box.bind("<<ComboboxSelected>>", draw)
button(tab_build, "Построить", on_build)
button(tab_build, "Сохранить в .obj", on_save)
button(tab_build, "Загрузить из .obj", on_load)

box = group(tab_move, "Смещение")
shift = entries(box, ["dx", "dy", "dz"], [0.5, 0, 0])
button(box, "Применить", lambda: apply(task2.translate, *numbers(shift)))

box = group(tab_move, "Вращение через центр")
rot_axis = combo(box, ["x", "y", "z"], "y")
rot_angle = entries(box, ["Угол, °"], [30])
button(box, "Применить", lambda: apply(task2.rotate_about_center_axis, rot_axis.get(), numbers(rot_angle)[0]))

box = group(tab_move, "Масштаб относительно центра")
scale_k = entries(box, ["kx", "ky", "kz"], [1.5, 1.5, 1.5])
button(box, "Применить", lambda: apply(task2.scale_about_center, *numbers(scale_k)))

box = group(tab_move, "Отражение относительно плоскости")
plane = combo(box, ["xy", "xz", "yz"], "xy")
button(box, "Применить", lambda: apply(task2.reflect, plane.get()))

box = group(tab_line, "Поворот вокруг прямой через две точки")
point1 = entries(box, ["x1", "y1", "z1"], [0, 0, 0])
point2 = entries(box, ["x2", "y2", "z2"], [1, 1, 0])
angle = entries(box, ["Угол, °"], [30])
button(box, "Применить", lambda: apply(task2.rotate_about_line, numbers(point1), numbers(point2), numbers(angle)[0]))

canvas.bind("<Configure>", draw)
canvas.bind("<MouseWheel>", lambda e: change_zoom(1.1 if e.delta > 0 else 1 / 1.1))
canvas.bind("<Button-4>", lambda e: change_zoom(1.1))
canvas.bind("<Button-5>", lambda e: change_zoom(1 / 1.1))

safe(on_build)()
window.mainloop()