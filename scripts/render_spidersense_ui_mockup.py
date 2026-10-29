"""
Renders a pixel-perfect, high-resolution UI/UX reference mockup for
Spider-Man Water Buddy v2.0 (Spider-Sense Minimal Edition).
"""
import math
import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

def create_spidersense_ui():
    width = 1200
    height = 760
    
    # 1. Base Image - Deep Obsidian Noir
    img = Image.new("RGBA", (width, height), (12, 15, 23, 255))
    draw = ImageDraw.Draw(img)
    
    # Fonts
    try:
        font_title = ImageFont.truetype("segoeui.ttf", 26)
        font_header = ImageFont.truetype("segoeuib.ttf", 20)
        font_sub = ImageFont.truetype("segoeui.ttf", 13)
        font_hero_num = ImageFont.truetype("segoeuib.ttf", 46)
        font_hero_sub = ImageFont.truetype("segoeui.ttf", 14)
        font_btn = ImageFont.truetype("segoeuib.ttf", 15)
        font_badge = ImageFont.truetype("segoeuib.ttf", 11)
        font_nav = ImageFont.truetype("segoeui.ttf", 14)
        font_nav_active = ImageFont.truetype("segoeuib.ttf", 14)
    except:
        font_title = font_header = font_sub = font_hero_num = font_hero_sub = font_btn = font_badge = font_nav = font_nav_active = ImageFont.load_default()

    # Subtle ambient gradient / glow in background
    # Soft warm spider-sense aura at top right
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    o_draw = ImageDraw.Draw(overlay)
    
    # Spider-sense golden aura radial blur in background
    for r in range(350, 50, -30):
        alpha = int(12 * (1.0 - r / 350))
        o_draw.ellipse([800 - r, 200 - r, 800 + r, 200 + r], fill=(255, 174, 0, alpha))
        
    # Soft crimson aura at bottom left
    for r in range(300, 50, -30):
        alpha = int(10 * (1.0 - r / 300))
        o_draw.ellipse([250 - r, 600 - r, 250 + r, 600 + r], fill=(230, 36, 69, alpha))
        
    img = Image.alpha_composite(img, overlay)
    draw = ImageDraw.Draw(img)

    # 2. Left Sidebar Navigation (Minimalist & Sleek)
    sidebar_w = 240
    sidebar_rect = [0, 0, sidebar_w, height]
    draw.rectangle(sidebar_rect, fill=(16, 20, 30, 255))
    draw.line([sidebar_w, 0, sidebar_w, height], fill=(255, 255, 255, 15), width=1)
    
    # App Logo / Title
    draw.ellipse([30, 32, 54, 56], fill=(230, 36, 69, 255)) # Crimson dot / emblem
    draw.ellipse([37, 39, 47, 49], fill=(255, 174, 0, 255)) # Spider-sense golden core
    draw.text((66, 30), "WATER BUDDY", fill=(245, 247, 250), font=font_header)
    draw.text((66, 52), "Spider-Sense Edition v2.0", fill=(140, 155, 180), font=font_sub)
    
    # Nav items
    nav_items = [
        ("⚡ Overview", True),
        ("💧 Hydration Log", False),
        ("⏰ Reminders & Quiet", False),
        ("🎨 Spider Companion", False),
        ("📊 History & Streaks", False),
        ("⚙️ Settings", False)
    ]
    ny = 110
    for label, is_active in nav_items:
        if is_active:
            # Active pill
            draw.rounded_rectangle([20, ny, sidebar_w - 20, ny + 42], radius=10, fill=(230, 36, 69, 35))
            draw.line([20, ny + 8, 20, ny + 34], fill=(230, 36, 69, 255), width=3)
            draw.text((38, ny + 11), label, fill=(255, 255, 255), font=font_nav_active)
        else:
            draw.text((38, ny + 11), label, fill=(145, 160, 185), font=font_nav)
        ny += 52

    # Bottom Profile in Sidebar
    draw.rounded_rectangle([20, height - 80, sidebar_w - 20, height - 24], radius=12, fill=(24, 30, 45, 200), outline=(255, 255, 255, 15), width=1)
    draw.ellipse([32, height - 68, 64, height - 36], fill=(230, 36, 69, 255))
    draw.text([42, height - 62], "🕷️", fill=(255, 255, 255), font=font_sub)
    draw.text([74, height - 66], "Peter Parker", fill=(245, 247, 250), font=font_nav_active)
    draw.text([74, height - 48], "Daily Goal: 2,000 ml", fill=(140, 155, 180), font=font_sub)

    # 3. Main Content Area
    cx = sidebar_w + 36
    cy = 32
    
    # Header Area
    draw.text((cx, cy), "Hydration Command", fill=(255, 255, 255), font=font_title)
    draw.text((cx, cy + 34), "Smooth, minimal tracking with real-time Spider-Sense awareness", fill=(145, 160, 185), font=font_sub)
    
    # Spider-Sense Status Pill (Top Right)
    badge_x = width - 260
    draw.rounded_rectangle([badge_x, cy + 4, width - 36, cy + 40], radius=18, fill=(255, 174, 0, 25), outline=(255, 174, 0, 120), width=1)
    draw.ellipse([badge_x + 14, cy + 18, badge_x + 22, cy + 26], fill=(255, 174, 0, 255)) # Pulsing dot
    draw.text((badge_x + 30, cy + 13), "SPIDER-SENSE: ACTIVE", fill=(255, 190, 40), font=font_badge)

    # 4. Hero Dashboard Card: Spider-Sense Hydration Chamber (Minimal, Smooth, No Clutter)
    hero_y = 96
    hero_w = width - sidebar_w - 72
    hero_h = 360
    
    # Soft glass card background
    draw.rounded_rectangle([cx, hero_y, cx + hero_w, hero_y + hero_h], radius=20, fill=(20, 25, 38, 240), outline=(255, 255, 255, 20), width=1)

    # Left: Spider-Sense Circular Reticle & Water Level
    reticle_cx = cx + 220
    reticle_cy = hero_y + 180
    reticle_r = 115
    
    # Spider-Sense Tingling Curved Arcs (Above Reticle - Iconic Comic Spider-Sense!)
    for i, arc_r in enumerate([135, 150, 165]):
        alpha = int(220 - i * 60)
        # Golden tingling arc
        draw.arc([reticle_cx - arc_r, reticle_cy - arc_r, reticle_cx + arc_r, reticle_cy + arc_r], 
                 start=-130, end=-50, fill=(255, 174, 0, alpha), width=3)
        # Symmetrical arc
        draw.arc([reticle_cx - arc_r, reticle_cy - arc_r, reticle_cx + arc_r, reticle_cy + arc_r], 
                 start=-220, end=-140, fill=(255, 174, 0, alpha // 2), width=2)
                 
    # Base circular track (Dark smooth groove)
    draw.arc([reticle_cx - reticle_r, reticle_cy - reticle_r, reticle_cx + reticle_r, reticle_cy + reticle_r],
             start=0, end=360, fill=(35, 42, 60), width=14)
             
    # Progress Arc (Glowing Bioluminescent Water Blue: 65% / 1300 ml)
    draw.arc([reticle_cx - reticle_r, reticle_cy - reticle_r, reticle_cx + reticle_r, reticle_cy + reticle_r],
             start=-90, end=144, fill=(0, 216, 246), width=14)
             
    # Center Telemetry
    draw.text((reticle_cx - 65, reticle_cy - 40), "1,300", fill=(255, 255, 255), font=font_hero_num)
    draw.text((reticle_cx - 48, reticle_cy + 16), "OF 2,000 ML", fill=(140, 155, 180), font=font_hero_sub)
    draw.text((reticle_cx - 40, reticle_cy + 38), "65% GOAL", fill=(0, 216, 246), font=font_badge)

    # Right: Minimal Hydration Controls & Action Area
    action_x = cx + 460
    draw.text((action_x, hero_y + 40), "HYDRATION COMPLIANCE", fill=(140, 155, 180), font=font_badge)
    draw.text((action_x, hero_y + 60), "Spider-Sense is Optimal", fill=(245, 247, 250), font=font_header)
    draw.text((action_x, hero_y + 90), "Next scheduled hydration prompt in 24 minutes.\nYou're on track to keep your web fluid fully synthesized.", fill=(145, 160, 185), font=font_sub)

    # Primary Action Button: "YES, I DRANK 💧" (Smooth Crimson Velvet Pill)
    btn_y = hero_y + 175
    btn_w = 260
    btn_h = 52
    draw.rounded_rectangle([action_x, btn_y, action_x + btn_w, btn_y + btn_h], radius=26, fill=(230, 36, 69, 255))
    draw.text((action_x + 48, btn_y + 16), "YES, I DRANK  💧", fill=(255, 255, 255), font=font_btn)

    # Cooldown Status & Chip Selection
    draw.text((action_x, btn_y + 70), "Quick Log Chips:", fill=(140, 155, 180), font=font_sub)
    chips = ["150 ml", "250 ml (Default)", "350 ml", "500 ml"]
    ch_x = action_x
    for i, ch in enumerate(chips):
        is_sel = (i == 1)
        bg = (230, 36, 69, 45) if is_sel else (30, 36, 52, 200)
        border = (230, 36, 69, 180) if is_sel else (255, 255, 255, 20)
        tc = (255, 255, 255) if is_sel else (145, 160, 185)
        ch_w = len(ch) * 8 + 18
        draw.rounded_rectangle([ch_x, btn_y + 96, ch_x + ch_w, btn_y + 126], radius=15, fill=bg, outline=border, width=1)
        draw.text((ch_x + 9, btn_y + 104), ch, fill=tc, font=font_badge)
        ch_x += ch_w + 8

    # 5. Bottom Dual Cards: Streak Achievement & Spider Companion
    bottom_y = hero_y + hero_h + 20
    card_w = (hero_w - 20) // 2
    card_h = 195
    
    # Left Card: Streak Engine & Web Shield
    draw.rounded_rectangle([cx, bottom_y, cx + card_w, bottom_y + card_h], radius=18, fill=(20, 25, 38, 240), outline=(255, 255, 255, 20), width=1)
    draw.text((cx + 24, bottom_y + 22), "STREAK & ACHIEVEMENTS", fill=(140, 155, 180), font=font_badge)
    draw.text((cx + 24, bottom_y + 44), "🔥 5-Day Hydration Streak!", fill=(255, 255, 255), font=font_header)
    draw.text((cx + 24, bottom_y + 76), "Personal Best: 12 days  •  Total Goal Days: 38", fill=(145, 160, 185), font=font_sub)
    
    # Web Shield Indicator
    draw.rounded_rectangle([cx + 24, bottom_y + 115, cx + card_w - 24, bottom_y + 165], radius=12, fill=(255, 174, 0, 18), outline=(255, 174, 0, 80), width=1)
    draw.text((cx + 40, bottom_y + 128), "🛡️ Web Shield Ready", fill=(255, 190, 40), font=font_nav_active)
    draw.text((cx + 40, bottom_y + 146), "Protects your streak if you miss 1 day this week", fill=(145, 160, 185), font=font_badge)

    # Right Card: Desktop Companion & Spider-Sense Tingle
    card2_x = cx + card_w + 20
    draw.rounded_rectangle([card2_x, bottom_y, card2_x + card_w, bottom_y + card_h], radius=18, fill=(20, 25, 38, 240), outline=(255, 255, 255, 20), width=1)
    draw.text((card2_x + 24, bottom_y + 22), "COMPANION BEHAVIOR", fill=(140, 155, 180), font=font_badge)
    draw.text((card2_x + 24, bottom_y + 44), "Spider-Sense Desktop Overlay", fill=(255, 255, 255), font=font_header)
    draw.text((card2_x + 24, bottom_y + 76), "Always-on-top, click-through overlay with 4-phase web swing.\nHotkey: Ctrl + Alt + W to toggle interaction.", fill=(145, 160, 185), font=font_sub)

    # Quick toggle buttons
    draw.rounded_rectangle([card2_x + 24, bottom_y + 125, card2_x + 160, bottom_y + 165], radius=10, fill=(30, 36, 52, 220), outline=(255, 255, 255, 20), width=1)
    draw.text((card2_x + 40, bottom_y + 137), "Remind Me Now", fill=(255, 255, 255), font=font_badge)
    
    draw.rounded_rectangle([card2_x + 172, bottom_y + 125, card2_x + 308, bottom_y + 165], radius=10, fill=(30, 36, 52, 220), outline=(255, 255, 255, 20), width=1)
    draw.text((card2_x + 188, bottom_y + 137), "Hide Overlay", fill=(145, 160, 185), font=font_badge)

    # Save output
    out_dir = Path("C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "spidersense_v2_ui_reference.png"
    img.save(out_path)
    print(f"Successfully generated reference UI image at {out_path}")

if __name__ == "__main__":
    create_spidersense_ui()
