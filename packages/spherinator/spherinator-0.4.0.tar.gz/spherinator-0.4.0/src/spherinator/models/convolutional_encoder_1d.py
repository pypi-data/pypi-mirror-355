from typing import Optional

import torch
import torch.nn as nn

from .consecutive_conv_1d_layers import ConsecutiveConv1DLayer
from .weights_provider import WeightsProvider


class ConvolutionalEncoder1D(nn.Module):
    def __init__(
        self,
        input_dim: list[int],
        output_dim: int,
        cnn_layers: list[ConsecutiveConv1DLayer] = [],
        weights: Optional[WeightsProvider] = None,
        freeze: bool = False,
    ) -> None:
        """ConvolutionalEncoder1D initializer
        Args:
            input_dim (tuple[int, int]): The number of input features
            output_dim (int): The number of output features
            cnn_layers (list[ConsecutiveConv1DLayer]): The list of consecutive convolutional layers
            weights (Optional[WeightsProvider], optional): The weights to load. Defaults to None.
            freeze (bool, optional): Whether to freeze the model. Defaults to False.
        """
        super().__init__()

        self.input_dim = input_dim
        self.output_dim = output_dim

        self.example_input_array = torch.randn(1, *input_dim)

        layers = []
        for layer in cnn_layers:
            layers.append(layer.get_model())
        self.cnn = nn.Sequential(*layers)

        self.fc = nn.Sequential(
            nn.Flatten(),
            nn.LazyLinear(output_dim),
        )

        if weights is not None:
            self.load_state_dict(weights.get_state_dict())
        if freeze:
            for param in self.parameters():
                param.requires_grad = False

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        x = self.cnn(x)
        x = self.fc(x)
        return x
