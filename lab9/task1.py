import math
import os
import sys
import tkinter as tk
from tkinter import colorchooser, filedialog, messagebox, ttk

root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(root_dir, 'lab6'))
sys.path.insert(1, root_dir)

from lab6.main import POLYHEDRONS
from lab6 import task2

RADIUS = 1.7
BACKGROUND = "#1e2228"
HEX = ["%02x" % i for i in range(256)]

base_verts = []
base_faces = []
base_normals = None
M = task2.identity()

world, faces, face_n, corner_n = [], [], [], []
cam = {"az": 30.0, "el": 20.0, "dist": 6.0}
obj_rgb = (70, 140, 230)
light_rgb = (255, 255, 255)
image = None
job = None
drag = None


def sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def normalize(a):
    length = math.sqrt(dot(a, a))
    return (a[0] / length, a[1] / length, a[2] / length) if length > 1e-12 else (0.0, 0.0, 0.0)


def mul_point(p, m):
    return tuple(p[0] * m[0][j] + p[1] * m[1][j] + p[2] * m[2][j] + m[3][j] for j in range(3))


def normal_matrix(m):
    a = [row[:3] for row in m[:3]]
    cof = [[a[(i + 1) % 3][(j + 1) % 3] * a[(i + 2) % 3][(j + 2) % 3]
            - a[(i + 1) % 3][(j + 2) % 3] * a[(i + 2) % 3][(j + 1) % 3] for j in range(3)]
           for i in range(3)]
    det = a[0][0] * cof[0][0] + a[0][1] * cof[0][1] + a[0][2] * cof[0][2]
    if abs(det) < 1e-9:
        raise ValueError("Вырожденное преобразование (масштаб 0)")
    return [[c / det for c in row] for row in cof], det


def view_matrix(pos, direction, up=(0, 1, 0)):
    f = normalize(direction)
    r = normalize(cross(f, up))
    u = cross(r, f)
    return [[r[0], u[0], -f[0], 0], [r[1], u[1], -f[1], 0], [r[2], u[2], -f[2], 0],
            [-dot(pos, r), -dot(pos, u), dot(pos, f), 1]]


def projection_matrix(fov_deg, aspect, near, far):
    t = 1 / math.tan(math.radians(fov_deg) / 2)
    return [[t / aspect, 0, 0, 0], [0, t, 0, 0],
            [0, 0, (far + near) / (near - far), -1], [0, 0, 2 * far * near / (near - far), 0]]


def normal_of(verts, f):
    p0, p1, p2 = verts[f[0]], verts[f[1]], verts[f[2]]
    return normalize(cross(sub(p1, p0), sub(p2, p0)))



def make_sphere(n_lat=12, n_lon=20):
    verts = [(0.0, 1.0, 0.0)]
    for i in range(1, n_lat):
        th = math.pi * i / n_lat
        for j in range(n_lon):
            ph = 2 * math.pi * j / n_lon
            verts.append((math.sin(th) * math.cos(ph), math.cos(th), math.sin(th) * math.sin(ph)))
    verts.append((0.0, -1.0, 0.0))
    ring = lambda i, j: 1 + (i - 1) * n_lon + j % n_lon
    fcs = [[0, ring(1, j), ring(1, j + 1)] for j in range(n_lon)]
    for i in range(1, n_lat - 1):
        for j in range(n_lon):
            fcs.append([ring(i, j), ring(i + 1, j), ring(i + 1, j + 1), ring(i, j + 1)])
    fcs += [[len(verts) - 1, ring(n_lat - 1, j + 1), ring(n_lat - 1, j)] for j in range(n_lon)]
    return verts, fcs


def load_obj(path):
    verts, norms, fcs, fnorms = [], [], [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "v":
                verts.append(tuple(map(float, t[1:4])))
            elif t[0] == "vn":
                norms.append(normalize(tuple(map(float, t[1:4]))))
            elif t[0] == "f":
                idx, nid = [], []
                for s in t[1:]:
                    parts = s.split("/")
                    idx.append(int(parts[0]) - 1)
                    if len(parts) == 3 and parts[2]:
                        nid.append(int(parts[2]) - 1)
                fcs.append(idx)
                fnorms.append(nid)
    if not verts or not fcs or any(not 0 <= i < len(verts) for f in fcs for i in f):
        raise ValueError("Некорректный OBJ-файл")
    normals = None
    if norms and all(len(n) == len(f) for n, f in zip(fnorms, fcs)):
        if any(not 0 <= i < len(norms) for n in fnorms for i in n):
            raise ValueError("Некорректные номера нормалей в OBJ")
        normals = [[norms[i] for i in n] for n in fnorms]       # нормали взяты из файла
    return verts, fcs, normals


def set_model(verts, fcs, normals=None):
    global base_verts, base_faces, base_normals, M
    n = len(verts)
    c = tuple(sum(v[i] for v in verts) / n for i in range(3))
    r = max(math.sqrt(sum((v[i] - c[i]) ** 2 for i in range(3))) for v in verts)
    k = RADIUS / r
    base_verts = [tuple((v[i] - c[i]) * k for i in range(3)) for v in verts]
    base_faces = [list(f) for f in fcs]
    base_normals = [list(cn) for cn in normals] if normals else None

    for fi, f in enumerate(base_faces):
        if base_normals:
            ref = tuple(sum(cn[i] for cn in base_normals[fi]) for i in range(3))   # нормаль из файла
        else:
            ref = tuple(sum(base_verts[v][i] for v in f) / len(f) for i in range(3))  # от центра к грани
        if dot(normal_of(base_verts, f), ref) < 0:
            f.reverse()
            if base_normals:
                base_normals[fi].reverse()
    M = task2.identity()
    rebuild()
    draw()


def rebuild():
    global world, faces, face_n, corner_n
    if not base_verts:
        return
    nm, det = normal_matrix(M)
    flip = det < 0
    world = [mul_point(v, M) for v in base_verts]
    faces = [f[::-1] if flip else f for f in base_faces]
    face_n = [normal_of(world, f) for f in faces]
    if base_normals:
        corner_n = [[normalize(tuple(sum(n[i] * nm[i][j] for i in range(3)) for j in range(3)))
                     for n in (cn[::-1] if flip else cn)] for cn in base_normals]
    else:
        cos_limit = math.cos(math.radians(crease_var.get())) - 1e-9
        adjacent = [[] for _ in world]
        for fi, f in enumerate(faces):
            for v in f:
                adjacent[v].append(fi)
        corner_n = []
        for fi, f in enumerate(faces):
            row = []
            for v in f:
                s = [0.0, 0.0, 0.0]
                for g in adjacent[v]:
                    if dot(face_n[g], face_n[fi]) >= cos_limit:
                        s = [s[0] + face_n[g][0], s[1] + face_n[g][1], s[2] + face_n[g][2]]
                row.append(normalize(s))
            corner_n.append(row)


def apply_matrix(t):
    global M
    if not base_verts:
        raise ValueError("Сначала выберите или загрузите модель")
    old = M
    M = task2.mat_mul(M, t)
    try:
        rebuild()
    except ValueError:
        M = old
        rebuild()
        raise
    draw()


def world_center():
    n = len(world)
    return tuple(sum(p[i] for p in world) / n for i in range(3))



def lambert(p, n, light, ambient):
    s = normalize(sub(light, p))
    k = min(1.0, ambient + max(0.0, dot(n, s)))
    return tuple(obj_rgb[i] * light_rgb[i] / 255 * k for i in range(3))


def fill_triangle(rows, w, h, a, b, c):
    ys = (a[1], b[1], c[1])
    for y in range(max(0, math.ceil(min(ys) - 0.5)), min(h - 1, math.ceil(max(ys) - 0.5) - 1) + 1):
        yc = y + 0.5
        hits = []
        for p, q in ((a, b), (b, c), (c, a)):
            if p[1] == q[1]:
                continue
            if p[1] > q[1]:
                p, q = q, p
            if p[1] <= yc < q[1]:
                t = (yc - p[1]) / (q[1] - p[1])
                hits.append((p[0] + t * (q[0] - p[0]),
                             p[2][0] + t * (q[2][0] - p[2][0]),
                             p[2][1] + t * (q[2][1] - p[2][1]),
                             p[2][2] + t * (q[2][2] - p[2][2])))
        if len(hits) < 2:
            continue
        hits.sort()
        (xl, rl, gl, bl), (xr, rr, gr, br) = hits[0], hits[-1]
        x0, x1 = max(0, math.ceil(xl - 0.5)), min(w - 1, math.ceil(xr - 0.5) - 1)
        if x1 < x0 or xr == xl:
            continue
        step = 1 / (xr - xl)
        dr, dg, db = (rr - rl) * step, (gr - gl) * step, (br - bl) * step
        off = x0 + 0.5 - xl
        r, g, bb = rl + dr * off, gl + dg * off, bl + db * off
        row = rows[y]
        for x in range(x0, x1 + 1):
            row[x] = "#" + HEX[int(r)] + HEX[int(g)] + HEX[int(bb)]
            r += dr
            g += dg
            bb += db


def render(w, h):
    rows = [[BACKGROUND] * w for _ in range(h)]
    if not world:
        return rows, 0
    az, el = math.radians(cam["az"]), math.radians(cam["el"])
    d = cam["dist"]
    pos = (d * math.cos(el) * math.sin(az), d * math.sin(el), d * math.cos(el) * math.cos(az))
    matrix = task2.mat_mul(view_matrix(pos, sub((0, 0, 0), pos)),
                           projection_matrix(60, w / h, 0.1, 100))
    light = (lx.get(), ly.get(), lz.get())
    ambient = ambient_var.get()

    screen = []
    for p in world:
        x, y, z, wv = (p[0] * matrix[0][j] + p[1] * matrix[1][j] + p[2] * matrix[2][j] + matrix[3][j]
                       for j in range(4))
        screen.append(((x / wv + 1) / 2 * w, (1 - y / wv) / 2 * h, wv) if wv > 0.1 else None)

    visible = []
    for fi, f in enumerate(faces):
        if dot(face_n[fi], sub(pos, world[f[0]])) <= 0 or any(screen[v] is None for v in f):
            continue
        visible.append((sum(screen[v][2] for v in f) / len(f), fi))
    visible.sort(reverse=True)

    for _, fi in visible:
        f = faces[fi]
        pts = []
        for k, v in enumerate(f):
            pts.append((screen[v][0], screen[v][1], lambert(world[v], corner_n[fi][k], light, ambient)))
        for k in range(1, len(f) - 1):
            fill_triangle(rows, w, h, pts[0], pts[k], pts[k + 1])
    return rows, len(visible), pos, matrix, light


def draw(_=None):
    global image
    canvas.delete("all")
    w, h = max(canvas.winfo_width(), 2), max(canvas.winfo_height(), 2)
    result = render(w, h)
    rows = result[0]
    image = tk.PhotoImage(width=w, height=h)
    image.put(" ".join("{" + " ".join(r) + "}" for r in rows))
    canvas.create_image(0, 0, anchor="nw", image=image)
    if world:
        matrix, light = result[3], result[4]
        x, y, z, wv = (light[0] * matrix[0][j] + light[1] * matrix[1][j] + light[2] * matrix[2][j] + matrix[3][j]
                       for j in range(4))
        if wv > 0.1:
            sx, sy = (x / wv + 1) / 2 * w, (1 - y / wv) / 2 * h
            canvas.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill="#ffd400", outline="white")
        canvas.create_text(10, 10, anchor="nw", fill="white",
                           text=f"граней: {len(faces)}, видимых (после отсечения нелицевых): {result[1]}")


def schedule(_=None):
    global job
    if job:
        window.after_cancel(job)
    job = window.after(20, draw)



def safe(fn):
    def wrapper():
        try:
            fn()
        except (ValueError, OSError) as e:
            messagebox.showerror("Ошибка", str(e))
    return wrapper


def numbers(entry_list):
    try:
        return [float(e.get().replace(",", ".")) for e in entry_list]
    except ValueError:
        raise ValueError("Введите числа")


def choose_figure(_=None):
    name = figure_box.get()
    if name == "Шар":
        set_model(*make_sphere())
    else:
        fig = POLYHEDRONS[name]()
        set_model([(p.x, p.y, p.z) for p in fig.vertices], [list(f.indices) for f in fig.faces])


def on_load():
    path = filedialog.askopenfilename(filetypes=[("OBJ", "*.obj")])
    if path:
        set_model(*load_obj(path))
        figure_box.set("")


def choose_color(which):
    global obj_rgb, light_rgb
    rgb, _ = colorchooser.askcolor(color="#%02x%02x%02x" % (obj_rgb if which == "obj" else light_rgb))
    if rgb:
        rgb = tuple(int(v) for v in rgb)
        if which == "obj":
            obj_rgb = rgb
            obj_swatch.config(bg="#%02x%02x%02x" % rgb)
        else:
            light_rgb = rgb
            light_swatch.config(bg="#%02x%02x%02x" % rgb)
        schedule()


def on_crease(_=None):
    rebuild()
    schedule()


def on_reset():
    global M
    M = task2.identity()
    rebuild()
    draw()


def on_press(e):
    global drag
    drag = (e.x, e.y)


def on_drag(e):
    global drag
    if drag:
        cam["az"] -= (e.x - drag[0]) * 0.5
        cam["el"] = max(-89, min(89, cam["el"] + (e.y - drag[1]) * 0.5))
        drag = (e.x, e.y)
        schedule()


def on_wheel(k):
    cam["dist"] = max(2.5, min(30, cam["dist"] * k))
    schedule()



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


def slider(parent, text, var, low, high, resolution, command):
    s = tk.Scale(parent, label=text, variable=var, from_=low, to=high, resolution=resolution,
                 orient="horizontal", command=command)
    s.pack(fill="x")
    return s


window = tk.Tk()
window.title("Лаба 9. Освещение: Ламберт + Гуро")
window.geometry("1150x720")
left = ttk.Frame(window, padding=8)
left.pack(side="left", fill="y")
canvas = tk.Canvas(window, width=700, height=600, bg=BACKGROUND, highlightthickness=0)
canvas.pack(side="right", fill="both", expand=True)

crease_var = tk.DoubleVar(value=50)
ambient_var = tk.DoubleVar(value=0.15)
lx, ly, lz = tk.DoubleVar(value=2.7), tk.DoubleVar(value=2.2), tk.DoubleVar(value=1.3)

tabs = ttk.Notebook(left)
tabs.pack(fill="both", expand=True)
tab_object = ttk.Frame(tabs, padding=6)
tab_light = ttk.Frame(tabs, padding=6)
tab_move = ttk.Frame(tabs, padding=6)
tab_line = ttk.Frame(tabs, padding=6)
tabs.add(tab_object, text="Объект")
tabs.add(tab_light, text="Свет")
tabs.add(tab_move, text="Преобразования")
tabs.add(tab_line, text="Прямая")
button(left, "Сбросить преобразования", on_reset)

# вкладка "Объект"
ttk.Label(tab_object, text="Фигура").pack(anchor="w")
figure_box = combo(tab_object, ["Шар"] + list(POLYHEDRONS), "Шар", 28)
figure_box.bind("<<ComboboxSelected>>", choose_figure)
button(tab_object, "Загрузить OBJ...", on_load)
row = ttk.Frame(tab_object)
row.pack(fill="x", pady=4)
ttk.Button(row, text="Цвет объекта...", command=lambda: choose_color("obj")).pack(side="left")
obj_swatch = tk.Label(row, width=4, bg="#%02x%02x%02x" % obj_rgb)
obj_swatch.pack(side="left", padx=6)
slider(tab_object, "Сглаживание нормалей, °", crease_var, 0, 180, 1, on_crease)
slider(tab_object, "Фоновая подсветка", ambient_var, 0, 0.6, 0.01, schedule)

# вкладка "Свет"
ttk.Label(tab_light, text="Положение точечного источника света\n(жёлтый кружок на картинке; если его\nне видно, свет за камерой)").pack(anchor="w")
slider(tab_light, "X", lx, -10, 10, 0.1, schedule)
slider(tab_light, "Y", ly, -10, 10, 0.1, schedule)
slider(tab_light, "Z", lz, -10, 10, 0.1, schedule)
row = ttk.Frame(tab_light)
row.pack(fill="x", pady=6)
ttk.Button(row, text="Цвет света...", command=lambda: choose_color("light")).pack(side="left")
light_swatch = tk.Label(row, width=4, bg="#%02x%02x%02x" % light_rgb)
light_swatch.pack(side="left", padx=6)

box = group(tab_move, "Смещение")
shift = entries(box, ["dx", "dy", "dz"], [0.5, 0, 0])
button(box, "Применить", lambda: apply_matrix(task2.translation(*numbers(shift))))

box = group(tab_move, "Вращение через центр")
rot_axis = combo(box, ["x", "y", "z"], "y")
rot_angle = entries(box, ["Угол, °"], [30])
button(box, "Применить", lambda: apply_matrix(task2.rotation_about_center_axis(
    world_center(), rot_axis.get(), math.radians(numbers(rot_angle)[0]))))

box = group(tab_move, "Масштаб относительно центра")
scale_k = entries(box, ["kx", "ky", "kz"], [1.5, 1.5, 1.5])
button(box, "Применить", lambda: apply_matrix(task2.scaling_about_center(world_center(), *numbers(scale_k))))

box = group(tab_move, "Отражение относительно плоскости")
plane = combo(box, ["xy", "xz", "yz"], "xy")
button(box, "Применить", lambda: apply_matrix(task2.reflection(plane.get())))

box = group(tab_line, "Поворот вокруг прямой через две точки")
point1 = entries(box, ["x1", "y1", "z1"], [0, 0, 0])
point2 = entries(box, ["x2", "y2", "z2"], [1, 1, 0])
angle = entries(box, ["Угол, °"], [30])
button(box, "Применить", lambda: apply_matrix(task2.rotation_about_line(
    numbers(point1), numbers(point2), math.radians(numbers(angle)[0]))))

canvas.bind("<Configure>", schedule)
canvas.bind("<ButtonPress-1>", on_press)
canvas.bind("<B1-Motion>", on_drag)
canvas.bind("<MouseWheel>", lambda e: on_wheel(0.9 if e.delta > 0 else 1 / 0.9))
canvas.bind("<Button-4>", lambda e: on_wheel(0.9))
canvas.bind("<Button-5>", lambda e: on_wheel(1 / 0.9))

set_model(*make_sphere())
window.mainloop()