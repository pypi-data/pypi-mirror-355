import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile
from torch.nn.modules.utils import _pair
from einops import rearrange
import numbers
import math
from PepperPepper.layers import AlternateCat


class PatchEmbedding(nn.Module):
    def __init__(self, in_dim, out_dim, PatchSize):
        super().__init__()
        # self.dim = dim
        self.in_dim = in_dim
        self.out_dim = out_dim
        self.PatchSize = PatchSize
        self.body = nn.Sequential(
            nn.Conv2d(in_dim, out_dim , kernel_size=PatchSize, stride=PatchSize, bias=True),
            nn.BatchNorm2d(out_dim),
            nn.LeakyReLU(inplace=True),
        )


    def forward(self, x):
        out = self.body(x)
        return out


def to_3d(x):
    return rearrange(x, 'b c h w -> b (h w) c')


def to_4d(x, h, w):
    return rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)


class BiasFree_LayerNorm(nn.Module):
    def __init__(self, normalized_shape):
        super(BiasFree_LayerNorm, self).__init__()
        if isinstance(normalized_shape, numbers.Integral):
            normalized_shape = (normalized_shape,)
        normalized_shape = torch.Size(normalized_shape)

        assert len(normalized_shape) == 1

        self.weight = nn.Parameter(torch.ones(normalized_shape))
        self.normalized_shape = normalized_shape

    def forward(self, x):
        sigma = x.var(-1, keepdim=True, unbiased=False)
        return x / torch.sqrt(sigma + 1e-5) * self.weight


class WithBias_LayerNorm(nn.Module):
    def __init__(self, normalized_shape):
        super(WithBias_LayerNorm, self).__init__()
        if isinstance(normalized_shape, numbers.Integral):
            normalized_shape = (normalized_shape,)
        normalized_shape = torch.Size(normalized_shape)

        assert len(normalized_shape) == 1

        self.weight = nn.Parameter(torch.ones(normalized_shape))
        self.bias = nn.Parameter(torch.zeros(normalized_shape))
        self.normalized_shape = normalized_shape

    def forward(self, x):
        mu = x.mean(-1, keepdim=True)
        sigma = x.var(-1, keepdim=True, unbiased=False)
        return (x - mu) / torch.sqrt(sigma + 1e-5) * self.weight + self.bias


class LayerNormC(nn.Module):
    def __init__(self, dim, LayerNorm_type):
        super(LayerNormC, self).__init__()
        if LayerNorm_type == 'BiasFree':
            self.body = BiasFree_LayerNorm(dim)
        else:
            self.body = WithBias_LayerNorm(dim)


    def forward(self, x):
        h, w = x.shape[-2:]
        return to_4d(self.body(to_3d(x)), h, w)




class SelfAttention(nn.Module):
    def __init__(self, channel_num):
        super(SelfAttention, self).__init__()
        self.KV_size = channel_num
        self.channel_num = channel_num
        self.num_attention_heads = 1
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
        self.attn_norm = LayerNormC(channel_num, LayerNorm_type='WithBias')





    def forward(self, emb_all):
        org = emb_all
        emb_all = self.attn_norm(emb_all)
        b , c, h, w = emb_all.shape
        q = self.q(self.mheadq(emb_all))
        k = self.k(self.mheadk(emb_all))
        v = self.v(self.mheadv(emb_all))


        q = rearrange(q, 'b (head c) h w -> b head (h w) c', head=self.num_attention_heads)
        k = rearrange(k, 'b (head c) h w -> b head (h w) c ', head=self.num_attention_heads)
        v = rearrange(v, 'b (head c) h w -> b head (h w) c ', head=self.num_attention_heads)


        # print(q.shape, k.shape, v.shape)
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






class TransfomerEncoder(nn.Module):
    def __init__(self, qkv_dims=992, num_layers=4):
        super().__init__()
        self.qkv_dims = qkv_dims
        self.num_layers = num_layers
        self.layers = nn.ModuleList()

        for _ in range(num_layers):
            layer = SelfAttention(qkv_dims)
            self.layers.append(layer)


    def forward(self, x):
        for layer_block in self.layers:
            x = layer_block(x)
        return x



from PepperPepper.IRSTD.models.MTransNet import get_MNet_config, MNet
from PepperPepper.layers import SCConv
from PepperPepper.layers import AlternateCat, AttentionalCS

class global_localCA(nn.Module):
    def __init__(self, dim=32, reduction_ratio=2):
        super().__init__()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)




        # 双路径注意力机制
        self.share_mlp = nn.Sequential(
            nn.Linear(dim, dim // reduction_ratio),
            nn.LeakyReLU(inplace=True),
            nn.Linear(dim // reduction_ratio, dim)
        )

        self.sigmoid = nn.Sigmoid()
        # dim = 1, num = 3
        self.alcat = AlternateCat(dim=1, num=2)
        self.proj = nn.Sequential(
            nn.Conv2d(dim * 2, dim, kernel_size=1, stride=1, padding=0, bias=True, groups=dim),
            nn.LeakyReLU(inplace=True),
        )




    def forward(self, e, Ctarget_max, Ctarget_avg):
        avg_pool = self.avg_pool(e).squeeze(-1).squeeze(-1)
        max_pool = self.max_pool(e).squeeze(-1).squeeze(-1)
        gl_avg_pool = Ctarget_avg - avg_pool
        gl_max_pool = (Ctarget_max == max_pool).float()
        gl_avgmax = self.alcat([gl_avg_pool, gl_max_pool]).unsqueeze(-1).unsqueeze(-1)
        gl_weight = self.share_mlp(self.proj(gl_avgmax).squeeze(-1).squeeze(-1))
        channel_weights = self.sigmoid(gl_weight + gl_weight).unsqueeze(-1).unsqueeze(-1)
        return e * channel_weights.expand_as(e)





class PAM_Processor(nn.Module):
    def __init__(self, dim=32, feature_size=[256, 128, 64, 32, 16]):
        super().__init__()
        self.dim = dim
        self.glCA = nn.ModuleList()
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)


        for i in range(len(feature_size)):
            self.glCA.append(global_localCA(dim*(2**i)))



    def forward(self, feature, PAM_out):
        batch_size, _, height_num, width_num = PAM_out.shape
        # print(PAM_out.shape)
        # 生成掩码
        mask = (PAM_out[:, 0] > 0).view(batch_size, -1)  # 展开为 [B, num_blocks]

        out = []
        for i in range(len(feature)):
            # feature_blocks = rearrange(feature[i], 'b c (h_num h) (w_num w) -> b c (h_num w_num) (h w)', h_num=height_num, w_num=width_num).contiguous()
            e = feature[i]
            B, C, H, W = e.shape

            # 校验输入合法性
            assert batch_size == B, "Batch size不匹配"
            assert H % height_num == 0, "特征图高度必须能被PAM输出高度整除"
            assert W % width_num == 0, "特征图宽度必须能被PAM输出宽度整除"

            # 分块处理
            blocks = rearrange(e, 'b c (h_num h) (w_num w) -> b (h_num w_num) c h w', h_num=height_num, w_num=width_num)
            target_blocks = blocks[mask]
            target_avg = self.avg_pool(target_blocks).squeeze(-1).squeeze(-1)
            target_max = self.max_pool(target_blocks).squeeze(-1).squeeze(-1)
            Btarget_max = torch.zeros(blocks.shape[:3]).to(blocks.device)
            Btarget_avg = torch.zeros(blocks.shape[:3]).to(blocks.device)

            Btarget_avg[mask] = target_avg
            Btarget_max[mask] = target_max

            Ctarget_max, _ = torch.max(Btarget_max, dim=1)
            Ctarget_avg = torch.sum(Btarget_avg, dim=1)
            mask_num = torch.sum(mask, dim=1, keepdim=True)
            flag_mask = (mask_num != 0)
            Ctarget_avg = torch.where(flag_mask, Ctarget_avg / mask_num, Ctarget_avg)
            e = self.glCA[i](e, Ctarget_max, Ctarget_avg)

            # target_blocks = torch.zeros_like(blocks)
            # target_blocks[mask] = blocks[mask]
            # target_e = rearrange(target_blocks, 'b (h_num w_num) c h w -> b c (h_num h) (w_num w)', h_num=height_num, w_num=width_num)
            # e = self.glCA[i](e, target_e)
            out.append(e)

        return out






class PAM(nn.Module):
    def __init__(self, dim=32, out_ch=1,feature_size=[256, 128, 64, 32, 16], num_layers=4):
        super().__init__()
        self.in_dim = dim * len(feature_size)
        self.dim = dim
        self.feature_size = feature_size
        PatchSize = feature_size[-1]
        self.PatchSize = feature_size[-1]
        self.PatchSizeLayers = []
        self.PatchEmbeddings = nn.ModuleList()
        self.qkv_dim = 0
        self.num_layers = num_layers

        for i,size in enumerate(feature_size):
            PS = size // PatchSize
            self.PatchSizeLayers.append(PS)
            self.PatchEmbeddings.append(PatchEmbedding(dim, dim, PS))
            self.qkv_dim += dim



        self.TransEncoder = TransfomerEncoder(qkv_dims=self.qkv_dim, num_layers=self.num_layers)


        self.Decoder = nn.Sequential(
            nn.Conv2d(in_channels=self.qkv_dim, out_channels=dim, kernel_size=1, stride=1),
            nn.BatchNorm2d(dim),
            nn.LeakyReLU()
        )


        self.PAM_out = nn.Conv2d(self.dim, out_ch, kernel_size=1, stride=1, padding=0)
        # self.PAM_Processor = PAM_Processor(dim=dim ,feature_size=feature_size)




    def forward(self,x):

        # 1.将多尺度的特征进行编码到Patch块的格式
        features = []
        for i, en in enumerate(x):
            f = self.PatchEmbeddings[i](en)
            features.append(f)
        features = torch.cat(features, dim=1)

        # 2.TransformerEncoder编码器
        features = self.TransEncoder(features)
        features = self.Decoder(features)
        out = self.PAM_out(features)
        return out, features



    # def PAMProcessor(self, feature, PAM_out):
    #     processed_F = self.PAM_Processor(feature, PAM_out)
    #     return processed_F



from thop import profile



if __name__ == '__main__':
    model = PAM().cuda()
    # en0 = torch.rand(1, 32, 256, 256).cuda()
    # en1 = torch.rand(1, 64, 128, 128).cuda()torch.ones(2, 256, 32, 32).cuda()
    # en2 = torch.rand(1, 128, 64, 64).cuda()
    # en3 = torch.rand(1, 256, 32, 32).cuda()
    # en4 = torch.rand(1, 512, 16, 16).cuda()
    #
    # en = [en0, en1, en2, en3, en4]

    feature = [torch.ones(1, 32, 256, 256).cuda(), torch.ones(1, 64, 128, 128).cuda(), torch.ones(1, 128, 64, 64).cuda(), torch.ones(1, 256, 32, 32).cuda(), torch.ones(1, 512, 16, 16).cuda()]
    PAM_out = torch.randn(1, 1, 16, 16).cuda()

    flops, params = profile(model.PAM_Processor, (feature, PAM_out))
    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')









