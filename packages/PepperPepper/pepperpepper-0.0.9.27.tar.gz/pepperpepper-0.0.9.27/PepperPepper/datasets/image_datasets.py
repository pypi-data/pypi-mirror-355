from ..environment import torch,torchvision




"""  
1.load_data_minist(batch_size=256, resize=None, train=True, download=True)
   加载MNIST数据集  

   参数:  
   batch_size (int): 每个batch的大小  
   train (bool): 如果为True，则加载训练集；如果为False，则加载测试集  
   download (bool): 如果为True，则从互联网上下载数据集（如果尚未下载）  

   返回:  
   dataloader (torch.tools.data.DataLoader): 数据加载器  
   
    # 加载训练集  
    train_loader = load_data_mnist(batch_size=64, train=True)  
  
    # 加载测试集  
    test_loader = load_data_mnist(batch_size=64, train=False)
   
"""
def load_data_minist(batch_size=256, resize=None, train=True, download=True):
    # 定义数据转换
    trans = [torchvision.transforms.ToTensor()]
    if resize:
        trans.insert(0,torchvision.transforms.Resize(resize))
    trans = torchvision.transforms.Compose(trans)

    # 根据train参数选择数据集
    if train:
        mnist_dataset = torchvision.datasets.MNIST(root='./data', train=True, transform=trans, download=download)
    else:
        mnist_dataset = torchvision.datasets.MNIST(root='./data', train=False, transform=trans, download=download)

    # 创建数据加载器
    dataloader = torch.utils.data.DataLoader(mnist_dataset, batch_size=batch_size, shuffle=True)

    return dataloader











"""  
2.load_data_fashion_mnist(batch_size=256, resize=None, train=True, download=True)
    加载Fashion-MNIST数据集  

    参数:  
    batch_size (int): 每个batch的大小  
    train (bool): 如果为True，则加载训练集；如果为False，则加载测试集  
    download (bool): 如果为True，则从互联网上下载数据集（如果尚未下载）  

    返回:  
    dataloader (torch.tools.data.DataLoader): 数据加载器  
    
    
    # 加载训练集  
    train_loader = load_data_fashion_mnist(batch_size=64, train=True)  
  
    # 加载测试集  
    test_loader = load_data_fashion_mnist(batch_size=64, train=False)
"""
def load_data_fashion_mnist(batch_size=256, resize=None, train=True, download=True):
    # 定义数据转换
    trans = [torchvision.transforms.ToTensor()]
    if resize:
        trans.insert(0,torchvision.transforms.Resize(resize))
    trans = torchvision.transforms.Compose(trans)

    # 根据train参数选择数据集
    if train:
        fashion_mnist_dataset = torchvision.datasets.FashionMNIST(root='./data', train=True, transform=trans, download=download)
    else:
        fashion_mnist_dataset = torchvision.datasets.FashionMNIST(root='./data', train=False, transform=trans, download=download)

    # 创建数据加载器
    dataloader = torch.utils.data.DataLoader(fashion_mnist_dataset, batch_size=batch_size, shuffle=True)

    return dataloader






