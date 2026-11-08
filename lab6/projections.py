import math
from task2 import mat_mul, rotation_x, rotation_y


def axonometric_matrix():
    """Изометрический вид: поворот системы наблюдения и проекция на XY."""
    view = mat_mul(rotation_y(-math.pi / 4),
                   rotation_x(math.atan(1 / math.sqrt(2))))
    orthographic = [[1, 0, 0, 0], [0, 1, 0, 0],
                    [0, 0, 0, 0], [0, 0, 0, 1]]
    return mat_mul(view, orthographic)


def perspective_matrix(distance=6.0):
    """Камера на расстоянии distance от начала координат вдоль оси вида.

    После умножения x и y делятся на w = 1 + z_view / distance.
    Видовой поворот совпадает с аксонометрическим для удобства сравнения.
    """
    if not math.isfinite(distance) or distance <= 0:
        raise ValueError("Расстояние до камеры должно быть положительным")
    view = mat_mul(rotation_y(-math.pi / 4),
                   rotation_x(math.atan(1 / math.sqrt(2))))
    perspective = [[1, 0, 0, 0], [0, 1, 0, 0],
                   [0, 0, 0, 1 / distance], [0, 0, 0, 1]]
    return mat_mul(view, perspective)


def project_vertices(vertices, matrix):
    """Возвращает однородные координаты без изменения исходных вершин."""
    result = []
    for point in vertices:
        row = (point.x, point.y, point.z, 1.0)
        result.append(tuple(sum(row[i] * matrix[i][j] for i in range(4))
                            for j in range(4)))
    return result


def project_edge(start, end, near=0.05):
    """Отсекает ребро у камеры до перспективного деления на w."""
    if start[3] < near and end[3] < near:
        return None
    if start[3] < near or end[3] < near:
        t = (near - start[3]) / (end[3] - start[3])
        intersection = tuple(a + t * (b - a) for a, b in zip(start, end))
        if start[3] < near:
            start = intersection
        else:
            end = intersection
    return ((start[0] / start[3], start[1] / start[3]),
            (end[0] / end[3], end[1] / end[3]))
