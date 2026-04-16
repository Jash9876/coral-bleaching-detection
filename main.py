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