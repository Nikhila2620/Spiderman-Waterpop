"""
Generates the official Spider-Man Water Buddy v2.0 app logo:
A stylized superhero spider emblem harmoniously fused with a crystal-clear cyan water droplet.
Generates master PNG and multi-resolution ICO for Windows taskbar, shortcuts, and app branding.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter
import math

def draw_spiderman_water_logo(size=1024):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = size / 2.0
    cy = size / 2.0
    radius = size * 0.46

    # 1. Subtle Outer Glow Ring (Cyan + Crimson)
    for i in range(16):
        r = radius + (16 - i) * 1.5
        alpha = int(8 + i * 3)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(0, 240, 255, alpha), width=2)

    # 2. Base Dark Obsidian Hex/Circle Card Background
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=(18, 20, 24, 255))
    
    # 3. Inner Hairline Border
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], outline=(44, 49, 58, 255), width=int(size * 0.012))
    inner_r = radius * 0.94
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], outline=(214, 72, 63, 120), width=int(size * 0.006))

    # 4. Stylized Spider Legs (4 on left, 4 on right)
    # Using smooth polygonal points
    crimson = (214, 72, 63, 255)
    scarlet = (255, 60, 80, 255)

    def draw_symmetric_leg(joint1, joint2, tip, width):
        # Left leg
        draw.line([joint1, joint2], fill=crimson, width=width)
        draw.line([joint2, tip], fill=scarlet, width=int(width * 0.8))
        # Right leg (mirrored across cx)
        m_j1 = (2 * cx - joint1[0], joint1[1])
        m_j2 = (2 * cx - joint2[0], joint2[1])
        m_tip = (2 * cx - tip[0], tip[1])
        draw.line([m_j1, m_j2], fill=crimson, width=width)
        draw.line([m_j2, m_tip], fill=scarlet, width=int(width * 0.8))

    # Upper legs 1 & 2
    w_leg = int(size * 0.038)
    draw_symmetric_leg((cx - size * 0.07, cy - size * 0.05), (cx - size * 0.28, cy - size * 0.28), (cx - size * 0.38, cy - size * 0.40), w_leg)
    draw_symmetric_leg((cx - size * 0.08, cy - size * 0.01), (cx - size * 0.35, cy - size * 0.16), (cx - size * 0.43, cy - size * 0.22), w_leg)

    # Lower legs 3 & 4
    draw_symmetric_leg((cx - size * 0.08, cy + size * 0.08), (cx - size * 0.36, cy + size * 0.18), (cx - size * 0.41, cy + size * 0.32), w_leg)
    draw_symmetric_leg((cx - size * 0.06, cy + size * 0.15), (cx - size * 0.26, cy + size * 0.34), (cx - size * 0.30, cy + size * 0.44), w_leg)

    # 5. Spider Head (Angular Mask Chevron at the top)
    head_points = [
        (cx, cy - size * 0.26),
        (cx - size * 0.09, cy - size * 0.15),
        (cx - size * 0.06, cy - size * 0.07),
        (cx + size * 0.06, cy - size * 0.07),
        (cx + size * 0.09, cy - size * 0.15),
    ]
    draw.polygon(head_points, fill=crimson)

    # Spider Eyes on the emblem (glossy white/cyan chevrons)
    eye_l = [
        (cx - size * 0.055, cy - size * 0.18),
        (cx - size * 0.015, cy - size * 0.13),
        (cx - size * 0.055, cy - size * 0.11),
    ]
    eye_r = [
        (cx + size * 0.055, cy - size * 0.18),
        (cx + size * 0.015, cy - size * 0.13),
        (cx + size * 0.055, cy - size * 0.11),
    ]
    draw.polygon(eye_l, fill=(255, 255, 255, 255))
    draw.polygon(eye_r, fill=(255, 255, 255, 255))

    # 6. Central Body: Crystal-Clear Luminous Cyan Water Droplet
    # The water droplet forms the abdomen of the superhero spider!
    drop_top_y = cy - size * 0.09
    drop_bottom_y = cy + size * 0.26
    drop_w = size * 0.18

    # Droplet teardrop shape
    drop_pts = []
    # Tip at top
    drop_pts.append((cx, drop_top_y))
    # Right bulge curve
    for deg in range(0, 185, 5):
        rad = math.radians(deg)
        x = cx + math.sin(rad) * drop_w
        # Bulge lower down
        y = (cy + size * 0.08) + math.cos(rad) * (drop_bottom_y - (cy + size * 0.08))
        drop_pts.append((x, y))
    
    # Left bulge curve
    for deg in range(180, 365, 5):
        rad = math.radians(deg)
        x = cx + math.sin(rad) * drop_w
        y = (cy + size * 0.08) + math.cos(rad) * (drop_bottom_y - (cy + size * 0.08))
        drop_pts.append((x, y))

    # Outer droplet glow
    draw.polygon(drop_pts, fill=(0, 240, 255, 220), outline=(108, 182, 200, 255))

    # Inner droplet gradient / fluid core
    inner_drop_w = drop_w * 0.78
    inner_pts = []
    inner_pts.append((cx, drop_top_y + size * 0.03))
    for deg in range(0, 365, 5):
        rad = math.radians(deg)
        x = cx + math.sin(rad) * inner_drop_w
        y = (cy + size * 0.10) + math.cos(rad) * ((drop_bottom_y - size * 0.03) - (cy + size * 0.10))
        inner_pts.append((x, y))
    draw.polygon(inner_pts, fill=(108, 182, 200, 255))

    # Droplet Specular Reflection Highlight (White crescent on upper-left)
    spec_w = inner_drop_w * 0.45
    spec_h = inner_drop_w * 0.70
    spec_cx = cx - inner_drop_w * 0.35
    spec_cy = cy + size * 0.06
    draw.ellipse([spec_cx - spec_w, spec_cy - spec_h, spec_cx + spec_w, spec_cy + spec_h], fill=(255, 255, 255, 210))

    return img

def main():
    root = Path(__file__).resolve().parent.parent
    assets_dir = root / "assets" / "images"
    assets_dir.mkdir(parents=True, exist_ok=True)

    master = draw_spiderman_water_logo(1024)

    # Save high-res master
    master_path = assets_dir / "app_icon_master.png"
    master.save(str(master_path), "PNG")
    print(f"[OK] Saved master to {master_path}")

    # Save 512x512 app_icon.png
    icon_512 = master.resize((512, 512), Image.Resampling.LANCZOS)
    icon_path = assets_dir / "app_icon.png"
    icon_512.save(str(icon_path), "PNG")
    print(f"[OK] Saved app_icon.png to {icon_path}")

    # Save 32x32 and 48x48
    master.resize((32, 32), Image.Resampling.LANCZOS).save(str(assets_dir / "app_icon_32.png"), "PNG")
    master.resize((48, 48), Image.Resampling.LANCZOS).save(str(assets_dir / "app_icon_48.png"), "PNG")

    # Save multi-res Windows ICO
    ico_sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_path = assets_dir / "app_icon.ico"
    master.save(str(ico_path), format="ICO", sizes=ico_sizes)
    print(f"[OK] Saved multi-resolution app_icon.ico to {ico_path}")

if __name__ == "__main__":
    main()
