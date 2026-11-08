"""Построение выпуклой оболочки на плоскости алгоритмом QuickHull."""

import random
import tkinter as tk
from tkinter import messagebox, ttk


WIDTH, HEIGHT = 900, 600


def cross(a, b, p):
    """Векторное произведение AB и AP: знак задаёт сторону от прямой AB."""
    return (b[0] - a[0]) * (p[1] - a[1]) - (b[1] - a[1]) * (p[0] - a[0])


def quick_hull(points):
    """
    Вернуть вершины оболочки против часовой стрелки, без повтора первой.
    """
    points = list(dict.fromkeys(tuple(p) for p in points))
    if len(points) <= 1:
        return points

    # Лексикографический порядок работает и для вертикального набора точек.
    a, b = min(points), max(points)

    def build_chain(start, end, candidates):
        if not candidates:
            return []

        # Для одной прямой длина AB постоянна, поэтому расстояние до неё
        # пропорционально модулю векторного произведения.
        # При равных расстояниях выбираем крайнюю точку вдоль прямой.
        farthest = max(
            candidates,
            key=lambda p: (
                abs(cross(start, end, p)),
                (p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2,
            ),
        )
        left_part = [p for p in candidates if cross(start, farthest, p) < 0]
        right_part = [p for p in candidates if cross(farthest, end, p) < 0]
        # Точки внутри треугольника start–farthest–end отбрасываются.
        return (
            build_chain(start, farthest, left_part)
            + [farthest]
            + build_chain(farthest, end, right_part)
        )

    below = [p for p in points if cross(a, b, p) < 0]
    above = [p for p in points if cross(b, a, p) < 0]
    return [a] + build_chain(a, b, below) + [b] + build_chain(b, a, above)


class QuickHullApp:
    def __init__(self, root):
        self.root = root
        self.points = []
        self.hull = []
        self.built = False
        root.title("QuickHull — построение выпуклой оболочки")
        root.resizable(False, False)

        controls = ttk.Frame(root, padding=8)
        controls.pack(fill="x")
        ttk.Button(controls, text="Построить оболочку", command=self.build).pack(
            side="left", padx=4
        )
        ttk.Label(controls, text="Количество точек:").pack(side="left", padx=4)
        self.count = tk.StringVar(value="50")
        ttk.Spinbox(controls, from_=1, to=2000, textvariable=self.count, width=6).pack(
            side="left", padx=4
        )
        ttk.Button(controls, text="Случайные точки", command=self.generate).pack(
            side="left", padx=4
        )
        ttk.Button(controls, text="Очистить", command=self.clear).pack(
            side="left", padx=4
        )

        ttk.Label(
            root,
            text="ЛКМ — добавить точку; ПКМ — удалить ближайшую. "
                 "Синие точки — исходный набор, красные — вершины оболочки.",
            padding=(8, 4),
        ).pack(anchor="w")
        self.canvas = tk.Canvas(
            root, width=WIDTH, height=HEIGHT, bg="white", highlightthickness=0
        )
        self.canvas.pack(padx=8, pady=4)
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.remove_point)
        self.status = tk.StringVar()
        ttk.Label(root, textvariable=self.status, padding=8).pack(anchor="w")
        self.draw()

    def add_point(self, event):
        point = (event.x, HEIGHT - event.y)
        if point not in self.points:
            self.points.append(point)
            self.refresh()

    def remove_point(self, event):
        if not self.points:
            return
        x, y = event.x, HEIGHT - event.y
        nearest = min(self.points, key=lambda p: (p[0] - x) ** 2 + (p[1] - y) ** 2)
        if (nearest[0] - x) ** 2 + (nearest[1] - y) ** 2 <= 15 ** 2:
            self.points.remove(nearest)
            self.refresh()

    def generate(self):
        try:
            count = int(self.count.get())
            if not 1 <= count <= 2000:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Введите целое число от 1 до 2000.")
            return
        # Выбор без повторов из целочисленной сетки с отступом от границ.
        width, height = WIDTH - 60, HEIGHT - 60
        self.points = [
            (30 + index % width, 30 + index // width)
            for index in random.sample(range(width * height), count)
        ]
        self.hull = []
        self.built = False
        self.draw()

    def build(self):
        self.built = True
        self.refresh()

    def refresh(self):
        if self.built:
            self.hull = quick_hull(self.points)
        self.draw()

    def clear(self):
        self.points.clear()
        self.hull = []
        self.built = False
        self.draw()

    def draw(self):
        self.canvas.delete("all")
        screen_hull = [(x, HEIGHT - y) for x, y in self.hull]
        if len(screen_hull) >= 3:
            self.canvas.create_polygon(
                *[coord for point in screen_hull for coord in point],
                fill="#eaf4ff", outline="#d32f2f", width=2,
            )
        elif len(screen_hull) == 2:
            self.canvas.create_line(*screen_hull[0], *screen_hull[1], fill="#d32f2f", width=2)

        hull_set = set(self.hull)
        for x, y in self.points:
            color = "#d32f2f" if (x, y) in hull_set else "#1565c0"
            radius = 5 if (x, y) in hull_set else 3
            sy = HEIGHT - y
            self.canvas.create_oval(
                x - radius, sy - radius, x + radius, sy + radius,
                fill=color, outline=color,
            )
        for i, (x, y) in enumerate(screen_hull, start=1):
            self.canvas.create_text(x + 9, y - 10, text=str(i), fill="#a32222")

        text = f"Точек: {len(self.points)}"
        if self.built:
            text += f" | Вершин оболочки: {len(self.hull)}"
            if not self.hull:
                text += " | Добавьте точки на поле."
            elif len(self.hull) == 1:
                text += " | Оболочка — точка."
            elif len(self.hull) == 2:
                text += " | Оболочка — отрезок."
        else:
            text += " | Нажмите «Построить оболочку»."
        self.status.set(text)


def main():
    root = tk.Tk()
    QuickHullApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
