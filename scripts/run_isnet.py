from rembg import remove, new_session
from PIL import Image
import numpy as np

input_path = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\superhero_upside_down_render_1792078424266.jpg"
output_png = r"c:\Users\hp\Downloads\spider_watepop\assets\images\spidey_3d_render.png"
artifact_png = r"C:\Users\hp\.gemini\antigravity\brain\29ab4e7c-1a5c-4aaa-b822-f3b5ff9f107e\spidey_3d_render.png"

print("[INFO] Loading image...")
img = Image.open(input_path).convert("RGB")
w, h = img.size

session = new_session("isnet-general-use")
print("[INFO] Running ISNet high-precision inference...")
result = remove(img, session=session)

# Preserve the delicate web strand at the top center
res_arr = np.array(result)
orig_arr = np.array(img)
lum = np.mean(orig_arr, axis=2)

web_x1, web_x2 = int(w * 0.45), int(w * 0.55)
web_y2 = int(h * 0.35)
web_mask = (lum[0:web_y2, web_x1:web_x2] > 40)
res_arr[0:web_y2, web_x1:web_x2, 3] = np.maximum(
    res_arr[0:web_y2, web_x1:web_x2, 3],
    (web_mask.astype(np.uint8) * 255)
)

final_img = Image.fromarray(res_arr, mode="RGBA")
final_img.save(output_png, format="PNG", optimize=True)
final_img.save(artifact_png, format="PNG", optimize=True)
print("[SUCCESS] Output saved successfully with ISNet!")
