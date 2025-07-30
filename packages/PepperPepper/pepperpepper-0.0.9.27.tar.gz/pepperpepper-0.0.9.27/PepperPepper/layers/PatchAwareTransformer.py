import torch
import torch.nn as nn
import torch.nn.functional as F
from thop import profile
from torch.nn.modules.utils import _pair
from einops import rearrange
import numbers
import math


class Channel_Embeddings(nn.Module):
    def __init__(self, patchsize, in_channels):
        super(Channel_Embeddings, self).__init__()
        patch_size = _pair(patchsize)

        self.proj = nn.Sequential(
            nn.Conv2d(in_channels, in_channels//4, kernel_size=1, stride=1),
            nn.BatchNorm2d(in_channels//4),
            nn.LeakyReLU()
        )


        self.patch_embeddings = nn.Conv2d(in_channels=in_channels//4,
                                        out_channels=in_channels//4,
                                        kernel_size=patch_size,
                                        stride=patch_size)


    def forward(self, x):
        if x is None :
            return None
        x = self.proj(x)
        x = self.patch_embeddings(x)
        return x






def to_3d(x):
    return rearrange(x, 'b c h w -> b (h w) c')


def to_4d(x, h, w):
    return rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)




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
        # self.ffn_norm = LayerNormC(channel_num, LayerNorm_type='WithBias')

    def forward(self, emb_all):
        org = emb_all
        emb_all = self.attn_norm(emb_all)
        b , c, h, w = emb_all.shape
        q = self.q(self.mheadq(emb_all))
        k = self.k(self.mheadk(emb_all))
        v = self.v(self.mheadv(emb_all))


        q = rearrange(q, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)
        k = rearrange(k, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)
        v = rearrange(v, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)


        # print(q.shape, k.shape, v.shape)
        q = torch.nn.functional.normalize(q, dim=-1)
        k = torch.nn.functional.normalize(k, dim=-1)
        _, _, c, _ = k.shape

        atten = (q @ k.transpose(-2, -1)) / math.sqrt(c)
        atten_probs = self.softmax(self.psi(atten))

        out = (atten_probs @ v)
        out = out.mean(dim=1)
        out = rearrange(out, 'b  c (h w) -> b c h w', h=h, w=w)
        out = self.project_out(out)

        cx = org + out
        org = cx

        # x = self.ffn_norm(cx)
        # print(cx.shape)

        return org











class Encoder(nn.Module):
    def __init__(self, num_layers=4, channel_num=[32, 64, 128, 256]):
        super(Encoder, self).__init__()
        self.num_layers = num_layers
        self.channel_num = channel_num
        self.layer = nn.ModuleList()
        self.allC_size = sum(channel_num)
        qkv_dim = sum(channel_num)
        

        for _ in range(num_layers):
            layer = SelfAttention(qkv_dim)
            self.layer.append(layer)


    def forward(self, emb1, emb2, emb3, emb4):
        emb_all = torch.cat((emb1, emb2, emb3, emb4), dim=1)
        for layer_block in self.layer:
            emb_all = layer_block(emb_all)

        return emb_all




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







class PatchAwareTransformer(nn.Module):
    def __init__(self, channel_num=[128, 256, 512, 1024], patchSize=[8, 4, 2, 1]):
        super().__init__()
        self.patchSize_1 = patchSize[0]
        self.patchSize_2 = patchSize[1]
        self.patchSize_3 = patchSize[2]
        self.patchSize_4 = patchSize[3]

        self.embeddings_1 = Channel_Embeddings(self.patchSize_1, in_channels=channel_num[0])
        self.embeddings_2 = Channel_Embeddings(self.patchSize_2, in_channels=channel_num[1])
        self.embeddings_3 = Channel_Embeddings(self.patchSize_3, in_channels=channel_num[2])
        self.embeddings_4 = Channel_Embeddings(self.patchSize_4, in_channels=channel_num[3])
        self.encoder = Encoder(num_layers=4)


    def forward(self, en1, en2, en3, en4):
        emb1 = self.embeddings_1(en1)
        emb2 = self.embeddings_2(en2)
        emb3 = self.embeddings_3(en3)
        emb4 = self.embeddings_4(en4)
        encoder = self.encoder(emb1, emb2, emb3, emb4)
        return encoder







if __name__ == '__main__':
    model = PatchAwareTransformer().cuda()
    # model = U_Net().cuda()
    en1 = torch.rand(1, 128, 128, 128).cuda()
    en2 = torch.rand(1, 256, 64, 64).cuda()
    en3 = torch.rand(1, 512, 32, 32).cuda()
    en4 = torch.rand(1, 1024, 16, 16).cuda()
    # output = model(inputs)
    # print(output.shape)
    flops, params = profile(model, (en1, en2, en3, en4))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')























































































