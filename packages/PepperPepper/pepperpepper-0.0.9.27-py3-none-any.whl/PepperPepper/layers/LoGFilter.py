from tokenize import group

import torch
import torch.nn as nn
import torch.nn.functional as F
# from mmcv.cnn import build_norm_layer
import math
from thop import profile
from einops import rearrange




class LocalAvgPatchcontrast(nn.Module):
    def __init__(self, dim, kernel_size):
        super(LocalAvgPatchcontrast, self).__init__()
        self.dim = dim
        self.kernel_size = kernel_size
        self.avg_pool = nn.AvgPool2d(kernel_size=kernel_size, stride=kernel_size)
        self.conv = nn.Sequential(
            nn.Conv2d(in_channels=self.dim, out_channels=self.dim, kernel_size=3, padding=1),
            nn.BatchNorm2d(self.dim),
            nn.Sigmoid()
        )
        self.up = nn.UpsamplingBilinear2d(scale_factor=kernel_size)




    def forward(self, x):
        x_avg = self.avg_pool(x)
        x_f = self.conv(x_avg)
        # x_f = torch.nn.Upsample(size=x_f.size()[2:], mode='bilinear')(x_f)
        x_f = self.up(x_f)
        out = x_f * x
        return out








class LoGFilter(nn.Module):
    def __init__(self, dim, kernel_size, sigma, norm_layer = dict(type='BN', requires_grad=True), act_layer=nn.LeakyReLU):
        super(LoGFilter, self).__init__()
        # 7x7 convolution with stride 1 for feature reinforcement, Channels from 3 to 1/4C.
        # self.conv_init = nn.Conv2d(in_c, out_c, kernel_size=3, stride=1, padding=1)
        """创建高斯-拉普拉斯核"""
        # 初始化二维坐标
        ax = torch.arange(-(kernel_size // 2), (kernel_size // 2) + 1, dtype=torch.float32)
        xx, yy = torch.meshgrid(ax, ax)
        # 计算高斯-拉普拉斯核
        kernel = (xx**2 + yy**2 - 2 * sigma**2) / (2 * math.pi * sigma**4) * torch.exp(-(xx**2 + yy**2) / (2 * sigma**2))
        # 归一化
        kernel = kernel - kernel.mean()
        kernel = kernel / kernel.sum()
        log_kernel = kernel.unsqueeze(0).unsqueeze(0) # 添加 batch 和 channel 维度
        self.LoG = nn.Conv2d(dim, dim, kernel_size=kernel_size, stride=1, padding=int(kernel_size // 2), groups=dim, bias=False)
        self.LoG.weight.data = log_kernel.repeat(dim, 1, 1, 1)
        # self.act = act_layer()
        # self.norm1 = build_norm_layer(norm_layer, out_c)[1]
        # self.norm2 = build_norm_layer(norm_layer, out_c)[1]
        # self.lapt = LocalAvgPatchcontrast(dim = out_c, kernel_size = 2)




    def forward(self, x):
        # 7x7 convolution with stride 1 for feature reinforcement, Channels from 3 to 1/4C.
        # x = self.conv_init(x)  # x = [B, C/4, H, W]
        LoG = self.LoG(x)
        # LoG_edge = self.act(self.norm1(LoG))
        # logatten = self.lapt(LoG_edge)
        # x = self.norm2(x + logatten)
        return x





if __name__ == '__main__':
    net = LoGFilter(1,7,1)
    inputs = torch.ones(1, 1, 256, 256)
    output = net(inputs)
    print(output.shape)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')




