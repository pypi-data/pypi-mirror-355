from PepperPepper.environment import torch
from PepperPepper.models.TransUNet.Embeddings import Embeddings
from PepperPepper.models.TransUNet.Encoder import Encoder

class Transformer(torch.nn.Module):
    def __init__(self, config, img_size, vis):
        super(Transformer, self).__init__()
        self.embeddings = Embeddings(config, img_size=img_size, in_channels=config.image_channels)
        self.encoder = Encoder(config, vis)

    def forward(self, input_ids):
        embedding_output, features = self.embeddings(input_ids)
        encoded, attn_weights = self.encoder(embedding_output)  # (B, n_patch, hidden)
        return encoded, attn_weights, features

