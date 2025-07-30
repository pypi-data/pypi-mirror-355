from PepperPepper.environment import torch, nn, F, profile



class MultiScaleSPWDilate(nn.Module):
    def __init__(self, dims=32, dilation_rates=[1, 3, 5]):
        super().__init__()

        self.branches  = nn.ModuleList([
            nn.Sequential(
                nn.Conv2d(dims, dims, kernel_size=3,
                         dilation=d, padding=d),
                nn.BatchNorm2d(dims),
                nn.GELU()
            ) for d in dilation_rates
        ])

        self.num = len(dilation_rates)

        self.synergy_weights = nn.Parameter(torch.randn(self.num) / self.num, requires_grad=True)
        self.independence_weights = nn.Parameter(torch.randn(self.num) / self.num, requires_grad=True)

        self.path_synergy_weights = nn.Parameter(torch.randn(2) / 2, requires_grad=True)


    def forward(self, x):

        f = []
        for branch in self.branches:
            f.append(branch(x))

        synergy_weights = torch.softmax(self.synergy_weights, dim=0)
        independence_weights = torch.sigmoid(self.independence_weights)
        path_synergy_weights = torch.softmax(self.path_synergy_weights, dim=0)

        synergy_f = 0
        independence_f = 0
        for i in range(len(f)):
            synergy_f += synergy_weights[i] * f[i]
            independence_f += independence_weights[i] * f[i]

        out = independence_f * path_synergy_weights[0] + synergy_f * path_synergy_weights[1] + x
        return out















class CrossScaleFeature(nn.Module):
    def __init__(self, base_dim=32):
        super().__init__()
        self.base_dim = base_dim


        self.conv3x3 = nn.Sequential(
            nn.Conv2d(base_dim, base_dim, 3, padding=1, groups=base_dim),
            nn.BatchNorm2d(base_dim),
            nn.GELU(),
        )

        self.conv5x5 = nn.Sequential(
            nn.Conv2d(base_dim, base_dim, 5, padding=2, groups=base_dim),
            nn.BatchNorm2d(base_dim),
            nn.GELU(),
        )

        self.conv7x7 = nn.Sequential(
            nn.Conv2d(base_dim, base_dim, 7, padding=3, groups=base_dim),
            nn.BatchNorm2d(base_dim),
            nn.GELU(),
        )


        self.weights = nn.Parameter(torch.randn(3)/3, requires_grad=True)

    def forward(self, x):
        residual = x
        feat3 = self.conv3x3(x)
        feat5 = self.conv5x5(x)
        feat7 = self.conv7x7(x)
        weights = F.softmax(self.weights, dim=0)
        fused_feat = weights[0] * feat3 + weights[1] * feat5 + weights[2] * feat7
        return fused_feat + residual



if __name__ == '__main__':
    net = MultiScaleSPWDilate(32)
    inputs = torch.rand(1, 32, 256, 256)
    output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')