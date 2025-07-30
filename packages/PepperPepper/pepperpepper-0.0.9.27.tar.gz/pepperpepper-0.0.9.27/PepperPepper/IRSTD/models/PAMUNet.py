import torch.nn as nn
import torch.nn.functional as F
import torch.utils.data
import torch



from PepperPepper.layers.MultiWaveFusion import DWT_2D, IDWT_2D
from PepperPepper.layers import Dynamic_conv2d, ODConv2d
from PepperPepper.layers.PatchAwareModule import PAM
from PepperPepper.layers import ResidualLeakBlock
from PepperPepper.layers import PAGLattention


class Encoder_conv_block(nn.Module):
    """
    Convolution Block
    """

    def __init__(self, in_ch, out_ch):
        super(Encoder_conv_block, self).__init__()


        # if mode == 'ODConv':
        #     Conv = ODConv2d
        # elif mode == 'Dynamic_conv2d':
        #     Conv = Dynamic_conv2d
        # else:
        #     Conv = nn.Conv2d
        #
        # self.conv = nn.Sequential(
        #     Conv(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
        #     nn.BatchNorm2d(out_ch),
        #     nn.ReLU(inplace=True),
        #     Conv(out_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
        #     nn.BatchNorm2d(out_ch),
        #     nn.ReLU(inplace=True))

        self.conv = ResidualLeakBlock(in_ch, out_ch)


    def forward(self, x):
        x = self.conv(x)
        return x


class Decoder_conv_block(nn.Module):
    """
    Convolution Block
    """

    def __init__(self, in_ch, out_ch):
        super(Decoder_conv_block, self).__init__()
        self.conv = ResidualLeakBlock(in_ch, out_ch)



    def forward(self, x):
        x = self.conv(x)
        return x


class up_conv(nn.Module):
    """
    Up Convolution Block
    """
    def __init__(self, in_ch, out_ch):
        super(up_conv, self).__init__()
        self.up = nn.Sequential(
            # nn.Upsample(scale_factor=2),
            nn.Conv2d(in_ch, out_ch, kernel_size=3, stride=1, padding=1, bias=True),
            nn.BatchNorm2d(out_ch),
            nn.LeakyReLU(inplace=True)
        )

    def forward(self, x):
        x = self.up(x)
        return x





class DWTModule(nn.Module):
    def __init__(self, wave = 'haar'):
        super(DWTModule, self).__init__()
        self.wave = wave
        self.dwt = DWT_2D(wave)
        # self.down = nn.MaxPool2d(2, 2)


    def forward(self, x, filters):
        e1_dwt = self.dwt(x)
        e1_ll, e1_lh, e1_hl, e1_hh = e1_dwt.split(filters, 1)  # torch.Size([1, 32, 16, 16])
        e1_highf = [e1_lh, e1_hl, e1_hh]
        # e1_down = self.down(e1_highf)
        return e1_ll , e1_highf








class IDWTModule(nn.Module):
    def __init__(self, wave = 'haar'):
        super(IDWTModule, self).__init__()
        self.wave = wave
        self.idwt = IDWT_2D(wave)

    def forward(self, d_dwt):
        d = self.idwt(d_dwt)
        return d


from PepperPepper.layers import AlternateCat

class AlCattention(nn.Module):
    def __init__(self, dim):
        super(AlCattention, self).__init__()
        self.dim = dim  # 保存通道维度参数
        # 自适应平均池化：将空间维度压缩为1x1（保留通道维度信息）
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        # 自适应最大池化：同样压缩空间维度，捕捉通道维度的最大值信息
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        # MLP多层感知机：用于将统计特征映射为通道权重
        self.alcat = AlternateCat(dim=1, num=3)
        self.share_mlp = nn.Sequential(
            nn.Conv2d(dim * 3, dim, kernel_size=1 , stride=1, padding=0, bias=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(dim, dim, kernel_size=1 , stride=1, padding=0, bias=True),
            nn.ReLU(inplace=True),
            nn.Conv2d(dim, dim, kernel_size=1 , stride=1, padding=0, bias=True),
            nn.Sigmoid()
        )

        self.spconv = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=3 , stride=1, padding=1, bias=True),
            nn.Sigmoid()
        )

    def forward(self, x, highf):
        x_avg = self.avg_pool(x)
        x_max = self.max_pool(x)
        std = torch.std(x, dim=(2, 3), keepdim=True)  # 空间维度标准差：(B, 2C)
        x_ams = self.alcat([x_avg, x_max, std])
        channel_weights = self.share_mlp(x_ams)
        x_1 = x * channel_weights + x



        avg_out = torch.mean(x_1, dim=1, keepdim=True)
        max_out, _ = torch.max(x_1, dim=1, keepdim=True)

        # 空间特征拼接
        spatial_features = torch.cat([avg_out,  max_out], dim=1)
        spatial_weights = self.spconv(spatial_features)
        dwt = []
        dwt.append(x_1)
        for i in range(len(highf)):
            temp = highf[i] * spatial_weights.expand_as(highf[i]) + highf[i]
            dwt.append(temp)
        dwt = torch.cat(dwt, dim=1)
        return dwt










class UNet(nn.Module):
    """
    UNet - Basic Implementation
    Paper : https://arxiv.org/abs/1505.04597
    """

    def __init__(self, in_ch=1, out_ch=1, dim=32):
        super(UNet, self).__init__()
        self.title = "UNet"


        n1 = dim
        self.dim = dim
        # filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]

        # self.filters = filters

        self.Maxpool1 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.Maxpool4 = nn.MaxPool2d(kernel_size=2, stride=2)

        self.Conv1 = Encoder_conv_block(in_ch, dim)
        self.Conv2 = Encoder_conv_block(dim, dim)
        self.Conv3 = Encoder_conv_block(dim, dim)
        self.Conv4 = Encoder_conv_block(dim, dim)
        self.Conv5 = Encoder_conv_block(dim, dim)

        self.Up5 = up_conv(dim, dim)
        self.Up_conv5 = Decoder_conv_block(dim * 2, dim)

        self.Up4 = up_conv(dim, dim)
        self.Up_conv4 = Decoder_conv_block(dim * 2, dim)

        self.Up3 = up_conv(dim, dim)
        self.Up_conv3 = Decoder_conv_block(dim * 2, dim)

        self.Up2 = up_conv(dim, dim)
        self.Up_conv2 = Decoder_conv_block(dim * 2, dim)

        self.Conv = nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0)

        self.Outv5 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=8)
        )

        self.Outv4 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=4)
        )

        self.Outv3 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=2)
        )

        self.Outv2 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=1)
        )

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
        pred5 = self.Outv5(d5)
        d5 = torch.cat((e4, d5), dim=1)
        d5 = self.Up_conv5(d5)

        d4 = self.Up4(d5)
        pred4 = self.Outv4(d4)
        d4 = torch.cat((e3, d4), dim=1)
        d4 = self.Up_conv4(d4)

        d3 = self.Up3(d4)
        pred3 = self.Outv3(d3)
        d3 = torch.cat((e2, d3), dim=1)
        d3 = self.Up_conv3(d3)

        d2 = self.Up2(d3)
        pred2 = self.Outv2(d2)
        d2 = torch.cat((e1, d2), dim=1)
        d2 = self.Up_conv2(d2)
        out = self.Conv(d2)

        if self.training:
            pred = []
            pred.append(pred5)
            pred.append(pred4)
            pred.append(pred3)
            pred.append(pred2)
            pred.append(out)
            return pred
        else:
            return out


from PepperPepper.layers.PAGLattention import PAGLattention

class PAM_UNet(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, dim=32, feature_size=[256, 128, 64, 32, 16]):
        super().__init__()


        n1 = dim
        self.dim = dim
        # filters = [n1, n1 * 2, n1 * 4, n1 * 8, n1 * 16]
        # self.filters = filters

        self.Maxpool = nn.MaxPool2d(kernel_size=2, stride=2)
        # self.Maxpool2 = nn.MaxPool2d(kernel_size=2, stride=2)
        # self.Maxpool3 = nn.MaxPool2d(kernel_size=2, stride=2)
        # self.Maxpool4 = nn.MaxPool2d(kernel_size=2, stride=2)
        self.dwtdown = DWTModule()
        self.idwtup = IDWTModule()



        self.Conv1 = Encoder_conv_block(in_ch, dim)
        self.Conv1_d = nn.Conv2d(dim * 2, dim, kernel_size=1, stride=1, padding=0)
        self.Conv2 = Encoder_conv_block(dim, dim)
        self.Conv2_d = nn.Conv2d(dim * 2, dim, kernel_size=1, stride=1, padding=0)
        self.Conv3 = Encoder_conv_block(dim, dim)
        self.Conv3_d = nn.Conv2d(dim * 2, dim, kernel_size=1, stride=1, padding=0)
        self.Conv4 = Encoder_conv_block(dim, dim)
        self.Conv4_d = nn.Conv2d(dim * 2, dim, kernel_size=1, stride=1, padding=0)
        self.Conv5 = Encoder_conv_block(dim, dim)



        self.ca5 = AlCattention(dim)
        self.Up5 = up_conv(dim, dim)
        self.Up_conv5 = Decoder_conv_block(dim * 2, dim)

        self.ca4 = AlCattention(dim)
        self.Up4 = up_conv(dim, dim)
        self.Up_conv4 = Decoder_conv_block(dim * 2, dim)

        self.ca3 = AlCattention(dim)
        self.Up3 = up_conv(dim, dim)
        self.Up_conv3 = Decoder_conv_block(dim * 2, dim)

        self.ca2 = AlCattention(dim)
        self.Up2 = up_conv(dim, dim)
        self.Up_conv2 = Decoder_conv_block(dim * 2, dim)

        self.Conv = nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0)

        self.Outv5 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=8)
        )

        self.Outv4 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=4)
        )

        self.Outv3 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=2)
        )

        self.Outv2 = nn.Sequential(
            nn.Conv2d(dim, out_ch, kernel_size=1, stride=1, padding=0),
            nn.Upsample(scale_factor=1)
        )




        self.PAM = PAM(self.dim, out_ch,feature_size=[256, 128, 64, 32, 16], num_layers=2)
        self.title = 'UNet_PAM_PAGL_Wave'
        # self.title = 'UNet_PAM_Wave'
        self.PGA = nn.ModuleList()

        for i in range(len(feature_size)):
            self.PGA.append(PAGLattention(dim, feature_size=feature_size[i], Patchnum=16))


    def forward(self, x):
        e1 = self.Conv1(x)
        # e2 = self.Maxpool1(e1)
        e1_ll, _ = self.dwtdown(e1, self.dim)
        e1_down = self.Maxpool(e1)
        e2 = self.Conv1_d(torch.cat([e1_ll, e1_down], dim=1))
        e2 = self.Conv2(e2)

        # e3 = self.Maxpool2(e2)
        e2_ll, _ = self.dwtdown(e2, self.dim)
        e2_down = self.Maxpool(e2)
        e3 =  self.Conv2_d(torch.cat([e2_ll, e2_down], dim=1))
        e3 = self.Conv3(e3)

        # e4 = self.Maxpool3(e3)
        e3_ll, _ = self.dwtdown(e3, self.dim)
        e3_down = self.Maxpool(e3)
        e4 = self.Conv3_d(torch.cat([e3_ll, e3_down], dim=1))
        e4 = self.Conv4(e4)

        # e5 = self.Maxpool4(e4)
        e4_ll, _ = self.dwtdown(e4, self.dim)
        e4_down = self.Maxpool(e4)
        e5 = self.Conv4_d(torch.cat([e4_ll, e4_down], dim=1))
        e5 = self.Conv5(e5)

        # PatchAware阶段
        Fan_feature = [e1, e2, e3, e4, e5]

        # 块感知模块，进行感知区域
        PAM_out, PAM_feature = self.PAM(Fan_feature)

        for i in range(len(self.PGA)):
            var_name = f'e{i + 1}'
            if var_name in locals():
                # tempout = locals()[var_name]
                tempout = Fan_feature[i]
                tempout = self.PGA[i](tempout, PAM_feature)
                # print(tempout.shape)
                # locals()[var_name] = tempout
                Fan_feature[i] = tempout

        e1, e2, e3, e4, e5 = Fan_feature

        _, e1_highf = self.dwtdown(e1, self.dim)
        _, e2_highf = self.dwtdown(e2, self.dim)
        _, e3_highf = self.dwtdown(e3, self.dim)
        _, e4_highf = self.dwtdown(e4, self.dim)


        # print(PAM_feature.shape)
        # print(e5.shape)         # [1, 32, 16, 16]
        # e5_idwt = torch.cat([e5] + e4_highf, dim=1)
        e5_idwt = self.ca5(e5, e4_highf)
        e5_idwt = self.idwtup(e5_idwt)
        d5 = self.Up5(e5_idwt)
        # print(d5.shape)         # [1, 32, 32, 32]

        pred5 = self.Outv5(d5)
        # print(pred5.shape)      # [1, 1, 256, 256]

        d5 = torch.cat((e4, d5), dim=1)
        d5 = self.Up_conv5(d5)

        # print(d5.shape)
        # e4_idwt = torch.cat([d5] + e3_highf, dim=1)
        e4_idwt = self.ca4(d5, e3_highf)
        e4_idwt = self.idwtup(e4_idwt)
        d4 = self.Up4(e4_idwt)
        pred4 = self.Outv4(d4)
        d4 = torch.cat((e3, d4), dim=1)
        d4 = self.Up_conv4(d4)

        e3_idwt = self.ca3(d4, e2_highf)
        # e3_idwt = torch.cat([d4] + e2_highf, dim=1)
        e3_idwt = self.idwtup(e3_idwt)
        d3 = self.Up3(e3_idwt)
        pred3 = self.Outv3(d3)
        d3 = torch.cat((e2, d3), dim=1)
        d3 = self.Up_conv3(d3)

        e2_idwt = self.ca2(d3, e1_highf)
        # e2_idwt = torch.cat([d3] + e1_highf, dim=1)
        e2_idwt = self.idwtup(e2_idwt)

        d2 = self.Up2(e2_idwt)
        pred2 = self.Outv2(d2)
        # print(pred2.shape)
        d2 = torch.cat((e1, d2), dim=1)
        d2 = self.Up_conv2(d2)
        out = self.Conv(d2)

        if self.training:
            pred = []
            pred.append(pred5)
            pred.append(pred4)
            pred.append(pred3)
            pred.append(pred2)
            pred.append(out)
            return pred, PAM_out
        else:
            return out, PAM_out


from thop import profile





if __name__ == '__main__':
    model = PAM_UNet().cuda()
    # model = UNet().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')










    

















