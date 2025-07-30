from PepperPepper.environment import torch, nn, F, partial, profile, rearrange
from PepperPepper.layers.WTConv import create_wavelet_filter, wavelet_transform, inverse_wavelet_transform, _ScaleModule


class Gatenetwork(nn.Module):
    def __init__(self, in_channels, h_dim = 128, feature_size = 256, activation=nn.GELU, norm=nn.LayerNorm):
        super().__init__()
        self.in_channels = in_channels
        self.h_dim = h_dim
        self.feature_size = feature_size
        self.embedding = nn.Conv2d(self.in_channels * 4, h_dim, feature_size//2, feature_size//2, groups=self.in_channels * 4)


        self.proj = nn.Sequential(
            norm(h_dim),
            nn.Linear(h_dim, h_dim//2),
            norm(h_dim // 2),
            activation(),
            nn.Linear(h_dim // 2, 4),
            norm(4),
        )



    def forward(self, x, x_tag):
        x = rearrange(x, 'b c n h w -> b (c n) h w ')
        x = self.embedding(x)
        x = rearrange(x, 'b c h w -> b (c h w)')
        # print(x.shape)
        x = self.proj(x)
        x_expanded = x.unsqueeze(1).unsqueeze(3).unsqueeze(4)
        return x_tag * x_expanded







class GateWTConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=5, stride=1, bias=True, wt_type='db1', feature_size = 256):
        super().__init__()

        # 确保输入通道数与输出通道数相等
        assert in_channels == out_channels

        self.feature_size = feature_size

        # 设置属性
        self.in_channels = in_channels
        self.stride = stride
        self.dilation = 1

        # 创建小波滤波器
        self.wt_filter, self.iwt_filter = create_wavelet_filter(wt_type, in_channels, in_channels, torch.float)
        # 将小波滤波器设置为不可训练参数
        self.wt_filter = nn.Parameter(self.wt_filter, requires_grad=False)
        self.iwt_filter = nn.Parameter(self.iwt_filter, requires_grad=False)

        # 部分应用函数，固定小波变换和逆变换中的滤波器参数
        self.wt_function = partial(wavelet_transform, filters=self.wt_filter)
        self.iwt_function = partial(inverse_wavelet_transform, filters=self.iwt_filter)

        # 定义基础卷积层
        self.base_conv = nn.Conv2d(in_channels, in_channels, kernel_size, padding='same', stride=1, dilation=1,
                                   groups=in_channels, bias=bias)
        # 定义基础缩放模块
        self.base_scale = _ScaleModule([1, in_channels, 1, 1])

        # 定义多级小波卷积层
        self.wavelet_convs = nn.Conv2d(in_channels * 4, in_channels * 4, kernel_size, padding='same', stride=1, dilation=1,
                       groups=in_channels * 4, bias=False)

        # 定义多级小波缩放模块
        self.wavelet_scale = _ScaleModule([1, in_channels * 4, 1, 1], init_scale=0.1)

        # 如果步长大于1，则定义步长滤波器
        if self.stride > 1:
            self.stride_filter = nn.Parameter(torch.ones(in_channels, 1, 1, 1), requires_grad=False)
            # 定义执行步长的lambda函数
            self.do_stride = lambda x_in: F.conv2d(x_in, self.stride_filter, bias=None, stride=self.stride,
                                                   groups=in_channels)
        else:
            # 否则，将do_stride设置为None
            self.do_stride = None

        self.gate = Gatenetwork(in_channels, h_dim = 128, feature_size = feature_size)





    def forward(self, x):
        # 初始化列表用于存储各级小波变换的结果
        # x_ll_in_levels = []
        # x_h_in_levels = []
        # shapes_in_levels = []

        # 当前处理的是原始输入x
        curr_x_ll = x

        # 对每一级执行小波变换
        # 存储当前级别的形状
        curr_shape = curr_x_ll.shape
        # shapes_in_levels.append(curr_shape)
        # 如果当前级别宽度或高度是奇数，则需要进行填充
        if (curr_shape[2] % 2 > 0) or (curr_shape[3] % 2 > 0):
            curr_pads = (0, curr_shape[3] % 2, 0, curr_shape[2] % 2)
            curr_x_ll = F.pad(curr_x_ll, curr_pads)

        # 执行当前级别的小波变换
        curr_x = self.wt_function(curr_x_ll)
        # 提取低频子带作为下一级别的输入
        curr_x_ll = curr_x[:, :, 0, :, :]

        # 获取当前级别的形状
        shape_x = curr_x.shape
        # 将当前级别数据重新整形以便进行卷积操作
        curr_x_tag = curr_x.reshape(shape_x[0], shape_x[1] * 4, shape_x[3], shape_x[4])
        # 应用小波卷积层和缩放模块
        curr_x_tag = self.wavelet_scale(self.wavelet_convs(curr_x_tag))
        # 重新调整张量形状
        curr_x_tag = curr_x_tag.reshape(shape_x)

        # print(curr_x_tag.shape)
        # print(curr_x.shape)

        curr_x_tag = self.gate(curr_x, curr_x_tag)
        # curr_x_tag = self.gate(curr_x_tag, curr_x)


        # 分别存储低频和高频子带
        # x_ll_in_levels.append(curr_x_tag[:, :, 0, :, :])
        # x_h_in_levels.append(curr_x_tag[:, :, 1:4, :, :])

        # 初始化next_x_ll变量
        # next_x_ll = 0

        # 反向遍历所有级别以执行逆小波变换

            # 从列表中取出对应级别的低频和高频子带
            # curr_x_ll = x_ll_in_levels.pop()
            # curr_x_h = x_h_in_levels.pop()
            # # 从列表中取出对应级别的原始形状
            # curr_shape = shapes_in_levels.pop()

            # 更新当前级别的低频子带
        # curr_x_ll = curr_x_ll

        # 将低频和高频子带组合在一起
        curr_x = curr_x_tag
        # 执行逆小波变换
        next_x_ll = self.iwt_function(curr_x)

        # 裁剪结果以匹配原始形状
        next_x_ll = next_x_ll[:, :, :curr_shape[2], :curr_shape[3]]

        # 最终结果赋值给x_tag
        x_tag = next_x_ll
        # # 确认所有的低频子带已经被正确处理
        # assert len(x_ll_in_levels) == 0

        # 应用基础卷积层和缩放模块
        x = self.base_scale(self.base_conv(x))
        # 将基础卷积结果与小波变换结果相加
        x = x + x_tag

        # 如果设置了步长，则执行步长操作
        if self.do_stride is not None:
            x = self.do_stride(x)

        # 返回最终结果
        return x





if __name__ == '__main__':
    net = GateWTConv(32, 32)
    inputs = torch.rand(1, 32, 256, 256)
    output = net(inputs)
    flops, params = profile(net, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')




