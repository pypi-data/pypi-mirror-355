# custom_deep_learning/__init__.py
from . import core
from . import models
from . import layers
from . import datasets
from . import optimizers
from . import losses
from . import callbacks
from . import examples
# from . import tools
from . import core
from . import environment
from . import IRSTD
from . import tools
from . import RL
# from . import OD
import sys
__all__ = ['core', 'layers', 'datasets', 'optimizers', 'losses', 'callbacks', 'examples', 'tools','models', 'environment', 'IRSTD', 'RL']

"""
包名: PepperPepper

模块:
core 模块
功能：包含包的核心功能和基础类。
子模块/文件：
base_model.py：定义基础模型类，提供模型初始化、保存、加载等基础功能。
tools.py：包含一些通用的工具函数，如数据处理、模型评估等。
text.tools: 负责处理文本数据相关的功能，例如词表构建、词频统计等。
image_utils: 负责处理图像数据相关的功能。
transforms: 负责实现数据增强的相关功能。

models 模块
功能：包含各种深度学习模型的实现。
子模块/文件：
cnn.py：卷积神经网络（CNN）相关模型的实现。
rnn.py：循环神经网络（RNN）相关模型的实现。
transformer.py：Transformer模型及其变体的实现。
custom_model.py：用户自定义模型的示例或模板。
YOLO.py:定义yolo系列算法。

layers 模块
功能：包含自定义的神经网络层或模块。
子模块/文件：
attention.py：实现各种注意力机制层。
custom_layer.py：用户自定义层的示例或模板。

datasets 模块
功能：包含数据集的加载、预处理和增强功能。
子模块/文件：
image_datasets.py：图像数据集的处理，如CIFAR、ImageNet等。
text_datasets.py：文本数据集的处理，如IMDB、WikiText等。
custom_dataset.py：用户自定义数据集的示例或模板。
dataset_utils.py:数据集工具模块，主要定义数据集处理工具.

optimizers 模块
功能：包含优化器的实现或扩展。
子模块/文件：
custom_optimizer.py：用户自定义优化器的示例或模板。

losses 模块
功能：包含损失函数的实现或扩展。
子模块/文件：
custom_loss.py：用户自定义损失函数的示例或模板。

callbacks 模块
功能：包含训练过程中的回调函数，用于实现如学习率调整、模型保存等功能。
子模块/文件：
learning_rate_scheduler.py：学习率调整策略的实现。
custom_callback.py：用户自定义回调函数的示例或模板。
trainer.py:训练器

examples 模块
功能：包含使用custom_deep_learning包进行深度学习任务的示例代码。
子模块/文件：
image_classification.py：使用CNN进行图像分类的示例。
text_generation.py：使用Transformer进行文本生成的示例。
custom_task.py：用户自定义任务的示例。

IRSTD 模块
功能：包含IRSTD任务方向的模型与论文，数据集的处理等相关操作在此。

"""