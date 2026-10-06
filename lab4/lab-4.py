import tkinter as tk
import math

root = tk.Tk()
root.title("Аффинные преобразования")

canvas = tk.Canvas(root, width=800, height=600, bg="white")
canvas.pack(side="left")

panel = tk.Frame(root)
panel.pack(side="right", padx=10, pady=10)

current = []
polygons = []
current_polygon = None
mode = "draw"


# ---------- МАТРИЦЫ ----------

def mul(A, B):
    result = []
    for i in range(len(A)):
        row = []
        for j in range(len(B[0])):
            value = 0
            for k in range(len(B)):
                value += A[i][k] * B[k][j]
            row.append(value)
        result.append(row)

    return result


def apply(M, p):
    r = mul(M, [[p[0]], [p[1]], [1]])
    return r[0][0], r[1][0]


def transform(M):
    global polygons
    if current_polygon is not None:
        polygons[current_polygon] = [apply(M, p) for p in polygons[current_polygon]]
        draw()


def T(x, y):
    return [[1, 0, x], 
            [0, 1, y], 
            [0, 0, 1]]


def R(a):
    a = math.radians(a)
    c, s = math.cos(a), math.sin(a)
    return [[c, -s, 0], 
            [s, c, 0], 
            [0, 0, 1]]


def S(x, y):
    return [[x, 0, 0], 
            [0, y, 0], 
            [0, 0, 1]]


def around(M, x, y):
    return mul(T(x, y), mul(M, T(-x, -y)))


# ---------- РИСОВАНИЕ ----------

def draw_polygon(p, close=True, current_polygon=False):
    color = "red" if current_polygon else "black"

    for x, y in p:
        canvas.create_oval(x-4, y-4, x+4, y+4, fill=color)

    if len(p) >= 2:
        n = len(p) if close else len(p)-1
        for i in range(n):
            x1, y1 = p[i]
            x2, y2 = p[(i+1) % len(p)]
            canvas.create_line(x1, y1, x2, y2, fill=color)


def draw():
    canvas.delete("all")

    for i, p in enumerate(polygons):
        draw_polygon(p, current_polygon=i == current_polygon)

    if current:
        draw_polygon(current, False)


def click(e):
    current.append((e.x, e.y))
    draw()


def finish():
    global current_polygon
    if current:
        polygons.append(current.copy())
        current.clear()
        current_polygon = len(polygons) - 1
        draw()


def clear():
    global current_polygon, edge1, edge2_start, ref_edge
    polygons.clear()
    current.clear()
    current_polygon = None
    edge1 = None
    edge2_start = None
    ref_edge = None
    draw()


# ---------- ОБЩЕЕ ОКНО ----------

def window(title, fields, action):
    w = tk.Toplevel(root)
    w.title(title)

    entries = []

    for i, name in enumerate(fields):
        tk.Label(w, text=name).grid(row=i, column=0, padx=5, pady=5)
        e = tk.Entry(w)
        e.grid(row=i, column=1, padx=5, pady=5)
        entries.append(e)

    def ok():
        try:
            values = [float(e.get()) for e in entries]
            action(values)
            w.destroy()
        except ValueError:
            pass

    tk.Button(w, text="Применить", command=ok).grid(
        row=len(fields), columnspan=2, pady=10
    )


# ---------- ПРЕОБРАЗОВАНИЯ ----------

def move():
    window("Смещение", ["dx", "dy"],
           lambda v: transform(T(v[0], v[1])))


def rotate_point():
    window("Поворот вокруг точки", ["Угол", "X точки", "Y точки"],
           lambda v: transform(around(R(v[0]), v[1], v[2])))


def rotate_center():
    if current_polygon is None:
        return

    def action(v):
        p = polygons[current_polygon]
        x = sum(a for a, b in p) / len(p)
        y = sum(b for a, b in p) / len(p)
        transform(around(R(v[0]), x, y))

    window("Поворот вокруг центра", ["Угол"], action)


def scale_point():
    window("Масштабирование вокруг точки",
           ["Коэффициент X", "Коэффициент Y", "X точки", "Y точки"],
           lambda v: transform(around(S(v[0], v[1]), v[2], v[3])))


def scale_center():
    if current_polygon is None:
        return

    def action(v):
        p = polygons[current_polygon]
        x = sum(a for a, b in p) / len(p)
        y = sum(b for a, b in p) / len(p)
        transform(around(S(v[0], v[1]), x, y))

    window("Масштабирование вокруг центра",
           ["Коэффициент X", "Коэффициент Y"], action)


# ---------- ГЕОМЕТРИЧЕСКИЕ ПРОВЕРКИ ----------

edge1 = None
edge2_start = None
ref_edge = None


def seg_intersection(A, B, C, D):
    ax, ay = A; bx, by = B
    cx, cy = C; dx, dy = D

    rx, ry = bx - ax, by - ay
    sx, sy = dx - cx, dy - cy

    denom = rx * sy - ry * sx
    if abs(denom) < 1e-9:
        return None  # параллельны

    t = ((cx - ax) * sy - (cy - ay) * sx) / denom
    u = ((cx - ax) * ry - (cy - ay) * rx) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        return (ax + t * rx, ay + t * ry)
    return None


def point_in_polygon(P, poly):
    x, y = P
    inside = False
    n = len(poly)
    if n < 3:
        return False

    j = n - 1
    for i in range(n):
        xi, yi = poly[i]
        xj, yj = poly[j]
        if (yi > y) != (yj > y):
            x_cross = (xj - xi) * (y - yi) / (yj - yi) + xi
            if x < x_cross:
                inside = not inside
        j = i
    return inside


def side_of_edge(P, A, B):
    d = (B[0] - A[0]) * (P[1] - A[1]) - (B[1] - A[1]) * (P[0] - A[0])
    if abs(d) < 1e-9:
        return "on"
    return "left" if d > 0 else "right"


def spec_click(e):
    global edge1, edge2_start, ref_edge

    if mode == "intersect":
        if edge1 is None:
            if edge2_start is None:
                edge2_start = (e.x, e.y)
            else:
                edge1 = (edge2_start, (e.x, e.y))
                edge2_start = None
                draw()
                canvas.create_line(edge1[0][0], edge1[0][1],
                                   edge1[1][0], edge1[1][1], fill="blue", width=2)
        else:
            if edge2_start is None:
                edge2_start = (e.x, e.y)
            else:
                edge2 = (edge2_start, (e.x, e.y))
                edge2_start = None
                draw()
                canvas.create_line(edge1[0][0], edge1[0][1],
                                   edge1[1][0], edge1[1][1], fill="blue", width=2)
                canvas.create_line(edge2[0][0], edge2[0][1],
                                   edge2[1][0], edge2[1][1], fill="green", width=2)
                pt = seg_intersection(edge1[0], edge1[1], edge2[0], edge2[1])
                if pt:
                    canvas.create_oval(pt[0] - 6, pt[1] - 6,
                                       pt[0] + 6, pt[1] + 6,
                                       outline="red", width=3)
                    canvas.create_text(pt[0] + 10, pt[1] + 10,
                                       text=f"({pt[0]:.0f},{pt[1]:.0f})",
                                       fill="red", anchor="nw")
                else:
                    canvas.create_text(e.x + 10, e.y + 10,
                                       text="нет пересечения",
                                       fill="gray", anchor="nw")
        return

    if mode == "poly":
        if current_polygon is None:
            return
        draw()
        inside = point_in_polygon((e.x, e.y), polygons[current_polygon])
        color = "green" if inside else "orange"
        canvas.create_oval(e.x - 5, e.y - 5, e.x + 5, e.y + 5,
                           outline=color, width=2)
        canvas.create_text(e.x + 10, e.y - 10,
                           text="ВНУТРИ" if inside else "СНАРУЖИ",
                           fill=color, anchor="w")
        return

    if mode == "edge":
        if ref_edge is None:
            if edge2_start is None:
                edge2_start = (e.x, e.y)
            else:
                ref_edge = (edge2_start, (e.x, e.y))
                edge2_start = None
                draw()
                canvas.create_line(ref_edge[0][0], ref_edge[0][1],
                                   ref_edge[1][0], ref_edge[1][1],
                                   fill="purple", width=2)
        else:
            draw()
            canvas.create_line(ref_edge[0][0], ref_edge[0][1],
                               ref_edge[1][0], ref_edge[1][1],
                               fill="purple", width=2)
            res = side_of_edge((e.x, e.y), ref_edge[0], ref_edge[1])
            text = {"left": "СЛЕВА", "right": "СПРАВА", "on": "НА ПРЯМОЙ"}[res]
            canvas.create_oval(e.x - 5, e.y - 5, e.x + 5, e.y + 5,
                               outline="purple", width=2)
            canvas.create_text(e.x + 10, e.y - 10, text=text,
                               fill="purple", anchor="w")
        return


def set_mode(new_mode):
    global mode, edge1, edge2_start, ref_edge
    mode = new_mode
    edge1 = None
    edge2_start = None
    ref_edge = None
    draw()


# ---------- КНОПКИ ----------

tk.Label(panel, text="Полигоны",
         font=("Arial", 12, "bold")).pack(pady=5)

tk.Button(panel, text="Завершить полигон",
          command=finish, width=25).pack(pady=3)

tk.Button(panel, text="Очистить сцену",
          command=clear, width=25).pack(pady=3)

tk.Label(panel, text="Преобразования",
         font=("Arial", 12, "bold")).pack(pady=15)

buttons = [
    ("Смещение", move),
    ("Поворот вокруг точки", rotate_point),
    ("Поворот вокруг центра", rotate_center),
    ("Масштабирование вокруг точки", scale_point),
    ("Масштабирование вокруг центра", scale_center)
]

for text, command in buttons:
    tk.Button(panel, text=text, command=command,
              width=25).pack(pady=3)

tk.Label(panel, text="Геометрические проверки",
         font=("Arial", 12, "bold")).pack(pady=10)

mode_var = tk.StringVar(value="draw")
modes = [
    ("Рисование", "draw"),
    ("Пересечение рёбер", "intersect"),
    ("Точка в полигоне", "poly"),
    ("Точка vs ребро", "edge"),
]
for text, value in modes:
    tk.Radiobutton(panel, text=text, variable=mode_var, value=value,
                   command=lambda v=value: set_mode(v)).pack(anchor="w")


# ---------- СОБЫТИЯ МЫШИ ----------

def dispatch_click(e):
    if mode == "draw":
        click(e)
    else:
        spec_click(e)


canvas.bind("<Button-1>", dispatch_click)

root.mainloop()