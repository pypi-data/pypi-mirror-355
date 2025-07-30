# import torch
# import torch.nn as nn
# import torch.nn.functional as F
# from utils import *
# from einops.array_api import rearrange
from einops import rearrange, repeat
from PepperPepper.environment import torch, nn, F
from PepperPepper.IRSTD.tools.utils import *
from scipy.ndimage  import label, center_of_mass
from PepperPepper.IRSTD.tools.metrics import SegmentationMetricTPFNFP


class SoftLoULoss(nn.Module):
    def __init__(self):
        super(SoftLoULoss, self).__init__()

    def forward(self, pred, target):
        pred = F.sigmoid(pred)
        smooth = 1

        intersection = pred * target

        intersection_sum = torch.sum(intersection, dim=(1,2,3))
        pred_sum = torch.sum(pred, dim=(1,2,3))
        target_sum = torch.sum(target, dim=(1,2,3))
        loss = (intersection_sum + smooth) / \
               (pred_sum + target_sum - intersection_sum + smooth)

        loss = 1 - torch.mean(loss)

        return loss




class PatchAwareLoss(nn.Module):
    def __init__(self, Patch_num = 16):
        super(PatchAwareLoss, self).__init__()
        self.Patch_num = Patch_num
        self.base_loss = nn.BCEWithLogitsLoss()
        self.iouloss = SoftLoULoss()
        self.metrics = SegmentationMetricTPFNFP(nclass=1)


    # def _generate_target_grid(self, target):
    #     batch_size, _, h, w = target.shape
    #     patch_size = h // self.Patch_num
    #     target_grid = torch.zeros((batch_size, 1, self.Patch_num, self.Patch_num),device=target.device)
    #
    #     for b in range(batch_size):
    #         mask_np = target[b, 0].cpu().numpy().astype(np.uint8)
    #         labeled_mask, num_labels = label(mask_np)
    #         for label_id in range(1, num_labels + 1):
    #             cy, cx = center_of_mass(labeled_mask == label_id)
    #             patch_y = min(int(cy // patch_size), self.Patch_num - 1)
    #             patch_x = min(int(cx // patch_size), self.Patch_num - 1)
    #             target_grid[b, 0, patch_y, patch_x] = 1
    #     return target_grid



    def _generate_target_grid(self, target):
        batch_size, _, h, w = target.shape
        Patch_num = self.Patch_num
        # patch_size = h // self.Patch_num

        # target_unfold = target.unfold(2, Patch_num, patch_size)  # 展开为块
        # target_unfold = target_unfold.unfold(3, Patch_num, patch_size)
        # target_grid = target_unfold.any(dim=4).any(dim=5).float()

        # target_unfold = rearrange(target, 'b c (P S) (P S) -> b c P P (S S)', P=Patch_num)
        target_unfold = rearrange(target, 'b c (P S1) (Q S2) -> b c P Q (S1 S2)', P=Patch_num, Q=Patch_num)

        # target_unfold = target_unfold.contiguous().view(
        #     batch_size, 1, Patch_num, Patch_num, -1
        # )

        target_grid = target_unfold.any(dim=-1).float()

        return target_grid








    def forward(self, pred, target):
        target_grid = self._generate_target_grid(target)
        loss = self.base_loss(pred, target_grid)

        # 查全率损失部分
        recall = 1.0 - torch.sum((torch.sigmoid(pred) * target_grid)) / torch.sum(target_grid)
        return loss + recall


    # 原有准确率计算（保持兼容）
    def forward_matchprecision(self, pred, target):
        target_grid = self._generate_target_grid(target)
        pred = torch.sigmoid(pred)
        pred_binary = (pred > 0.5).float()
        correct = (pred_binary == target_grid).sum().item()
        return correct / pred.numel()

    # 新增：查全率计算
    def forward_recall(self, pred, target):
        target_grid = self._generate_target_grid(target)
        pred = torch.sigmoid(pred)
        pred_binary = (pred > 0.5).float()

        # 计算真正例（TP）和实际正例（TP+FN）
        true_positives = (pred_binary * target_grid).sum()  # 正确预测的正例
        actual_positives = target_grid.sum()  # 所有真实正例

        # 处理无正例的情况
        if actual_positives == 0:
            return 0.0  # 可根据任务需求返回nan或其他值

        recall = true_positives / actual_positives
        return recall.item()



    def TargetLoss(self, patch_target_out, PAM_out, mask):
        loss = 0.0
        Patch_binary = (PAM_out > 0.0).to(torch.float)

        # 获取需要处理的块位置
        batch_size, channels, height, width = Patch_binary.shape
        target_patch_num = 0.0
        for b in range(batch_size):
            for h in range(height):
                for w in range(width):
                    if Patch_binary[b, 0, h, w] == 1.0:
                        block_target = patch_target_out[b, :, h*16:(h+1)*16, w*16:(w+1)*16].unsqueeze(0)
                        block_mask = mask[b, :, h*16:(h+1)*16, w*16:(w+1)*16].unsqueeze(0)
                        temp_loss = self.base_loss(block_target, block_mask) + self.iouloss(block_target, block_mask)
                        target_patch_num += 1.0
                        loss += temp_loss

        return loss/target_patch_num








    def forward_iou(self, patch_target_out, PAM_out, mask):
        self.metrics.reset()
        Patch_binary = (PAM_out > 0.0).to(torch.float)

        # 获取需要处理的块位置
        batch_size, channels, height, width = Patch_binary.shape
        target_patch_num = 0.0
        for b in range(batch_size):
            for h in range(height):
                for w in range(width):
                    if Patch_binary[b, 0, h, w] == 1.0:
                        block_target = patch_target_out[b, :, h*16:(h+1)*16, w*16:(w+1)*16].unsqueeze(0)
                        block_mask = mask[b, :, h*16:(h+1)*16, w*16:(w+1)*16].unsqueeze(0)
                        target_patch_num += 1.0
                        self.metrics.update(block_mask.cpu(), block_target.cpu())

        miou, prec, recall, fmeasure = self.metrics.get()

        return miou







        # self.Conv1 = Encoder_conv_block(in_ch, filters[0], mode='None')
        # self.Conv2 = Encoder_conv_block(filters[0], filters[1], mode='None')
        # self.Conv3 = Encoder_conv_block(filters[1], filters[2], mode='None')
        # self.Conv4 = Encoder_conv_block(filters[2], filters[3], mode='None')
        # self.Conv5 = Encoder_conv_block(filters[3], filters[4], mode='None')
        #
        # self.Up5 = up_conv(filters[4], filters[3], mode='None')
        # self.Up_conv5 = Decoder_conv_block(filters[4], filters[3], mode='None')
        #
        # self.Up4 = up_conv(filters[3], filters[2], mode='None')
        # self.Up_conv4 = Decoder_conv_block(filters[3], filters[2], mode='None')
        #
        # self.Up3 = up_conv(filters[2], filters[1], mode='None')
        # self.Up_conv3 = Decoder_conv_block(filters[2], filters[1], mode='None')
        #
        # self.Up2 = up_conv(filters[1], filters[0], mode='None')
        # self.Up_conv2 = Decoder_conv_block(filters[1], filters[0], mode='None')

