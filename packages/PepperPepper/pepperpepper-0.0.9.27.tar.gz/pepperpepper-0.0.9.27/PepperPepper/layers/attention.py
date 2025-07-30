from PepperPepper.environment import torch, nn, einops, rearrange, Rearrange

class SpatialAttention(nn.Module):
    """增强目标空间位置的注意力机制"""
    def __init__(self, kernel_size=5):
        super().__init__()
        assert kernel_size % 2 == 1, "Kernel size must be odd"
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size // 2)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 空间维度统计
        avg_out = torch.mean(x,  dim=1, keepdim=True)
        max_out, _ = torch.max(x,  dim=1, keepdim=True)


        # 空间特征拼接
        spatial_features = torch.cat([avg_out,  max_out], dim=1)
        spatial_weights = self.sigmoid(self.conv(spatial_features))
        return x * spatial_weights.expand_as(x)


class ChannelAttention(nn.Module):
    """增强目标相关通道特征的注意力机制"""

    def __init__(self, in_channels, reduction_ratio=2):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)

        # 双路径注意力机制
        self.shared_mlp = nn.Sequential(
            nn.Linear(in_channels, in_channels // reduction_ratio),
            nn.ReLU(inplace=True),
            nn.Linear(in_channels // reduction_ratio, in_channels)
        )

        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        # 通道维度统计
        avg_out = self.shared_mlp(self.avg_pool(x).view(x.size(0), -1))
        max_out = self.shared_mlp(self.max_pool(x).view(x.size(0), -1))

        # 注意力权重融合
        channel_weights = self.sigmoid(avg_out + max_out).unsqueeze(2).unsqueeze(3)
        return x * channel_weights.expand_as(x)


class AttentionalCS(nn.Module):
    """完整注意力调制模块（通道+空间级联）"""

    def __init__(self, dim):
        super().__init__()
        self.ca = ChannelAttention(dim)
        self.sa = SpatialAttention()

    def forward(self, x):
        x = self.ca(x)  # 先增强通道维度
        x = self.sa(x)  # 再增强空间维度
        return x



class PixelAttention(nn.Module):
    def __init__(self, dim):
        super(PixelAttention, self).__init__()
        self.pa2 = nn.Conv2d(2 * dim, dim, 7, padding=3, padding_mode='reflect', groups=dim, bias=True)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, pattn1):
        B, C, H, W = x.shape
        x = x.unsqueeze(dim=2)  # B, C, 1, H, W
        pattn1 = pattn1.unsqueeze(dim=2)  # B, C, 1, H, W
        x2 = torch.cat([x, pattn1], dim=2)  # B, C, 2, H, W
        x2 = Rearrange('b c t h w -> b (c t) h w')(x2)
        pattn2 = self.pa2(x2)
        pattn2 = self.sigmoid(pattn2)
        return pattn2



# sobel注意力机制
class SobelAttention(torch.nn.Module):
    def __init__(self, in_channels):
        super(SobelAttention, self).__init__()
        self.channels = in_channels

        # sobel算子
        self.sobel_v = torch.nn.Conv2d(in_channels=in_channels, out_channels=in_channels, kernel_size=3, padding=1,
                                       bias=False)
        self.sobel_h = torch.nn.Conv2d(in_channels=in_channels, out_channels=in_channels, kernel_size=3, padding=1,
                                       bias=False)

        # 初始化卷积核
        sobel_kernel_v = torch.tensor([[0, -1, 0],
                                       [0, 0, 0],
                                       [0, 1, 0]], dtype=torch.float32).view(1, 1, 3, 3)
        sobel_kernel_h = torch.tensor([[0, 0, 0],
                                       [-1, 0, 1],
                                       [0, 0, 0]], dtype=torch.float32).view(1, 1, 3, 3)

        # 将卷积核扩展到多个通道
        sobel_kernel_v = sobel_kernel_v.repeat(in_channels, in_channels, 1, 1)
        sobel_kernel_h = sobel_kernel_h.repeat(in_channels, in_channels, 1, 1)

        self.sobel_v.weight = torch.nn.Parameter(sobel_kernel_v, requires_grad=False)
        self.sobel_h.weight = torch.nn.Parameter(sobel_kernel_h, requires_grad=False)


    def forward(self, input):
        edge_x = self.sobel_h(input)
        edge_y = self.sobel_v(input)
        magnitude = torch.sqrt(edge_x ** 2 + edge_y ** 2)
        return magnitude

