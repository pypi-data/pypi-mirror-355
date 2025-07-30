from ..environment import torch,np
from ..core.image_utils import box_iou_xywh, get_yolo_box_xxyy
from .cnn import ResidualBlock,InceptionBlockV1



'''
1.YOLOv3_104
    summary:此模型是在yolov3的版本上的改进算法，将多尺度检测中添加grid cell为104，以此增强小目标检测的性能。
'''
class YOLOv3_104(torch.nn.Module):
    def __init__(self, in_channels=3, num_classes=1000):
        super(YOLOv3_104, self).__init__()
        self.num_classes = num_classes

        '''
        DarkNet53_104
        简述：Dark53是在YOLOv3论文中提出来的，相比于上一代DarkNet网络加入了残差模块。能更好的避免梯度爆炸以及梯度消失。
            输入必须为：416x416 输出为特征图
        '''
        class DarkNet53_104(torch.nn.Module):
            def __init__(self,in_channels):
                super(DarkNet53_104, self).__init__()
                self.feature104 = torch.nn.Sequential(
                    self._DBL_block(in_channels, 32, 3, 1, 1),
                    self._DBL_block(32, 64, 3, 2, 1),
                    ResidualBlock(64, 64),
                    self._DBL_block(64, 128, 3, 2, 1),
                    *self._resnet_block(128, 128, 2, True)
                )
                self.feature52 = torch.nn.Sequential(
                    self._DBL_block(128, 256, 3, 2, 1),
                    *self._resnet_block(256, 256, 8, True)
                )
                self.feature26 = torch.nn.Sequential(
                    self._DBL_block(256, 512, 3, 2, 1),
                    *self._resnet_block(512, 512, 8, True)
                )
                self.feature13 = torch.nn.Sequential(
                    self._DBL_block(512, 1024, 3, 2, 1),
                    *self._resnet_block(1024, 1024, 4, True)
                )

            def forward(self, x):
                features104 = self.feature104(x)
                features52 = self.feature52(features104)
                features26 = self.feature26(features52)
                features13 = self.feature13(features26)
                return [features104, features52, features26, features13]

            # DBL块
            def _DBL_block(self, in_channels, out_channels, kernel_size, stride, padding):
                return torch.nn.Sequential(
                    torch.nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding),
                    torch.nn.BatchNorm2d(out_channels),
                    torch.nn.LeakyReLU(negative_slope=0.2)
                )

            # resnet块
            def _resnet_block(self, in_channels, out_channels, num_residual, fist_block=False):
                blk = []
                for i in range(num_residual):
                    if i == 0 and not fist_block:
                        blk.append(ResidualBlock(in_channels, out_channels, strides=2))
                    else:
                        blk.append(ResidualBlock(out_channels, out_channels))
                return blk
        # 将DarkNet53_104实例化
        self.DarkNet53_104 = DarkNet53_104(in_channels)




        '''
        NeckNet_DarkNet53_104
        简述：专门为DarkNet53_104设计的颈部网络，用于FeatureExtractor进行特征提取之后实现多尺度检测部分。
        '''
        class NeckNet_DarkNet53_104(torch.nn.Module):
            def __init__(self):
                super(NeckNet_DarkNet53_104,self).__init__()
                self.output13_FE = torch.nn.Sequential(*self._FeatureExtractor_block(1024, 512, 3))
                self.output13_to_26_UpSample = self._UpSample_block(512, 256)


                self.output26_FE = torch.nn.Sequential(*self._FeatureExtractor_block(768, 256, 3))
                self.output26_to_52_UpSample = self._UpSample_block(256, 128)
                self.output26_FE_to_13_DownSample = self._DownSample_block(256, 256)


                self.output52_FE = torch.nn.Sequential(*self._FeatureExtractor_block(384, 128, 3))
                self.output52_to_104_UpSample = self._UpSample_block(128, 64)
                self.output52_FE_to_26_DowmSample = self._DownSample_block(128, 128)
                self.output52_FE_26_to_13_DowmSample = self._DownSample_block(128, 128)






            # FE模块设计，实现Neck网络中的特征提取部分的功能
            def _FeatureExtractor_block(self,in_channels, out_channels, num_inception):
                blk = []
                blk.append(self._DBL_block(in_channels, out_channels , 1, 1, 0))
                for i in range(num_inception):
                    blk.append(InceptionBlockV1(out_channels, ch1=(out_channels - 3 * out_channels// 4), ch2=(out_channels//4, out_channels//4), ch3=( out_channels//4, out_channels//4) , ch4=out_channels//4))
                blk.append(self._DBL_block(out_channels, out_channels , 3, 1, 1))
                return blk

            # UpSample模块，上采样模块设计。
            def _UpSample_block(self, in_channels, out_channels):
                return torch.nn.Sequential(self._DBL_block(in_channels, out_channels, 3, 1,1),
                                           torch.nn.ConvTranspose2d(out_channels, out_channels, 2, 2, 0))

            def _DownSample_block(self, in_channels, out_channels):
                return self._DBL_block(in_channels, out_channels, 3, 2,1)

            # DBL模块设计
            def _DBL_block(self, in_channels, out_channels, kernel_size, stride, padding):
                return torch.nn.Sequential(
                    torch.nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding),
                    torch.nn.BatchNorm2d(out_channels),
                    torch.nn.LeakyReLU(negative_slope=0.2)
                )

            def forward(self, features):
                features104, features52, features26, features13 = features
                features13_FE = self.output13_FE(features13)
                features13_to_26_UpSample = self.output13_to_26_UpSample(features13_FE)


                features26_FE = self.output26_FE(torch.cat((features26, features13_to_26_UpSample), dim=1))
                features26_to_52_UpSample = self.output26_to_52_UpSample(features26_FE)


                features52_FE = self.output52_FE(torch.cat((features52, features26_to_52_UpSample), dim=1))
                features52_to_104_UpSample = self.output52_to_104_UpSample(features52_FE)

                output104 = torch.cat((features104, features52_to_104_UpSample), dim=1)

                features52_to_26_DowmSample = self.output52_FE_to_26_DowmSample(features52_FE)
                output26 = torch.cat((features26_FE, features52_to_26_DowmSample), dim=1)

                features52_to_13_DownSample = self.output52_FE_26_to_13_DowmSample(features52_to_26_DowmSample)
                features26_to_13_DownSample = self.output26_FE_to_13_DownSample(features26_FE)
                output13 = torch.cat((features13_FE, features26_to_13_DownSample, features52_to_13_DownSample), dim=1)

                return [output104, output26, output13]


        # 实例化颈部网络
        self.NeckNet_DarkNet53_104 = NeckNet_DarkNet53_104()

        self.classifier_DarkNet53_104 = torch.nn.Sequential(
            self._DBL_block(192, 3*(5+num_classes), 1, 1, 0),
            torch.nn.Conv2d(3*(5+num_classes), 3*(5+num_classes), 1, 1, 0)
        )

        self.classifier_DarkNet53_26 = torch.nn.Sequential(
            self._DBL_block(384, 3*(5+num_classes), 1, 1, 0),
            torch.nn.Conv2d(3*(5+num_classes), 3*(5+num_classes), 1, 1, 0)
        )

        self.classifier_DarkNet53_13 = torch.nn.Sequential(
            self._DBL_block(896, 3*(5+num_classes), 1, 1, 0),
            torch.nn.Conv2d(3*(5+num_classes), 3*(5+num_classes), 1, 1, 0)
        )





    def forward(self, x):
        x = self.DarkNet53_104(x)
        x = self.NeckNet_DarkNet53_104(x)
        output104, output26, output13 = x
        output104 = self.classifier_DarkNet53_104(output104)

        output26 = self.classifier_DarkNet53_26(output26)

        output13 = self.classifier_DarkNet53_13(output13)

        return [output104, output26, output13]



    # DBL模块设计
    def _DBL_block(self, in_channels, out_channels, kernel_size, stride, padding):
        return torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, out_channels, kernel_size, stride, padding),
            torch.nn.BatchNorm2d(out_channels),
            torch.nn.LeakyReLU(negative_slope=0.2)
        )

    def get_objectness_label(self,img_shape, gt_boxes, gt_labels, iou_threshold=0.3, anchors=[5,6,25,10,20,34], num_classes=3, downsample=32):
        """
        img 是输入的图像数据，形状是[N, C, H, W]
        gt_boxes，真实框，维度是[N, 50, 4]，其中50是真实框数目的上限，当图片中真实框不足50个时，不足部分的坐标全为0
                  真实框坐标格式是xywh，这里使用相对值
        gt_labels，真实框所属类别，维度是[N, 50]
        iou_threshold，当预测框与真实框的iou大于iou_threshold时不将其看作是负样本
        anchors，锚框可选的尺寸
        anchor_masks，通过与anchors一起确定本层级的特征图应该选用多大尺寸的锚框
        num_classes，类别数目
        downsample，特征图相对于输入网络的图片尺寸变化的比例
        """
        img_shape = img_shape
        batch_size = img_shape[0]
        num_anchors = len(anchors)//2
        input_h = img_shape[2]
        input_w = img_shape[3]
        # 将输入图片划分成num_rows x num_cols个小方块区域，每个小方块的边长是 downsample
        # 计算一共有多少行小方块
        num_rows = input_h//downsample
        # 计算一共有多少列小方块
        num_cols = input_w//downsample
        label_objectness = torch.zeros([batch_size, num_anchors, num_rows, num_cols])
        label_classification = torch.zeros([batch_size, num_anchors, num_classes, num_rows, num_cols])
        label_location = torch.zeros([batch_size, num_anchors, 4, num_rows, num_cols])



        scale_location = torch.ones([batch_size, num_anchors, num_rows, num_cols])
        # 对batchsize进行循环，依次处理每张图片
        for n in range(batch_size):

            # 对图片上的真实框进行循环，依次找出跟真实框形状最匹配的锚框
            for n_gt in range(len(gt_boxes[n])):
                gt = gt_boxes[n][n_gt]
                gt_cls = gt_labels[n][n_gt]
                gt_center_x = gt[0]
                gt_center_y = gt[1]
                gt_width = gt[2]
                gt_height = gt[3]
                if (gt_height < 1e-3) or (gt_height < 1e-3):
                    continue
                i = int(gt_center_y * num_rows)
                j = int(gt_center_x * num_cols)
                ious = []
                for ka in range(num_anchors):
                    bbox1 = [0., 0., float(gt_width), float(gt_height)]
                    anchor_w = anchors[ka * 2]
                    anchor_h = anchors[ka * 2 + 1]
                    bbox2 = [0., 0., anchor_w / float(input_w), anchor_h / float(input_h)]
                    # 计算IOU
                    iou = box_iou_xywh(bbox1, bbox2)
                    ious.append(iou)
                ious = torch.tensor(ious)
                inds = torch.argsort(ious)
                k = inds[-1]
                label_objectness[n, k, i, j] = 1
                c = int(gt_cls)
                label_classification[n, k, c, i, j] = 1.

                # for those prediction bbox with objectness =1, set label of location
                dx_label = gt_center_x * num_cols - j
                dy_label = gt_center_y * num_rows - i
                dw_label = torch.log(gt_width * input_w / anchors[k * 2])
                dh_label = torch.log(gt_height * input_h / anchors[k * 2 + 1])
                label_location[n, k, 0, i, j] = dx_label
                label_location[n, k, 1, i, j] = dy_label
                label_location[n, k, 2, i, j] = dw_label
                label_location[n, k, 3, i, j] = dh_label
                # scale_location用来调节不同尺寸的锚框对损失函数的贡献，作为加权系数和位置损失函数相乘
                scale_location[n, k, i, j] = 2.0 - gt_width * gt_height

        # 目前根据每张图片上所有出现过的gt box，都标注出了objectness为正的预测框，剩下的预测框则默认objectness为0
        # 对于objectness为1的预测框，标出了他们所包含的物体类别，以及位置回归的目标
        return label_objectness.float(), label_location.float(), label_classification.float(), scale_location.float()




    # 计算某一尺度时的损失
    def loss(self, output, label_objectness, label_location, label_classification, scales, num_anchors,  class_num):
        # 将output从[N, C, H, W]变形为[N, NUM_ANCHORS, NUM_CLASSES + 5, H, W]
        reshaped_output = torch.reshape(output, [-1, num_anchors, 5+class_num, output.shape[2], output.shape[3]])
        # 从output中取出跟objectness相关的预测值
        pred_objectness = reshaped_output[:, :, 4, :, :]
        label_objectness = label_objectness.to(device=pred_objectness.device)
        label_location = label_location.to(device=pred_objectness.device)
        label_classification = label_classification.to(device=pred_objectness.device)
        # print(pred_objectness.device, label_objectness.device)
        # print(pred_objectness.requires_grad, label_objectness.requires_grad)
        loss_objectness = torch.nn.functional.binary_cross_entropy_with_logits(pred_objectness,label_objectness,reduction="none")
        loss_objectness.requires_grad_(True)


        # pos_samples 只有在正样本的地方取值为1.，其它地方取值全为0.
        pos_objectness = label_objectness > 0
        pos_samples = pos_objectness.float()
        pos_samples.requires_grad = False

        # 从output中取出所有跟位置相关的预测值
        tx = reshaped_output[:, :, 0, :, :]
        ty = reshaped_output[:, :, 1, :, :]
        tw = reshaped_output[:, :, 2, :, :]
        th = reshaped_output[:, :, 3, :, :]
        # 从gt_box中取出各个位置坐标的标签
        dx_label = label_location[:, :, 0, :, :]
        dy_label = label_location[:, :, 1, :, :]
        dw_label = label_location[:, :, 2, :, :]
        dh_label = label_location[:, :, 3, :, :]

        # 构建损失函数
        loss_location_x = torch.nn.functional.binary_cross_entropy_with_logits(tx, dx_label,reduction="none")
        loss_location_y = torch.nn.functional.binary_cross_entropy_with_logits(ty, dy_label,reduction="none")
        loss_location_w = torch.abs(tw - dw_label)
        loss_location_h = torch.abs(th - dh_label)
        # 计算总的位置损失函数
        loss_location = loss_location_x + loss_location_y + loss_location_w + loss_location_h
        loss_location.requires_grad_(True)
        scales = scales.to(device=loss_location.device)
        # 乘以scales
        loss_location = loss_location * scales
        # 只计算正样本的位置损失函数
        loss_location = loss_location * pos_samples

        # 从output取出所有跟物体类别相关的像素点
        pred_classification = reshaped_output[:, :, 5:5 + class_num, :, :]

        # print(pred_classification.shape, label_classification.shape)

        # 计算分类相关的损失函数
        loss_classification = torch.nn.functional.binary_cross_entropy_with_logits(pred_classification, label_classification,reduction="none")
        loss_objectness.requires_grad_(True)

        loss_classification = torch.sum(loss_classification, dim=2)
        loss_classification.requires_grad_(True)
        # 只计算objectness为正的样本的分类损失函数
        loss_classification = loss_classification * pos_samples
        loss_classification.requires_grad_(True)
        total_loss = loss_objectness + loss_classification + loss_location
        total_loss.requires_grad_(True)
        # 对所有预测框的loss进行求和
        total_loss = torch.sum(total_loss, dim=[1, 2, 3])
        # 对所有样本求平均
        total_loss = torch.mean(total_loss)
        return total_loss

    # 挑选出跟真实框IoU大于阈值的预测框
    def get_iou_above_thresh_inds(self,pred_box, gt_boxes, iou_threshold):
        # print(pred_box.dtype, ' ', gt_boxes.dtype)
        batchsize = pred_box.shape[0]
        num_rows = pred_box.shape[1]
        num_cols = pred_box.shape[2]
        num_anchors = pred_box.shape[3]
        ret_inds = torch.zeros([batchsize, num_rows, num_cols, num_anchors])
        for i in range(batchsize):
            pred_box_i = pred_box[i]
            gt_boxes_i = gt_boxes[i]
            for k in range(len(gt_boxes_i)):  # gt in gt_boxes_i:
                gt = gt_boxes_i[k]
                gtx_min = gt[0] - gt[2] / 2.
                gty_min = gt[1] - gt[3] / 2.
                gtx_max = gt[0] + gt[2] / 2.
                gty_max = gt[1] + gt[3] / 2.
                if (gtx_max - gtx_min < 1e-3) or (gty_max - gty_min < 1e-3):
                    continue
                x1 = torch.maximum(pred_box_i[:, :, :, 0], gtx_min)
                y1 = torch.maximum(pred_box_i[:, :, :, 1], gty_min)
                x2 = torch.minimum(pred_box_i[:, :, :, 2], gtx_max)
                y2 = torch.minimum(pred_box_i[:, :, :, 3], gty_max)
                intersection = torch.maximum(x2 - x1, torch.tensor(0.)) * torch.maximum(y2 - y1, torch.tensor(0.))
                s1 = (gty_max - gty_min) * (gtx_max - gtx_min)
                s2 = (pred_box_i[:, :, :, 2] - pred_box_i[:, :, :, 0]) * (pred_box_i[:, :, :, 3] - pred_box_i[:, :, :, 1])
                # print(s1.dtype, ' ', s2.dtype,' ',s1.shape,' ',s2.shape)
                union = s2 + s1 - intersection
                iou = intersection / union
                above_inds = torch.where(iou > iou_threshold)
                ret_inds[i][above_inds] = 1
        ret_inds = torch.permute(ret_inds, (0, 3, 1, 2))
        return ret_inds.bool()

    #
    def label_objectness_ignore(self, label_objectness, iou_above_thresh_indices):
        negative_indices = (label_objectness < 0.5)
        ignore_indices = negative_indices * iou_above_thresh_indices
        label_objectness[ignore_indices] = -1
        return label_objectness

    # 定义损失函数
    def get_loss(self, outputs, gtbox, gtlabel, anchors=[[5,6,25,10,20,34],[35,79,52,43,59,115],[115,90,156,197,374,326]],ignore_thresh=0.7):
        self.losses = torch.tensor([])
        self.losses.requires_grad_(True)

        downsample = [4, 16, 32]
        for i, out in enumerate(outputs):
            batch_size = torch.tensor(out.shape[0])

            label_objectness,label_location,label_classification, scale_location = self.get_objectness_label([batch_size,3,416,416], gtbox, gtlabel, iou_threshold=ignore_thresh, anchors=anchors[i],num_classes=self.num_classes, downsample=downsample[i])
            pred_boxes = get_yolo_box_xxyy(out,anchors[i],num_classes=self.num_classes, downsample=downsample[i])
            iou_above_thresh_indices = self.get_iou_above_thresh_inds(pred_boxes, gtbox, iou_threshold=0.7)
            label_objectness = self.label_objectness_ignore(label_objectness, iou_above_thresh_indices)

            label_objectness = torch.tensor(label_objectness)
            label_location = torch.tensor(label_location)
            label_classification = torch.tensor(label_classification)
            label_objectness.to(out.device)
            label_location.to(out.device)
            label_classification.to(out.device)
            label_objectness.requires_grad = False
            label_location.requires_grad = False
            label_classification.requires_grad = False
            scale_location = torch.tensor(scale_location)
            scale_location.requires_grad = False

            loss = self.loss(output=out, label_objectness=label_objectness, label_location=label_location, label_classification=label_classification, scales=scale_location, num_anchors=len(anchors[i])//2, class_num=self.num_classes)
            self.losses = torch.cat((self.losses, torch.tensor([torch.mean(loss)])))

        return torch.sum(self.losses)














