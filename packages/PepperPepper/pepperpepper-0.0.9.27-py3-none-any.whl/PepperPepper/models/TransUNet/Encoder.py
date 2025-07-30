from PepperPepper.environment import torch, math, copy

def swish(x):
    return x * torch.sigmoid(x)

ACT2FN = {"gelu": torch.nn.functional.gelu, "relu": torch.nn.functional.relu, "swish": swish}


class Mlp(torch.nn.Module):
    def __init__(self, config):
        super(Mlp, self).__init__()
        self.fc1 = torch.nn.Linear(config.hidden_size, config.transformer["mlp_dim"])
        self.fc2 = torch.nn.Linear(config.transformer["mlp_dim"], config.hidden_size)
        self.act_fn = ACT2FN["gelu"]
        self.dropout = torch.nn.Dropout(config.transformer["dropout_rate"])

        self._init_weights()

    def _init_weights(self):
        torch.nn.init.xavier_uniform_(self.fc1.weight)
        torch.nn.init.xavier_uniform_(self.fc2.weight)
        torch.nn.init.normal_(self.fc1.bias, std=1e-6)
        torch.nn.init.normal_(self.fc2.bias, std=1e-6)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act_fn(x)
        x = self.dropout(x)
        x = self.fc2(x)
        x = self.dropout(x)
        return x


class Attention(torch.nn.Module):
    def __init__(self, config, vis):
        super(Attention, self).__init__()
        self.vis = vis
        self.num_attention_heads = config.transformer["num_heads"]  # 16
        self.attention_head_size = int(config.hidden_size / self.num_attention_heads) # 64
        self.all_head_size = self.num_attention_heads * self.attention_head_size # 786

        self.query = torch.nn.Linear(config.hidden_size, self.all_head_size)
        self.key = torch.nn.Linear(config.hidden_size, self.all_head_size)
        self.value = torch.nn.Linear(config.hidden_size, self.all_head_size)

        self.out = torch.nn.Linear(config.hidden_size, config.hidden_size)
        self.attn_dropout = torch.nn.Dropout(config.transformer["attention_dropout_rate"])
        self.proj_dropout = torch.nn.Dropout(config.transformer["attention_dropout_rate"])

        self.softmax = torch.nn.Softmax(dim=-1)

    def transpose_for_scores(self, x):
        new_x_shape = x.size()[:-1] + (self.num_attention_heads, self.attention_head_size)
        x = x.view(*new_x_shape)
        return x.permute(0, 2, 1, 3)

    def forward(self, hidden_states):
        mixed_query_layer = self.query(hidden_states)
        mixed_key_layer = self.key(hidden_states)
        mixed_value_layer = self.value(hidden_states)

        query_layer = self.transpose_for_scores(mixed_query_layer)
        key_layer = self.transpose_for_scores(mixed_key_layer)
        value_layer = self.transpose_for_scores(mixed_value_layer)

        attention_scores = torch.matmul(query_layer, key_layer.transpose(-1, -2))
        attention_scores = attention_scores / math.sqrt(self.attention_head_size)
        attention_probs = self.softmax(attention_scores)
        weights = attention_probs if self.vis else None
        attention_probs = self.attn_dropout(attention_probs)

        context_layer = torch.matmul(attention_probs, value_layer)
        context_layer = context_layer.permute(0, 2, 1, 3).contiguous()
        new_context_layer_shape = context_layer.size()[:-2] + (self.all_head_size,)
        context_layer = context_layer.view(*new_context_layer_shape)
        attention_output = self.out(context_layer)
        attention_output = self.proj_dropout(attention_output)
        return attention_output, weights




class Block(torch.nn.Module):
    def __init__(self, config, vis):
        super(Block, self).__init__()
        self.hidden_size = config.hidden_size  # 768
        self.attention_norm = torch.nn.LayerNorm(config.hidden_size, eps=1e-6) # 768
        self.ffn_norm = torch.nn.LayerNorm(config.hidden_size, eps=1e-6) # 768
        self.ffn = Mlp(config)
        self.attn = Attention(config, vis)

    def forward(self, x):
        h = x
        x = self.attention_norm(x)
        x, weights = self.attn(x)
        x = x + h

        h = x
        x = self.ffn_norm(x)
        x = self.ffn(x)
        x = x + h
        return x, weights



class Encoder(torch.nn.Module):
    def __init__(self, config, vis):
        super(Encoder, self).__init__()
        self.vis = vis
        self.layer = torch.nn.ModuleList()
        self.encoder_norm = torch.nn.LayerNorm(config.hidden_size, eps=1e-6)
        for _ in range(config.transformer["num_layers"]):
            layer = Block(config, vis)
            self.layer.append(copy.deepcopy(layer))

    def forward(self, hidden_states):
        attn_weights = []
        for layer_block in self.layer:
            hidden_states, weights = layer_block(hidden_states)
            if self.vis:
                attn_weights.append(weights)
        encoded = self.encoder_norm(hidden_states)
        return encoded, attn_weights