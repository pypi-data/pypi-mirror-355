import numpy as np

from ..environment import torch, cv2, plt




'''
1.visualize_grid_cells(image_path, W, H, X, Y)
将图像划分的grid cell进行可视化
image_path：图像的路径
W:设置图像的宽
H：设置图像的高
X、Y：设置grid cell的数量为X行×Y列个
'''
def visualize_grid_cells(image_path, W, H, ROW, COLUMN, Title='Resized Image with Grid Cells'):
    # 读取图像
    image = cv2.imread(image_path)

    # 如果图像为空（例如文件不存在或损坏），则退出
    if image is None:
        print(f"Error: Could not read image at {image_path}")
        return

        # 调整图像大小
    resized_image = cv2.resize(image, (W, H))

    # 划分grid cell
    cell_width = W // COLUMN
    cell_height = H // ROW

    # 遍历每个grid cell，绘制边界
    for i in range(COLUMN):
        for j in range(ROW):
            # 计算grid cell的左上角坐标
            start_x = i * cell_width
            start_y = j * cell_height
            # 计算grid cell的右下角坐标
            end_x = min((i + 1) * cell_width, W)  # 防止超出图像宽度
            end_y = min((j + 1) * cell_height, H)  # 防止超出图像高度

            # 绘制grid cell边界（使用BGR颜色，因为在OpenCV中图像是BGR格式的）
            cv2.rectangle(resized_image, (start_x, start_y), (end_x, end_y), (0, 255, 0), 2)

            # 显示原图与grid cell（合并到一张图像）
    plt.imshow(cv2.cvtColor(resized_image, cv2.COLOR_BGR2RGB))
    plt.title(Title)
    plt.axis('off')
    plt.show()





'''
2.show_images(imgs, num_rows, num_cols, titles=None, scale=1.5, normalize = False)
展示图像
'''
def show_images(imgs, num_rows, num_cols, titles=None, scale=1.5, normalize = False):
    # 绘制图像列表
    figsize = (num_cols * scale, num_rows * scale)
    _, axes = plt.subplots(num_rows, num_cols, figsize=figsize)
    axes = axes.flatten()
    for i, (ax, img) in enumerate(zip(axes, imgs)):
        if torch.is_tensor(img):
            # 图像张量
            if img.dim() == 3:
                img = img.permute(1, 2, 0)  # 将通道维度移动到最后的位置
            if normalize:
                img = img.numpy().clip(0, 1)  # 归一化到0-1范围，并裁剪超出范围的值
            ax.imshow(img)

        else:
            # PIL图像
            ax.imshow(img)
        ax.axes.get_xaxis().set_visible(False)
        ax.axes.get_yaxis().set_visible(False)
        if titles:
            ax.set_title(titles[i])
    return axes





'''
3.box_corner_to_center(boxes)
    summary: it transform the box corners to center
'''
def box_corner_to_center(boxes):
    x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
    cx = (x1 + x2) // 2
    cy = (y1 + y2) // 2
    w = x2 - x1
    h = y2 - y1
    boxes = torch.stack([cx, cy, w, h], axis=-1)
    return boxes





'''
4.bbox_to_rect(bbox, color)
    summary: it draw bounding box rectangle
'''
def bbox_to_rect(bbox, color):
    return plt.Rectangle(xy=(bbox[0], bbox[1]),width=bbox[2]-bbox[0],height=bbox[3]-bbox[1],fill=False,edgecolor=color,linewidth=2)


'''
5.show_boxes(axes, bboxes, labels=None, colors=None)
    summary: it show the box corners
    
'''
def show_boxes(axes, bboxes, labels, colors=None):
    """显示所有的边框"""
    def _make_list(obj, default_values=None):
        if obj is None:
            obj = default_values
        elif not isinstance(obj, (list, tuple)):
            obj = [obj]
        return obj

    labels = _make_list(labels)
    colors = _make_list(colors,['b', 'g', 'r', 'm', 'c' ])
    for i, bbox in enumerate(bboxes):
        color = colors[i % len(colors)]
        rect = bbox_to_rect(bbox.detach().numpy(), color)
        axes.add_patch(rect)
        if labels and len(labels)>i:
            text_color = 'k' if color== 'w' else 'w'
            axes.text(rect.xy[0],rect.xy[1],labels[i],va='center',ha='center',color=text_color,fontsize=9,bbox=dict(facecolor=color, lw=0))


# 5.visualize_bounding_boxes
def visualize_bounding_boxes(image, bounding_boxes, labels):
    """
    visualize_bounding_boxes(image, bounding_boxes, labels)
    Visualizes bounding boxes on an image.

    Parameters:
        image (numpy.ndarray): The input image.
        bounding_boxes (list): A list of bounding boxes in the format [xmin, ymin, xmax, ymax].
        labels (list): A list of labels corresponding to each bounding box.
    """
    # Create figure and axes
    fig, ax = plt.subplots()

    # Display the image
    ax.imshow(image)

    # Add bounding boxes
    for bbox, label in zip(bounding_boxes, labels):
        xmin, ymin, xmax, ymax = bbox
        # Convert relative coordinates to absolute coordinates
        xmin_abs = xmin * image.shape[1]
        ymin_abs = ymin * image.shape[0]
        xmax_abs = xmax * image.shape[1]
        ymax_abs = ymax * image.shape[0]
        width = xmax_abs - xmin_abs
        height = ymax_abs - ymin_abs
        # Create a Rectangle patch
        rect = plt.Rectangle((xmin_abs, ymin_abs), width, height, fill=False, edgecolor='red', linewidth=2)
        ax.add_patch(rect)
        # Add label
        ax.text(xmin_abs, ymin_abs, label, color='red', fontsize=12, verticalalignment='top')

    plt.show()



'''
6.box_iou_xyxy()
    summary: 计算预测框与真实框之间的IOU值，坐标格式为xyxy
    Args:
        boxes (list): A list of bounding boxes in the format [xmin, ymin, xmax, ymax].
'''
def box_iou_xyxy(boxe1, boxe2):
    # 获取box1的具体坐标
    x1min, y1min, x2max, y2max = boxe1[0], boxe1[1], boxe1[2], boxe1[3]

    # 计算boxe1的框面积
    S1 = np.maximum((x2max - x1min) * (y2max - y1min), 0)

    # 获取box2的具体坐标
    x2min, y2min, x2max, y2max = boxe2[0], boxe2[1], boxe2[2], boxe2[3]

    # 计算boxe2的框面积.
    S2 = np.maximum((x2max - x2min) * (y2max - y2min), 0)

    # 计算相交矩形框的坐标，即boxe1与boxe2的交集
    xmin = np.maximum(x1min, x2min)
    ymin = np.maximum(y1min, y2min)
    xmax = np.minimum(x2max, x2max)
    ymax = np.minimum(y2max, y2max)

    # 计算两个矩形框的交集
    intersection = np.maximum((xmax - xmin) * (ymax - ymin), 0)

    IoU = intersection / np.maximum((S1 + S2 - intersection),1.)

    return IoU



'''
7.box_iou_xywh(boxe1, boxe2)
'''
def box_iou_xywh(boxe1, boxe2):
    # 将xywh化为xyxy
    x1min, y1min, x1max, y1max = boxe1[0] - boxe1[2]/2.0 , boxe1[1] - boxe1[3]/2.0, boxe1[0] + boxe1[2]/2.0 , boxe1[1] + boxe1[3]/2.0
    x2min, y2min, x2max, y2max = boxe2[0] - boxe2[2]/2.0 , boxe2[1] - boxe2[3]/2.0, boxe2[0] + boxe2[2]/2.0 , boxe2[1] + boxe2[3]/2.0

    return box_iou_xyxy((x1min, y1min, x1max, y1max), (x2min, y2min, x2max, y2max))




'''
8.draw_anchor_boxes(image, center_x, center_y, widths, heights)
'''
def draw_anchor_boxes(image, center_x, center_y, widths, heights):
    """
    在图像中画出给定中心点和多种宽高的锚框。

    参数：
        image: 输入的图像，可以是 numpy 数组。
        center_x: 中心点的 x 坐标。
        center_y: 中心点的 y 坐标。
        widths: 锚框的宽度列表。
        heights: 锚框的高度列表。

    返回值：
        annotated_image: 画有锚框的图像，numpy 数组格式。
    """
    # 创建一个副本以保留原始图像
    annotated_image = image.copy()

    # 循环绘制每个锚框
    for width, height in zip(widths, heights):
        # 计算左上角和右下角坐标
        top_left = (int(center_x - width / 2), int(center_y - height / 2))
        bottom_right = (int(center_x + width / 2), int(center_y + height / 2))

        # 在图像上画出锚框
        annotated_image = cv2.rectangle(annotated_image, top_left, bottom_right, (0, 255, 0), 2)

    return annotated_image









'''
9.get_objectness_label(img, gt_boxes, gtlabels, iou_threshold=0.7, anchors = [])
    summary: 标注预测框的objectness
    img 是输入的图像数据，形状是[N, C, H, W]
    gt_boxes，真实框，维度是[N, 50, 4]，其中50是真实框数目的上限，当图片中真实框不足50个时，不足部分的坐标全为0
              真实框坐标格式是xywh，这里使用相对值
    gt_labels，真实框所属类别，维度是[N, 50]
    iou_threshold，当预测框与真实框的iou大于iou_threshold时不将其看作是负样本
    anchors，锚框可选的尺寸
    anchor_masks，通过与anchors一起确定本层级的特征图应该选用多大尺寸的锚框
    num_classes，类别数目
    downsample，特征图相对于输入网络的图片尺寸变化的比例
'''
def get_objectness_label(img, gt_boxes, gtlabels, iou_threshold=0.7, anchors = [116, 90, 156, 198, 373, 326], num_classes = 3, downsample = 32):
    img_shape = img.shape
    batch_size = img.shape[0]
    num_anchors = len(anchors) // 2
    input_h = img.shape[2]
    input_w = img.shape[3]

    # 将输入图片划分成num_rows x num_cols个候选区域，每个候选区域的边长是downsample
    # 计算共有多少列候选区域
    num_cols = input_w // downsample
    # 计算共有多少行候选区域
    num_rows = input_h // downsample

    label_objectness = np.zeros([batch_size, num_anchors, num_rows, num_cols])
    label_classification = np.zeros([batch_size, num_anchors, num_classes, num_rows, num_cols])
    label_location = np.zeros([batch_size, num_anchors, 4, num_rows, num_cols])

    # 这里有个scale_location，用来调节大目标和小目标的权重的
    # 大目标和小目标对于相同的偏移，大目标更加敏感，故增强这个权重系数
    scale_location = np.zeros([batch_size, num_anchors, num_rows, num_cols])

    # batch_size进行循环，处理每一张图片
    for n in range(batch_size):
        # 对图片上的真实框进行遍历，依次找出与真实框形状最匹配的锚框
        for n_gt in range(len(gt_boxes[n])):
            gt_box = gt_boxes[n][n_gt]
            # 真实框所属类别
            gt_label = gtlabels[n][n_gt]
            # 真实框的中心坐标和长宽（YOLO中采用xywh）
            gt_center_x = gt_box[0]
            gt_center_y = gt_box[1]
            gt_width = gt_box[2]
            gt_height = gt_box[3]
            if (gt_width < 1e-3) or (gt_height < 1e-3):
                continue

            # 计算这个真实框的中心点落在哪个格子里,xy是真实边界框的中心点在图像中的归一化坐标（即范围在 [0, 1] 内）
            i = int(gt_center_y * num_rows)
            j = int(gt_center_x * num_cols)

            ious = []

            for ka in range(num_anchors):
                # x，y为0，假设锚框和真实框的x，y相同
                gt_bbox = [0., 0., float(gt_width), float(gt_height)]
                # 生成输入（i，j）这个格子里的锚框
                anchor_w = anchors[ka * 2]
                anchor_h = anchors[ka * 2 + 1]
                anchor_bbox = [0., 0., anchor_w / float(input_w), anchor_h / float(input_h)]
                # 计算iou
                iou = box_iou_xywh(gt_bbox, anchor_bbox)
                ious.append(iou)
            ious = np.array(ious)
            inds = np.argsort(ious)
            k = inds[-1]
            label_objectness[n, k, i, j] = 1
            c = gt_label
            # 使用one-hot方法标注
            label_classification[n, k, c, i, j] = 1

            # for those prediction bbox with objectness =1, set label of location
            # 反算出真实框的tx*，ty*，tw*，th*
            dx_label = gt_center_x * num_cols - j
            dy_label = gt_center_y * num_rows - i
            dw_label = np.log(gt_width * input_w / anchors[k * 2])
            dh_label = np.log(gt_height * input_h / anchors[k * 2 + 1])
            label_location[n, k, 0, i, j] = dx_label
            label_location[n, k, 1, i, j] = dy_label
            label_location[n, k, 2, i, j] = dw_label
            label_location[n, k, 3, i, j] = dh_label

            # scale_location用来调节不同尺寸的锚框对损失函数的贡献，作为加权系数和位置损失函数相乘
            # 根据这个计算方法，可以得出真实框越大，权重越小
            scale_location[n, k, i, j] = 2.0 - gt_width * gt_height

    # 目前根据每张图片上所有出现过的gt_box都标注出了objectness为正的预测框，剩下的预测框的objectness为0
    # 对于objectness为1的预测框，标出它们所包含的物体类别以及位置回归的目标
    return label_objectness.astype('float32'), label_location.astype('float32'), label_classification.astype('float32'), scale_location.astype('float32')






'''
10.nms(bboxes, scores, score_thresh, nms_thresh, pre_nms_topk, i=0, c=0)
    NMS非极大值抑制
    summary: Non-Maximum Suppression
'''
def nms(bboxes, scores, score_thresh, nms_thresh, pre_nms_topk, i=0, c=0):
    inds = np.argsort(scores)
    inds = inds[::-1]
    keep_inds = []
    while(len(inds) > 0):
        cur_ind = inds[0]
        cur_score = scores[cur_ind]
        # 如果该框的分数小于score.thresh，则丢弃该框
        if cur_score < score_thresh:
            break

        keep = True
        for ind in keep_inds:
            current_box = bboxes[cur_ind]
            remain_box = bboxes[ind]
            iou = box_iou_xywh(current_box, remain_box)
            if iou > nms_thresh:
                keep = False
                break
        # 调试代码，用于观察信息使用
        if i == 0 and c == 4 and cur_ind == 951:
            print('suppressed, ',keep,i,c,cur_ind,ind,iou)
        if keep:
            keep_inds.append(cur_ind)
        # 去除当前处理的边界框索引，即将 inds 数组中的第一个元素移除，继续处理下一个边界框。
        inds = inds[1:]
    return np.array(keep_inds)






'''
11.multiclass_nms(bboxes, scores, score_thresh = 0.01, nms_thresh = 0.45, pre_nms_topk = 1000, pos_nms_topk = 100 )
    summary: multiclass-Non-Maximum Suppression
'''
def multiclass_nms(bboxes, scores, score_thresh = 0.01, nms_thresh = 0.45, pre_nms_topk = 1000, pos_nms_topk = 100 ):
    # 获取批量大小和类别数量
    batch_size = bboxes.shape[0]
    class_num = scores.shape[1]
    rets = []
    # 遍历每个样本
    for i in range(batch_size):
        # 获取当前样本的边界框和分数
        bboxes_i = bboxes[i]
        scores_i = scores[i]
        ret = []
        # 遍历每个类别
        for c in range(class_num):
            # 获取当前类别的分数
            scores_i_c = scores_i[c]
            # 使用 NMS 函数进行非最大抑制
            keep_inds = nms(bboxes_i, scores_i_c, score_thresh, nms_thresh, pre_nms_topk, i, c)

            # 如果保留的边界框数量小于1，则跳过当前类别
            if len(keep_inds) < 1:
                continue
            # 根据保留的索引获取对应的边界框和分数
            keep_bboxes = bboxes_i[keep_inds]
            keep_scores = scores_i_c[keep_inds]
            # 构造保留结果
            keep_results = np.zeros([keep_scores.shape[0], 6])
            keep_results[:, 0] = c # 类别索引
            keep_results[:, 1] = keep_scores[:] # 分数
            keep_results[:, 2:6] = keep_bboxes[:, :]    # 边界框坐标
            ret.append(keep_results)
        # 如果当前样本没有保留的结果，则跳过
        if len(ret) < 1:
            rets.append(ret)
            continue
        # 将每个类别的结果拼接在一起
        ret_i = np.concatenate(ret, axis=0)
        # 如果保留的结果数量超过了指定的阈值，则根据分数进行排序并截取指定数量的结果
        scores_i = ret_i[:, 1]
        if len(scores_i) > pos_nms_topk:
            inds = np.argsort(scores_i)[::-1]
            inds = inds[:pos_nms_topk]
            ret_i = ret_i[inds]

        rets.append(ret_i)

    return rets



'''
12.get_yolo_box_xxyy(pred, anchors, num_classes, downsample)
    summary: get_yolo_box_xxyy将网络特征图输出的[tx,ty,tw,th]转化为预测框的坐标[x1,y1,x2,y2]
    
'''
def get_yolo_box_xxyy(pred, anchors, num_classes, downsample):
    """
    Args:
    :param pred: 网络输出特征图,[N,C,H,W],其中C = NUM_ANCHORS * (5 + NUM_CLASSES),类型为numpy.ndarray
    :param anchors: list,表示锚框的大小
    :param num_classes: 类别数
    :param downsample: 相比于原图下采样多少倍
    :return: pred_box: 预测框的坐标
    """
    batch_size = pred.shape[0]
    num_rows = pred.shape[-2]
    num_cols = pred.shape[-1]

    input_h = num_rows * downsample
    input_w = num_cols * downsample

    num_anchors = len(anchors)//2

    # 对pred进行改造
    pred = pred.reshape([-1, num_anchors, 5+num_classes, num_rows, num_cols])
    pred_location = pred[:, :, 0:4, :, :]
    pred_location = torch.permute(pred_location, (0, 3, 4, 1, 2))
    anchors_this = []
    for ind in range(num_anchors):
        anchors_this.append([anchors[ind*2], anchors[ind*2 + 1]])
    anchors_this = torch.tensor(anchors_this).float()

    # 最终输出数据保存在pred_box中，其形状是[N, H, W, NUM_ANCHORS, 4],
    # 其中最后一个维度4代表位置的4个坐标
    pred_box = torch.zeros(pred_location.shape)
    for n in range(batch_size):
        for i in range(num_rows):
            for j in range(num_cols):
                for k in range(num_anchors):
                    pred_box[n,i,j,k,0] = j
                    pred_box[n,i,j,k,1] = i
                    pred_box[n,i,j,k,2] = anchors_this[k][0]
                    pred_box[n,i,j,k,3] = anchors_this[k][1]
    pred_box = pred_box.to(pred_location.device)


    # 使用相对坐标，pred_box的输出元素数值在0~1.0之间
    pred_box[:, :, :, :, 0] = (torch.nn.functional.sigmoid(pred_location[:, :, :, :, 0]) + pred_box[:, :, :, :, 0]) / num_cols
    pred_box[:, :, :, :, 1] = (torch.nn.functional.sigmoid(pred_location[:, :, :, :, 1]) + pred_box[:, :, :, :, 1]) / num_rows
    pred_box[:, :, :, :, 2] = torch.exp(pred_location[:, :, :, :, 2]) * pred_box[:, :, :, :, 2] / input_w
    pred_box[:, :, :, :, 3] = torch.exp(pred_location[:, :, :, :, 3]) * pred_box[:, :, :, :, 3] / input_h

    # 将坐标从xywh转化成xyxy
    pred_box[:, :, :, :, 0] = pred_box[:, :, :, :, 0] - pred_box[:, :, :, :, 2] / 2.
    pred_box[:, :, :, :, 1] = pred_box[:, :, :, :, 1] - pred_box[:, :, :, :, 3] / 2.
    pred_box[:, :, :, :, 2] = pred_box[:, :, :, :, 0] + pred_box[:, :, :, :, 2]
    pred_box[:, :, :, :, 3] = pred_box[:, :, :, :, 1] + pred_box[:, :, :, :, 3]

    pred_box = torch.clip(pred_box, 0., 1.0)
    return pred_box










'''
13.image_downsampling(image, ratio)
    summary: 对图像进行下采样。
    Parameters:
        image: shape：(w,h,c),type：numpy.ndarray
        ratio: 下采样比率，ratio>1且最好为整数
        manner: 采样方式,默认为mean
    Return:
        image_sampling(numpy.ndarray):shape:(w,h,c),type:numpy.ndarray
        
'''
def image_downsampling(image, ratio, manner='mean'):
    image_sampling = np.zeros((int(image.shape[0]/ratio), int(image.shape[1]/ratio), image.shape[2]), dtype='int32')
    fun = np.mean
    if manner == 'mean':
        fun = np.mean
    elif manner == 'max':
        fun = np.max
    for i in range(image_sampling.shape[0]):
        for j in range(image_sampling.shape[1]):
            for k in range(image_sampling.shape[2]):
                delta = image[i * ratio:(i + 1) * ratio, j * ratio:(j + 1) * ratio, k]
                image_sampling[i, j, k] = fun(delta)

    return image_sampling

'''
14.image_quantization(image, ratio)
    summary: 对图像进行量化
    Parameters:
        image: shape：(w,h,c),type：numpy.ndarray
        ratio: 设置量化比率
    Returns:
        image: shape：(w,h,c),type：numpy.ndarray,量化后的图像数据
'''
def image_quantization(image, ratio):
    image_quantization = image.copy()
    for i in range(image_quantization.shape[0]):
        for j in range(image_quantization.shape[1]):
            for k in range(image_quantization.shape[2]):
                image_quantization[i][j][k] = int(image_quantization[i][j][k] / ratio) * ratio

    return image_quantization





'''
15.image_Brightness(image, value)
    summary: 对图像进行亮度调整
    Parameters:
        image为shape：(w,h,c),type：numpy.ndarray
        value：为int类型，可正可负，正为增强图像的亮度，负为降低图像的亮度
    Return：
        image_Brightness：(w,h,c),type：numpy.ndarray
'''
def image_Brightness(image, value):
    image_Brightness = image.copy()
    for i in range(image_Brightness.shape[0]):
        for j in range(image_Brightness.shape[1]):
            for k in range(image_Brightness.shape[2]):
                image_Brightness[i][j][k] = min(image_Brightness[i][j][k], image_Brightness[i][j][k] + value)

    return image_Brightness





'''
16.image_contrast(image, ratio)
    summary: 对图像的对比度
    Parameters:
        image,shape：(w,h,c),type：numpy.ndarray
        ratio,所有元素乘以这个系数增大最大灰度值与最小灰度值的差异即落差值
    Return:
        image_contrast,(w,h,c),type：numpy.ndarray
'''
def image_contrast(image, ratio):
    image_contrast = image.copy()
    for i in range(image_contrast.shape[0]):
        for j in range(image_contrast.shape[1]):
            for k in range(image_contrast.shape[2]):
                if image_contrast[i,j,k]*ratio > 255:
                    image_contrast[i,j,k] = 255
                elif image_contrast[i,j,k]*ratio < 0:
                    image_contrast[i,j,k] = 0
                else:
                    image_contrast[i,j,k] = image_contrast[i,j,k] * ratio
    return image_contrast



'''
17.image_cv2plt(image)
    将图像bgr空间转rgb空间
'''
def image_cv2plt(image):
    imgCp = image.copy()
    imgCp = cv2.cvtColor(imgCp, cv2.COLOR_BGR2RGB)
    return imgCp



