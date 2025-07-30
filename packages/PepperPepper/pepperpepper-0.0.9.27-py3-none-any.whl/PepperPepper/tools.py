"""
工具包，主要包含Pepper项目中一些深度学习常用的操作
"""

from .environment import cv2, torch, plt, np

"""
1.测试工具
概述：用于检测python包
作用：打印print测试Pepper安装效果
"""
def printPepper():
    print("welcome to Pepper!")




'''
2.Document_scanning
概况：文档扫描功能
'''
def Document_scanning(img):
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # OTSU
    ret, thresh_image = cv2.threshold(img_gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 高斯模糊
    binary = cv2.GaussianBlur(img_gray, (5, 5), 0)

    # 边缘检测
    binary = cv2.Canny(binary, int(ret / 3), ret, apertureSize=3)

    # 膨胀操作，尽量使边缘闭合
    kernel = np.ones((3, 3), np.uint8)
    img_binary = cv2.dilate(binary, kernel, iterations=1)

    # 寻找边缘
    contours, _ = cv2.findContours(img_binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # 计算面积
    max_area = 0.0
    max_contour = []
    for contour in contours:
        currentArea = cv2.contourArea(contour)
        if currentArea > max_area:
            max_area = currentArea
            max_contour = contour

    # 多边形拟合凸包
    hull = cv2.convexHull(max_contour)
    epsilon = 0.02 * cv2.arcLength(max_contour, True)
    approx = cv2.approxPolyDP(hull, epsilon, True)
    boxes = approx.reshape((len(approx), 2))

    rect = np.zeros((4, 2), dtype='float32')
    s = boxes.sum(axis=1)
    rect[0] = boxes[np.argmin(s)]
    rect[2] = boxes[np.argmax(s)]
    diff = np.diff(boxes, axis=1)
    rect[1] = boxes[np.argmin(diff)]
    rect[3] = boxes[np.argmax(diff)]
    (tl, tr, br, bl) = rect

    # 计算输入的w和h的值
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    # 变化后对应坐标位置
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]],
        dtype='float32')

    # 计算变换矩阵
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(img, M, (maxWidth, maxHeight))

    return warped






























