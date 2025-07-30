from PepperPepper.environment import torch, nn, profile


class AlternateCat(nn.Module):
    def __init__(self, dim=1, num=3):
        """
        沿指定维度交替拼接两个张量。

        Args:
            dim (int, optional): 指定的维度，默认为 1（通道维度）。
        """
        super().__init__()
        self.dim = dim
        self.num = num

    def forward(self, x_list):
        """
        沿指定维度交替拼接两个张量。

        Args:
            x (torch.Tensor): 第一个输入张量。
            y (torch.Tensor): 第二个输入张量。

        Returns:
            torch.Tensor: 沿指定维度交替拼接后的张量。

        Raises:
            AssertionError: 如果输入张量在指定维度上的大小不一致。
        """
        # 确保两个张量在指定维度上的大小一致
        # assert x.shape == y.shape, f'x.shape:{x.shape} != y.shape:{y.shape}'
        assert len(x_list) == self.num, f'input num error!'
        for i in range(self.num):
            assert x_list[0].shape == x_list[i].shape, f'input index{i} shape error!'



        # 获取指定维度的大小
        size = x_list[0].size(self.dim)
        # print(size)

        x_list_slices = []
        # 将 x 和 y 沿着指定维度拆分为单个元素的切片
        for i in range(self.num):
            x_list_slices.append(torch.split(x_list[i], 1, dim=self.dim))

        # 交替拼接 x 和 y 的切片
        interleaved_slices = []
        for i in range(size):
            for j in range(self.num):
                interleaved_slices.append(x_list_slices[j][i])
            # interleaved_slices.extend([x_slices[i], y_slices[i]])

        # 沿着指定维度堆叠交替后的切片
        concatenated = torch.cat(interleaved_slices, dim=self.dim)

        return concatenated


if __name__ == '__main__':
    net = AlternateCat(dim=1, num=3).cuda()
    x = torch.rand(1, 32, 256, 256).cuda()
    y = torch.rand(1, 32, 256, 256).cuda()
    z = torch.rand(1, 32, 256, 256).cuda()
    out = net([x, y, z])

    print(out.shape)
    flops, params = profile(net, ([x,y,z],))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')

