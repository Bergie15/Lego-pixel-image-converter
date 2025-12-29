import os
import sys
import glob
import argparse
from image_to_pixels import image_to_pixel_map
from planner import build
from export_spike import export
from colors import EMOJI, LEGO_COLORS
from collections import Counter
from PIL import Image


def _ensure_dir(path):
    try:
        os.makedirs(path, exist_ok=True)
    except Exception:
        pass


def create_bitdepth_assets(src_path, size, out_dir, scale=8):
    """Create asset images for multiple bit-depth targets.

    Outputs paletted (1/2/4/8-bit) versions, an RGB565-like 16-bit reduced
    image, 24-bit RGB, 32-bit RGBA, and 48/64-bit per-channel (if numpy
    is available). Files are written into `out_dir`.
    """
    _ensure_dir(out_dir)
    base = Image.open(src_path).convert("RGB")
    base = base.resize((size, size), resample=Image.NEAREST)

    targets = [1, 2, 4, 8, 16, 24, 32, 48, 64]
    for bits in targets:
        try:
            if bits in (1, 2, 4, 8):
                colors = 2 ** bits
                im = base.quantize(colors=min(colors, 256), method=Image.MEDIANCUT)
                # ensure paletted PNG saved
                out_path = os.path.join(out_dir, f"asset_{bits}bit.png")
                # scale for preview/asset size
                scaled = im.convert("RGB").resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 16:
                # emulate RGB565: reduce R5 G6 B5 then expand back to 8-bit for storage
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
                        # expand back to 8-bit (approx)
                        r8 = (r5 << 3) | (r5 >> 2)
                        g8 = (g6 << 2) | (g6 >> 4)
                        b8 = (b5 << 3) | (b5 >> 2)
                        px_dst[x, y] = (r8, g8, b8)
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb565.png")
                scaled = im16.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 24:
                # standard RGB 8-bit per channel
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb888.png")
                scaled = base.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits == 32:
                # RGBA8888 - add opaque alpha
                rgba = base.copy().convert("RGBA")
                out_path = os.path.join(out_dir, f"asset_{bits}bit_rgba8888.png")
                scaled = rgba.resize((size * scale, size * scale), resample=Image.NEAREST)
                scaled.save(out_path)

            elif bits in (48, 64):
                # 16 bits per channel. Prefer numpy if available to create uint16 arrays
                try:
                    import numpy as np
                except Exception:
                    # fallback: create 8-bit scaled image (best-effort)
                    out_path = os.path.join(out_dir, f"asset_{bits}bit_fallback.png")
                    scaled = base.resize((size * scale, size * scale), resample=Image.NEAREST)
                    scaled.save(out_path)
                else:
                    arr = np.array(base, dtype=np.uint8)
                    # expand 0-255 to 0-65535 by scaling
                    arr16 = (arr.astype(np.uint16) * 257)
                    if bits == 48:
                        # shape (h,w,3) uint16 RGB
                        img16 = Image.fromarray(arr16, mode="RGB")
                        out_path = os.path.join(out_dir, f"asset_{bits}bit_rgb16.png")
                        scaled = img16.resize((size * scale, size * scale), resample=Image.NEAREST)
                        scaled.save(out_path)
                    else:
                        # 64-bit RGBA: add opaque alpha channel as uint16 65535
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
    """Find an image to convert.

    Priority:
    1. CLI argument (first arg)
    2. First image found in repo-root/images/ (by extension order)
    3. repo-root/image.png fallback
    """
    repo_root = os.path.dirname(os.path.dirname(__file__))
    images_dir = os.path.join(repo_root, "images")

    # If user passed a path via CLI, use it
    if cli_path:
        arg = cli_path
        if os.path.isabs(arg) and os.path.exists(arg):
            return arg
        # allow relative to repo root or absolute
        candidate = os.path.join(repo_root, arg) if not os.path.exists(arg) else arg
        if os.path.exists(candidate):
            return candidate

    # ensure images dir exists (create empty folder to make it easy)
    try:
        os.makedirs(images_dir, exist_ok=True)
    except Exception:
        pass

    # look for a common image file inside images/
    for pattern in ("*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"):
        matches = sorted(glob.glob(os.path.join(images_dir, pattern)))
        if matches:
            return matches[0]

    # fallback to repo-root/image.png
    root_image = os.path.join(repo_root, "image.png")
    if os.path.exists(root_image):
        return root_image

    # nothing found
    print(f"No images found in '{images_dir}' and no 'image.png' in repo root.")
    print("Place an image into the 'images' folder or pass a path as the first argument:")
    print("  python .\\lego_pixel_bot\\main.py path/to/image.png")
    sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Convert an image to a LEGO pixel map.")
    parser.add_argument("image", nargs="?", help="Path to image (optional). If omitted the first image in images/ is used.")
    parser.add_argument("--size", type=int, default=64, help="Resize image to SIZE x SIZE before conversion (default: 64)")
    parser.add_argument("--scale", type=int, default=8, help="Scale factor for saved preview PNG (each LEGO pixel becomes SCALE x SCALE pixels, default: 8)")
    args = parser.parse_args()

    img_path = find_input_image(args.image)
    print(f"Using image: {img_path}")

    pixel_map = image_to_pixel_map(img_path, size=args.size)

    print("\n🖼️ PIXEL PREVIEW")
    for row in pixel_map:
        print(" ".join(EMOJI[c] for c in row))

    # Write a color usage summary to repo-root/colors_used.txt
    try:
        counts = Counter(c for row in pixel_map for c in row)
        colors_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "colors_used.txt")
        with open(colors_file, "w", encoding="utf-8") as fh:
            fh.write("code,count,R,G,B,emoji\n")
            for code, cnt in counts.most_common():
                rgb = LEGO_COLORS.get(code, (0, 0, 0))
                emoji = EMOJI.get(code, "")
                fh.write(f"{code},{cnt},{rgb[0]},{rgb[1]},{rgb[2]},{emoji}\n")
        print(f"Saved color usage to {colors_file}")
    except Exception as e:
        print(f"Failed to write color usage file: {e}")

    # Create and save a blocky PNG preview that looks like a pixel-art game texture
    try:
        h = len(pixel_map)
        w = len(pixel_map[0]) if h else 0
        preview = Image.new("RGB", (w, h))
        px = preview.load()
        for y in range(h):
            for x in range(w):
                code = pixel_map[y][x]
                rgb = LEGO_COLORS.get(code, (0, 0, 0))
                px[x, y] = rgb

        out_scale = args.scale
        scaled = preview.resize((w * out_scale, h * out_scale), resample=Image.NEAREST)
        out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "lego_preview.png")
        scaled.save(out_path)
        print(f"Saved blocky preview to {out_path} (size {w}x{h} scaled x{out_scale})")
    except Exception as e:
        print(f"Failed to create preview PNG: {e}")

    # Generate bit-depth assets (1..64). Assets placed in repo-root/assets/
    assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets")
    print(f"Generating bit-depth assets into {assets_dir} ...")
    create_bitdepth_assets(img_path, size=args.size, out_dir=assets_dir, scale=args.scale)

    print("\n🤖 VIRTUAL BUILD")
    build(pixel_map)

    export(pixel_map)
    print("\n✅ Exported SPIKE-ready pixel_map")
