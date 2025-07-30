from PepperPepper.environment import torch, nn, F, profile
from PepperPepper.layers import extractembedding, ResidualBlock, _FCNHead


class EXEM(nn.Module):
    def __init__(self, input_channels=3, num_classes=1, dim = 32):
        super(EXEM, self).__init__()
        self.input_channels = input_channels
        self.num_classes = num_classes

        self.EE = extractembedding(in_channels=input_channels, out_channels=dim)

        self.Res = ResidualBlock(dim, out_channels=dim)

        self.outc = _FCNHead(dim, num_classes)

        self.title = 'EXEM_Grad'


    def forward(self, x):
        if x.size()[1] == 1:
            x = x.repeat(1, 3, 1, 1)
        x = self.EE(x)
        x = self.Res(x)
        x = self.outc(x)
        return x



if __name__ == '__main__':
    model = EXEM().cuda()
    inputs = torch.rand(1, 1, 256, 256).cuda()
    output = model(inputs)
    print(output.shape)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')

