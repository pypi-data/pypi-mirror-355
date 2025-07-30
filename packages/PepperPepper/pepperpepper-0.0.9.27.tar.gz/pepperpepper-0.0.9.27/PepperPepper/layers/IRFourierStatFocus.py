import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile
from einops import rearrange


class IRFourierStatFocus(nn.Module):
    def __init__(self, in_dims, out_dims):
        super().__init__()
        self.in_dims = in_dims
        self.out_dims = out_dims
        self.proj = nn.Sequential(
            nn.Conv2d(in_dims, out_dims, kernel_size=1, stride=1, padding=0, bias=False),
            nn.BatchNorm2d(out_dims)
        )

        # self.D = nn.Parameter(torch.ones(1))
        self.D = nn.Parameter(torch.ones(out_dims, 1, 1))  # 形状为 [out_dims, 1, 1]

    def forward(self, x):
        B, C, rows, cols = x.shape
        f = self.proj(x)
        fre = torch.fft.fft2(f, dim=(-2, -1))
        f_shift = torch.fft.fftshift(fre)

        D0 = torch.sigmoid(self.D) * (rows // 2)
        u = torch.arange(-cols // 2, cols // 2)
        v = torch.arange(-rows // 2, rows // 2)
        U, V = torch.meshgrid(u, v, indexing='xy')
        D = torch.sqrt(U ** 2 + V ** 2).detach().to(D0.device)
        D.requires_grad_(False)


        # # 查看张量所在的设备
        # print(D.device)
        # print(D0.device)
        H = 1 - torch.exp(-(D ** 2) / (2 * D0 ** 2))

        filtered_shift = f_shift * H
        filtered = torch.fft.ifftshift(filtered_shift)
        edge_freq = torch.abs(torch.fft.ifft2(filtered))

        return edge_freq


if __name__ == '__main__':
    net = IRFourierStatFocus(3, 16).cuda()
    inputs = torch.rand(4, 3, 256, 256).cuda()
    output = net(inputs)
    print(output.shape)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')