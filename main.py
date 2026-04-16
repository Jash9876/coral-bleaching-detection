import cv2
import numpy as np
import matplotlib.pyplot as plt

# STEP 1: Loading the image

image_path = "coral.jpg"
img = cv2.imread(image_path)

if img is None:
    print("Error loading image")
    exit()

img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

# STEP 2: Preprocessing the image

# Noise Reduction
blur = cv2.GaussianBlur(img_rgb, (5, 5), 0)

# Color Correction (Normalization)
corrected = cv2.normalize(blur, None, 0, 255, cv2.NORM_MINMAX)

# STEP 3: LAB Color Space Enhancement

lab = cv2.cvtColor(corrected, cv2.COLOR_RGB2LAB)
l, a, b = cv2.split(lab)

l_eq = cv2.equalizeHist(l)
lab_eq = cv2.merge((l_eq, a, b))

enhanced = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2RGB)

# STEP 4: Coral Segmentation using K-means Clustering

Z = enhanced.reshape((-1, 3))
Z = np.float32(Z)

K = 3
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)

_, labels, centers = cv2.kmeans(Z, K, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)

centers = np.uint8(centers)
segmented = centers[labels.flatten()]
segmented = segmented.reshape(enhanced.shape)

# Convert to grayscale to identify dominant cluster
gray_seg = cv2.cvtColor(segmented, cv2.COLOR_RGB2GRAY)

# Threshold to isolate coral (heuristic)
_, coral_mask = cv2.threshold(gray_seg, 0, 255, cv2.THRESH_OTSU)

# Apply mask
coral_only = cv2.bitwise_and(enhanced, enhanced, mask=coral_mask)
