import tkinter as tk

EPS = 1e-9

def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])


def area(P):
    s = 0
    for i in range(len(P)):
        x1, y1 = P[i]
        x2, y2 = P[(i + 1) % len(P)]
        s += x1 * y2 - x2 * y1
    return s / 2


def ccw(P):
    if area(P) > 0:
        return list(P)
    return P[::-1]


def crosses(a, b, c, d):
    ab_c = cross(a, b, c)
    ab_d = cross(a, b, d)
    cd_a = cross(c, d, a)
    cd_b = cross(c, d, b)

    first = (ab_c > EPS and ab_d < -EPS) or (ab_c < -EPS and ab_d > EPS)
    second = (cd_a > EPS and cd_b < -EPS) or (cd_a < -EPS and cd_b > EPS)

    return first and second


def on_segment(a, b, p):
    return (min(a[0], b[0]) - EPS <= p[0] <= max(a[0], b[0]) + EPS and
            min(a[1], b[1]) - EPS <= p[1] <= max(a[1], b[1]) + EPS)


def inside(P, p):
    result = False
    for i in range(len(P)):
        a = P[i]
        b = P[(i + 1) % len(P)]
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if x > p[0]:
                result = not result
    return result


def diagonal_ok(P, i, j):
    n = len(P)
    if i == j or (i + 1) % n == j or (j + 1) % n == i:
        return False

    a = P[i]
    b = P[j]

    for k in range(n):
        if k in (i, j):
            continue

        if abs(cross(a, b, P[k])) <= EPS and on_segment(a, b, P[k]):
            return False

        k2 = (k + 1) % n
        if k2 not in (i, j) and crosses(a, b, P[k], P[k2]):
            return False

    middle = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return inside(P, middle)


def side_x(P, i, step):
    k = (i + step) % len(P)
    while abs(P[k][0] - P[i][0]) <= EPS and k != i:
        k = (k + step) % len(P)
    return P[k][0]


def bend_type(P, i):
    if cross(P[i - 1], P[i], P[(i + 1) % len(P)]) >= -EPS:
        return None

    x = P[i][0]
    prev_x = side_x(P, i, -1)
    next_x = side_x(P, i, 1)

    if prev_x > x and next_x > x:
        return 'left'
    if prev_x < x and next_x < x:
        return 'right'
    return None


def find_bend(P, kind):
    order = sorted(range(len(P)), key=lambda k: P[k])
    if kind == 'right':
        order.reverse()

    for k in order:
        if bend_type(P, k) == kind:
            return k
    return None


def is_monotone(P):
    n = len(P)
    left = min(range(n), key=lambda k: P[k])
    right = max(range(n), key=lambda k: P[k])

    for step in (1, -1):
        k = left
        while k != right:
            nxt = (k + step) % n
            if P[nxt][0] < P[k][0] - EPS:
                return False
            k = nxt
    return True


def find_partner(P, i, kind, strict=False):
    n = len(P)
    xi, yi = P[i]

    if kind == 'left':
        side = -1
    else:
        side = 1

    up = None
    down = None

    for k in range(n):
        k2 = (k + 1) % n
        a = P[k]
        b = P[k2]

        if i in (k, k2) or abs(a[0] - b[0]) < EPS:
            continue

        if min(a[0], b[0]) - EPS <= xi <= max(a[0], b[0]) + EPS:
            y = a[1] + (b[1] - a[1]) * (xi - a[0]) / (b[0] - a[0])
            if y > yi + EPS and (up is None or y < up[0]):
                up = (y, k)
            if y < yi - EPS and (down is None or y > down[0]):
                down = (y, k)

    candidates = set()
    for edge in (up, down):
        if edge is not None:
            candidates.add(edge[1])
            candidates.add((edge[1] + 1) % n)

    candidates = [k for k in candidates if k != i and (P[k][0] - xi) * side >= -EPS]
    candidates.sort(key=lambda k: (abs(P[k][0] - xi), abs(P[k][1] - yi)))

    for k in candidates:
        if diagonal_ok(P, i, k):
            return k

    if strict:
        return None

    others = [k for k in range(n) if k != i and (P[k][0] - xi) * side >= -EPS]
    others.sort(key=lambda k: (abs(P[k][0] - xi), abs(P[k][1] - yi)))

    for k in others:
        if diagonal_ok(P, i, k):
            return k
    return None


def split(P, i, j):
    if i > j:
        i, j = j, i
    return P[i:j + 1], P[j:] + P[:i + 1]


def make_monotone(polygon, strict=False):
    parts = []
    diagonals = []
    stack = [ccw(polygon)]

    while stack:
        P = stack.pop()

        kind = 'left'
        i = find_bend(P, kind)
        if i is None:
            kind = 'right'
            i = find_bend(P, kind)

        if i is None:
            parts.append(P)
            continue

        j = find_partner(P, i, kind, strict)
        if j is None:
            raise RuntimeError("Не нашли диагональ для " + str(P[i]))

        diagonals.append((P[i], P[j], kind))
        stack.extend(split(P, i, j))

    return parts, diagonals


def verify(polygon, parts, diagonals):
    errors = []
    P = ccw(polygon)

    for k, part in enumerate(parts, 1):
        if not is_monotone(part):
            errors.append("часть " + str(k) + " не монотонна")

    if abs(sum(area(p) for p in parts) - area(P)) > 1e-6 * max(1, area(P)):
        errors.append("сумма площадей частей не равна площади полигона")

    if len(parts) != len(diagonals) + 1:
        errors.append("число частей != число диагоналей + 1")

    for a, b, kind in diagonals:
        if a not in P or b not in P or not diagonal_ok(P, P.index(a), P.index(b)):
            errors.append("диагональ " + str(a) + "-" + str(b) + " вне полигона")

    return errors


def draw(polygon, parts, diagonals):
    size = 700
    min_x = min(p[0] for p in polygon)
    min_y = min(p[1] for p in polygon)
    width = max(p[0] for p in polygon) - min_x
    height = max(p[1] for p in polygon) - min_y
    scale = min((size - 80) / (width or 1), (size - 80) / (height or 1))

    def tr(p):
        return (40 + (p[0] - min_x) * scale, size - 40 - (p[1] - min_y) * scale)

    def flat(points):
        return [c for p in points for c in tr(p)]

    root = tk.Tk()
    canvas = tk.Canvas(root, width=size, height=size, bg="white")
    canvas.pack()

    colors = ["#ffd6d6", "#d6e4ff", "#d6ffd9", "#fff3b8", "#ecd6ff", "#d6fff7"]
    for n, part in enumerate(parts):
        canvas.create_polygon(flat(part), fill=colors[n % len(colors)], outline="")

    canvas.create_polygon(flat(polygon), fill="", outline="black", width=2)

    for a, b, kind in diagonals:
        color = "red" if kind == 'left' else "blue"
        canvas.create_line(*tr(a), *tr(b), fill=color, width=2, dash=(4, 2))

    root.mainloop()


if __name__ == "__main__":
    poly = [(0, 0), (12, 0), (12, 2), (5, 2), (6, 4), (12, 4), (12, 10),
            (0, 10), (0, 8), (7, 8), (6, 6), (0, 6)]

    parts, diagonals = make_monotone(poly)

    print("Диагонали:")
    for a, b, kind in diagonals:
        print("  ", a, "->", b, kind)

    print("Монотонных полигонов:", len(parts))
    for p in parts:
        print("  ", p)

    errors = verify(poly, parts, diagonals)
    print("Проверка:", errors or "OK")

    try:
        draw(ccw(poly), parts, diagonals)
    except Exception as e:
        print("Рисование пропущено:", e)