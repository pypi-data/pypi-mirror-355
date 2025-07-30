from ..environment import torch, math


'''
1.train_epoch_ch8(net, train_iter, loss, updater, device, use_random_iter)
    parameter:
    - net: network to train
    - train_iter: iterator for training the network
    - loss: loss function
    - updater: updater is Optimizer
    - device: training which device is used
    - use_random_iter: whether to use random iterator for training
    
    Returns:
    - perplexity: perplexity of the network
    - speed: speed of training
'''

def train_epoch_ch8(net, train_iter, loss, updater, device, use_random_iter):
    '''动手学深度学习第八章，用于序列训练的训练函数'''
    from ..core.utils import Timer,Accumulator
    from ..optimizers.custom_optimizer import grad_clipping


    state, timer = None, Timer()
    metric = Accumulator(2)
    for X, Y in train_iter:
        if state is None or use_random_iter:
            # 在第一次迭代或使用随机抽样时初始化state
            state = net.begin_state(batch_size=X.shape[0], device=device)
        else:
            if isinstance(net, torch.nn.Module) and not isinstance(state, tuple):
                # state对于nn.GRU是个张量
                state.detach_()
            else:
                # state对于nn.LSTM或对于我们从零开始实现的模型是个张量
                for s in state:
                    s.detach_()
        y = Y.T.reshape(-1)
        X, y = X.to(device), y.to(device)
        y_hat, state = net(X, state)
        l = loss(y_hat, y.long()).mean()
        if isinstance(updater, torch.optim.Optimizer):
            updater.zero_grad()
            l.backward()
            grad_clipping(net, 1)
            updater.step()
        else:
            l.backward()
            grad_clipping(net, 1)
            # 因为已经调用了mean函数
            updater(batch_size=1)
        metric.add(l * y.numel(), y.numel())
    return math.exp(metric[0] / metric[1]), metric[1] / timer.stop()



'''
2.predict_ch8(prefix, num_preds, net, vocab, device)
在给定前缀后面生成新字符。

    Parameters:
        prefix (str): 用于生成新字符的前缀。
        num_preds (int): 预测的字符数。
        net (torch.nn.Module): 经过训练的神经网络模型。
        vocab (Vocab): 词汇表，将字符映射到索引。
        device (torch.device): 设备，用于计算。

    Returns:
        str: 生成的新字符序列。
'''
def predict_ch8(prefix, num_preds, net, vocab, device):  #@save
    """在prefix后面生成新字符"""
    state = net.begin_state(batch_size=1, device=device)
    outputs = [vocab[prefix[0]]]
    get_input = lambda: torch.tensor([outputs[-1]], device=device).reshape((1, 1))
    for y in prefix[1:]:  # 预热期
        _, state = net(get_input(), state)
        outputs.append(vocab[y])
    for _ in range(num_preds):  # 预测num_preds步
        y, state = net(get_input(), state)
        outputs.append(int(y.argmax(dim=1).reshape(1)))
    return ''.join([vocab.idx_to_token[i] for i in outputs])



'''
3.train_ch8(net, train_iter, vocab, lr, num_epochs, device,use_random_iter=False):
    训练模型（定义见第8章）
    
    参数:
        net (torch.nn.Module): 要训练的神经网络模型。
        train_iter (iterator): 训练数据集的迭代器。
        vocab (dict): 词汇表，用于将字符转换为索引。
        lr (float): 学习率，用于控制参数更新的步长。
        num_epochs (int): 训练的轮数。
        device (str): 训练设备，如'cpu'或'cuda:0'。
        use_random_iter (bool, optional): 是否使用随机数据迭代器，默认为False。
    
    返回值:
        无，直接打印训练过程中的困惑度和速度信息，并输出预测结果。
'''
def train_ch8(net, train_iter, vocab, lr, num_epochs, device,
              use_random_iter=False):

    from ..core.utils import Animator
    from ..optimizers import sgd
    """训练模型（定义见第8章）"""
    loss = torch.nn.CrossEntropyLoss()
    animator = Animator(xlabel='epoch', ylabel='perplexity',
                            legend=['train'], xlim=[10, num_epochs])
    # 初始化
    if isinstance(net, torch.nn.Module):
        updater = torch.optim.SGD(net.parameters(), lr)
    else:
        updater = lambda batch_size: sgd(net.params, lr, batch_size)
    predict = lambda prefix: predict_ch8(prefix, 50, net, vocab, device)
    # 训练和预测
    for epoch in range(num_epochs):
        ppl, speed = train_epoch_ch8(
            net, train_iter, loss, updater, device, use_random_iter)
        if (epoch + 1) % 10 == 0:
            print(predict('time traveller'))
            animator.add(epoch + 1, [ppl])
    print(f'困惑度 {ppl:.1f}, {speed:.1f} 词元/秒 {str(device)}')
    print(predict('time traveller'))
    print(predict('traveller'))










'''
4.train_seq2seq(net, data_iter, lr, num_epochs, tgt_vocab, device)
    序列模型训练函数
    Parameters:
        net： Seq模型
        data_iter： 数据集
        lr： 学习率
        num_epochs： 训练轮数
        tgt_vocab： 词表
        device： 训练设备
'''
def train_seq2seq(net, data_iter, lr, num_epochs, tgt_vocab, device):
    from ..core.utils import Animator, Timer, Accumulator
    from ..optimizers.custom_optimizer import grad_clipping
    from ..losses.custom_loss import MaskedSoftmaxCELoss
    """训练序列到序列模型"""
    def xavier_init_weights(m):
        if type(m) == torch.nn.Linear:
            torch.nn.init.xavier_uniform_(m.weight)
        if type(m) == torch.nn.GRU:
            for param in m._flat_weights_names:
                if "weight" in param:
                    torch.nn.init.xavier_uniform_(m._parameters[param])

    net.apply(xavier_init_weights)
    net.to(device)
    optimizer = torch.optim.Adam(net.parameters(), lr=lr)
    loss = MaskedSoftmaxCELoss()
    net.train()
    animator = Animator(xlabel='epoch', ylabel='loss',
                     xlim=[10, num_epochs])
    for epoch in range(num_epochs):
        timer = Timer()
        metric = Accumulator(2)  # 训练损失总和，词元数量
        for batch in data_iter:
            optimizer.zero_grad()
            X, X_valid_len, Y, Y_valid_len = [x.to(device) for x in batch]
            bos = torch.tensor([tgt_vocab['<bos>']] * Y.shape[0],
                          device=device).reshape(-1, 1)
            dec_input = torch.cat([bos, Y[:, :-1]], 1)  # 强制教学
            Y_hat, _ = net(X, dec_input, X_valid_len)
            l = loss(Y_hat, Y, Y_valid_len)
            l.sum().backward()      # 损失函数的标量进行“反向传播”
            grad_clipping(net, 1)
            num_tokens = Y_valid_len.sum()
            optimizer.step()
            with torch.no_grad():
                metric.add(l.sum(), num_tokens)
        if (epoch + 1) % 10 == 0:
            animator.add(epoch + 1, (metric[0] / metric[1],))
    print(f'loss {metric[0] / metric[1]:.3f}, {metric[1] / timer.stop():.1f} '
        f'tokens/sec on {str(device)}')





'''
5.predict_seq2seq(net, src_sentence, src_vocab, tgt_vocab, num_steps,device, save_attention_weights=False)
    Parameter:
        net: 预测模型
        src_sentence： 原句子
        src_vocab： 原词汇表
        tgt_vocab： 目标词汇表
        num_steps： 时间步
        device： 设备
        save_attention_weights： 保存注意力权重
'''
#@save
def predict_seq2seq(net, src_sentence, src_vocab, tgt_vocab, num_steps,
                    device, save_attention_weights=False):
    from ..datasets.dataset_utils import truncate_pad
    """序列到序列模型的预测"""
    # 在预测时将net设置为评估模式
    net.eval()
    src_tokens = src_vocab[src_sentence.lower().split(' ')] + [
        src_vocab['<eos>']]
    enc_valid_len = torch.tensor([len(src_tokens)], device=device)
    src_tokens = truncate_pad(src_tokens, num_steps, src_vocab['<pad>'])
    # 添加批量轴
    enc_X = torch.unsqueeze(
        torch.tensor(src_tokens, dtype=torch.long, device=device), dim=0)
    enc_outputs = net.encoder(enc_X, enc_valid_len)
    dec_state = net.decoder.init_state(enc_outputs, enc_valid_len)
    # 添加批量轴
    dec_X = torch.unsqueeze(torch.tensor(
        [tgt_vocab['<bos>']], dtype=torch.long, device=device), dim=0)
    output_seq, attention_weight_seq = [], []
    for _ in range(num_steps):
        Y, dec_state = net.decoder(dec_X, dec_state)
        # 我们使用具有预测最高可能性的词元，作为解码器在下一时间步的输入
        dec_X = Y.argmax(dim=2)
        pred = dec_X.squeeze(dim=0).type(torch.int32).item()
        # 保存注意力权重（稍后讨论）
        if save_attention_weights:
            attention_weight_seq.append(net.decoder.attention_weights)
        # 一旦序列结束词元被预测，输出序列的生成就完成了
        if pred == tgt_vocab['<eos>']:
            break
        output_seq.append(pred)
    return ' '.join(tgt_vocab.to_tokens(output_seq)), attention_weight_seq