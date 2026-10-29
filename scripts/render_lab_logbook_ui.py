"""
Renders a pixel-perfect, high-resolution UI/UX mockup synthesizing:
1. The Peter Parker 'LAB LOGBOOK v2.0' layout from user's screenshot.
2. The 'Spider-Sense' glowing reticle & tingling shockwave arcs.
3. The 'Ink & Thread' calm graphite palette from waterpop-ui-redesign.patch.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def render_lab_logbook():
    width = 1240
    height = 800
    
    # 1. Base Canvas - Warm Graphite Background (#111214)
    img = Image.new("RGBA", (width, height), (17, 18, 20, 255))
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_app_title = ImageFont.truetype("segoeuib.ttf", 16)
        font_title = ImageFont.truetype("segoeuib.ttf", 19)
        font_sub = ImageFont.truetype("segoeui.ttf", 12)
        font_hero_pct = ImageFont.truetype("segoeuib.ttf", 52)
        font_hero_stat = ImageFont.truetype("segoeuib.ttf", 15)
        font_card_head = ImageFont.truetype("segoeuib.ttf", 11)
        font_btn_bold = ImageFont.truetype("segoeuib.ttf", 13)
        font_btn_sub = ImageFont.truetype("segoeui.ttf", 11)
        font_metric_val = ImageFont.truetype("segoeuib.ttf", 22)
        font_metric_lbl = ImageFont.truetype("segoeuib.ttf", 10)
        font_badge = ImageFont.truetype("segoeuib.ttf", 11)
    except:
        font_app_title = font_title = font_sub = font_hero_pct = font_hero_stat = font_card_head = font_btn_bold = font_btn_sub = font_metric_val = font_metric_lbl = font_badge = ImageFont.load_default()

    # Ambient soft glow (Spider-Sense warm amber at top-left, calm cyan at top-right)
    ambient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    a_draw = ImageDraw.Draw(ambient)
    for r in range(350, 40, -30):
        alpha = int(14 * (1.0 - r / 350))
        a_draw.ellipse([300 - r, 300 - r, 300 + r, 300 + r], fill=(217, 165, 72, alpha))
        a_draw.ellipse([900 - r, 200 - r, 900 + r, 200 + r], fill=(108, 182, 200, alpha))
    img = Image.alpha_composite(img, ambient)
    draw = ImageDraw.Draw(img)

    # 2. Window Chrome & Header Bar
    # Window controls (macOS style / modern minimal)
    draw.ellipse([26, 24, 38, 36], fill=(235, 87, 87, 255))
    draw.ellipse([46, 24, 58, 36], fill=(242, 201, 76, 255))
    draw.ellipse([66, 24, 78, 36], fill=(39, 174, 96, 255))
    draw.text((94, 20), "Spider-Man Waterpop v2.0", fill=(141, 145, 153), font=font_app_title)

    # Top Right Controls: [Spidey Perch] and Status Dots
    draw.rounded_rectangle([width - 240, 16, width - 110, 46], radius=8, fill=(26, 29, 33), outline=(42, 46, 51), width=1)
    draw.text((width - 224, 23), "🕷️ Spidey Perch", fill=(214, 72, 63), font=font_btn_bold)
    
    # Status indicators
    draw.rounded_rectangle([width - 96, 16, width - 26, 46], radius=8, fill=(26, 29, 33), outline=(42, 46, 51), width=1)
    draw.ellipse([width - 82, 27, width - 74, 35], fill=(214, 72, 63))
    draw.ellipse([width - 66, 27, width - 58, 35], fill=(255, 255, 255))
    draw.ellipse([width - 50, 27, width - 42, 35], fill=(217, 165, 72))

    # Divider below window title
    draw.line([24, 58, width - 24, 58], fill=(31, 35, 39), width=1)

    # 3. Lab Logbook Subheader
    draw.ellipse([28, 76, 58, 106], fill=(214, 72, 63)) # PP Badge
    draw.text((37, 83), "PP", fill=(255, 255, 255), font=font_btn_bold)
    draw.text((70, 74), "LAB LOGBOOK", fill=(236, 235, 230), font=font_title)
    
    # Version badge
    draw.rounded_rectangle([214, 77, 252, 97], radius=4, fill=(42, 46, 51))
    draw.text((220, 80), "v2.0", fill=(141, 145, 153), font=font_badge)
    draw.text((70, 96), "Daily Osmosis & Hydration Metric", fill=(141, 145, 153), font=font_sub)

    # Center Spider-Sense status pill
    status_x = width // 2 - 110
    draw.rounded_rectangle([status_x, 74, status_x + 220, 104], radius=15, fill=(217, 165, 72, 35), outline=(217, 165, 72, 120), width=1)
    draw.ellipse([status_x + 14, 85, status_x + 22, 93], fill=(217, 165, 72))
    draw.text((status_x + 30, 81), "SPIDER-SENSE: ACTIVE", fill=(235, 185, 95), font=font_badge)

    # 4. Main Two-Column Layout
    col_gap = 20
    left_w = 680
    right_w = width - left_w - 48 - col_gap
    start_y = 126
    left_x = 24
    right_x = left_x + left_w + col_gap

    # ================= LEFT HERO: CORE FLUID LEVEL =================
    left_h = 640
    # Frosted flat card
    draw.rounded_rectangle([left_x, start_y, left_x + left_w, start_y + left_h], radius=16, fill=(24, 27, 31), outline=(42, 46, 51), width=1)
    
    # Card Header
    draw.ellipse([left_x + 24, start_y + 24, left_x + 32, start_y + 32], fill=(127, 200, 160)) # Green dot
    draw.text((left_x + 40, start_y + 21), "CORE FLUID LEVEL", fill=(141, 145, 153), font=font_card_head)
    
    # Streak badge (top-right of card)
    streak_bx = left_x + left_w - 150
    draw.rounded_rectangle([streak_bx, start_y + 16, streak_bx + 126, start_y + 44], radius=14, fill=(214, 72, 63, 30), outline=(214, 72, 63, 100), width=1)
    draw.text((streak_bx + 14, start_y + 23), "🔥 3 Day Streak", fill=(229, 138, 131), font=font_badge)

    # --- Central Spider-Sense & Water Chamber Hero ---
    ret_cx = left_x + left_w // 2
    ret_cy = start_y + 210
    ret_r = 110

    # Spider-Sense Golden Tingling Waves (Radiating shockwave arcs - iconic comic style!)
    for i, arc_r in enumerate([135, 152, 168]):
        alpha = int(240 - i * 70)
        draw.arc([ret_cx - arc_r, ret_cy - arc_r, ret_cx + arc_r, ret_cy + arc_r],
                 start=-135, end=-45, fill=(217, 165, 72, alpha), width=3)
        draw.arc([ret_cx - arc_r, ret_cy - arc_r, ret_cx + arc_r, ret_cy + arc_r],
                 start=-225, end=-135, fill=(217, 165, 72, alpha // 2), width=2)
        draw.arc([ret_cx - arc_r, ret_cy - arc_r, ret_cx + arc_r, ret_cy + arc_r],
                 start=-45, end=45, fill=(217, 165, 72, alpha // 2), width=2)

    # Base track groove
    draw.arc([ret_cx - ret_r, ret_cy - ret_r, ret_cx + ret_r, ret_cy + ret_r],
             start=0, end=360, fill=(35, 39, 45), width=16)

    # Bioluminescent Water Swirl Arc (60% / 1,500 ml)
    draw.arc([ret_cx - ret_r, ret_cy - ret_r, ret_cx + ret_r, ret_cy + ret_r],
             start=-90, end=126, fill=(108, 182, 200), width=16)

    # Center Typography
    draw.text((ret_cx - 52, ret_cy - 48), "60%", fill=(236, 235, 230), font=font_hero_pct)
    draw.text((ret_cx - 62, ret_cy + 16), "1,500 / 2,500 ml", fill=(193, 192, 186), font=font_hero_stat)
    draw.text((ret_cx - 68, ret_cy + 42), "Tap core or buttons to log", fill=(141, 145, 153), font=font_sub)

    # Big "YES, I DRANK 💧" Action Pill
    btn_w = 260
    btn_h = 48
    bx = left_x + (left_w - btn_w) // 2
    by = start_y + 365
    draw.rounded_rectangle([bx, by, bx + btn_w, by + btn_h], radius=24, fill=(214, 72, 63), outline=(226, 88, 79), width=1)
    draw.text((bx + 62, by + 14), "YES, I DRANK  💧", fill=(255, 255, 255), font=font_btn_bold)

    # 3 Quick-Log Cards (From screenshot: Quick Glass, Lab Flask, Hydro Canteen)
    cards_y = start_y + 440
    cw = (left_w - 48 - 24) // 3
    q_amounts = [
        ("+250ml", "Quick Glass"),
        ("+350ml", "Lab Flask"),
        ("+500ml", "Hydro Canteen")
    ]
    for i, (amt, lbl) in enumerate(q_amounts):
        cx = left_x + 24 + i * (cw + 12)
        draw.rounded_rectangle([cx, cards_y, cx + cw, cards_y + 80], radius=12, fill=(30, 34, 40), outline=(45, 50, 58), width=1)
        draw.text((cx + cw // 2 - 24, cards_y + 18), amt, fill=(236, 235, 230), font=font_btn_bold)
        draw.text((cx + cw // 2 - 34, cards_y + 42), lbl, fill=(141, 145, 153), font=font_btn_sub)

    # Custom amount row & Reset Day
    row_y = start_y + 545
    # Input box
    draw.rounded_rectangle([left_x + 24, row_y, left_x + 130, row_y + 38], radius=8, fill=(18, 20, 23), outline=(42, 46, 51), width=1)
    draw.text((left_x + 44, row_y + 10), "250 ml", fill=(236, 235, 230), font=font_sub)
    # Log button
    draw.rounded_rectangle([left_x + 140, row_y, left_x + 210, row_y + 38], radius=8, fill=(38, 43, 50), outline=(50, 56, 65), width=1)
    draw.text((left_x + 162, row_y + 10), "Log", fill=(236, 235, 230), font=font_btn_bold)
    # Reset Day
    draw.text((left_x + left_w - 130, row_y + 11), "🔄 Reset Day", fill=(141, 145, 153), font=font_sub)

    # ================= RIGHT COLUMN (3 Stacked Cards) =================
    # Card 1: DAILY THREAD MATRIX (7-Day Log)
    r1_h = 185
    draw.rounded_rectangle([right_x, start_y, right_x + right_w, start_y + r1_h], radius=16, fill=(24, 27, 31), outline=(42, 46, 51), width=1)
    draw.text((right_x + 22, start_y + 20), "🕸️ DAILY THREAD MATRIX", fill=(214, 72, 63), font=font_card_head)
    draw.text((right_x + right_w - 85, start_y + 20), "7-Day Log", fill=(141, 145, 153), font=font_card_head)

    # 7-Day Web Nodes (M, T, W, T, F, S, S)
    day_labels = ["M", "T", "W", "T", "F", "S", "S"]
    day_status = [True, True, True, False, False, False, False] # 3-day streak active
    node_y = start_y + 75
    node_spacing = (right_w - 44) // 7
    for i, (d, is_done) in enumerate(zip(day_labels, day_status)):
        nx = right_x + 24 + i * node_spacing + 12
        if is_done:
            draw.ellipse([nx - 16, node_y - 16, nx + 16, node_y + 16], fill=(214, 72, 63))
            draw.text((nx - 6, node_y - 8), "✓", fill=(255, 255, 255), font=font_btn_bold)
        else:
            draw.ellipse([nx - 16, node_y - 16, nx + 16, node_y + 16], fill=(35, 39, 45), outline=(50, 56, 65), width=1)
        draw.text((nx - 4, node_y + 26), d, fill=(141, 145, 153), font=font_card_head)

    draw.text((right_x + 22, start_y + 144), "Web threads connect consecutive hydration goals.", fill=(141, 145, 153), font=font_sub)

    # Card 2: OSMOSIS METRICS
    r2_y = start_y + r1_h + 16
    r2_h = 150
    draw.rounded_rectangle([right_x, r2_y, right_x + right_w, r2_y + r2_h], radius=16, fill=(24, 27, 31), outline=(42, 46, 51), width=1)
    draw.text((right_x + 22, r2_y + 20), "📊 OSMOSIS METRICS", fill=(108, 182, 200), font=font_card_head)

    # Dual mini-metric tiles
    tile_w = (right_w - 44 - 14) // 2
    tile_h = 75
    # Tile 1: Weekly Avg
    draw.rounded_rectangle([right_x + 22, r2_y + 50, right_x + 22 + tile_w, r2_y + 50 + tile_h], radius=10, fill=(30, 34, 40), outline=(45, 50, 58), width=1)
    draw.text((right_x + 36, r2_y + 60), "WEEKLY AVG", fill=(141, 145, 153), font=font_metric_lbl)
    draw.text((right_x + 36, r2_y + 80), "1.8 L", fill=(236, 235, 230), font=font_metric_val)

    # Tile 2: Peak Intake
    draw.rounded_rectangle([right_x + 22 + tile_w + 14, r2_y + 50, right_x + right_w - 22, r2_y + 50 + tile_h], radius=10, fill=(30, 34, 40), outline=(45, 50, 58), width=1)
    draw.text((right_x + 36 + tile_w + 14, r2_y + 60), "PEAK INTAKE", fill=(141, 145, 153), font=font_metric_lbl)
    draw.text((right_x + 36 + tile_w + 14, r2_y + 80), "2:15 PM", fill=(236, 235, 230), font=font_metric_val)

    # Card 3: LAB PARAMETERS
    r3_y = r2_y + r2_h + 16
    r3_h = left_h - (r1_h + 16 + r2_h + 16)
    draw.rounded_rectangle([right_x, r3_y, right_x + right_w, r3_y + r3_h], radius=16, fill=(24, 27, 31), outline=(42, 46, 51), width=1)
    draw.text((right_x + 22, r3_y + 20), "⚙️ LAB PARAMETERS", fill=(217, 165, 72), font=font_card_head)

    # Form parameters
    f_y = r3_y + 56
    draw.text((right_x + 22, f_y + 6), "Daily Target (mL)", fill=(193, 192, 186), font=font_sub)
    draw.rounded_rectangle([right_x + right_w - 110, f_y, right_x + right_w - 22, f_y + 32], radius=6, fill=(18, 20, 23), outline=(42, 46, 51), width=1)
    draw.text((right_x + right_w - 85, f_y + 7), "2,500", fill=(236, 235, 230), font=font_sub)

    f_y += 48
    draw.text((right_x + 22, f_y + 6), "Spider-Sense Interval", fill=(193, 192, 186), font=font_sub)
    draw.rounded_rectangle([right_x + right_w - 120, f_y, right_x + right_w - 22, f_y + 32], radius=6, fill=(18, 20, 23), outline=(42, 46, 51), width=1)
    draw.text((right_x + right_w - 105, f_y + 7), "30 Mins ▾", fill=(236, 235, 230), font=font_sub)

    f_y += 48
    draw.text((right_x + 22, f_y + 6), "Acoustic Audio FX", fill=(193, 192, 186), font=font_sub)
    # Checkbox
    draw.rounded_rectangle([right_x + right_w - 44, f_y + 4, right_x + right_w - 24, f_y + 24], radius=4, fill=(214, 72, 63))
    draw.text((right_x + right_w - 38, f_y + 5), "✓", fill=(255, 255, 255), font=font_btn_bold)

    # Save artifact
    out_dir = Path("C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "spidersense_lab_final_mockup.png"
    img.save(out_file)
    print(f"Rendered final Lab Logbook mockup to {out_file}")

if __name__ == "__main__":
    render_lab_logbook()
