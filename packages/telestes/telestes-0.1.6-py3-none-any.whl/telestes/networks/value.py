import torch
import torch.nn as nn
import torch.optim as optim

from .architectures.transformer import TransformerBlock, AttentionGate
from .architectures.linear import LinearBlock


class ValueNetwork(nn.Module):
    def __init__(
        self,
        input_dims: int,
        transformer_layers: int = 2,
        linear_layers: int = 2,
        optimizer_class: optim.Optimizer = optim.Adam,
        device: str = 'cpu',
        **kwargs
    ):
        """
        Initialize the Value Network (Critic in A/C settings).
        """
        super(ValueNetwork, self).__init__()

        self.transformer_layers = transformer_layers

        if transformer_layers:
            transformer_hparams = {
                **kwargs.get("transformer", {})
            }
            self.transformer = nn.ModuleList(
                [
                    TransformerBlock(
                        embed_dims=input_dims,
                        **transformer_hparams
                    )
                    for _ in range(transformer_layers)
                ]
            )

            gate_hparams = {
                **kwargs.get("gate", {})
            }
            self.gate = AttentionGate(
                embed_dims=input_dims,
                **gate_hparams
            )

            self.normalizer = nn.LayerNorm(input_dims)

        linear_hparams = {
            **kwargs.get("linear", {})
        }
        self.linear = LinearBlock(
            input_dims=input_dims,
            output_dims=1,
            **linear_hparams
        )

        self.to(device)

        optimizer_hparams = {
            **kwargs.get("optimizer", {})
        }
        self.optimizer = optimizer_class(
            self.parameters(),
            **optimizer_hparams
        )

    def forward(
        self,
        state: torch.Tensor,
        mask=None
    ) -> torch.Tensor:
        """
        Output an evaluation of the current state.
        """
        out = state
        if self.transformer_layers:
            for layer in self.transformer:
                out = layer(out, out, out, mask)
            out = self.gate(out)
            out = self.normalizer(out)
        out = self.linear(out)
        value = out
        return value
        

