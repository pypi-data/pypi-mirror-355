import torch
import torch.nn.functional as F
import torch.nn as nn
from PepperPepper.layers import Dynamic_conv2d, LoGFilter, ResidualLeakBlock, IRGradOri, AttentionalCS, AlternateCat, ResidualLeakBlock, extractembedding, FrequencyBandModulation

class Extractor(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(Extractor, self).__init__()

        self.body = nn.Sequential(
            Dynamic_conv2d(in_channels, out_channels,  kernel_size=3, ratio=0.25, stride=1, padding=1),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True),

            Dynamic_conv2d(out_channels, out_channels,  kernel_size=3, ratio=0.25, stride=1, padding=1),
            nn.BatchNorm2d(out_channels),
        )

        if in_channels != out_channels:
            self.shortcut = nn.Sequential(
                Dynamic_conv2d(in_channels, out_channels, kernel_size=1),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = None

        self.relu = nn.LeakyReLU(0.2, inplace=True)



    def forward(self, x):
        residual = x
        x = self.body(x)

        if self.shortcut is not None:
            residual = self.shortcut(residual)
        out = self.relu(x+residual)

        return out



class SA(nn.Module):
    def __init__(self, kernel_size=3):
        super().__init__()
        assert kernel_size % 2 == 1, "Kernel size must be odd"

        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size // 2)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 空间维度统计
        avg_out = torch.mean(x, dim=1, keepdim=True)
        max_out, _ = torch.max(x, dim=1, keepdim=True)

        # 空间特征拼接
        spatial_features = torch.cat([avg_out, max_out], dim=1)
        spatial_weights = self.sigmoid(self.conv(spatial_features))
        return x * spatial_weights.expand_as(x)



class CA(nn.Module):
    """增强目标相关通道特征的注意力机制"""

    def __init__(self, in_channels, reduction_ratio=2):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.amcat = AlternateCat(dim=1, num=2)
        self.amconv = nn.Sequential(
            nn.Conv2d(in_channels * 2, in_channels, kernel_size=1, stride=1, padding=0, groups=in_channels),
            nn.BatchNorm2d(in_channels),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.mlp = nn.Sequential(
            nn.Conv2d(in_channels , in_channels // reduction_ratio, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(in_channels // reduction_ratio),
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(in_channels // reduction_ratio, in_channels, kernel_size=1, stride=1, padding=0),
        )

        # 双路径注意力机制
        # self.shared_mlp = nn.Sequential(
        #     nn.Linear(in_channels, in_channels // reduction_ratio),
        #     nn.LeakyReLU(inplace=True),
        #     nn.Linear(in_channels // reduction_ratio, in_channels)
        # )

        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 通道维度统计
        # avg_out = self.shared_mlp(self.avg_pool(x).view(x.size(0), -1))
        # max_out = self.shared_mlp(self.max_pool(x).view(x.size(0), -1))
        # print(avg_out.shape, max_out.shape)
        avg_out = self.avg_pool(x)
        max_out = self.max_pool(x)
        # print(avg_out.shape)
        # print(max_out.shape)

        am_out = self.amcat([avg_out, max_out])
        am_out = self.amconv(am_out)
        am_out = self.mlp(am_out)
        # print(am_out.shape) # Bx32x1x1
        # 注意力权重融合
        channel_weights = self.sigmoid(am_out)
        return x * channel_weights


# from PepperPepper.layers.FDConv_initialversion import FrequencyBandModulation
class Middlestage(nn.Module):
    def __init__(self, dim):
        super(Middlestage, self).__init__()
        self.ca = CA(dim, reduction_ratio=2)
        self.sa = SA(3)
        self.fbm = FrequencyBandModulation(dim)
        self.conv = nn.Sequential(
            nn.Conv2d(dim , dim , kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(dim),
            nn.LeakyReLU(0.2, inplace=True),
        )

        self.adjf = nn.Sequential(
            nn.Conv2d(dim * 2, dim , kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(dim ),
            nn.LeakyReLU(0.2, inplace=True),
        )
        self.conv = nn.Sequential(
            nn.Conv2d(dim, dim , kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(dim),
            nn.LeakyReLU(0.2, inplace=True),
        )


    def forward(self, x):
        res = x.clone()
        x = self.conv(x)
        fbm = self.fbm(x)
        sa = self.sa(x)
        midf = torch.cat([sa, fbm], dim=1)
        midf = self.adjf(midf)
        x = self.ca(midf) + res
        out = self.conv(x)
        return out




from PepperPepper.layers import _FCNHead




class segpix(nn.Module):
    def __init__(self, in_dim = 3, out_dim = 1, dim = 32):
        super(segpix, self).__init__()
        self.title = 'trainV17'
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.dim = dim
        self.extractor = Extractor(in_channels=in_dim, out_channels=dim)

        self.middlestage = nn.Sequential(
            Middlestage(dim=dim),
            # Middlestage(dim=dim),
        )


        self.finalstage = nn.Sequential(
            ResidualLeakBlock(dim, dim),
            _FCNHead(dim, out_dim),
        )

    def forward(self, x):
        if x.size(1) == 1:
            x = x.repeat(1, self.in_dim, 1, 1)
        e1 = self.extractor(x)
        e2 = self.middlestage(e1)
        out = self.finalstage(e2)
        return out



from thop import profile








if __name__ == '__main__':
    model = segpix().cuda()
    x = torch.randn(2,1,16,16).cuda()
    y = model(x)
    print(y.shape)

    flops, params = profile(model, (x,))
    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')