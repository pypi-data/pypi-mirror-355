import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile
from mamba_ssm import Mamba
import torch







class RCLayer(nn.Module):
    def __init__(self, dim, reduction=16):
        super(RCLayer, self).__init__()

        self.avgPoolW = nn.AdaptiveAvgPool2d((1, None))
        self.maxPoolW = nn.AdaptiveMaxPool2d((1, None))

        self.avgPoolH = nn.AdaptiveAvgPool2d((None, 1))
        self.maxPoolH = nn.AdaptiveMaxPool2d((None, 1))


        self.projW = nn.Sequential(
            nn.Conv2d(dim * 2, dim * 2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(dim * 2),
            nn.LeakyReLU(),
        )


        self.projH = nn.Sequential(
            nn.Conv2d(dim * 2, dim * 2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(dim * 2),
            nn.LeakyReLU(),
        )










    def forward(self, x):
        N, C, H, W = x.size()
        res = x
        x_W = torch.cat([self.avgPoolW(x), self.maxPoolW(x)], dim=1)
        x_H = torch.cat([self.avgPoolH(x), self.maxPoolH(x)], dim=1)

        x_W = self.projW(x_W)
        x_H = self.projH(x_H)


        print(x_W.shape)
        print(x_H.shape)


        return x





if __name__ == '__main__':
    x = torch.randn(1, 3, 256, 256)
    net = RCLayer(dim=3)

    flops, params = profile(net, (x,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')




