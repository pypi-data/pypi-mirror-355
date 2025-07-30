# models 模块
# 功能：包含各种深度学习模型的实现。
# 子模块/文件：
# cnn.py：卷积神经网络（CNN）相关模型的实现。
# rnn.py：循环神经网络（RNN）相关模型的实现。
# transformer.py：Transformer模型及其变体的实现。
# custom_model.py：用户自定义模型的示例或模板。
# YOLO.py:定义yolo系列算法。

# models/__init__.py
# 如果需要，您可以直接导入这些模块中的特定类或函数
from .cnn import LeNet5, AlexNet, VGGBlock, VGG16, MLPConv, NiNBlock, NiN, InceptionBlockV1, GoogLeNet, ResidualBlock, ResNet, DenseBlock, TransitionBlock, DenseNet

from .rnn import RNNModel, Seq2SeqEncoder, Seq2SeqDecoder

from .YOLO import YOLOv3_104

from .model_module import Encoder, Decoder, EncoderDecoder, AttentionDecoder, Seq2SeqAttentionDecoder

from .transformer import NWKernelRegression, AdditiveAttention, DotProductAttention,MultiHeadAttention

from .custom_model import PositionalEncoding

from .Gan import Generator, Discriminator

from . import TransUNet

from . import mixture_of_experts






# __all__ 变量定义了当使用 from models import * 时导入哪些对象
# 注意：通常不推荐使用 from package import *
__all__ = [
   'LeNet5', 'AlexNet', 'VGGBlock', 'VGG16', 'MLPConv', 'NiNBlock', 'NiN', 'InceptionBlockV1', 'GoogLeNet', 'ResidualBlock', 'ResNet', 'DenseBlock', 'TransitionBlock', 'DenseNet',
   'RNNModel', 'Seq2SeqEncoder', 'Seq2SeqDecoder',
   'YOLOv3_104',
   'Encoder', 'Decoder', 'EncoderDecoder','AttentionDecoder','Seq2SeqAttentionDecoder',
   'NWKernelRegression', 'AdditiveAttention', 'DotProductAttention','MultiHeadAttention',
   'PositionalEncoding',
   'Generator', 'Discriminator',
   'TransUNet',
   'mixture_of_experts'
]













