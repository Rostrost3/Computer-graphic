import math


# БАЗОВЫЕ КЛАССЫ
class Point3D:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __repr__(self):
        return f"({self.x:.2f}, {self.y:.2f}, {self.z:.2f})"


class Polygon:
    def __init__(self, indices, color="#4A90E2"):
        self.indices = list(indices)
        self.color = color

    def get_normal(self, vertices):
        """Вычисляет вектор нормали"""
        if len(self.indices) < 3: return (0.0, 0.0, 0.0)
        p0, p1, p2 = vertices[self.indices[0]], vertices[self.indices[1]], vertices[self.indices[2]]

        ux, uy, uz = p1.x - p0.x, p1.y - p0.y, p1.z - p0.z
        vx, vy, vz = p2.x - p0.x, p2.y - p0.y, p2.z - p0.z
        nx = uy * vz - uz * vy
        ny = uz * vx - ux * vz
        nz = ux * vy - uy * vx

        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        return (nx / length, ny / length, nz / length) if length > 0 else (0, 0, 0)


class Polyhedron:
    def __init__(self, vertices, faces, name="Фигура"):
        self.vertices = vertices
        self.faces = faces
        self.name = name
        self.edges = []  # Уникальные ребра
        self._build_edges()

    def _build_edges(self):
        """Строит список уникальных ребер"""
        edge_set = set()
        for face in self.faces:
            n = len(face.indices)
            for i in range(n):
                v1 = face.indices[i]
                v2 = face.indices[(i + 1) % n]
                edge_set.add((min(v1, v2), max(v1, v2)))
        self.edges = list(edge_set)

    def get_center(self):
        """Центр фигуры"""
        n = len(self.vertices)
        cx = sum(p.x for p in self.vertices) / n
        cy = sum(p.y for p in self.vertices) / n
        cz = sum(p.z for p in self.vertices) / n
        return Point3D(cx, cy, cz)


# ГЕНЕРАТОРЫ ФИГУР
def make_tetrahedron(s=1.0):
    v = [Point3D(s, s, s), Point3D(s, -s, -s), Point3D(-s, s, -s), Point3D(-s, -s, s)]
    f = [Polygon([0, 1, 2]), Polygon([0, 3, 1]), Polygon([0, 2, 3]), Polygon([1, 3, 2])]
    return Polyhedron(v, f, "Тетраэдр")


def make_cube(s=1.0):
    v = [
        Point3D(-s, -s, -s), Point3D(s, -s, -s), Point3D(s, s, -s), Point3D(-s, s, -s),  # задняя грань
        Point3D(-s, -s, s), Point3D(s, -s, s), Point3D(s, s, s), Point3D(-s, s, s)  # передняя грань
    ]
    f = [
        Polygon([0, 1, 2, 3]), Polygon([4, 5, 6, 7]), Polygon([0, 1, 5, 4]),
        Polygon([3, 2, 6, 7]), Polygon([0, 3, 7, 4]), Polygon([1, 2, 6, 5])
    ]
    return Polyhedron(v, f, "Куб")


def make_octahedron(s=1.0):
    v = [Point3D(s, 0, 0), Point3D(-s, 0, 0), Point3D(0, s, 0),
         Point3D(0, -s, 0), Point3D(0, 0, s), Point3D(0, 0, -s)]
    f = [
        Polygon([0, 2, 4]), Polygon([2, 1, 4]), Polygon([1, 3, 4]), Polygon([3, 0, 4]),
        Polygon([2, 0, 5]), Polygon([1, 2, 5]), Polygon([3, 1, 5]), Polygon([0, 3, 5])
    ]
    return Polyhedron(v, f, "Октаэдр")


def make_icosahedron(s=1.0):
    phi = (1 + math.sqrt(5)) / 2  # Золотое сечение
    v = [
        Point3D(-s, phi * s, 0), Point3D(s, phi * s, 0), Point3D(-s, -phi * s, 0), Point3D(s, -phi * s, 0),
        Point3D(0, -s, phi * s), Point3D(0, s, phi * s), Point3D(0, -s, -phi * s), Point3D(0, s, -phi * s),
        Point3D(phi * s, 0, -s), Point3D(phi * s, 0, s), Point3D(-phi * s, 0, -s), Point3D(-phi * s, 0, s)
    ]
    f = [
        Polygon([0, 11, 5]), Polygon([0, 5, 1]), Polygon([0, 1, 7]), Polygon([0, 7, 10]), Polygon([0, 10, 11]),
        Polygon([1, 5, 9]), Polygon([5, 11, 4]), Polygon([11, 10, 2]), Polygon([10, 7, 6]), Polygon([7, 1, 8]),
        Polygon([3, 9, 4]), Polygon([3, 4, 2]), Polygon([3, 2, 6]), Polygon([3, 6, 8]), Polygon([3, 8, 9]),
        Polygon([4, 9, 5]), Polygon([2, 4, 11]), Polygon([6, 2, 10]), Polygon([8, 6, 7]), Polygon([9, 8, 1])
    ]
    return Polyhedron(v, f, "Икосаэдр")


def make_dodecahedron(s=1.0):
    ico = make_icosahedron(s)
    v = []
    for face in ico.faces:
        cx = sum(ico.vertices[i].x for i in face.indices) / 3
        cy = sum(ico.vertices[i].y for i in face.indices) / 3
        cz = sum(ico.vertices[i].z for i in face.indices) / 3
        v.append(Point3D(cx, cy, cz))

    f = []
    for i_vertex in range(12):
        attached_faces = [idx for idx, face in enumerate(ico.faces) if i_vertex in face.indices]
        center = ico.vertices[i_vertex]

        n = (center.x, center.y, center.z)
        length = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        n = (n[0] / length, n[1] / length, n[2] / length)

        if abs(n[0]) < 0.9:
            u = (1.0, 0.0, 0.0)
        else:
            u = (0.0, 1.0, 0.0)

        dot = u[0] * n[0] + u[1] * n[1] + u[2] * n[2]
        u = (u[0] - dot * n[0], u[1] - dot * n[1], u[2] - dot * n[2])
        u_len = math.sqrt(u[0] ** 2 + u[1] ** 2 + u[2] ** 2)
        u = (u[0] / u_len, u[1] / u_len, u[2] / u_len)

        v_axis = (
            n[1] * u[2] - n[2] * u[1],
            n[2] * u[0] - n[0] * u[2],
            n[0] * u[1] - n[1] * u[0]
        )

        def angle(face_idx):
            p = v[face_idx]
            dx, dy, dz = p.x - center.x, p.y - center.y, p.z - center.z

            a = dx * u[0] + dy * u[1] + dz * u[2]
            b = dx * v_axis[0] + dy * v_axis[1] + dz * v_axis[2]
            return math.atan2(b, a)

        attached_faces.sort(key=angle)
        f.append(Polygon(attached_faces))

    return Polyhedron(v, f, "Додекаэдр")


POLYHEDRONS = {
    "Тетраэдр": make_tetrahedron,
    "Гексаэдр (Куб)": make_cube,
    "Октаэдр": make_octahedron,
    "Икосаэдр": make_icosahedron,
    "Додекаэдр": make_dodecahedron
}


# ТЕСТИРОВАНИЕ
if __name__ == "__main__":
    print("Проверка топологии по формуле Эйлера (Г + В - Р = 2):")
    for name, generator in POLYHEDRONS.items():
        poly = generator(1.0)
        V = len(poly.vertices)
        E = len(poly.edges)
        F = len(poly.faces)
        euler = V - E + F
        print(f"{name:15} | Вершин: {V:2}, Ребер: {E:2}, Граней: {F:2} | Г+В-Р = {euler}")