import os
import sys
import glob
import argparse
from collections import Counter
from PIL import Image

try:
    from .image_to_pixels import image_to_pixel_map
    # planner and robot removed — focus on image generation
    from .colors import EMOJI, PALETTE_COLORS
except Exception:
    from image_to_pixels import image_to_pixel_map
    from colors import EMOJI, PALETTE_COLORS


def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def create_bitdepth_assets(src_path, size=None, out_dir=None, scale=8):
    _ensure_dir(out_dir)
    base = Image.open(src_path).convert("RGB")
    if size and size > 0:
        base = base.resize((size, size), resample=Image.NEAREST)

    targets = [1, 2, 4, 8, 16, 24, 32, 48, 64]
    for bits in targets:
        try:
            if bits in (1, 2, 4, 8):
                colors = 2 ** bits
                im = base.quantize(colors=min(colors, 256), method=Image.MEDIANCUT)
                out_path = os.path.join(out_dir, f"asset_{bits}bit.png")
                scaled = im.convert("RGB").resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 16:
                w, h = base.size
                im16 = Image.new("RGB", (w, h))
                px_src = base.load()
                px_dst = im16.load()
                for y in range(h):
                    for x in range(w):
                        r, g, b = px_src[x, y]
                        r5 = r >> 3
                        g6 = g >> 2
                        b5 = b >> 3
                        r8 = (r5 << 3) | (r5 >> 2)
                        g8 = (g6 << 2) | (g6 >> 4)
                        b8 = (b5 << 3) | (b5 >> 2)
                        px_dst[x, y] = (r8, g8, b8)
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb565.png")
                scaled = im16.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 24:
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb888.png")
                scaled = base.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 32:
                rgba = base.copy().convert("RGBA")
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgba8888.png")
                scaled = rgba.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits in (48, 64):
                try:
                    import numpy as np
                except Exception:
                    out_path = os.path.join(out_dir, f"asset_{bits}bit_fallback.png")
                    scaled = base.resize((size * scale, size * scale), resample=Image.NEAREST)
                    scaled.save(out_path)
                else:
                    arr = np.array(base, dtype=np.uint8)
                    arr16 = (arr.astype(np.uint16) * 257)
                    if bits == 48:
                        img16 = Image.fromarray(arr16, mode="RGB")
                        out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb16.png")
                        scaled = img16.resize((size * scale, size * scale), resample=Image.NEAREST)
                        scaled.save(out_path)
                    else:
                        h, w = arr.shape[:2]
                        alpha16 = np.full((h, w, 1), 65535, dtype=np.uint16)
                        rgba16 = np.concatenate([arr16, alpha16], axis=2)
                        img64 = Image.fromarray(rgba16, mode="RGBA")
                        out_path = os.path.join(out_dir, f"asset_{bits}bit_rgba16.png")
                        scaled = img64.resize((size * scale, size * scale), resample=Image.NEAREST)
                        scaled.save(out_path)

            print(f"Created asset for {bits}-bit: {out_path}")
        except Exception as e:
            print(f"Failed to create {bits}-bit asset: {e}")



def find_input_image(cli_path=None):
    repo_root = os.path.dirname(os.path.dirname(__file__))
    images_dir = os.path.join(repo_root, "images")

    if cli_path:
        arg = cli_path
        if os.path.isabs(arg) and os.path.exists(arg):
            return arg
        candidate = os.path.join(repo_root, arg) if not os.path.exists(arg) else arg
        if os.path.exists(candidate):
            return candidate

    try:
        os.makedirs(images_dir, exist_ok=True)
    except Exception:
        pass

    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"):
        matches = sorted(glob.glob(os.path.join(images_dir, pattern)))
        if matches:
            return matches[0]

    root_image = os.path.join(repo_root, "image.png")
    if os.path.exists(root_image):
        return root_image

    print(f"No images found in '{images_dir}' and no 'image.png' in repo root.")
    print("Place an image into the 'images' folder or pass a path as the first argument:")
    print("  python ./decor_planner/main.py path/to/image.png")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an image to a decor pixel map.")
    parser.add_argument("image", nargs="?", help="Path to image (optional). If omitted the first image in images/ is used.")
    parser.add_argument("--size", type=int, default=64, help="Resize image to SIZE x SIZE before conversion (default: 64)")
    parser.add_argument("--scale", type=int, default=8, help="Scale factor for saved preview PNG (each pixel becomes SCALE x SCALE pixels, default: 8)")
    args = parser.parse_args()

    img_path = find_input_image(args.image)
    print(f"Using image: {img_path}")

    pixel_map = image_to_pixel_map(img_path, size=args.size)

    print("\n🖼️ PIXEL PREVIEW")
    for row in pixel_map:
        print(" ".join(EMOJI[c] for c in row))

    try:
        counts = Counter(c for row in pixel_map for c in row)
        colors_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "colors_used.txt")
        with open(colors_file, "w", encoding="utf-8") as fh:
            fh.write("code,count,R,G,B,emoji\n")
            for code, cnt in counts.most_common():
                rgb = PALETTE_COLORS.get(code, (0, 0, 0))
                emoji = EMOJI.get(code, "")
                fh.write(f"{code},{cnt},{rgb[0]},{rgb[1]},{rgb[2]},{emoji}\n")
        print(f"Saved color usage to {colors_file}")
    except Exception as e:
        print(f"Failed to write color usage file: {e}")

    try:
        h = len(pixel_map)
        w = len(pixel_map[0]) if h else 0
        preview = Image.new("RGB", (w, h))
        px = preview.load()
        for y in range(h):
            for x in range(w):
                code = pixel_map[y][x]
                rgb = PALETTE_COLORS.get(code, (0, 0, 0))
                px[x, y] = rgb

        out_scale = args.scale
        scaled = preview.resize((w * out_scale, h * out_scale), resample=Image.NEAREST)
        out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "decor_preview.png")
        scaled.save(out_path)
        print(f"Saved blocky preview to {out_path} (size {w}x{h} scaled x{out_scale})")
    except Exception as e:
        print(f"Failed to create preview PNG: {e}")

    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    print(f"Generating bit-depth assets into {assets_dir} ...")
    create_bitdepth_assets(img_path, size=args.size, out_dir=assets_dir, scale=args.scale)

    # Virtual build/export removed — this tool now only generates previews and assets
