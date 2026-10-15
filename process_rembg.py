import os
from rembg import remove, new_session
from PIL import Image
import numpy as np

def run_rembg():
    input_path = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\superhero_upside_down_render_1792078424266.jpg"
    output_dir = r"c:\Users\hp\Downloads\spider_watepop\assets\images"
    os.makedirs(output_dir, exist_ok=True)
    output_png = os.path.join(output_dir, "spidey_3d_render.png")
    artifact_png = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\spidey_3d_render.png"

    print("[INFO] Loading input image...")
    input_img = Image.open(input_path).convert("RGB")
    w, h = input_img.size
    print(f"[INFO] Image dimensions: {w}x{h}")

    print("[INFO] Initializing rembg U2-Net session...")
    session = new_session("u2net")

    print("[INFO] Executing high-precision alpha removal...")
    result = remove(
        input_img,
        session=session,
        alpha_matting=False,
    )

    # Let's verify and preserve the delicate web strand at the top
    # The web strand is near the vertical center (x around 370-400) from y=0 down to the hands
    res_arr = np.array(result)
    orig_arr = np.array(input_img)

    # Luminance of original
    lum = np.mean(orig_arr, axis=2)

    # Web region: top center strip
    web_x_min, web_x_max = int(w * 0.45), int(w * 0.55)
    web_y_max = int(h * 0.35)

    # Where original has bright web strand in the top region, ensure alpha is crisp
    web_mask = (lum[0:web_y_max, web_x_min:web_x_max] > 60)
    res_arr[0:web_y_max, web_x_min:web_x_max, 3] = np.maximum(
        res_arr[0:web_y_max, web_x_min:web_x_max, 3],
        (web_mask.astype(np.uint8) * 255)
    )

    final_img = Image.fromarray(res_arr, mode="RGBA")
    final_img.save(output_png, format="PNG", optimize=True)
    final_img.save(artifact_png, format="PNG", optimize=True)
    print(f"[SUCCESS] High-fidelity RGBA asset saved to: {output_png}")
    print(f"[SUCCESS] Artifact RGBA asset saved to: {artifact_png}")

if __name__ == "__main__":
    run_rembg()
