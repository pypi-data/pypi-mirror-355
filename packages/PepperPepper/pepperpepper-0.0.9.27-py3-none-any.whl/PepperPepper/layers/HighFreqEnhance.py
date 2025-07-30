from PepperPepper.environment import torch, nn, F, profile
from PepperPepper.layers import ResidualBlock, AlternateCat, IRGradOri



'''
1.LearnableSobel：可学习的Sobel算子；
2.SobelHighFreqEnhance：利用上述复现的可学习的sobel算子进行高频增强，其先使用residualblock进行初步抽取特征，然后使用深度可学习的sobel进行提取，最后将其进行cat起来；
'''



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
        padded_x = F.pad(x, pad=(1, 1, 1, 1), mode='replicate')

        grad_x = F.conv2d(padded_x, masked_h, groups=x.size(1))
        grad_y = F.conv2d(padded_x, masked_v, groups=x.size(1))

        # 梯度幅值计算（带可学习缩放系数）
        magnitude = self.scale * torch.sqrt(grad_x ** 2 + grad_y ** 2 + 1e-6)
        return magnitude





class SobelHighFreqEnhance(nn.Module):
    def __init__(self, in_dims=3, out_dims=64, stride=1,  base_dim=None):
        super().__init__()
        if base_dim is None:
            base_dim = out_dims//2

        self.base_dim = base_dim
        self.proj_conv = ResidualBlock(in_dims, base_dim, stride)
        # self.sobel_conv = LearnableSobel(base_dim)

        self.iro = IRGradOri(base_dim, 3)
        self.altercat = AlternateCat(dim=1, num=2)




    def forward(self, x):
        f1 = self.proj_conv(x)
        fs = self.iro(f1)
        fout = self.altercat([f1, fs])

        return fout


if __name__ == '__main__':
    net = SobelHighFreqEnhance(3, 32).cuda()
    inputs = torch.rand(1, 3, 256, 256).cuda()
    output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')











