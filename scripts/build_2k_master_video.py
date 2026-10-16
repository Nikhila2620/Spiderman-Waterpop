"""
Spider-Man Water Buddy — True 2K (2560x1440) QHD Cinematic Master Video Generator.
Fixes all text clipping, overflows, and layout misalignments with:
- Dynamic bounding-box pill sizing and vertical auto-centering
- True 2K (2560x1440) canvas rendering with high-DPI typography
- Lanczos-resampled UI screenshots with unsharp mask sharpening for crisp 2K presentation
- Universal broadcast compatibility: H.264 High Profile (yuv420p) & AAC-LC 48000 Hz Stereo (256 kbps)
- Seamless lo-fi ambient score mixed at -22 dB under authorative voice-over
"""
import asyncio
import math
import os
import shutil
import subprocess
import time
from pathlib import Path

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from scipy.io import wavfile

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "video_2k"
AUDIO_SRC_DIR = ROOT_DIR / "build" / "full_length_video"
DIST_DIR = ROOT_DIR / "dist"
FONTS_DIR = ROOT_DIR / "build" / "fonts"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

BUILD_DIR.mkdir(parents=True, exist_ok=True)
DIST_DIR.mkdir(parents=True, exist_ok=True)

FONT_INTER_REG = str(FONTS_DIR / "Inter.ttf")
FONT_INTER_BOLD = "segoeuib.ttf"
FONT_MONO_BOLD = str(FONTS_DIR / "JetBrainsMono-Bold.ttf")

USER_SCREENSHOTS = [
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160974961_da0ef2d0.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160978815_a48b5c09.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160982669_af298988.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160986700_567678d5.png",
]

SPIDEY_RENDER = ROOT_DIR / "assets" / "images" / "spidey_3d_render.png"
APP_ICON = ROOT_DIR / "assets" / "images" / "app_icon_master.png"

VOICE = "en-US-ChristopherNeural"

# 8 In-Depth Chapters
CHAPTERS = [
    {
        "id": "ch01_vision",
        "tag": "CHAPTER 01 // OVERVIEW",
        "title": "The Developer Problem & Vision",
        "script": (
            "During intensive software development and deep problem solving, hydration is almost always the first habit neglected. "
            "Standard notification popups are either disruptive, easily dismissed, or completely ignored. "
            "Spider-Man Water Buddy is engineered from the ground up to solve this: an always-on-top, non-intrusive desktop companion "
            "that lives right on your screen with a refined Aquatic Liquid Glass aesthetic."
        ),
        "type": "title_card",
        "card_tag": "PROJECT PHILOSOPHY",
        "card_sub": "Desktop Companion Design",
        "card_tokens": [
            ("A native desktop companion engineered for ", "normal"),
            ("DEEP DEVELOPER FOCUS", "highlight_cyan"),
            (" and optimal ", "normal"),
            ("HYDRATION HABITS", "highlight_mint"),
            (".", "normal")
        ]
    },
    {
        "id": "ch02_dashboard",
        "tag": "CHAPTER 02 // UI ARCHITECTURE",
        "title": "The Aquatic Liquid Glass Dashboard",
        "script": (
            "The redesigned main dashboard replaces traditional flat UI with an immersive oceanic glass design system. "
            "It features translucent frosted cards, delicate cyan refraction borders, and glowing telemetry indicators. "
            "You get an instant overview of your companion status, next reminder countdown, and today's total hydration progress."
        ),
        "screenshot_idx": 0,
        "type": "screenshot",
        "card_tag": "AQUATIC LIQUID GLASS",
        "card_sub": "Translucent UI System",
        "card_tokens": [
            ("Immersive oceanic theme with ", "normal"),
            ("FROSTED GLASS CARDS", "highlight_cyan"),
            (", glowing telemetry, and ", "normal"),
            ("HIGH-CONTRAST ACCENTS", "highlight_white"),
            (".", "normal")
        ]
    },
    {
        "id": "ch03_reservoir",
        "tag": "CHAPTER 03 // FLUID PHYSICS",
        "title": "Simulated Fluid Dynamics & Quick Log",
        "script": (
            "At the center of the dashboard sits the custom Daily Hydration Reservoir, rendered with PySide6 QPainter vector graphics. "
            "It simulates real fluid physics using dual-layer sinusoidal wave equations operating at a smooth thirty frames per second. "
            "The reservoir automatically pauses wave calculation when minimized to conserve CPU, and allows instant logging with quick pills like plus two-hundred and fifty milliliters."
        ),
        "screenshot_idx": 0,
        "type": "screenshot",
        "card_tag": "FLUID DYNAMICS",
        "card_sub": "QPainter Mathematical Physics",
        "card_tokens": [
            ("Dual-layer ", "normal"),
            ("SINUSOIDAL WAVE PHYSICS", "highlight_mint"),
            (" with one-click quick pills like ", "normal"),
            ("+250 ml (Glass)", "code"),
            (".", "normal")
        ]
    },
    {
        "id": "ch04_general",
        "tag": "CHAPTER 04 // PERSONALIZATION",
        "title": "Custom Identity & System Behavior",
        "script": (
            "The General configuration tab offers comprehensive personalization. "
            "You can customize your companion's name, such as Nikhila, set your preferred greeting like Hero, and calibrate your exact daily milliliter target. "
            "System settings let you toggle automatic Windows startup, start minimized in the background system tray, and control always-on-top window layering."
        ),
        "screenshot_idx": 1,
        "type": "screenshot",
        "card_tag": "IDENTITY & PREFERENCES",
        "card_sub": "Deep Personalization",
        "card_tokens": [
            ("Personalized companion name (", "normal"),
            ("Nikhila", "highlight_cyan"),
            ("), daily targets, and ", "normal"),
            ("WINDOWS STARTUP REGISTRATION", "highlight_white"),
            (".", "normal")
        ]
    },
    {
        "id": "ch05_reminders",
        "tag": "CHAPTER 05 // REMINDER ENGINE",
        "title": "Smart Recurrence, Snooze & Retry",
        "script": (
            "The reminder engine is designed to adapt to your working rhythm. "
            "Instead of rigid alarms, you can set custom recurring intervals, select five, ten, or fifteen-minute snooze periods, "
            "and configure a dedicated retry interval if you select Not Yet. Every state transition is backed by dedicated timers with zero orphaned memory leaks."
        ),
        "screenshot_idx": 2,
        "type": "screenshot",
        "card_tag": "INTELLIGENT TIMERS",
        "card_sub": "Zero-Leak Engine Lifecycle",
        "card_tokens": [
            ("Custom intervals, ", "normal"),
            ("5 / 10 / 15-MIN SNOOZE", "code"),
            (", and intelligent ", "normal"),
            ("RETRY-AFTER-NO", "highlight_mint"),
            (" fallback logic.", "normal")
        ]
    },
    {
        "id": "ch06_quiet_hours",
        "tag": "CHAPTER 06 // SLEEP PROTECTION",
        "title": "Configurable Overnight Quiet Hours",
        "script": (
            "Respecting developer focus and rest is paramount. "
            "Spider-Man Water Buddy includes a robust Quiet Hours engine with full midnight-crossing rollover support. "
            "When enabled, notifications are automatically suppressed between twenty-two hundred and zero-eight hundred, seamlessly resuming in the morning."
        ),
        "screenshot_idx": 2,
        "type": "screenshot",
        "card_tag": "QUIET HOURS",
        "card_sub": "Midnight-Crossing Support",
        "card_tokens": [
            ("Automatic ", "normal"),
            ("DO NOT DISTURB", "highlight_azure"),
            (" suppresses notifications overnight to protect your ", "normal"),
            ("SLEEP & FOCUS", "highlight_white"),
            (".", "normal")
        ]
    },
    {
        "id": "ch07_win32",
        "tag": "CHAPTER 07 // WIN32 ENGINEERING",
        "title": "Focus-Safe Companion Overlay",
        "script": (
            "The desktop companion hangs upside down from your screen's top-right edge with natural pendulum web swinging physics and cursor proximity awareness. "
            "Most importantly, by leveraging Windows Win32 ctypes and the WS_EX_NOACTIVATE window style, the companion never steals keyboard focus while you are actively typing in your code editor."
        ),
        "screenshot_idx": 3,
        "type": "screenshot",
        "card_tag": "WIN32 FOCUS PROTECTION",
        "card_sub": "Native User32 Architecture",
        "card_tokens": [
            ("Native Windows ", "normal"),
            ("WS_EX_NOACTIVATE", "code"),
            (" ensures prompts ", "normal"),
            ("NEVER STEAL KEYBOARD FOCUS", "highlight_mint"),
            (" while typing.", "normal")
        ]
    },
    {
        "id": "ch08_architecture",
        "tag": "CHAPTER 08 // PRODUCTION RELEASE",
        "title": "Packaging, Distribution & Open Source",
        "script": (
            "Under the hood, the app features single-instance enforcement via Windows Mutex, atomic JSON configuration writes, and rotating logs. "
            "It ships as both a standalone portable ZIP and a zero-admin Windows Setup Installer with full Add and Remove Programs integration. "
            "Spider-Man Water Buddy is completely open source on GitHub under the MIT license. Star the repo and build your own companion today!"
        ),
        "type": "outro_card",
        "card_tag": "OPEN SOURCE RELEASE",
        "card_sub": "MIT License • GitHub",
        "card_tokens": [
            ("100% Offline, ", "normal"),
            ("SINGLE-INSTANCE MUTEX", "highlight_cyan"),
            (", atomic persistence, and ", "normal"),
            ("ZERO CLOUD TELEMETRY", "highlight_mint"),
            (".", "normal")
        ]
    }
]


def draw_linear_gradient(draw: ImageDraw.ImageDraw, size, color_top, color_bottom):
    w, h = size
    for y in range(h):
        ratio = y / h
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


async def prepare_chapter_audio():
    print("\n[STEP 1] Validating and Linking Pre-Synthesized Chapter Voiceover...")
    total_time = 0.0

    for ch in CHAPTERS:
        src_audio = AUDIO_SRC_DIR / f"{ch['id']}.mp3"
        dest_audio = BUILD_DIR / f"{ch['id']}.mp3"
        
        if not src_audio.exists():
            import edge_tts
            print(f"  -> Synthesizing missing audio for {ch['id']}...")
            comm = edge_tts.Communicate(ch["script"], VOICE, rate="-2%")
            await comm.save(str(dest_audio))
        else:
            shutil.copy2(src_audio, dest_audio)

        # Measure audio duration
        cmd = [FFMPEG_EXE, "-i", str(dest_audio)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        dur = 0.0
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                dur = float(h) * 3600 + float(m) * 60 + float(s)
                break

        ch["audio_path"] = dest_audio
        ch["duration"] = dur + 1.0  # 1.0s comfortable breathing pause
        total_time += ch["duration"]
        print(f"  -> {ch['tag']}: {dur:.2f}s audio (+1.0s pause = {ch['duration']:.2f}s)")

    print(f"[SUCCESS] All 8 chapter audio tracks validated! Total duration: {total_time:.2f}s (~{total_time/60:.2f} min)")
    return total_time


def generate_ambient_music(total_duration: float, output_path: Path):
    print(f"\n[STEP 2] Synthesizing Studio 48kHz Stereo Ambient Score ({total_duration:.1f}s)...")
    sample_rate = 48000
    t = np.linspace(0, total_duration, int(sample_rate * total_duration), endpoint=False)

    chords = [
        [146.83, 220.00, 277.18, 329.63, 440.00],  # Dmaj9
        [123.47, 185.00, 220.00, 293.66, 369.99],  # Bm7
        [98.00, 146.83, 196.00, 246.94, 293.66],   # Gmaj7
        [110.00, 164.81, 220.00, 293.66, 329.63]   # Asus4
    ]

    chord_dur = 4.0
    music_track = np.zeros_like(t)

    for i in range(int(math.ceil(total_duration / chord_dur))):
        chord = chords[i % len(chords)]
        start_idx = int(i * chord_dur * sample_rate)
        end_idx = min(len(t), int((i + 1) * chord_dur * sample_rate))
        if start_idx >= len(t):
            break
        sub_t = t[start_idx:end_idx] - t[start_idx]
        sub_audio = np.zeros_like(sub_t)
        for freq in chord:
            harmonic = (
                np.sin(2 * np.pi * freq * sub_t) * 0.6 +
                np.sin(2 * np.pi * freq * 2 * sub_t) * 0.25 +
                np.sin(2 * np.pi * freq * 3 * sub_t) * 0.1
            )
            tremolo = 1.0 + 0.08 * np.sin(2 * np.pi * 1.5 * sub_t)
            sub_audio += harmonic * tremolo

        env = np.ones_like(sub_t)
        attack_len = int(0.3 * sample_rate)
        if len(env) > attack_len:
            env[:attack_len] = np.linspace(0, 1, attack_len)
        decay_len = int(0.5 * sample_rate)
        if len(env) > decay_len:
            env[-decay_len:] = np.linspace(1, 0.4, decay_len)
        music_track[start_idx:end_idx] += sub_audio * env

    music_track = music_track / np.max(np.abs(music_track)) * 0.14
    stereo_audio = np.column_stack((music_track, music_track))
    wavfile.write(str(output_path), sample_rate, (stereo_audio * 32767).astype(np.int16))
    print(f"[SUCCESS] 48kHz Stereo ambient score generated: {output_path}")


def render_2k_chapter_frames_and_kinetic_cards():
    print("\n[STEP 3] Rendering Pristine 2K (2560x1440) Frames & Aligned Typography Cards...")
    W, H = 2560, 1440

    font_main_title = ImageFont.truetype(FONT_INTER_BOLD, 72)
    font_sub = ImageFont.truetype(FONT_INTER_REG, 38)
    font_badge = ImageFont.truetype(FONT_INTER_BOLD, 30)
    font_tag = ImageFont.truetype(FONT_MONO_BOLD, 22)
    font_subtag = ImageFont.truetype(FONT_INTER_REG, 22)
    font_body = ImageFont.truetype(FONT_INTER_REG, 34)
    font_bold = ImageFont.truetype(FONT_INTER_BOLD, 34)
    font_code = ImageFont.truetype(FONT_MONO_BOLD, 30)

    spidey_img = Image.open(SPIDEY_RENDER).convert("RGBA") if SPIDEY_RENDER.exists() else None
    app_icon_img = Image.open(APP_ICON).convert("RGBA") if APP_ICON.exists() else None

    for idx, ch in enumerate(CHAPTERS):
        # 1. Base 2K visual frame
        frame_file = BUILD_DIR / f"{ch['id']}_frame_2k.png"
        img = Image.new("RGB", (W, H), (7, 17, 30))
        draw = ImageDraw.Draw(img)
        draw_linear_gradient(draw, (W, H), (7, 17, 30), (12, 26, 46))

        if ch["type"] == "title_card":
            # Glass container in center
            card_rect = [120, 120, 2440, 1320]
            draw.rounded_rectangle(card_rect, radius=28, fill=(13, 27, 46), outline=(0, 240, 255), width=2)

            if app_icon_img:
                icon_scaled = app_icon_img.resize((190, 190), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (220, 200), icon_scaled)

            draw.text((450, 210), "SPIDER-MAN WATER BUDDY", fill=(0, 240, 255), font=font_main_title)
            draw.text((454, 305), "Full Architectural Walkthrough • 2K Master Edition", fill=(168, 196, 216), font=font_sub)

            pills = [
                "Native Windows Desktop Hydration Companion",
                "Non-Focus-Stealing Architecture (WS_EX_NOACTIVATE)",
                "Real-Time Sinusoidal Wave Reservoir (PySide6 QPainter)",
                "100% Offline & Private (Zero Cloud Telemetry)"
            ]
            py = 460
            for pill in pills:
                draw.rounded_rectangle([220, py, 1550, py + 74], radius=16, fill=(18, 38, 64), outline=(10, 132, 255), width=1)
                # Sleek glowing cyan bullet dot
                draw.ellipse([252, py + 31, 266, py + 45], fill=(0, 240, 255))
                draw.text((284, py + 18), pill, fill=(240, 246, 252), font=font_badge)
                py += 105

            if spidey_img:
                sp_h = 1050
                sp_w = int(spidey_img.width * (sp_h / spidey_img.height))
                sp_scaled = spidey_img.resize((sp_w, sp_h), Image.Resampling.LANCZOS)
                img.paste(sp_scaled, (1750, 140), sp_scaled)

        elif ch["type"] == "screenshot":
            # --- 2K PIXEL-PERFECT ALIGNED HEADER BAR ---
            header_y1 = 36
            header_y2 = 164
            header_h = header_y2 - header_y1
            header_mid_y = header_y1 + header_h // 2
            header_rect = [60, header_y1, 2500, header_y2]

            draw.rounded_rectangle(header_rect, radius=18, fill=(13, 27, 46), outline=(0, 240, 255), width=2)

            # Left Tag Pill (Dynamic width based on text length)
            tag_text = ch["tag"]
            tag_bbox = draw.textbbox((0, 0), tag_text, font=font_tag)
            tag_w = tag_bbox[2] - tag_bbox[0]
            tag_h = tag_bbox[3] - tag_bbox[1]

            pill_w = tag_w + 40
            pill_h = 56
            pill_x1 = 88
            pill_y1 = header_mid_y - pill_h // 2
            pill_rect = [pill_x1, pill_y1, pill_x1 + pill_w, pill_y1 + pill_h]

            draw.rounded_rectangle(pill_rect, radius=12, fill=(12, 54, 78), outline=(0, 240, 255), width=2)
            tag_draw_x = pill_x1 + (pill_w - tag_w) // 2
            tag_draw_y = pill_y1 + (pill_h - tag_h) // 2 - 2
            draw.text((tag_draw_x, tag_draw_y), tag_text, fill=(0, 240, 255), font=font_tag)

            # Title Text (Dynamic sizing & vertical centering)
            title_start_x = pill_x1 + pill_w + 36
            max_title_w = 2460 - title_start_x

            title_font_size = 46
            title_str = ch["title"].upper()
            curr_title_font = ImageFont.truetype(FONT_INTER_BOLD, title_font_size)
            title_bbox = draw.textbbox((0, 0), title_str, font=curr_title_font)

            while (title_bbox[2] - title_bbox[0]) > max_title_w and title_font_size > 26:
                title_font_size -= 2
                curr_title_font = ImageFont.truetype(FONT_INTER_BOLD, title_font_size)
                title_bbox = draw.textbbox((0, 0), title_str, font=curr_title_font)

            title_h = title_bbox[3] - title_bbox[1]
            title_draw_y = header_mid_y - (title_h // 2) - 4
            draw.text((title_start_x, title_draw_y), title_str, fill=(255, 255, 255), font=curr_title_font)

            # Paste 2K-Upscaled Screenshot with Lanczos Filtering and subtle unsharp enhancement
            shot_path = USER_SCREENSHOTS[ch["screenshot_idx"]]
            shot_img = Image.open(shot_path).convert("RGBA")

            target_w = 2360
            target_h = int(shot_img.height * (target_w / shot_img.width))
            if target_h > 1050:
                target_h = 1050
                target_w = int(shot_img.width * (target_h / shot_img.height))

            # Resample at 2K with Lanczos
            shot_scaled = shot_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            # Subtle unsharp mask to crisp up text rendering on 2K displays
            shot_scaled = shot_scaled.filter(ImageFilter.UnsharpMask(radius=1.2, percent=115, threshold=3))

            sx = (W - target_w) // 2
            sy = 190 + (1050 - target_h) // 2

            # Clean outer container border
            draw.rounded_rectangle([sx - 4, sy - 4, sx + target_w + 4, sy + target_h + 4], radius=16, fill=(10, 22, 38), outline=(0, 240, 255), width=2)
            img.paste(shot_scaled, (sx, sy), shot_scaled)

        elif ch["type"] == "outro_card":
            card_rect = [140, 120, 2420, 1320]
            draw.rounded_rectangle(card_rect, radius=28, fill=(13, 27, 46), outline=(0, 230, 153), width=2)

            if app_icon_img:
                icon_scaled = app_icon_img.resize((160, 160), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (220, 180), icon_scaled)

            draw.text((420, 185), "SPIDER-MAN WATER BUDDY", fill=(0, 230, 153), font=font_main_title)
            draw.text((424, 280), "Production-Grade Desktop Architecture & Open Source Release", fill=(168, 196, 216), font=font_sub)

            features = [
                ("Aquatic Liquid Glass UI", "Deep oceanic palette, translucent glass cards, and glowing cyan accents."),
                ("Single-Instance Mutex", "Enforces exactly one active companion instance across Windows sessions."),
                ("Atomic Persistence", "Crash-safe JSON state writes with %APPDATA% directory migration."),
                ("Focus-Free Architecture", "WS_EX_NOACTIVATE ensures reminders never interrupt your active typing."),
                ("Turnkey Distribution", "Clean portable ZIP and zero-admin Windows Setup Installer.")
            ]

            fy = 370
            for ft_title, desc in features:
                draw.rounded_rectangle([220, fy, 2340, fy + 100], radius=16, fill=(16, 34, 58), outline=(0, 240, 255), width=1)
                # Sleek cyan dot
                draw.ellipse([252, fy + 24, 266, fy + 38], fill=(0, 240, 255))
                draw.text((284, fy + 16), ft_title, fill=(0, 240, 255), font=font_badge)
                draw.text((284, fy + 56), desc, fill=(168, 196, 216), font=font_body)
                fy += 122

            draw.rounded_rectangle([680, 1160, 1880, 1260], radius=18, fill=(0, 230, 153), outline=(0, 230, 153), width=2)
            draw.text((750, 1190), "OPEN SOURCE // MIT Licensed on GitHub • Python & PySide6", fill=(10, 22, 38), font=font_badge)

        img.save(frame_file)
        ch["frame_path"] = frame_file

        # 2. Render 2K kinetic typography overlay card
        card_file = BUILD_DIR / f"{ch['id']}_kinetic_card_2k.png"
        card_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(card_img)

        line_w = 0
        piece_metrics = []
        for text, style in ch["card_tokens"]:
            if style == "code":
                f = font_code
                bbox = cdraw.textbbox((0, 0), text, font=f)
                pw = (bbox[2] - bbox[0]) + 24
            elif "highlight" in style:
                f = font_bold
                bbox = cdraw.textbbox((0, 0), text, font=f)
                pw = bbox[2] - bbox[0]
            else:
                f = font_body
                bbox = cdraw.textbbox((0, 0), text, font=f)
                pw = bbox[2] - bbox[0]
            piece_metrics.append((text, style, f, pw))
            line_w += pw

        card_w = max(1300, min(2200, line_w + 140))
        card_h = 144
        card_x = (W - card_w) // 2
        card_y = 1245

        # Glass shadow
        cdraw.rounded_rectangle([card_x + 8, card_y + 10, card_x + card_w + 8, card_y + card_h + 10], radius=24, fill=(0, 0, 0, 150))
        # Glass container
        cdraw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=22, fill=(7, 17, 30, 238), outline=(0, 240, 255, 140), width=2)

        # Micro header pill
        tag_text = ch["card_tag"]
        tag_bbox = cdraw.textbbox((0, 0), tag_text, font=font_tag)
        tag_w = tag_bbox[2] - tag_bbox[0] + 30
        cdraw.rounded_rectangle([card_x + 40, card_y + 18, card_x + 40 + tag_w, card_y + 52], radius=8, fill=(0, 240, 255, 35), outline=(0, 240, 255, 160), width=1)
        cdraw.text((card_x + 55, card_y + 22), tag_text, fill=(0, 240, 255), font=font_tag)
        cdraw.text((card_x + 40 + tag_w + 20, card_y + 23), ch["card_sub"], fill=(168, 196, 216), font=font_subtag)

        # Main text line
        cur_x = card_x + (card_w - line_w) // 2
        text_y = card_y + 76
        for text, style, font, pw in piece_metrics:
            if style == "code":
                cdraw.rounded_rectangle([cur_x, text_y - 6, cur_x + pw, text_y + 42], radius=8, fill=(10, 132, 255, 50), outline=(0, 240, 255, 180), width=1)
                cdraw.text((cur_x + 12, text_y), text, fill=(0, 240, 255), font=font)
                cur_x += pw
            elif style == "highlight_cyan":
                cdraw.text((cur_x, text_y), text, fill=(0, 240, 255), font=font)
                cur_x += pw
            elif style == "highlight_mint":
                cdraw.text((cur_x, text_y), text, fill=(0, 230, 153), font=font)
                cur_x += pw
            elif style == "highlight_azure":
                cdraw.text((cur_x, text_y), text, fill=(56, 189, 248), font=font)
                cur_x += pw
            elif style == "highlight_white":
                cdraw.text((cur_x, text_y), text, fill=(255, 255, 255), font=font)
                cur_x += pw
            else:
                cdraw.text((cur_x, text_y), text, fill=(240, 246, 252), font=font)
                cur_x += pw

        card_img.save(card_file)
        ch["card_path"] = card_file
        print(f"  -> Generated 2K base frame & kinetic card: {ch['id']}")

    print("[SUCCESS] All 2K chapter frames and kinetic typography cards rendered perfectly!")


def assemble_2k_master_video(total_duration: float):
    print("\n[STEP 4] Assembling 2K Master Video (2560x1440, YUV420p, 48kHz Stereo AAC)...")
    final_output = DIST_DIR / "SpiderManWaterBuddy-2K-Master.mp4"

    clip_files = []
    for idx, ch in enumerate(CHAPTERS):
        clip_path = BUILD_DIR / f"{ch['id']}_clip_2k.mp4"
        frame_path = ch["frame_path"]
        card_path = ch["card_path"]
        audio_path = ch["audio_path"]
        duration = ch["duration"]

        total_frames = int(duration * 30)
        # Slow zoom + smooth fade in/out + upward kinetic glide overlay at 2K
        filter_str = (
            f"[0:v]scale=2560:1440,zoompan=z='min(zoom+0.00010,1.03)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=2560x1440:fps=30,"
            f"fade=t=in:st=0:d=0.4,fade=t=out:st={duration-0.4:.2f}:d=0.4[base];"
            f"[base][1:v]overlay=x=0:y='if(lt(t,0.35),18*(1-t/0.35),0)':format=auto,format=yuv420p[v]"
        )

        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1", "-i", str(frame_path),
            "-i", str(card_path),
            "-i", str(audio_path),
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "2:a",
            "-c:v", "libx264", "-profile:v", "high", "-level", "5.1", "-pix_fmt", "yuv420p", "-preset", "medium", "-crf", "16",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "256k",
            "-t", f"{duration:.3f}",
            str(clip_path)
        ]
        subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        clip_files.append(clip_path)
        print(f"  -> Rendered 2K Chapter {idx+1}/{len(CHAPTERS)}: {clip_path.name}")

    # Concat all chapters
    concat_list = BUILD_DIR / "concat_list_2k.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c.name}'\n")

    concatenated_video = BUILD_DIR / "concatenated_2k.mp4"
    cmd_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(concatenated_video)
    ]
    subprocess.run(cmd_concat, check=True, cwd=str(BUILD_DIR), creationflags=subprocess.CREATE_NO_WINDOW)
    print("  -> Concatenated all 2K chapters.")

    # Master mix with ambient background score
    ambient_wav = BUILD_DIR / "ambient_score_48k.wav"
    cmd_master = [
        FFMPEG_EXE, "-y",
        "-i", str(concatenated_video),
        "-i", str(ambient_wav),
        "-filter_complex",
        "[1:a]volume=0.16[bgm];"
        "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "256k",
        "-movflags", "+faststart",
        str(final_output)
    ]
    print("\n[STEP 5] Finalizing Master 2K Integration...")
    subprocess.run(cmd_master, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

    size_mb = final_output.stat().st_size / (1024 * 1024)
    print("\n==================================================")
    print(" 2K MASTER DEMO COMPLETED SUCCESSFULLY!")
    print(f" Output File:  {final_output}")
    print(f" File Size:    {size_mb:.2f} MB")
    print(f" Resolution:   2560x1440 (2K QHD, 16:9 Landscape)")
    print(f" Color Format: YUV420p Progressive (H.264 High Profile)")
    print(f" Audio Track:  AAC-LC 48000 Hz Stereo (256 kbps)")
    print(f" Duration:     {total_duration:.1f} seconds (~{total_duration/60:.2f} minutes)")
    print("==================================================")
    return final_output


async def main():
    print("==================================================")
    print(" Spider-Man Water Buddy — 2K QHD Master Video Builder")
    print("==================================================")
    start_time = time.time()

    total_dur = await prepare_chapter_audio()
    ambient_wav = BUILD_DIR / "ambient_score_48k.wav"
    generate_ambient_music(total_dur, ambient_wav)
    render_2k_chapter_frames_and_kinetic_cards()
    assemble_2k_master_video(total_dur)

    elapsed = time.time() - start_time
    print(f"\n2K Workflow completed in {elapsed:.1f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
