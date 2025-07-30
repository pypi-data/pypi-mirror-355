import numpy as np

from ..environment import torch, cv2, plt


'''
1.geometric_mean_filter
    summary: 几何均值滤波器,几何均值滤波器能够在一定程度上对图像进行降噪，且这种降噪使丢失的图像细节更少。其算法的基本原理是通过计算大小为 ｍ×ｎ的矩形子图像窗口的一组像素，每个复原的像素由子图像窗口中像素乘积的 １／ｍｎ次幂给出。
'''
def geometric_mean_filter(img, kernel_size=(3,3)):
    # kernel_size必须是奇数
    assert kernel_size[0] % 2 == 1 and kernel_size[1]%2 == 1, "Kernel size must be odd."

    img_h = img.shape[0]
    img_w = img.shape[1]
    m, n = kernel_size[0], kernel_size[1]
    order = 1 / (m * n)
    kernalMean = np.ones((m, n), np.float32)  # 生成盒式核

    hPad = int((m - 1) / 2)
    wPad = int((n - 1) / 2)
    imgPad = np.pad(img.copy(), ((hPad, m - hPad - 1), (wPad, n - wPad - 1)), mode="edge")
    imgGeoMean = img.copy()
    for i in range(hPad, img_h + hPad):
        for j in range(wPad, img_w + wPad):
            prod = np.prod(imgPad[i - hPad:i + hPad + 1, j - wPad:j + wPad + 1] * 1.0)
            imgGeoMean[i - hPad][j - wPad] = np.power(prod, order)

    return imgGeoMean



