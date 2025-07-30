from PepperPepper.environment import torch, nn, F, profile, math, rearrange, Rearrange
from PepperPepper.layers import Patch_embed, VSSLayer, PatchExpand2D

'''
Global Context Mamba Bridge (GCMB) Block
在Mamba-UNet中整合多分辨率特征的模块可命名为 Cross-Scale Mamba Fusion (CSMF)，具体设计如下：

CSMF模块技术方案
核心设计理念:
双向跨尺度交互：通过Mamba的状态空间模型实现高低分辨率特征的双向信息流动
动态权重竞争：引入可学习参数实现特征的自适应重要性分配
轻量化序列重组：利用Mamba的线性计算复杂度保持效率

'''

class Global_Context_Mamba_Bridge(nn.Module):
    def __init__(self, img_size=256, patch_size=4, depths=[64, 128, 256]):
        super().__init__()
        self.img_size = img_size
        self.patch_size = patch_size
        self.depths = depths
        self.base_size = img_size // (patch_size * 2**(len(depths) - 1))

        self.downsample = nn.ModuleList()
        self.upsample = nn.ModuleList()

        for i_layer in range(len(depths)):
            self.downsample.append(
                Patch_embed(depths[i_layer], depths[i_layer], patch_size = (2 ** (len(depths) - i_layer - 1)))
            )

        for i_layer in range(len(depths)):
            self.upsample.append(
                PatchExpand2D(sum(depths), depths[i_layer], dim_scale = (2 ** (len(depths) - i_layer - 1)))
            )

        # print(self.upsample)


        self.VSSlayer = VSSLayer(
            dim=sum(depths),
            depth = 2,
            d_state= math.ceil(sum(depths) / 6),
            drop = 0.2
        )




    def forward(self, x_list):
        flist = []
        assert len(x_list) == len(self.depths),'the lengths of x_list and self.depths must be equal.'
        for i in range(len(self.depths)):
            self.downsample[i](x_list[i])
            flist.append(self.downsample[i](x_list[i]))

        f_cat = torch.cat(flist, dim = 1)
        f_cat = rearrange(f_cat, 'b c h w -> b h w c').contiguous()


        GC = self.VSSlayer(f_cat)
        out_list = []
        for i in range(len(self.depths)):
            out_list.append(rearrange(self.upsample[i](GC),'b h w c -> b c h w'))

        return out_list








if __name__ == '__main__':
    net = Global_Context_Mamba_Bridge(256, 1, [32, 64, 128, 256]).cuda()
    # inputs = torch.rand(1, 32, 256, 256)
    inputs = [torch.rand(1, 32, 256, 256).cuda(), torch.rand(1, 64, 128, 128).cuda(), torch.rand(1, 128, 64, 64).cuda(), torch.rand(1, 256, 32, 32).cuda()]
    flops, params = profile(net, (inputs,))



    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')


