from ..environment import torch




"""
1.LeNet
abstract:
        LeNet5是一个经典的卷积神经网络，由多个卷积层、池化层和全连接层组成。它通过卷积操作提取图像中的局部特征，利用池化层进行特征下采样，并通过全连接层进行分类。LeNet最初用于手写数字识别任务，并展现出了良好的性能。其结构简洁明了，为后续更复杂的神经网络结构提供了基础，对深度学习领域的发展产生了重要影响。

struct:
        卷积编码器：由两个卷积层组成;
        全连接层密集块：由三个全连接层组成。

input: 
        28*28的单通道（黑白）图像通过LeNet,in_channels×28×28。

output: 
        最后一层输出为10的Linear层，分别代表十种数字的类别数。

"""
class LeNet5(torch.nn.Module):
    def __init__(self,in_channels=3 ,num_classes=10):
        super(LeNet5, self).__init__()
        self.features = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, 6, 5, padding=2), # 输入通道数为in_channels，输出通道数为6，卷积核大小为5
            torch.nn.BatchNorm2d(6),
            torch.nn.Sigmoid(),
            torch.nn.AvgPool2d(kernel_size=2, stride=2), # 池化窗口2x2，步长2
            torch.nn.Conv2d(6, 16, 5), # 输入通道6，输出通道16，卷积核5x5
            torch.nn.BatchNorm2d(16),
            torch.nn.Sigmoid(),
            torch.nn.AvgPool2d(kernel_size=2, stride=2), # 池化窗口2x2，步长2
        )

        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(16 * 5 * 5, 120),
            torch.nn.BatchNorm1d(120),
            torch.nn.Sigmoid(),
            torch.nn.Linear(120, 84),
            torch.nn.BatchNorm1d(84),
            torch.nn.Sigmoid(),
            torch.nn.Linear(84, num_classes)
        )

    def forward(self, x):
        x = self.features(x)
        #x = x.view(x.size(0), -1)  # 确保这里的展平操作是正确的
        x = self.classifier(x)
        return x



    def initialize_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Conv2d):
                torch.nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    torch.nn.init.zeros_(m.bias)
            elif isinstance(m, torch.nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    torch.nn.init.zeros_(m.bias)



"""
2.AlexNet
abstract:
        AlexNet 是 2012 年 ImageNet 竞赛的冠军模型，由 Alex Krizhevsky、Ilya Sutskever 和 Geoffrey Hinton 提出。

struct:
        模型首先包含了一个特征提取部分 self.features，该部分由几个卷积层、ReLU 激活函数和最大池化层组成。然后，通过一个自适应平均池化层 self.avgpool 将特征图的大小减小到 6x6。最后，通过三个全连接层 self.classifier 进行分类。

input: 
        输入图像的大小是 in_channelsx224x224（AlexNet 的原始输入大小）。

output: 
        num_classes 参数用于指定分类的类别数，你可以根据你的任务需求进行修改。
"""
# 定义AlexNet模型类，继承自nn.Module
class AlexNet(torch.nn.Module):
    # 初始化函数，用于设置网络层
    def __init__(self, in_channels=3, num_classes=1000):
        super(AlexNet,self).__init__()  # 调用父类nn.Module的初始化函数

        # 定义特征提取部分
        self.features = torch.nn.Sequential(
            # 第一个卷积层，输入通道3（RGB），输出通道64，卷积核大小11x11，步长4，填充2
            torch.nn.Conv2d(in_channels, 64, kernel_size=11, stride=4, padding=2),
            # ReLU激活函数，inplace=True表示直接修改原变量，节省内存
            torch.nn.ReLU(inplace=True),
            # 最大池化层，池化核大小3x3，步长2
            torch.nn.MaxPool2d(kernel_size=3, stride=2),

            # 第二个卷积层，输入通道64，输出通道192，卷积核大小5x5，填充2
            torch.nn.Conv2d(64, 192, kernel_size=5, padding=2),
            torch.nn.ReLU(inplace=True),
            torch.nn.MaxPool2d(kernel_size=3, stride=2),

            # 接下来的三个卷积层没有池化层
            torch.nn.Conv2d(192, 384, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(384, 256, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(256, 256, kernel_size=3, padding=1),
            torch.nn.ReLU(inplace=True),

            # 最后一个最大池化层
            torch.nn.MaxPool2d(kernel_size=3, stride=2),
        )

        # 自适应平均池化层，将特征图大小调整为6x6
        self.avgpool = torch.nn.AdaptiveAvgPool2d((6, 6))

        # 定义分类器部分
        self.classifier = torch.nn.Sequential(
            # Dropout层用于防止过拟合
            torch.nn.Dropout(),
            # 第一个全连接层，输入特征数量取决于上一个池化层的输出，输出4096
            torch.nn.Linear(256 * 6 * 6, 4096),
            torch.nn.ReLU(inplace=True),
            # 第二个Dropout层
            torch.nn.Dropout(),
            # 第二个全连接层，输出4096
            torch.nn.Linear(4096, 4096),
            torch.nn.ReLU(inplace=True),
            # 输出层，输出类别数由num_classes指定
            torch.nn.Linear(4096, num_classes),
        )


    def forward(self, x):
        # 数据通过特征提取部分
        x = self.features(x)
        # 数据通过自适应平均池化层
        x = self.avgpool(x)
        # 将数据展平为一维向量，以便输入到全连接层
        x = torch.flatten(x, 1)
        # 数据通过分类器部分
        x = self.classifier(x)
        # 返回最终分类结果
        return x


    def initialize_weights(self):
        for m in self.modules():
            if isinstance(m, torch.nn.Conv2d):
                torch.nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    torch.nn.init.zeros_(m.bias)
            elif isinstance(m, torch.nn.Linear):
                torch.nn.init.xavier_uniform_(m.weight)
                if m.bias is not None:
                    torch.nn.init.zeros_(m.bias)






# 3.定义一个VGG卷积块
class VGGBlock(torch.nn.Module):
    def __init__(self, in_channels, out_channels, num_convs, pool=True):
        """
        VGG块，包含多个卷积层和一个可选的最大池化层

        参数:
            in_channels (int): 输入通道数
            out_channels (int): 输出通道数（每个卷积层的输出通道数）
            num_convs (int): 卷积层的数量
            pool (bool, 可选): 是否在块后添加最大池化层。默认为True
        """
        super(VGGBlock, self).__init__()

        # 创建多个卷积层，每个卷积层后面都跟着ReLU激活函数
        layers = []
        for _ in range(num_convs):
            layers.append(torch.nn.Conv2d(in_channels if _ == 0 else out_channels, out_channels, kernel_size=3, padding=1))
            layers.append(torch.nn.ReLU(inplace=True))

            # 如果有池化层，则添加
        if pool:
            layers.append(torch.nn.MaxPool2d(kernel_size=2, stride=2))

            # 将所有层组合成一个Sequential模块
        self.conv_block = torch.nn.Sequential(*layers)

    def forward(self, x):
        """
        前向传播

        参数:
            x (torch.Tensor): 输入张量

        返回:
            torch.Tensor: 输出张量
        """
        x = self.conv_block(x)
        return x






#4.定义VGG16模型
class VGG16(torch.nn.Module):
    def __init__(self, in_channels=3, num_classes=1000):
        """
        VGG16模型

        参数:
            num_classes (int, 可选): 分类的数量。默认为1000
        """
        super(VGG16, self).__init__()

        # 定义特征提取部分
        self.features = torch.nn.Sequential(
            VGGBlock(in_channels, 64, 2, pool=True),  # block1: 64 channels, 2 conv layers, maxpool
            VGGBlock(64, 128, 2, pool=True),  # block2: 128 channels, 2 conv layers, maxpool
            VGGBlock(128, 256, 3, pool=True),  # block3: 256 channels, 3 conv layers, maxpool
            VGGBlock(256, 512, 3, pool=True),  # block4: 512 channels, 3 conv layers, maxpool
            VGGBlock(512, 512, 3, pool=True)  # block5: 512 channels, 3 conv layers, maxpool
        )

        # 定义分类器部分（全连接层）
        self.classifier = torch.nn.Sequential(
            torch.nn.Linear(512 * 7 * 7, 4096),  # fully connected layer, 4096 output neurons
            torch.nn.ReLU(True),
            torch.nn.Dropout(),
            torch.nn.Linear(4096, 4096),
            torch.nn.ReLU(True),
            torch.nn.Dropout(),
            torch.nn.Linear(4096, num_classes)  # fully connected layer, num_classes output neurons for classification
        )

        # 初始化权重
        for m in self.modules():
            if isinstance(m, torch.nn.Conv2d):
                torch.nn.init.kaiming_normal_(m.weight, mode='fan_out', nonlinearity='relu')
                if m.bias is not None:
                    torch.nn.init.constant_(m.bias, 0)
            elif isinstance(m, torch.nn.Linear):
                torch.nn.init.normal_(m.weight, 0, 0.01)
                torch.nn.init.constant_(m.bias, 0)

    def forward(self, x):
        """
        前向传播

        参数:
            x (torch.Tensor): 输入张量

        返回:
            torch.Tensor: 分类的logits
        """
        # 特征提取
        x = self.features(x)

        # 在将特征图送入全连接层之前，需要将其展平（flatten）
        # 假设输入图像的大小是3x224x224，经过5个池化层（每个池化层将尺寸减半）后，
        # 特征图的大小会变成 7x7
        x = x.view(x.size(0), -1)  # 展平操作，-1 表示让PyTorch自动计算该维度的大小

        # 送入分类器
        x = self.classifier(x)

        return x











#5.MLPConv层
class MLPConv(torch.nn.Module):
    """
    MLPConv层，包含一个1x1卷积层模拟MLP的行为
    """
    def __init__(self, in_channels, hidden_channels, out_channels):
        super(MLPConv,self).__init__()
        # 第一个1x1卷积层，用于减少通道数
        self.conv1 = torch.nn.Conv2d(in_channels, hidden_channels, kernel_size=1, bias=True)

        # ReLU激活函数
        self.relu = torch.nn.ReLU(inplace=True)

        # 第二个1x1卷积层，用于恢复到输出通道数
        self.conv2 = torch.nn.Conv2d(hidden_channels, out_channels, kernel_size=1, bias=True)



    def forward(self, x):
        # 通过第一个1x1卷积层
        x = self.conv1(x)
        # 应用ReLU激活函数
        x = self.relu(x)
        # 通过第二个1x1卷积层
        x = self.conv2(x)
        # 应用ReLU激活函数
        x = self.relu(x)
        return x






#6.NiN块
class NiNBlock(torch.nn.Module):
    """
    NiN块，包含一个标准的卷积层和一个MLPConv层
    """
    def __init__(self, in_channels, num_channels , kernel_size=3, stride=1, padding=1):
        super(NiNBlock, self).__init__()
        # 标准的卷积层
        self.conv = torch.nn.Conv2d(in_channels, num_channels, kernel_size=kernel_size, stride=stride, padding=padding, bias=True)
        # MLPConv层
        self.mlpconv = MLPConv(num_channels, num_channels // 2, num_channels)



    def forward(self, x):
        # 通过标准的卷积层
        x = self.conv(x)
        # 通过MLPConv层
        x = self.mlpconv(x)
        return x






#7.Network in Network模型
class NiN(torch.nn.Module):
    """
    Network in Network模型
    输入图片大小为224x224
    """

    def __init__(self, in_channels=3, num_classes=10):
        super(NiN, self).__init__()
        # 初始卷积层
        self.features = torch.nn.Sequential(
            NiNBlock(in_channels, 96, kernel_size=11, stride=4, padding=0),  # 使用较大的卷积核和步长来减少空间维度
            torch.nn.MaxPool2d(kernel_size=3, stride=2),  # 最大池化层
            NiNBlock(96, 256, kernel_size=5, stride=1, padding=2),
            torch.nn.MaxPool2d(kernel_size=3, stride=2),
            NiNBlock(256, 384, kernel_size=3, stride=1, padding=1),
            torch.nn.MaxPool2d(kernel_size=3, stride=2),
            torch.nn.Dropout(p=0.5),  # 引入Dropout层防止过拟合
            NiNBlock(384, num_classes, kernel_size=3, stride=1, padding=1),
            # 使用全局平均池化替代全连接层
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten()
        )

    def forward(self, x):
        # 通过特征提取层
        x = self.features(x)
        return x










#8.InceptionBlock块v1版本
"""
简介：Inception块v1版本，也称为Inception-v1，是GoogLeNet网络中的一个核心组成部分，由Google团队在2014年提出。Inception-v1的主要特点是使用多尺度的卷积操作来捕捉图像中不同层次的特征。为了实现这一目标，Inception-v1引入了称为“Inception模块”的基本构建块。一个典型的Inception模块由四个并行的卷积分支组成，每个分支执行不同尺度的卷积操作。这些分支的输出在通道维度上进行拼接，形成模块的最终输出。
结构：
1x1卷积分支：使用1x1的卷积核对输入进行卷积，这种卷积方式可以减少神经网络的参数量，并压缩通道数，提高计算效率。
3x3卷积分支：使用3x3的卷积核对输入进行卷积，以捕获局部特征。
5x5卷积分支：使用5x5的卷积核对输入进行卷积，以捕获更大范围的特征。但是，直接使用5x5的卷积核会导致计算量较大，因此在实际实现中，可能会使用两个3x3的卷积层来替代。
最大池化分支：使用3x3的最大池化层对输入进行下采样，然后使用1x1的卷积层来改变通道数。这个分支的目的是捕获更抽象的特征。
"""
class InceptionBlockV1(torch.nn.Module):
    def __init__(self,
                 in_channels,   # 输入到Inception块的通道数
                 ch1,           # 路径1：1x1卷积分支的输出通道数
                 ch2,           # 路径2：ch2[0]为3x3卷积分支的第一个1x1卷积的输出通道数（用于降维），ch2[1]为3x3卷积分支的3x3卷积的输出通道数
                 ch3,           # 路径3：ch3[0]为5x5卷积分支的第一个1x1卷积的输出通道数（用于降维），ch3[1]5x5卷积分支的5x5卷积的输出通道数
                 ch4):          # 最大池化分支的1x1卷积的输出通道数（用于降维后投影到同一通道数）
        super(InceptionBlockV1,self).__init__()

        # 路径1，单1x1卷积层，直接对输入进行1x1卷积
        self.brach1 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, ch1, kernel_size=1),
            torch.nn.ReLU(inplace=True)
        )



        # 路径2，1x1卷积 -> 3x3卷积分支，先进行1x1卷积降维，再进行3x3卷积
        self.brach2 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, ch2[0], kernel_size=1),      # 输入in_channels, 输出ch3x3red
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(ch2[0], ch2[1], kernel_size=3, padding=1), # 输入ch3x3red, 输出ch3x3
            torch.nn.ReLU(inplace=True)
        )



        # 路径3，1x1卷积 -> 5x5卷积分支
        self.brach3 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, ch3[0], kernel_size=1),      # 输入in_channels, 输出ch5x5red
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(ch3[0], ch3[1], kernel_size=5, padding=2), # 输入ch5x5red, 输出ch5x5
            torch.nn.ReLU(inplace=True)
        )


        # 路径4，3x3最大池化 -> 1x1卷积分支，先进行3x3最大池化，然后进行1x1卷积改变通道数
        self.brach4 = torch.nn.Sequential(
            torch.nn.MaxPool2d(kernel_size=3, stride=1, padding=1),
            torch.nn.Conv2d(in_channels, ch4, kernel_size=1),
            torch.nn.ReLU(inplace=True)
        )



    def forward(self, x):
        branch1 = self.brach1(x)
        branch2 = self.brach2(x)
        branch3 = self.brach3(x)
        branch4 = self.brach4(x)

        # 拼接各分支的输出
        outputs = torch.cat((branch1, branch2, branch3, branch4), dim=1)
        return outputs











#9.GoogLeNet的复现
"""
简介：GoogLeNet的设计特点在于既有深度，又在横向上拥有“宽度”，并采用了一种名为Inception的核心子网络结构。这个网络名字中的“GoogLeNet”是对LeNet的致敬，LeNet是早期由Yann LeCun设计的卷积神经网络。
基本结构：
    Inception模块：这是GoogLeNet的核心子网络结构。Inception模块的基本组成结构有四个：1x1卷积、3x3卷积、5x5卷积和3x3最大池化。这四个操作并行进行以提取特征，然后将这四个操作的输出进行通道维度的拼接。这种设计使得网络能够捕捉不同尺度的特征。
    1x1卷积：在Inception模块中，1x1卷积起到了两个主要作用。首先，它可以在相同尺寸的感受野中叠加更多的卷积，从而提取到更丰富的特征。其次，它还可以用于降维，降低计算复杂度。当某个卷积层输入的特征数较多时，对输入先进行降维，减少特征数后再做卷积，可以显著减少计算量。
    辅助分类器：GoogLeNet在网络的不同深度处添加了两个辅助分类器。这些辅助分类器在训练过程中与主分类器一同进行优化，有助于提升整个网络的训练效果。
    全局平均池化：与传统的全连接层相比，全局平均池化能够减少网络参数，降低过拟合风险，并且具有更强的鲁棒性。
"""
class GoogLeNet(torch.nn.Module):
    def __init__(self, in_channels=3, num_classes=1000):
        super(GoogLeNet,self).__init__()


        # 第一个模块:使用64个通道、7x7卷积层。
        self.block1 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )


        # 第二个模块:第一层卷积层是64个通道、1x1卷积层；第二个卷积层使用将通道数增加3x的3x3卷积层。
        self.block2 = torch.nn.Sequential(
            torch.nn.Conv2d(64, 64, kernel_size=1),
            torch.nn.ReLU(),
            torch.nn.Conv2d(64, 192, kernel_size=3, padding=1),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )


        # 第三个模块：串联两个Inception块。具体操作请看相关论文
        self.block3 = torch.nn.Sequential(
            InceptionBlockV1(192, 64, (96, 128), (16, 32), 32),
            InceptionBlockV1(256, 128, (128, 192), (32, 96), 64),
            torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )



        # 第四个模块：串联了5个Inception块
        self.block4 = torch.nn.Sequential(
            InceptionBlockV1( 480, 192, (96, 208), (16, 48), 64),
            InceptionBlockV1(512, 160, (112, 224), (24, 64), 64),
            InceptionBlockV1(512, 128, (128, 256), (24, 64), 64),
            InceptionBlockV1(512, 112, (114, 288), (32, 64), 64),
            InceptionBlockV1(528, 256, (160, 320), (32, 128), 128),
            torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )


        # 第五个模块： 其中每条路径通道数的分配思路和第三、第四模块中的一致，只是在具体数值上有所不同。 需要注意的是，第五模块的后面紧跟输出层，该模块同NiN一样使用全局平均汇聚层，将每个通道的高和宽变成1。 最后我们将输出变成二维数组，再接上一个输出个数为标签类别数的全连接层。
        self.block5 = torch.nn.Sequential(
            InceptionBlockV1(832, 256, (160, 320), (32, 128), 128),
            InceptionBlockV1(832, 384, (192, 384), (48,128), 128),
            torch.nn.AdaptiveAvgPool2d((1, 1)),
            torch.nn.Flatten()
        )

        self.features = torch.nn.Sequential(self.block1, self.block2, self.block3, self.block4, self.block5)

        # 分类器（全连接层）
        self.classifier = torch.nn.Linear(1024, num_classes)





    def forward(self, x):
        # 前向传播：通过特征提取层
        x = self.features(x)

        # 展平特征图，准备进行全连接层
        x = self.classifier(x)

        # 输出分类结果
        return x








"""
10.ResidualBlock的复现
简介：残差块允许网络学习残差映射，这有助于解决深度网络中的梯度消失和表示瓶颈问题。
参数:  
    - in_channels: 输入的通道数  
    - out_channels: 输出的通道数  
    - stride: 卷积的步长，默认为1  
"""
class ResidualBlock(torch.nn.Module):
    def __init__(self, in_channels, out_channels, strides=1):
        super(ResidualBlock, self).__init__()

        # 当输入输出通道数不同或者步长不为1时，需要使用一个1x1的卷积进行降维和步长调整
        # 这样可以确保主路径（shortcut）和残差路径（residual path）的输出形状一致
        self.shortcut = torch.nn.Sequential()
        if strides != 1 or in_channels != out_channels:
            self.shortcut = torch.nn.Sequential(
                torch.nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=strides),
            )

        # 残差路径包含两个3x3的卷积层，每个卷积层后都跟着一个批量归一化层和一个ReLU激活函数
        self.residual = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=strides, padding=1),
            torch.nn.BatchNorm2d(out_channels),
            torch.nn.LeakyReLU(0.1,inplace=True),
            torch.nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1),
            torch.nn.BatchNorm2d(out_channels)
        )

        # 最后一个ReLU激活函数在残差块外部，以确保仅在残差路径有贡献时才进行非线性变换

    def forward(self, x):
        # 残差路径的输出
        residual = self.residual(x)

        # 主路径输出
        shortcut = self.shortcut(x)

        # 将残差路径和主路径的输出相加，并经过ReLU激活函数
        out = shortcut + residual
        out = torch.nn.functional.leaky_relu(out, 0.1)
        return out





"""
10.ResNet的复现
简介：ResNet最突出的特点是采用了残差学习（residual learning）的思想。这种思想通过引入残差块（Residual Block），跳过网络的某些层或部分，直接将输入传到后面的层中。残差块的设计使得模型可以学习到残差，即剩余的映射，而不仅仅是对输入的变换。通过引入残差连接，ResNet使得信息可以更容易地在网络中传播，即使网络非常深，梯度也可以通过残差连接直接传递到较浅层，从而避免了梯度消失的问题。

"""
class ResNet(torch.nn.Module):
    def __init__(self, in_channels=3, num_classes=1000):
        super(ResNet,self).__init__()

        # 第一个模块：7x7的卷积层+3x3的最大汇聚层
        self.block1 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, 64, kernel_size=7, stride=2, padding=3),
            torch.nn.BatchNorm2d(64),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=3, stride=2, padding=1)
        )

        # 第二个模块~第五个模块都是有两个残差块组成
        self.block2 = torch.nn.Sequential(*self._resnet_block(64,64,2,True))
        self.block3 = torch.nn.Sequential(*self._resnet_block(64,128,2))
        self.block4 = torch.nn.Sequential(*self._resnet_block(128,256,2))
        self.block5 = torch.nn.Sequential(*self._resnet_block(256,512,2))

        #  特征提取
        self.features = torch.nn.Sequential(
            self.block1,self.block2,self.block3,self.block4,self.block5,
            torch.nn.AdaptiveAvgPool2d((1, 1)),
        )

        # 分类器
        self.classifier = torch.nn.Sequential(
            torch.nn.Flatten(),
            torch.nn.Linear(512,num_classes)
        )


    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x

    # resnet块
    def _resnet_block(self, in_channels, out_channels, num_residual, fist_block=False):
        blk = []
        for i in range(num_residual):
            if i==0 and not fist_block:
                blk.append(ResidualBlock(in_channels, out_channels, strides=2))
            else:
                blk.append(ResidualBlock(out_channels, out_channels))
        return blk




"""
11.DenseBlock的复现
简介：一个稠密块由多个卷积块组成，每个卷积块使用相同数量的输出通道。前向传播中，将每个卷积块的输入与输出在通道上连接。
"""
class DenseBlock(torch.nn.Module):
    def __init__(self, in_channels, out_channels, num_convs):
        super(DenseBlock, self).__init__()
        self.net = torch.nn.ModuleList([self._conv_block(in_channels + i * out_channels, out_channels) for i in range(num_convs)])

    #批量生成规范层、激活层和卷积层
    def _conv_block(self, in_channels, num_channels):
        return torch.nn.Sequential(
            torch.nn.BatchNorm2d(in_channels),
            torch.nn.ReLU(inplace=True),
            torch.nn.Conv2d(in_channels, num_channels, kernel_size=3, padding=1)
        )


    def forward(self, x):
        # 实现DenseBlock中将输出与输入相连
        features = [x]
        for layer in self.net:
            out = layer(torch.cat(features, dim=1))
            features.append(out)
        return torch.cat(features, dim=1) # 将所有输出连接在一起







"""
12.TransitionBlock
简述：过渡层，每一个稠密块都会增加通道数，因此使用过多会过于复杂，而过度层可以控制模型复杂度，通过1x1卷积层来减小通道数，并使用步幅为2的平均汇聚层减半高度和宽度
"""
class TransitionBlock(torch.nn.Module):
    def __init__(self, in_channels, out_channels):
        super(TransitionBlock, self).__init__()
        self.features = torch.nn.Sequential(
            torch.nn.BatchNorm2d(in_channels),torch.nn.ReLU(),
            torch.nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=1, padding=0), # 使用1x1卷积进行特征通道数的调整
            torch.nn.AvgPool2d(kernel_size=4, stride=2, padding=1)  # 使用平均池化进行特征尺寸的减半
        )



    def forward(self, x):
        return self.features(x)







"""
13.DenseNet
简述：使用4个稠密块，每个稠密块可以设定包含多少个卷积层，稠密块使用过度层来调整特征图的大小
"""
class DenseNet(torch.nn.Module):
    def __init__(self, in_channels=3, num_classes=1000,):
        super(DenseNet, self).__init__()
        # num_channels为当前的通道数，growth_rate增长率，num_convs_in_dense_block为四个稠密块包含的卷积层数
        self.num_channels = 64
        self.growth_rate = 32
        self.num_convs_in_dense_block = [4, 4, 4, 4]
        self.blk = []

        #第一个模块使用单卷积层和最大汇聚层
        self.block1 = torch.nn.Sequential(
            torch.nn.Conv2d(in_channels, self.num_channels, kernel_size=3, stride=2, padding=3),
            torch.nn.BatchNorm2d(self.num_channels),
            torch.nn.ReLU(),
            torch.nn.MaxPool2d(kernel_size=2, stride=2, padding=0) # 使用最大池化进行下采样
        )




        # 使用4个稠密块，稠密块里的卷积层通道数即增长率设为32，所以每个稠密块将增加128个通道
        for i, num_convs in enumerate(self.num_convs_in_dense_block):
            # 添加一个稠密块
            self.blk.append(DenseBlock(self.num_channels, self.growth_rate, num_convs))

            # 上一个稠密块的输出通道数
            self.num_channels += self.growth_rate * num_convs

            # 在稠密块直接添加一个过度层，使通道数减半
            if i != len(self.num_convs_in_dense_block) - 1:
                self.blk.append(TransitionBlock(self.num_channels, self.num_channels // 2))
                self.num_channels = self.num_channels // 2


        self.features = torch.nn.Sequential(self.block1, *self.blk, torch.nn.BatchNorm2d(self.num_channels), torch.nn.ReLU(), torch.nn.AdaptiveAvgPool2d((1, 1)))

        self.classifier = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(self.num_channels, num_classes))


    def forward(self, x):
        x = self.features(x)
        x = self.classifier(x)
        return x





