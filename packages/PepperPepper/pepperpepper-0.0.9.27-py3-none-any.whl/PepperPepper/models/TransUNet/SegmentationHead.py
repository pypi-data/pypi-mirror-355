from PepperPepper.environment import torch

class SegmentationHead(torch.nn.Sequential):
    def __init__(self, in_channels, out_channels, kernel_size=3, upsampling=1):
        conv2d = torch.nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=kernel_size // 2)
        upsampling = torch.nn.UpsamplingBilinear2d(scale_factor=upsampling) if upsampling > 1 else torch.nn.Identity()
        super().__init__(conv2d, upsampling)

