from PepperPepper.environment import torch, nn, F, rearrange, math


class _FCNHead(torch.nn.Module):
    def __init__(self, in_channels, channels, norm_layer=torch.nn.BatchNorm2d):
        super(_FCNHead, self).__init__()
        self.block = torch.nn.Sequential()
        inter_channels = in_channels // 4
        self.block.append(torch.nn.Conv2d(in_channels=in_channels, out_channels=inter_channels, kernel_size=3, padding=1, bias=False))
        self.block.append(norm_layer(inter_channels))
        self.block.append(torch.nn.LeakyReLU(negative_slope=0.2))
        self.block.append(torch.nn.Dropout(0.1))
        self.block.append(torch.nn.Conv2d(in_channels=inter_channels, out_channels=channels, kernel_size=1))

    def forward(self, x):
        return self.block(x)



class Patch_embed(nn.Module):
    def __init__(self, in_channels, out_channels, patch_size, V='V1'):
        super().__init__()
        self.in_channels = in_channels
        self.patch_size = patch_size
        self.V = V
        self.out_channels = out_channels

        if patch_size == 0:
            self.V = 'V0'

        if self.V == 'V1' and self.is_power_of_two(patch_size):
            self.block = self._make_patch_embed_V1(in_channels, out_channels, patch_size)
        elif self.V == 'V0':
            self.block = self._make_patch_embed_V0(in_channels, out_channels, patch_size)
        else:
            self.block = self._make_patch_embed_last(in_channels, out_channels, patch_size)
            # raise ValueError(f"Unsupported version: {self.V}")



    def forward(self, x):
        y = self.block(x)
        return y

    def is_power_of_two(self, n):
        if n <= 1:
            return False
        log2_n = math.log2(n)
        return log2_n.is_integer()

    def check_divisible_by_power_of_two(self, n, k):
        divisor = 2 ** k

        if n % divisor != 0:
            raise ValueError(f"Error: {n} is not divisible by 2^{k}. Please try again.")

        return


    def _make_patch_embed_V1(self, in_channels, out_channels, patch_size):
        stage_num = int(math.log2(patch_size))
        dim = out_channels // stage_num

        block = []
        for d in range(stage_num):
            block.append(nn.Sequential(
                nn.Conv2d(in_channels * (d + 1) if d == 0 else dim * (d), dim * (d + 1) if d+1 != stage_num else out_channels, kernel_size=2, stride=2),
                Permute(0, 2, 3, 1),
                nn.LayerNorm(dim * (d + 1) if d+1 != stage_num else out_channels),
                Permute(0, 3, 1, 2),
                (nn.GELU() if d+1 != stage_num else nn.Identity() )
            ))

        return nn.Sequential(*block)




    def _make_patch_embed_last(self, in_channels, channels, patch_size):
        block = nn.Sequential(
            nn.Conv2d(in_channels, channels, kernel_size=patch_size,stride=patch_size),
            Permute(0, 2, 3, 1),
            nn.LayerNorm(channels),
            Permute(0, 3, 1, 2),
            nn.GELU()
        )

        return block



    def _make_patch_embed_V0(self, in_channels, out_channels, patch_size):
        block = nn.Sequential(
            nn.Conv2d(in_channels, out_channels, kernel_size=1,stride=1),
            Permute(0, 2, 3, 1),
            nn.LayerNorm(out_channels),
            Permute(0, 3, 1, 2),
            nn.GELU()
        )

        return block






class Permute(nn.Module):
    def __init__(self, *args):
        super().__init__()
        self.args = args

    def forward(self, x: torch.Tensor):
        return x.permute(*self.args)


class PatchExpand2D(nn.Module):
    def __init__(self, in_channels, out_channels, dim_scale=2):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.dim_scale = dim_scale
        self.expand = nn.Linear(in_channels, dim_scale*dim_scale*self.out_channels, bias=False)
        self.norm = nn.LayerNorm(out_channels)

    def forward(self, x):#(b,h,w,c)->(b,h,w,2c)->(b,2h,2w,c/2)
        B, H, W, C = x.shape
        # x=x.permute(0,2,3,1)
        # B, H, W, C = x.shape
        x = self.expand(x)

        x = rearrange(x, 'b h w (p1 p2 c)-> b (h p1) (w p2) c', p1=self.dim_scale, p2=self.dim_scale, c=self.out_channels)
        x= self.norm(x)


        return x



