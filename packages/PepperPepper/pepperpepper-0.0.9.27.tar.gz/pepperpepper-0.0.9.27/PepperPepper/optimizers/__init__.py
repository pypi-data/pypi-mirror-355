# optimizers 模块
# 功能：包含优化器的实现或扩展。
# 子模块/文件：
# custom_optimizer.py：用户自定义优化器的示例或模板。
# optimizers/__init__.py
# 导入 optimizers 子包中的各个模块
# from . import custom_optimizer

from .custom_optimizer import grad_clipping,sgd
#
# # __all__ 变量定义了当使用 from optimizers import * 时导入哪些对象
# # 注意：通常不推荐使用 from package import *
__all__ = [
     'grad_clipping',
     'sgd'
]