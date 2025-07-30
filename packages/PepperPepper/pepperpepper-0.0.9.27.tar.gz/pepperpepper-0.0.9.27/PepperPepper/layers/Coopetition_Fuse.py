from PepperPepper.environment import torch, nn, F, profile


class Coopetition_Fuse(nn.Module):
    def __init__(self, feature_num=2):
        super().__init__()

        self.feature_num = feature_num

        self.synergy_weights = nn.Parameter(torch.randn(self.feature_num) / self.feature_num, requires_grad=True)
        self.independence_weights = nn.Parameter(torch.randn(self.feature_num) / self.feature_num, requires_grad=True)

        self.path_synergy_weights = nn.Parameter(torch.randn(2) / 2, requires_grad=True)





    def forward(self, f_list):
        synergy_weights = torch.softmax(self.synergy_weights, dim=0)
        independence_weights = (torch.sigmoid(self.independence_weights) - 0.5 ) * 4
        path_synergy_weights = torch.softmax(self.path_synergy_weights, dim=0)

        synergy_f = 0
        independence_f = 0
        out = 0
        for i in range(self.feature_num):
            synergy_f += synergy_weights[i] * f_list[i]
            independence_f += independence_weights[i] * f_list[i]

        out = independence_f * path_synergy_weights[0] + synergy_f * path_synergy_weights[1]


        return out


if __name__ == '__main__':
    net = Coopetition_Fuse(2).cuda()
    inputs = [torch.rand(1, 32, 256, 256).cuda(), torch.rand(1, 32, 256, 256).cuda()]
    # output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')


