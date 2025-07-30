import torch
import torch.nn as nn
import math
import torch.nn.functional as F
from einops import rearrange, repeat


try:
    from mamba_ssm.ops.selective_scan_interface import selective_scan_fn
except ImportError as e:
    print(f"Import failed: {e}")





class SnycTwinSSM(nn.Module):
    def __init__(self, d_model, d_state=16, d_conv=4, expand=1, dt_rank="auto", dt_min=0.001, dt_max=0.1,
                 dt_init="random", dt_scale=1.0, dt_init_floor=1e-4, conv_bias=True, bias=False,
                 use_fast_path=True, layer_idx=None, device=None, dtype=None):
        factory_kwargs = {"device": device, "dtype": dtype}
        super().__init__()
        self.d_model = d_model
        self.d_state = d_model // 4 * expand
        self.d_conv = d_conv
        self.expand = expand
        self.d_inner = int(self.expand * self.d_model)
        self.dt_rank = math.ceil(self.d_model / 16) if dt_rank == "auto" else dt_rank
        self.use_fast_path = use_fast_path
        self.layer_idx = layer_idx

        # Linear layers for input projection and sparse representation
        self.in_proj = nn.Linear(self.d_model, self.d_inner, bias=bias, **factory_kwargs)
        self.x_proj = nn.Linear(self.d_inner // 2, self.dt_rank + self.d_state * 2, bias=False, **factory_kwargs)
        self.dt_proj = nn.Linear(self.dt_rank, self.d_inner // 2, bias=True, **factory_kwargs)
        self.out_proj = nn.Linear(self.d_inner, self.d_model, bias=bias, **factory_kwargs)

        self.in_proj_2 = nn.Linear(self.d_model, self.d_inner, bias=bias, **factory_kwargs)
        self.x_proj_2 = nn.Linear(self.d_inner // 2, self.dt_rank + self.d_state * 2, bias=False, **factory_kwargs)
        self.dt_proj_2 = nn.Linear(self.dt_rank, self.d_inner // 2, bias=True, **factory_kwargs)
        self.out_proj_2 = nn.Linear(self.d_inner, self.d_model, bias=bias, **factory_kwargs)

        # Initialize dt_proj weights
        dt_init_std = self.dt_rank ** -0.5 * dt_scale
        if dt_init == "constant":
            nn.init.constant_(self.dt_proj.weight, dt_init_std)
        elif dt_init == "random":
            nn.init.uniform_(self.dt_proj.weight, -dt_init_std, dt_init_std)
        else:
            raise NotImplementedError

        # Initialize dt bias
        dt = torch.exp(
            torch.rand(self.d_inner // 2, **factory_kwargs) * (math.log(dt_max) - math.log(dt_min))
            + math.log(dt_min)
        ).clamp(min=dt_init_floor)
        inv_dt = dt + torch.log(-torch.expm1(-dt))
        with torch.no_grad():
            self.dt_proj.bias.copy_(inv_dt)

        # Initialize A matrix
        A = repeat(
            torch.arange(1, self.d_state + 1, dtype=torch.float32, device=device),
            "n -> d n",
            d=self.d_inner // 2,
        ).contiguous()
        A_log = torch.log(A)
        self.A_log = nn.Parameter(A_log)
        self.A_log._no_weight_decay = True
        self.D = nn.Parameter(torch.ones(self.d_inner // 2, device=device))
        self.D._no_weight_decay = True

        # Convolution layers
        self.conv1d_x = nn.Conv1d(
            in_channels=self.d_inner // 2,
            out_channels=self.d_inner // 2,
            bias=conv_bias // 2,
            kernel_size=d_conv,
            groups=self.d_inner // 2,
            **factory_kwargs,
        )
        self.conv1d_z = nn.Conv1d(
            in_channels=self.d_inner // 2,
            out_channels=self.d_inner // 2,
            bias=conv_bias // 2,
            kernel_size=d_conv,
            groups=self.d_inner // 2,
            **factory_kwargs,
        )

        self.conv1d_x_2 = nn.Conv1d(
            in_channels=self.d_inner // 2,
            out_channels=self.d_inner // 2,
            bias=conv_bias // 2,
            kernel_size=d_conv,
            groups=self.d_inner // 2,
            **factory_kwargs,
        )
        self.conv1d_z_2 = nn.Conv1d(
            in_channels=self.d_inner // 2,
            out_channels=self.d_inner // 2,
            bias=conv_bias // 2,
            kernel_size=d_conv,
            groups=self.d_inner // 2,
            **factory_kwargs,
        )

        self.epsilon = nn.Parameter(torch.Tensor([0.01]), requires_grad=True)



    def sparse_approximation(self, matrix):
        threshold = torch.max(matrix) * 0.1
        return torch.sign(matrix) * F.relu(torch.abs(matrix) - threshold)


    def forward(self, inp):
        """
        hidden_states: (B, L, D)
        Returns: same shape as hidden_states
        """
        _, c, _ = inp.size()
        inpx, inpy = torch.split(inp, [c // 2, c // 2], dim=1)

        inpx = inpx.permute(0, 2, 1)
        inpy = inpy.permute(0, 2, 1)

        _, seqlen, _ = inpx.shape
        # xz = self.conv1d_in(inpx)
        xz = self.in_proj(inpx)
        xz = rearrange(xz, "b l d -> b d l")
        x, z = xz.chunk(2, dim=1)

        A = -torch.exp(self.A_log.float())
        disturbance = torch.randn_like(A) * self.epsilon
        A = (1 + self.epsilon) * A

        # A = self.robust_control(A, disturbance)
        D = self.D.float()

        x = F.silu(F.conv1d(input=x, weight=self.conv1d_x.weight, bias=self.conv1d_x.bias, padding='same',
                            groups=self.d_inner // 2))

        z = F.conv1d(input=z, weight=self.conv1d_z.weight, bias=self.conv1d_z.bias, padding='same',
                     groups=self.d_inner // 2)
        z = F.silu(z)

        x_dbl = self.x_proj(rearrange(x, "b d l -> (b l) d"))
        dt, B, C = torch.split(x_dbl, [self.dt_rank, self.d_state, self.d_state], dim=-1)

        dt = rearrange(self.dt_proj(dt), "(b l) d -> b d l", l=seqlen)
        B = rearrange(B, "(b l) dstate -> b dstate l", l=seqlen).contiguous()
        C = rearrange(C, "(b l) dstate -> b dstate l", l=seqlen).contiguous()

        A = self.sparse_approximation(A)
        B = self.sparse_approximation(B)
        C = self.sparse_approximation(C)

        y = selective_scan_fn(x,
                              dt,
                              A,
                              B,
                              C,
                              D,
                              z=None,
                              delta_bias=self.dt_proj.bias.float(),
                              delta_softplus=True,
                              return_last_state=None)

        xz2 = self.in_proj_2(inpy)
        xz2 = rearrange(xz2, "b l d -> b d l")
        x2, z2 = xz2.chunk(2, dim=1)

        x2 = F.silu(F.conv1d(input=x2, weight=self.conv1d_x_2.weight, bias=self.conv1d_x_2.bias, padding='same',
                             groups=self.d_inner // 2))

        z2 = F.conv1d(input=z2, weight=self.conv1d_z_2.weight, bias=self.conv1d_z_2.bias, padding='same',
                      groups=self.d_inner // 2)
        z2 = F.silu(z2)

        x_dbl2 = self.x_proj_2(rearrange(x2, "b d l -> (b l) d"))
        dt2, B2, C2 = torch.split(x_dbl2, [self.dt_rank, self.d_state, self.d_state], dim=-1)

        dt2 = rearrange(self.dt_proj_2(dt2), "(b l) d -> b d l", l=seqlen)
        B2 = rearrange(B2, "(b l) dstate -> b dstate l", l=seqlen).contiguous()
        C2 = rearrange(C2, "(b l) dstate -> b dstate l", l=seqlen).contiguous()

        A2 = self.sparse_approximation(A)
        B2 = self.sparse_approximation(B2)
        C2 = self.sparse_approximation(C2)
        y2 = selective_scan_fn(x2,
                               dt2,
                               A2,
                               B2,
                               C2,
                               D,
                               z=None,
                               delta_bias=self.dt_proj_2.bias.float(),
                               delta_softplus=True,
                               return_last_state=None)

        out1 = torch.cat([y, z], dim=1)
        out1 = rearrange(out1, "b d l -> b l d")
        out1 = self.out_proj(out1)

        out2 = torch.cat([y2, z2], dim=1)
        out2 = rearrange(out2, "b d l -> b l d")
        out2 = self.out_proj_2(out2)

        with torch.no_grad():
            yy = torch.mean(y, dim=[0, 1, 2])
            yy2 = torch.mean(y2, dim=[0, 1, 2])
            self.epsilon.copy_(self.epsilon * (yy - yy2).sigmoid())

        return out1, out2



class att_sparse_single(nn.Module):
    def __init__(self, channel):
        super(att_sparse_single, self).__init__()
        self.avgh = nn.AdaptiveAvgPool2d((None, 1))
        self.avgw = nn.AdaptiveAvgPool2d((1, None))
        self.stssm = SnycTwinSSM(d_model=channel // 2, d_state=8, d_conv=3, expand=1)

    def forward(self, x):
        _, in_c, _, _ = x.size()
        identity = x
        b, c, h, w = x.size()
        inp = torch.cat([self.avgh(x).squeeze(-1), self.avgw(x).squeeze(-2)], dim=-1)
        # print(inp.shape)
        k, q = self.stssm(inp)
        oupx = k.permute(0, 2, 1)
        oupy = q.permute(0, 2, 1)
        oup = torch.cat([oupx, oupy], dim=1)
        ouph, oupw = torch.split(oup, [h, w], dim=-1)
        ouph = ouph.unsqueeze(-1).sigmoid()
        oupw = oupw.unsqueeze(-2).sigmoid()
        out = identity * (oupw * ouph) + identity
        return out


from thop import profile

if __name__ == '__main__':
    model = att_sparse_single(32).cuda()
    feature = torch.ones(1, 32, 256, 256).cuda()
    # PAM_out = torch.randn(1, 32, 16, 16).cuda()
    flops, params = profile(model, (feature, ))
    print("-" * 50)
    print('FLOPs = ' + str(flops / 1000 ** 3) + ' G')
    print('Params = ' + str(params / 1000 ** 2) + ' M')



