from main import make_cube, make_tetrahedron, POLYHEDRONS

import copy
import math


def identity():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)] for i in range(4)]


def translation(tx, ty, tz):
    M = identity()
    M[3][0], M[3][1], M[3][2] = tx, ty, tz
    return M


def scaling(mx, my, mz):
    M = identity()
    M[0][0], M[1][1], M[2][2] = mx, my, mz
    return M


def rotation_x(a):
    c, s = math.cos(a), math.sin(a)
    M = identity()
    M[1][1], M[1][2] = c, s
    M[2][1], M[2][2] = -s, c
    return M


def rotation_y(a):
    c, s = math.cos(a), math.sin(a)
    M = identity()
    M[0][0], M[0][2] = c, -s
    M[2][0], M[2][2] = s, c
    return M


def rotation_z(a):
    c, s = math.cos(a), math.sin(a)
    M = identity()
    M[0][0], M[0][1] = c, s
    M[1][0], M[1][1] = -s, c
    return M


def reflection(plane):
    plane = plane.lower()
    if plane == "xy":
        return scaling(1, 1, -1)
    if plane == "yz":
        return scaling(-1, 1, 1)
    if plane == "xz":
        return scaling(1, -1, 1)
    raise ValueError("Плоскость должна быть 'xy', 'yz' или 'xz'")


def about_point(M, c):
    return mat_mul(mat_mul(translation(-c[0], -c[1], -c[2]), M), translation(c[0], c[1], c[2]))


def scaling_about_center(center, mx, my=None, mz=None):
    my = mx if my is None else my
    mz = mx if mz is None else mz
    return about_point(scaling(mx, my, mz), center)


def rotation_about_center_axis(center, axis, angle):
    rot = {"x": rotation_x, "y": rotation_y, "z": rotation_z}[axis.lower()]
    return about_point(rot(angle), center)


def _direction(p1, p2):
    d = [p2[i] - p1[i] for i in range(3)]
    length = math.sqrt(sum(v * v for v in d))
    if length < 1e-12:
        raise ValueError("Точки, задающие прямую, совпадают")
    return [v / length for v in d]


def rotation_about_line(p1, p2, angle):
    l, m, n = _direction(p1, p2)
    c, s = math.cos(angle), math.sin(angle)
    k = 1 - c
    R = [
        [l*l + c*(1 - l*l), l*k*m + n*s,        l*k*n - m*s,        0.0],
        [l*k*m - n*s,       m*m + c*(1 - m*m),  m*k*n + l*s,        0.0],
        [l*k*n + m*s,       m*k*n - l*s,        n*n + c*(1 - n*n),  0.0],
        [0.0,               0.0,                0.0,                1.0],
    ]
    return about_point(R, p1)


def rotation_about_line_decomposed(p1, p2, angle):
    l, m, n = _direction(p1, p2)
    d = math.hypot(m, n)
    psi = math.atan2(m, n) if d > 1e-12 else 0.0   # cosψ = n/d, sinψ = m/d
    theta = math.atan2(-l, d)                      # cosθ = d,   sinθ = -l
    M = translation(-p1[0], -p1[1], -p1[2])
    for step in (rotation_x(psi), rotation_y(theta), rotation_z(angle),
                 rotation_y(-theta), rotation_x(-psi),
                 translation(p1[0], p1[1], p1[2])):
        M = mat_mul(M, step)
    return M



def _xyz(p):
    if hasattr(p, "x"):
        return (p.x, p.y, p.z)
    return (float(p[0]), float(p[1]), float(p[2]))


def _det3(M):
    return (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
            - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
            + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))


def transform(poly, M):
    new = copy.deepcopy(poly)
    for p in new.vertices:
        x, y, z = p.x, p.y, p.z
        nx = x * M[0][0] + y * M[1][0] + z * M[2][0] + M[3][0]
        ny = x * M[0][1] + y * M[1][1] + z * M[2][1] + M[3][1]
        nz = x * M[0][2] + y * M[1][2] + z * M[2][2] + M[3][2]
        w = x * M[0][3] + y * M[1][3] + z * M[2][3] + M[3][3]
        p.x, p.y, p.z = nx / w, ny / w, nz / w
    if _det3(M) < 0:
        for face in new.faces:
            face.indices.reverse()
    return new



def translate(poly, dx, dy, dz):
    return transform(poly, translation(dx, dy, dz))


def rotate_about_origin(poly, ax_deg, ay_deg, az_deg):
    M = mat_mul(mat_mul(rotation_x(math.radians(ax_deg)),
                        rotation_y(math.radians(ay_deg))),
                rotation_z(math.radians(az_deg)))
    return transform(poly, M)


def scale_about_origin(poly, mx, my, mz):
    return transform(poly, scaling(mx, my, mz))


def scale_about_center(poly, mx, my=None, mz=None):
    return transform(poly, scaling_about_center(_xyz(poly.get_center()), mx, my, mz))


def reflect(poly, plane):
    return transform(poly, reflection(plane))


def rotate_about_center_axis(poly, axis, angle_deg):
    c = _xyz(poly.get_center())
    return transform(poly, rotation_about_center_axis(c, axis, math.radians(angle_deg)))


def rotate_about_line(poly, p1, p2, angle_deg):
    """p1, p2 — Point3D или кортежи (x, y, z)."""
    return transform(poly, rotation_about_line(_xyz(p1), _xyz(p2), math.radians(angle_deg)))



if __name__ == "__main__":
    def pts(poly):
        return [(p.x, p.y, p.z) for p in poly.vertices]

    def close(a, b, eps=1e-9):
        return all(abs(u - v) < eps for p, q in zip(a, b) for u, v in zip(p, q))

    cube = make_cube(1.0)

    p1, p2, ang = (0.3, -1.0, 2.0), (2.0, 1.5, -0.5), math.radians(37)
    A = rotation_about_line(p1, p2, ang)
    B = rotation_about_line_decomposed(p1, p2, ang)
    print("Формула == разложение по лекции:",
          all(abs(A[i][j] - B[i][j]) < 1e-9 for i in range(4) for j in range(4)))

    from_poly = type(cube.vertices[0])
    line_pts = [from_poly(*p1), from_poly(*p2)]
    tmp = copy.deepcopy(cube)
    tmp.vertices = line_pts
    tmp.faces = []
    print("Точки оси неподвижны:", close(pts(transform(tmp, A)), [p1, p2]))

    def edge_lengths(poly):
        v = poly.vertices
        return sorted(round(math.dist((v[a].x, v[a].y, v[a].z), (v[b].x, v[b].y, v[b].z)), 9)
                      for a, b in poly.edges)
    print("Длины рёбер сохраняются:",
          edge_lengths(cube) == edge_lengths(rotate_about_line(cube, p1, p2, 37)))

    scaled = scale_about_center(cube, 2)
    print("Центр после масштаба:", scaled.get_center(), "| ребро x2:",
          edge_lengths(scaled)[0] == 2 * edge_lengths(cube)[0])

    r = cube
    for _ in range(4):
        r = rotate_about_center_axis(r, "y", 90)
    print("4 x 90° = исходная фигура:", close(pts(r), pts(cube)))

    def outward(poly):
        c = poly.get_center()
        res = []
        for f in poly.faces:
            n = f.get_normal(poly.vertices)
            p = poly.vertices[f.indices[0]]
            res.append(n[0]*(p.x-c.x) + n[1]*(p.y-c.y) + n[2]*(p.z-c.z) > 0)
        return res

    for name, gen in POLYHEDRONS.items():
        fig = gen(1.0)
        print(f"Отражение XY, {name:15}: ориентация граней сохранена = "
              f"{outward(fig) == outward(reflect(fig, 'xy'))}")