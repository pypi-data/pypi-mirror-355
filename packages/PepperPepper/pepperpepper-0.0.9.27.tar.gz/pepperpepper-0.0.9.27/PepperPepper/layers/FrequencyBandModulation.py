import torch.nn as nn
import torch
from PepperPepper.layers import AlternateCat




class CA(nn.Module):
    """增强目标相关通道特征的注意力机制"""
    def __init__(self, in_channels, out_channels, reduction_ratio=1):
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
            nn.LeakyReLU(0.2, inplace=True),
            nn.Conv2d(in_channels // reduction_ratio, out_channels, kernel_size=1, stride=1, padding=0),
        )

    def forward(self, x):
        # 通道维度统计
        avg_out = self.avg_pool(x)
        max_out = self.max_pool(x)

        am_out = self.amcat([avg_out, max_out])
        am_out = self.amconv(am_out)
        am_out = self.mlp(am_out)
        am_out = am_out.view(am_out.size(0), -1)
        return am_out








class FrequencyBandModulation(nn.Module):
    def __init__(self, dim, BandNum=4):
        super().__init__()
        self.BandNum = BandNum
        self.dim = dim
        self.cutoffLayer = CA(dim, BandNum)
        self.BandLayer = CA(dim, BandNum)
        # self.conv = nn.Sequential(
        #     nn.Conv2d(dim * BandNum, dim, kernel_size=3, stride=1, padding=1),
        #     nn.BatchNorm2d(dim),
        #     nn.LeakyReLU(0.2, inplace=True),
        # )




    def forward(self, x):
        B, C, H, W = x.shape

        # 1. Get frequency band cutoffs
        cutoff = self.cutoffLayer(x)  # [B, BandNum]
        cutoff = torch.softmax(cutoff, dim=-1) * 0.5
        cum_cutoff = torch.cumsum(cutoff, dim=-1)  # [B, BandNum]

        bandweight = self.BandLayer(x)
        filters = torch.softmax(bandweight, dim=-1) * 4
        # bandweight = bandweight.view(B, self.BandNum, self.dim, 1, 1)
        # filters = torch.sigmoid(bandweight)
        # print(bandweight.shape)


        # bandweight = torch.sigmoid(bandweight)
        # print(bandweight.shape)

        # print(cum_cutoff.shape)

        # 2. Perform FFT on input features
        x_fft = torch.fft.rfft2(x, norm='ortho')
        x_fft = torch.cat([x_fft.real, x_fft.imag], dim=1)  # [B, 2C, H, W//2+1]

        freqs_h = torch.fft.fftfreq(H, device=x.device).abs().view(1, 1, H, 1)
        freqs_w = torch.fft.rfftfreq(W,  device=x.device).abs().view(1,  1, 1, W//2+1)
        freqs = torch.sqrt(freqs_h ** 2 + freqs_w ** 2)  # [1, 1, H, W//2+1]

        masks = []

        for i in range(self.BandNum):
            if i == 0:
                mask = (freqs <= cum_cutoff[:, i, None, None, None])
            else:
                mask = (freqs > cum_cutoff[:, i - 1, None, None, None]) & \
                       (freqs <= cum_cutoff[:, i, None, None, None])
            # print(mask.shape)
            masks.append(mask.float())

        # 4. Apply masks and inverse FFT for each band
        band_features = []
        band_features_sum = 0
        real, imag = x_fft.chunk(2, dim=1)
        x_fft_complex = torch.complex(real, imag)

        for i in range(self.BandNum):
            masked_fft = x_fft_complex * masks[i]
            band_feature = torch.fft.irfft2(masked_fft, s=(H, W), norm='ortho')

            # Apply learned frequency filter
            # filtered = band_feature * self.filters[i]
            # print(band_feature.shape)
            # print(filters.shape)
            filtered = band_feature * filters[:, i, None, None, None]
            band_features_sum += filtered
            band_features.append(filtered)

            # 5. Combine all band features
        # output = torch.stack(band_features, dim=1)  # [B, BandNum, C, H, W]
        # output = torch.cat(band_features, dim=1)
        # output = self.conv(output)

        return band_features_sum






from thop import profile
if __name__ == '__main__':
    x = torch.randn(2, 32, 20, 20).cuda()
    FBM = FrequencyBandModulation(32).cuda()

    y = FBM(x)
    # print(len(y))

    flops, params = profile(FBM, (x,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')
