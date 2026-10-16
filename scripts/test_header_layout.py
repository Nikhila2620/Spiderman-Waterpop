import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "test_2k"
FONTS_DIR = ROOT_DIR / "build" / "fonts"
BUILD_DIR.mkdir(parents=True, exist_ok=True)

FONT_INTER_REG = str(FONTS_DIR / "Inter.ttf")
FONT_INTER_BOLD = "segoeuib.ttf"
FONT_MONO_BOLD = str(FONTS_DIR / "JetBrainsMono-Bold.ttf")

W, H = 2560, 1440

def test_headers():
    test_cases = [
        ("CHAPTER 01 // OVERVIEW", "The Developer Problem & Vision"),
        ("CHAPTER 02 // UI ARCHITECTURE", "The Aquatic Liquid Glass Dashboard"),
        ("CHAPTER 03 // FLUID PHYSICS", "Simulated Fluid Dynamics & Quick Log"),
        ("CHAPTER 04 // PERSONALIZATION", "Custom Identity & System Behavior"),
        ("CHAPTER 05 // REMINDER ENGINE", "Smart Recurrence, Snooze & Retry"),
        ("CHAPTER 06 // SLEEP PROTECTION", "Configurable Overnight Quiet Hours"),
        ("CHAPTER 07 // WIN32 ENGINEERING", "Focus-Safe Companion Overlay"),
        ("STEP 05 // APPEARANCE", "Physics, Motion & Focus-Safe Architecture"),
        ("CHAPTER 08 // PRODUCTION RELEASE", "Packaging, Distribution & Open Source")
    ]

    font_tag = ImageFont.truetype(FONT_MONO_BOLD, 22)
    base_title_size = 46

    for idx, (tag_text, title_text) in enumerate(test_cases):
        img = Image.new("RGB", (W, 220), (7, 17, 30))
        draw = ImageDraw.Draw(img)

        # Header bar in 2K: from y=36 to y=164 (height = 128px)
        header_y1 = 36
        header_y2 = 164
        header_h = header_y2 - header_y1
        header_mid_y = header_y1 + header_h // 2
        header_rect = [60, header_y1, 2500, header_y2]

        draw.rounded_rectangle(header_rect, radius=18, fill=(13, 27, 46, 235), outline=(0, 240, 255, 90), width=2)

        # Dynamic pill width calculation
        tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
        tag_w = tag_bbox[2] - tag_bbox[0]
        tag_h = tag_bbox[3] - tag_bbox[1]
        
        pill_w = tag_w + 40
        pill_h = 56
        pill_x1 = 88
        pill_y1 = header_mid_y - pill_h // 2
        pill_rect = [pill_x1, pill_y1, pill_x1 + pill_w, pill_y1 + pill_h]

        draw.rounded_rectangle(pill_rect, radius=12, fill=(12, 54, 78), outline=(0, 240, 255), width=2)
        # Center text inside pill
        tag_draw_x = pill_x1 + (pill_w - tag_w) // 2
        tag_draw_y = pill_y1 + (pill_h - tag_h) // 2 - 2
        draw.text((tag_draw_x, tag_draw_y), tag_text, fill=(0, 240, 255), font=font_tag)

        # Title calculation with auto-fitting so it never collides or overflows
        title_start_x = pill_x1 + pill_w + 36
        max_title_w = 2460 - title_start_x
        
        title_font_size = base_title_size
        title_str = title_text.upper()
        font_title = ImageFont.truetype(FONT_INTER_BOLD, title_font_size)
        title_bbox = draw.textbbox((0, 0), title_str, font=font_title)
        
        while (title_bbox[2] - title_bbox[0]) > max_title_w and title_font_size > 26:
            title_font_size -= 2
            font_title = ImageFont.truetype(FONT_INTER_BOLD, title_font_size)
            title_bbox = draw.textbbox((0, 0), title_str, font=font_title)

        title_w = title_bbox[2] - title_bbox[0]
        title_h = title_bbox[3] - title_bbox[1]
        title_draw_y = header_mid_y - (title_h // 2) - 4

        draw.text((title_start_x, title_draw_y), title_str, fill=(255, 255, 255), font=font_title)

        out_path = BUILD_DIR / f"test_header_{idx}.png"
        img.save(out_path)
        print(f"Case {idx}: pill_w={pill_w}, title_size={title_font_size}, title_w={title_w}/{max_title_w}, title_y={title_draw_y}")

if __name__ == "__main__":
    test_headers()
