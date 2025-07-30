from PepperPepper.IRSTD.tools.metrics import SegmentationMetricTPFNFP
from PepperPepper.environment import nn, torch, profile, math, trunc_normal_, DropPath, rearrange, repeat, checkpoint, partial, Callable, F
from PepperPepper.layers.custom_layer import Permute
from PepperPepper.layers import VSSBlock, extractembedding, Global_Context_Mamba_Bridge, Coopetition_Fuse, ResidualBlock


class PatchEmbed2D(nn.Module):
    r""" Image to Patch Embedding
    Args:
        patch_size (int): Patch token size. Default: 4.
        in_chans (int): Number of input image channels. Default: 3.
        embed_dim (int): Number of linear projection output channels. Default: 96.
        norm_layer (nn.Module, optional): Normalization layer. Default: None
    """
    def __init__(self, patch_size=4, in_chans=3, embed_dim=96, norm_layer=None, **kwargs):
        super().__init__()
        if isinstance(patch_size, int):
            patch_size = (patch_size, patch_size)
        self.proj = nn.Conv2d(in_chans, embed_dim, kernel_size=patch_size, stride=patch_size)
        if norm_layer is not None:
            self.norm = norm_layer(embed_dim)
        else:
            self.norm = None

    def forward(self, x):
        x = self.proj(x).permute(0, 2, 3, 1)
        if self.norm is not None:
            x = self.norm(x)
        return x


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

    def forward(self, x):
        B, H, W, C = x.shape
        x = self.expand(x)

        x = rearrange(x, 'b h w (p1 p2 c)-> b (h p1) (w p2) c', p1=self.dim_scale, p2=self.dim_scale, c=C//self.dim_scale)
        x= self.norm(x)

        return x

class Final_PatchExpand2D(nn.Module):
    def __init__(self, dim, dim_scale=2, norm_layer=nn.LayerNorm):
        super().__init__()
        self.dim = dim
        self.dim_scale = dim_scale
        self.expand = nn.Linear(self.dim, self.dim_scale * self.dim_scale * dim//2, bias=False)
        self.norm = norm_layer(self.dim // 2)

    def forward(self, x):
        B, H, W, C = x.shape
        x = self.expand(x)

        x = rearrange(x, 'b h w (p1 p2 c)-> b (h p1) (w p2) c', p1=self.dim_scale, p2=self.dim_scale, c=C // 2)
        x= self.norm(x)

        return x



class VSSLayer(nn.Module):
    """ A basic Swin Transformer layer for one stage.
    Args:
        dim (int): Number of input channels.
        depth (int): Number of blocks.
        drop (float, optional): Dropout rate. Default: 0.0
        attn_drop (float, optional): Attention dropout rate. Default: 0.0
        drop_path (float | tuple[float], optional): Stochastic depth rate. Default: 0.0
        norm_layer (nn.Module, optional): Normalization layer. Default: nn.LayerNorm
        downsample (nn.Module | None, optional): Downsample layer at the end of the layer. Default: None
        use_checkpoint (bool): Whether to use checkpointing to save memory. Default: False.
    """

    def __init__(
            self,
            dim,
            depth,
            attn_drop=0.,
            drop_path=0.,
            norm_layer=nn.LayerNorm,
            downsample=None,
            use_checkpoint=False,
            d_state=16,
            **kwargs,
    ):
        super().__init__()
        self.dim = dim
        self.use_checkpoint = use_checkpoint

        self.blocks = nn.ModuleList([
            VSSBlock(
                hidden_dim=dim,
                drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path,
                norm_layer=norm_layer,
                attn_drop_rate=attn_drop,
                d_state=d_state,
            )
            for i in range(depth)])

        if True:  # is this really applied? Yes, but been overriden later in VSSM!
            def _init_weights(module: nn.Module):
                for name, p in module.named_parameters():
                    if name in ["out_proj.weight"]:
                        p = p.clone().detach_()  # fake init, just to keep the seed ....
                        nn.init.kaiming_uniform_(p, a=math.sqrt(5))

            self.apply(_init_weights)

        if downsample is not None:
            self.downsample = downsample(dim=dim // 2, norm_layer=norm_layer)
        else:
            self.downsample = None

    def forward(self, x):
        if self.downsample is not None:
            x = self.downsample(x)

        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)

        return x


class VSSLayer_up(nn.Module):
    """ A basic Swin Transformer layer for one stage.
    Args:
        dim (int): Number of input channels.
        depth (int): Number of blocks.
        drop (float, optional): Dropout rate. Default: 0.0
        attn_drop (float, optional): Attention dropout rate. Default: 0.0
        drop_path (float | tuple[float], optional): Stochastic depth rate. Default: 0.0
        norm_layer (nn.Module, optional): Normalization layer. Default: nn.LayerNorm
        downsample (nn.Module | None, optional): Downsample layer at the end of the layer. Default: None
        use_checkpoint (bool): Whether to use checkpointing to save memory. Default: False.
    """

    def __init__(
            self,
            dim,
            depth,
            attn_drop=0.,
            drop_path=0.,
            norm_layer=nn.LayerNorm,
            upsample=None,
            use_checkpoint=False,
            d_state=16,
            **kwargs,
    ):
        super().__init__()
        self.dim = dim
        self.use_checkpoint = use_checkpoint

        self.blocks = nn.ModuleList([
            VSSBlock(
                hidden_dim=dim,
                drop_path=drop_path[i] if isinstance(drop_path, list) else drop_path,
                norm_layer=norm_layer,
                attn_drop_rate=attn_drop,
                d_state=d_state,
            )
            for i in range(depth)])

        if True:  # is this really applied? Yes, but been overriden later in VSSM!
            def _init_weights(module: nn.Module):
                for name, p in module.named_parameters():
                    if name in ["out_proj.weight"]:
                        p = p.clone().detach_()  # fake init, just to keep the seed ....
                        nn.init.kaiming_uniform_(p, a=math.sqrt(5))

            self.apply(_init_weights)

        if upsample is not None:
            self.upsample = upsample(dim=dim, norm_layer=norm_layer)
        else:
            self.upsample = None

    def forward(self, x):
        if self.upsample is not None:
            x = self.upsample(x)
        for blk in self.blocks:
            if self.use_checkpoint:
                x = checkpoint.checkpoint(blk, x)
            else:
                x = blk(x)
        return x


class VSSM(nn.Module):
    def __init__(self, patch_size=4, in_chans=3, num_classes=1, depths=[2, 2, 2, 2], depths_decoder=[2, 2, 2],
                 dims=[64, 128, 256, 512], dims_decoder=[256, 128, 64, 32], d_state=16, drop_rate=0., attn_drop_rate=0.,
                 drop_path_rate=0.1,
                 norm_layer=nn.LayerNorm, patch_norm=True,
                 use_checkpoint=False, **kwargs):
        super().__init__()
        self.num_classes = num_classes
        self.num_layers = len(depths)
        self.num_uplayers = len(depths_decoder)
        if isinstance(dims, int):
            dims = [int(dims * 2 ** i_layer) for i_layer in range(self.num_layers)]
        self.embed_dim = dims[0]
        self.num_features = dims[-1]
        self.dims = dims

        self.embed_extract = extractembedding(in_chans, self.embed_dim//2)

        self.patch_embed = PatchEmbed2D(patch_size=patch_size, in_chans=self.embed_dim//2, embed_dim=self.embed_dim,
                                        norm_layer=norm_layer if patch_norm else None)

        self.skipequalpix = ResidualBlock(self.embed_dim//2, self.embed_dim//2)
        self.CPF = Coopetition_Fuse(2)
        self.CPF1 = Coopetition_Fuse(2)
        self.CPF2 = Coopetition_Fuse(2)
        self.CPF3 = Coopetition_Fuse(2)

        # WASTED absolute position embedding ======================
        self.pos_drop = nn.Dropout(p=drop_rate)

        dpr = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths))]  # stochastic depth decay rule
        dpr_decoder = [x.item() for x in torch.linspace(0, drop_path_rate, sum(depths_decoder))][::-1]

        self.GCMB = Global_Context_Mamba_Bridge(img_size=256, patch_size=4, depths=dims[:-1])

        self.layers = nn.ModuleList()
        for i_layer in range(self.num_layers):
            layer = VSSLayer(
                dim=dims[i_layer],
                depth=depths[i_layer],
                d_state=math.ceil(dims[0] / 6) if d_state is None else d_state,  # 20240109
                drop=drop_rate,
                attn_drop=attn_drop_rate,
                drop_path=dpr[sum(depths[:i_layer]):sum(depths[:i_layer + 1])],
                norm_layer=norm_layer,
                downsample=PatchMerging2D if (i_layer > 0) else None,
                use_checkpoint=use_checkpoint,
            )
            self.layers.append(layer)

        self.layers_up = nn.ModuleList()
        for i_layer in range(self.num_uplayers):
            layer = VSSLayer_up(
                dim=dims_decoder[i_layer],
                depth=depths_decoder[i_layer],
                d_state=math.ceil(dims[0] / 6) if d_state is None else d_state,  # 20240109
                drop=drop_rate,
                attn_drop=attn_drop_rate,
                drop_path=dpr_decoder[sum(depths_decoder[:i_layer]):sum(depths_decoder[:i_layer + 1])],
                norm_layer=norm_layer,
                upsample=PatchExpand2D , # if (i_layer < len(self.num_layers) -1 ) else None,
                use_checkpoint=use_checkpoint,
            )
            self.layers_up.append(layer)

        self.final_up = Final_PatchExpand2D(dim=dims_decoder[-2], dim_scale=4, norm_layer=norm_layer)
        self.final_conv = nn.Conv2d(dims_decoder[-1], num_classes, 1)
        self.integral_conv = nn.Conv2d(5, num_classes, 1)

        self.out_up = nn.ModuleList()
        for i_layer in range(len(self.dims)):
            self.out_up.append(nn.Sequential(
                Final_PatchExpand2D(dim=self.dims[i_layer], dim_scale=2, norm_layer=norm_layer),
                Permute(0, 3, 1, 2),
                nn.Conv2d(self.dims[i_layer] // 2, num_classes, 1)
            ))

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

    @torch.jit.ignore
    def no_weight_decay(self):
        return {'absolute_pos_embed'}

    @torch.jit.ignore
    def no_weight_decay_keywords(self):
        return {'relative_position_bias_table'}


    def forward_outlist(self, out_list):
        pre_list = []
        for inx, out in enumerate(self.out_up):
            # print(out_list[inx].shape)
            # pre = F.interpolate(pre, scale_factor=2 ** (inx + 1), mode='bilinear',align_corners=True)

            # pre = rearrange(out_list[inx], 'b h w c-> b c h w')
            # pre = F.interpolate(pre, scale_factor=2 ** (inx + 1), mode='bilinear',align_corners=True)
            # pre = rearrange(pre, 'b c h w-> b h w c')
            # pre = self.out_up[inx](pre)

            pre = self.out_up[inx](out_list[inx])
            pre = F.interpolate(pre, scale_factor=2 ** (inx + 1), mode='bilinear',align_corners=True)

            # print(pre.shape)
            pre_list.append(pre)

        return pre_list

    def forward(self, x):
        x1 = self.embed_extract(x)    # B x 32 x 256 x 256
        x2 = self.patch_embed(x1)    # B x 64 x 64 x 64
        x2 = self.pos_drop(x2)
        x2 = self.layers[0](x2)      # B x 64 x 64 x 64

        # x1 = x1.permute(0, 2, 3, 1)

        x3 = self.layers[1](x2)      # B x 32 x 32 x 128

        x4 = self.layers[2](x3)      # B x 16 x 16 x 256

        d5 = self.layers[3](x4)      # B x 8 x 8 x 512


        #  CCT
        f1 = x1
        f2 = rearrange(x2, 'b h w c -> b c h w')
        f3 = rearrange(x3, 'b h w c -> b c h w')
        f4 = rearrange(x4, 'b h w c -> b c h w')

        # print(f1.shape)
        # print(f2.shape)
        # print(f3.shape)
        # print(f4.shape)
        # print(d5.shape)


        f2, f3, f4 =self.GCMB([f2, f3, f4])


        f1 = self.skipequalpix(f1)
        f1 = rearrange(f1, 'b c h w -> b h w c')
        f2 = rearrange(f2, 'b c h w -> b h w c')
        f3 = rearrange(f3, 'b c h w -> b h w c')
        f4 = rearrange(f4, 'b c h w -> b h w c')


        d4 = self.layers_up[0](d5)      # B x 32 x 32 x 256
        d4 = self.CPF1([d4, f4])
        d3 = self.layers_up[1](d4) # B x 64 x 64 x 128
        d3 = self.CPF2([d3, f3])
        d2 = self.layers_up[2](d3) # B x 128 x 128 x 64
        d2 = self.CPF3([d2 , f2])

        pre_out = self.final_up(d2)
        d1 = self.CPF([f1, pre_out])


        out_up = [d2, d3, d4, d5]

        out_up = self.forward_outlist(out_up)

        # for i in range(len(out_up)):
        #     print(out_up[i].shape)

        out = rearrange(d1, 'b h w c -> b c h w')


        out = self.final_conv(out)

        out_up.append(out)

        allout = torch.cat(out_up, dim=1)
        allout = self.integral_conv(allout)
        out_up.append(allout)
        out_up.append(out)

        return out_up





class VMUNet(nn.Module):
    def __init__(self,
                 input_channels=3,
                 num_classes=1,
                 depths=[2, 2, 2, 2],
                 depths_decoder=[2, 2, 2],
                 drop_path_rate=0.2,
                 ):
        super().__init__()
        self.num_classes = num_classes
        self.vmunet = VSSM(in_chans=input_channels,
                           num_classes=num_classes,
                           depths=depths,
                           depths_decoder=depths_decoder,
                           drop_path_rate=drop_path_rate)

        self.title ='train_EE_GCMB_CPF_finalconv'

    def forward(self, x):
        if x.size()[1] == 1:
            x = x.repeat(1 ,3 ,1 ,1)
        pre_list = self.vmunet(x)

        # return pre_list

        if self.training:
            return pre_list[-1]
        else:
            return pre_list[-1]


if __name__ == '__main__':

    model = VMUNet(
        num_classes=1,
        input_channels=3,
        depths=[2, 2, 2, 2],
        depths_decoder=[2, 2, 2],
        drop_path_rate=0.2,
    ).cuda()

    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    flops, params = profile(model, (inputs,))

    # print(len(output))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')
