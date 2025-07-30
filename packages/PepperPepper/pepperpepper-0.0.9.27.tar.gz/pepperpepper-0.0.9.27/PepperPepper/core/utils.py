from ..environment import np, pd, plt, torch, torchvision, cv2, backend_inline, display, time
from ..callbacks import save_best_model


"""  
1.evaluate_accuracy_gpu(net, data_iter, device=None)
评估模型在给定数据集上的准确性，并将数据加载到指定的GPU设备上（如果可用）。  

Args:  
    net (torch.nn.Module): 需要评估的神经网络模型。  
    data_iter (Iterable): 数据迭代器，提供图像和标签的批量数据。  
    device (torch.device, optional): 要将数据加载到的设备。默认为None，表示如果GPU可用则使用第一个GPU，否则使用CPU。  

Returns:  
    float: 模型的准确性（正确预测的样本数占总样本数的比例）。  

"""
def evaluate_accuracy_gpu(net, data_iter, device=None):
    if device is None and torch.cuda.is_available():
        device = torch.device('cuda')  # 如果未指定设备且GPU可用，则使用GPU
    elif device is None:
        device = torch.device('cpu')  # 如果未指定设备且GPU不可用，则使用CPU


    net.eval()  # 设置为评估模式
    acc_sum = 0
    num_examples = 0

    with torch.no_grad():
        for images, labels in data_iter:
            # 将图像和标签移动到指定的设备
            images, labels = images.to(device), labels.to(device)
            # 前向传播，获取预测结果
            outputs = net(images)
            # 获取预测结果中概率最大的类别作为预测类别
            _, predicted  = torch.max(outputs, 1)
            # 累加样本数量和正确预测的样本数量
            num_examples += labels.size(0)
            acc_sum += (predicted == labels).sum().item()

    # 返回准确率
    return acc_sum / num_examples



""" 
    2.train_custom(model, train_loader, valid_loader, epochs, lr, device, model_path)
    自定义的模型训练函数，包含保存最佳模型的功能  

    参数:  
        model (nn.Module): 待训练的神经网络模型  
        train_loader (DataLoader): 训练数据加载器  
        valid_loader (DataLoader): 验证数据加载器  
        epochs (int): 训练轮数  
        lr (float): 学习率  
        device (torch.device): 设备类型（CPU或GPU）  
        model_path (str): 最佳模型保存路径  

    返回:  
        None  
"""

def train_custom(model, train_loader, valid_loader, epochs, lr, device, model_path):
    # 用于评估模型准确率的函数，同时返回验证损失和准确率
    def evaluate_accuracy(model, valid_loader, criterion, device):
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        with torch.no_grad():
            for images, labels in valid_loader:
                images, labels = images.to(device), labels.to(device)
                outputs = model(images)
                loss = criterion(outputs, labels)
                val_loss += loss.item() * images.size(0)
                _, predicted = torch.max(outputs, 1)
                total += labels.size(0)
                correct += (predicted == labels).sum().item()
        val_acc = 100 * correct / total
        return val_loss / total, val_acc

        # 初始化模型参数，使用xavier方法
    def init_weights(m):
        if isinstance(m, (torch.nn.Linear, torch.nn.Conv2d)):  # 使用isinstance替代type判断
            torch.nn.init.xavier_uniform_(m.weight)
    model.apply(init_weights)


    # 将模型移至指定设备
    model.to(device)
    model.train()

    # 定义优化器和损失函数
    optimizer = torch.optim.SGD(model.parameters(), lr=lr, momentum=0.9)
    criterion  = torch.nn.CrossEntropyLoss()

    best_acc = 0.0
    history = {'loss': [], 'val_loss': [], 'acc': [], 'val_acc': []}

    for epoch in range(epochs):
        model.train(True)
        running_loss = 0.0
        correct = 0
        total = 0


        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, predicted = torch.max(outputs, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()

        train_acc = 100 * correct / total
        val_loss, val_acc = evaluate_accuracy(model, valid_loader, criterion, device)
        history['loss'].append(running_loss / total)
        history['val_loss'].append(val_loss)
        history['acc'].append(train_acc)
        history['val_acc'].append(val_acc)

        # 打印训练和验证的统计信息
        print(
            f'Epoch {epoch + 1}/{epochs}, Loss: {running_loss / total:.4f}, Train Acc: {train_acc:.2f}%, Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%')

        # 如果当前验证准确率是最佳的，则保存模型
        if val_acc > best_acc:
            best_acc = val_acc
            save_best_model(model, optimizer, model_path)
            print(f"Model improved and saved to {model_path}")






"""
3.try_gpu(i=0) 
    如果存在，则返回指定的GPU设备，否则返回CPU设备。  
  
    Args:  
        i (int, optional): GPU设备的索引。默认为0。  
  
    Returns:  
        torch.device: 指定的GPU设备或CPU设备。 

"""
def try_gpu(i=0):
    # @save 注解：这个通常用于Jupyter Notebook中，用于保存函数定义到某个地方，但在这里它对代码执行没有影响。
    """如果存在，则返回gpu(i)，否则返回cpu()"""
    # 检查是否有足够的GPU设备数量，至少要比指定的索引i大1
    if torch.cuda.device_count() >= i + 1:
        # 如果有足够的GPU设备，则返回指定索引i的GPU设备
        return torch.device(f'cuda:{i}')
        # 如果没有足够的GPU设备或没有检测到GPU，则返回CPU设备
    return torch.device('cpu')



"""  
4.try_all_gpus()
   返回所有可用的GPU设备列表，如果没有GPU，则返回包含CPU设备的列表。  

   Returns:  
       list[torch.device]: 所有GPU设备或CPU设备的列表。  
"""

def try_all_gpus():
    # @save 注解：同样地，这个注解通常用于Jupyter Notebook中，用于保存函数定义。
    """返回所有可用的GPU，如果没有GPU，则返回[cpu(),]"""
    # 初始化一个空列表用于存储所有GPU设备
    devices = []
    # 遍历所有检测到的GPU设备
    for i in range(torch.cuda.device_count()):
        # 将每个GPU设备添加到列表中
        devices.append(torch.device(f'cuda:{i}'))
        # 如果devices列表不为空（即存在GPU设备），则返回该列表
    # 否则，返回只包含CPU设备的列表
    return devices if devices else [torch.device('cpu')]




'''
5.use_svg_display()
    目的是在 Jupyter 笔记本中使用 SVG 格式来显示绘图。
'''
def use_svg_display():
    """
    Use the svg format to display a plot in Jupyter.

    """
    backend_inline.set_matplotlib_formats('svg')





'''
6.set_figsize(figsize=(3.5, 2.5))
    设置 Matplotlib（一个流行的 Python 绘图库）中图形的尺寸。
    
    Args:
        figsize:设置图形的具体尺寸，默认为(3.5, 2.5)
'''
def set_figsize(figsize=(3.5, 2.5)):
    """Set the figure size for matplotlib.

    Defined in :numref:`sec_calculus`"""
    use_svg_display()
    plt.rcParams['figure.figsize'] = figsize




'''
7.set_axes(axes, xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
    设置 Matplotlib 图形中的坐标轴的各种属性。
    
    Args:
        axes (matplotlib.axes.Axes): 需要修改的坐标轴对象。
        xlabel (str): x轴的标签。 
        ylabel (str): y轴的标签。 
        xlim (tuple): x轴的限制范围，为一个元组(min, max)。 
        ylim (tuple): y轴的限制范围，为一个元组(min, max)。 
        xscale (str): x轴的刻度类型，如'linear', 'log'。 
        yscale (str): y轴的刻度类型，如'linear', 'log'。 
        legend (list or tuple, optional): 一个包含元组的列表或元组，其中每个元组包含一个图例句柄和标签。  
        
'''
def set_axes(axes, xlabel, ylabel, xlim, ylim, xscale, yscale, legend):
    """Set the axes for matplotlib.

    Defined in :numref:`sec_calculus`"""
    axes.set_xlabel(xlabel), axes.set_ylabel(ylabel)
    axes.set_xscale(xscale), axes.set_yscale(yscale)
    axes.set_xlim(xlim),     axes.set_ylim(ylim)
    if legend:
        axes.legend(legend)
    axes.grid()



'''
8.plot(X, Y=None, xlabel=None, ylabel=None, legend=[], xlim=None,
         ylim=None, xscale='linear', yscale='linear',
         fmts=('-', 'm--', 'g-.', 'r:'), figsize=(3.5, 2.5), axes=None)
    绘制数据点。  
  
    参数:  
        X (tensor, list, or iterable): 数据点x的集合。如果只有一个数据系列，则可以为1D tensor、list或其他可迭代对象。  
        Y (tensor, list, or iterable, optional): 数据点y的集合。如果X有多个数据系列，则Y也应有相应数量的数据系列。默认为None，表示X只包含y数据。  
        xlabel (str, optional): x轴的标签。默认为None。  
        ylabel (str, optional): y轴的标签。默认为None。  
        legend (list, optional): 图例的标签列表。默认为空列表。  
        xlim (tuple, optional): x轴的范围限制。默认为None。  
        ylim (tuple, optional): y轴的范围限制。默认为None。  
        xscale (str, optional): x轴的刻度类型，如'linear', 'log'。默认为'linear'。  
        yscale (str, optional): y轴的刻度类型，如'linear', 'log'。默认为'linear'。  
        fmts (tuple, optional): 绘图格式的元组，包含不同数据系列的线条样式。默认为('-', 'm--', 'g-.', 'r:')。  
        figsize (tuple, optional): 图形的大小（宽度，高度）。默认为(3.5, 2.5)。  
        axes (matplotlib.axes.Axes, optional): 坐标轴对象。如果为None，则使用当前活动的坐标轴。默认为None。  
  
    返回:  
        None: 此函数不返回任何值，而是直接在给定的坐标轴上绘制图形。
'''
def plot(X, Y=None, xlabel=None, ylabel=None, legend=[], xlim=None,
         ylim=None, xscale='linear', yscale='linear',
         fmts=('-', 'm--', 'g-.', 'r:'), figsize=(3.5, 2.5), axes=None):
    """Plot data points.

    Defined in :numref:`sec_calculus`"""

    def has_one_axis(X):  # True if X (tensor or list) has 1 axis
        return (hasattr(X, "ndim") and X.ndim == 1 or isinstance(X, list)
                and not hasattr(X[0], "__len__"))

    if has_one_axis(X): X = [X]
    if Y is None:
        X, Y = [[]] * len(X), X
    elif has_one_axis(Y):
        Y = [Y]
    if len(X) != len(Y):
        X = X * len(Y)

    set_figsize(figsize)
    if axes is None:
        axes = plt.gca()
    axes.cla()
    for x, y, fmt in zip(X, Y, fmts):
        axes.plot(x,y,fmt) if len(x) else axes.plot(y,fmt)
    set_axes(axes, xlabel, ylabel, xlim, ylim, xscale, yscale, legend)




'''
9.evaluate_loss(net, data_iter, loss)
    在给定的数据集上评估模型的损失。  
  
    参数:  
        net (nn.Module): 需要评估的神经网络模型。  
        data_iter (DataLoader): 数据迭代器，用于遍历数据集。  
        loss (function): 损失函数，用于计算预测值与实际值之间的损失。  
  
    返回:  
        float: 平均损失值，即所有样本损失的总和除以样本数量。 
'''
def evaluate_loss(net, data_iter, loss):
    metric = Accumulator(2)  # Sum of losses, no. of examples
    for X, y in data_iter:
        out = net(X)
        y = torch.reshape(y, out.shape)
        l = loss(out, y)
        metric.add(l.sum(), l.numel())
    return metric[0] / metric[1]


'''
10. class Accumulator
    用于对 `n` 个变量的累加值进行累积的类。
'''
class Accumulator:
    """For accumulating sums over `n` variables."""
    def __init__(self, n):
        """
        初始化累加器，为 `n` 个变量创建一个初始值全为 0.0 的列表。

        参数:
            n (int): 需要累加的变量的数量。

        定义在: :numref:`sec_utils`（这是一个假设的章节引用）
        """
        self.data = [0.0] * n

    def add(self, *args):
        """
        将给定的参数值累加到对应的变量上。

        参数:
            *args: 任意数量的位置参数，表示要累加到每个变量的值。

        注意：此方法的参数数量必须与初始化时指定的变量数量 `n` 匹配。
        """
        self.data = [a + float(b) for a, b in zip(self.data, args)]

    def reset(self):
        """
        重置累加器的值，将所有变量的值重置为 0.0。
        """
        self.data = [0.0] * len(self.data)

    def __getitem__(self, idx):
        """
        获取指定索引处的累加值。

        参数:
            idx (int): 要获取的累加值的索引。

        返回:
            float: 索引为 `idx` 的变量的累加值。
        """
        return self.data[idx]




'''
11.Timer
    记录多次运行时间的计时器类。
    该类可以记录多次运行的时间，并提供计算平均时间、总时间以及累积时间的功能。
    
    Parameter:
    - None
    
    Attributes:
    - times (list): 用于存储每次运行的时间。
    - tik (float): 记录每次开始计时的时间戳。
'''
class Timer:
    """Record multiple running times."""
    def __init__(self):
        """初始化计时器对象。

        初始化计时器对象时，创建一个空的时间列表并启动计时器。
        """
        """Defined in :numref:`sec_minibatch_sgd`"""
        self.times = []
        self.start()

    def start(self):
        """Start the timer."""
        """开始计时。

        记录当前时间作为开始时间。
        """
        self.tik = time.time()

    def stop(self):
        """Stop the timer and record the time in a list."""
        """停止计时并记录时间。

        计算从开始计时到当前时间的时间差，并将其添加到时间列表中，然后返回该时间差。
        """
        self.times.append(time.time() - self.tik)
        return self.times[-1]

    def avg(self):
        """Return the average time."""
        """计算平均时间。

        返回所有运行时间的平均值。
        """
        return sum(self.times) / len(self.times)

    def sum(self):
        """Return the sum of time."""
        """计算总时间。

        返回所有运行时间的总和。
        """
        return sum(self.times)

    def cumsum(self):
        """Return the accumulated time."""
        """计算累积时间。

        返回所有运行时间的累积和。
        """
        return np.array(self.times).cumsum().tolist()




'''
12.Animator
    用于在动画中绘制数据的类。
    Parameters:
    - xlabel (str): x 轴的标签。
    - ylabel (str): y 轴的标签。
    - legend (list): 图例。
    - xlim (tuple): x 轴的范围。
    - ylim (tuple): y 轴的范围。
    - xscale (str): x 轴的缩放方式。
    - yscale (str): y 轴的缩放方式。
    - fmts (tuple): 绘图格式。
    - nrows (int): 子图的行数。
    - ncols (int): 子图的列数。
    - figsize (tuple): 图的尺寸。
'''
class Animator:
    """For plotting data in animation."""
    def __init__(self, xlabel=None, ylabel=None, legend=None, xlim=None,
                 ylim=None, xscale='linear', yscale='linear',
                 fmts=('-', 'm--', 'g-.', 'r:'), nrows=1, ncols=1,
                 figsize=(3.5, 2.5)):
        """Defined in :numref:`sec_utils`"""
        # Incrementally plot multiple lines
        if legend is None:
            legend = []
        use_svg_display()
        self.fig, self.axes = plt.subplots(nrows, ncols, figsize=figsize)
        if nrows * ncols == 1:
            self.axes = [self.axes, ]
        # Use a lambda function to capture arguments
        self.config_axes = lambda: set_axes(
            self.axes[0], xlabel, ylabel, xlim, ylim, xscale, yscale, legend)
        self.X, self.Y, self.fmts = None, None, fmts

    def add(self, x, y):
        """
        向图中添加数据点。

        Parameters:
            x (list): x 值。
            y (list): y 值。
        """
        # Add multiple data points into the figure
        if not hasattr(y, "__len__"):
            y = [y]
        n = len(y)
        if not hasattr(x, "__len__"):
            x = [x] * n
        if not self.X:
            self.X = [[] for _ in range(n)]
        if not self.Y:
            self.Y = [[] for _ in range(n)]
        for i, (a, b) in enumerate(zip(x, y)):
            if a is not None and b is not None:
                self.X[i].append(a)
                self.Y[i].append(b)
        self.axes[0].cla()
        for x, y, fmt in zip(self.X, self.Y, self.fmts):
            self.axes[0].plot(x, y, fmt)
        self.config_axes()
        display.display(self.fig)
        display.clear_output(wait=True)



'''
13.show_heatmaps(matrices, xlabel, ylabel, titles=None, figsize=(2.5, 2.5),cmap='Reds')
    显示矩阵热图
    Parameters:
        matrices (List[ndarray] or ndarray): 要显示的矩阵列表或单个矩阵（如果为单个矩阵，则视为二维列表中的一个元素）。  
        xlabel (str): x轴的标签。  
        ylabel (str): y轴的标签。  
        titles (List[str], optional): 每个子图的标题列表。如果为None，则不显示标题。  
        figsize (tuple, optional): 图形的大小（宽，高）。默认为(2.5, 2.5)。  
        cmap (str, optional): 用于热图的颜色映射。默认为'Reds'。
        
    Returns:  
        None: 该函数没有返回值，而是直接显示热图。
'''
#@save
def show_heatmaps(matrices, xlabel, ylabel, titles=None, figsize=(2.5, 2.5),cmap='Reds'):
    """显示矩阵热图"""
    use_svg_display()
    num_rows, num_cols = matrices.shape[0], matrices.shape[1]
    fig, axes = plt.subplots(num_rows, num_cols, figsize=figsize,
                                 sharex=True, sharey=True, squeeze=False)
    for i, (row_axes, row_matrices) in enumerate(zip(axes, matrices)):
        for j, (ax, matrix) in enumerate(zip(row_axes, row_matrices)):
            pcm = ax.imshow(matrix.detach().numpy(), cmap=cmap)
            if i == num_rows - 1:
                ax.set_xlabel(xlabel)
            if j == 0:
                ax.set_ylabel(ylabel)
            if titles:
                ax.set_title(titles[j])
    fig.colorbar(pcm, ax=axes, shrink=0.6);



