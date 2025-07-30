# Infrared Gaussian attention
import torch
import torch.nn as nn
from PepperPepper.layers import IRGradOri
from thop import profile





class MultiOrderDWConv(nn.Module):
    """使用膨胀深度卷积核的多阶特征。

    参数:
        embed_dims (int): 输入通道数。
        dw_dilation (list): 三个深度卷积层的膨胀率。
        channel_split (list): 三个分割通道的比例。
    """

    def __init__(self,
                 embed_dims,
                 dw_dilation=[1, 2, 3,],
                 channel_split=[1, 3, 4,],
                ):
        super(MultiOrderDWConv, self).__init__()

        # 计算各部分通道比例
        self.split_ratio = [i / sum(channel_split) for i in channel_split]  # 1/8   3/8   4/8

        self.embed_dims_1 = int(self.split_ratio[1] * embed_dims)       # 3/8 * embed_dims

        self.embed_dims_2 = int(self.split_ratio[2] * embed_dims)       # 4/8 * embed_dims

        self.embed_dims_0 = embed_dims - self.embed_dims_1 - self.embed_dims_2      # 1/8  * embed_dims

        self.embed_dims = embed_dims

        assert len(dw_dilation) == len(channel_split) == 3  # 确保长度正确
        assert 1 <= min(dw_dilation) and max(dw_dilation) <= 3  # 检查膨胀率范围
        assert embed_dims % sum(channel_split) == 0  # 确保embed_dims可以整除channel_split总和

        # 基础深度卷积
        self.DW_conv0 = nn.Conv2d(
            in_channels=self.embed_dims,
            out_channels=self.embed_dims,
            kernel_size=5,
            padding=(1 + 4 * dw_dilation[0]) // 2,  # 根据膨胀率计算填充
            groups=self.embed_dims,                 # 分组数量等于输入通道数
            stride=1,                      # 设置步长
            dilation=dw_dilation[0],      # 膨胀率  1
        )
        # 第二个深度卷积
        self.DW_conv1 = nn.Conv2d(
            in_channels=self.embed_dims_1,
            out_channels=self.embed_dims_1,
            kernel_size=5,
            padding=(1 + 4 * dw_dilation[1]) // 2,
            groups=self.embed_dims_1,
            stride=1,
            dilation=dw_dilation[1],        # 膨胀率  2
        )

        # 第三个深度卷积
        self.DW_conv2 = nn.Conv2d(
            in_channels=self.embed_dims_2,
            out_channels=self.embed_dims_2,
            kernel_size=7,
            padding=(1 + 6 * dw_dilation[2]) // 2,
            groups=self.embed_dims_2,
            stride=1,
            dilation=dw_dilation[2],        # 膨胀率  3
        )

        # 逐点卷积
        self.PW_conv = nn.Conv2d(  # 点卷积用于融合不同分支
            in_channels=embed_dims,
            out_channels=embed_dims,
            kernel_size=1
        )


    def forward(self, x):
        x_0 = self.DW_conv0(x)  # 第一个 5X5深度卷积

                            #[:,1/8  * embed_dims ：1/8  * embed_dims+ 3/8 * embed_dims: ...]
        x_1 = self.DW_conv1(x_0[:, self.embed_dims_0: self.embed_dims_0+self.embed_dims_1, ...])

                            # [:, embed_dims- 4/8 * embed_dims ：embed_dims: ...]
        x_2 = self.DW_conv2(x_0[:, self.embed_dims-self.embed_dims_2:, ...])

        x = torch.cat([x_0[:, :self.embed_dims_0, ...], x_1, x_2], dim=1)  # 按通道维度拼接

        x = self.PW_conv(x)     # 点卷积用于融合不同分支
        return x






class IRGAttention(nn.Module):
    def __init__(self, embed_dims):
        super(IRGAttention, self).__init__()
        self.embed_dims = embed_dims
        self.proj_1 = nn.Conv2d(
            in_channels=embed_dims, out_channels=1, kernel_size=1)
        self.IRGConv = IRGradOri(dim=1)


    def feat_IRGConv(self, x):
        x = self.proj_1(x)
        # 对x使用红外高斯卷积
        out = self.IRGConv(x)
        return out.sigmoid()



    def forward(self, x):
        # 获得高斯空间注意力
        atten = self.feat_IRGConv(x)

        # 进行多尺度操作，增加其空间上的视野

        # 输出
        # x = x + atten * x  # 残差连接
        return atten







if __name__ == "__main__":
    net = IRGAttention(embed_dims=32)
    inputs = torch.ones(1, 32, 256, 256)
    output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')



