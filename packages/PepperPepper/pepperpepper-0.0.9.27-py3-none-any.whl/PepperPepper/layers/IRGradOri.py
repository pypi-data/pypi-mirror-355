from PepperPepper.environment import torch, nn, F, profile



class LearnableSobel(nn.Module):
    def __init__(self, dim=32, requires_grad=False, sobel_randn=False):
        super().__init__()
        kernel_size = 3
        self.sobel_rand = sobel_randn

        # 初始化水平/垂直梯度核参数
        self.h_kernel = nn.Parameter(torch.randn(dim, 1, kernel_size, kernel_size), requires_grad=requires_grad)
        self.v_kernel = nn.Parameter(torch.randn(dim, 1, kernel_size, kernel_size), requires_grad=requires_grad)

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



    def _init_sobel_weights(self):
        # 水平梯度核初始化模板
        h_template = torch.tensor([[-1, 0, 1],
                                   [-2, 0, 2],
                                   [-1, 0, 1]], dtype=torch.float32)
        # 垂直梯度核初始化模板
        v_template = torch.tensor([[-1, -2, -1],
                                   [0, 0, 0],
                                   [1, 2, 1]], dtype=torch.float32)

        if self.sobel_rand == True:
        # 扩展模板到所有通道
            for c in range(self.h_kernel.shape[0]):
                self.h_kernel.data[c] = h_template.clone() + torch.randn_like(h_template) * 0.1
                self.v_kernel.data[c] = v_template.clone() + torch.randn_like(v_template) * 0.1
        else:
            for c in range(self.h_kernel.shape[0]):
                self.h_kernel.data[c] = h_template.clone()
                self.v_kernel.data[c] = v_template.clone()

    def forward(self, x):
        """
        输入: [B, C, H, W]
        输出: 梯度幅值图 [B, C, H, W]
        """
        # 应用可学习掩码
        masked_h = self.h_kernel * self.h_mask
        masked_v = self.v_kernel * self.v_mask

        # 深度可分离卷积
        padded_x = F.pad(x, pad=(1, 1, 1, 1), mode='replicate')

        grad_x = F.conv2d(padded_x, masked_h, groups=x.size(1))
        grad_y = F.conv2d(padded_x, masked_v, groups=x.size(1))

        # magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)

        return grad_x, grad_y





class IROri(nn.Module):
    def __init__(self, dim=32, kernel_size=3):
        super().__init__()
        self.kernel_size = kernel_size
        self.grad = LearnableSobel(dim=dim, sobel_randn=False, requires_grad=False)
        self.register_buffer('gride', self._create_position_grid(kernel_size))
        self.grad_x = nn.Parameter(torch.ones(dim, kernel_size, kernel_size) * 0.1, requires_grad=True)
        self.grad_y = nn.Parameter(torch.ones(dim, kernel_size, kernel_size) * 0.1, requires_grad=True)
        # self.adjust = nn.Parameter(torch.ones(dim, kernel_size, kernel_size) * 0.1, requires_grad=True)

        self.norm = nn.BatchNorm2d(dim)
        self.act = nn.LeakyReLU()

    def _create_position_grid(self, k):

        # 处理kernel尺寸
        if isinstance(k, int):
            kernel_h = kernel_w = k
        else:
            kernel_h, kernel_w = k

        """创建相对位置坐标网格"""
        rx = (kernel_w - 1) // 2
        ry = (kernel_h - 1) // 2

        y, x = torch.meshgrid(
            torch.linspace(-ry, ry, kernel_h),
            torch.linspace(-rx, rx, kernel_w),
            indexing='ij'
        )
        PiK = torch.atan2(-1 * y + 1e-6, -1 * x + 1e-6)
        return PiK

    def forward(self, x):
        kernel_theta = torch.atan2(self.grad_y + 1e-6, self.grad_x + 1e-6)/8  + self.gride
        # kernel_theta = (torch.sigmoid(self.adjust)-0.5) * torch.pi +  self.gride

        grad_x, grad_y = self.grad(x)
        effective_k_h = self.kernel_size
        effective_k_w = self.kernel_size
        pad_h = ((x.shape[2] - 1) * 1 + effective_k_h - x.shape[2]) // 2
        pad_w = ((x.shape[3] - 1) * 1 + effective_k_w - x.shape[3]) // 2
        theta = torch.atan2(grad_y+ 1e-6, grad_x+ 1e-6)
        _, _, H_out, W_out = theta.shape
        theta = F.pad(theta, (pad_w, pad_w, pad_h, pad_h), mode='replicate')

        theta_unfold = theta.unfold(2, self.kernel_size, 1).unfold(3, self.kernel_size, 1)

        # 维度重排 [B,C,H_out,W_out,KH,KW] -> [B,C,KH,KW,H_out,W_out]
        theta_unfold = theta_unfold.permute(0, 1, 4, 5, 2, 3)
        # print(theta_unfold.shape)

        # 广播计算 [B,C,KH,KW,H_out,W_out] - [KH,KW]
        # T = torch.cos(theta_unfold - self.gride.to(x.device)[None, None, :, :, None, None])
        T = torch.cos(theta_unfold - kernel_theta.to(x.device)[None, :, :, :, None, None])

        # 中心位置置零
        center_h, center_w = effective_k_h // 2, effective_k_w // 2
        T[:, :, center_h, center_w, :, :] = 0.0

        # 求和并恢复形状
        vector = T.sum(dim=(2, 3))  # [B,C,H_out,W_out]

        # 梯度幅值计算（带可学习缩放系数）
        # magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)

        return self.act(self.norm(vector))




class IRGradOri(nn.Module):
    def __init__(self, dim=32, kernel_size=3):
        super().__init__()
        self.kernel_size = kernel_size
        self.grad = LearnableSobel(dim=dim, sobel_randn=True, requires_grad=True)
        self.ori = IROri(dim=dim, kernel_size=kernel_size)
        self.norm = nn.BatchNorm2d(dim)
        self.act = nn.LeakyReLU()

        self.scale = nn.Parameter(torch.ones(dim), requires_grad=True)



    def forward(self, x):
        grad_x, grad_y = self.grad(x)
        magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)
        # magnitude = self.act(self.norm(magnitude))
        # vector = self.ori(x)

        # Weak_constraint = magnitude * vector
        Weak_constraint = magnitude
        Strong_constraint = Weak_constraint * x
        out = Strong_constraint * self.scale.view(1, -1, 1, 1)

        return out










class IRFixOri(nn.Module):
    def __init__(self, dim=32, kernel_size=3):
        super().__init__()
        self.kernel_size = kernel_size
        self.grad = LearnableSobel(dim=dim, sobel_randn=False, requires_grad=False)
        self.register_buffer('gride', self._create_position_grid(kernel_size))

    def _create_position_grid(self, k):

        # 处理kernel尺寸
        if isinstance(k, int):
            kernel_h = kernel_w = k
        else:
            kernel_h, kernel_w = k

        """创建相对位置坐标网格"""
        rx = (kernel_w - 1) // 2
        ry = (kernel_h - 1) // 2

        y, x = torch.meshgrid(
            torch.linspace(-ry, ry, kernel_h),
            torch.linspace(-rx, rx, kernel_w),
            indexing='ij'
        )
        PiK = torch.atan2(-1 * y + 1e-6, -1 * x + 1e-6)
        return PiK

    def forward(self, x):
        kernel_theta = self.gride
        grad_x, grad_y = self.grad(x)
        effective_k_h = self.kernel_size
        effective_k_w = self.kernel_size
        pad_h = ((x.shape[2] - 1) * 1 + effective_k_h - x.shape[2]) // 2
        pad_w = ((x.shape[3] - 1) * 1 + effective_k_w - x.shape[3]) // 2
        theta = torch.atan2(grad_y+ 1e-6, grad_x+ 1e-6)
        _, _, H_out, W_out = theta.shape
        theta = F.pad(theta, (pad_w, pad_w, pad_h, pad_h), mode='replicate')

        theta_unfold = theta.unfold(2, self.kernel_size, 1).unfold(3, self.kernel_size, 1)

        # 维度重排 [B,C,H_out,W_out,KH,KW] -> [B,C,KH,KW,H_out,W_out]
        theta_unfold = theta_unfold.permute(0, 1, 4, 5, 2, 3)

        # 广播计算 [B,C,KH,KW,H_out,W_out] - [KH,KW]
        T = torch.cos(theta_unfold - kernel_theta.to(x.device)[None, None, :, :, None, None])

        # 中心位置置零
        center_h, center_w = effective_k_h // 2, effective_k_w // 2
        T[:, :, center_h, center_w, :, :] = 0.0

        # 求和并恢复形状
        vector = T.sum(dim=(2, 3))  # [B,C,H_out,W_out]

        # 梯度幅值计算（带可学习缩放系数）
        magnitude = torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)

        return vector, magnitude



if __name__ == "__main__":
    net = IRGradOri(dim=32)
    inputs = torch.ones(1, 32, 256, 256)
    # output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')

