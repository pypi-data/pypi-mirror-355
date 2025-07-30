from ..environment import torch



"""
    1.save_best_model(model, optimizer, path)
    保存模型的最佳参数和优化器状态到指定路径。

    Args:
        model (nn.Module): 神经网络模型，包含训练得到的最佳参数。
        optimizer (torch.optim.Optimizer): 优化器对象，包含优化器状态（如学习率等）。
        path (str): 文件路径，用于保存模型参数和优化器状态。

    Returns:
        None: 该函数没有返回值，但会在指定路径下保存模型参数和优化器状态。

"""
def save_best_model(model, optimizer, path):
    torch.save({'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict()}, path)









"""  
2.load_best_model(path, model, optimizer=None)
    从指定路径加载模型的最佳参数和优化器状态。  

    Args:  
        path (str): 文件路径，包含要加载的模型参数和优化器状态。  
        model (nn.Module): 神经网络模型，用于加载参数。  
        optimizer (torch.optim.Optimizer, optional): 优化器对象，用于加载优化器状态。默认为None，如果提供则会加载优化器状态。  

    Returns:  
        tuple: 包含加载了参数的模型（nn.Module）和（如果提供了）加载了状态的优化器（torch.optim.Optimizer）。  
"""
def load_best_model(path, model, optimizer=None):
    checkpoint = torch.load(path)
    model.load_state_dict(checkpoint['model_state_dict'])

    if optimizer is not None:
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])

    return model, optimizer if optimizer is not None else None


