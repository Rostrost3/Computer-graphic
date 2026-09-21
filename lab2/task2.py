from PIL import Image
import matplotlib.pyplot as plt

def draw_histogram(histogram, color, filename):
    plt.figure()
    plt.bar(range(256), histogram, color=color)
    plt.xlabel("Intensity")
    plt.ylabel("Number of pixels")
    plt.savefig(filename)
    plt.close()

def task2():
    image = Image.open("lab2/image.png")
    width, height = image.size

    histogram_r = [0] * 256
    histogram_g = [0] * 256
    histogram_b = [0] * 256

    image_r = Image.new("L", (width, height))
    image_g = Image.new("L", (width, height))
    image_b = Image.new("L", (width, height))

    for y in range(height):
        for x in range(width):
            r, g, b = image.getpixel((x, y))

            image_r.putpixel((x, y), r)
            image_g.putpixel((x, y), g)
            image_b.putpixel((x, y), b)

            histogram_r[r] += 1
            histogram_g[g] += 1
            histogram_b[b] += 1
    
    image_r.save("lab2/image_r.png")
    image_g.save("lab2/image_g.png")
    image_b.save("lab2/image_b.png")

    draw_histogram(histogram_r, "red", "lab2/histogram_r.png")
    draw_histogram(histogram_g, "green", "lab2/histogram_g.png")
    draw_histogram(histogram_b, "blue", "lab2/histogram_b.png")

    
task2() 
