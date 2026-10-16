"""
Award-Winning Kinetic Typography & Video Stabilization Engine.
Builds an editorial-grade Apple-style product demo video with:
- 2-pass motion-stabilized footage
- Editorial kinetic typography with multi-font pairing (Inter + JetBrains Mono)
- Accent keyword highlights, code badges, and dark aquatic glass pills
- Smooth mathematical upward glide animation on phrase entries
- Exact voice-over synchronization
"""
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "demo_video"
DIST_DIR = ROOT_DIR / "dist"
FONTS_DIR = ROOT_DIR / "build" / "fonts"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Font definitions
FONT_INTER_REG = str(FONTS_DIR / "Inter.ttf")
FONT_INTER_BOLD = "segoeuib.ttf"  # Windows Segoe UI Bold as punchy bold pairing
FONT_MONO_BOLD = str(FONTS_DIR / "JetBrainsMono-Bold.ttf")

# Editorial kinetic captions specification (18 scenes)
KINETIC_CAPTIONS = [
    {
        "id": "cap_01",
        "start": 0.10,
        "end": 5.62,
        "tag": "DEEP WORK & FLOW",
        "subtag": "The Developer Problem",
        "tokens": [
            ("When you are deep in the ", "normal"),
            ("FLOW STATE", "highlight_cyan"),
            (", staying ", "normal"),
            ("HYDRATED", "highlight_mint"),
            (" is often forgotten.", "normal")
        ]
    },
    {
        "id": "cap_02",
        "start": 5.62,
        "end": 12.46,
        "tag": "THE NOTIFICATION PROBLEM",
        "subtag": "Legacy Tools",
        "tokens": [
            ("Traditional reminder apps are either ", "normal"),
            ("ANNOYING", "highlight_azure"),
            (", ", "normal"),
            ("INTRUSIVE", "highlight_cyan"),
            (", or get lost in notification clutter.", "normal")
        ]
    },
    {
        "id": "cap_03",
        "start": 12.46,
        "end": 21.54,
        "tag": "THE SOLUTION",
        "subtag": "Product Introduction",
        "tokens": [
            ("Introducing ", "normal"),
            ("SPIDER-MAN WATER BUDDY", "highlight_cyan"),
            (" — native companion with ", "normal"),
            ("AQUATIC LIQUID GLASS", "highlight_mint"),
            (" UI.", "normal")
        ]
    },
    {
        "id": "cap_04",
        "start": 22.50,
        "end": 26.74,
        "tag": "UI REDESIGN",
        "subtag": "Main Dashboard",
        "tokens": [
            ("At the core of the experience is the redesigned ", "normal"),
            ("AQUATIC DASHBOARD", "highlight_cyan"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_05",
        "start": 26.74,
        "end": 36.24,
        "tag": "FLUID PHYSICS",
        "subtag": "Native Rendering Engine",
        "tokens": [
            ("Built with ", "normal"),
            ("PySide6", "code"),
            (" and ", "normal"),
            ("QPainter", "code"),
            (", featuring a ", "normal"),
            ("LIVE FLUID RESERVOIR", "highlight_cyan"),
            (" with ", "normal"),
            ("SINUSOIDAL WAVE DYNAMICS", "highlight_mint"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_06",
        "start": 36.24,
        "end": 44.91,
        "tag": "HYDRATION TELEMETRY",
        "subtag": "Interactive Logging",
        "tokens": [
            ("Track your ", "normal"),
            ("DAILY HYDRATION %", "highlight_mint"),
            (" at a glance and log water instantly with quick pills like ", "normal"),
            ("+250 ml", "code"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_07",
        "start": 45.88,
        "end": 50.24,
        "tag": "GENERAL SETTINGS",
        "subtag": "User Customization",
        "tokens": [
            ("The General settings page puts ", "normal"),
            ("PERSONALIZATION", "highlight_cyan"),
            (" front and center.", "normal")
        ]
    },
    {
        "id": "cap_08",
        "start": 50.24,
        "end": 59.39,
        "tag": "SYSTEM INTEGRATION",
        "subtag": "Identity & Windows Startup",
        "tokens": [
            ("Customize your companion identity (", "normal"),
            ("Nikhila", "highlight_cyan"),
            ("), daily targets, and enable ", "normal"),
            ("WINDOWS STARTUP", "highlight_white"),
            (" integration.", "normal")
        ]
    },
    {
        "id": "cap_09",
        "start": 59.39,
        "end": 64.52,
        "tag": "WINDOW BEHAVIOR",
        "subtag": "Layering Architecture",
        "tokens": [
            ("Best of all, gives you full control over ", "normal"),
            ("ALWAYS-ON-TOP", "highlight_mint"),
            (" desktop window layering.", "normal")
        ]
    },
    {
        "id": "cap_10",
        "start": 65.47,
        "end": 69.35,
        "tag": "REMINDER ENGINE",
        "subtag": "Productivity Design",
        "tokens": [
            ("The reminder engine is engineered for ", "normal"),
            ("REAL PRODUCTIVITY", "highlight_cyan"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_11",
        "start": 69.35,
        "end": 79.01,
        "tag": "INTERVALS & SNOOZE",
        "subtag": "Flexible Timers",
        "tokens": [
            ("Set custom recurrence intervals, configure ", "normal"),
            ("5 / 10 / 15-min", "code"),
            (" snoozes, and intelligent ", "normal"),
            ("RETRY-IF-NOT-YET", "highlight_mint"),
            (" logic.", "normal")
        ]
    },
    {
        "id": "cap_12",
        "start": 79.01,
        "end": 86.77,
        "tag": "QUIET HOURS",
        "subtag": "Sleep & Focus Protection",
        "tokens": [
            ("Configurable ", "normal"),
            ("QUIET HOURS", "highlight_azure"),
            (" automatically mute reminders overnight so your ", "normal"),
            ("SLEEP & FOCUS", "highlight_white"),
            (" are protected.", "normal")
        ]
    },
    {
        "id": "cap_13",
        "start": 87.73,
        "end": 92.30,
        "tag": "DESKTOP PRESENCE",
        "subtag": "Screen Placement",
        "tokens": [
            ("The companion hangs effortlessly from the ", "normal"),
            ("TOP-RIGHT CORNER", "highlight_cyan"),
            (" of your display.", "normal")
        ]
    },
    {
        "id": "cap_14",
        "start": 92.30,
        "end": 100.13,
        "tag": "PHYSICS & MOTION",
        "subtag": "Natural Interaction",
        "tokens": [
            ("Features natural ", "normal"),
            ("PENDULUM SWINGING", "highlight_white"),
            (", ", "normal"),
            ("SPIDER-SENSE", "highlight_cyan"),
            (" proximity reaction, and celebrations.", "normal")
        ]
    },
    {
        "id": "cap_15",
        "start": 100.13,
        "end": 110.81,
        "tag": "WIN32 ENGINEERING",
        "subtag": "Non-Focus-Stealing Architecture",
        "tokens": [
            ("Crucially, using native Win32 APIs and ", "normal"),
            ("WS_EX_NOACTIVATE", "code"),
            (", it ", "normal"),
            ("NEVER STEALS KEYBOARD FOCUS", "highlight_mint"),
            (" while typing.", "normal")
        ]
    },
    {
        "id": "cap_16",
        "start": 111.76,
        "end": 120.87,
        "tag": "CORE ARCHITECTURE",
        "subtag": "Offline & Private",
        "tokens": [
            ("Engineered with ", "normal"),
            ("PySide6", "code"),
            (", native ", "normal"),
            ("Win32 ctypes", "code"),
            (", atomic JSON writes, and ", "normal"),
            ("ZERO CLOUD DEPENDENCIES", "highlight_mint"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_17",
        "start": 120.87,
        "end": 127.91,
        "tag": "ENGINEERING BENCHMARK",
        "subtag": "Production Standards",
        "tokens": [
            ("Proving desktop utilities can be ", "normal"),
            ("HIGH-PERFORMANCE", "highlight_cyan"),
            (", ", "normal"),
            ("ROBUST", "highlight_azure"),
            (", and ", "normal"),
            ("DELIGHTFUL", "highlight_mint"),
            (".", "normal")
        ]
    },
    {
        "id": "cap_18",
        "start": 127.91,
        "end": 130.67,
        "tag": "OPEN SOURCE",
        "subtag": "GitHub Release",
        "tokens": [
            ("Explore the source and star the project on ", "normal"),
            ("GITHUB", "highlight_mint"),
            (" today!", "normal")
        ]
    }
]


def render_kinetic_cards():
    print("\n[STEP 1] Rendering Kinetic Typography Transparent Overlay Cards...")
    W, H = 1920, 1080

    font_tag = ImageFont.truetype(FONT_MONO_BOLD, 19)
    font_subtag = ImageFont.truetype(FONT_INTER_REG, 17)
    font_body = ImageFont.truetype(FONT_INTER_REG, 28)
    font_bold = ImageFont.truetype(FONT_INTER_BOLD, 28)
    font_code = ImageFont.truetype(FONT_MONO_BOLD, 25)

    card_paths = []

    for item in KINETIC_CAPTIONS:
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 1. Compute text width for centering
        # Measure line pieces
        line_w = 0
        piece_metrics = []
        for text, style in item["tokens"]:
            if style == "code":
                f = font_code
                bbox = draw.textbbox((0, 0), text, font=f)
                pw = (bbox[2] - bbox[0]) + 20  # + padding for code pill
            elif "highlight" in style:
                f = font_bold
                bbox = draw.textbbox((0, 0), text, font=f)
                pw = bbox[2] - bbox[0]
            else:
                f = font_body
                bbox = draw.textbbox((0, 0), text, font=f)
                pw = bbox[2] - bbox[0]
            piece_metrics.append((text, style, f, pw))
            line_w += pw

        # Dynamic card size
        card_w = max(980, min(1560, line_w + 100))
        card_h = 120
        card_x = (W - card_w) // 2
        card_y = 920

        # Draw soft glass drop shadow
        shadow_rect = [card_x + 6, card_y + 8, card_x + card_w + 6, card_y + card_h + 8]
        draw.rounded_rectangle(shadow_rect, radius=20, fill=(0, 0, 0, 140))

        # Draw aquatic glass container
        card_rect = [card_x, card_y, card_x + card_w, card_y + card_h]
        draw.rounded_rectangle(card_rect, radius=18, fill=(7, 17, 30, 230), outline=(0, 240, 255, 120), width=2)

        # Top micro header: Tag badge + Subtag
        tag_text = item["tag"]
        tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
        tag_w = tag_bbox[2] - tag_bbox[0] + 24
        draw.rounded_rectangle([card_x + 32, card_y + 16, card_x + 32 + tag_w, card_y + 44], radius=7, fill=(0, 240, 255, 35), outline=(0, 240, 255, 140), width=1)
        draw.text((card_x + 44, card_y + 19), tag_text, fill=(0, 240, 255), font=font_tag)

        # Subtag description
        draw.text((card_x + 32 + tag_w + 16, card_y + 20), item["subtag"], fill=(168, 196, 216), font=font_subtag)

        # Content line: center text horizontally in the card
        content_start_x = card_x + (card_w - line_w) // 2
        cur_x = content_start_x
        text_y = card_y + 64

        for text, style, font, pw in piece_metrics:
            if style == "code":
                # Draw monospaced code pill
                pill_rect = [cur_x, text_y - 4, cur_x + pw, text_y + 36]
                draw.rounded_rectangle(pill_rect, radius=6, fill=(10, 132, 255, 45), outline=(0, 240, 255, 170), width=1)
                draw.text((cur_x + 10, text_y), text, fill=(0, 240, 255), font=font)
                cur_x += pw
            elif style == "highlight_cyan":
                draw.text((cur_x, text_y), text, fill=(0, 240, 255), font=font)
                cur_x += pw
            elif style == "highlight_mint":
                draw.text((cur_x, text_y), text, fill=(0, 230, 153), font=font)
                cur_x += pw
            elif style == "highlight_azure":
                draw.text((cur_x, text_y), text, fill=(56, 189, 248), font=font)
                cur_x += pw
            elif style == "highlight_white":
                draw.text((cur_x, text_y), text, fill=(255, 255, 255), font=font)
                cur_x += pw
            else:
                draw.text((cur_x, text_y), text, fill=(240, 246, 252), font=font)
                cur_x += pw

        card_file = BUILD_DIR / f"{item['id']}_card.png"
        img.save(card_file)
        item["card_path"] = card_file
        card_paths.append(card_file)
        print(f"  -> Rendered {card_file.name}")

    print("[SUCCESS] All 18 kinetic typography cards rendered!")
    return card_paths


def build_stabilized_kinetic_video():
    print("\n[STEP 2] Assembling Stabilized Footage with Kinetic Typography...")
    stab_base = BUILD_DIR / "stabilized_base.mp4"
    if not stab_base.exists():
        raise FileNotFoundError(f"Stabilized base {stab_base} not found!")

    final_output = DIST_DIR / "SpiderManWaterBuddy-LinkedIn-Demo-Stabilized.mp4"

    # Build FFmpeg filtergraph overlay chain
    # We will overlay each of the 18 cards with a 0.35s upward glide animation
    inputs = ["-i", str(stab_base)]
    filter_chains = []

    last_out = "[0:v]"
    for idx, item in enumerate(KINETIC_CAPTIONS):
        card_path = item["card_path"]
        inputs.extend(["-i", str(card_path)])
        
        in_idx = idx + 1
        out_lbl = f"[v{idx}]" if idx < len(KINETIC_CAPTIONS) - 1 else "[v_final]"

        start_t = item["start"]
        end_t = item["end"]

        # 0.35s upward glide: starts at y=14, glides to y=0 smoothly
        glide_expr = f"if(lt(t-{start_t:.2f},0.35),14*(1-(t-{start_t:.2f})/0.35),0)"
        enable_expr = f"between(t,{start_t:.2f},{end_t:.2f})"

        filter_step = f"{last_out}[{in_idx}:v]overlay=x=0:y='{glide_expr}':enable='{enable_expr}':format=auto{out_lbl}"
        filter_chains.append(filter_step)
        last_out = out_lbl

    filter_complex = ";".join(filter_chains)

    cmd = [
        FFMPEG_EXE, "-y",
        *inputs,
        "-filter_complex", filter_complex,
        "-map", "[v_final]",
        "-map", "0:a",
        "-c:v", "libx264", "-preset", "medium", "-crf", "18",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(final_output)
    ]

    print("\n[STEP 3] Rendering Final Master Video...")
    subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

    size_mb = final_output.stat().st_size / (1024 * 1024)
    print("\n==================================================")
    print(" STABILIZED KINETIC DEMO COMPLETED SUCCESSFULLY!")
    print(f" File:     {final_output}")
    print(f" Size:     {size_mb:.2f} MB")
    print(f" Format:   1080p 16:9 MP4 (30 FPS, H.264/AAC)")
    print("==================================================")
    return final_output


if __name__ == "__main__":
    start = time.time()
    render_kinetic_cards()
    out = build_stabilized_kinetic_video()
    print(f"Workflow finished in {time.time() - start:.1f} seconds.")
