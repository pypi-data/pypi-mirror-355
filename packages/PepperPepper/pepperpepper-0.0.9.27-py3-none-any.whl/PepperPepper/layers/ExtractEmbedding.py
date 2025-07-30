from PepperPepper.environment import torch, nn, F, profile
from PepperPepper.layers import SobelHighFreqEnhance, AttentionalCS, MultiScaleSPWDilate



class extractembedding(nn.Module):
    def __init__(self, in_channels, out_channels, stride = 1):
        super().__init__()
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.stride = stride
        self.SHFE = SobelHighFreqEnhance(self.in_channels, self.out_channels, stride)
        self.MSSPWD = MultiScaleSPWDilate(self.out_channels)
        self.ACS = AttentionalCS(self.out_channels)


    def forward(self, x):
        lv1 = self.SHFE(x)
        lv2 = self.MSSPWD(lv1)
        out = self.ACS(lv2)
        return out





if __name__ == '__main__':
    net = extractembedding(3, 32, 1)
    inputs = torch.rand(1, 3, 256, 256)


    output = net(inputs)
    flops, params = profile(net, (inputs,))

    # print("-" * 50)
    # print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    # print('Params = ' + str(params / 1000 ** 2) + ' M')

    print("-" * 50)
    print('FLOPs = %.2fG' % (flops / 1e9))  # 优化单位显示精度
    print('Params = %.2fM' % (params / 1e6))












