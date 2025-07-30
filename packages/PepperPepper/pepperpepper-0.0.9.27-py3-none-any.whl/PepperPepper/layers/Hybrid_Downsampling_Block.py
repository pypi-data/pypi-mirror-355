from PepperPepper.environment import torch, nn, profile
from PepperPepper.layers import AlternateCat



class hybrid_downsampling(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.dim = dim
        self.pool = nn.MaxPool2d(2, 2)
        self.depthcnv = nn.Sequential(
            nn.Conv2d(in_channels=dim, out_channels=dim, kernel_size=3, stride=2, padding=1, groups=dim),
            nn.BatchNorm2d(dim),
            nn.LeakyReLU(),
        )
        self.AC = AlternateCat(dim=1)
        self.norm = nn.BatchNorm2d(dim)



    def forward(self, x):
        f1 = self.depthcnv(x)
        f2 = self.pool(x)

        fa = self.AC(f1, f2)

        return fa

if __name__ == '__main__':
    net = hybrid_downsampling(3)
    inputs = torch.rand(1, 3, 256, 256)
    output = net(inputs)
    print(output.shape)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')


