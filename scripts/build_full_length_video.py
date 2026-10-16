"""
Full-Length Master Project Walkthrough & Showcase Video Generator.
Produces an in-depth, comprehensive ~3.5 to 4 minute 1080p cinematic presentation with:
- Strict YUV420p progressive video & 48 kHz stereo audio for 100% universal player compatibility
- Deep architectural narration across 8 detailed chapters
- Multi-font kinetic typography (Inter Bold + JetBrains Mono) with upward glide animation
- Dual-layer ambient synth background score ducked under voiceover
- High-res footage of all app screens, 3D character assets, and engineering specifications
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
from PIL import Image, ImageDraw, ImageFont
from scipy.io import wavfile

ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "full_length_video"
DIST_DIR = ROOT_DIR / "dist"
FONTS_DIR = ROOT_DIR / "build" / "fonts"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# Ensure directories
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

# 8 In-Depth Chapters for Full-Length Master Video
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


async def generate_speech_for_chapters():
    import edge_tts
    print("\n[STEP 1] Synthesizing In-Depth Chapter Narration (edge-tts)...")

    total_time = 0.0
    for idx, ch in enumerate(CHAPTERS):
        audio_file = BUILD_DIR / f"{ch['id']}.mp3"
        comm = edge_tts.Communicate(ch["script"], VOICE, rate="-2%")
        await comm.save(str(audio_file))

        # Measure audio duration
        cmd = [FFMPEG_EXE, "-i", str(audio_file)]
        res = subprocess.run(cmd, capture_output=True, text=True)
        dur = 0.0
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                dur = float(h) * 3600 + float(m) * 60 + float(s)
                break

        ch["audio_path"] = audio_file
        ch["duration"] = dur + 1.0  # 1.0s comfortable pause between chapters
        total_time += ch["duration"]
        print(f"  -> {ch['tag']}: {dur:.2f}s audio (+1.0s padding = {ch['duration']:.2f}s)")

    print(f"[SUCCESS] All 8 chapters generated! Total length: {total_time:.2f}s (~{total_time/60:.2f} minutes)")
    return total_time


def generate_ambient_music(total_duration: float, output_path: Path):
    print(f"\n[STEP 2] Synthesizing Master Ambient Lo-Fi Background Score ({total_duration:.1f}s)...")
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
    # Create stereo channels
    stereo_audio = np.column_stack((music_track, music_track))
    wavfile.write(str(output_path), sample_rate, (stereo_audio * 32767).astype(np.int16))
    print(f"[SUCCESS] Master 48kHz stereo ambient score created: {output_path}")


def render_chapter_frames_and_kinetic_cards():
    print("\n[STEP 3] Rendering High-Definition 1080p Base Frames & Kinetic Typography Cards...")
    W, H = 1920, 1080

    font_title = ImageFont.truetype(FONT_INTER_BOLD, 60)
    font_sub = ImageFont.truetype(FONT_INTER_REG, 32)
    font_badge = ImageFont.truetype(FONT_INTER_BOLD, 24)
    font_tag = ImageFont.truetype(FONT_MONO_BOLD, 18)
    font_subtag = ImageFont.truetype(FONT_INTER_REG, 17)
    font_body = ImageFont.truetype(FONT_INTER_REG, 28)
    font_bold = ImageFont.truetype(FONT_INTER_BOLD, 28)
    font_code = ImageFont.truetype(FONT_MONO_BOLD, 25)

    spidey_img = Image.open(SPIDEY_RENDER).convert("RGBA") if SPIDEY_RENDER.exists() else None
    app_icon_img = Image.open(APP_ICON).convert("RGBA") if APP_ICON.exists() else None

    for idx, ch in enumerate(CHAPTERS):
        # 1. Base visual frame
        frame_file = BUILD_DIR / f"{ch['id']}_frame.png"
        img = Image.new("RGB", (W, H), (7, 17, 30))
        draw = ImageDraw.Draw(img)
        draw_linear_gradient(draw, (W, H), (7, 17, 30), (12, 26, 46))

        if ch["type"] == "title_card":
            card_rect = [120, 140, 1800, 940]
            draw.rounded_rectangle(card_rect, radius=24, fill=(13, 27, 46, 220), outline=(0, 240, 255, 60), width=2)

            if app_icon_img:
                icon_scaled = app_icon_img.resize((140, 140), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (200, 220), icon_scaled)

            draw.text((370, 225), "SPIDER-MAN WATER BUDDY", fill=(0, 240, 255), font=font_title)
            draw.text((374, 305), "Full Architectural Walkthrough • v1.0.0", fill=(168, 196, 216), font=font_sub)

            pills = [
                "💧 Native Windows Desktop Hydration Companion",
                "🛡️ Non-Focus-Stealing Architecture (WS_EX_NOACTIVATE)",
                "🌊 Real-Time Sinusoidal Wave Reservoir (PySide6 QPainter)",
                "🔒 100% Offline & Private (Zero Cloud Telemetry)"
            ]
            py = 420
            for pill in pills:
                draw.rounded_rectangle([200, py, 1150, py + 56], radius=14, fill=(18, 38, 64), outline=(10, 132, 255, 90), width=1)
                draw.text((224, py + 12), pill, fill=(240, 246, 252), font=font_badge)
                py += 78

            if spidey_img:
                sp_h = 750
                sp_w = int(spidey_img.width * (sp_h / spidey_img.height))
                sp_scaled = spidey_img.resize((sp_w, sp_h), Image.Resampling.LANCZOS)
                img.paste(sp_scaled, (1320, 100), sp_scaled)

        elif ch["type"] == "screenshot":
            header_rect = [60, 40, 1860, 110]
            draw.rounded_rectangle(header_rect, radius=16, fill=(13, 27, 46, 230), outline=(0, 240, 255, 60), width=1)
            
            draw.rounded_rectangle([80, 52, 290, 98], radius=10, fill=(0, 240, 255, 30), outline=(0, 240, 255, 120), width=1)
            draw.text((95, 62), ch["tag"], fill=(0, 240, 255), font=font_tag)
            draw.text((315, 54), ch["title"].upper(), fill=(255, 255, 255), font=font_title)

            shot_path = USER_SCREENSHOTS[ch["screenshot_idx"]]
            shot_img = Image.open(shot_path).convert("RGBA")
            target_w = 1760
            target_h = int(shot_img.height * (target_w / shot_img.width))
            if target_h > 880:
                target_h = 880
                target_w = int(shot_img.width * (target_h / shot_img.height))
            shot_scaled = shot_img.resize((target_w, target_h), Image.Resampling.LANCZOS)

            sx = (W - target_w) // 2
            sy = 145 + (880 - target_h) // 2
            draw.rounded_rectangle([sx - 4, sy - 4, sx + target_w + 4, sy + target_h + 4], radius=12, fill=(10, 22, 38), outline=(0, 240, 255, 80), width=2)
            img.paste(shot_scaled, (sx, sy), shot_scaled)

        elif ch["type"] == "outro_card":
            card_rect = [140, 120, 1780, 960]
            draw.rounded_rectangle(card_rect, radius=24, fill=(13, 27, 46, 230), outline=(0, 230, 153, 90), width=2)

            if app_icon_img:
                icon_scaled = app_icon_img.resize((120, 120), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (200, 180), icon_scaled)

            draw.text((350, 180), "SPIDER-MAN WATER BUDDY", fill=(0, 230, 153), font=font_title)
            draw.text((354, 255), "Production-Grade Desktop Architecture & Open Source Release", fill=(168, 196, 216), font=font_sub)

            features = [
                ("💎 Aquatic Liquid Glass UI", "Deep oceanic palette, translucent glass cards, and glowing cyan accents."),
                ("⚡ Single-Instance Mutex", "Enforces exactly one active companion instance across Windows sessions."),
                ("📝 Atomic Persistence", "Crash-safe JSON state writes with %APPDATA% directory migration."),
                ("🎯 Focus-Free Architecture", "WS_EX_NOACTIVATE ensures reminders never interrupt your active typing."),
                ("📦 Turnkey Distribution", "Clean portable ZIP and zero-admin Windows Setup Installer.")
            ]

            fy = 340
            for ft_title, desc in features:
                draw.rounded_rectangle([200, fy, 1720, fy + 78], radius=12, fill=(16, 34, 58), outline=(0, 240, 255, 40), width=1)
                draw.text((224, fy + 12), ft_title, fill=(0, 240, 255), font=font_badge)
                draw.text((224, fy + 44), desc, fill=(168, 196, 216), font=font_body)
                fy += 92

            draw.rounded_rectangle([560, 840, 1360, 915], radius=16, fill=(0, 230, 153, 40), outline=(0, 230, 153, 180), width=2)
            draw.text((610, 856), "⭐ MIT Licensed on GitHub • Built with Python & PySide6", fill=(255, 255, 255), font=font_badge)

        img.save(frame_file)
        ch["frame_path"] = frame_file

        # 2. Render kinetic typography overlay card
        card_file = BUILD_DIR / f"{ch['id']}_kinetic_card.png"
        card_img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        cdraw = ImageDraw.Draw(card_img)

        line_w = 0
        piece_metrics = []
        for text, style in ch["card_tokens"]:
            if style == "code":
                f = font_code
                bbox = cdraw.textbbox((0, 0), text, font=f)
                pw = (bbox[2] - bbox[0]) + 20
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

        card_w = max(1000, min(1580, line_w + 100))
        card_h = 120
        card_x = (W - card_w) // 2
        card_y = 920

        # Glass shadow
        cdraw.rounded_rectangle([card_x + 6, card_y + 8, card_x + card_w + 6, card_y + card_h + 8], radius=20, fill=(0, 0, 0, 140))
        # Glass container
        cdraw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=18, fill=(7, 17, 30, 235), outline=(0, 240, 255, 120), width=2)

        # Micro header
        tag_text = ch["card_tag"]
        tag_bbox = cdraw.textbbox((0, 0), tag_text, font=font_tag)
        tag_w = tag_bbox[2] - tag_bbox[0] + 24
        cdraw.rounded_rectangle([card_x + 32, card_y + 16, card_x + 32 + tag_w, card_y + 44], radius=7, fill=(0, 240, 255, 35), outline=(0, 240, 255, 140), width=1)
        cdraw.text((card_x + 44, card_y + 19), tag_text, fill=(0, 240, 255), font=font_tag)
        cdraw.text((card_x + 32 + tag_w + 16, card_y + 20), ch["card_sub"], fill=(168, 196, 216), font=font_subtag)

        # Text line
        cur_x = card_x + (card_w - line_w) // 2
        text_y = card_y + 64
        for text, style, font, pw in piece_metrics:
            if style == "code":
                cdraw.rounded_rectangle([cur_x, text_y - 4, cur_x + pw, text_y + 36], radius=6, fill=(10, 132, 255, 45), outline=(0, 240, 255, 170), width=1)
                cdraw.text((cur_x + 10, text_y), text, fill=(0, 240, 255), font=font)
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
        print(f"  -> Generated base frame and kinetic card for {ch['id']}")

    print("[SUCCESS] All chapter base frames and kinetic typography cards rendered!")


def assemble_full_length_video(total_duration: float):
    print("\n[STEP 4] Assembling Full-Length Video with Universal Compatibility (yuv420p & 48kHz Stereo)...")
    final_output = DIST_DIR / "SpiderManWaterBuddy-Full-Length-Master.mp4"

    # 1. Render each chapter clip with motion and overlaid kinetic card
    clip_files = []
    for idx, ch in enumerate(CHAPTERS):
        clip_path = BUILD_DIR / f"{ch['id']}_clip.mp4"
        frame_path = ch["frame_path"]
        card_path = ch["card_path"]
        audio_path = ch["audio_path"]
        duration = ch["duration"]

        total_frames = int(duration * 30)
        # Slow zoom + smooth fade in/out + upward kinetic glide overlay
        filter_str = (
            f"[0:v]scale=1920:1080,zoompan=z='min(zoom+0.00012,1.04)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps=30,"
            f"fade=t=in:st=0:d=0.4,fade=t=out:st={duration-0.4:.2f}:d=0.4[base];"
            f"[base][1:v]overlay=x=0:y='if(lt(t,0.35),14*(1-t/0.35),0)':format=auto,format=yuv420p[v]"
        )

        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1", "-i", str(frame_path),
            "-i", str(card_path),
            "-i", str(audio_path),
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "2:a",
            "-c:v", "libx264", "-profile:v", "high", "-level", "4.1", "-pix_fmt", "yuv420p", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
            "-t", f"{duration:.3f}",
            str(clip_path)
        ]
        subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        clip_files.append(clip_path)
        print(f"  -> Rendered Chapter {idx+1}/{len(CHAPTERS)}: {clip_path.name}")

    # 2. Concat all chapters
    concat_list = BUILD_DIR / "full_concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c.name}'\n")

    concatenated_video = BUILD_DIR / "concatenated_video.mp4"
    cmd_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(concatenated_video)
    ]
    subprocess.run(cmd_concat, check=True, cwd=str(BUILD_DIR), creationflags=subprocess.CREATE_NO_WINDOW)
    print("  -> Concatenated all chapter video and narration tracks.")

    # 3. Final Master Merge with background ambient music ducked at -22dB
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
        "-c:a", "aac", "-ar", "48000", "-ac", "2", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_output)
    ]
    print("\n[STEP 5] Finalizing Master Audio-Video Integration...")
    subprocess.run(cmd_master, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

    size_mb = final_output.stat().st_size / (1024 * 1024)
    print("\n==================================================")
    print(" FULL-LENGTH MASTER DEMO COMPLETED SUCCESSFULLY!")
    print(f" File:     {final_output}")
    print(f" Size:     {size_mb:.2f} MB")
    print(f" Format:   1080p 16:9 MP4 (30 FPS, YUV420p Progressive)")
    print(f" Audio:    AAC-LC 48000 Hz Stereo (192 kbps)")
    print(f" Duration: {total_duration:.1f} seconds (~{total_duration/60:.2f} minutes)")
    print("==================================================")
    return final_output


async def main():
    print("==================================================")
    print(" Spider-Man Water Buddy — Full-Length Master Video")
    print("==================================================")
    start_time = time.time()

    total_dur = await generate_speech_for_chapters()
    ambient_wav = BUILD_DIR / "ambient_score_48k.wav"
    generate_ambient_music(total_dur, ambient_wav)
    render_chapter_frames_and_kinetic_cards()
    final_video = assemble_full_length_video(total_dur)

    elapsed = time.time() - start_time
    print(f"\nWorkflow finished in {elapsed:.1f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
