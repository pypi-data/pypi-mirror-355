from PepperPepper.environment import torch, nn, F, profile






class GradientFocusEnhancer(nn.Module):
    def __init__(self, kernel_size=3, angle_threshold=30, enhance_factor=2.0):
        """
        Args:
            kernel_size: 邻域检测范围（奇数）
            angle_threshold: 角度容忍阈值（度）
            enhance_factor: 增强系数
        """
        super().__init__()
        self.kernel_size = kernel_size
        self.angle_threshold = nn.Parameter(30, requires_grad=True)
        # self.theta_thresh = torch.cos(torch.radians(angle_threshold))
        self.enhance = enhance_factor

        # 预生成位置坐标网格
        self.register_buffer("grid", self._create_position_grid(kernel_size),
                             persistent=False)

    def _create_position_grid(self, k):
        """创建相对位置坐标网格"""
        r = (k - 1) // 2
        y, x = torch.meshgrid(
            torch.linspace(r, -r, k),
            torch.linspace(-r, r, k),
            indexing='ij'
        )
        return torch.stack((x, y), dim=0)  # (2, k, k)

    def _get_angle_cos_similarity(self, grad_angle, center_angle):
        """
        计算梯度方向与期望方向的余弦相似度
        Args:
            grad_angle: 梯度角度张量 (B, C, H, W)
            center_angle: 期望角度张量 (B, C, H, W)
        Returns:
            cos_sim: 余弦相似度矩阵 (B, C, H, W)
        """
        # 将角度转换为向量形式
        grad_vec = torch.stack((
            torch.cos(grad_angle),
            torch.sin(grad_angle)
        ), dim=2)  # (B, 2, C, H, W)

        target_vec = torch.stack((
            torch.cos(center_angle),
            torch.sin(center_angle)
        ), dim=2)  # (B, 2, C, H, W)

        # 计算余弦相似度
        cos_sim = (grad_vec * target_vec).sum(dim=2)  # (B, C, H, W)
        return cos_sim

    def forward(self, theta):
        """
        Args:
            theta: 梯度角度矩阵 (B, C, H, W)，范围[-pi, pi]
        Returns:
            enhanced: 增强后的特征图 (B, C, H, W)
        """
        B, C, H, W = theta.shape
        k = self.kernel_size
        pad = (k - 1) // 2

        # 生成期望方向场 --------------------------------------------------------
        # 展开邻域坐标 (2, k, k) -> (1, 2, k, k, 1, 1)
        pos_grid = self.grid.unsqueeze(0).unsqueeze(-1).unsqueeze(-1)

        # 计算每个位置到中心的方向角度
        dx = pos_grid[:, 0, ...]  # (1, k, k, 1, 1)
        dy = pos_grid[:, 1, ...]  # (1, k, k, 1, 1)
        phi = torch.atan2(dy, dx)  # (1, k, k, 1, 1) 期望方向角度

        # 扩展维度用于广播
        theta_exp = theta.unsqueeze(2).unsqueeze(2)  # (B, C, 1, 1, H, W)
        phi_exp = phi.permute(0, 2, 3, 4, 5, 1)  # (1, k, k, 1, 1, 1)

        # 计算余弦相似度
        cos_sim = self._get_angle_cos_similarity(theta_exp, phi_exp)

        # 判断方向一致性 --------------------------------------------------------
        mask = (cos_sim > self.theta_thresh).float()  # (B, C, k, k, H, W)

        # 统计有效方向数
        valid_count = mask.sum(dim=(2, 3))  # (B, C, H, W)

        # 生成增强系数 --------------------------------------------------------
        total_positions = k ** 2 - 1  # 排除中心自身
        ratio = valid_count / total_positions
        enhance_coeff = torch.sigmoid(10 * (ratio - 0.8)) * self.enhance

        # 应用增强
        enhanced = theta * enhance_coeff

        return enhanced
































class adaptivegradient(nn.Module):
    def __init__(self, dim = 32):
        super().__init__()
        self.dim = dim

        # sobel算子
        self.sigma = nn.Parameter(torch.ones(1), requires_grad=True)

        # Sobel 算子的 y 方向核
        sobel_y_kernel = torch.tensor([
            [self.sigma, 2 * self.sigma, self.sigma],
            [0, 0, 0],
            [-1 * self.sigma, -2 * self.sigma, -1 * self.sigma]
        ], dtype=torch.float32).view(1, 1, 3, 3)

        # Sobel 算子的 x 方向核

        sobel_x_kernel = torch.tensor([
            [-1* self.sigma, 0, self.sigma],
            [-2 * self.sigma, 0, 2 * self.sigma],
            [-1 * self.sigma, 0,  self.sigma]
        ], dtype=torch.float32).view(1, 1, 3, 3)

        # 将核注册为参数或缓冲区，以便在 forward 中使用
        self.register_buffer("sobel_y_kernel", sobel_y_kernel)
        self.register_buffer("sobel_x_kernel", sobel_x_kernel)




    def forward(self, x):
        padding_x = F.pad(x, (1, 1, 1, 1), mode='replicate')

        sobel_y_kernel = self.sobel_y_kernel.repeat(self.dim, 1, 1, 1)
        sobel_x_kernel = self.sobel_x_kernel.repeat(self.dim, 1, 1, 1)

        edge_y = F.conv2d(padding_x, sobel_y_kernel, groups=self.dim)
        edge_x = F.conv2d(padding_x, sobel_x_kernel, groups=self.dim)


        magnitude = torch.sqrt(edge_x ** 2 + edge_y ** 2)
        Gradient_Vector = torch.atan2(edge_y, edge_x)



        return magnitude, Gradient_Vector



if __name__ == '__main__':
    net = adaptivegradient(dim=32).cuda()
    x = torch.rand(1, 32, 256, 256).cuda()
    out = net(x)

    # print(out.shape)
    flops, params = profile(net, x)

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')