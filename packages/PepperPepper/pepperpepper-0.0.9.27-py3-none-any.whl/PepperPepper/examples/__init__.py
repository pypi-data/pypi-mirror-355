# examples 模块
# 功能：包含使用custom_deep_learning包进行深度学习任务的示例代码。
# 子模块/文件：
# image_classification.py：使用CNN进行图像分类的示例。
# text_generation.py：使用Transformer进行文本生成的示例。
# custom_task.py：用户自定义任务的示例。











# examples/__init__.py

# 这个文件是 examples 包的初始化文件。
# 它主要用于组织和文档化 examples 包中的示例脚本。
# 通常，这里不会定义任何函数或类。

# 如果需要，可以在这里添加一些描述或文档字符串。
"""
This package contains example scripts demonstrating various functionalities
of the custom_deep_learning package.

Available examples:
- mnist_example.py: A script showing how to train a model on the MNIST dataset.
- cifar10_example.py: An example of training a model on the CIFAR-10 dataset.
- custom_data_example.py: A script for training a model on a custom dataset.

To run an example, use the command line:
python -m custom_deep_learning.examples.mnist_example
"""

# 如果需要，也可以在这里导入其他模块或包，但通常这不是必需的。

# 注意：通常情况下，这个文件中不会有 __all__ 变量的定义，
# 因为我们并不希望从 examples 包中直接导入任何对象。