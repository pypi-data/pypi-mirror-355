from PepperPepper.environment import ml_collections, math, torch, nn, F, rearrange, _pair, numbers, copy, profile

def get_MNet_config():
    config = ml_collections.ConfigDict()
    config.transformer = ml_collections.ConfigDict()
    config.KV_size = 32  # KV_size = Q1 + Q2 + Q3 + Q4
    config.transformer.num_heads = 1
    config.transformer.num_layers = 2
    config.patch_sizes = [1]
    config.base_channel = 32  # base channel of U-Net
    config.n_classes = 1

    # ********** useless **********
    config.transformer.embeddings_dropout_rate = 0.1
    config.transformer.attention_dropout_rate = 0.1
    config.transformer.dropout_rate = 0
    return config


class Channel_Embeddings(nn.Module):
    def __init__(self, patchsize, img_size, in_channels):
        super().__init__()
        img_size = _pair(img_size)
        patch_size = _pair(patchsize)

        self.patch_embeddings = nn.Conv2d(in_channels=in_channels,
                                       out_channels=in_channels,
                                       kernel_size=patch_size,
                                       stride=patch_size)
    def forward(self, x):
        if x is None:
            return None
        x = self.patch_embeddings(x)
        return x


class Reconstruct(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size, scale_factor):
        super(Reconstruct, self).__init__()
        if kernel_size == 3:
            padding = 1
        else:
            padding = 0
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=padding)
        self.norm = nn.BatchNorm2d(out_channels)
        self.activation = nn.ReLU(inplace=True)
        self.scale_factor = scale_factor

    # def forward(self, x, h, w):
    def forward(self, x):
        if x is None:
            return None

        x = nn.Upsample(scale_factor=self.scale_factor, mode='bilinear')(x)

        out = self.conv(x)
        out = self.norm(out)
        out = self.activation(out)
        return out


# spatial-embedded Single-head Channel-cross Attention (SSCA)
class Attention_org(nn.Module):
    def __init__(self, config, vis, channel_num):
        super(Attention_org, self).__init__()
        self.vis = vis
        self.KV_size = config.KV_size
        self.channel_num = channel_num
        self.num_attention_heads = config.transformer.num_heads
        self.psi = nn.InstanceNorm2d(self.num_attention_heads)
        self.softmax = nn.Softmax(dim=3)

        # self.temperature = nn.Parameter(torch.ones(num_heads, 1, 1))
        self.mhead1 = nn.Conv2d(channel_num[0], channel_num[0] * self.num_attention_heads, kernel_size=1, bias=False)
        self.mheadk = nn.Conv2d(self.KV_size, self.KV_size * self.num_attention_heads, kernel_size=1, bias=False)
        self.mheadv = nn.Conv2d(self.KV_size, self.KV_size * self.num_attention_heads, kernel_size=1, bias=False)

        self.q1 = nn.Conv2d(channel_num[0] * self.num_attention_heads, channel_num[0] * self.num_attention_heads, kernel_size=3, stride=1,
                            padding=1,
                            groups=channel_num[0] * self.num_attention_heads // 2, bias=False)

        self.k = nn.Conv2d(self.KV_size * self.num_attention_heads, self.KV_size * self.num_attention_heads, kernel_size=3, stride=1,
                           padding=1, groups=self.KV_size * self.num_attention_heads, bias=False)
        self.v = nn.Conv2d(self.KV_size * self.num_attention_heads, self.KV_size * self.num_attention_heads, kernel_size=3, stride=1,
                           padding=1, groups=self.KV_size * self.num_attention_heads, bias=False)

        self.project_out1 = nn.Conv2d(channel_num[0], channel_num[0], kernel_size=1, bias=False)


        # ****************** useless ***************************************
        self.q1_attn1 = torch.nn.Parameter(torch.tensor([0.2]), requires_grad=True)

    def forward(self, emb1, emb_all):
        b, c, h, w = emb1.shape
        q1 = self.q1(self.mhead1(emb1))
        k = self.k(self.mheadk(emb_all))
        v = self.v(self.mheadv(emb_all))

        q1 = rearrange(q1, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)
        k = rearrange(k, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)
        v = rearrange(v, 'b (head c) h w -> b head c (h w)', head=self.num_attention_heads)

        q1 = torch.nn.functional.normalize(q1, dim=-1)
        k = torch.nn.functional.normalize(k, dim=-1)

        _, _, c1, _ = q1.shape
        _, _, c, _ = k.shape
        # print(k.shape)
        # print(q1.shape)

        attn1 = (q1 @ k.transpose(-2, -1)) / math.sqrt(self.KV_size)

        attention_probs1 = self.softmax(self.psi(attn1))

        out1 = (attention_probs1 @ v)

        out_1 = out1.mean(dim=1)

        out_1 = rearrange(out_1, 'b  c (h w) -> b c h w', h=h, w=w)

        O1 = self.project_out1(out_1)
        weights = None

        return O1, weights


def to_3d(x):
    return rearrange(x, 'b c h w -> b (h w) c')


def to_4d(x, h, w):
    return rearrange(x, 'b (h w) c -> b c h w', h=h, w=w)


class BiasFree_LayerNorm(nn.Module):
    def __init__(self, normalized_shape):
        super(BiasFree_LayerNorm, self).__init__()
        if isinstance(normalized_shape, numbers.Integral):
            normalized_shape = (normalized_shape,)
        normalized_shape = torch.Size(normalized_shape)

        assert len(normalized_shape) == 1

        self.weight = nn.Parameter(torch.ones(normalized_shape))
        self.normalized_shape = normalized_shape

    def forward(self, x):
        sigma = x.var(-1, keepdim=True, unbiased=False)
        return x / torch.sqrt(sigma + 1e-5) * self.weight


class WithBias_LayerNorm(nn.Module):
    def __init__(self, normalized_shape):
        super(WithBias_LayerNorm, self).__init__()
        if isinstance(normalized_shape, numbers.Integral):
            normalized_shape = (normalized_shape,)
        normalized_shape = torch.Size(normalized_shape)

        assert len(normalized_shape) == 1

        self.weight = nn.Parameter(torch.ones(normalized_shape))
        self.bias = nn.Parameter(torch.zeros(normalized_shape))
        self.normalized_shape = normalized_shape

    def forward(self, x):
        mu = x.mean(-1, keepdim=True)
        sigma = x.var(-1, keepdim=True, unbiased=False)
        return (x - mu) / torch.sqrt(sigma + 1e-5) * self.weight + self.bias


class LayerNorm3d(nn.Module):
    def __init__(self, dim, LayerNorm_type):
        super(LayerNorm3d, self).__init__()
        if LayerNorm_type == 'BiasFree':
            self.body = BiasFree_LayerNorm(dim)
        else:
            self.body = WithBias_LayerNorm(dim)

    def forward(self, x):
        h, w = x.shape[-2:]
        return to_4d(self.body(to_3d(x)), h, w)

class eca_layer_2d(nn.Module):
    def __init__(self, channel, k_size=3):
        super(eca_layer_2d, self).__init__()
        padding = k_size // 2
        self.avg_pool = nn.AdaptiveAvgPool2d(output_size=1)
        self.conv = nn.Sequential(
            nn.Conv1d(in_channels=1, out_channels=1, kernel_size=k_size, padding=padding, bias=False),
            nn.Sigmoid()
        )
        self.channel = channel
        self.k_size = k_size

    def forward(self, x):
        out = self.avg_pool(x)
        out = out.view(x.size(0), 1, x.size(1))
        out = self.conv(out)
        out = out.view(x.size(0), x.size(1), 1, 1)
        return out * x

# Complementary Feed-forward Network (CFN)
class FeedForward(nn.Module):
    def __init__(self, dim, ffn_expansion_factor, bias):
        super(FeedForward, self).__init__()

        hidden_features = int(dim * ffn_expansion_factor)

        self.project_in = nn.Conv2d(dim, hidden_features * 2, kernel_size=1, bias=bias)

        self.dwconv3x3 = nn.Conv2d(hidden_features, hidden_features, kernel_size=3, stride=1, padding=1, groups=hidden_features,
                                   bias=bias)
        self.dwconv5x5 = nn.Conv2d(hidden_features, hidden_features, kernel_size=5, stride=1, padding=2, groups=hidden_features,
                                   bias=bias)
        self.relu3 = nn.ReLU()
        self.relu5 = nn.ReLU()
        self.project_out = nn.Conv2d(hidden_features * 2, dim, kernel_size=1, bias=bias)
        self.eca = eca_layer_2d(dim)

    def forward(self, x):
        x_3,x_5 = self.project_in(x).chunk(2, dim=1)
        x1_3 = self.relu3(self.dwconv3x3(x_3))
        x1_5 = self.relu5(self.dwconv5x5(x_5))
        x = torch.cat([x1_3, x1_5], dim=1)
        x = self.project_out(x)
        x = self.eca(x)
        return x


#  Spatial-channel Cross Transformer Block (SCTB)
class Block_ViT(nn.Module):
    def __init__(self, config, vis, channel_num):
        super(Block_ViT, self).__init__()
        self.attn_norm1 = LayerNorm3d(channel_num[0], LayerNorm_type='WithBias')
        self.attn_norm = LayerNorm3d(config.KV_size, LayerNorm_type='WithBias')
        self.channel_attn = Attention_org(config, vis, channel_num)
        self.ffn_norm1 = LayerNorm3d(channel_num[0], LayerNorm_type='WithBias')
        self.ffn1 = FeedForward(channel_num[0], ffn_expansion_factor=2.66, bias=False)

    def forward(self, emb1):
        embcat = []
        org1 = emb1

        for i in range(1):
            var_name = "emb" + str(i + 1)
            tmp_var = locals()[var_name]
            if tmp_var is not None:
                embcat.append(tmp_var)
        emb_all = torch.cat(embcat, dim=1)
        cx1 = self.attn_norm1(emb1) if emb1 is not None else None

        emb_all = self.attn_norm(emb_all)  # 1 196 960
        cx1, weights = self.channel_attn(cx1, emb_all)
        cx1 = org1 + cx1 if emb1 is not None else None


        org1 = cx1

        x1 = self.ffn_norm1(cx1) if emb1 is not None else None

        x1 = self.ffn1(x1) if emb1 is not None else None

        x1 = x1 + org1 if emb1 is not None else None
        return x1,  weights


class Encoder(nn.Module):
    def __init__(self, config, vis, channel_num):
        super(Encoder, self).__init__()
        self.vis = vis
        self.layer = nn.ModuleList()
        self.encoder_norm1 = LayerNorm3d(channel_num[0], LayerNorm_type='WithBias')

        for _ in range(config.transformer["num_layers"]):
            layer = Block_ViT(config, vis, channel_num)
            self.layer.append(copy.deepcopy(layer))

    def forward(self, emb1):
        attn_weights = []
        for layer_block in self.layer:
            emb1, weights = layer_block(emb1)
            if self.vis:
                attn_weights.append(weights)
        emb1 = self.encoder_norm1(emb1) if emb1 is not None else None

        return emb1, attn_weights


class ChannelTransformer(nn.Module):
    def __init__(self, config, vis, img_size, channel_num=[32], patchSize=[1]):
        super().__init__()
        self.patchSize_1 = patchSize[0]
        self.embeddings_1 = Channel_Embeddings(self.patchSize_1, img_size=img_size, in_channels=channel_num[0])
        self.encoder = Encoder(config, vis, channel_num)
        self.reconstruct_1 = Reconstruct(channel_num[0], channel_num[0], kernel_size=1, scale_factor=(self.patchSize_1, self.patchSize_1))

    def forward(self, en1):
        emb1 = self.embeddings_1(en1)
        encoded1,attn_weights = self.encoder(emb1)  # (B, n_patch, hidden)

        x1 = self.reconstruct_1(encoded1) if en1 is not None else None

        x1 = x1 + en1 if en1 is not None else None

        return x1, attn_weights


def get_activation(activation_type):
    activation_type = activation_type.lower()
    if hasattr(nn, activation_type):
        return getattr(nn, activation_type)()
    else:
        return nn.ReLU()


def _make_nConv(in_channels, out_channels, nb_Conv, activation='ReLU'):
    layers = []
    layers.append(CBN(in_channels, out_channels, activation))

    for _ in range(nb_Conv - 1):
        layers.append(CBN(out_channels, out_channels, activation))
    return nn.Sequential(*layers)


class CBN(nn.Module):
    def __init__(self, in_channels, out_channels, activation='ReLU'):
        super(CBN, self).__init__()
        self.conv = nn.Conv2d(in_channels, out_channels,
                              kernel_size=3, padding=1)
        self.norm = nn.BatchNorm2d(out_channels)
        self.activation = get_activation(activation)

    def forward(self, x):
        out = self.conv(x)
        out = self.norm(out)
        return self.activation(out)


class DownBlock(nn.Module):
    def __init__(self, in_channels, out_channels, nb_Conv, activation='ReLU'):
        super(DownBlock, self).__init__()
        self.maxpool = nn.MaxPool2d(2)
        self.nConvs = _make_nConv(in_channels, out_channels, nb_Conv, activation)

    def forward(self, x):
        out = self.maxpool(x)
        return self.nConvs(out)


class Flatten(nn.Module):
    def forward(self, x):
        return x.view(x.size(0), -1)


class CCA(nn.Module):
    def __init__(self, F_g, F_x):
        super().__init__()
        self.mlp_x = nn.Sequential(
            Flatten(),
            nn.Linear(F_x, F_x))
        self.mlp_g = nn.Sequential(
            Flatten(),
            nn.Linear(F_g, F_x))
        self.relu = nn.ReLU(inplace=True)

    def forward(self, x):
        avg_pool_x = F.avg_pool2d(x, (x.size(2), x.size(3)), stride=(x.size(2), x.size(3)))
        channel_att_x = self.mlp_x(avg_pool_x)
        # avg_pool_g = F.avg_pool2d(g, (g.size(2), g.size(3)), stride=(g.size(2), g.size(3)))
        # channel_att_g = self.mlp_g(avg_pool_g)
        # channel_att_sum = (channel_att_x + channel_att_g) / 2.0
        channel_att_sum = channel_att_x
        scale = torch.sigmoid(channel_att_sum).unsqueeze(2).unsqueeze(3).expand_as(x)
        x_after_channel = x * scale
        out = self.relu(x_after_channel)
        return out


class UpBlock_attention(nn.Module):
    def __init__(self, in_channels, out_channels, nb_Conv, activation='ReLU'):
        super().__init__()
        # self.up = nn.Upsample(scale_factor=2)
        self.coatt = CCA(F_g=in_channels // 2, F_x=in_channels // 2)
        # self.nConvs = _make_nConv(in_channels, out_channels, nb_Conv, activation)

    def forward(self, skip_x):
        # print(f'x shape: {x.shape}, skip_x shape: {skip_x.shape}')
        # up = self.up(x)
        # print(f'up shape: {up.shape}')
        skip_x_att = self.coatt(x=skip_x)
        # x = torch.cat([skip_x_att, up], dim=1)  # dim 1 is the channel dimension
        # return self.nConvs(x)

        return skip_x_att





class Res_block(nn.Module):
    def __init__(self, in_channels, out_channels, stride=1):
        super(Res_block, self).__init__()
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, stride=stride, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.LeakyReLU(inplace=True)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn2 = nn.BatchNorm2d(out_channels)
        # self.fca = FCA_Layer(out_channels)
        if stride != 1 or out_channels != in_channels:
            self.shortcut = nn.Sequential(
                nn.Conv2d(in_channels, out_channels, kernel_size=1, stride=stride),
                nn.BatchNorm2d(out_channels))
        else:
            self.shortcut = None

    def forward(self, x):
        residual = x
        if self.shortcut is not None:
            residual = self.shortcut(x)
        out = self.conv1(x)
        out = self.bn1(out)
        out = self.relu(out)
        out = self.conv2(out)
        out = self.bn2(out)

        out += residual
        out = self.relu(out)
        return out


class MNet(nn.Module):
    def __init__(self, config, n_channels=32, n_classes=1, img_size=16, vis=False):
        super().__init__()
        self.vis = vis
        # self.deepsuper = deepsuper
        # print('Deep-Supervision:', deepsuper)
        # self.mode = mode
        self.n_channels = n_channels
        self.n_classes = n_classes
        dim = config.base_channel  # basic channel 64
        block = Res_block
        self.pool = nn.MaxPool2d(2, 2)
        # self.inc = self._make_layer(block, n_channels, dim)
        self.down_encoder1 = self._make_layer(block, dim, dim, 1)  # 64  128
        # self.down_encoder2 = self._make_layer(block, dim * 2, dim * 2, 1)  # 64  128

        self.mtc = ChannelTransformer(config, vis, img_size,
                                      channel_num=[dim],
                                      patchSize=[1])

        # self.up_decoder2 = UpBlock_attention(dim * 4, dim, nb_Conv=2)
        self.up_decoder1 = UpBlock_attention(dim * 2, dim, nb_Conv=2)
        # self.outc = nn.Conv2d(dim, n_classes, kernel_size=(1, 1), stride=(1, 1))

    def _make_layer(self, block, input_channels, output_channels, num_blocks=1):
        layers = []
        layers.append(block(input_channels, output_channels))
        for i in range(num_blocks - 1):
            layers.append(block(output_channels, output_channels))
        return nn.Sequential(*layers)

    def forward(self, x):
        # x1 = self.inc(x)  # 64 224 224
        x1 = x
        x2 = self.down_encoder1(self.pool(x1))  # 128 112 112
        # d3 = self.down_encoder2(self.pool(x2))  # 256 56  56

        #  CCT
        f1 = x1

        x1, att_weights = self.mtc(x1)
        x1 = x1 + f1
        # x2 = f2
        # d2 = x2

        # d2 = self.up_decoder2(d3, x2)
        out = self.up_decoder1(x1)
        # print(out.shape)
        return out













if __name__ == '__main__':
    config_vit = get_MNet_config()
    model = MNet(config_vit).cuda()
    model = model
    inputs = torch.rand(1, 32, 16, 16).cuda()
    # output = model(inputs)
    flops, params = profile(model, (inputs,))

    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')
