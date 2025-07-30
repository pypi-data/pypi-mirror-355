# callbacks 模块
# 功能：包含训练过程中的回调函数，用于实现如学习率调整、模型保存等功能。
# 子模块/文件：
# learning_rate_scheduler.py：学习率调整策略的实现。
# custom_callback.py：用户自定义回调函数的示例或模板。
# trainer.py:训练器


# callbacks/__init__.py

from .custom_callback import save_best_model
from .custom_callback import load_best_model
from .trainer import train_epoch_ch8,predict_ch8,train_ch8, train_seq2seq, predict_seq2seq

from .config_setting import get_sch_config, get_opt_config, get_scheduler, get_optimizer, set_seed
# # __all__ 变量定义了当使用 from callback import * 时导入哪些对象
# # 注意：通常不推荐使用 from package import *
__all__ = [
    'save_best_model', 'load_best_model',
    'train_epoch_ch8', 'predict_ch8', 'train_ch8', 'train_seq2seq', 'predict_seq2seq',
    'get_sch_config',
    'get_opt_config',
    'get_scheduler',
    'get_optimizer',
    'set_seed'
]