from functools import partial

import torch
import torch.utils
import torch.nn as nn

# [0] J. Ho, A. Jain, P. Abbeel. Denoising diffusion probabilistic models. https://arxiv.org/abs/2006.11239
# [1] A. Vaswani et al.. Attention is all you need. https://arxiv.org/abs/1706.03762

def ensure_proper_time_tensor(t, samples=None, device=None):
    if isinstance(t, int):
        if samples is None:
            raise ValueError("Transforming an integer time step to a tensor requires to know the number of samples.")
        t = torch.ones(samples, dtype=torch.long, device=device)*t
    elif isinstance(t, list):
        t = torch.tensor(t).to(device)
    elif torch.is_tensor(t):
        t = t.to(device)
    else:
        raise ValueError("Unsupported time step of type '{}'.".format(type(t)))

    return t

def check_time_tensor(t, max=None):
    if torch.any(t < 0):
        raise ValueError("Time steps must be nonnegative.")
    if max is not None and torch.any(t > max):
        raise ValueError("Time steps must be bounded by {}.".format(max))

class DDPM(nn.Module):
    """This implements the diffusion model of the paper [0]. The forward
    process uses the simple linear beta variance schedule."""

    def __init__(self, backward_model=None, N_steps=1000, min_beta=10**(-4), max_beta=0.02, rng=None, device=None):
        super().__init__()

        self.device = device
        self.backward_model = backward_model.to(device) if backward_model is not None else None
        if rng is not None:
            self.rng = rng.get_rng("torch")
        else:
            # We create a new Pytorch RNG with random seed.
            self.rng = torch.Generator()
            self.rng.manual_seed(torch.randint(2**15, size=(1, )[0]))

        self.N_steps = N_steps
        self.min_beta = min_beta
        self.max_beta = max_beta

        # The beta variance schedule is a simple linear schedule from minimum
        # to maximum. We add 0 to front to get the indexing to work correctly.
        self.betas = torch.cat((torch.tensor([0.0]), torch.linspace(min_beta, max_beta, self.N_steps)), dim=0).to(self.device)
        self.alphas = 1 - self.betas
        z = torch.cumprod(self.alphas, axis=0)
        self.alpha_bars = torch.cumprod(self.alphas, axis=0)

    def forward(self, x0, t, noise=None):
        """Add noise to x0 so that it is a sample from the distribution at time
        step t. With the final parameter a predetermined sample of noise from
        N(0, I) can be specified."""

        x0 = x0.to(self.device)
        # If x0 consists of a single sample, ensure it has proper dimensions.
        if len(x0.shape) == 1:
            x0 = torch.unsqueeze(x0, 0)
        n = x0.shape[0]

        t = ensure_proper_time_tensor(t, samples=n, device=self.device)
        check_time_tensor(t, max=self.N_steps)

        # Sample z in N(0,1) (or use the given noise) so that y = SD*z + MEAN
        # is distributed N(MEAN, SD^2).
        if noise is None:
            z = torch.randn(x0.size(), generator=self.rng, device=self.device)
        else:
            z = noise.to(self.device)
        a_bar = self.alpha_bars[t]
        y = (1 - a_bar).sqrt().reshape(n,1)*z + a_bar.sqrt().reshape(n,1)*x0

        return y

    def backward(self, xt, t):
        """Estimate noise that has been added to xt after t steps."""

        if self.backward_model is None:
            raise Exception("No backword process model defined.")

        xt = xt.to(self.device)
        # If xt consists of a single sample, ensure it has proper dimensions.
        if len(xt.shape) == 1:
            xt = torch.unsqueeze(xt, 0)

        t = t.to(self.device)
        
        return self.backward_model(xt, timestep=t)

    def denoise(self, xt, t):
        """Denoise x_t to obtain x_{t-1}."""
        
        xt = xt.to(self.device)
        # If xt consists of a single sample, ensure it has proper dimensions.
        if len(xt.shape) == 1:
            xt = torch.unsqueeze(xt, 0)
        n = xt.shape[0]

        t = ensure_proper_time_tensor(t, samples=n, device=self.device)
        check_time_tensor(t, max=self.N_steps)

        z = torch.randn(xt.size(), generator=self.rng, device=self.device)
        # Edit samples corresponding to t = 1 to be zeros.
        z[t == 1] = torch.zeros_like(z[t == 1])

        # Option 1 from the DDPM paper.
        sigma = self.betas[t].sqrt()
        # Option 2 from the DDPM paper.
        #sigma = (((1 - self.alpha_bars[t-1]) / (1 - self.alpha_bars[t]))*self.betas(t)).sqrt() if t > 1 else 0
        y = (1/self.alphas[t].sqrt()).reshape(n,1) * (xt - (self.betas[t] / (1-self.alpha_bars[t]).sqrt()).reshape(n,1) * self.backward(xt, t)) + sigma.reshape(n,1) * z
        
        return y

def sinusoidal_embedding(time_steps, dim):
    """Computes a sinusoidal embedding of dimension dim for time steps given by
    time_steps."""

    if dim % 2 != 0:
        raise ValueError("Time embedding dimension must be even.")

    embedding = torch.zeros(time_steps, dim)
    A = torch.arange(1, time_steps + 1).log().reshape(time_steps, 1)
    B = torch.arange(dim//2)*(1/dim)*torch.log(torch.tensor([10000]))
    embedding[:,::2] = torch.sin(torch.exp(A - B))
    embedding[:,1::2] = torch.cos(torch.exp(A - B))

    return embedding

class Block(nn.Module):
    """A simple convolution block consisting of a convolution followed by group
    normalization and SiLU activation. If residual_connection=True, then a
    residual connection is added around the block."""

    def __init__(self, channels_in, channels_out, residual_connection=False, kernel_size=3):
        super().__init__()

        if kernel_size % 2 != 1:
            raise ValueError("Kernel size not odd.")

        padding = (kernel_size - 1) // 2
        self.normalization = nn.GroupNorm(1, channels_out) if channels_out > 1 else nn.Identity()
        self.convolution = nn.Conv1d(channels_in, channels_out, kernel_size=kernel_size, padding=padding)
        self.activation = nn.SiLU()
        self.residual_connection = residual_connection
        self.residual_transformation = nn.Conv1d(channels_in, channels_out, 1) if channels_in != channels_out else nn.Identity()

    def forward(self, x):
        y = self.convolution(x)
        y = self.normalization(y)
        y = self.activation(y)
        if self.residual_connection:
            return y + self.residual_transformation(x)
        else:
            return y

class UNet(nn.Module):
    """Simple UNet model that starts from 8 channels on top and doubles the
    amount of channels when downsampling. Otherwise as in the original UNet
    paper. Time embeddings are added channelwise before the input is fed into
    the two convolution blocks per network level."""

    def __init__(self, input_size, time_steps=1000, time_embedding_dim=100, residual_connection=False, max_depth=5, debug=False, device=None, rng=None):
        super().__init__()

        self.debug = (lambda x: print(x)) if debug else (lambda x: None)

        if max_depth <= 0:
            raise ValueError("UNet depth must be positive.")

        self.device = device
        
        # This ensures determinism.
        if rng is not None:
            state_torch_global = rng.set_torch_global_rng_from()

        # We disable time embedding model creation if it is not needed.
        self.time_embedding_possible = not(time_steps is None or time_embedding_dim is None)

        # Sinusoidal time embedding.
        if self.time_embedding_possible:
            self.time_embedding = nn.Embedding(time_steps + 1, time_embedding_dim)
            try:
                self.time_embedding.weight.data = sinusoidal_embedding(time_steps + 1, time_embedding_dim)
            except:
                raise
            self.time_embedding.requires_grad_(False)
        else:
            self.time_embedding = None
        make_te_transformation = lambda dim_in, dim_out: nn.Sequential(nn.Linear(dim_in, dim_out), nn.GroupNorm(1, dim_out) if dim_out > 1 else nn.Identity(), nn.SiLU()) if self.time_embedding_possible else None

        BLOCK = partial(Block, kernel_size=3, residual_connection=residual_connection)
        
        # Figure out the downsampling sizes when dividing by two until the
        # length is 1 or max depth has been reached. We record these sizes to
        # be able to perform upsamling correctly.
        L = input_size
        depth = 0
        upsampling_sizes = []
        while L > 1 and depth < max_depth:
            upsampling_sizes.append(L)
            L = L // 2
            depth += 1

        self.depth = depth
        channel_counts = [2**(3+i) for i in range(self.depth)]

        # Create the sequence of channels sizes when going downward and upward.
        prev = 1
        down_parameters = []
        for n in range(len(channel_counts)):
            down_parameters.append((prev, channel_counts[n]))
            prev = channel_counts[n]
        down_parameters.append((prev, prev))
        up_parameters = [x[::-1] for x in down_parameters[:-1][::-1]]
        up_parameters[-1] = (up_parameters[-1][0], up_parameters[-1][0])

        # UNet down path.
        self.down_blocks = nn.ModuleList([])
        for n, (channels_in, channels_out) in enumerate(down_parameters):
            time_embedding_transformation = make_te_transformation(time_embedding_dim, channels_in)
            block = nn.Sequential(
                BLOCK(channels_in, channels_out),
                BLOCK(channels_out, channels_out)
            )
            down_transformation = nn.Conv1d(channels_out, channels_out, 4, 2, 1)
            self.down_blocks.append(nn.ModuleList([time_embedding_transformation, block, down_transformation]))

        # UNet up path.
        self.up_blocks = nn.ModuleList([])
        for n, (channels_in, channels_out) in enumerate(up_parameters):
            size = upsampling_sizes[-1 - n]
            time_embedding_transformation = make_te_transformation(time_embedding_dim, 2*channels_in)
            up_transformation = nn.ConvTranspose1d(channels_in, channels_in, 4, 2, 1) if size % 2 == 0 else nn.ConvTranspose1d(channels_in, channels_in, 3, 2, 0)
            block = nn.Sequential(
                BLOCK(2*channels_in, channels_in),
                BLOCK(channels_in, channels_out),
                BLOCK(channels_out, channels_out)
            )
            self.up_blocks.append(nn.ModuleList([time_embedding_transformation, block, up_transformation]))

        # Map to one channel and preserve size.
        self.final = nn.Conv1d(up_parameters[-1][0], 1, 3, 1, 1)

        # Restore the RNG.
        if rng is not None:
            rng.set_from_torch_global_rng(state_torch_global)

    def forward(self, x, timestep=None):
        assert timestep is None or isinstance(timestep, torch.Tensor)
        assert timestep is None or timestep.shape == torch.Size([x.shape[0]])
        if timestep is not None and not self.time_embedding_possible:
            raise Exception("Cannot use provided timestep information as the UNet was initialized without time embedding information.")
        
        x = x.to(self.device)
        self.debug("x of shape {}".format(x.shape))
        # Ensure proper channels in the input.
        if len(x.shape) == 2:
            x = x.reshape(x.shape[0], 1, -1)
        elif len(x.shape) == 1:
            x = x.reshape(1, 1, -1)
        self.debug("x reshaped to shape {}".format(x.shape))
        
        timestep = timestep.to(self.device) if timestep is not None else None
        t = self.time_embedding(timestep) if timestep is not None else None
        if t is not None:
            self.debug("Time embedding of shape {}.".format(t.shape))
        
        # Go down the UNet. We use residual block + downsampling except we
        # omit the last downsampling.
        self.debug("Starting left part...")
        left_inputs = []
        for n, (time_embedding_transformation, block, downsample) in enumerate(self.down_blocks):
            if t is not None:
                te = time_embedding_transformation(t)
                self.debug("Time embedding transformed to shape {}".format(te.shape))
                te = te.reshape(x.shape[0],-1,1)
                self.debug("Reshaped the transformed time embedding to shape {}.".format(te.shape))
                x = x + te
            self.debug("Added this to x.")
            self.debug("x of shape {} into block.".format(x.shape))
            x = block(x)
            self.debug("x of shape {} out from block.".format(x.shape))
            # Do not downsample and save left input when at the very bottom.
            if n < len(self.down_blocks) - 1:
                left_inputs.append(x)
                x = downsample(x)
            self.debug("Downsampled x to shape {}.".format(x.shape))
            self.debug("")

        self.debug("Starting right part...")
        for n, (time_embedding_transformation, block, upsample) in enumerate(self.up_blocks):
            if t is not None:
                te = time_embedding_transformation(t)
                self.debug("Transformed the time embedding to shape {}.".format(te.shape))
            self.debug("Umpsampling x of shape {}.".format(x.shape))
            y = torch.cat((left_inputs[-1-n], upsample(x)), dim=1)
            self.debug("Concatenated upsampled with a left input of size to get shape {}.".format(left_inputs[-1-n].shape))
            if t is not None:
                y = y + te.reshape(x.shape[0],-1,1)
            self.debug("Added this to x.")
            self.debug("x of shape {} into block.".format(x.shape))
            x = block(y)
            self.debug("x of shape {} out from block.".format(x.shape))

        x = self.final(x)
        x = x.squeeze(1) # Remove the channel.
        self.debug("Final x shape {}.".format(x.shape))
        return x
