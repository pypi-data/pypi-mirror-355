from ..environment import torch, plt
from ..environment import collections, math
from ..environment import random


'''
1.show_list_len_pair_hist(legend, xlabel, ylabel, xlist, ylist)
    绘制列表长度对的直方图，绘制文本序包含的词元数的直方图。
'''
def show_list_len_pair_hist(legend, xlabel, ylabel, xlist, ylist):
    from .utils import set_figsize
    """绘制列表长度对的直方图"""
    set_figsize()
    _, _, patches = plt.hist(
        [[len(l) for l in xlist], [len(l) for l in ylist]])
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    for patch in patches[1].patches:
        patch.set_hatch('/')
    plt.legend(legend)

'''
2.bleu(pred_seq, label_seq, k)
    Parameter:
        `pred_seq`：预测的序列（字符串形式）  
        `label_seq`：标签或参考序列（字符串形式）  
        `k`：n-gram的最大值
'''
def bleu(pred_seq, label_seq, k):
    """计算BLEU"""
    pred_tokens, label_tokens = pred_seq.split(' '), label_seq.split(' ')
    len_pred, len_label = len(pred_tokens), len(label_tokens)
    score = math.exp(min(0, 1 - len_label / len_pred))
    for n in range(1, k + 1):
        num_matches, label_subs = 0, collections.defaultdict(int)
        for i in range(len_label - n + 1):
            label_subs[' '.join(label_tokens[i: i + n])] += 1
        for i in range(len_pred - n + 1):
            if label_subs[' '.join(pred_tokens[i: i + n])] > 0:
                num_matches += 1
                label_subs[' '.join(pred_tokens[i: i + n])] -= 1
        score *= math.pow(num_matches / (len_pred - n + 1), math.pow(0.5, n))
    return score





























