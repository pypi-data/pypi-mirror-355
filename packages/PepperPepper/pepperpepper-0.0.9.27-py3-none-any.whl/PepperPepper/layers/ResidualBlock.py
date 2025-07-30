# from PepperPepper.environment import torch, nn
import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile



class ResidualLeakBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride = 1):
        super().__init__()
        self.proj = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1, bias=True),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU()
        )

        self.body = nn.Sequential(
            nn.Conv2d(out_channels, out_channels,  kernel_size=5, stride=stride, padding=2, bias=True),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),

            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(out_channels),
        )
        # if stride != 1 or out_channels != in_channels:
        #     self.shortcut = nn.Sequential(
        #         nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride, bias=True),
        #         nn.BatchNorm2d(out_channels),
        #     )
        # else:
        #     self.shortcut = None

        self.relu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x):
        x = self.proj(x)
        residual = x
        x = self.body(x)
        #
        # if self.shortcut is not None:
        #     residual = self.shortcut(residual)
        out = self.relu(x+residual)
        return out






class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.body = nn.Sequential(
            nn.Conv2d(in_channels, out_channels,  kernel_size=3, stride=stride, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.ReLU(True),

            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_channels),
        )
        if stride != 1 or out_channels != in_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = None

        self.relu = nn.ReLU(True)

    def forward(self, x):

        # if torch.isnan(x).any():
        #     print(x)
        #     print(f'ResidualBlock, input is nan, and the in_channels:{self.in_channels} and out_channels:{self.out_channels}')

        residual = x
        x = self.body(x)

        # if torch.isnan(x).any():
        #     print(f'ResidualBlock, body is nan, and the in_channels:{self.in_channels} and out_channels:{self.out_channels}')

        if self.shortcut is not None:
            residual = self.shortcut(residual)
        out = F.relu(x+residual)

        # if torch.isnan(out).any():
        #     print(f'ResidualBlock, out is nan, and the in_channels:{self.in_channels} and out_channels:{self.out_channels}')

        return out



if __name__ == "__main__":
    net = ResidualBlock(32, 32)
    inputs = torch.rand(1, 32, 256, 256)
    output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')