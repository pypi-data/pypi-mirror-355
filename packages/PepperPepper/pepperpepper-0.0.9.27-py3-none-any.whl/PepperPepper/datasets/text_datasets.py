from ..environment import re, os


'''
1.read_time_machine()
    将时间机器数据集加载到文本行列表中
    
    Parameters:
    - None

    Returns:
    - list: 文本行列表
'''
def read_time_machine():
    from .dataset_utils import download
    """将时间机器数据集加载到文本行的列表中"""
    with open(download('time_machine'), 'r') as f:
        lines = f.readlines()
    return [re.sub('[^A-Za-z]+', ' ', line).strip().lower() for line in lines]




'''
2.load_corpus_time_machine(max_tokens=-1)
    返回时光机器数据集的词元索引列表和词表
    
    Parameters:
    - max_tokens: int，corpus取多少数
    
    Returns:
    - corpus(list) : 词元索引列表
    - vocab(Vocab) : 时光机器语料库的词表
'''
def load_corpus_time_machine(max_tokens=-1):
    from .dataset_utils import tokenize, Vocab
    lines = read_time_machine()
    tokens = tokenize(lines,'char')
    vocab = Vocab(tokens)

    # 将时光机器数据集文本展平到一个列表中
    corpus = [vocab[token] for line in tokens for token in line]
    if max_tokens > 0:
        corpus = corpus[:max_tokens]
    return corpus, vocab


'''
3.SeqDataLoader
    加载序列数据的迭代器。这个类提供了两种加载序列数据的方式：随机抽样（seq_data_iter_random）和顺序抽取（seq_data_iter_sequential）。

    Parameters:
    - batch_size (int): 每个小批量中的样本数量。  
    - num_steps (int): 每个子序列的长度。  
    - use_random_iter (bool): 是否使用随机迭代。  
    - max_tokens (int): 用于加载语料库时的最大词元数。  

    Attributes:
    - data_iter_fn (callable): 用于生成数据迭代器的函数（随机或顺序）。
    - corpus (list): 加载的语料库，包含序列数据。
    - vocab (dict): 词汇表，将词元映射到索引。
    - batch_size (int): 每个小批量中的样本数量。
    - num_steps (int): 每个子序列的长度。
'''


class SeqDataLoader_time_machine:
    """加载序列数据的迭代器类"""

    def __init__(self, batch_size, num_steps, use_random_iter, max_tokens):
        """
        初始化序列数据加载器

        Args:
            batch_size (int): 每个小批量中的样本数量。
            num_steps (int): 每个子序列的长度。
            use_random_iter (bool): 是否使用随机迭代。
            max_tokens (int): 用于加载语料库时的最大词元数。

        Attributes:
            data_iter_fn (callable): 用于生成数据迭代器的函数（随机或顺序）。
            corpus (list): 加载的语料库，包含序列数据。
            vocab (dict): 词汇表，将词元映射到索引。
            batch_size (int): 每个小批量中的样本数量。
            num_steps (int): 每个子序列的长度。
        """
        from .dataset_utils import seq_data_iter_random,seq_data_iter_sequential

        if use_random_iter:
            # 如果使用随机迭代，则将 data_iter_fn 设置为 seq_data_iter_random 函数
            self.data_iter_fn = seq_data_iter_random
        else:
            # 否则，将 data_iter_fn 设置为 seq_data_iter_sequential 函数
            self.data_iter_fn = seq_data_iter_sequential

            # 加载语料库和词汇表，并限制最大词元数为 max_tokens
        self.corpus, self.vocab = load_corpus_time_machine(max_tokens)

        # 设置 batch_size 和 num_steps
        self.batch_size, self.num_steps = batch_size, num_steps

    def __iter__(self):
        """
        实现迭代器协议，使得对象可迭代

        Returns:
            generator: 返回一个生成器，该生成器使用 data_iter_fn 函数生成小批量数据。
        """
        # 调用之前设置好的 data_iter_fn 函数来生成数据迭代器
        # 并返回该迭代器，用于迭代获取小批量数据
        return self.data_iter_fn(self.corpus, self.batch_size, self.num_steps)



'''
4.load_data_time_machine(batch_size, num_steps, use_random_iter=False, max_tokens=10000)
    返回时光机器数据集的迭代器和词表
    Parameters:
    - batch_size (int): 每个小批量中的样本数量。  
    - num_steps (int): 序列中每个样本的时间步数（或长度）。  
    - use_random_iter (bool, optional): 是否使用随机迭代来生成小批量。默认为False。  
    - max_tokens (int, optional): 加载语料库时使用的最大词元数。默认为10000。 

    Returns:  
    - data_iter (SeqDataLoader): 数据加载器的迭代器，用于生成小批量数据。  
    - vocab (dict): 词汇表，将词元映射到索引。  
'''
def load_data_time_machine(batch_size, num_steps, use_random_iter=False, max_tokens=10000):
    """返回时光机器数据集的迭代器和词表"""
    data_iter = SeqDataLoader_time_machine(
        batch_size, num_steps, use_random_iter, max_tokens)
    return data_iter, data_iter.vocab



'''
5.read_data_nmt()
    载入“英语－法语”数据集  
    该函数从指定的数据源下载并解压“英语－法语”数据集，然后读取法语部分（假设是fra.txt文件）并返回其内容。  
  
    Returns:  
        str: 法语文本数据，作为字符串返回。
'''
def read_data_nmt():
    """载入“英语－法语”数据集"""
    from .dataset_utils import download_extract
    data_dir = download_extract('fra-eng')
    with open(os.path.join(data_dir, 'fra.txt'), 'r',
             encoding='utf-8') as f:
        return f.read()






'''
6.preprocess_nmt(text)
    预处理“英语－法语”数据集，大写转小写，字母与符号之间加空格，多个空格转为一个空格符。
    
    Parameters:
    - text：读取的文本list。
    
    Returns:
    - list: 处理后的文本序列。
'''
def preprocess_nmt(text):
    """预处理“英语－法语”数据集"""
    def no_space(char, prev_char):
        return char in set(',.!?') and prev_char != ' '

    # 使用空格替换不间断空格
    # 使用小写字母替换大写字母
    text = text.replace('\u202f', ' ').replace('\xa0', ' ').lower()
    # 在单词和标点符号之间插入空格
    out = [' ' + char if i > 0 and no_space(char, text[i - 1]) else char
           for i, char in enumerate(text)]
    return ''.join(out)



'''
7.tokenize_nmt(text, num_examples=None)
    该函数用于对“英语－法语”翻译任务的数据集进行词元化。  
  
    Args:  
        text (str): 包含“英语－法语”翻译对的字符串，其中每行以换行符（'\n'）分隔，  
                     每行内部使用制表符（'\t'）分隔英语和法语文本。  
        num_examples (int, optional): 需要处理的翻译对数量。如果设置了此参数，  
                                      函数将只处理前`num_examples`个翻译对。默认为None，  
                                      表示处理所有翻译对。  
  
    Returns:  
        tuple: 包含两个列表的元组，分别表示源语言（英语）和目标语言（法语）的词元化结果。  
        - source (list): 源语言（英语）文本的词元化列表，其中每个元素都是一个字符串列表，每个字符串表示一个单词。  
        - target (list): 目标语言（法语）文本的词元化列表，与源语言列表的结构相同。
'''
def tokenize_nmt(text, num_examples=None):
    """词元化“英语－法语”数据数据集"""
    source, target = [], []
    for i, line in enumerate(text.split('\n')):
        if num_examples and i > num_examples:
            break
        parts = line.split('\t')
        if len(parts) == 2:
            source.append(parts[0].split(' '))
            target.append(parts[1].split(' '))
    return source, target





'''
8.load_data_nmt(batch_size, num_steps, num_examples=600)
    加载并预处理机器英-法翻译数据集，返回数据迭代器以及源语言和目标语言的词表。  
  
    Args:  
        batch_size (int): 每个小批量中的样本数。  
        num_steps (int): 序列的最大长度，用于截断或填充。  
        num_examples (int, optional): 用于加载的数据样本数。默认为600。  
  
    Returns:  
        Tuple[DataLoader, Vocab, Vocab]:  
        - data_iter (DataLoader): 加载数据的小批量迭代器。  
        - src_vocab (Vocab): 源语言词表。  
        - tgt_vocab (Vocab): 目标语言词表。  
'''
def load_data_nmt(batch_size, num_steps, num_examples=600):
    from .dataset_utils import Vocab, build_array_nmt
    from .custom_dataset import load_arrays
    """返回翻译数据集的迭代器和词表"""
    text = preprocess_nmt(read_data_nmt())
    source, target = tokenize_nmt(text, num_examples)
    src_vocab = Vocab(source, min_freq=2,
                          reserved_tokens=['<pad>', '<bos>', '<eos>'])
    tgt_vocab = Vocab(target, min_freq=2,
                          reserved_tokens=['<pad>', '<bos>', '<eos>'])
    src_array, src_valid_len = build_array_nmt(source, src_vocab, num_steps)
    tgt_array, tgt_valid_len = build_array_nmt(target, tgt_vocab, num_steps)
    data_arrays = (src_array, src_valid_len, tgt_array, tgt_valid_len)
    data_iter = load_arrays(data_arrays, batch_size)
    return data_iter, src_vocab, tgt_vocab