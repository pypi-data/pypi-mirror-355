import torch
import torch.nn.functional as F
import torch.nn as nn
from thop import profile

# from PepperPepper.layers.Local_Region_Self_Attention import LRSA
from PepperPepper.layers.LoGFilter import LoGFilter
from PepperPepper.layers import VSSBlock, ResidualBlock





class conv_block(nn.Module):
    """
    Convolution Block
    """
    def __init__(self, in_ch, out_ch):
        super(conv_block, self).__init__()

        self.conv_init = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(inplace=True)
        )

        self.conv = nn.Sequential(
            nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(inplace=True))
        # in_c, out_c, kernel_size, sigma, norm_layer = dict(type='BN', requires_grad=True), act_layer = nn.ReLU
        self.log = LoGFilter(in_c=out_ch, out_c=out_ch, kernel_size=7, sigma=1)
        self.fuse_conv = nn.Sequential(
            nn.Conv2d(out_ch * 2, out_ch, kernel_size=3, stride=1, padding=1),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(inplace=True)
        )



    def forward(self, x):
        f = self.conv_init(x)
        b1 = self.conv(f) + f
        b2 = self.log(b1)
        B = torch.cat([b1, b2], dim=1)
        out = self.fuse_conv(B)
        return out


class up_conv(nn.Module):
    """
    Up Convolution Block
    """
    def __init__(self, in_ch, out_ch):
        super(up_conv, self).__init__()
        self.up = nn.Sequential(
            nn.Upsample(scale_factor=2),
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.up(x)
        return x


class U_Net(nn.Module):
    """
    UNet - Basic Implementation
    Paper : https://arxiv.org/abs/1505.04597
    """
    def __init__(self, in_ch=1, out_ch=1, dim=32):
        super(U_Net, self).__init__()

        self.title = 'Base_WAVE_H'

        n1 = dim
        filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]

        self.Maxpool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.Conv1 = conv_block(in_ch, filters[0])
        self.Conv2 = conv_block(filters[0], filters[1])
        self.Conv3 = conv_block(filters[1], filters[2])
        self.Conv4 = conv_block(filters[2], filters[3])
        self.Conv5 = conv_block(filters[3], filters[4])

        self.Up5 = up_conv(filters[4], filters[3])
        self.Up_conv5 = conv_block(filters[4], filters[3])

        self.Up4 = up_conv(filters[3], filters[2])
        self.Up_conv4 = conv_block(filters[3], filters[2])

        self.Up3 = up_conv(filters[2], filters[1])
        self.Up_conv3 = conv_block(filters[2], filters[1])

        self.Up2 = up_conv(filters[1], filters[0])
        self.Up_conv2 = conv_block(filters[1], filters[0])

        self.Conv = nn.Conv2d(filters[0], out_ch, kernel_size=1, stride=1, padding=0)

        self.active = torch.nn.Sigmoid()

    def forward(self, x):

        e1 = self.Conv1(x)

        e2 = self.Maxpool1(e1)
        e2 = self.Conv2(e2)

        e3 = self.Maxpool2(e2)
        e3 = self.Conv3(e3)

        e4 = self.Maxpool3(e3)
        e4 = self.Conv4(e4)

        e5 = self.Maxpool4(e4)
        e5 = self.Conv5(e5)

        d5 = self.Up5(e5)
        # print(e4.shape)
        # print(d5.shape)


        d5 = torch.cat((e4, d5), dim=1)
        # print(d5.shape)



        d5 = self.Up_conv5(d5)

        d4 = self.Up4(d5)
        d4 = torch.cat((e3, d4), dim=1)
        d4 = self.Up_conv4(d4)

        d3 = self.Up3(d4)
        d3 = torch.cat((e2, d3), dim=1)
        d3 = self.Up_conv3(d3)

        d2 = self.Up2(d3)
        d2 = torch.cat((e1, d2), dim=1)
        d2 = self.Up_conv2(d2)

        out = self.Conv(d2)

        # out = self.active(out)

        return out



from PepperPepper.layers.MultiWaveFusion import DWT_2D, IDWT_2D
from PepperPepper.layers import IRGAttention
from PepperPepper.layers import PatchAwareTransformer




class up_convV1(nn.Module):
    """
    Up Convolution Block
    """
    def __init__(self, in_ch, out_ch):
        super(up_convV1, self).__init__()
        self.up = nn.Sequential(
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(out_ch),
            nn.ReLU(inplace=True)
        )

    def forward(self, x):
        x = self.up(x)
        return x




class DWTModule(nn.Module):
    def __init__(self, wave = 'haar'):
        super(DWTModule, self).__init__()
        self.wave = wave
        self.dwt = DWT_2D(wave)


    def forward(self, x, filters):
        e1_dwt = self.dwt(x)
        e1_ll, e1_lh, e1_hl, e1_hh = e1_dwt.split(filters, 1)  # torch.Size([1, 32, 16, 16])
        e1_highf = torch.cat((e1_lh, e1_hl, e1_hh), 1)
        return e1_ll , e1_highf



class IDWTModule(nn.Module):
    def __init__(self, wave = 'haar'):
        super(IDWTModule, self).__init__()
        self.wave = wave
        self.idwt = IDWT_2D(wave)

    def forward(self, e_ll, e_highf):
        d_dwt = torch.cat((e_ll, e_highf), dim=1)
        d = self.idwt(d_dwt)
        return d





class WUNet2(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, dim=32, wave='haar'):
        super(WUNet2, self).__init__()
        self.title = 'Base_log'
        n1 = dim
        filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]
        self.filters = filters

        self.dwt = DWTModule(wave)
        self.idwt = IDWTModule(wave)

        self.Conv1 = conv_block(in_ch, filters[0])
        self.Conv2 = conv_block(filters[0], filters[1])
        self.Conv3 = conv_block(filters[1], filters[2])
        self.Conv4 = conv_block(filters[2], filters[3])
        self.Conv5 = conv_block(filters[3], filters[4])

        self.Up5 = up_convV1(filters[4], filters[3])
        self.Up_conv5 = conv_blockV1(filters[4], filters[3])

        self.Up4 = up_convV1(filters[3], filters[2])
        self.Up_conv4 = conv_blockV1(filters[3], filters[2])

        self.Up3 = up_convV1(filters[2], filters[1])
        self.Up_conv3 = conv_blockV1(filters[2], filters[1])

        self.Up2 = up_convV1(filters[1], filters[0])
        self.Up_conv2 = conv_blockV1(filters[1], filters[0])
        self.Conv = nn.Conv2d(filters[0], out_ch, kernel_size=1, stride=1, padding=0)

        self.mnt = PatchAwareTransformer(channel_num=[128, 256, 512, 1024], patchSize=[8, 4, 2, 1])


    def forward(self, x):

        e1 = self.Conv1(x)
        e1_ll, e1_highf = self.dwt(e1, self.filters[0])
        e2 = e1_ll


        e2 = self.Conv2(e2)
        e2_ll, e2_highf = self.dwt(e2, self.filters[1])
        e3 = e2_ll


        e3 = self.Conv3(e3)
        e3_ll, e3_highf = self.dwt(e3, self.filters[2])
        e4 = e3_ll


        e4 = self.Conv4(e4)
        e4_ll, e4_highf = self.dwt(e4, self.filters[3])
        e5 = e4_ll


        e5 = self.Conv5(e5)



        d5 = self.Up5(e5)
        d4 = self.idwt(d5, e4_highf)
        d4 = torch.cat((e4, d4), dim=1)
        d4 = self.Up_conv5(d4)

        d4 = self.Up4(d4)
        d3 = self.idwt(d4, e3_highf)
        d3 = torch.cat((e3, d3), dim=1)
        d3 = self.Up_conv4(d3)

        d3 = self.Up3(d3)
        d2 = self.idwt(d3, e2_highf)
        d2 = torch.cat((e2, d2), dim=1)
        d2 = self.Up_conv3(d2)

        d2 = self.Up2(d2)
        d1 = self.idwt(d2, e1_highf)
        d1 = self.Up_conv2(d1)
        out = self.Conv(d1)

        return out






class conv_blockV1(nn.Module):
    def __init__(self, in_ch, out_ch):
        super(conv_blockV1, self).__init__()

        self.conv = nn.Sequential(
                nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True),
                nn.Conv2d(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
                nn.BatchNorm2d(out_ch),
                nn.ReLU(inplace=True))

    def forward(self, x):
        x = self.conv(x)
        return x






class HLF(nn.Module):
    def __init__(self, dim, kernel_size=7):
        super().__init__()
        self.adjustF = nn.Sequential(
            nn.Conv2d(dim, dim * 2, kernel_size=3, stride=2, padding=1),
        )

        self.conv = nn.Sequential(
            nn.Conv2d(dim * 4, dim * 2, kernel_size=3, stride=1, padding=1),
            nn.LeakyReLU(inplace=True),
        )


        self.proj = nn.Conv2d(dim * 2, 1, kernel_size=3, stride=1, padding=1)


        self.convatten = nn.Sequential(
            nn.Conv2d(3, 1, kernel_size, padding=kernel_size // 2),
            nn.Sigmoid()
        )



        # self.vssblock = VSSBlock(
        #     hidden_dim=dim * 2,
        #     drop_path=0.0,
        #     channel_first=True,
        #     ssm_d_state=dim//2,
        #     ssm_ratio=1.0
        # )



    def forward(self, e_ll, e_highf, feature):
        fj = self.adjustF(feature)
        e = torch.cat((e_ll, e_highf), dim=1)
        e = self.conv(e)
        out = e + fj

        avg_out = torch.mean(out, dim=1, keepdim=True)
        max_out, _ = torch.max(out, dim=1, keepdim=True)
        out = self.proj(out)

        spatial_features = torch.cat([avg_out, max_out, out], dim=1)
        spatial_weights = self.convatten(spatial_features)

        return spatial_weights




class WUNet(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, dim=32, wave='haar'):
        super(WUNet, self).__init__()
        self.title = 'Base_Wave_HPROJ'
        n1 = dim
        filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]
        self.filters = filters

        self.dwt = DWTModule(wave)
        self.idwt = IDWTModule(wave)

        self.Conv1 = ResidualBlock(in_ch, filters[0])
        self.Conv2 = ResidualBlock(filters[0], filters[1])
        self.Conv3 = ResidualBlock(filters[1], filters[2])
        self.Conv4 = ResidualBlock(filters[2], filters[3])
        self.Conv5 = ResidualBlock(filters[3], filters[4])

        self.proj1 = nn.Sequential(
            nn.Conv2d(filters[0] * 3, filters[0], kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(filters[0]),
            nn.ReLU(inplace=True),
            nn.Conv2d(filters[0], filters[0] * 3, kernel_size=1, stride=1, padding=0),
        )

        self.proj2 = nn.Sequential(
            nn.Conv2d(filters[1] * 3, filters[1], kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(filters[1]),
            nn.ReLU(inplace=True),
            nn.Conv2d(filters[1], filters[1] * 3, kernel_size=1, stride=1, padding=0),
        )

        self.proj3 = nn.Sequential(
            nn.Conv2d(filters[2] * 3, filters[2], kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(filters[2]),
            nn.ReLU(inplace=True),
            nn.Conv2d(filters[2], filters[2] * 3, kernel_size=1, stride=1, padding=0),
        )

        self.proj4 = nn.Sequential(
            nn.Conv2d(filters[3] * 3, filters[3], kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(filters[3]),
            nn.ReLU(inplace=True),
            nn.Conv2d(filters[3], filters[3] * 3, kernel_size=1, stride=1, padding=0),
        )



        # self.hlf1 = HLF(filters[0])
        # self.hlf2 = HLF(filters[1])
        # self.hlf3 = HLF(filters[2])
        # self.hlf4 = HLF(filters[3])



        self.Up5 = up_convV1(filters[4], filters[3])
        self.Up_conv5 = ResidualBlock(filters[4], filters[3])

        self.Up4 = up_convV1(filters[3], filters[2])
        self.Up_conv4 = ResidualBlock(filters[3], filters[2])

        self.Up3 = up_convV1(filters[2], filters[1])
        self.Up_conv3 = ResidualBlock(filters[2], filters[1])

        self.Up2 = up_convV1(filters[1], filters[0])
        self.Up_conv2 = ResidualBlock(filters[0], filters[0])
        self.Conv = nn.Conv2d(filters[0], out_ch, kernel_size=1, stride=1, padding=0)
        # self.qkv_dim = sum([128, 256, 512, 1024]) // 4




    def forward(self, x):
        e1 = self.Conv1(x)
        e1_ll, e1_highf = self.dwt(e1, self.filters[0])
        e2 = e1_ll


        e2 = self.Conv2(e2)
        e2_ll, e2_highf = self.dwt(e2, self.filters[1])
        e3 = e2_ll


        e3 = self.Conv3(e3)
        e3_ll, e3_highf = self.dwt(e3, self.filters[2])
        e4 = e3_ll


        e4 = self.Conv4(e4)
        e4_ll, e4_highf = self.dwt(e4, self.filters[3])
        e5 = e4_ll


        e5 = self.Conv5(e5)



        d5 = self.Up5(e5)
        d4 = self.idwt(d5, e4_highf)
        d4 = torch.cat((e4, d4), dim=1)
        d4 = self.Up_conv5(d4)

        d4 = self.Up4(d4)
        d3 = self.idwt(d4, e3_highf)
        d3 = torch.cat((e3, d3), dim=1)
        d3 = self.Up_conv4(d3)

        d3 = self.Up3(d3)
        d2 = self.idwt(d3, e2_highf)
        d2 = torch.cat((e2, d2), dim=1)
        d2 = self.Up_conv3(d2)

        d2 = self.Up2(d2)
        d1 = self.idwt(d2, e1_highf)
        # d1 = torch.cat((e1, d1), dim=1)
        # print(d1.shape)
        # print(d1.shape)
        d1 = self.Up_conv2(d1)
        out = self.Conv(d1)

        return out









if __name__ == '__main__':
    model = WUNet().cuda()
    # model = U_Net().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    # output = model(inputs)
    # print(output.shape)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')



