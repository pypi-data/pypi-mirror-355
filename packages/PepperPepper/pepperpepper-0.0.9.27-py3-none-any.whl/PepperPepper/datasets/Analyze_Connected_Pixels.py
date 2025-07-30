from PepperPepper.environment import cv2, os, np


def analyze_connected_pixels(img_dir, min_area=1):
    pixel_counts = []

    for filename in os.listdir(img_dir):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp')):
            img_path = os.path.join(img_dir, filename)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

            if img is not None:
                # 二值化处理（保留所有非零像素为前景）
                _, binary = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY)

                # 连通域分析（排除背景标签0）
                num_labels, _, stats, _ = cv2.connectedComponentsWithStats(binary)

                # 收集所有连通域的像素数量（过滤掉背景和微小区域）
                for label in range(1, num_labels):
                    area = stats[label, cv2.CC_STAT_AREA]
                    if area == 1065:
                        print(filename)

                    if area >= min_area:
                        pixel_counts.append(area)

    if not pixel_counts:
        return None

    return {
        "mean": np.mean(pixel_counts),
        "std": np.std(pixel_counts),
        "max": np.max(pixel_counts),
        "min": np.min(pixel_counts)
    }


if __name__ == "__main__":
    result = analyze_connected_pixels("/mnt/d/code/algorithms/IRSTD/SCTransNet/datasets/IRSTD-1k/masks")
    if result:
        print(f"连通域平均像素数: {result['mean']:.2f} ± {result['std']:.2f}")
        print(f"最大连通域: {result['max']} 像素")
        print(f"最小连通域: {result['min']} 像素")