import tkinter as tk


points = [(100, 300), (300, 150), (500, 400), (700, 200), (800, 350)]
dragging = None
RADIUS = 6
STEPS = 50


# Геометрия
def tangent(i):
    n = len(points)
    if n < 2:
        return (0, 0)
    if i == 0:
        return (points[1][0] - points[0][0], points[1][1] - points[0][1])
    if i == n - 1:
        return (points[-1][0] - points[-2][0], points[-1][1] - points[-2][1])
    return ((points[i+1][0] - points[i-1][0]) / 2,
            (points[i+1][1] - points[i-1][1]) / 2)


def control_points(i):
    P0 = points[i]
    P3 = points[i+1]
    T0 = tangent(i)
    T3 = tangent(i+1)
    C1 = (P0[0] + T0[0]/3, P0[1] + T0[1]/3)
    C2 = (P3[0] - T3[0]/3, P3[1] - T3[1]/3)
    return P0, C1, C2, P3


def bezier_point(P0, P1, P2, P3, t):
    mt = 1 - t
    x = mt**3*P0[0] + 3*mt**2*t*P1[0] + 3*mt*t**2*P2[0] + t**3*P3[0]
    y = mt**3*P0[1] + 3*mt**2*t*P1[1] + 3*mt*t**2*P2[1] + t**3*P3[1]
    return x, y


# Отрисовка
def redraw(canvas):
    canvas.delete("all")
    for i in range(len(points) - 1):
        P0, C1, C2, P3 = control_points(i)
        canvas.create_line(*P0, *C1, fill="#cccccc", dash=(3,3))
        canvas.create_line(*C2, *P3, fill="#cccccc", dash=(3,3))
        canvas.create_line(*C1, *C2, fill="#dddddd", dash=(2,4))
        prev = P0
        for k in range(1, STEPS + 1):
            t = k / STEPS
            pt = bezier_point(P0, C1, C2, P3, t)
            canvas.create_line(prev[0], prev[1], pt[0], pt[1],
                               fill="blue", width=2)
            prev = pt
    for i, (x, y) in enumerate(points):
        color = "red" if i == dragging else "black"
        canvas.create_oval(x-RADIUS, y-RADIUS, x+RADIUS, y+RADIUS,
                           fill=color, outline="black")


# События мыши
def hit_test(x, y):
    for i, (px, py) in enumerate(points):
        if (px-x)**2 + (py-y)**2 <= (RADIUS+3)**2:
            return i
    return None


def on_left_click(event, canvas):
    global dragging
    i = hit_test(event.x, event.y)
    if i is not None:
        dragging = i
    else:
        points.append((event.x, event.y))
    redraw(canvas)


def on_drag(event, canvas):
    if dragging is not None:
        points[dragging] = (event.x, event.y)
        redraw(canvas)


def on_release(event, canvas):
    global dragging
    dragging = None
    redraw(canvas)


def on_right_click(event, canvas):
    i = hit_test(event.x, event.y)
    if i is not None:
        points.pop(i)
        redraw(canvas)


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Составная кубическая кривая Безье")
    canvas = tk.Canvas(root, width=900, height=600, bg="white")
    canvas.pack()

    canvas.bind("<Button-1>", lambda e: on_left_click(e, canvas))
    canvas.bind("<B1-Motion>", lambda e: on_drag(e, canvas))
    canvas.bind("<ButtonRelease-1>", lambda e: on_release(e, canvas))
    canvas.bind("<Button-3>", lambda e: on_right_click(e, canvas))

    redraw(canvas)
    root.mainloop()