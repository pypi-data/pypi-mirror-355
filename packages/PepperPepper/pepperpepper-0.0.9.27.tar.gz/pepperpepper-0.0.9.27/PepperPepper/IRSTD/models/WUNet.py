import torch
import torch.nn.functional as F
import torch.nn as nn
from einops.array_api import rearrange
from thop import profile
from PepperPepper.layers import VSSBlock, ResidualBlock, ResidualLeakBlock
from PepperPepper.layers.MultiWaveFusion import DWT_2D, IDWT_2D
from PepperPepper.layers.PatchAwareModule import PAM
from einops import rearrange
import math


class conv_block(nn.Module):
    """
    Convolution Block
    """
    def __init__(self, in_ch, out_ch):
        super(conv_block, self).__init__()
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
            # nn.ReLU(inplace=True)
            nn.LeakyReLU(inplace=True),
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
        e1_highf = [e1_lh, e1_hl, e1_hh]
        return e1_ll , e1_highf

class IDWTModule(nn.Module):
    def __init__(self, wave = 'haar'):
        super(IDWTModule, self).__init__()
        self.wave = wave
        self.idwt = IDWT_2D(wave)

    def forward(self, d_dwt):
        d = self.idwt(d_dwt)
        return d


from PepperPepper.layers import AlternateCat, AttentionalCS

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



class DWTConv(nn.Module):
    def __init__(self, in_channels, out_channels, wave='haar'):
        super(DWTConv, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.dwt = DWTModule(wave)
        self.conv = ResidualLeakBlock(in_channels, out_channels)

    def forward(self, x):
        # e = self.conv(x)
        e_ll, e_highf = self.dwt(x, self.in_channels)
        e_ll = self.conv(e_ll)
        return e_ll, e_highf





class IDWTConv(nn.Module):
    def __init__(self, in_channels, out_channels, wave='haar'):
        super(IDWTConv, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.ChConv = up_conv(in_channels, out_channels)
        # self.fcm = FCM(out_channels, wave='haar')
        self.alca = AlCattention(out_channels)
        self.Conv = ResidualLeakBlock(out_channels * 2, out_channels)
        self.idwt = IDWTModule(wave)

    def forward(self, d, e, highf):
        d = self.ChConv(d)
        dwt = self.alca(d, highf)
        d = self.idwt(dwt)
        out = self.Conv(torch.cat((d, e), dim=1))
        return out






class WUNet(nn.Module):
    def __init__(self, in_ch=1, out_ch=1, dim=32, wave='haar'):
        super(WUNet, self).__init__()
        # self.title = 'RsidualConv_WaveMaxPool_CAtten(caV1)_SAD_Multiout'
        self.title = 'Wave'
        n1 = dim
        filters = [n1, n1 , n1 , n1 , n1 ] # 32, 64, 128, 256, 512
        self.filters = filters
        self.Conv1 = ResidualLeakBlock(in_ch, filters[0])
        self.Conv2 = DWTConv(filters[0], filters[1])
        self.Conv3 = DWTConv(filters[1], filters[2])
        self.Conv4 = DWTConv(filters[2], filters[3])
        self.Conv5 = DWTConv(filters[3], filters[4])

        self.DConv4 = IDWTConv(filters[4], filters[3], wave)
        self.DConv3 = IDWTConv(filters[3], filters[2], wave)
        self.DConv2 = IDWTConv(filters[2], filters[1], wave)
        self.DConv1 = IDWTConv(filters[1], filters[0], wave)
        self.Conv = nn.Conv2d(filters[0], out_ch, kernel_size=1, stride=1, padding=0)

        self.Conv_out = nn.ModuleList()
        for i in range(1, len(filters)):
            temp_block = nn.Sequential(
                nn.Conv2d(filters[i], out_ch, kernel_size=1, stride=1, padding=0),
                nn.Upsample(scale_factor=2 ** i,  mode='bilinear')
            )
            self.Conv_out.append(temp_block)





    def forward(self, x):
        e1 = self.Conv1(x)
        e2, e1_highf = self.Conv2(e1)
        e3, e2_highf = self.Conv3(e2)
        e4, e3_highf = self.Conv4(e3)
        e5, e4_highf = self.Conv5(e4)

        # Fan_feature = [e1, e2, e3, e4, e5]
        #
        # # 块感知模块，进行感知区域
        # PAM_out, PAM_feature = self.PAM(Fan_feature)
        #
        # for i in range(len(self.PGA)):
        #     var_name = f'e{i + 1}'
        #     if var_name in locals():
        #         # tempout = locals()[var_name]
        #         tempout = Fan_feature[i]
        #         tempout = self.PGA[i](tempout, PAM_feature)
        #         # print(tempout.shape)
        #         # locals()[var_name] = tempout
        #         Fan_feature[i] = tempout
        #
        # e1, e2, e3, e4, e5 = Fan_feature




        d5_out = e5
        d4_out = self.DConv4(d5_out, e4, e4_highf)
        d3_out = self.DConv3(d4_out, e3, e3_highf)
        d2_out = self.DConv2(d3_out, e2, e2_highf)
        d1_out = self.DConv1(d2_out, e1, e1_highf)
        out = self.Conv(d1_out)
        if self.training:
            pred = []
            for i in range(2,6):
                var_name = f"d{i}_out"  # 构造变量名
                if var_name in locals():  # 检查变量是否存在
                    tempout = locals()[var_name]
                    tempout = self.Conv_out[i-2](tempout)
                    pred.append(tempout)
            pred.append(out)
            # for i in range(len(pred)):
            #     print(pred[i].shape)
            return pred

        return out


from PepperPepper.layers import ChannelAttention
class IDWTConvPam(nn.Module):
    def __init__(self, in_channels, out_channels, wave='haar'):
        super(IDWTConvPam, self).__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.ChConv = up_conv(in_channels, out_channels)
        self.idwt = IDWTModule(wave)
        # self.catten = CAttion(out_channels)
        # self.Conv = conv_block(out_channels * 2, out_channels)
        self.layer = nn.Sequential(
            nn.Conv2d(out_channels * 2, out_channels, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU(),
        )
        self.ca = ChannelAttention(out_channels)
        self.PT = TransformerLayer(out_channels, num_layers=1, num_attention_heads=1)
        self.layerout = nn.Sequential(
            nn.Conv2d(out_channels, out_channels, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(out_channels),
            nn.LeakyReLU()
        )

    def forward(self, d, e, highf, PAM_feature):
        d = self.ChConv(d)
        dwt_features = torch.cat((d, torch.cat(highf, dim=1)), dim=1)
        d = self.idwt(dwt_features)
        d = torch.cat((e, d), dim=1)
        d = self.layer(d)

        B, C, H, W = d.shape
        patch_prob = F.interpolate(PAM_feature, size=(H, W))
        d = d * patch_prob.detach().sigmoid()
        d = self.ca(d)
        d = self.PT(d, PAM_feature)
        out = self.layerout(d)
        return out
class TransformerLayer(nn.Module):
    def  __init__(self, qkv_dims=32, num_layers=4, num_attention_heads = 1):
        super().__init__()
        self.qkv_dims = qkv_dims
        self.num_layers = num_layers
        self.num_attention_heads = num_attention_heads
        self.layers = nn.ModuleList()

        for _ in range(num_layers):
            layer = PatchAttention(qkv_dims, num_attention_heads)
            self.layers.append(layer)

    def forward(self, e, PAM_out):
        batch_size, _, height_num, width_num = PAM_out.shape
        mask = (PAM_out[:, 0] > 0).view(batch_size, -1)  # 展开为 [B, num_blocks]
        B, C, H, W = e.shape

        # 校验输入合法性
        assert batch_size == B, "Batch size不匹配"
        assert H % height_num == 0, "特征图高度必须能被PAM输出高度整除"
        assert W % width_num == 0, "特征图宽度必须能被PAM输出宽度整除"

        # 分块处理
        blocks = rearrange(e, 'b c (h_num h) (w_num w) -> b (h_num w_num) c h w', h_num=height_num, w_num=width_num)
        target_blocks = blocks[mask]

        for layer_block in self.layers:
            target_blocks = layer_block(target_blocks)

        blocks[mask] = target_blocks

        target_e = rearrange(blocks, 'b (h_num w_num) c h w -> b c (h_num h) (w_num w)', h_num=height_num,
                             w_num=width_num)

        return target_e
from PepperPepper.layers.PatchAwareModule import LayerNormC
class PatchAttention(nn.Module):
    def __init__(self, qkv_dims, num_attention_heads):
        super().__init__()
        self.KV_size = qkv_dims
        self.channel_num = qkv_dims
        self.num_attention_heads = num_attention_heads
        self.psi = nn.InstanceNorm2d(self.num_attention_heads)
        self.softmax = nn.Softmax(dim=3)

        self.mheadq = nn.Conv2d(self.KV_size, self.KV_size * self.num_attention_heads, kernel_size=1, bias=False)
        self.mheadk = nn.Conv2d(self.KV_size, self.KV_size * self.num_attention_heads, kernel_size=1, bias=False)
        self.mheadv = nn.Conv2d(self.KV_size, self.KV_size * self.num_attention_heads, kernel_size=1, bias=False)


        self.q = nn.Conv2d(self.KV_size * self.num_attention_heads, self.KV_size * self.num_attention_heads, kernel_size=3, stride=1,
                           padding=1, groups=self.KV_size * self.num_attention_heads, bias=False)
        self.k = nn.Conv2d(self.KV_size * self.num_attention_heads, self.KV_size * self.num_attention_heads, kernel_size=3, stride=1,
                           padding=1, groups=self.KV_size * self.num_attention_heads, bias=False)
        self.v = nn.Conv2d(self.KV_size * self.num_attention_heads, self.KV_size * self.num_attention_heads, kernel_size=3, stride=1,
                           padding=1, groups=self.KV_size * self.num_attention_heads, bias=False)


        self.project_out = nn.Conv2d(self.channel_num, self.channel_num, kernel_size=1, stride=1)
        self.attn_norm = LayerNormC(qkv_dims, LayerNorm_type='WithBias')


    def forward(self, emb_all):
        org = emb_all
        emb_all = self.attn_norm(emb_all)

        b, c, h, w = emb_all.shape

        q = self.q(self.mheadq(emb_all))
        k = self.k(self.mheadk(emb_all))
        v = self.v(self.mheadv(emb_all))

        q = rearrange(q, 'b (head c) h w -> b head (h w) c', head=self.num_attention_heads)
        k = rearrange(k, 'b (head c) h w -> b head (h w) c ', head=self.num_attention_heads)
        v = rearrange(v, 'b (head c) h w -> b head (h w) c ', head=self.num_attention_heads)

        q = torch.nn.functional.normalize(q, dim=-1)
        k = torch.nn.functional.normalize(k, dim=-1)
        _, _, num, _ = k.shape


        atten = (q @ k.transpose(-2, -1)) / math.sqrt(num)
        atten_probs = self.softmax(self.psi(atten))


        out = (atten_probs @ v)
        out = out.mean(dim=1)
        out = rearrange(out, 'b  (h w) c -> b c h w', h=h, w=w)
        out = self.project_out(out)
        cx = org + out
        org = cx
        return org
class WUNet_Pam(WUNet):
    def __init__(self, in_ch=1, out_ch=1, dim=32, wave='haar'):
        super().__init__(in_ch=1, out_ch=1, dim=32, wave='haar')
        self.PAM = PAM(dim, out_ch, feature_size=[256, 128, 64, 32, 16], num_layers=4)
        self.DConv4 = IDWTConvPam(self.filters[4], self.filters[3], wave)
        self.DConv3 = IDWTConvPam(self.filters[3], self.filters[2], wave)
        self.DConv2 = IDWTConvPam(self.filters[2], self.filters[1], wave)
        self.DConv1 = IDWTConvPam(self.filters[1], self.filters[0], wave)


    def forward(self, x):
        e1 = self.Conv1(x)
        e2, e1_highf = self.Conv2(e1)
        e3, e2_highf = self.Conv3(e2)
        e4, e3_highf = self.Conv4(e3)
        e5, e4_highf = self.Conv5(e4)
        d5_out = e5

        # 块感知模块，进行感知区域
        Fan_feature = [e1, e2, e3, e4, e5]
        PAM_feature = self.PAM(Fan_feature)

        d4_out = self.DConv4(d5_out, e4, e4_highf, PAM_feature)
        d3_out = self.DConv3(d4_out, e3, e3_highf, PAM_feature)
        d2_out = self.DConv2(d3_out, e2, e2_highf, PAM_feature)
        d1_out = self.DConv1(d2_out, e1, e1_highf, PAM_feature)
        out = self.Conv(d1_out)


        if self.training:
            pred = []
            for i in range(2,6):
                var_name = f"d{i}_out"  # 构造变量名
                if var_name in locals():  # 检查变量是否存在
                    tempout = locals()[var_name]
                    tempout = self.Conv_out[i-2](tempout)
                    pred.append(tempout)
            pred.append(out)
            return pred, PAM_feature
        return out, PAM_feature



if __name__ == '__main__':
    model = WUNet().cuda().eval()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')








