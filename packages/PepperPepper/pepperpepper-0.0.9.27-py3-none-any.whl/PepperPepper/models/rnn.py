from ..environment import torch
from .model_module import Encoder, Decoder



'''
1.RNNModel
简述：循环神经网络模型
'''
class RNNModel(torch.nn.Module):
    def __init__(self, rnn_layer, vocab_size, **kwargs):
        """
        初始化 RNN 模型

        参数:
            rnn_layer (torch.nn.Module): 循环神经网络层，可以是 nn.RNN、nn.LSTM 或 nn.GRU。
            vocab_size (int): 词表大小，用于全连接层输出。
            **kwargs: 其他参数。
        """
        super(RNNModel, self).__init__(**kwargs)
        self.rnn = rnn_layer  # 循环神经网络层，可以是nn.RNN、nn.LSTM或nn.GRU
        self.vocab_size = vocab_size  # 词表大小，用于全连接层输出
        self.num_hiddens = self.rnn.hidden_size  # 隐藏单元数，等于循环神经网络层的隐藏单元数

        # 如果RNN是双向的（之后将介绍），num_directions应该是2，否则应该是1
        if not self.rnn.bidirectional:
            self.num_directions = 1
            # 线性层，用于将RNN的输出映射到词表大小的空间上
            self.linear = torch.nn.Linear(self.num_hiddens, self.vocab_size)
        else:
            self.num_directions = 2
            # 如果是双向的RNN，线性层的输入维度是隐藏单元数的两倍
            self.linear = torch.nn.Linear(self.num_hiddens * 2, self.vocab_size)

    def forward(self, inputs, state):
        """
        定义模型的前向传播过程

        参数:
            inputs (tensor): 输入数据，形状为 (seq_len, batch_size)。
            state: 隐状态。

        返回:
            output (tensor): 输出数据，形状为 (seq_len * batch_size, vocab_size)。
            state: 新的隐状态。
        """
        # 将输入转换为one-hot编码，并转换为浮点型张量
        X = torch.nn.functional.one_hot(inputs.T.long(), self.vocab_size)
        X = X.to(torch.float32)
        # 前向传播过程，获取RNN的输出和新的隐状态
        Y, state = self.rnn(X, state)
        # 全连接层首先将Y的形状改为(时间步数*批量大小,隐藏单元数)
        # 它的输出形状是(时间步数*批量大小,词表大小)。
        output = self.linear(Y.reshape((-1, Y.shape[-1])))
        return output, state

    def begin_state(self, device, batch_size=1):
        """
        初始化模型的隐状态

        参数:
            device (str): 计算设备，如 'cpu' 或 'cuda:0'。
            batch_size (int, optional): 批量大小，默认为 1。

        返回:
            state: 初始化的隐状态。
        """
        if not isinstance(self.rnn, torch.nn.LSTM):
            # nn.GRU以张量作为隐状态
            return  torch.zeros((self.num_directions * self.rnn.num_layers,
                                 batch_size, self.num_hiddens),
                                device=device)
        else:
            # nn.LSTM以元组作为隐状态
            return (torch.zeros((
                self.num_directions * self.rnn.num_layers,
                batch_size, self.num_hiddens), device=device),
                    torch.zeros((
                        self.num_directions * self.rnn.num_layers,
                        batch_size, self.num_hiddens), device=device))




'''
2.Seq2SeqEncoder
    用于序列到序列学习的循环神经网络编码器,其中rnn部分默认输入提供state为零
'''
class Seq2SeqEncoder(Encoder):
    def __init__(self, vocab_size, embed_size, num_hiddens, num_layers, dropout=0, **kwargs):
        super(Seq2SeqEncoder, self).__init__(**kwargs)
        # 嵌入层
        self.embedding = torch.nn.Embedding(vocab_size, embed_size)
        self.rnn = torch.nn.GRU(embed_size, num_hiddens, num_layers, dropout=dropout)


    def forward(self, X, *args):
        # 输出'X'的形状：(batch_size,num_steps,embed_size)
        X = self.embedding(X)
        # 在循环神经网络模型中，第一个轴对应于时间步
        X = X.permute(1, 0, 2)
        # 如果未提及状态，则默认为0
        output, state = self.rnn(X)
        # output的形状:(num_steps,batch_size,num_hiddens)
        # state的形状:(num_layers,batch_size,num_hiddens)
        return output, state



'''
3.Seq2SeqDecoder
    用于序列到序列学习的循环神经网络的解码器
'''
class Seq2SeqDecoder(Decoder):
    def __init__(self, vocab_size, embed_size, num_hiddens, num_layers, dropout=0, **kwargs):
        super(Seq2SeqDecoder, self).__init__(**kwargs)
        self.embedding = torch.nn.Embedding(vocab_size, embed_size)
        self.rnn = torch.nn.GRU(embed_size + num_hiddens, num_hiddens, num_layers, dropout=dropout)
        self.dense = torch.nn.Linear(num_hiddens, vocab_size)

    def init_state(self, enc_outputs, *args):
        return enc_outputs[1]

    def forward(self, X, state):
        # 输出'X'的形状：(batch_size,num_steps,embed_size)
        X = self.embedding(X).permute(1, 0, 2)
        # 广播context，使其具有与X相同的num_steps
        context = state[-1].repeat(X.shape[0], 1, 1)
        X_and_context = torch.cat((X, context), 2)
        output, state = self.rnn(X_and_context, state)
        output = self.dense(output).permute(1, 0, 2)
        # output的形状:(batch_size,num_steps,vocab_size)
        # state的形状:(num_layers,batch_size,num_hiddens)
        return output, state
