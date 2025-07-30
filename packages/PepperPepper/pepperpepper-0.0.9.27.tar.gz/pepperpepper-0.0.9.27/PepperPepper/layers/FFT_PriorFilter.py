from PepperPepper.environment import nn, torch, rearrange


class FFT_PriorFilter(nn.Module):
    def __init__(self, in_channels , windows_size):
        super().__init__()
        self.dim = in_channels
        self.windows_size = windows_size
        self.cond = nn.Parameter(torch.randn(self.windows_size, self.windows_size // 2 + 1, self.dim, 2, dtype=(torch.float32)) * 0.02)


    def forward(self, x):
        B, C, H, W = x.size()
        assert H % self.windows_size == 0 and W % self.windows_size == 0, 'windows_size must be divisible by windows_size'
        x = rearrange(x, 'b c (h p1) (w p2) -> (b h w) p1 p2 c', p1=self.windows_size, p2=self.windows_size)

        X = torch.fft.rfft2(x, dim=(1, 2), norm='ortho')
        cond = torch.view_as_complex(self.cond)

        X = X * cond

        x = torch.fft.irfft2(X, s=(self.windows_size, self.windows_size), dim=(1, 2), norm='ortho')
        x = rearrange(x, '(b h w) p1 p2 c -> b c (h p1) (w p2)', h=H // self.windows_size, w=W // self.windows_size)

        return x


