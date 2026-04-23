"""Batch test across healthy and bleached coral images."""
import sys, os
sys.path.insert(0, '.')
import cv2
import numpy as np
import matplotlib
matplotlib.use('Agg')

from main import load_image, preprocess, segment_coral, analyze_bleaching

def quick_test(path):
    name = os.path.basename(path)[:30]
    img = load_image(path)
    preprocessed = preprocess(img)
    mask = segment_coral(preprocessed)
    r = analyze_bleaching(preprocessed, mask)
    area = np.sum(mask == 255) / mask.size * 100
    status = r["status"]
    bp = r["bleach_pct"]
    w = r["whiteness"]
    ri = r["red_index"]
    s = r["mean_sat"]
    print(f"  {name:35s} | Area:{area:5.1f}% | Bleach:{bp:5.1f}% | White:{w:5.1f}% | RI:{ri:.3f} | Sat:{s:5.1f} | {status}")

if __name__ == "__main__":
    print("HEALTHY CORALS")
    print("=" * 120)
    folder = r"C:\Users\Jashwanth\Downloads\CoralDIP\healthy_corals"
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.jpg')])
    for f in files:
        quick_test(os.path.join(folder, f))

    print("\nBLEACHED CORALS")
    print("=" * 120)
    folder = r"C:\Users\Jashwanth\Downloads\CoralDIP\bleached_corals"
    files = sorted([f for f in os.listdir(folder) if f.lower().endswith('.jpg')])
    for f in files:
        quick_test(os.path.join(folder, f))
