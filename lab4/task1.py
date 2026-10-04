import tkinter as tk

root = tk.Tk()

canvas = tk.Canvas(root, width=800, height=600)
canvas.pack()

current_polygon = []
polygons = []


def on_click(event):
    current_polygon.append((event.x, event.y))
    draw_scene()


def finish_polygon():
    if not current_polygon:
        return

    polygons.append(current_polygon.copy())
    current_polygon.clear()

    draw_scene()


def clear_scene():
    polygons.clear()
    current_polygon.clear()

    draw_scene()


def draw_polygon(polygon, close=True):
    for x, y in polygon:
        canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill='black')

    if len(polygon) >= 2:
        last = len(polygon) if close else len(polygon) - 1

        for i in range(last):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % len(polygon)]

            canvas.create_line(x1, y1, x2, y2, fill='black')


def draw_scene():
    canvas.delete('all')

    for polygon in polygons:
        draw_polygon(polygon)

    if current_polygon:
        draw_polygon(current_polygon, close=False)


canvas.bind('<Button-1>', on_click)
finish_button = tk.Button(root, text='Завершить полигон', command=finish_polygon)
finish_button.pack()
clear_button = tk.Button(root, text='Очистить сцену', command=clear_scene)
clear_button.pack()

root.mainloop()