from PepperPepper.layers import IRGradOri, MultiScaleSPWDilate, AttentionalCS, Coopetition_Fuse, ResidualLeakBlock, AlternateCat, IRFourierStatFocus
from torch.nn.init  import trunc_normal_
import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile





class IRGradSkip(nn.Module):
    def __init__(self, dim, kernel_size=[5, 9]):
        super().__init__()
        self.dim = dim
        self.kernel_size = kernel_size
        self.gradori = nn.ModuleList()
        for i in range(len(kernel_size)):
            self.gradori.append(IRGradOri(dim, kernel_size=kernel_size[i]))

        self.proj = nn.Sequential(
            nn.Conv2d(dim * (len(kernel_size) + 1), dim, kernel_size=1),
            nn.BatchNorm2d(dim),
            nn.LeakyReLU(0.2),
        )
        self.MSPWD = MultiScaleSPWDilate(dim)
        self.ACS = AttentionalCS(dim)

    def forward(self, x):
        grad_list = []
        grad_list.append(x)
        for i in range(len(self.kernel_size)):
            grad = self.gradori[i](x)
            grad_list.append(grad)

        # act = self.ACT(grad_list)
        act = torch.cat(grad_list, dim=1)
        fproj = self.proj(act)
        fmspwd = self.MSPWD(fproj)
        fout = self.ACS(fmspwd)
        return fout



class Uplayer(nn.Module):
    def __init__(self, in_channels, out_channels):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.proj = nn.Conv2d(in_channels, out_channels, 1)
        self.CPF = Coopetition_Fuse(2)
        # self.residual = ResidualLeakBlock(out_channels, out_channels)
        self.residual = Downlayer(out_channels, out_channels)

    def forward(self, x, skip_x):
        fproj = self.proj(x)
        assert fproj.shape == skip_x.shape
        fcpf = self.CPF([fproj, skip_x])
        # fcpf = fproj + skip_x
        cout = self.residual(fcpf)
        return cout



class Downlayer(nn.Module):
    def __init__(self, in_channels, out_channels, stride = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.stride = stride

        self.step1 = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, 1),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(0.2, inplace=True)
        )

        self.step2 = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, 3, 1, 1),
            nn.BatchNorm2d(out_channels)
        )

        self.irfs = nn.Sequential(
            # IRFourierStatFocus(out_channels, out_channels),
            # nn.BatchNorm2d(out_channels)
            nn.Identity()
        )


        if stride != 1 or out_channels != in_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels),
            )
        else:
            self.shortcut = None

        self.relu = nn.LeakyReLU(0.2, inplace=True)

    def forward(self, x):
        if torch.isnan(x).any():
            print(f"[{self.__class__.__name__}] input_x")
        residual = x
        if torch.isnan(residual).any():
            print(f"[{self.__class__.__name__}] residual")
        f1 = self.step1(x)
        if torch.isnan(f1).any():
            print(f"[{self.__class__.__name__}] f1")

        irfse = self.irfs(f1)
        if torch.isnan(irfse).any():
            print(f"[{self.__class__.__name__}] irfse")
        f2 = self.step2(f1)
        if torch.isnan(f2).any():
            print(f"[{self.__class__.__name__}] f2")



        if self.shortcut is not None:
            residual = self.shortcut(residual)
            if torch.isnan(residual).any():
                print(f"[{self.__class__.__name__}] residual")


        out = self.relu(residual + f2 + irfse)

        if torch.isnan(out).any():
            print(f"[{self.__class__.__name__}] out")


        return out




class IRGradOriNet(nn.Module):
    def __init__(self, in_dim = 3, dim=32, num_classes=1):
        super().__init__()
        # self.title = 'IRGradOriNet_IRFSV3_IRGS_dim32_angle45'
        # self.title = 'IRGradOriNet_IRFS_dim32'
        self.title = 'BASE_UNET_dim32_CPF_IRGS'

        self.in_dim = in_dim
        self.dim = dim
        self.num_classes = num_classes

        self.downsample = nn.MaxPool2d(2, 2)
        self.upsample = nn.Upsample(scale_factor=2)

        self.downlayer1 = Downlayer(in_channels=in_dim, out_channels=dim * 1)
        self.downlayer2 = Downlayer(in_channels=dim * 1 , out_channels=dim * 2)
        self.downlayer3 = Downlayer(in_channels=dim * 2, out_channels=dim * 4)
        self.downlayer4 = Downlayer(in_channels=dim * 4, out_channels=dim * 8)


        self.skip1 = IRGradSkip(dim=dim * 1, kernel_size=[3])
        self.skip2 = IRGradSkip(dim=dim * 2, kernel_size=[3])
        self.skip3 = IRGradSkip(dim=dim * 4, kernel_size=[3])

        self.uplayer3 = Uplayer(in_channels=dim * 8, out_channels=dim * 4)
        self.uplayer2 = Uplayer(in_channels=dim * 4, out_channels=dim * 2)
        self.uplayer1 = Uplayer(in_channels=dim * 2, out_channels=dim * 1)

        self.cout = nn.Conv2d(dim, num_classes, 1)
        self.coud2 = nn.Sequential(
            nn.Conv2d(dim * 2, 1, 1),
            nn.Upsample(scale_factor=2)
        )

        self.coud3 = nn.Sequential(
            nn.Conv2d(dim * 4, 1, 1),
            nn.Upsample(scale_factor=4)
        )

        self.apply(self._init_weights)





    def forward(self, x):
        if x.size(1) == 1:
            x = x.repeat(1, self.in_dim, 1, 1)

        f1 = self.downlayer1(x)
        f2 = self.downlayer2(self.downsample(f1))
        f3 = self.downlayer3(self.downsample(f2))
        f4 = self.downlayer4(self.downsample(f3))

        fskip1 = self.skip1(f1)
        fskip2 = self.skip2(f2)
        fskip3 = self.skip3(f3)
        # fskip1 = f1
        # fskip2 = f2
        # fskip3 = f3


        d3 = self.uplayer3(self.upsample(f4), fskip3)
        d2 = self.uplayer2(self.upsample(d3), fskip2)
        d1 = self.uplayer1(self.upsample(d2), fskip1)
        out = self.cout(d1)
        return out

    def _init_weights(self, m):
        """ 增强版权重初始化方法，支持主流网络层类型
        核心策略：
        - Transformer风格线性层初始化
        - CNN优化卷积层初始化
        - 自适应归一化层处理
        """

        # 线性层初始化（适配Transformer结构）
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=0.02)  # 截断正态分布，限制极端值
            if m.bias is not None:  # 偏置项零初始化
                nn.init.zeros_(m.bias)

                # 卷积层初始化（适配CNN结构）
        elif isinstance(m, nn.Conv2d):
            # 计算Kaiming初始化标准差
            fan_in = m.kernel_size[0] * m.kernel_size[1] * m.in_channels
            # 使用ReLU激活的推荐模式（兼容GELU/SiLU）
            nn.init.kaiming_normal_(m.weight,
                                    mode='fan_in',
                                    nonlinearity='relu')
            if m.bias is not None:  # 偏置项零初始化
                nn.init.zeros_(m.bias)

                # 归一化层初始化
        elif isinstance(m, (nn.LayerNorm, nn.BatchNorm2d)):
            nn.init.ones_(m.weight)  # 缩放系数初始为1
            nn.init.zeros_(m.bias)  # 平移系数初始为0



if __name__ == '__main__':
    model = IRGradOriNet().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    if torch.isnan(output).any():
        print(f"NaN detected at layer output: {output}")
        # break

    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')


