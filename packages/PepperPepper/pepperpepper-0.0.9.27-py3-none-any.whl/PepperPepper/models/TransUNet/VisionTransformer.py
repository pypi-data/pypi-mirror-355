from PepperPepper.environment import torch
from PepperPepper.models.TransUNet.Transformer import Transformer
from PepperPepper.models.TransUNet.DecoderCup import DecoderCup
from PepperPepper.models.TransUNet.SegmentationHead import SegmentationHead


class VisionTransformer(torch.nn.Module):
    def __init__(self, config, img_size=224, num_classes=None, zero_head=False, vis=False):
        super(VisionTransformer, self).__init__()
        if num_classes==None:
            num_classes = config.n_classes
        else:
            num_classes = num_classes
        self.num_classes = num_classes
        self.zero_head = zero_head
        self.classifier = config.classifier
        self.transformer = Transformer(config, img_size, vis)
        self.decoder = DecoderCup(config)
        self.segmentation_head = SegmentationHead(
            in_channels=config['decoder_channels'][-1],
            out_channels=self.num_classes,
            kernel_size=3,
        )
        self.config = config




    def forward(self, x):
        if x.size()[1] == 1:
            x = x.repeat(1,3,1,1)
        x, attn_weights, features = self.transformer(x)  # (B, n_patch, hidden)
        x = self.decoder(x, features)
        logits = self.segmentation_head(x)
        return logits