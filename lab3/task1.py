import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk

W, H = 800, 600

root = tk.Tk()
root.title("лабораторная работа 3")

canvas = tk.Canvas(root, width=W, height=H, bg="white")
canvas.pack()

img = Image.new("RGB", (W, H), "white")
photo = ImageTk.PhotoImage(img)
canvas.create_image(0, 0, image=photo, anchor="nw")

BORDER = (0, 0, 0)
texture = None
texture_filled = set()


def update():
    global photo
    photo = ImageTk.PhotoImage(img)
    canvas.delete("image")
    canvas.create_image(0, 0, image=photo, anchor="nw", tags="image")


# Рисование линии алгоритмом Брезенхэма
def draw_line(x1, y1, x2, y2, color):
    dx = abs(x2 - x1)
    dy = abs(y2 - y1)
    sx = 1 if x1 < x2 else -1
    sy = 1 if y1 < y2 else -1
    err = dx - dy

    while True:
        if 0 <= x1 < W and 0 <= y1 < H:
            img.putpixel((x1, y1), color)

        if x1 == x2 and y1 == y2:
            break

        e = 2 * err

        if e > -dy:
            err -= dy
            x1 += sx

        if e < dx:
            err += dx
            y1 += sy


# Рисование фигуры мышью
drawing = False
last = None


def mouse_down(event):
    global drawing, last
    drawing = True
    last = (event.x, event.y)


def mouse_move(event):
    global last
    if drawing:
        draw_line(last[0], last[1], event.x, event.y, BORDER)
        last = (event.x, event.y)
        update()


def mouse_up(event):
    global drawing, last
    drawing = False
    last = None


canvas.bind("<Button-1>", mouse_down)
canvas.bind("<B1-Motion>", mouse_move)
canvas.bind("<ButtonRelease-1>", mouse_up)


# 1а. Рекурсивная заливка цветом
def span_fill(x, y, new_color):
    if not (0 <= x < W and 0 <= y < H):
        return

    old_color = img.getpixel((x, y))

    if old_color != (255, 255, 255):
        return

    left = x
    while left >= 0 and img.getpixel((left, y)) == old_color:
        left -= 1
    left += 1

    right = x
    while right < W and img.getpixel((right, y)) == old_color:
        right += 1
    right -= 1

    for px in range(left, right + 1):
        img.putpixel((px, y), new_color)

    check_line(left, right, y - 1, old_color, new_color)
    check_line(left, right, y + 1, old_color, new_color)


def check_line(left, right, y, old_color, new_color):
    if y < 0 or y >= H:
        return

    x = left

    while x <= right:
        while x <= right and img.getpixel((x, y)) != old_color:
            x += 1

        if x > right:
            return

        start = x

        while x <= right and img.getpixel((x, y)) == old_color:
            x += 1

        middle = (start + x - 1) // 2
        span_fill(middle, y, new_color)
        x += 1


def start_color_fill():
    canvas.unbind("<Button-1>")
    canvas.bind("<Button-1>", color_click)


def color_click(event):
    canvas.unbind("<Button-1>")
    span_fill(event.x, event.y, (255, 100, 100))
    update()


# 1б. Загрузка текстуры
def load_texture():
    global texture

    filename = filedialog.askopenfilename(
        filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")]
    )

    if filename:
        texture = Image.open(filename).convert("RGB")
        print("Текстура загружена:", texture.size)


def texture_pixel(x, y):
    tx = x % texture.width
    ty = y % texture.height
    return texture.getpixel((tx, ty))


# 1б. Рекурсивная заливка текстурой
def texture_fill(x, y):
    if not (0 <= x < W and 0 <= y < H):
        return

    if (x, y) in texture_filled:
        return

    if img.getpixel((x, y)) != (255, 255, 255):
        return

    left = x
    while (left >= 0 and img.getpixel((left, y)) == (255, 255, 255)
           and (left, y) not in texture_filled):
        left -= 1
    left += 1

    right = x
    while (right < W and img.getpixel((right, y)) == (255, 255, 255)
           and (right, y) not in texture_filled):
        right += 1
    right -= 1

    for px in range(left, right + 1):
        if (px, y) not in texture_filled:
            img.putpixel((px, y), texture_pixel(px, y))
            texture_filled.add((px, y))

    texture_line(left, right, y - 1)
    texture_line(left, right, y + 1)


def texture_line(left, right, y):
    if y < 0 or y >= H:
        return

    x = left

    while x <= right:
        while x <= right and (
            img.getpixel((x, y)) != (255, 255, 255)
            or (x, y) in texture_filled
        ):
            x += 1

        if x > right:
            return

        start = x

        while x <= right and img.getpixel((x, y)) == (255, 255, 255) \
                and (x, y) not in texture_filled:
            x += 1

        middle = (start + x - 1) // 2
        texture_fill(middle, y)
        x += 1


def start_texture_fill():
    if texture is None:
        print("Сначала загрузите текстуру")
        return

    canvas.unbind("<Button-1>")
    canvas.bind("<Button-1>", texture_click)


def texture_click(event):
    global texture_filled

    canvas.unbind("<Button-1>")
    texture_filled = set()
    texture_fill(event.x, event.y)
    update()


# 1в. Выделение границы связной области

DIRS = [(1, 0), (1, -1), (0, -1), (-1, -1),
        (-1, 0), (-1, 1), (0, 1), (1, 1)]

boundary_points = []

def is_border(x, y):
    return 0 <= x < W and 0 <= y < H and img.getpixel((x, y)) == BORDER

def find_start():
    for x in range(W - 1, -1, -1):
        for y in range(H):
            if is_border(x, y):
                return x, y
    return None

def trace_boundary(start):
    points = [start]
    cur = start

    # Первое направление — вниз
    direction = 6

    first_move = None

    for _ in range(W * H * 8):
        # 90 градусов вправо от направления прихода
        right = (direction - 2) % 8

        found = None
        new_direction = None

        # От правого направления идём против часовой стрелки
        for k in range(8):
            d = (right + k) % 8

            nx = cur[0] + DIRS[d][0]
            ny = cur[1] + DIRS[d][1]

            if is_border(nx, ny):
                found = (nx, ny)
                new_direction = d
                break

        if found is None:
            break

        # Запоминаем первый переход
        if first_move is None:
            first_move = (found, new_direction)
        elif cur == start and (found, new_direction) == first_move:
            break

        points.append(found)
        cur = found
        direction = new_direction

    return points

def find_boundary():
    global boundary_points

    start = find_start()

    if start is None:
        print("Граница не найдена")
        return

    boundary_points = trace_boundary(start)

    print("Начальная точка:", start)
    print("Количество точек границы:", len(boundary_points))
    print(boundary_points)

    for x, y in boundary_points:
        img.putpixel((x, y), (0, 0, 255))

    update()




# Кнопки
buttons = tk.Frame(root)
buttons.pack(pady=5)

tk.Button(
    buttons, text="1а — Заливка цветом", command=start_color_fill
).pack(side="left", padx=5)

tk.Button(
    buttons, text="Загрузить текстуру", command=load_texture
).pack(side="left", padx=5)

tk.Button(
    buttons, text="1б — Заливка рисунком", command=start_texture_fill
).pack(side="left", padx=5)

tk.Button(
    buttons, text="1в — Найти границу", command=find_boundary
).pack(side="left", padx=5)

root.mainloop()