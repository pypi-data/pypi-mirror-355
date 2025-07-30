
from ..environment import torch

'''
1.Encoder
    编码器架构，指定长度可变的序列作为编码器的输入X。
    编码器-解码器架构的基本编码器接口。  
    这是一个抽象基类，用于定义编码器的通用接口。  
    实际使用时，需要继承这个类并实现`forward`方法

'''


class Encoder(torch.nn.Module):
    '''编码器-解码器架构的基本编码器接口'''

    def __init__(self, **kwargs):
        '''
        初始化方法。
        通常用于定义编码器所需的层或组件。

        参数:
            **kwargs: 可选的参数，允许在实例化时传入额外的参数。
                然而，在这个基本接口中，我们并不直接使用这些参数。
        '''
        super(Encoder, self).__init__(**kwargs)

    def forward(self, x, *args):
        '''
        前向传播方法。
        这是一个抽象方法，需要在子类中实现。

        参数:
            x: 输入数据，通常是一个张量（Tensor）。
            *args: 可变参数列表，允许传入额外的输入。
                具体的使用方式取决于编码器的设计。

        返回:
            通常返回一个编码后的表示（通常是张量），但具体取决于实现。

        注意:
            在这个基本接口中，我们直接抛出了一个`NotImplementedError`，
            这意味着如果你尝试直接实例化这个类并使用它，将会引发错误。
            你需要继承这个类并实现你自己的`forward`方法。
        '''
        raise NotImplementedError("编码器的前向传播方法需要在子类中实现。")


'''
2.Decoder
    编码器-解码器架构的基本解码器接口。
    这是一个抽象基类，用于定义解码器的通用接口。
    实际使用时，需要继承这个类并实现`init_state`和`forward`方法。
'''


class Decoder(torch.nn.Module):

    def __init__(self, **kwargs):
        '''
        初始化方法。
        通常用于定义解码器所需的层或组件。

        参数:
        **kwargs: 可选的参数，允许在实例化时传入额外的参数。
                然而，在这个基本接口中，我们并不直接使用这些参数。
        '''
        super(Decoder, self).__init__(**kwargs)

    def init_state(self, enc_outputs, *args):
        '''
        初始化解码器的状态。
        这个方法通常用于根据编码器的输出来设置解码器的初始状态。

        参数:
        enc_outputs: 编码器的输出，通常是一个包含编码信息的张量或张量序列。
        *args: 可变参数列表，允许传入额外的信息以初始化状态。

        返回:
        解码器的初始状态，具体的形式取决于解码器的设计。

        注意:
        这是一个抽象方法，需要在子类中实现具体的初始化逻辑。
        '''
        raise NotImplementedError("解码器的初始化方法需要在子类中实现")

    def forward(self, x, state):
        '''
        前向传播方法。
        这个方法定义了给定输入和当前状态下解码器的行为。

        参数:
        x: 当前时间步的输入，通常是一个张量（Tensor）。
        state: 解码器的当前状态，通常是一个包含之前时间步信息的张量或张量序列。

        返回:
        解码器的输出和更新后的状态。输出的具体形式取决于解码器的设计。

        注意:
        这是一个抽象方法，需要在子类中实现具体的前向传播逻辑。
        '''
        raise NotImplementedError('解码器的前向传播方法需要在子类中实现。')


'''
3.EncoderDecoder
    编码器-解码器架构的基类。
    这个类将编码器和解码器组合在一起，形成一个完整的编码器-解码器模型。
'''


# @save
class EncoderDecoder(torch.nn.Module):
    """
    编码器-解码器架构的基类。
    这个类将编码器和解码器组合在一起，形成一个完整的编码器-解码器模型。
    """

    def __init__(self, encoder, decoder, **kwargs):
        """
        初始化方法。

        参数:
        encoder (nn.Module): 编码器模块，负责将输入数据编码为某种表示。
        decoder (nn.Module): 解码器模块，负责根据编码器的输出和输入数据生成输出。
        **kwargs: 可选的参数，允许在实例化时传入额外的参数。
                  这些参数在基类中不使用，但可以被子类使用。
        """
        super(EncoderDecoder, self).__init__(**kwargs)
        self.encoder = encoder  # 存储编码器模块
        self.decoder = decoder  # 存储解码器模块

    def forward(self, enc_X, dec_X, *args):
        """
        前向传播方法。
        给定编码器的输入enc_X和解码器的输入dec_X，执行编码器-解码器架构的前向传播。

        参数:
        enc_X (Tensor): 编码器的输入数据。
        dec_X (Tensor): 解码器的输入数据（通常是目标序列的一部分或起始符号）。
        *args: 可变参数列表，允许传入额外的参数给编码器和解码器。

        返回:
        Tensor: 解码器的输出，通常是预测的目标序列。

        注意:
        该方法首先通过编码器对enc_X进行编码，然后将编码器的输出传递给解码器的初始化状态方法，
        最后使用解码器生成输出。
        """
        # 编码器的前向传播，得到编码后的输出
        enc_outputs = self.encoder(enc_X, *args)

        # 使用编码器的输出来初始化解码器的状态
        dec_state = self.decoder.init_state(enc_outputs, *args)

        # 解码器的前向传播，得到最终输出
        return self.decoder(dec_X, dec_state)



'''
4.AttentionDecoder(Decoder)
    带有注意力机制解码器的基本接口,具体应用需要通过继承实现
'''
class AttentionDecoder(Decoder):
    """带有注意力机制解码器的基本接口"""
    def __init__(self, **kwargs):
        super(AttentionDecoder, self).__init__(**kwargs)

    @property
    def attention_weights(self):
        raise NotImplementedError



'''
5.Seq2SeqAttentionDecoder(AttentionDecoder)
    Bahdanau注意力解码器
'''
class Seq2SeqAttentionDecoder(AttentionDecoder):
    def __init__(self, vocab_size, embed_size, num_hiddens, num_layers, dropout=0, **kwargs):
        from .transformer import AdditiveAttention

        super(Seq2SeqAttentionDecoder, self).__init__(**kwargs)
        self.attention = AdditiveAttention(num_hiddens, num_hiddens, num_hiddens, dropout)
        self.embedding = torch.nn.Embedding(vocab_size, embed_size)
        self.rnn = torch.nn.GRU(embed_size+num_hiddens, num_hiddens, num_layers, dropout=dropout)

        self.dense = torch.nn.Linear(num_hiddens, vocab_size)

    def init_state(self, enc_outputs, enc_valid_lens, *args):
        # outputs的形状为(batch_size，num_steps，num_hiddens).
        # hidden_state的形状为(num_layers，batch_size，num_hiddens)
        outputs, hidden_state = enc_outputs
        return (outputs.permute(1, 0, 2), hidden_state, enc_valid_lens)

    def forward(self, X, state):
        # enc_outputs的形状为(batch_size,num_steps,num_hiddens).
        # hidden_state的形状为(num_layers,batch_size,num_hiddens)
        enc_outputs, hidden_state, enc_valid_lens = state
        # 输出X的形状为(num_steps,batch_size,embed_size)

        X = self.embedding(X).permute(1, 0, 2)
        outputs, self._attention_weights = [], []
        for x in X:
            # query的形状为(batch_size,1,num_hiddens)
            query = torch.unsqueeze(hidden_state[-1], dim=1)
            # context的形状为(batch_size,1,num_hiddens)
            context = self.attention(
                query, enc_outputs, enc_outputs, enc_valid_lens)
            # 在特征维度上连结
            x = torch.cat((context, torch.unsqueeze(x, dim=1)), dim=-1)
            # 将x变形为(1,batch_size,embed_size+num_hiddens)
            out, hidden_state = self.rnn(x.permute(1, 0, 2), hidden_state)
            outputs.append(out)
            self._attention_weights.append(self.attention.attention_weights)
            # 全连接层变换后，outputs的形状为
            # (num_steps,batch_size,vocab_size)
        outputs = self.dense(torch.cat(outputs, dim=0))
        return outputs.permute(1, 0, 2), [enc_outputs, hidden_state,
                                          enc_valid_lens]


    @property
    def attention_weights(self):
        return self._attention_weights