from PepperPepper.environment import torch, nn, F, profile, math, rearrange, Rearrange,trunc_normal_
from PepperPepper.layers import extractembedding, hybrid_downsampling, VSSLayer, _FCNHead, ResidualBlock, Coopetition_Fuse, IRGradOri



class CM2UNetV2(nn.Module):
    def __init__(self,
                 # img_size=256,
                 in_dims=3,
                 num_classes = 1,
                 dim=32,
                 depth=1
                 ):
        super().__init__()
        self.title = 'CM2UNetV2'
        self.in_dims = in_dims
        self.num_classes = num_classes
        self.dim = dim
        self.depth = depth

        self.stem = extractembedding(in_dims, dim)
        self.pool = nn.MaxPool2d(2, 2)
        self.up = nn.Upsample(scale_factor=2)
        self.downlayer1 = extractembedding(dim, dim * 2)
        self.downlayer2 = self._make_Downlayer(dim*2, dim*4, depth=depth, d_state=16, drop_path=0.1)
        self.downlayer3 = self._make_Downlayer(dim*4, dim*8, depth=depth, d_state=16, drop_path=0.1)
        self.uplayer2 = self._make_Upsample(dim*4, dim*4, depth=depth, d_state=16, drop_path=0.1)
        self.uplayer1 = self._make_Upsample(dim*2, dim*2, depth=depth, d_state=16, drop_path=0.1)
        self.uplayer0 = ResidualBlock(dim, num_classes)

        self.track2 = nn.Conv2d(dim*8, dim*4, kernel_size=1)
        self.track1 = nn.Conv2d(dim*4, dim*2, kernel_size=1)
        self.track0 = nn.Conv2d(dim*2, dim, kernel_size=1)
        self.CPF2 = Coopetition_Fuse(2)
        self.CPF1 = Coopetition_Fuse(2)
        self.CPF0 = Coopetition_Fuse(2)





        self.outc = _FCNHead(dim, num_classes)

    def _make_Downlayer(self, in_dim, out_dim, depth, d_state, drop_path):
        block = nn.Sequential(
            extractembedding(in_dim, out_dim),
            Rearrange('b c h w -> b h w c'),
            VSSLayer(out_dim, depth=depth, d_state=d_state, drop_path=drop_path),
            Rearrange('b h w c -> b c h w'),
        )
        return block

    def _make_Upsample(self, in_dim, out_dim, depth, d_state, drop_path):
        block = nn.Sequential(
            extractembedding(in_dim, out_dim),
            Rearrange('b c h w -> b h w c'),
            VSSLayer(out_dim, depth=depth, d_state=d_state, drop_path=drop_path),
            Rearrange('b h w c -> b c h w'),
        )
        return block




    def forward(self, x):
        # check the dims
        if x.size()[1] == 1:
            x = x.repeat(1, self.in_dims, 1, 1)

        f0 = self.stem(x)
        f1 = self.downlayer1(self.pool(f0))
        f2 = self.downlayer2(self.pool(f1))
        f3 = self.downlayer3(self.pool(f2))


        d2 = self.uplayer2(self.CPF2([self.track2(self.up(f3)), f2]))
        d1 = self.uplayer1(self.CPF1([self.track1(self.up(d2)), f1]))
        d0 = self.uplayer0(self.CPF0([self.track0(self.up(d1)), f0]))
        return d0



if __name__ == '__main__':
    model = CM2UNetV2().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    print(output.shape)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')