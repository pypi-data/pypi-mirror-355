import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile

class ResidualBlock(nn.Module):
    def __init__(self, in_channels, out_channels, stride = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.body = nn.Sequential(
            nn.Conv2d(in_channels, out_channels,  kernel_size=3, stride=stride, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(True),
            nn.Conv2d(out_channels, out_channels, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_channels),
        )
        if stride != 1 or out_channels != in_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels)
            )
        else:
            self.shortcut = None
        self.relu = nn.LeakyReLU(True)

    def forward(self, x):
        residual = x
        x = self.body(x)
        if self.shortcut is not None:
            residual = self.shortcut(residual)
        out = F.leaky_relu_(x+residual)
        return out

class IRWACV(nn.Module):
    def __init__(self,in_dim = 3, dim=32, num_classes=1):
        super().__init__()
        self.title = 'DPRes'
        self.stem = ResidualBlock(in_dim, dim)
        self.stage = ResidualBlock(dim, dim)
        self.stage2 = ResidualBlock(dim, dim)
        self.out = ResidualBlock(dim, num_classes)


    def forward(self, x):
        if x.size(1) == 1:
            x = x.repeat(1, 3, 1, 1)


        out = self.stem(x)
        out = self.stage(out)
        out = self.stage2(out)
        out = self.out(out)
        return out


if __name__ == '__main__':
    model = IRWACV().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    if torch.isnan(output).any():
        print(f"NaN detected at layer output: {output}")

    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')










