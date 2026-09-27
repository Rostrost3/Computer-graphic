from PIL import Image
import math

width = int(input("Введите ширину изображения: ")) + 1
height = int(input("Введите высоту изображения: ")) + 1

image = Image.new("RGB", (width, height), "white")

def distance(p1, p2):
    return math.sqrt((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1]) ** 2)

def read_point(name):
    print(f"\nВершина {name}")
    x = int(input("  X: "))
    y = int(input("  Y: "))
    return (x, y)


def read_color(name):
    print(f"\nЦвет вершины {name} (RGB, 0-255)")
    r = int(input("  R: "))
    g = int(input("  G: "))
    b = int(input("  B: "))
    return (r, g, b)

A = read_point("A")
B = read_point("B")
C = read_point("C")

if not all(0 <= x < width and 0 <= y < height for x, y in [A, B, C]):
    print("Ошибка: вершины должны находиться внутри изображения")
    exit()

ab = distance(A, B)
bc = distance(B, C)
ac = distance(A, C)

if ab + bc <= ac or ab + ac <= bc or ac + bc <= ab:
    print("Такие точки не образуют треугольник")
    exit()

color_a = read_color("A")
color_b = read_color("B")
color_c = read_color("C")

def get_x_on_line(p1, p2, y):
    x1, y1 = p1
    x2, y2 = p2

    if x1 == x2:
        return x1

    if y1 == y2:
        return None

    m = (y2 - y1) / (x2 - x1)

    return x1 + (y - y1) / m

def get_barycentric_coordinates(x, y, A, B, C):
    denominator = ((B[1] - C[1]) * (A[0] - C[0]) + (C[0] - B[0]) * (A[1] - C[1]))

    alpha = ((B[1] - C[1]) * (x - C[0]) + (C[0] - B[0]) * (y - C[1])) / denominator

    beta = ((C[1] - A[1]) * (x - C[0]) + (A[0] - C[0]) * (y - C[1])) / denominator

    gamma = 1 - alpha - beta

    return alpha, beta, gamma

for y in range(height):

    intersections = []

    if min(A[1], B[1]) <= y <= max(A[1], B[1]):
        x = get_x_on_line(A, B, y)
        if x is not None:
            intersections.append(x)

    if min(B[1], C[1]) <= y <= max(B[1], C[1]):
        x = get_x_on_line(B, C, y)
        if x is not None:
            intersections.append(x)

    if min(A[1], C[1]) <= y <= max(A[1], C[1]):
        x = get_x_on_line(A, C, y)
        if x is not None:
            intersections.append(x)

    if len(intersections) >= 2:
        left_x = round(min(intersections))
        right_x = round(max(intersections))

        for x in range(left_x, right_x + 1):
            alpha, beta, gamma = get_barycentric_coordinates(x, y, A, B, C)

            r = alpha * color_a[0] + beta * color_b[0] + gamma * color_c[0]
            g = alpha * color_a[1] + beta * color_b[1] + gamma * color_c[1]
            b = alpha * color_a[2] + beta * color_b[2] + gamma * color_c[2]

            image.putpixel((x, y), (round(r), round(g), round(b)))


image.save("lab3/triangle.png")