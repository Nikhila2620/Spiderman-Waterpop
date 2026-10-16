import os
import sys
from PIL import Image, ImageFilter
import numpy as np
from collections import deque

def process_superhero_image():
    input_path = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\superhero_upside_down_render_1792078424266.jpg"
    output_dir = r"c:\Users\hp\Downloads\spider_watepop\assets\images"
    os.makedirs(output_dir, exist_ok=True)
    output_png = os.path.join(output_dir, "spidey_3d_render.png")

    img = Image.open(input_path).convert("RGB")
    w, h = img.size
    print(f"[INFO] Loaded image size: {w}x{h}")

    arr = np.array(img, dtype=np.float32)

    # Luminance / brightness metric
    brightness = np.maximum(arr[:, :, 0], np.maximum(arr[:, :, 1], arr[:, :, 2]))

    # Seed-fill from borders to find exterior background
    # The background is pitch black, so threshold around 12-16
    bg_mask = np.zeros((h, w), dtype=bool)
    visited = np.zeros((h, w), dtype=bool)

    # Queue for BFS
    queue = deque()

    # Add all border pixels that have low brightness
    THRESHOLD = 14.0

    for x in range(w):
        if brightness[0, x] <= THRESHOLD:
            queue.append((0, x))
            visited[0, x] = True
        if brightness[h - 1, x] <= THRESHOLD:
            queue.append((h - 1, x))
            visited[h - 1, x] = True

    for y in range(h):
        if brightness[y, 0] <= THRESHOLD:
            queue.append((y, 0))
            visited[y, 0] = True
        if brightness[y, w - 1] <= THRESHOLD:
            queue.append((y, w - 1))
            visited[y, w - 1] = True

    # 4-connected BFS
    while queue:
        cy, cx = queue.popleft()
        bg_mask[cy, cx] = True

        for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
            if 0 <= ny < h and 0 <= nx < w and not visited[ny, nx]:
                visited[ny, nx] = True
                if brightness[ny, nx] <= THRESHOLD:
                    queue.append((ny, nx))

    # Foreground is the inverse of background
    fg_mask = ~bg_mask

    # To ensure smooth anti-aliased edges and prevent black fringing:
    # Convert mask to float 0.0 - 1.0
    alpha_raw = fg_mask.astype(np.float32) * 255.0
    alpha_img = Image.fromarray(alpha_raw.astype(np.uint8), mode="L")

    # Anti-alias feathering (slight gaussian blur on edges)
    alpha_blurred = alpha_img.filter(ImageFilter.GaussianBlur(radius=0.8))
    alpha_arr = np.array(alpha_blurred, dtype=np.float32) / 255.0

    # Ensure inner character is 100% solid alpha (erode mask before blur or clamp)
    eroded = alpha_img.filter(ImageFilter.MinFilter(size=3))
    eroded_arr = np.array(eroded, dtype=np.float32) / 255.0
    # Blend: solid inside, smooth at transition boundary
    final_alpha = np.where(eroded_arr > 0.5, 1.0, alpha_arr)

    # Assemble RGBA
    rgba_arr = np.zeros((h, w, 4), dtype=np.uint8)
    rgba_arr[:, :, :3] = np.array(img)
    rgba_arr[:, :, 3] = (final_alpha * 255.0).astype(np.uint8)

    result_img = Image.fromarray(rgba_arr, mode="RGBA")
    result_img.save(output_png, format="PNG", optimize=True)
    print(f"[SUCCESS] Saved transparent RGBA asset to: {output_png}")

    # Also copy to artifacts directory for display and link
    artifact_png = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\spidey_3d_render.png"
    result_img.save(artifact_png, format="PNG", optimize=True)
    print(f"[SUCCESS] Saved artifact PNG to: {artifact_png}")

if __name__ == "__main__":
    process_superhero_image()
