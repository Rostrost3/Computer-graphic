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
    global current_polygon
    polygons.clear()
    current.clear()
    current_polygon = None
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


canvas.bind("<Button-1>", click)

root.mainloop()