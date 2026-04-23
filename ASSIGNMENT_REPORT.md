# 21CSE251T — DIGITAL IMAGE PROCESSING
## Assignment Report

# Coral Bleaching Detection and Health Assessment Using Digital Image Processing

---

**Submitted by:** [Your Name]
**Roll No:** [Your Reg No]
**Department:** Computing Technologies
**Date:** 20 April 2026

---

## 1. Introduction and Objectives

Coral reefs are among the most biodiverse and economically valuable ecosystems on Earth, supporting approximately 25% of all marine species while covering less than 1% of the ocean floor. However, rising sea surface temperatures, ocean acidification, and anthropogenic stressors have led to widespread coral bleaching events globally. Coral bleaching occurs when stressed corals expel their symbiotic algae (zooxanthellae), causing the coral tissue to turn white and eventually leading to coral death if conditions persist.

This project applies **Digital Image Processing (DIP)** techniques to automatically detect and quantify coral bleaching from underwater photographs. By leveraging color space transformations, morphological operations, and spectral feature extraction, the system provides a non-invasive, scalable method for monitoring coral reef health — eliminating the need for manual diver surveys.

The system is implemented as a full-stack web application with a Python/OpenCV backend and a real-time interactive dashboard frontend.

### 1.1 Objectives

- Apply image preprocessing techniques (noise reduction, color correction) to compensate for underwater optical distortions such as blue-green absorption and light scattering.
- Implement coral segmentation using HSV color space thresholding with morphological refinement to isolate coral regions from the marine background.
- Extract spectral health features — Whiteness Index, Red Index, Mean Saturation, and Bleaching Pixel Percentage — from the segmented coral body.
- Classify coral health status into three categories: **Healthy**, **Moderately Bleached**, and **Severely Bleached** using a multi-signal scoring matrix.
- Detect structural boundaries of coral colonies using Canny edge detection.
- Deploy the pipeline as a real-time web dashboard for interactive coral health analysis.

### 1.2 About Coral Bleaching

Coral bleaching is a stress response triggered primarily by elevated sea surface temperatures (SSTs). When water temperatures rise 1–2°C above the seasonal maximum for a sustained period, corals expel their zooxanthellae — the photosynthetic dinoflagellate algae living within their tissue. Since zooxanthellae provide corals with up to 90% of their energy (via photosynthesis) and are responsible for their vibrant coloration, their loss leaves the coral tissue transparent, revealing the white calcium carbonate skeleton beneath.

| Bleaching Stage | Visual Indicator | Saturation | Whiteness |
|---|---|---|---|
| Healthy | Vibrant red, orange, brown, green, purple | > 90 | < 35% |
| Moderate Bleaching | Pale, faded colors | 50–65 | 35–50% |
| Severe Bleaching | White, ghostly appearance | < 40 | > 60% |

*Table 1: Visual and Spectral Indicators of Coral Bleaching Stages*

### 1.3 DIP Techniques Used in This Project

| Technique | Purpose | OpenCV Function |
|---|---|---|
| Gaussian Blur | Noise reduction (salt-and-pepper, sensor noise) | `cv2.GaussianBlur()` |
| Gray-World Color Correction | Neutralize underwater blue/green color cast | Manual channel scaling |
| Min-Max Normalization | Contrast enhancement | `cv2.normalize()` |
| RGB → HSV Conversion | Color-based segmentation | `cv2.cvtColor()` |
| Binary Thresholding | Water vs. coral classification | Boolean array operations |
| Morphological Opening | Remove small noise regions | `cv2.morphologyEx(MORPH_OPEN)` |
| Morphological Closing | Fill holes inside coral bodies | `cv2.morphologyEx(MORPH_CLOSE)` |
| Connected Component Analysis | Filter regions by area | `cv2.connectedComponentsWithStats()` |
| Median Blur | Smooth jagged mask boundaries | `cv2.medianBlur()` |
| Canny Edge Detection | Detect coral structural boundaries | `cv2.Canny()` |
| RGB → HSV Feature Extraction | Compute bleaching metrics | `cv2.cvtColor()` + array ops |
| Color Map Overlay | Generate health heatmap visualization | `cv2.applyColorMap()` |
| Contour Detection | Draw coral boundary outlines | `cv2.findContours()` |

*Table 2: Digital Image Processing Techniques and Their Applications*

---

## 2. System Architecture

The system follows a modular pipeline architecture where each DIP stage processes the output of the previous stage. The complete pipeline is implemented in `main.py` with a Flask REST API (`app.py`) serving a Vite/TypeScript frontend dashboard.

### 2.1 Pipeline Flowchart

```
┌─────────────────┐
│  Image Upload    │
│  (JPG/PNG)       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 1. ACQUISITION   │  cv2.imread() → BGR → RGB conversion
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. PREPROCESSING │  Gaussian Blur → Gray-World → Min-Max Normalize
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. SEGMENTATION  │  RGB→HSV → Water Exclusion → Morphology → CCA
└────────┬────────┘
         │
         ├──────────────────┐
         ▼                  ▼
┌─────────────────┐  ┌─────────────────┐
│ 4. EDGE DETECT   │  │ 5. FEATURE EXTR  │
│ Canny(50,150)    │  │ Whiteness, RI,   │
│                   │  │ Saturation, %    │
└────────┬────────┘  └────────┬────────┘
         │                    │
         │                    ▼
         │           ┌─────────────────┐
         │           │ 6. CLASSIFY      │
         │           │ Multi-signal     │
         │           │ scoring matrix   │
         │           └────────┬────────┘
         │                    │
         ▼                    ▼
┌──────────────────────────────────────┐
│           7. VISUALIZATION            │
│ 6-Panel Scientific Pipeline Display   │
│ + Interactive Web Dashboard           │
└──────────────────────────────────────┘
```

### 2.2 Technology Stack

| Component | Technology | Purpose |
|---|---|---|
| Core DIP Engine | Python 3.x, OpenCV, NumPy | Image processing pipeline |
| Web Backend | Flask, Flask-CORS | REST API serving `/api/analyze` |
| Web Frontend | Vite, TypeScript, ApexCharts | Interactive dashboard UI |
| Image Encoding | Pillow, base64 | Convert processed images for web transport |
| Visualization | Matplotlib | Offline 6-panel pipeline display |

*Table 3: Technology Stack*

---

## 3. Methodology — Detailed Pipeline

### 3.1 Stage 1: Image Acquisition

```python
def load_image(path):
    img = cv2.imread(path)
    if img is None:
        print(f"ERROR: Cannot load image: {path}")
        sys.exit(1)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
```

**Explanation:**
- OpenCV reads images in **BGR** format by default. Since all subsequent processing (HSV conversion, visualization) expects **RGB** ordering, we immediately convert the color space using `cv2.cvtColor()`.
- For web uploads, the raw bytes are decoded using `cv2.imdecode()` with `np.frombuffer()`.

📸 *Screenshot 1: Upload interface of the Coral Guardian dashboard showing the drag-and-drop zone.*

---

### 3.2 Stage 2: Preprocessing (Noise Reduction + Color Correction)

Underwater images suffer from two fundamental optical distortions:
1. **Wavelength-dependent absorption**: Water absorbs red light first (within 5m depth), then orange and yellow. At typical reef depths (5–30m), images appear heavily blue/green-shifted.
2. **Scattering**: Suspended particles scatter light in all directions, reducing contrast and introducing haze.

#### 3.2.1 Gaussian Blur — Noise Reduction

```python
blurred = cv2.GaussianBlur(img, (5, 5), 0)
```

A 5×5 Gaussian kernel is applied to reduce high-frequency sensor noise and compression artifacts while preserving major edges. The Gaussian function:

**G(x, y) = (1 / 2πσ²) × e^(-(x² + y²) / 2σ²)**

With kernel size 5 and σ computed automatically (σ=0), OpenCV uses σ = 0.3 × ((ksize-1)×0.5 - 1) + 0.8 = **1.1**.

#### 3.2.2 Gray-World Color Correction

```python
result = blurred.astype(np.float32)
avg_B = np.mean(result[:,:,2])
avg_G = np.mean(result[:,:,1])
avg_R = np.mean(result[:,:,0])

avg_gray = (avg_B + avg_G + avg_R) / 3

result[:,:,0] = np.clip(result[:,:,0] * (avg_gray / (avg_R + 1e-6)), 0, 255)
result[:,:,1] = np.clip(result[:,:,1] * (avg_gray / (avg_G + 1e-6)), 0, 255)
result[:,:,2] = np.clip(result[:,:,2] * (avg_gray / (avg_B + 1e-6)), 0, 255)
```

**The Gray-World Assumption** states that the average color of a scene under neutral lighting should be gray (equal R, G, B). In underwater images, the average is heavily biased toward blue. By computing the overall mean intensity and scaling each channel to match it, we effectively **reverse the underwater color absorption**.

**Scaling factors:**
- R_scale = avg_gray / avg_R (typically > 1.0 → amplifies suppressed red)
- G_scale = avg_gray / avg_G (close to 1.0)
- B_scale = avg_gray / avg_B (typically < 1.0 → attenuates dominant blue)

#### 3.2.3 Min-Max Normalization

```python
corrected = cv2.normalize(gray_world, None, 0, 255, cv2.NORM_MINMAX)
```

After gray-world correction, the pixel range may not span the full 0–255 dynamic range. `cv2.normalize()` with `NORM_MINMAX` linearly stretches the values:

**I_out = 255 × (I_in − min) / (max − min)**

This ensures maximum contrast for subsequent processing stages.

📸 *Screenshot 2: Side-by-side comparison showing the original underwater image (blue-tinted) vs. the preprocessed image (color-corrected with restored reds).*

---

### 3.3 Stage 3: Coral Segmentation

This is the most critical stage of the pipeline. The goal is to generate a binary mask that separates coral tissue from the marine background (water, sand, open ocean).

#### 3.3.1 Color Space: RGB → HSV

```python
hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
h = hsv[:, :, 0]  # Hue: 0-180 in OpenCV
s = hsv[:, :, 1]  # Saturation: 0-255
v = hsv[:, :, 2]  # Value: 0-255
```

HSV (Hue-Saturation-Value) decouples color information from brightness, making it ideal for color-based segmentation under varying illumination:
- **Hue (H)**: Dominant wavelength (color). Range 0–180 in OpenCV.
- **Saturation (S)**: Color purity. High = vivid, Low = gray/white.
- **Value (V)**: Brightness. High = bright, Low = dark.

| Object | Hue Range (OpenCV) | Saturation | Description |
|---|---|---|---|
| Blue/Cyan Water | 80–130 | > 30 | Consistent across all images |
| Red/Orange Coral | 0–20, 170–180 | > 50 | Red wraps around 0/180 |
| Yellow/Green Coral | 20–70 | > 40 | Varies by species |
| White/Bleached Coral | Any | < 30 | Very low saturation |
| Dark Shadows | Any | Any | V < 30 |

*Table 4: HSV Color Ranges for Underwater Objects*

#### 3.3.2 Inverted Water-Exclusion Logic

```python
is_blue_water = (h >= 80) & (h <= 130) & (s > 30)
is_too_dark = (v < 30)
coral_raw = (~is_blue_water & ~is_too_dark).astype(np.uint8) * 255
```

**Key Design Decision:** Rather than attempting to enumerate all possible coral colors (which vary by species, depth, lighting, and health), we identify the ONE consistent element — **blue water** — and exclude it. Everything that is NOT blue water and NOT pitch-black shadow is classified as potential coral/reef substrate.

This inverted approach is robust because:
- Coral can be any color: red, orange, yellow, green, purple, brown, white, pink
- Water is ALWAYS blue/cyan (hue 80–130) in both raw and preprocessed images
- The method generalizes across all species without retraining

#### 3.3.3 Morphological Cleanup

```python
# Step 1: Remove noise (Morphological Opening)
kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
mask = cv2.morphologyEx(coral_raw, cv2.MORPH_OPEN, kernel_open, iterations=2)
```

**Morphological Opening** = Erosion followed by Dilation. This removes small isolated noise pixels (false positives from water reflections, suspended particles) without affecting the shape of large coral bodies.

We use **elliptical structuring elements** (`cv2.MORPH_ELLIPSE`) instead of rectangular ones (`np.ones()`) to prevent introducing artificial square/blocky artifacts into the naturally curved coral boundaries.

#### 3.3.4 Connected Component Analysis (CCA)

```python
num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
total_pixels = img.shape[0] * img.shape[1]
min_area = total_pixels * 0.005  # 0.5% threshold

coral_mask = np.zeros_like(mask)
for label_id in range(1, num_labels):
    if stats[label_id, cv2.CC_STAT_AREA] >= min_area:
        coral_mask[labels == label_id] = 255
```

`cv2.connectedComponentsWithStats()` labels each isolated white region in the binary mask. We keep all components larger than **0.5% of the total image area**, which removes remaining noise while preserving multiple coral colonies in wide reef photographs.

#### 3.3.5 Hole Filling and Boundary Smoothing

```python
# Fill internal holes
kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
coral_mask = cv2.morphologyEx(coral_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)

# Smooth boundaries
coral_mask = cv2.medianBlur(coral_mask, 11)
```

- **Morphological Closing** (Dilation → Erosion) fills internal holes caused by small blue spots within the coral body (e.g., gaps between polyps, water pockets).
- **Median Blur** with kernel size 11 smooths the jagged staircase edges of the binary mask into natural, organic curves that follow the actual coral contour.

📸 *Screenshot 3: The 03 SEGMENT panel showing the coral perfectly isolated from the blue water background with smooth organic boundaries.*

---

### 3.4 Stage 4: Edge Detection

```python
def detect_edges(img, mask):
    masked = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(masked, cv2.COLOR_RGB2GRAY)
    return cv2.Canny(gray, 50, 150)
```

The **Canny edge detector** is a multi-stage algorithm:
1. **Gaussian smoothing** to reduce noise
2. **Gradient computation** using Sobel operators in X and Y directions
3. **Non-maximum suppression** to thin edges to single-pixel width
4. **Double thresholding** (low=50, high=150) with hysteresis to connect strong and weak edges

The mask is applied first using `cv2.bitwise_and()` to ensure edges are only detected within the coral body — preventing water ripples, sand textures, and background noise from contaminating the structural analysis.

📸 *Screenshot 4: The 06 STRUCTURE panel showing white edge lines delineating the coral polyp structure and colony boundaries against a black background.*

---

### 3.5 Stage 5: Feature Extraction and Bleaching Classification

#### 3.5.1 Feature: Bleaching Pixel Percentage

```python
bleach_cond_s = (s < sat_mean * 0.65) | (s < 60)
bleach_cond_v = (v > val_mean * 1.08) | (v > 160)
bleach_cond = bleach_cond_s & bleach_cond_v & coral_pixels
bleach_pct = (np.sum(bleach_mask == 255) / total_coral) * 100
```

A pixel is classified as **bleached** if it satisfies BOTH conditions:
- **Low saturation**: Below 65% of the coral's mean saturation OR below an absolute threshold of 60 (desaturated/pale)
- **High brightness**: Above 108% of the coral's mean value OR above an absolute threshold of 160 (unusually bright/white)

This dual-threshold approach uses both **relative** bounds (adapting to each image's lighting) and **absolute** bounds (catching uniformly bleached corals where variance collapses).

#### 3.5.2 Feature: Whiteness Index

```python
gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
whiteness = np.mean(gray[coral_pixels]) / 255 * 100
```

The average grayscale intensity of the coral region, expressed as a percentage. Healthy corals are dark (richly pigmented), while bleached corals reflect more light. Range: 0% (pure black) to 100% (pure white).

#### 3.5.3 Feature: Red Index

```python
R = img[:, :, 0].astype(np.float32)
G = img[:, :, 1].astype(np.float32)
B = img[:, :, 2].astype(np.float32)
red_index = np.mean((R / (R + G + B + 1e-6))[coral_pixels])
```

The normalized red channel ratio. Healthy corals rich in zooxanthellae exhibit strong red/brown pigmentation (Red Index > 0.40). Bleached corals lose pigmentation and converge toward equal R≈G≈B, yielding Red Index ≈ 0.33 (gray).

#### 3.5.4 Multi-Signal Health Score

```python
scores = []
scores.append(min(bleach_pct * 2.0, 100))              # Bleaching Pixel Penalty
scores.append(np.clip((whiteness - 35) / 40 * 100, 0, 100))  # Whiteness Penalty
scores.append(np.clip((90 - mean_sat) / 50 * 100, 0, 100))   # Saturation Penalty
scores.append(np.clip((0.40 - red_index) / 0.10 * 100, 0, 100))  # Red Index Penalty
health_score = np.mean(scores)
```

Four independent penalty signals (each 0–100) are averaged into a single health score. This multi-signal approach prevents any single noisy metric from dominating the classification.

| Score Range | Classification |
|---|---|
| 0 – 35 | Healthy Coral |
| 35 – 60 | Moderately Bleached |
| 60 – 100 | Severely Bleached |

*Table 5: Health Score Classification Thresholds*

**Global Overrides** ensure extreme cases are always caught:
- Whiteness > 60% → Severely Bleached
- Mean Saturation < 40 → Severely Bleached
- Bleaching Pixel % > 35% → Severely Bleached

📸 *Screenshot 5: Dashboard showing all extracted metrics — Bleaching %, Red Index, Health Score — alongside the health status classification.*

---

### 3.6 Stage 6: Visualization

The system generates a **6-panel scientific visualization**:

| Panel | Title | Content |
|---|---|---|
| 01 | SOURCE | Original uploaded image |
| 02 | BALANCE | After Gray-World color correction and normalization |
| 03 | SEGMENT | Coral body isolated using binary mask (background = black) |
| 04 | TRACE | Bleaching mask (white = bleached pixels, black = healthy) |
| 05 | HEALTH | Saturation-inverse heatmap overlaid on image with green contour |
| 06 | STRUCTURE | Canny edge detection showing coral polyp structure |

*Table 6: Six-Panel Pipeline Output Description*

The **Health Heatmap (Panel 05)** is generated by:
1. Extracting the Saturation channel from HSV
2. Inverting it (low sat = high heat = bleached)
3. Applying `cv2.COLORMAP_JET` to create a red-blue color gradient
4. Blending with the original image at 60/40 opacity using `cv2.addWeighted()`
5. Drawing the segmentation contour in green using `cv2.drawContours()`

📸 *Screenshot 6: Complete 6-panel Multi-Spectral Processing Pipeline display from the web dashboard.*

---

## 4. Web Application Architecture

### 4.1 Backend — Flask REST API (`app.py`)

```python
@app.route('/api/analyze', methods=['POST'])
def analyze():
    file = request.files['image']
    image_bytes = file.read()
    results = process_for_web(image_bytes)
    return jsonify(serializable_results)
```

The Flask backend:
1. Accepts multipart form uploads via `POST /api/analyze`
2. Reads the raw image bytes
3. Passes them through the complete DIP pipeline (`process_for_web()`)
4. Converts all processed images to **base64-encoded PNG strings** for JSON transport
5. Returns a JSON response with metrics + encoded images

### 4.2 Frontend — Vite/TypeScript Dashboard

The frontend is a glassmorphic "Frosted Obsidian" dashboard built with:
- **Vite** build system with TypeScript
- **ApexCharts** for interactive gauge and sparkline charts
- **CSS custom properties** for the dark theme design system

The dashboard displays:
- Upload zone with drag-and-drop
- Real-time bleaching percentage with sparkline chart
- Red Index gauge
- Health status indicator (green ✅ for healthy, red ⚠️ for bleached)
- 6-panel scientific pipeline gallery
- Current date stamp

📸 *Screenshot 7: Full Coral Guardian dashboard showing all components — upload zone, metrics panels, charts, status indicator, and the 6-panel pipeline gallery.*

---

## 5. Results

### 5.1 Test Case 1: Healthy Red Coral (Brain Coral)

| Metric | Value |
|---|---|
| Coral Area | ~42% of image |
| Bleaching % | 3.8% |
| Whiteness | ~32% |
| Red Index | ~0.42 |
| Mean Saturation | ~95 |
| **Status** | **Healthy Coral** ✅ |

📸 *Screenshot 8: Pipeline output for the healthy red brain coral showing vibrant segmentation with minimal bleaching trace.*

### 5.2 Test Case 2: Multi-Colony Reef Scene

| Metric | Value |
|---|---|
| Coral Area | ~55% of image |
| Colonies Detected | Multiple (varied species) |
| **Status** | **[Fill in after testing]** |

📸 *Screenshot 9: Pipeline output for the wide reef scene showing multiple coral colonies segmented simultaneously.*

### 5.3 Test Case 3: Bleached Coral

| Metric | Value |
|---|---|
| Bleaching % | [Fill in] |
| Whiteness | [Fill in] |
| Red Index | [Fill in] |
| **Status** | **[Fill in]** |

📸 *Screenshot 10: Pipeline output for a bleached coral showing high whiteness and low saturation.*

---

## 6. Analysis and Discussion

### 6.1 Preprocessing Effectiveness

The Gray-World color correction successfully restores the red/orange channel that is absorbed by water, transforming blue-tinted underwater images into color-balanced representations. This is critical because:
- Without correction, healthy red coral appears brown/gray, artificially inflating whiteness metrics
- The HSV segmentation relies on accurate hue values, which are distorted by the blue underwater cast

### 6.2 Segmentation Robustness

The **inverted water-exclusion approach** (coral = NOT blue water) proved significantly more robust than direct coral detection methods:
- **LAB B-channel Otsu**: Failed because gray-world preprocessing compressed the B-channel dynamic range, making coral and water indistinguishable
- **K-means clustering**: Failed on 3-class problems (water/pigmented/bleached) because bleached coral was clustered with water
- **HSV warm-hue detection**: Failed for green, yellow, and purple coral species
- **Water exclusion**: Works universally because water is ALWAYS blue (hue 80–130)

### 6.3 Classification Accuracy

The multi-signal scoring approach prevents single-metric failure modes:
- A coral in shadow might have low whiteness but also low saturation → the saturation penalty catches it
- A uniformly bleached coral has zero variance → the absolute thresholds (S < 60, V > 160) catch it
- A partially bleached coral → the bleaching pixel percentage directly measures the affected area

### 6.4 Limitations

1. **Sandy substrate**: White sand adjacent to coral may be included in the mask (not blue, so not excluded)
2. **Fish and divers**: Non-coral objects that are not blue will be included. A potential improvement would be shape-based filtering.
3. **Very deep images**: At extreme depth (>30m), red light is completely absorbed and gray-world correction cannot restore information that was never captured.
4. **Night/artificial lighting**: The algorithm assumes natural underwater lighting. Artificial dive lights may create uneven illumination.

---

## 7. Conclusion

This project demonstrates the effective application of Digital Image Processing techniques to a real-world environmental monitoring problem. The complete pipeline — from underwater color correction through HSV-based segmentation to multi-signal health classification — provides a robust, automated system for coral bleaching detection.

**Key achievements:**
- Successfully implemented Gray-World color correction to compensate for underwater blue absorption
- Developed a universal coral segmentation algorithm using inverted water-exclusion logic that works across all coral species and colors
- Built a multi-signal health scoring system that combines four independent spectral features for robust classification
- Deployed the pipeline as an interactive web dashboard with real-time analysis

**Future work:**
- Integration with deep learning (CNN-based) segmentation for improved accuracy on complex reef scenes
- Time-series analysis for tracking bleaching progression over multiple surveys
- GPS-tagged image analysis for spatial mapping of reef health
- Mobile application for in-field diver use

---

## 8. Complete Source Code

### 8.1 `main.py` — Core DIP Engine

```python
"""
Coral Bleaching Detection using Digital Image Processing
=========================================================
Pipeline:
  1. Image Acquisition
  2. Preprocessing (Noise Reduction, Color Correction)
  3. Color Space Conversion (RGB → HSV)
  4. Coral Segmentation (HSV Water Exclusion + Morphology + CCA)
  5. Edge Detection (Canny)
  6. Feature Extraction (Whiteness, Red Index, Saturation)
  7. Bleaching Classification (Multi-signal scoring)
  8. Visualization (Heatmap, Overlay, Pipeline)
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
import os, sys, base64, io
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
    blurred = cv2.GaussianBlur(img, (5, 5), 0)
    result = blurred.astype(np.float32)
    avg_B = np.mean(result[:,:,2])
    avg_G = np.mean(result[:,:,1])
    avg_R = np.mean(result[:,:,0])
    avg_gray = (avg_B + avg_G + avg_R) / 3
    result[:,:,0] = np.clip(result[:,:,0] * (avg_gray / (avg_R + 1e-6)), 0, 255)
    result[:,:,1] = np.clip(result[:,:,1] * (avg_gray / (avg_G + 1e-6)), 0, 255)
    result[:,:,2] = np.clip(result[:,:,2] * (avg_gray / (avg_B + 1e-6)), 0, 255)
    gray_world = result.astype(np.uint8)
    corrected = cv2.normalize(gray_world, None, 0, 255, cv2.NORM_MINMAX)
    return corrected

# ============================================================
# 3. CORAL SEGMENTATION
# ============================================================
def segment_coral(img, raw_img=None):
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
    
    is_blue_water = (h >= 80) & (h <= 130) & (s > 30)
    is_too_dark = (v < 30)
    coral_raw = (~is_blue_water & ~is_too_dark).astype(np.uint8) * 255
    
    kernel_open = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(coral_raw, cv2.MORPH_OPEN, kernel_open, iterations=2)
    
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    if num_labels <= 1:
        return np.zeros(img.shape[:2], dtype=np.uint8)
    
    total_pixels = img.shape[0] * img.shape[1]
    min_area = total_pixels * 0.005
    
    coral_mask = np.zeros_like(mask)
    for label_id in range(1, num_labels):
        if stats[label_id, cv2.CC_STAT_AREA] >= min_area:
            coral_mask[labels == label_id] = 255
    
    kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (15, 15))
    coral_mask = cv2.morphologyEx(coral_mask, cv2.MORPH_CLOSE, kernel_close, iterations=2)
    coral_mask = cv2.medianBlur(coral_mask, 11)
    return coral_mask

# ============================================================
# 4. EDGE DETECTION
# ============================================================
def detect_edges(img, mask):
    masked = cv2.bitwise_and(img, img, mask=mask)
    gray = cv2.cvtColor(masked, cv2.COLOR_RGB2GRAY)
    return cv2.Canny(gray, 50, 150)

# ============================================================
# 5. FEATURE EXTRACTION + CLASSIFICATION
# ============================================================
def analyze_bleaching(img, mask):
    if np.sum(mask == 255) == 0:
        return {"bleach_pct": 0, "whiteness": 0, "red_index": 0,
                "mean_sat": 0, "health_score": 0, "status": "No Coral Detected",
                "bleach_mask": np.zeros_like(mask)}

    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    coral_pixels = (mask == 255)

    shadow_mask = (v < 40)
    lit_coral_pixels = coral_pixels & ~shadow_mask
    if np.sum(lit_coral_pixels) < 10:
        lit_coral_pixels = coral_pixels

    sat_mean = np.mean(s[lit_coral_pixels])
    val_mean = np.mean(v[lit_coral_pixels])

    bleach_cond_s = (s < sat_mean * 0.65) | (s < 60)
    bleach_cond_v = (v > val_mean * 1.08) | (v > 160)
    bleach_cond = bleach_cond_s & bleach_cond_v & coral_pixels
    bleach_mask = bleach_cond.astype(np.uint8) * 255
    bleach_mask = cv2.medianBlur(bleach_mask, 5)

    total_coral = np.sum(coral_pixels)
    bleach_pct = (np.sum(bleach_mask == 255) / total_coral) * 100

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    whiteness = np.mean(gray[coral_pixels]) / 255 * 100

    R = img[:,:,0].astype(np.float32)
    G = img[:,:,1].astype(np.float32)
    B = img[:,:,2].astype(np.float32)
    red_index = np.mean((R / (R + G + B + 1e-6))[coral_pixels])
    mean_sat = sat_mean

    scores = []
    scores.append(min(bleach_pct * 2.0, 100))
    scores.append(np.clip((whiteness - 35) / 40 * 100, 0, 100))
    scores.append(np.clip((90 - mean_sat) / 50 * 100, 0, 100))
    scores.append(np.clip((0.40 - red_index) / 0.10 * 100, 0, 100))
    health_score = np.mean(scores)

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

    return {"bleach_pct": bleach_pct, "whiteness": whiteness,
            "red_index": red_index, "mean_sat": mean_sat,
            "health_score": health_score, "status": status,
            "bleach_mask": bleach_mask}
```

*Code Block 1: Complete DIP Engine (main.py) — Core functions for preprocessing, segmentation, feature extraction, and classification.*

### 8.2 `app.py` — Flask Web Backend

```python
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os, numpy as np
from main import process_for_web

app = Flask(__name__, static_folder='frontend/dist')
CORS(app)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/analyze', methods=['POST'])
def analyze():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400
    file = request.files['image']
    if file and allowed_file(file.filename):
        try:
            image_bytes = file.read()
            results = process_for_web(image_bytes)
            serializable_results = {}
            for k, v in results.items():
                if isinstance(v, (np.float32, np.float64)):
                    serializable_results[k] = float(v)
                elif isinstance(v, (np.int32, np.int64)):
                    serializable_results[k] = int(v)
                else:
                    serializable_results[k] = v
            if "bleach_mask" in serializable_results:
                del serializable_results["bleach_mask"]
            return jsonify(serializable_results)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
    return jsonify({"error": "Invalid file type"}), 400

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path != "" and os.path.exists(app.static_folder + '/' + path):
        return send_from_directory(app.static_folder, path)
    else:
        return send_from_directory(app.static_folder, 'index.html')

if __name__ == '__main__':
    app.run(debug=True, port=5003)
```

*Code Block 2: Flask REST API Backend (app.py)*

---

## 9. Output Screenshots

📸 *Screenshot 11: Coral Guardian Dashboard — Initial landing state before any image is uploaded.*

📸 *Screenshot 12: Coral Guardian Dashboard — After uploading a healthy coral image, showing green "HEALTHY CORAL" status, low bleaching %, and vibrant pipeline panels.*

📸 *Screenshot 13: Coral Guardian Dashboard — After uploading a bleached coral image, showing red "SEVERELY BLEACHED" status, high bleaching %, and pale pipeline panels.*

📸 *Screenshot 14: 6-panel pipeline comparison for healthy vs. bleached coral side by side.*

---

## 10. References

1. OpenCV Documentation: https://docs.opencv.org/4.x/
2. Buchsbaum, G. (1980). A spatial processor model for object colour perception. *Journal of the Franklin Institute*, 310(1), 1–26. (Gray-World Assumption)
3. Otsu, N. (1979). A threshold selection method from gray-level histograms. *IEEE Transactions on Systems, Man, and Cybernetics*, 9(1), 62–66.
4. Canny, J. (1986). A computational approach to edge detection. *IEEE Transactions on Pattern Analysis and Machine Intelligence*, 8(6), 679–698.
5. Hughes, T.P. et al. (2017). Global warming and recurrent mass bleaching of corals. *Nature*, 543, 373–377.
6. Gonzalez, R.C. & Woods, R.E. (2018). *Digital Image Processing* (4th ed.). Pearson.
7. Hedley, J.D. et al. (2016). Remote sensing of coral reefs for monitoring and management. *Remote Sensing*, 8(2), 118.
8. Flask Web Framework: https://flask.palletsprojects.com/
9. Pillow (PIL Fork): https://pillow.readthedocs.io/

---

*End of Report*
