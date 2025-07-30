from PepperPepper.environment import torch, os, hashlib,requests, collections, random, zipfile, tarfile, Image, np

'''
DATA_HUB: 数据集字典。
D2L_DATA_URL: dive into deep learning 的数据集下载源。
DATA_HUB['time_machine']: 时光机器文本数据集下载地址及hash效验码。
DATA_HUB['fra-eng']: 英-法数据集
'''
DATA_HUB = dict()
D2L_DATA_URL = 'http://d2l-data.s3-accelerate.amazonaws.com/'
DATA_HUB['time_machine'] = (D2L_DATA_URL + 'timemachine.txt','090b5e7e70c295757f55df93cb0a180b9691891a')
DATA_HUB['fra-eng'] = (D2L_DATA_URL+'fra-eng.zip','94646ad1522d915e7b0f9296181140edcf86a4f5')








'''
1.download(url, folder='../data', sha1_hash=None)
    从给定的 URL 下载文件，保存到指定文件夹，并返回本地文件路径。
    Parameters:
    - url(str):文件的 URL 地址。
    - folder (str, optional):文件保存的本地文件夹路径。默认为 '../data'。  
    - sha1_hash (str, optional): 文件的 SHA-1 哈希值，用于校验文件的完整性。默认为 None。 

    Returns:
    - str: 本地文件路径。
'''
def download(url, folder='../data', sha1_hash=None):
    if not url.startswith('http'):
        # For back compatability
        url, sha1_hash = DATA_HUB[url]
    os.makedirs(folder, exist_ok=True)
    fname = os.path.join(folder, url.split('/')[-1])
    # Check if hit cache
    if os.path.exists(fname) and sha1_hash:
        sha1 = hashlib.sha1()
        with open(fname, 'rb') as f:
            while True:
                data = f.read(1048576)
                if not data:
                    break
                sha1.update(data)
        if sha1.hexdigest() == sha1_hash:
            return fname
    # Download
    print(f'Downloading {fname} from {url}...')
    r = requests.get(url, stream=True, verify=True)
    with open(fname, 'wb') as f:
        f.write(r.content)
    return fname







"""
2.tokenize(lines, token='word')
    简述：tokenize函数将文本行列表（lines）作为输入， 列表中的每个元素是一个文本序列（如一条文本行）。每个文本序列又被拆分成一个词元列表，词元（token）是文本的基本单位。最后，返回一个由词元列表组成的列表，其中的每个词元都是一个字符串（string）。
    Parameters:
    - lines (list): 文本行列表
    - token (str): 词元化类型
    
    Returns:
    - list(None): 词元化后的列表
"""
def tokenize(lines, token='word'):
    """将文本行拆分为单词或字符词元"""
    if token == 'word':
        return [line.split() for line in lines]
    elif token == 'char':
        return [list(line) for line in lines]
    else:
        print('错误：未知词元类型：' + token)








"""
3.Vocab
    文本词表(vocabulary),初始化词表对象。
    Parameters:
    - tokens (list): 用于构建词表的词元列表，默认为 None。
    - min_freq (int): 词频阈值，低于该频率的词元将被过滤，默认为 0。
    - reserved_tokens (list): 预留的特殊词元列表，默认为 None。

Attributes:
        _token_freqs (list): 按词频降序排列的词元及其频率的列表。
        idx_to_token (list): 索引到词元的映射列表。
        token_to_idx (dict): 词元到索引的映射字典。
        __len__(def) : 返回词表中的词元数量。
        __getitem__(tokens) : 返回给定词元的索引。
        to_tokens(indices) : 返回给定索引对应的词元。 
        token_freqs() : 返回词元及其频率的列表，该方法为属性。
        unk() : 返回未知词元的索引，该方法为属性。
"""
class Vocab:

    def __init__(self, tokens=None, min_freq=0, reserved_tokens=None):
        if tokens is None:
            tokens = []
        if reserved_tokens is None:
            reserved_tokens = []


        # 统计词元的频率
        counter = self.count_corpus(tokens)

        # 按出现频率排序
        self._token_freqs = sorted(counter.items(), key=lambda x: x[1], reverse=True)

        # 初始化索引到词元的映射列表，加入预留词元 "<unk>"
        self.idx_to_token = ['<unk>'] + reserved_tokens

        # 初始化词元到索引的映射字典
        self.token_to_idx = {token: idx for idx, token in enumerate(self.idx_to_token)}

        # 将词频大于 min_freq 的词元添加到词表中
        for token, freq in self._token_freqs:
            if freq < min_freq:
                break
            if token not in self.token_to_idx:
                self.idx_to_token.append(token)
                self.token_to_idx[token] = len(self.idx_to_token) - 1

    def __len__(self):
        """返回词表中的词元数量"""
        return len(self.idx_to_token)

    def __getitem__(self, tokens):
        """
        返回给定词元的索引。

        Parameters:
            tokens (str or list): 单个词元或词元列表。

        Returns:
            idx (int or list): 词元对应的索引或索引列表。
        """
        # 如果 tokens 是单个词元，返回其索引；如果是词元列表，则返回对应的索引列表
        if not isinstance(tokens, (list, tuple)):
            return self.token_to_idx.get(tokens, self.unk)
        return [self.__getitem__(token) for token in tokens]

    def to_tokens(self, indices):
        """
        返回给定索引对应的词元。

        Parameters:
            indices (int or list): 单个索引或索引列表。

        Returns:
            tokens (str or list): 索引对应的词元或词元列表。
        """
        # 如果 indices 是单个索引，返回对应的词元；如果是索引列表，则返回对应的词元列表
        if not isinstance(indices, (list, tuple)):
            return self.idx_to_token[indices]
        return [self.idx_to_token[index] for index in indices]

    @property
    def unk(self):
        """返回未知词元的索引"""
        return 0

    @property
    def token_freqs(self):
        """返回词元及其频率的列表"""
        return self._token_freqs

    def count_corpus(self, tokens):  # 改为实例方法
        """
        统计词元的频率。

        Parameters:
            tokens (list): 用于统计的词元列表，可以是一维或二维列表。

        Returns:
            counter (collections.Counter): 词元及其频率的计数器。
        """
        # 如果 tokens 是二维列表，将其展平成一维列表
        if len(tokens) == 0 or isinstance(tokens[0], list):
            tokens = [token for line in tokens for token in line]

        # 统计词元的频率并返回计数器
        return collections.Counter(tokens)









"""  
4.seq_data_iter_random(corpus, batch_size, num_steps)
    使用随机抽样生成一个小批量子序列  

    参数:  
    - corpus (list): 文本语料库，一个字符列表  
    - batch_size (int): 每个小批量的样本数量  
    - num_steps (int): 每个子序列的长度,时间步

    返回:  
    - 生成器: 产生包含输入X和标签Y的小批量数据  
"""
def seq_data_iter_random(corpus, batch_size, num_steps):
    """使用随机抽样生成一个小批量子序列"""
    # 从随机偏移量开始对序列进行分区，随机范围包括num_steps-1
    corpus = corpus[random.randint(0, num_steps - 1):]

    # 减去1，是因为我们需要考虑标签
    num_subseqs = (len(corpus) - 1) // num_steps

    # 长度为num_steps的子序列的起始索引
    initial_indices = list(range(0, num_subseqs * num_steps, num_steps))

    # 在随机抽样的迭代过程中，
    # 来自两个相邻的、随机的、小批量中的子序列不一定在原始序列上相邻
    random.shuffle(initial_indices)


    def data(pos):
        # 返回从pos位置开始的长度为num_steps的序列
        return corpus[pos: pos + num_steps]


    num_batches = num_subseqs // batch_size
    for i in range(0, batch_size * num_batches, batch_size):
        # 在这里，initial_indices包含子序列的随机起始索引
        initial_indices_per_batch = initial_indices[i: i + batch_size]
        X = [data(j) for j in initial_indices_per_batch]
        Y = [data(j + 1) for j in initial_indices_per_batch]
        yield torch.tensor(X), torch.tensor(Y)




"""  
5.seq_data_iter_sequential(corpus, batch_size, num_steps)
    顺序抽样生成一个小批量子序列  

    参数:  
    - corpus (list): 文本语料库，一个字符列表  
    - batch_size (int): 每个小批量的样本数量  
    - num_steps (int): 每个子序列的长度  

    返回:  
    - 生成器: 产生包含输入X和标签Y的小批量数据  
"""
def seq_data_iter_sequential(corpus, batch_size, num_steps):
    """使用顺序分区生成一个小批量子序列"""
    # 从随机偏移量开始划分序列
    offset = random.randint(0, num_steps)
    num_tokens = ((len(corpus) - offset - 1) // batch_size) * batch_size
    Xs = torch.tensor(corpus[offset: offset + num_tokens])
    Ys = torch.tensor(corpus[offset + 1: offset + 1 + num_tokens])
    Xs, Ys = Xs.reshape(batch_size, -1), Ys.reshape(batch_size, -1)
    num_batches = Xs.shape[1] // num_steps
    for i in range(0, num_steps * num_batches, num_steps):
        X = Xs[:, i: i + num_steps]
        Y = Ys[:, i: i + num_steps]
        yield X, Y





'''
6.download_extract(name, folder=None)
    Download and extract a zip/tar file.  
  
    Args:  
        name (str): 要下载和提取的文件名（或链接名，具体取决于download函数的实现）。  
        folder (str, optional): 可选参数，指定解压后的文件应存放的文件夹名。默认为None，表示不解压到特定文件夹。  
  
    Returns:  
        str: 解压后文件的路径。如果指定了folder参数，则返回该文件夹的路径；否则，返回解压后文件的原始目录路径。  
'''
def download_extract(name, folder=None):
    """Download and extract a zip/tar file."""

    # 调用download函数（该函数未在代码片段中定义，可能是在其他地方定义的）下载文件，并返回文件名
    fname = download(name)

    # 获取文件名所在的目录路径
    base_dir = os.path.dirname(fname)

    # 分离文件名和扩展名
    data_dir, ext = os.path.splitext(fname)

    # 根据文件扩展名选择解压方式
    if ext == '.zip':
        # 如果文件是zip格式，使用zipfile模块打开文件
        fp = zipfile.ZipFile(fname, 'r')
    elif ext in ('.tar', '.gz'):
        # 如果文件是tar或tar.gz格式，使用tarfile模块打开文件
        fp = tarfile.open(fname, 'r')
    else:
        # 如果文件不是zip或tar格式，则抛出断言错误
        assert False, 'Only zip/tar files can be extracted.'

        # 解压文件到原始目录
    fp.extractall(base_dir)

    # 根据folder参数返回相应的路径
    # 如果指定了folder参数，则返回该文件夹的路径（在base_dir下）
    # 否则，返回解压后文件的原始目录路径（即data_dir，因为data_dir和fname的目录是相同的）
    return os.path.join(base_dir, folder) if folder else data_dir


'''
7.truncate_pad(line, num_steps, padding_token)
    截断或填充文本序列，使其长度等于给定的num_steps。  
  
    Args:  
        line (list): 文本序列，通常是一个包含单词或字符的列表。  
        num_steps (int): 序列期望的长度。  
        padding_token (Any): 用于填充的标记或值，可以是字符串、数字等。  
  
    Returns:  
        list: 经过截断或填充后，长度为num_steps的文本序列。
'''
def truncate_pad(line, num_steps, padding_token):
    """截断或填充文本序列"""
    if len(line) > num_steps:
        return line[:num_steps]  # 截断
    return line + [padding_token] * (num_steps - len(line))  # 填充





'''
8.build_array_nmt(lines, vocab, num_steps)
    将机器翻译的文本序列转换成小批量，包括必要的填充和结束标记添加。  
  
    Args:  
        lines (List[str]): 包含原始文本行的列表，每行是一个文本序列。  
        vocab (Dict[str, int]): 词汇表，将文本中的每个单词或字符映射到唯一的整数。  
        num_steps (int): 序列的最大长度，用于截断或填充。  
  
    Returns:  
        Tuple[torch.Tensor, torch.Tensor]:  
        - array (torch.Tensor): 形状为 (batch_size, num_steps) 的二维张量，包含转换后的整数序列。  
        - valid_len (torch.Tensor): 形状为 (batch_size,) 的一维张量，包含每个序列的有效长度（不包括填充）。  
'''
def build_array_nmt(lines, vocab, num_steps):
    """将机器翻译的文本序列转换成小批量"""
    lines = [vocab[l] for l in lines]
    lines = [l + [vocab['<eos>']] for l in lines]
    array = torch.tensor([truncate_pad(
        l, num_steps, vocab['<pad>']) for l in lines])
    valid_len = (array != vocab['<pad>']).type(torch.int32).sum(1)
    return array, valid_len



'''
9.sequence_mask(X, valid_len, value=0)
    通过零值化屏蔽不相关的项， 以便后面任何不相关预测的计算都是与零的乘积，结果都等于零。
    Parameter:
        - X: 文本序列
        - valid_len: 文本序列的有效长度
        - value: 填充值
        
    Return:
        - X: 屏蔽不相关项后的文本序列
'''
def sequence_mask(X, valid_len, value=0):
    """在序列中屏蔽不相关的项"""
    maxlen = X.size(1)
    mask = torch.arange((maxlen), dtype=torch.float32,
                        device=X.device)[None, :] < valid_len[:, None]
    X[~mask] = value
    return X




'''
10.masked_softmax(X, valid_lens)
    通过在最后一个轴上掩蔽元素来执行softmax操作。  
      
    Args:  
        X (Tensor): 输入的3D张量，形状通常为[batch_size, seq_len, features]。  
        valid_lens (Tensor or None): 1D或2D张量，包含每个序列的有效长度。  
          
    Returns:  
        Tensor: 在最后一个轴上应用softmax并掩蔽无效位置后的张量，形状与X相同。  
'''
def masked_softmax(X, valid_lens):
    """通过在最后一个轴上掩蔽元素来执行softmax操作"""
    # X:3D张量，valid_lens:1D或2D张量
    if valid_lens is None:
        return torch.nn.functional.softmax(X, dim=-1)
    else:
        shape = X.shape
        if valid_lens.dim() == 1:
            valid_lens = torch.repeat_interleave(valid_lens, shape[1])
        else:
            valid_lens = valid_lens.reshape(-1)
        # 最后一轴上被掩蔽的元素使用一个非常大的负值替换，从而其softmax输出为0
        X = sequence_mask(X.reshape(-1, shape[-1]), valid_lens,
                              value=-1e6)
        return torch.nn.functional.softmax(X.reshape(shape), dim=-1)


def get_all_images(path, load_images=False):
    """
    获取指定路径下的所有图像文件路径或图像数据。

    参数:
        path (str): 要搜索的文件夹路径。
        load_images (bool): 是否加载图像数据。如果为 False，则仅返回图像文件路径。

    返回:
        list: 图像文件路径列表或加载后的图像数据列表。
    """
    # 支持的图像扩展名
    image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff'}
    image_data = []

    # 遍历文件夹及其子文件夹
    for root, _, files in os.walk(path):
        for file in files:
            # 检查文件扩展名是否为图像格式
            if os.path.splitext(file)[1].lower() in image_extensions:
                file_path = os.path.join(root, file)
                if load_images:
                    try:
                        # 加载图像数据
                        img = Image.open(file_path)
                        image_data.append(img)
                    except Exception as e:
                        print(f"无法加载图像 {file_path}: {e}")
                else:
                    # 仅保存图像路径
                    image_data.append(file_path)

    return image_data



def get_img_norm_cfg(dataset_dir):
    """获取图像归一化配置（假设是预定义的）"""
    # 这里可以根据数据集名称返回对应的均值和标准差
    # 示例：假设所有数据集使用相同的归一化配置
    image_data = get_all_images(dataset_dir, load_images=False)

    # with open(dataset_dir + '/' + dataset_name + '/img_idx/train_' + dataset_name + '.txt', 'r') as f:
    #     train_list = f.read().splitlines()
    # with open(dataset_dir + '/' + dataset_name + '/img_idx/test_' + dataset_name + '.txt', 'r') as f:
    #     test_list = f.read().splitlines()
    # img_list = train_list + test_list
    # img_dir = dataset_dir + '/' + dataset_name + '/images/'
    mean_list = []
    std_list = []

    for img_pth in image_data:
        try:
            img = Image.open(img_pth).convert('I')
            img = np.array(img, dtype=np.float32)
            mean_list.append(img.mean())
            std_list.append(img.std())
        except Exception as e:
            print(f"无法加载图像 {img_pth}: {e}")
    img_norm_cfg = dict(mean=float(np.array(mean_list).mean()), std=float(np.array(std_list).mean()))
    return img_norm_cfg