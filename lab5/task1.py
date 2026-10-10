import turtle
import math
import random


def read_lsystem(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = file.readlines()

    atom, angle, direction = lines[0].split()

    rules = {}

    for line in lines[1:]:
        symbol, replacement = line.split("->")
        rules[symbol.strip()] = replacement.strip()

    return atom, float(angle), float(direction), rules


def generate(axiom, rules, iterations):
    current = axiom

    for _ in range(iterations):
        result = ""

        for symbol in current:
            if symbol in rules:
                result += rules[symbol]
            else:
                result += symbol

        current = result

    return current


def calculate_points(commands, angle, length, direction):
    x, y = 0, 0
    heading = direction

    segments = []
    stack = []

    for symbol in commands:
        if symbol == "F":
            new_x = x + length * math.cos(math.radians(heading))
            new_y = y + length * math.sin(math.radians(heading))

            segments.append(((x, y), (new_x, new_y)))

            x, y = new_x, new_y

        elif symbol == "+":
            heading += angle# + random.uniform(-90, 90)

        elif symbol == "-":
            heading -= angle# + random.uniform(-90, 90)

        elif symbol == "[":
            stack.append((x, y, heading))

        elif symbol == "]":
            x, y, heading = stack.pop()

    return segments


def get_bounds(segments):
    xs = []
    ys = []

    for start, end in segments:
        xs.extend([start[0], end[0]])
        ys.extend([start[1], end[1]])

    min_x = min(xs)
    max_x = max(xs)
    min_y = min(ys)
    max_y = max(ys)

    return min_x, max_x, min_y, max_y


def draw_segments(segments, min_x, max_x, min_y, max_y):
    screen_width = screen.window_width() - 40
    screen_height = screen.window_height() - 40

    width = max_x - min_x
    height = max_y - min_y

    scale_x = screen_width / width if width > 0 else 1
    scale_y = screen_height / height if height > 0 else 1
    scale = min(scale_x, scale_y)

    center_x = (min_x + max_x) / 2
    center_y = (min_y + max_y) / 2

    t.penup()

    for start, end in segments:
        x1, y1 = start
        x2, y2 = end

        screen_x1 = (x1 - center_x) * scale
        screen_y1 = (y1 - center_y) * scale
        screen_x2 = (x2 - center_x) * scale
        screen_y2 = (y2 - center_y) * scale

        t.goto(screen_x1, screen_y1)
        t.pendown()
        t.goto(screen_x2, screen_y2)
        t.penup()


screen = turtle.Screen()
t = turtle.Turtle()

t.speed(0)
t.hideturtle()

atom, angle, direction, rules = read_lsystem("lab5/test.txt")

result = generate(atom, rules, 3)

segments = calculate_points(result, angle, 10, direction)
min_x, max_x, min_y, max_y = get_bounds(segments)

draw_segments(segments, min_x, max_x, min_y, max_y)

turtle.done()
