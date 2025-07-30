from PepperPepper.environment import torch, nn, F, profile, math, rearrange, Rearrange,trunc_normal_
from PepperPepper.layers import extractembedding, hybrid_downsampling, VSSLayer, _FCNHead, ResidualBlock, Coopetition_Fuse


class MambaPatchEmbed(nn.Module):
    def __init__(self,
                 in_chans=3,
                 embed_dim=96,
                 patch_size=4,
                 norm_layer=nn.BatchNorm2d):
        """
        适配MambaUNet的增强型图像分块嵌入模块
        参数：
            in_chans: 输入通道数 (默认3)
            embed_dim: 嵌入维度 (默认96)
            patch_size: 分块大小 (默认4)
            norm_layer: 标准化层 (默认BatchNorm2d)
        """
        super().__init__()
        self.patch_size = (patch_size, patch_size)

        # 多尺度兼容的卷积投影 (参考VM-UNet设计[8]())
        self.proj = nn.Sequential(
            nn.Conv2d(in_chans, embed_dim // 2, kernel_size=3,
                      stride=patch_size // 2, padding=1),
            norm_layer(embed_dim // 2),
            nn.GELU(),
            nn.Conv2d(embed_dim // 2, embed_dim,
                      kernel_size=patch_size//2,
                      stride=patch_size//2)
        )

        # 轻量化位置编码 (适配Mamba的序列处理[6]())
        self.pos_embed = nn.Parameter(
            torch.randn(1, embed_dim, 1, 1) * 0.02
        )

        # 通道注意力增强 (来自CM-UNet设计[6]())
        self.channel_att = nn.Sequential(
            nn.AdaptiveAvgPool2d(1),
            nn.Conv2d(embed_dim, embed_dim // 4, 1),
            nn.ReLU(),
            nn.Conv2d(embed_dim // 4, embed_dim, 1),
            nn.Sigmoid()
        )

    def forward(self, x):
        """输入形状: (B, C, H, W)"""
        # 分阶段卷积投影
        x = self.proj(x)  # (B, E, H/p, W/p)

        # 通道注意力增强
        att = self.channel_att(x)
        x = x * att

        # 轻量化位置编码
        x = x + self.pos_embed

        return x



class UpSample(nn.Module):
    def __init__(self, dim, depth, d_state, drop_path):
        super().__init__()
        if d_state==None:
            d_state = math.ceil(dim / 6) * 2


        self.up = nn.Upsample(scale_factor=2)
        self.proj = nn.Linear(dim * 2, dim)
        self.vss = VSSLayer(dim=dim, depth=depth, d_state=d_state, drop_path=drop_path)


    def forward(self, x, skip_x):
        up = self.up(x)
        up = rearrange(up, 'b c h w -> b h w c')
        up = self.proj(up)
        skip_x = rearrange(skip_x, 'b c h w -> b h w c')
        out = self.vss(up) + skip_x
        out = rearrange(out, 'b h w c -> b c h w')
        return out


        # self.embed_extract = extractembedding(in_dims, dim)
        # self.downlayer1 = self.make_downlayers(dim=dim * 1, depth= depth, d_state=None, drop_path=0.1)
        # self.downlayer2 = self.make_downlayers(dim=dim * 2, depth= depth, d_state=None, drop_path=0.1)
        # self.downlayer3 = self.make_downlayers(dim=dim * 4, depth= depth, d_state=None, drop_path=0.1)
        # self.downlayer4 = self.make_downlayers(dim=dim * 8, depth= depth, d_state=None, drop_path=0.1)
        #
        # self.uplayer3 = UpSample(dim=dim * 8, depth= depth, d_state=None, drop_path=0.1)
        # self.uplayer2 = UpSample(dim=dim * 4, depth= depth, d_state=None, drop_path=0.1)
        # self.uplayer1 = UpSample(dim=dim * 2, depth= depth, d_state=None, drop_path=0.1)
        # # self.uplayer0 = UpSample(dim=dim * 1, depth= depth, d_state=None, drop_path=0.1)
        #
        # self.up = nn.Upsample(scale_factor=2)
        # self.res = ResidualBlock(dim * 2, dim)
        #
        #
        # self.outc = nn.Conv2d(dim, num_classes, kernel_size=(1, 1), stride=(1, 1))

class PatchMerging2D(nn.Module):
    r""" Patch Merging Layer.
    Args:
        input_resolution (tuple[int]): Resolution of input feature.
        dim (int): Number of input channels.
        norm_layer (nn.Module, optional): Normalization layer.  Default: nn.LayerNorm
    """

    def __init__(self, dim, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.reduction = nn.Linear(4 * dim, 2 * dim, bias=False)
        self.norm = norm_layer(4 * dim)

    def forward(self, x):
        B, H, W, C = x.shape

        SHAPE_FIX = [-1, -1]
        if (W % 2 != 0) or (H % 2 != 0):
            print(f"Warning, x.shape {x.shape} is not match even ===========", flush=True)
            SHAPE_FIX[0] = H // 2
            SHAPE_FIX[1] = W // 2

        x0 = x[:, 0::2, 0::2, :]  # B H/2 W/2 C
        x1 = x[:, 1::2, 0::2, :]  # B H/2 W/2 C
        x2 = x[:, 0::2, 1::2, :]  # B H/2 W/2 C
        x3 = x[:, 1::2, 1::2, :]  # B H/2 W/2 C

        if SHAPE_FIX[0] > 0:
            x0 = x0[:, :SHAPE_FIX[0], :SHAPE_FIX[1], :]
            x1 = x1[:, :SHAPE_FIX[0], :SHAPE_FIX[1], :]
            x2 = x2[:, :SHAPE_FIX[0], :SHAPE_FIX[1], :]
            x3 = x3[:, :SHAPE_FIX[0], :SHAPE_FIX[1], :]

        x = torch.cat([x0, x1, x2, x3], -1)  # B H/2 W/2 4*C
        x = x.view(B, H // 2, W // 2, 4 * C)  # B H/2*W/2 4*C

        x = self.norm(x)
        x = self.reduction(x)

        return x


class PatchExpand2D(nn.Module):
    def __init__(self, dim, dim_scale=2, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim*2
        self.dim_scale = dim_scale
        self.expand = nn.Linear(self.dim, dim_scale*self.dim, bias=False)
        self.norm = norm_layer(self.dim // dim_scale)

    def forward(self, x):#(b,h,w,c)->(b,h,w,2c)->(b,2h,2w,c/2)
        B, H, W, C = x.shape
        x = self.expand(x)

        x = rearrange(x, 'b h w (p1 p2 c)-> b (h p1) (w p2) c', p1=self.dim_scale, p2=self.dim_scale, c=C//self.dim_scale)
        x= self.norm(x)

        return x






class CM2UNet(nn.Module):
    def __init__(self,
                 in_dims=3,
                 num_classes = 1,
                 patch_size=4,
                 dim=64,
                 depth=2
                 ):
        super().__init__()

        self.title = 'CM2UNet_EE_CPF'
        self.in_dims = in_dims
        self.num_classes = num_classes
        self.dim = dim


        self.EE = extractembedding(in_channels=in_dims, out_channels=dim//2)
        self.patchembedding = MambaPatchEmbed(in_chans=dim//2, embed_dim=dim, patch_size=patch_size, norm_layer=nn.BatchNorm2d)
        self.Downvss1 = self.make_Vsslayers(dim, depth)

        self.patchmerge2 = PatchMerging2D(dim)
        self.Downvss2 = self.make_Vsslayers(dim * 2, depth)


        self.patchmerge3 = PatchMerging2D(dim * 2)
        self.Downvss3 = self.make_Vsslayers(dim * 4, depth)


        self.patchmerge4 = PatchMerging2D(dim * 4)
        self.Downvss4 = self.make_Vsslayers(dim * 8, depth)

        self.patchmerge5 = PatchMerging2D(dim * 8)
        self.Downvss5 = self.make_Vsslayers(dim * 16, depth)

        self.patchexpand4 = PatchExpand2D(dim * 8)
        self.CPF4 = Coopetition_Fuse(2)
        self.Upvss4 = self.make_Vsslayers(dim * 8, depth)

        self.patchexpand3 = PatchExpand2D(dim * 4)
        self.CPF3 = Coopetition_Fuse(2)
        self.Upvss3 = self.make_Vsslayers(dim * 4, depth)

        self.patchexpand2 = PatchExpand2D(dim * 2)
        self.CPF2 = Coopetition_Fuse(2)
        self.Upvss2 = self.make_Vsslayers(dim * 2, depth)

        self.patchexpand1 = PatchExpand2D(dim * 1)
        self.CPF1 = Coopetition_Fuse(2)
        self.Upvss1 = self.make_Vsslayers(dim * 1, depth)

        self.final_proj = nn.Sequential(
            PatchExpand2D(dim//2, dim_scale=4),
            # PatchExpand2D(dim//4),
            Rearrange('b h w c -> b c h w'),
            # nn.Conv2d(dim//4, num_classes, kernel_size=1, stride=1)
        )
        # self.CPF0 = Coopetition_Fuse(2)

        self.skip_conv = ResidualBlock(dim//2, dim//4)

        self.outc = nn.Conv2d(dim//4, num_classes, kernel_size=1, stride=1)

        self.CSPOUT = Coopetition_Fuse(2)

        self.apply(self._init_weights)





    def _init_weights(self, m: nn.Module):
        """
        out_proj.weight which is previously initilized in VSSBlock, would be cleared in nn.Linear
        no fc.weight found in the any of the model parameters
        no nn.Embedding found in the any of the model parameters
        so the thing is, VSSBlock initialization is useless

        Conv2D is not intialized !!!
        """
        if isinstance(m, nn.Linear):
            trunc_normal_(m.weight, std=.02)
            if isinstance(m, nn.Linear) and m.bias is not None:
                nn.init.constant_(m.bias, 0)
        elif isinstance(m, nn.LayerNorm):
            nn.init.constant_(m.bias, 0)
            nn.init.constant_(m.weight, 1.0)





    def forward(self, x):
        # check the dims
        if x.size()[1] == 1:
            x = x.repeat(1, self.in_dims, 1, 1)

        x = self.EE(x)
        f1 = self.patchembedding(x)
        f1 = rearrange(f1, 'b c h w -> b h w c')
        f1 = self.Downvss1(f1)

        f2 = self.patchmerge2(f1)
        f2 = self.Downvss2(f2)

        f3 = self.patchmerge3(f2)
        f3 = self.Downvss3(f3)

        f4 = self.patchmerge4(f3)
        f4 = self.Downvss4(f4)

        f5 = self.patchmerge5(f4)
        f5 = self.Downvss5(f5)

        d4 = self.patchexpand4(f5)

        d4 = self.Upvss4(self.CPF4([d4, f4]))

        d3 = self.patchexpand3(d4)
        d3 = self.Upvss3(self.CPF3([d3, f3]))

        d2 = self.patchexpand2(d3)
        d2 = self.Upvss2(self.CPF2([d2, f2]))

        d1 = self.patchexpand1(d2)
        d1 = self.Upvss1(self.CPF1([d1, f1]))


        out = self.final_proj(d1)
        x = self.skip_conv(x)
        out = self.CSPOUT([out, x])

        outc = self.outc(out)

        return outc


    def make_Vsslayers(self, dim, depth, d_state=None, drop_path=0.0):
        if d_state is None:
            d_state = math.ceil(dim / 6)

        blocks = nn.Sequential(
            VSSLayer(dim=dim, depth=depth, d_state=d_state, drop_path=drop_path),
        )

        return blocks




if __name__ == '__main__':
    model = CM2UNet().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    print(output.shape)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')