# # Infrared Gradient Orientation: 突出红外图像中梯度方向。
#
# from PepperPepper.environment import torch, nn, F, profile, math
#
#
#
# class IRGradOri(nn.Module):
#     def __init__(self, dim=3, angle_threshold=30, enhance_factor=2.0, kernel_size=3,
#                  stride=1, padding='same', dilation=1):
#         super().__init__()
#         groups = dim
#         # 参数验证
#         assert dim % groups == 0, "输入通道数必须能被groups整除"
#         assert dim % groups == 0, "输出通道数必须能被groups整除"
#         assert isinstance(dilation, (int, tuple)), "dilation必须是整数或元组"
#
#         # 核心参数
#         self.in_channels = dim
#         self.out_channels = dim
#         self.kernel_size = kernel_size
#         self.stride = stride
#         self.padding = padding
#         self.dilation = dilation
#         self.groups = groups
#
#         self.angle_threshold = angle_threshold
#         self.enhance = enhance_factor
#
#         # 处理kernel尺寸
#         if isinstance(kernel_size, int):
#             self.kernel_h = self.kernel_w = kernel_size
#         else:
#             self.kernel_h, self.kernel_w = kernel_size
#
#
#         # 预生成位置坐标网格
#         self.register_buffer("grid", self._create_position_grid(kernel_size),
#                             persistent=False)
#
#         # 处理dilation参数
#         if isinstance(dilation, int):
#             self.dilation_h = self.dilation_w = dilation
#         else:
#             self.dilation_h, self.dilation_w = dilation
#
#         # 计算每个组的通道数
#         self.in_channels_per_group = groups // groups
#         self.out_channels_per_group = groups // groups
#
#         self.weight = nn.Parameter(self.grid, requires_grad=False)
#
#
#
#
#     def _create_position_grid(self, k):
#         # 处理kernel尺寸
#         if isinstance(k, int):
#             kernel_h = kernel_w = k
#         else:
#             kernel_h, kernel_w = k
#
#
#         """创建相对位置坐标网格"""
#         rx = (kernel_w - 1) // 2
#         ry = (kernel_h - 1) // 2
#
#         y, x = torch.meshgrid(
#             torch.linspace(ry, -ry, kernel_h),
#             torch.linspace(-rx, rx, kernel_w),
#             indexing='ij'
#         )
#
#
#         PiK = torch.atan2(-1*y, -1*x)
#
#         return PiK
#
#
#
#
#     def forward(self, x):
#         # 输入形状检查
#         assert x.ndim == 4, "输入必须是4D张量 (N, C, H, W)"
#
#         # 自动计算padding（如果指定'same'模式）
#         if isinstance(self.padding, str):
#             if self.padding.lower() == 'same':
#                 # 考虑dilation后的等效核尺寸
#                 effective_k_h = self.kernel_h + (self.kernel_h - 1) * (self.dilation_h - 1)
#                 effective_k_w = self.kernel_w + (self.kernel_w - 1) * (self.dilation_w - 1)
#                 pad_h = ((x.shape[2] - 1) * self.stride + effective_k_h - x.shape[2]) // 2
#                 pad_w = ((x.shape[3] - 1) * self.stride + effective_k_w - x.shape[3]) // 2
#                 padding = (pad_h, pad_w)
#             elif self.padding.lower() == 'valid':
#                 padding = (0, 0)
#             else:
#                 raise ValueError("不支持的padding模式")
#         else:
#             padding = self.padding
#
#
#         # 执行手动卷积计算
#         return self.conv2d(x, self.weight,
#                            stride=self.stride,
#                            padding=padding,
#                            dilation=(self.dilation_h, self.dilation_w),
#                            groups=self.groups)
#
#     @staticmethod
#     def conv2d(x, weight, stride, padding, dilation, groups):
#         # 输入形状
#         N, C_in, H_in, W_in = x.shape
#         K_h, K_w = weight.shape
#
#         # 处理padding和dilation
#         if isinstance(padding, int):
#             pad_h = pad_w = padding
#         else:
#             pad_h, pad_w = padding
#
#         if isinstance(dilation, int):
#             dilation_h = dilation_w = dilation
#         else:
#             dilation_h, dilation_w = dilation
#
#         # 计算等效核尺寸
#         effective_k_h = K_h + (K_h - 1) * (dilation_h - 1)
#         effective_k_w = K_w + (K_w - 1) * (dilation_w - 1)
#
#
#         # 填充输入（注意padding在dilation之前应用）
#         x_padded = F.pad(x, (pad_w, pad_w, pad_h, pad_h))
#
#         # 计算输出尺寸（考虑dilation）
#         H_out = (H_in + 2 * pad_h - effective_k_h) // stride + 1
#         W_out = (W_in + 2 * pad_w - effective_k_w) // stride + 1
#         assert H_out > 0 and W_out > 0, "无效的输出尺寸，请检查参数组合"
#
#         # 展开输入为im2col格式（包含dilation处理）
#         unfold = nn.Unfold(kernel_size=(K_h, K_w),
#                            dilation=dilation,
#                            padding=0,
#                            stride=stride)
#
#
#         x_unfold = unfold(x_padded)  # (N, C*K_h*K_w, H_out*W_out)
#
#
#         # 调整形状便于分组计算
#         # x_unfold = x_unfold.view(N, groups, C_in_per_group, K_h * K_w, H_out, W_out)
#         # weight = weight.view(groups, C_out // groups, C_in_per_group, K_h * K_w)
#
#
#         x_unfold = x_unfold.view(N, C_in, H_out, W_out, -1)
#         # print(x_unfold.shape)
#         weight = torch.flatten(weight)
#
#         out = torch.cos(x_unfold-weight)
#
#         out[:, :, :, :, (K_h*K_w)//2] = 0
#
#         output = out.sum(dim=-1)
#
#         return output
#
#     def __repr__(self):
#         return (f"IRGradOri({self.in_channels}, {self.out_channels}, "
#                 f"kernel_size={self.kernel_size}, stride={self.stride}, "
#                 f"padding={self.padding}, dilation={self.dilation}, "
#                 f"groups={self.groups})")
#
#
#
#
# if __name__=="__main__":
#     net = IRGradOri(dim=3, kernel_size=(3, 3), stride=1).cuda()
#     inputs = torch.rand(1, 3, 64, 64).cuda()
#     flops, params = profile(net, (inputs,))
#     print("-" * 50)
#     print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
#     print('Params = ' + str(params / 1000 ** 2) + ' M')
#
