"""Generate assets/icon.ico — a simple microphone icon at multiple sizes."""

from pathlib import Path
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 64, 128, 256]
OUT = Path(__file__).parent.parent / "assets" / "icon.ico"


def draw_mic(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # Dark blue background circle
    m = max(1, size // 16)
    d.ellipse([m, m, size - m - 1, size - m - 1], fill=(30, 30, 80, 255))

    # Microphone capsule (white rounded rectangle)
    cx = size / 2
    bw = size * 0.22
    bt = size * 0.15
    bb = bt + size * 0.34
    d.rounded_rectangle([cx - bw, bt, cx + bw, bb], radius=bw, fill=(255, 255, 255, 255))

    # Stand arc below capsule
    lw = max(1, size // 24)
    ar = size * 0.28
    acy = bb - size * 0.04
    d.arc([cx - ar, acy - ar, cx + ar, acy + ar], start=0, end=180,
          fill=(255, 255, 255, 255), width=lw)

    # Vertical stand
    stand_bot = size * 0.82
    d.line([(cx, acy), (cx, stand_bot)], fill=(255, 255, 255, 255), width=lw)

    # Horizontal base
    bw2 = size * 0.22
    d.line([(cx - bw2, stand_bot), (cx + bw2, stand_bot)], fill=(255, 255, 255, 255), width=lw)

    return img


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [draw_mic(s) for s in SIZES]
    images[0].save(
        OUT,
        format="ICO",
        sizes=[(s, s) for s in SIZES],
        append_images=images[1:],
    )
    print(f"Icon written to {OUT}")


if __name__ == "__main__":
    main()
