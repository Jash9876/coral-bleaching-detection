# Coral Bleaching Detection using Digital Image Processing

## Overview

This project presents an **Explainable Coral Bleaching Detection System** developed using core **Digital Image Processing (DIP)** techniques. The system analyzes underwater coral images to identify and quantify bleaching by examining color and intensity variations.

Unlike deep learning approaches, this project focuses on **classical DIP methods**, making it computationally efficient, interpretable, and suitable for academic analysis.

---

## Objective

* Detect bleached coral regions from underwater images
* Enhance image quality affected by underwater distortions
* Quantify bleaching percentage
* Classify coral health into meaningful categories
* Provide intuitive visual outputs such as heatmaps

---

## Key Features

* Adaptive bleaching detection based on image statistics
* Coral region isolation using K-Means clustering
* LAB-based contrast enhancement for underwater clarity
* HSV-based segmentation using saturation and brightness
* Morphological refinement for accurate region detection
* Heatmap visualization for intuitive interpretation
* Rule-based classification (Healthy / Moderate / Severe)

---

## Methodology

### 1. Image Acquisition

Input underwater coral images from dataset or real-world sources.

### 2. Preprocessing

* Noise reduction using Gaussian filtering
* Color correction to compensate underwater distortions

### 3. Image Enhancement

* LAB color space transformation
* Histogram equalization on luminance channel

### 4. Coral Segmentation

* K-Means clustering to isolate coral regions from background

### 5. Color Space Conversion

* RGB → HSV for better color-based analysis

### 6. Adaptive Thresholding

* Dynamic thresholds based on saturation and brightness
* Identifies potential bleached regions

### 7. Morphological Operations

* Noise removal and gap filling for clean segmentation

### 8. Feature Extraction

* Pixel-based analysis of bleached regions
* Area computation

### 9. Bleaching Quantification

* Percentage of bleached pixels over coral region

### 10. Classification

* Healthy (0–20%)
* Moderately Bleached (20–50%)
* Severely Bleached (50%+)

### 11. Visualization

* Heatmap overlay for bleaching severity
* Step-by-step pipeline visualization

---

## 🛠️ Tech Stack

* Python
* OpenCV
* NumPy
* Matplotlib

---

## Output

* Enhanced coral image
* Segmented coral region
* Bleaching mask
* Heatmap visualization
* Bleaching percentage and classification

---

## Applications

* Marine ecosystem monitoring
* Coral reef conservation analysis
* Environmental impact assessment
* Research and academic studies

---

## Limitations

* Performance depends on image quality
* Challenging under extreme lighting variations
* Rule-based approach less robust than deep learning

---

## Future Enhancements

* Integration with CNN models for improved accuracy
* Real-time analysis using underwater drones
* Mobile/web-based deployment
* Dataset expansion for robustness

---

## Sample Workflow

Input Image → Enhancement → Segmentation → Detection → Heatmap → Classification

---

## Author

Jashwanth B

---

## Contribution

Feel free to fork, improve, or extend this project for research and development purposes.
