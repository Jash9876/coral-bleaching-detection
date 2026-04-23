"""
Coral Bleaching Detection using Digital Image Processing
=========================================================
Pipeline:
  1. Image Acquisition
  2. Preprocessing (Noise Reduction, Color Correction)
  3. Image Enhancement (CLAHE on LAB L-channel)
  4. Color Space Conversion (RGB → LAB, RGB → HSV)
  5. Coral Segmentation (LAB a-channel + Otsu + Morphology + CCA)
  6. Edge Detection (Canny)
  7. Feature Extraction (Whiteness, Red Index, Saturation)
  8. Bleaching Classification (Multi-signal scoring)
  9. Visualization (Heatmap, Overlay, Pipeline)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import base64
import io
from PIL import Image

# ============================================================
# 1. IMAGE ACQUISITION
# ============================================================
def load_image(path):
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: Cannot load image: {path}")
        sys.exit(1)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


# ============================================================
# 2. PREPROCESSING
# ============================================================
def preprocess(img):
    # Gentle noise reduction
    blurred = cv2.GaussianBlur(img, (5, 5), 0)

    # Gray-World Assumption for underwater color correction
    result = blurred.astype(np.float32)
    avg_B = np.mean(result[:,:,2])
    avg_G = np.mean(result[:,:,1])
    avg_R = np.mean(result[:,:,0])
    
    avg_gray = (avg_B + avg_G + avg_R) / 3
    
    # Scale channels to neutralize deep-water blue/green absorption
    result[:,:,0] = np.clip(result[:,:,0] * (avg_gray / (avg_R + 1e-6)), 0, 255)
    result[:,:,1] = np.clip(result[:,:,1] * (avg_gray / (avg_G + 1e-6)), 0, 255)
    result[:,:,2] = np.clip(result[:,:,2] * (avg_gray / (avg_B + 1e-6)), 0, 255)
    gray_world = result.astype(np.uint8)

    # Mild global min-max normalization to secure contrast
    corrected = cv2.normalize(gray_world, None, 0, 255, cv2.NORM_MINMAX)
    return corrected


# ============================================================
# 5. CORAL SEGMENTATION
# ============================================================
def segment_coral(img, raw_img=None):
    """
    Segment coral from water using HSV hue.
    
    Red/orange coral occupies warm hues (0-40, 150-180 in OpenCV's 0-180 range).
    Blue/cyan water occupies cool hues (80-130).
    This separation is much more robust than LAB B-channel, which gets confused
    after gray-world preprocessing equalizes all channels.
    
    Args:
        img: Preprocessed RGB image (used for fallback and morphology reference)
        raw_img: Original RGB image before preprocessing (preferred for hue detection)
    """
    # Use the PREPROCESSED image for color detection.
    # Raw underwater images have a pervasive blue tint that makes all pixels look
    # like hue 80-100. Gray-world preprocessing removes this tint, cleanly separating
    # coral (hue 0-30, 150-180) from water (hue 80-120).
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h = hsv[:, :, 0]  # Hue: 0-180 in OpenCV
    s = hsv[:, :, 1]  # Saturation: 0-255
    v = hsv[:, :, 2]  # Value: 0-255
    
    # INVERTED LOGIC: Detect blue/cyan WATER and exclude it.
    # Water hue is consistently 80-130 (blue-cyan range).
    # Coral can be ANY color (red, orange, yellow, green, purple, white, brown).
    # So we define: coral = NOT water.
    is_blue_water = (h >= 80) & (h <= 130) & (s > 30)
    
    # Also exclude very dark pixels (deep shadows / black borders) 
    # and very unsaturated dark pixels (not useful for analysis)
    is_too_dark = (v < 30)
    
    # Coral mask = everything that is NOT blue water and NOT pitch black
    coral_raw = (~is_blue_water & ~is_too_dark).astype(np.uint8) * 255
    
    # Clean up with elliptical kernels for organic edges
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(coral_raw, cv2.MORPH_OPEN, kernel_open, iterations=2)
    
    # Remove tiny noise specs but keep ALL significant coral regions.
    # A reef photo can have many separate coral colonies — we must keep them all.
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if num_labels <= 1:
        return np.zeros(img.shape[:2], dtype=np.uint8)
    
    # Minimum area threshold: 0.5% of total image area
    total_pixels = img.shape[0] * img.shape[1]
    min_area = total_pixels * 0.005
    
    coral_mask = np.zeros_like(mask)
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] >= min_area:
            coral_mask[labels == label_id] = 255
    
    # Fill internal holes in coral bodies
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    coral_mask = cv2.morphologyEx(coral_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    
    # Smooth boundaries for natural-looking edges
    coral_mask = cv2.medianBlur(coral_mask, 11)
    
    return coral_mask


# ============================================================
# 6. EDGE DETECTION
# ============================================================
def detect_edges(img, mask):
    masked = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(masked, cv2.COLOR_RGB2GRAY)
    return cv2.Canny(gray, 50, 150)


# ============================================================
# 7. FEATURE EXTRACTION + CLASSIFICATION
# ============================================================
def analyze_bleaching(img, mask):
    if np.sum(mask == 255) == 0:
        return {
            "bleach_pct": 0, "whiteness": 0, "red_index": 0,
            "mean_sat": 0, "health_score": 0, "status": "No Coral Detected",
            "bleach_mask": np.zeros_like(mask)
        }

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    coral_pixels = (mask == 255)

    # Shadow Exclusion
    shadow_mask = (v < 40)
    lit_coral_pixels = coral_pixels & ~shadow_mask
    
    # Fallback if the entire coral is in deep shadow
    if np.sum(lit_coral_pixels) < 10:
        lit_coral_pixels = coral_pixels

    sat_mean = np.mean(s[lit_coral_pixels])
    val_mean = np.mean(v[lit_coral_pixels])

    # Absolute + Relative Bounds for robust bleaching detection
    # If the coral is uniformly bleached, variance vanishes. So we widen the absolute safety net.
    bleach_cond_s = (s < sat_mean * 0.65) | (s < 60)
    bleach_cond_v = (v > val_mean * 1.08) | (v > 160)
    
    bleach_cond = bleach_cond_s & bleach_cond_v & coral_pixels
    bleach_mask = bleach_cond.astype(np.uint8) * 255
    bleach_mask = cv2.medianBlur(bleach_mask, 5)

    total_coral = np.sum(coral_pixels)
    bleach_pct = (np.sum(bleach_mask == 255) / total_coral) * 100

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    whiteness = np.mean(gray[coral_pixels]) / 255 * 100

    R = img[:, :, 0].astype(np.float32)
    G = img[:, :, 1].astype(np.float32)
    B = img[:, :, 2].astype(np.float32)
    red_index = np.mean((R / (R + G + B + 1e-6))[coral_pixels])
    mean_sat = sat_mean

    # Classification scoring (0 = Perfect Health, 100 = Completely Dead)
    scores = []
    
    # 1. Bleaching Pixel Penalty (Direct geometric thresholding)
    scores.append(min(bleach_pct * 2.0, 100))
    
    # 2. Whiteness Penalty (Healthy corals are dark, bleached are bright)
    scores.append(np.clip((whiteness - 35) / 40 * 100, 0, 100))
    
    # 3. Saturation Penalty (Healthy are vibrant > 90, bleached are dull < 50)
    scores.append(np.clip((90 - mean_sat) / 50 * 100, 0, 100))
    
    # 4. Red Index Penalty (Healthy are red > 0.40, bleached are gray/blue ~ 0.33)
    # The lower the red index, the higher the penalty.
    ri_score = np.clip((0.40 - red_index) / 0.10 * 100, 0, 100)
    scores.append(ri_score)

    health_score = np.mean(scores)

    # Global Overrides: If the coral is overall completely pale/gray, bypass the scoring matrix.
    if whiteness > 60 or mean_sat < 40 or bleach_pct > 35:
        status = "Severely Bleached"
    elif whiteness > 50 or mean_sat < 65 or red_index < 0.35:
        status = "Moderately Bleached"
    elif health_score > 60:
        status = "Severely Bleached"
    elif health_score > 35:
        status = "Moderately Bleached"
    else:
        status = "Healthy Coral"

    return {
        "bleach_pct": bleach_pct,
        "whiteness": whiteness,
        "red_index": red_index,
        "mean_sat": mean_sat,
        "health_score": health_score,
        "status": status,
        "bleach_mask": bleach_mask,
    }


# ============================================================
# 9. VISUALIZATION
# ============================================================
def visualize(original, preprocessed, mask, edges, results):
    coral_only = cv2.bitwise_and(preprocessed, preprocessed, mask=mask)

    hsv = cv2.cvtColor(preprocessed, cv2.COLOR_RGB2HSV)
    s = hsv[:, :, 1]
    s_inv = 255 - cv2.normalize(s, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_color = cv2.applyColorMap(s_inv, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(preprocessed, 0.6, heatmap_rgb, 0.4, 0)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    # Draw thicker, smoother contour for visibility
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 3)

    fig, axes = plt.subplots(2, 3, figsize=(16, 10))
    panels = [
        (original, "1. Original"),
        (preprocessed, "2. Preprocessed (Color Corrected)"),
        (coral_only, "3. Coral Segmented"),
        (results["bleach_mask"], "4. Bleaching Mask"),
        (overlay, "5. Health Heatmap"),
        (edges, "6. Edge Detection"),
    ]

    for ax, (img, title) in zip(axes.flat, panels):
        if len(img.shape) == 2:
            ax.imshow(img, cmap="gray")
        else:
            ax.imshow(img)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.axis("off")

    r = results
    fig.suptitle(
        f"Bleaching: {r['bleach_pct']:.1f}%  |  Status: {r['status']}\n"
        f"Whiteness: {r['whiteness']:.1f}%  |  Red Index: {r['red_index']:.3f}  |  "
        f"Mean Saturation: {r['mean_sat']:.1f}",
        fontsize=14, fontweight='bold', y=0.98
    )

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()


# ============================================================
# 10. WEB API HELPERS
# ============================================================
def get_base64_image(img, is_gray=False):
    """Helper to convert CV2 image to base64 for web display."""
    if is_gray:
        # Convert single channel to 3-channel BGR heatmap, then to RGB
        img = cv2.applyColorMap(img, cv2.COLORMAP_BONE) if len(img.shape) == 2 else img
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    
    pil_img = Image.fromarray(img)
    buff = io.BytesIO()
    pil_img.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")

def process_for_web(image_bytes):
    """Processes image and returns JSON-compatible results with base64 images."""
    # Convert bytes to cv2 image
    nparr = np.frombuffer(image_bytes, np.uint8)
    img_bgr = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    cv2.imwrite("debug.jpg", img_bgr)
    img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    
    # Run the pipeline
    preprocessed = preprocess(img_rgb)
    mask = segment_coral(preprocessed, raw_img=img_rgb)
    edges = detect_edges(preprocessed, mask)
    results = analyze_bleaching(preprocessed, mask)
    
    # Generate the visualization overlay (Panel 5)
    hsv = cv2.cvtColor(preprocessed, cv2.COLOR_RGB2HSV)
    s = hsv[:, :, 1]
    s_inv = 255 - cv2.normalize(s, None, 0, 255, cv2.NORM_MINMAX)
    heatmap_color = cv2.applyColorMap(s_inv, cv2.COLORMAP_JET)
    heatmap_rgb = cv2.cvtColor(heatmap_color, cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(preprocessed, 0.6, heatmap_rgb, 0.4, 0)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cv2.drawContours(overlay, contours, -1, (0, 255, 0), 3)

    coral_only = cv2.bitwise_and(preprocessed, preprocessed, mask=mask)
    
    # Collect Base64 images for all 6 panels
    results["images"] = {
        "original": get_base64_image(img_rgb),
        "preprocessed": get_base64_image(preprocessed),
        "segmented": get_base64_image(coral_only),
        "bleach_mask": get_base64_image(results["bleach_mask"], is_gray=True),
        "heatmap": get_base64_image(overlay),
        "edges": get_base64_image(edges, is_gray=True)
    }
    
    return results

def process_image(path):
    print(f"\nProcessing: {os.path.basename(path)}")
    print("=" * 50)
    original = load_image(path)
    preprocessed = preprocess(original)

    mask = segment_coral(preprocessed, raw_img=original)
    coral_area = np.sum(mask == 255)
    total_area = mask.shape[0] * mask.shape[1]
    print(f"  Coral area: {coral_area / total_area * 100:.1f}% of image")

    edges = detect_edges(preprocessed, mask)
    results = analyze_bleaching(preprocessed, mask)

    print(f"  Bleaching: {results['bleach_pct']:.1f}%")
    print(f"  Whiteness: {results['whiteness']:.1f}%")
    print(f"  Red Index: {results['red_index']:.3f}")
    print(f"  Mean Saturation: {results['mean_sat']:.1f}")
    print(f"  Health Score: {results['health_score']:.1f}")
    print(f"  => Status: {results['status']}")

    visualize(original, preprocessed, mask, edges, results)
    return results


if __name__ == "__main__":
    test_image = r"C:\Users\Jashwanth\Downloads\CoralDIP\healthy_corals\9944219035_5c47b13e8f_o.jpg"
    if not os.path.exists(test_image):
        folder = r"C:\Users\Jashwanth\Downloads\CoralDIP\healthy_corals"
        if os.path.isdir(folder):
            files = [f for f in os.listdir(folder) if f.lower().endswith(('.jpg', '.png'))]
            test_image = os.path.join(folder, files[0])
    process_image(test_image)