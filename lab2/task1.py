from PIL import Image
import matplotlib.pyplot as plt


def draw_histogram(histogram, color, filename):
    plt.figure()
    plt.bar(range(256), histogram, color=color)
    plt.xlabel("Intensity")
    plt.ylabel("Number of pixels")
    plt.savefig(filename)
    plt.close()


def task1():
    image = Image.open("image.png").convert("RGB")
    width, height = image.size

    gray_pal  = Image.new("L", (width, height))
    gray_hdtv = Image.new("L", (width, height))
    gray_diff = Image.new("L", (width, height))

    histogram_pal  = [0] * 256
    histogram_hdtv = [0] * 256
    histogram_diff = [0] * 256

    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))

            # Y = 0.299*R + 0.587*G + 0.114*B
            v_pal = int(0.299 * r + 0.587 * g + 0.114 * b)

            # Y = 0.2126*R + 0.7152*G + 0.0722*B
            v_hdtv = int(0.2126 * r + 0.7152 * g + 0.0722 * b)

            v_pal  = max(0, min(255, v_pal))
            v_hdtv = max(0, min(255, v_hdtv))

            gray_pal.putpixel((x, y), v_pal)
            gray_hdtv.putpixel((x, y), v_hdtv)

            histogram_pal[v_pal] += 1
            histogram_hdtv[v_hdtv] += 1

            v_diff = abs(v_pal - v_hdtv)
            gray_diff.putpixel((x, y), v_diff)
            histogram_diff[v_diff] += 1

    gray_pal.save("gray_pal.png")
    gray_hdtv.save("gray_hdtv.png")
    gray_diff.save("gray_diff.png")

    draw_histogram(histogram_pal,  "gray",   "histogram_gray_pal.png")
    draw_histogram(histogram_hdtv, "gray",   "histogram_gray_hdtv.png")
    draw_histogram(histogram_diff, "purple", "histogram_gray_diff.png")


if __name__ == "__main__":
    task1()