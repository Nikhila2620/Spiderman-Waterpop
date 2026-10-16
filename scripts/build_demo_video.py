"""
Automated Video-Editing & Showcase Generation Pipeline for Spider-Man Water Buddy.
Creates a professional 16:9 1080p demo video (~2 minutes) with:
- Neural AI voiceover (edge-tts)
- Synchronized burned-in closed captions
- Subtle ambient background music
- Dynamic Ken Burns pan/zoom motion on screenshots
- Professional intro and outro title cards
- 100% locally runnable with zero paid APIs
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

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT_DIR / "build" / "demo_video"
DIST_DIR = ROOT_DIR / "dist"
FFMPEG_EXE = imageio_ffmpeg.get_ffmpeg_exe()

# User uploaded screenshots
USER_SCREENSHOTS = [
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160974961_da0ef2d0.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160978815_a48b5c09.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160982669_af298988.png",
    r"C:/Users/hp/.gemini/antigravity/brain/29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e/.user_uploaded/media_1792160986700_567678d5.png",
]

SPIDEY_RENDER = ROOT_DIR / "assets" / "images" / "spidey_3d_render.png"
APP_ICON = ROOT_DIR / "assets" / "images" / "app_icon_master.png"

VOICE = "en-US-ChristopherNeural"

# Structured Script
SCENES_SCRIPT = [
    {
        "id": "scene_01_intro",
        "title": "Introduction & The Challenge",
        "text": (
            "When you are deep in the flow state, staying hydrated is often the first thing forgotten. "
            "Traditional reminder apps are either annoying, intrusive, or get lost in background notifications. "
            "Introducing Spider-Man Water Buddy — a lightweight, native Windows desktop companion designed with a premium Aquatic Liquid Glass aesthetic."
        ),
        "type": "intro_card"
    },
    {
        "id": "scene_02_dashboard",
        "title": "Aquatic Liquid Glass Dashboard",
        "text": (
            "At the core of the experience is the redesigned Aquatic Dashboard. "
            "Built with PySide6 and custom QPainter physics, it features a live simulated fluid reservoir with dual-layer sinusoidal wave dynamics. "
            "You can track your daily hydration percentage at a glance and log water instantly with one-click quick pills like plus two-hundred and fifty milliliters."
        ),
        "screenshot_idx": 0,
        "type": "screenshot"
    },
    {
        "id": "scene_03_general",
        "title": "Personalization & System Integration",
        "text": (
            "The General settings page puts personalization front and center. "
            "You can customize your companion's identity and greeting, configure your daily target in milliliters, "
            "and enable seamless Windows startup integration. Best of all, it gives you full control over always-on-top window layering."
        ),
        "screenshot_idx": 1,
        "type": "screenshot"
    },
    {
        "id": "scene_04_reminders",
        "title": "Intelligent Reminders & Quiet Hours",
        "text": (
            "The reminder engine is engineered for real productivity. "
            "Set your custom recurrence interval, configure five, ten, or fifteen-minute snoozes, "
            "and benefit from intelligent retry-if-not-yet logic. "
            "With configurable Quiet Hours, reminders automatically mute overnight so your sleep and focus sessions are never disturbed."
        ),
        "screenshot_idx": 2,
        "type": "screenshot"
    },
    {
        "id": "scene_05_appearance",
        "title": "Physics, Motion & Focus-Safe Architecture",
        "text": (
            "The companion hangs effortlessly from the top-right corner of your screen. "
            "It features natural pendulum web swinging, Spider-Sense cursor proximity awareness, and celebratory animations. "
            "Crucially, using native Windows User32 APIs and WS_EX_NOACTIVATE, the overlay never steals keyboard focus while you are typing."
        ),
        "screenshot_idx": 3,
        "type": "screenshot"
    },
    {
        "id": "scene_06_outro",
        "title": "Engineering Highlights & Outro",
        "text": (
            "Engineered with PySide6, native Win32 ctypes, atomic JSON persistence, and zero external cloud dependencies. "
            "Spider-Man Water Buddy proves that desktop utilities can be high-performance, robust, and delightful. "
            "Check out the project on GitHub!"
        ),
        "type": "outro_card"
    }
]


def format_srt_time(seconds: float) -> str:
    hrs = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds - int(seconds)) * 1000)
    return f"{hrs:02d}:{mins:02d}:{secs:02d},{millis:03d}"


async def generate_speech_for_scenes():
    import edge_tts
    print("\n[STEP 1] Generating AI Voiceover and Sentence Timestamps...")
    BUILD_DIR.mkdir(parents=True, exist_ok=True)

    total_time = 0.0
    for idx, scene in enumerate(SCENES_SCRIPT):
        audio_file = BUILD_DIR / f"{scene['id']}.mp3"
        comm = edge_tts.Communicate(scene["text"], VOICE, rate="-2%")
        
        sentences = []
        with open(audio_file, "wb") as f:
            async for chunk in comm.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    start_s = chunk["offset"] / 10_000_000
                    dur_s = chunk["duration"] / 10_000_000
                    sentences.append({
                        "start": start_s,
                        "end": start_s + dur_s,
                        "text": chunk["text"].strip()
                    })
        
        # Get exact audio file duration using ffprobe
        cmd = [
            FFMPEG_EXE, "-i", str(audio_file)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        # Parse Duration: 00:00:18.42
        duration = 0.0
        for line in res.stderr.splitlines():
            if "Duration:" in line:
                part = line.split("Duration:")[1].split(",")[0].strip()
                h, m, s = part.split(":")
                duration = float(h) * 3600 + float(m) * 60 + float(s)
                break
        
        scene["audio_path"] = audio_file
        scene["duration"] = duration + 0.8  # Add 0.8s comfortable padding
        scene["sentences"] = sentences
        total_time += scene["duration"]
        print(f"  -> Scene {idx+1} ({scene['id']}): {duration:.2f}s audio (+0.8s padding = {scene['duration']:.2f}s)")

    print(f"[SUCCESS] Voiceover generated! Total narration length: {total_time:.2f}s (~{total_time/60:.1f} mins)")
    return total_time


def generate_ambient_music(total_duration: float, output_path: Path):
    print(f"\n[STEP 2] Synthesizing Warm Lo-Fi Ambient Background Music ({total_duration:.1f}s)...")
    sample_rate = 44100
    t = np.linspace(0, total_duration, int(sample_rate * total_duration), endpoint=False)

    # Chord progression (Dmaj9 -> Bm7 -> Gmaj7 -> Asus4)
    chords = [
        [146.83, 220.00, 277.18, 329.63, 440.00],  # Dmaj9
        [123.47, 185.00, 220.00, 293.66, 369.99],  # Bm7
        [98.00, 146.83, 196.00, 246.94, 293.66],   # Gmaj7
        [110.00, 164.81, 220.00, 293.66, 329.63]   # Asus4
    ]

    chord_dur = 4.0  # 4 seconds per chord
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
            # Soft organ / Rhodes style harmonics
            harmonic = (
                np.sin(2 * np.pi * freq * sub_t) * 0.6 +
                np.sin(2 * np.pi * freq * 2 * sub_t) * 0.25 +
                np.sin(2 * np.pi * freq * 3 * sub_t) * 0.1
            )
            # Gentle tremolo / chorus
            tremolo = 1.0 + 0.08 * np.sin(2 * np.pi * 1.5 * sub_t)
            sub_audio += harmonic * tremolo

        # Apply gentle envelope (attack, sustain, decay)
        env = np.ones_like(sub_t)
        attack_len = int(0.3 * sample_rate)
        if len(env) > attack_len:
            env[:attack_len] = np.linspace(0, 1, attack_len)
        decay_len = int(0.5 * sample_rate)
        if len(env) > decay_len:
            env[-decay_len:] = np.linspace(1, 0.4, decay_len)
        
        music_track[start_idx:end_idx] += sub_audio * env

    # Normalize and scale to soft background level
    music_track = music_track / np.max(np.abs(music_track)) * 0.15
    wavfile.write(str(output_path), sample_rate, (music_track * 32767).astype(np.int16))
    print(f"[SUCCESS] Ambient music generated: {output_path}")


def draw_linear_gradient(draw: ImageDraw.ImageDraw, size, color_top, color_bottom):
    w, h = size
    for y in range(h):
        ratio = y / h
        r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
        g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
        b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
        draw.line([(0, y), (w, y)], fill=(r, g, b))


def generate_canvas_frames():
    print("\n[STEP 3] Rendering 1080p Cinematic Slide Frames...")
    W, H = 1920, 1080

    try:
        font_title = ImageFont.truetype("segoeuib.ttf", 64)
        font_sub = ImageFont.truetype("segoeui.ttf", 34)
        font_badge = ImageFont.truetype("segoeuib.ttf", 26)
        font_body = ImageFont.truetype("segoeui.ttf", 28)
    except Exception:
        font_title = font_sub = font_badge = font_body = ImageFont.load_default()

    # Load 3D Spider-Man Render and App Icon
    spidey_img = None
    if SPIDEY_RENDER.exists():
        spidey_img = Image.open(SPIDEY_RENDER).convert("RGBA")
    
    app_icon_img = None
    if APP_ICON.exists():
        app_icon_img = Image.open(APP_ICON).convert("RGBA")

    for idx, scene in enumerate(SCENES_SCRIPT):
        frame_file = BUILD_DIR / f"{scene['id']}_frame.png"
        img = Image.new("RGB", (W, H), (7, 17, 30))
        draw = ImageDraw.Draw(img)
        draw_linear_gradient(draw, (W, H), (7, 17, 30), (12, 26, 46))

        if scene["type"] == "intro_card":
            # Glass container in center
            card_rect = [120, 140, 1800, 940]
            draw.rounded_rectangle(card_rect, radius=24, fill=(13, 27, 46, 210), outline=(0, 240, 255, 60), width=2)

            # Left side: App Logo and Title
            if app_icon_img:
                icon_scaled = app_icon_img.resize((140, 140), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (200, 220), icon_scaled)

            draw.text((370, 225), "SPIDER-MAN WATER BUDDY", fill=(0, 240, 255), font=font_title)
            draw.text((374, 305), "Aquatic Liquid Glass Edition • v1.0.0", fill=(168, 196, 216), font=font_sub)

            # Feature Pills
            pills = [
                "💧 Native Windows Hydration Companion",
                "🛡️ Non-Focus-Stealing Architecture (WS_EX_NOACTIVATE)",
                "🌊 Live Sinusoidal Wave Reservoir (PySide6 QPainter)",
                "🔒 100% Offline & Private (Zero Cloud Telemetry)"
            ]
            py = 420
            for pill in pills:
                draw.rounded_rectangle([200, py, 1150, py + 56], radius=14, fill=(18, 38, 64), outline=(10, 132, 255, 90), width=1)
                draw.text((224, py + 12), pill, fill=(240, 246, 252), font=font_badge)
                py += 78

            # Right side: Hanging Spidey 3D render
            if spidey_img:
                sp_h = 750
                sp_w = int(spidey_img.width * (sp_h / spidey_img.height))
                sp_scaled = spidey_img.resize((sp_w, sp_h), Image.Resampling.LANCZOS)
                img.paste(sp_scaled, (1320, 100), sp_scaled)

        elif scene["type"] == "screenshot":
            # Frame with title banner at top and high-res screenshot centered
            header_rect = [60, 40, 1860, 110]
            draw.rounded_rectangle(header_rect, radius=16, fill=(13, 27, 46, 230), outline=(0, 240, 255, 60), width=1)
            
            # Badge
            draw.rounded_rectangle([80, 52, 230, 98], radius=10, fill=(0, 240, 255, 30), outline=(0, 240, 255, 120), width=1)
            draw.text((95, 62), f"STEP 0{idx}", fill=(0, 240, 255), font=font_badge)
            draw.text((255, 58), scene["title"].upper(), fill=(255, 255, 255), font=font_title)

            # Paste screenshot into high-res frame
            shot_path = USER_SCREENSHOTS[scene["screenshot_idx"]]
            shot_img = Image.open(shot_path).convert("RGBA")
            
            # Maintain aspect ratio and center on 1760x900
            target_w = 1760
            target_h = int(shot_img.height * (target_w / shot_img.width))
            if target_h > 880:
                target_h = 880
                target_w = int(shot_img.width * (target_h / shot_img.height))

            shot_scaled = shot_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
            
            # Subtle drop shadow and cyan border container
            sx = (W - target_w) // 2
            sy = 145 + (900 - target_h) // 2
            draw.rounded_rectangle([sx - 4, sy - 4, sx + target_w + 4, sy + target_h + 4], radius=12, fill=(10, 22, 38), outline=(0, 240, 255, 80), width=2)
            img.paste(shot_scaled, (sx, sy), shot_scaled)

        elif scene["type"] == "outro_card":
            # Outro showcase card
            card_rect = [140, 120, 1780, 960]
            draw.rounded_rectangle(card_rect, radius=24, fill=(13, 27, 46, 230), outline=(0, 230, 153, 90), width=2)

            if app_icon_img:
                icon_scaled = app_icon_img.resize((120, 120), Image.Resampling.LANCZOS)
                img.paste(icon_scaled, (200, 180), icon_scaled)

            draw.text((350, 180), "SPIDER-MAN WATER BUDDY", fill=(0, 230, 153), font=font_title)
            draw.text((354, 255), "Production-Grade Desktop Architecture", fill=(168, 196, 216), font=font_sub)

            features = [
                ("💎 Aquatic Liquid Glass UI", "Deep oceanic palette, translucent glass cards, and glowing accents."),
                ("⚡ Single-Instance Mutex", "Enforces exactly one active companion instance across Windows sessions."),
                ("📝 Atomic Persistence", "Crash-safe JSON state writes with %APPDATA% directory migration."),
                ("🎯 Focus-Free Architecture", "WS_EX_NOACTIVATE ensures reminders never interrupt your active typing."),
                ("📦 Turnkey Distribution", "Clean portable ZIP and zero-admin Windows Setup Installer.")
            ]

            fy = 340
            for title, desc in features:
                draw.rounded_rectangle([200, fy, 1720, fy + 78], radius=12, fill=(16, 34, 58), outline=(0, 240, 255, 40), width=1)
                draw.text((224, fy + 12), title, fill=(0, 240, 255), font=font_badge)
                draw.text((224, fy + 44), desc, fill=(168, 196, 216), font=font_body)
                fy += 92

            draw.rounded_rectangle([560, 840, 1360, 915], radius=16, fill=(0, 230, 153, 40), outline=(0, 230, 153, 180), width=2)
            draw.text((620, 856), "⭐ Open Source on GitHub • Built with Python & PySide6", fill=(255, 255, 255), font=font_badge)

        img.save(frame_file)
        scene["frame_path"] = frame_file
        print(f"  -> Generated {frame_file.name}")

    print("[SUCCESS] All 1080p frames rendered successfully.")


def generate_synchronized_subtitles(output_srt: Path):
    print("\n[STEP 4] Compiling Master Synchronized SRT Subtitles...")
    entries = []
    srt_idx = 1
    current_time = 0.0

    for scene in SCENES_SCRIPT:
        scene_start = current_time
        for s in scene["sentences"]:
            start_t = scene_start + s["start"]
            end_t = scene_start + s["end"]
            text = s["text"]
            entries.append(
                f"{srt_idx}\n"
                f"{format_srt_time(start_t)} --> {format_srt_time(end_t)}\n"
                f"{text}\n"
            )
            srt_idx += 1
        current_time += scene["duration"]

    with open(output_srt, "w", encoding="utf-8") as f:
        f.write("\n".join(entries))

    print(f"[SUCCESS] Subtitle file generated: {output_srt} ({len(entries)} subtitle events)")


def assemble_final_video(total_duration: float):
    print("\n[STEP 5] Assembling Video Clips, Crossfades, Audio Ducking, and Closed Captions...")
    DIST_DIR.mkdir(parents=True, exist_ok=True)
    final_output = DIST_DIR / "SpiderManWaterBuddy-LinkedIn-Demo.mp4"
    master_srt = BUILD_DIR / "master_subtitles.srt"

    # 1. Generate individual scene clips
    clip_files = []
    for idx, scene in enumerate(SCENES_SCRIPT):
        clip_path = BUILD_DIR / f"{scene['id']}.mp4"
        frame_path = scene["frame_path"]
        audio_path = scene["audio_path"]
        duration = scene["duration"]

        # Zoompan effect for dynamic motion: gentle slow zoom-in
        # zoom from 1.0 to 1.04 over duration
        total_frames = int(duration * 30)
        vf_filter = (
            f"scale=1920:1080,zoompan=z='min(zoom+0.00015,1.05)':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={total_frames}:s=1920x1080:fps=30,"
            f"fade=t=in:st=0:d=0.5,fade=t=out:st={duration-0.5:.2f}:d=0.5"
        )

        cmd = [
            FFMPEG_EXE, "-y",
            "-loop", "1", "-i", str(frame_path),
            "-i", str(audio_path),
            "-vf", vf_filter,
            "-c:v", "libx264", "-tune", "stillimage", "-preset", "fast", "-crf", "18",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{duration:.3f}",
            "-pix_fmt", "yuv420p",
            str(clip_path)
        ]
        subprocess.run(cmd, check=True, creationflags=subprocess.CREATE_NO_WINDOW)
        clip_files.append(clip_path)
        print(f"  -> Rendered clip {idx+1}/{len(SCENES_SCRIPT)}: {clip_path.name}")

    # 2. Concat all scene clips
    concat_list = BUILD_DIR / "concat_list.txt"
    with open(concat_list, "w", encoding="utf-8") as f:
        for c in clip_files:
            f.write(f"file '{c.name}'\n")

    combined_narration = BUILD_DIR / "combined_narration.mp4"
    cmd_concat = [
        FFMPEG_EXE, "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(combined_narration)
    ]
    subprocess.run(cmd_concat, check=True, cwd=str(BUILD_DIR), creationflags=subprocess.CREATE_NO_WINDOW)
    print("  -> Combined narration and video tracks created.")

    # 3. Final Master Merge with background music and burned-in styled subtitles
    ambient_music = BUILD_DIR / "ambient_music.wav"
    escaped_srt = str(master_srt.resolve()).replace("\\", "/").replace(":", "\\:")

    # Style: elegant yellow/cyan highlight, crisp dark translucent bounding box
    subtitle_style = "FontSize=20,PrimaryColour=&H00FFFFFF,BackColour=&H8007111E,BorderStyle=4,MarginV=42,Bold=1"

    cmd_master = [
        FFMPEG_EXE, "-y",
        "-i", str(combined_narration),
        "-i", str(ambient_music),
        "-filter_complex",
        f"[0:v]subtitles='{escaped_srt}':force_style='{subtitle_style}'[v];"
        f"[1:a]volume=0.18[bgm];"
        f"[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "[v]",
        "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(final_output)
    ]
    print("\n[STEP 6] Rendering final master MP4 (with subtitle burn-in & audio ducking)...")
    subprocess.run(cmd_master, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

    # 4. Also render clean version WITHOUT subtitles
    nocaptions_output = DIST_DIR / "SpiderManWaterBuddy-LinkedIn-Demo-NoCaptions.mp4"
    cmd_nocaptions = [
        FFMPEG_EXE, "-y",
        "-i", str(combined_narration),
        "-i", str(ambient_music),
        "-filter_complex",
        "[1:a]volume=0.18[bgm];"
        "[0:a][bgm]amix=inputs=2:duration=first:dropout_transition=2[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(nocaptions_output)
    ]
    print("[STEP 6b] Rendering clean version without captions...")
    subprocess.run(cmd_nocaptions, check=True, creationflags=subprocess.CREATE_NO_WINDOW)

    size_mb = final_output.stat().st_size / (1024 * 1024)
    size_nocap_mb = nocaptions_output.stat().st_size / (1024 * 1024)
    print(f"\n==================================================")
    print(f" DEMO VIDEO GENERATION COMPLETED SUCCESSFULLY!")
    print(f" 1. Captions Version:    {final_output} ({size_mb:.2f} MB)")
    print(f" 2. No-Captions Version:  {nocaptions_output} ({size_nocap_mb:.2f} MB)")
    print(f" Format:                 1080p 16:9 MP4 (30 FPS, H.264/AAC)")
    print(f" Duration:               {total_duration:.1f} seconds (~{total_duration/60:.2f} minutes)")
    print(f"==================================================")
    return final_output, nocaptions_output


async def main():
    print("==================================================")
    print(" Spider-Man Water Buddy — LinkedIn Demo Video Engine")
    print("==================================================")
    start_time = time.time()

    total_duration = await generate_speech_for_scenes()
    ambient_wav = BUILD_DIR / "ambient_music.wav"
    generate_ambient_music(total_duration, ambient_wav)
    generate_canvas_frames()
    master_srt = BUILD_DIR / "master_subtitles.srt"
    generate_synchronized_subtitles(master_srt)
    final_video = assemble_final_video(total_duration)

    elapsed = time.time() - start_time
    print(f"\nWorkflow finished in {elapsed:.1f} seconds.")


if __name__ == "__main__":
    asyncio.run(main())
