import math
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

EPS = 1e-9
model = {"v": [], "f": [], "e": [], "base_v": [], "base_f": []}
view = {"rx": 0.4, "ry": -0.6, "scale": 90.0, "drag": None}
ui = {}
DEFAULT_PROFILE = "0 -1\n1 -1\n1.5 0\n1 1\n0 1"



def rotate_point(p, axis, a):
    x, y, z = p
    c, s = math.cos(a), math.sin(a)
    if axis == "x":
        return (x, y * c - z * s, y * s + z * c)
    if axis == "y":
        return (x * c + z * s, y, -x * s + z * c)
    return (x * c - y * s, x * s + y * c, z)


def parse_profile(text, axis):
    pts = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            nums = [float(v) for v in line.replace(",", ".").split()]
        except ValueError:
            raise ValueError(f"Не удалось прочитать строку: '{line}'")
        if len(nums) == 3:
            pts.append(tuple(nums))
        elif len(nums) == 2:
            r, h = nums
            pts.append({"x": (h, r, 0.0), "y": (r, h, 0.0), "z": (r, 0.0, h)}[axis])
        else:
            raise ValueError(f"В строке '{line}' нужно 2 или 3 числа")
    return pts


def on_axis(p, axis):
    i = "xyz".index(axis)
    return math.sqrt(sum(p[j] ** 2 for j in range(3) if j != i)) < EPS


def build_revolution(profile, axis, n):
    if len(profile) < 2:
        raise ValueError("В образующей должно быть минимум 2 точки")
    if n < 3:
        raise ValueError("Разбиений должно быть не меньше 3")

    step = math.radians(360.0 / n)
    verts, table = [], []
    for p in profile:
        if on_axis(p, axis):
            verts.append(tuple(p))
            table.append([len(verts) - 1] * n)
        else:
            row = []
            for k in range(n):
                row.append(len(verts))
                verts.append(rotate_point(p, axis, step * k))
            table.append(row)

    faces = []
    for k in range(n):
        k2 = (k + 1) % n
        for i in range(len(profile) - 1):
            quad = [table[i][k], table[i + 1][k], table[i + 1][k2], table[i][k2]]
            face = [v for j, v in enumerate(quad) if v != quad[j - 1]]
            if len(face) >= 3:
                faces.append(face)

    c = center(verts)
    s = 0.0
    for f in faces:
        nrm = normal(verts, f)
        p = verts[f[0]]
        s += sum(nrm[i] * (p[i] - c[i]) for i in range(3))
    if s < 0:
        faces = [f[::-1] for f in faces]
    return verts, faces


def normal(verts, face):
    p0, p1, p2 = verts[face[0]], verts[face[1]], verts[face[2]]
    u = [p1[i] - p0[i] for i in range(3)]
    w = [p2[i] - p0[i] for i in range(3)]
    return (u[1] * w[2] - u[2] * w[1], u[2] * w[0] - u[0] * w[2], u[0] * w[1] - u[1] * w[0])


def center(verts):
    n = len(verts)
    return tuple(sum(p[i] for p in verts) / n for i in range(3))


def edges_of(faces):
    es = set()
    for f in faces:
        for i in range(len(f)):
            a, b = f[i], f[(i + 1) % len(f)]
            es.add((min(a, b), max(a, b)))
    return list(es)



def save_obj(path, verts, faces):
    with open(path, "w", encoding="utf-8") as f:
        for x, y, z in verts:
            f.write(f"v {x:.6f} {y:.6f} {z:.6f}\n")
        for face in faces:
            f.write("f " + " ".join(str(i + 1) for i in face) + "\n")


def load_obj(path):
    verts, faces = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            t = line.split()
            if not t:
                continue
            if t[0] == "v":
                verts.append(tuple(map(float, t[1:4])))
            elif t[0] == "f":
                faces.append([int(s.split("/")[0]) - 1 for s in t[1:]])
    if not verts or not faces:
        raise ValueError("В файле нет вершин или граней")
    return verts, faces



def move(dx, dy, dz):
    model["v"] = [(x + dx, y + dy, z + dz) for x, y, z in model["v"]]


def rotate_about_center(axis, deg):
    cx, cy, cz = center(model["v"])
    a = math.radians(deg)
    out = []
    for x, y, z in model["v"]:
        rx, ry, rz = rotate_point((x - cx, y - cy, z - cz), axis, a)
        out.append((rx + cx, ry + cy, rz + cz))
    model["v"] = out


def scale_about_center(k):
    cx, cy, cz = center(model["v"])
    model["v"] = [(cx + (x - cx) * k, cy + (y - cy) * k, cz + (z - cz) * k)
                  for x, y, z in model["v"]]


def reflect(plane):
    i = {"yz": 0, "xz": 1, "xy": 2}[plane]
    model["v"] = [tuple(-p[j] if j == i else p[j] for j in range(3)) for p in model["v"]]
    model["f"] = [f[::-1] for f in model["f"]]



def project(x, y, z):
    cy, sy = math.cos(view["ry"]), math.sin(view["ry"])
    cx, sx = math.cos(view["rx"]), math.sin(view["rx"])
    x, z = x * cy + z * sy, -x * sy + z * cy
    y, z = y * cx - z * sx, y * sx + z * cx
    k = view["scale"]
    x, y, z = x * k, y * k, z * k
    f = 1000 / max(1000 - z, 100)
    c = ui["canvas"]
    return c.winfo_width() / 2 + x * f, c.winfo_height() / 2 - y * f


def draw(_=None):
    c = ui["canvas"]
    c.delete("all")
    L = 150 / view["scale"]
    x0, y0 = project(0, 0, 0)
    for vec, color, name in (((L, 0, 0), "red", "X"), ((0, L, 0), "green", "Y"),
                             ((0, 0, L), "blue", "Z")):
        x1, y1 = project(*vec)
        c.create_line(x0, y0, x1, y1, fill=color, width=2, arrow="last")
        c.create_text(x1 + 8, y1 - 8, text=name, fill=color)
    if model["v"]:
        pts = [project(*p) for p in model["v"]]
        for a, b in model["e"]:
            c.create_line(*pts[a], *pts[b], fill="#333")
        c.create_text(10, 10, anchor="nw",
                      text=f"вершин: {len(model['v'])}, рёбер: {len(model['e'])}, "
                           f"граней: {len(model['f'])}")


def set_model(verts, faces):
    model.update(v=verts, f=faces, e=edges_of(faces), base_v=verts, base_f=faces)
    r = max(math.sqrt(x * x + y * y + z * z) for x, y, z in verts)
    view["scale"] = 200 / max(r, 1e-6)
    draw()



def num(entry):
    try:
        return float(entry.get().replace(",", "."))
    except ValueError:
        raise ValueError(f"'{entry.get()}' - не число")


def safe(fn):
    """Оборачивает действие: ошибки показываются окном, а не падением программы."""
    def wrapper():
        try:
            fn()
        except (ValueError, OSError) as e:
            messagebox.showerror("Ошибка", str(e))
    return wrapper


def need_model():
    if not model["v"]:
        raise ValueError("Сначала постройте или загрузите модель")


def on_build():
    axis = ui["axis"].get()
    profile = parse_profile(ui["profile"].get("1.0", "end"), axis)
    set_model(*build_revolution(profile, axis, int(num(ui["n"]))))


def on_save():
    need_model()
    path = filedialog.asksaveasfilename(defaultextension=".obj", filetypes=[("OBJ", "*.obj")])
    if path:
        save_obj(path, model["v"], model["f"])


def on_load():
    path = filedialog.askopenfilename(filetypes=[("OBJ", "*.obj")])
    if path:
        set_model(*load_obj(path))


def on_move():
    need_model()
    move(*[num(e) for e in ui["mv"]])
    draw()


def on_rotate():
    need_model()
    rotate_about_center(ui["rot_axis"].get(), num(ui["rot_angle"]))
    draw()


def on_scale():
    need_model()
    scale_about_center(num(ui["k"]))
    draw()


def on_reflect():
    need_model()
    reflect(ui["plane"].get())
    draw()


def on_reset():
    if model["base_v"]:
        model.update(v=model["base_v"], f=model["base_f"])
        draw()


def on_press(e):
    view["drag"] = (e.x, e.y)


def on_drag(e):
    if view["drag"]:
        view["ry"] += (e.x - view["drag"][0]) * 0.01
        view["rx"] += (e.y - view["drag"][1]) * 0.01
        view["drag"] = (e.x, e.y)
        draw()


def zoom(k):
    view["scale"] *= k
    draw()



def field(parent, value, width=5):
    e = ttk.Entry(parent, width=width)
    e.insert(0, value)
    e.pack(side="left", padx=2)
    return e


def combo(parent, values, default, width):
    cb = ttk.Combobox(parent, values=values, width=width, state="readonly")
    cb.set(default)
    cb.pack(side="left", padx=2)
    return cb


def button(parent, text, cmd):
    ttk.Button(parent, text=text, command=safe(cmd)).pack(fill="x", pady=2)


root = tk.Tk()
root.title("Фигура вращения")
left = ttk.Frame(root, padding=8)
left.pack(side="left", fill="y")
c = tk.Canvas(root, width=700, height=600, bg="white")
c.pack(side="right", fill="both", expand=True)
ui["canvas"] = c

ttk.Label(left, text="Образующая (точка в строке):").pack(anchor="w")
ttk.Label(left, foreground="gray",
            text="2 числа: расстояние от оси, высота\n3 числа: x y z").pack(anchor="w")
ui["profile"] = tk.Text(left, width=24, height=7)
ui["profile"].insert("1.0", DEFAULT_PROFILE)
ui["profile"].pack(pady=4)

r = ttk.Frame(left)
r.pack(fill="x")
ttk.Label(r, text="Ось:").pack(side="left")
ui["axis"] = combo(r, ["x", "y", "z"], "y", 3)
ttk.Label(r, text="Разбиений:").pack(side="left")
ui["n"] = field(r, "24")

button(left, "Построить", on_build)
button(left, "Сохранить в .obj", on_save)
button(left, "Загрузить из .obj", on_load)

box = ttk.LabelFrame(left, text="Аффинные преобразования", padding=6)
box.pack(fill="x", pady=8)

f = ttk.Frame(box); f.pack(fill="x")
ttk.Label(f, text="dx dy dz").pack(side="left")
ui["mv"] = [field(f, v) for v in ("0.5", "0", "0")]
button(box, "Сместить", on_move)

f = ttk.Frame(box); f.pack(fill="x")
ttk.Label(f, text="Ось, угол°").pack(side="left")
ui["rot_axis"] = combo(f, ["x", "y", "z"], "y", 3)
ui["rot_angle"] = field(f, "30")
button(box, "Повернуть вокруг оси через центр", on_rotate)

f = ttk.Frame(box); f.pack(fill="x")
ttk.Label(f, text="Коэффициент").pack(side="left")
ui["k"] = field(f, "1.5")
button(box, "Масштабировать от центра", on_scale)

f = ttk.Frame(box); f.pack(fill="x")
ttk.Label(f, text="Плоскость").pack(side="left")
ui["plane"] = combo(f, ["xy", "yz", "xz"], "xy", 4)
button(box, "Отразить", on_reflect)

button(box, "Сбросить к исходной", on_reset)

c.bind("<Configure>", draw)
c.bind("<ButtonPress-1>", on_press)
c.bind("<B1-Motion>", on_drag)
c.bind("<MouseWheel>", lambda e: zoom(1.1 if e.delta > 0 else 1 / 1.1))
c.bind("<Button-4>", lambda e: zoom(1.1))
c.bind("<Button-5>", lambda e: zoom(1 / 1.1))

safe(on_build)()
root.mainloop()