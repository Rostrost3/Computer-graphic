
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, Button


class MidpointDisplacement:
    def __init__(self, iterations=8, amplitude=1.0, roughness=0.5):
        self.iterations = iterations
        self.amplitude = amplitude
        self.roughness = roughness
        self.steps = []
        self.generate()

    def generate(self):
        """Генерация последовательных шагов алгоритма."""
        self.steps = []

        # Начальный отрезок
        points = [(0.0, 0.0), (1.0, 0.0)]
        self.steps.append(points.copy())

        displacement = self.amplitude

        for _ in range(self.iterations):
            new_points = []

            for i in range(len(points) - 1):
                x1, y1 = points[i]
                x2, y2 = points[i + 1]

                # Добавляем левую точку отрезка
                new_points.append((x1, y1))

                # Находим середину отрезка
                xm = (x1 + x2) / 2
                ym = (y1 + y2) / 2

                # Случайное вертикальное смещение
                ym += np.random.uniform(-displacement, displacement)

                new_points.append((xm, ym))

            # Добавляем последнюю точку
            new_points.append(points[-1])

            points = new_points
            self.steps.append(points.copy())

            # Уменьшаем амплитуду для следующей итерации
            displacement *= self.roughness


class MidpointDisplacementApp:
    def __init__(self):
        self.algorithm = MidpointDisplacement()

        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        plt.subplots_adjust(bottom=0.34)

        self.current_step = 0

        # Ползунок выбора итерации
        ax_step = self.fig.add_axes([0.2, 0.23, 0.65, 0.03])
        self.slider_step = Slider(
            ax_step, "Итерация",
            0, self.algorithm.iterations,
            valinit=0, valstep=1
        )
        self.slider_step.on_changed(self.update_step)

        # Ползунок количества итераций
        ax_iterations = self.fig.add_axes([0.2, 0.17, 0.65, 0.03])
        self.slider_iterations = Slider(
            ax_iterations, "Количество итераций",
            1, 10, valinit=8, valstep=1
        )
        self.slider_iterations.on_changed(self.update_parameters)

        # Ползунок начальной амплитуды
        ax_amplitude = self.fig.add_axes([0.2, 0.11, 0.65, 0.03])
        self.slider_amplitude = Slider(
            ax_amplitude, "Амплитуда",
            0.1, 3.0, valinit=1.0
        )
        self.slider_amplitude.on_changed(self.update_parameters)

        # Ползунок шероховатости
        ax_roughness = self.fig.add_axes([0.2, 0.05, 0.65, 0.03])
        self.slider_roughness = Slider(
            ax_roughness, "Шероховатость",
            0.1, 0.9, valinit=0.5
        )
        self.slider_roughness.on_changed(self.update_parameters)

        # Кнопка генерации нового рельефа
        ax_button = self.fig.add_axes([0.78, 0.89, 0.17, 0.06])
        self.button_generate = Button(ax_button, "Новый рельеф")
        self.button_generate.on_clicked(self.new_terrain)

        self.draw()

    def draw(self):
        """Отрисовка текущего шага алгоритма."""
        self.ax.clear()

        points = self.algorithm.steps[self.current_step]
        x = [p[0] for p in points]
        y = [p[1] for p in points]

        self.ax.plot(x, y, color="black", linewidth=1.5)
        self.ax.scatter(x, y, color="red", s=12, zorder=3)

        self.ax.fill_between(x, y, min(min(y), 0) - 0.5,
                             color="lightgray", alpha=0.7)

        self.ax.set_title(
            f"Midpoint Displacement — шаг {self.current_step}"
        )
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Высота")
        self.ax.grid(True, alpha=0.3)

        self.ax.set_xlim(0, 1)

        self.fig.canvas.draw_idle()

    def update_step(self, value):
        self.current_step = int(value)
        self.draw()

    def update_parameters(self, _):
        """Перестраиваем рельеф при изменении параметров."""
        iterations = int(self.slider_iterations.val)
        amplitude = self.slider_amplitude.val
        roughness = self.slider_roughness.val

        self.algorithm = MidpointDisplacement(
            iterations=iterations,
            amplitude=amplitude,
            roughness=roughness
        )

        self.current_step = min(self.current_step, iterations)

        # Обновляем диапазон ползунка шага
        self.slider_step.valmax = iterations
        self.slider_step.ax.set_xlim(0, iterations)
        self.slider_step.set_val(self.current_step)

        self.draw()

    def new_terrain(self, _):
        """Создаём новый случайный профиль с теми же параметрами."""
        self.algorithm = MidpointDisplacement(
            iterations=int(self.slider_iterations.val),
            amplitude=self.slider_amplitude.val,
            roughness=self.slider_roughness.val
        )

        self.current_step = 0
        self.slider_step.set_val(0)
        self.draw()


if __name__ == "__main__":
    app = MidpointDisplacementApp()
    plt.show()
