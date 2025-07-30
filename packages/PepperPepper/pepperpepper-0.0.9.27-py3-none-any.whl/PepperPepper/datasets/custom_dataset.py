
from ..environment import np, pd, plt,torch,torchvision, random

"""  
1.load_arrays(data_arrays, batch_size, is_train=True)
    构建一个 PyTorch 数据迭代器。

    Parameters:
    - data_arrays (tuple of torch.Tensor): 包含输入数据和标签数据的元组。
    - batch_size (int): 每个批次的样本数量。
    - is_train (bool, optional): 指定是否为训练模式，默认为 True。

    Returns:
    - torch.tools.data.DataLoader: PyTorch 数据加载器对象，用于迭代数据批次。
"""
def load_arrays(data_arrays, batch_size, is_train=True):
    # 创建一个 PyTorch 数据集对象，其中包含输入数据和标签数据
    dataset = torch.utils.data.TensorDataset(*data_arrays)

    # 创建一个 PyTorch 数据加载器对象，用于批次化地加载数据
    # 参数 shuffle 指定是否在每个 epoch 开始前打乱数据顺序
    return torch.utils.data.DataLoader(dataset, batch_size=batch_size, shuffle=is_train)





