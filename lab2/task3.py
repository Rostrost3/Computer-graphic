from PIL import Image
import tkinter as tk
from PIL import ImageTk
import colorsys


def _rgb_to_hsv_image(img):
    pixels = list(img.getdata())
    hsv_pixels = []
    for r, g, b in pixels:
        h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
        hsv_pixels.append((h, s, v))
    return hsv_pixels


def _hsv_to_rgb_image(hsv_pixels, w, h):
    new_img = Image.new("RGB", (w, h))
    rgb_pixels = []
    for hh, ss, vv in hsv_pixels:
        hh = hh % 1.0
        ss = max(0.0, min(1.0, ss))
        vv = max(0.0, min(1.0, vv))
        r, g, b = colorsys.hsv_to_rgb(hh, ss, vv)
        rgb_pixels.append((int(r * 255), int(g * 255), int(b * 255)))
    new_img.putdata(rgb_pixels)
    return new_img


def task3(image_path="lab2/image.png"):
    original_image = Image.open(image_path).convert("RGB")
    width, height = original_image.size

    hsv_data = _rgb_to_hsv_image(original_image)

    def apply_changes(*args):
        dh = hue_shift.get() / 360.0
        ds = sat_shift.get() / 100.0
        dv = val_shift.get() / 100.0

        new_hsv = [(h + dh, s + ds, v + dv) for (h, s, v) in hsv_data]
        result_img = _hsv_to_rgb_image(new_hsv, width, height)

        result_img.save("lab2/task3_hsv_result.png")

        preview = result_img.copy()
        preview.thumbnail((500, 500))
        tk_img = ImageTk.PhotoImage(preview)
        label_image.configure(image=tk_img)
        label_image.image = tk_img

    root = tk.Tk()
    root.title("Task 3: RGB -> HSV (H, S, V)")

    preview = original_image.copy()
    preview.thumbnail((500, 500))
    tk_img = ImageTk.PhotoImage(preview)
    label_image = tk.Label(root, image=tk_img)
    label_image.pack()

    tk.Label(root, text="Hue").pack()
    hue_shift = tk.Scale(root, from_=-180, to=180, orient=tk.HORIZONTAL,
                         length=500, command=apply_changes)
    hue_shift.set(0)
    hue_shift.pack()

    tk.Label(root, text="Saturation").pack()
    sat_shift = tk.Scale(root, from_=-100, to=100, orient=tk.HORIZONTAL,
                         length=500, command=apply_changes)
    sat_shift.set(0)
    sat_shift.pack()

    tk.Label(root, text="Value").pack()
    val_shift = tk.Scale(root, from_=-100, to=100, orient=tk.HORIZONTAL,
                         length=500, command=apply_changes)
    val_shift.set(0)
    val_shift.pack()

    tk.Button(root, text="Сохранить в task3_hsv_result.png",
              command=apply_changes).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    task3("lab2/image.png")