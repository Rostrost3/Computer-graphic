from PIL import Image
import math

width = int(input("Введите ширину изображения: ")) + 1
height = int(input("Введите высоту изображения: ")) + 1

image = Image.new("RGB", (width, height), "white")


def read_point(name):
    print(f"\nТочка {name}")
    x = int(input("  X: "))
    y = int(input("  Y: "))
    return (x, y)


def read_color(name):
    print(f"\nЦвет {name} (RGB, 0-255)")
    r = int(input("  R: "))
    g = int(input("  G: "))
    b = int(input("  B: "))
    return (r, g, b)


def put_pixel(x, y, color):
    if 0 <= x < width and 0 <= y < height:
        image.putpixel((x, y), color)


def blend_pixel(x, y, color, alpha):
    if not (0 <= x < width and 0 <= y < height):
        return
    bg = image.getpixel((x, y))
    r = round(color[0] * alpha + bg[0] * (1 - alpha))
    g = round(color[1] * alpha + bg[1] * (1 - alpha))
    b = round(color[2] * alpha + bg[2] * (1 - alpha))
    image.putpixel((x, y), (r, g, b))


def draw_line_bresenham(x0, y0, x1, y1, color):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x1 > x0 else (-1 if x1 < x0 else 0)
    sy = 1 if y1 > y0 else (-1 if y1 < y0 else 0)

    err = dx - dy

    while True:
        put_pixel(x0, y0, color)

        if x0 == x1 and y0 == y1:
            break

        e2 = 2 * err

        if e2 > -dy:
            err -= dy
            x0 += sx

        if e2 < dx:
            err += dx
            y0 += sy


def draw_line_wu(x0, y0, x1, y1, color):
    steep = abs(y1 - y0) > abs(x1 - x0)

    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0

    gradient = dy / dx if dx != 0 else 0

    # начальная дробная y
    y = y0

    for x in range(x0, x1 + 1):
        y_int = math.floor(y)
        frac = y - y_int

        if steep:
            blend_pixel(y_int,     x, color, 1 - frac)
            blend_pixel(y_int + 1, x, color, frac)
        else:
            blend_pixel(x, y_int,     color, 1 - frac)
            blend_pixel(x, y_int + 1, color, frac)

        y += gradient


P0 = read_point("P0 (начало)")
P1 = read_point("P1 (конец)")

if not all(0 <= x < width and 0 <= y < height for x, y in [P0, P1]):
    print("Ошибка: точки должны находиться внутри изображения")
    exit()

color = read_color("линии")

print("\nВыберите алгоритм:")
print("  1 — Брезенхем (целочисленный)")
print("  2 — Ву (сглаженный)")
choice = input("Ваш выбор: ").strip()

if choice == "1":
    draw_line_bresenham(P0[0], P0[1], P1[0], P1[1], color)
    filename = "line_bresenham.png"
elif choice == "2":
    draw_line_wu(P0[0], P0[1], P1[0], P1[1], color)
    filename = "line_wu.png"
else:
    print("Неверный выбор")
    exit()

image.save(filename)
print(f"Сохранено: {filename}")