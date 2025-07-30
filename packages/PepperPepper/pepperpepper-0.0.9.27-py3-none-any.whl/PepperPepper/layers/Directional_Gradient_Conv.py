from PepperPepper.environment import torch, nn, F, profile


class LearnableSobel(nn.Module):
    def __init__(self, dim=32):
        super().__init__()
        kernel_size = 3
        # 初始化水平/垂直梯度核参数
        self.h_kernel = nn.Parameter(torch.randn(dim, 1, kernel_size, kernel_size))
        self.v_kernel = nn.Parameter(torch.randn(dim, 1, kernel_size, kernel_size))

        # Sobel模式初始化
        self._init_sobel_weights()

        # 固定中间列参数为0（水平核）和中间行参数为0（垂直核）
        with torch.no_grad():
            # 水平核中间列置零
            self.h_kernel[:, :, :, 1] = 0
            # 垂直核中间行置零
            self.v_kernel[:, :, 1, :] = 0

        # 设置参数冻结掩码
        self.register_buffer('h_mask', torch.ones_like(self.h_kernel))
        self.h_mask[:, :, :, kernel_size//2] = 0  # 中间列不可学习

        self.register_buffer('v_mask', torch.ones_like(self.v_kernel))
        self.v_mask[:, :, kernel_size//2, :] = 0  # 中间行不可学习

        self.scale = nn.Parameter(torch.ones(1))

    def _init_sobel_weights(self):
        # 水平梯度核初始化模板
        h_template = torch.tensor([[-1, 0, 1],
                                   [-2, 0, 2],
                                   [-1, 0, 1]], dtype=torch.float32)
        # 垂直梯度核初始化模板
        v_template = torch.tensor([[-1, -2, -1],
                                   [0, 0, 0],
                                   [1, 2, 1]], dtype=torch.float32)

        # 扩展模板到所有通道
        for c in range(self.h_kernel.shape[0]):
            self.h_kernel.data[c] = h_template.clone() + torch.randn_like(h_template) * 0.1
            self.v_kernel.data[c] = v_template.clone() + torch.randn_like(v_template) * 0.1

    def forward(self, x):
        """
        输入: [B, C, H, W]
        输出: 梯度幅值图 [B, C, H, W]
        """
        # 应用可学习掩码
        masked_h = self.h_kernel * self.h_mask
        masked_v = self.v_kernel * self.v_mask

        # 深度可分离卷积
        x_padded = F.pad(x, pad=(1, 1, 1, 1), mode='replicate')
        grad_x = F.conv2d(x_padded, masked_h, groups=x.size(1))
        grad_y = F.conv2d(x_padded, masked_v, groups=x.size(1))

        # 梯度幅值计算
        magnitude = self.scale * torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)

        # 梯度方向计算（使用atan2保留象限信息）
        orientation = torch.atan2(grad_y, grad_x)  # 输出范围[-π, π]
        return magnitude, orientation



class directional_gradient_Conv(nn.Module):
    def __init__(self, dim = 32):
        super().__init__()
        self.dim = dim
        self.LS = LearnableSobel(dim=dim)


    def forward(self, x):
        magnitude, orientation = self.LS(x)
        print(magnitude.shape)
        print(orientation.shape)

        return magnitude, orientation




if __name__ == '__main__':
    net = directional_gradient_Conv(32)
    inputs = torch.rand(1, 32, 256, 256)
    # output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')


