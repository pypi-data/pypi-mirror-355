from ..environment import torch

"""
1.grad_clipping(net, theta)
    定义一个函数来裁剪模型的梯度， 模型是从零开始实现的模型或由高级API构建的模型。 我们在此计算了所有模型参数的梯度的范数。
    parameter:
    - net: 算法模型
    - theta: 更新参数
    
    Returns:
    - None
"""
def grad_clipping(net, theta):
    """裁剪梯度"""
    if isinstance(net, torch.nn.Module):
        params = [p for p in net.parameters() if p.requires_grad]
    else:
        params = net.params

    norm = torch.sqrt(sum(torch.sum((p.grad ** 2)) for p in params))
    if norm > theta:
        for param in params:
            param.grad[:] *= theta / norm


'''
2.sgd(params, lr, batch_size)
    小批量随机梯度下降算法。

    Parameters:
    - params (iterable): 模型参数的迭代器。
    - lr (float): 学习率。
    - batch_size (int): 小批量大小。
'''
def sgd(params, lr, batch_size):
    """Minibatch stochastic gradient descent.

    Defined in :numref:`sec_utils`"""
    with torch.no_grad():
        for param in params:
            param -= lr * param.grad / batch_size
            param.grad.zero_()





