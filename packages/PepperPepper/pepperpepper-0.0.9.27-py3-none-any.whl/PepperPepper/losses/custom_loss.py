from ..environment import torch
from ..datasets.dataset_utils import sequence_mask



'''
1.MaskedSoftmaxCELoss
    带遮蔽的softmax交叉熵损失函数，暂时为Seq2Seq模型设计的loss函数
    
    Parameter:
        - pred: pred的形状：(batch_size,num_steps,vocab_size)
        - label: label的形状：(batch_size,num_steps)
        - valid_len: valid_len的形状：(batch_size,)
    
    Return:
        - weighted_loss: weighted_loss形状为(batch_size,)
'''
class MaskedSoftmaxCELoss(torch.nn.CrossEntropyLoss):
    """带遮蔽的softmax交叉熵损失函数"""
    # pred的形状：(batch_size,num_steps,vocab_size)
    # label的形状：(batch_size,num_steps)
    # valid_len的形状：(batch_size,)
    def forward(self, pred, label, valid_len):
        weights = torch.ones_like(label)
        weights = sequence_mask(weights, valid_len)
        self.reduction='none'
        unweighted_loss = super(MaskedSoftmaxCELoss, self).forward(
            pred.permute(0, 2, 1), label)
        weighted_loss = (unweighted_loss * weights).mean(dim=1)
        return weighted_loss