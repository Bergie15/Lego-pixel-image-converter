def export(pixel_map, filename="spike_pixels.txt"):
    with open(filename, "w") as f:
        f.write("pixel_map = [\n")
        for row in pixel_map:
            f.write(f" {row},\n")
        f.write("]\n")
