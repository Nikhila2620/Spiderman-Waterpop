import os
from PIL import Image

def generate_app_icon():
    src_png = r"c:\Users\hp\Downloads\spider_watepop\assets\images\spidey_3d_render.png"
    out_ico = r"c:\Users\hp\Downloads\spider_watepop\assets\images\app_icon.ico"
    out_png = r"c:\Users\hp\Downloads\spider_watepop\assets\images\app_icon.png"

    img = Image.open(src_png).convert("RGBA")
    w, h = img.size

    # Crop to square focused on the character's head and upper chest for a crisp icon
    # Head is near bottom center (y: 650..1350, x: 150..650)
    # Let's create a square crop with padding
    square_size = max(w, h)
    square_img = Image.new("RGBA", (square_size, square_size), (0, 0, 0, 0))
    # Paste centered
    offset_x = (square_size - w) // 2
    offset_y = (square_size - h) // 2
    square_img.paste(img, (offset_x, offset_y), img)

    # Save PNG icon (256x256)
    icon_png = square_img.resize((256, 256), Image.Resampling.LANCZOS)
    icon_png.save(out_png, format="PNG")
    print(f"[SUCCESS] Saved app_icon.png to: {out_png}")

    # Save multi-resolution Windows ICO (16, 32, 48, 64, 128, 256)
    icon_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    square_img.save(out_ico, format="ICO", sizes=icon_sizes)
    print(f"[SUCCESS] Saved multi-resolution app_icon.ico to: {out_ico}")

if __name__ == "__main__":
    generate_app_icon()
