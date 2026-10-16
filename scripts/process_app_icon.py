"""
Process and generate all required Windows application icon formats and resolutions.
Creates transparent master PNG, multi-resolution ICO, and sized PNG icons.
"""
import sys
import os
from pathlib import Path
from PIL import Image

def process_icon(input_path: str):
    base_dir = Path(r"c:\Users\hp\Downloads\spider_watepop\assets\images")
    base_dir.mkdir(parents=True, exist_ok=True)

    master_path = base_dir / "app_icon_master.png"
    out_png = base_dir / "app_icon.png"
    out_ico = base_dir / "app_icon.ico"
    out_32 = base_dir / "app_icon_32.png"
    out_48 = base_dir / "app_icon_48.png"

    print(f"Loading generated icon from: {input_path}")
    raw_img = Image.open(input_path).convert("RGBA")

    # Use rembg with isnet-general-use if background needs removal
    try:
        from rembg import remove, new_session
        print("Removing background with rembg (isnet-general-use)...")
        session = new_session("isnet-general-use")
        clean_img = remove(raw_img, session=session)
    except Exception as e:
        print(f"rembg notice: {e}, using direct image alpha")
        clean_img = raw_img

    # Crop to non-transparent bounding box with balanced square padding
    bbox = clean_img.getbbox()
    if bbox:
        cropped = clean_img.crop(bbox)
        cw, ch = cropped.size
        dim = max(cw, ch)
        pad = int(dim * 0.08)  # 8% comfortable breathing margin
        sq_size = dim + pad * 2
        square_img = Image.new("RGBA", (sq_size, sq_size), (0, 0, 0, 0))
        ox = (sq_size - cw) // 2
        oy = (sq_size - ch) // 2
        square_img.paste(cropped, (ox, oy), cropped)
    else:
        square_img = clean_img

    # 1. Master 512x512 PNG
    master_512 = square_img.resize((512, 512), Image.Resampling.LANCZOS)
    master_512.save(master_path, format="PNG")
    print(f"Master PNG created: {master_path} (512x512)")

    # 2. Main 256x256 PNG
    main_256 = square_img.resize((256, 256), Image.Resampling.LANCZOS)
    main_256.save(out_png, format="PNG")
    print(f"Standard PNG created: {out_png} (256x256)")

    # 3. 32x32 and 48x48 PNGs
    square_img.resize((32, 32), Image.Resampling.LANCZOS).save(out_32, format="PNG")
    square_img.resize((48, 48), Image.Resampling.LANCZOS).save(out_48, format="PNG")
    print(f"Small UI icons created: {out_32}, {out_48}")

    # 4. Multi-resolution Windows ICO (16, 24, 32, 48, 64, 128, 256)
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    square_img.save(out_ico, format="ICO", sizes=sizes)
    print(f"Multi-size Windows ICO created: {out_ico} with sizes {sizes}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        process_icon(sys.argv[1])
    else:
        print("Please provide path to raw icon image.")
