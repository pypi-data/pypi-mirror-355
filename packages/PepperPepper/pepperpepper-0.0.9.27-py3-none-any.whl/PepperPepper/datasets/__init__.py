"""
datasets 模块
功能：包含数据集的加载、预处理和增强功能。
子模块/文件：
image_datasets.py：图像数据集的处理，如CIFAR、ImageNet等。
text_datasets.py：文本数据集的处理，如IMDB、WikiText等。
custom_dataset.py：用户自定义数据集的示例或模板。
dataset_utils.py:数据集工具模块，主要定义数据集处理工具.
"""


# 如果需要，可以直接导入这些模块中的特定类或函数
from .image_datasets import load_data_minist, load_data_fashion_mnist

from .text_datasets import read_time_machine, load_corpus_time_machine, SeqDataLoader_time_machine, load_data_time_machine, read_data_nmt, preprocess_nmt, tokenize_nmt, load_data_nmt

from .custom_dataset import load_arrays

from .dataset_utils import download, tokenize, Vocab, seq_data_iter_random, seq_data_iter_sequential, download_extract, truncate_pad, sequence_mask, masked_softmax, get_img_norm_cfg

from .get_all_images import get_all_images

from .collect_image_names import collect_image_names

from .Analyze_Connected_Pixels import analyze_connected_pixels


from .Translate_COCO import convert_txt_to_coco, convert_voc_to_coco
# from .cifar10_dataset import load_cifar10_data
# from .custom_dataset import load_custom_data
#
# __all__ 变量定义了当使用 from datasets import * 时导入哪些对象
# 注意：通常不推荐使用 from package import *
__all__ = [
    'load_data_minist',
    'load_data_fashion_mnist',
    'read_time_machine',
    'load_corpus_time_machine',
    'SeqDataLoader_time_machine',
    'load_data_time_machine',
    'read_data_nmt',
    'preprocess_nmt',
    'tokenize_nmt',
    'load_data_nmt',
    'load_arrays',
    'download',
    'tokenize',
    'Vocab',
    'seq_data_iter_random',
    'seq_data_iter_sequential',
    'download_extract',
    'truncate_pad',
    'sequence_mask','masked_softmax','get_all_images', 'get_img_norm_cfg',
    'collect_image_names','analyze_connected_pixels',
    'convert_txt_to_coco', 'convert_voc_to_coco'
]


