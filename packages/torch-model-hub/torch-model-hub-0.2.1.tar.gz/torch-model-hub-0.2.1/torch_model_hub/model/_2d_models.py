from abc import ABC
import torch
from torch import nn
import torch.nn.functional as F

from ._text_cnn import TextCNN
from ._attention import (
    RNNAttention,
    CNNRNNAttention,
    RNNCNNAttention,
    ResRNNCNNAttention,
    TransformerEncoder,
    TransformerDecoder,
)


class Base2DModel(nn.Module, ABC):
    """
    A base 2D model class, inherits from nn.Module and ABC.
    Used as the base class for two-dimensional model construction,
    providing basic functionality for model transformation.
    """

    def __init__(self, in_features: int, embed_dim: int, hidden_size: int):
        """
        Initializes the base 2D model.
        
        Parameters:
        - in_features: Number of input features.
        - embed_dim: Dimension of the embedding.
        - hidden_size: Size of the hidden layer.
        
        Asserts that the hidden size is divisible by the embedding dimension when embed_dim is greater than 1.
        """
        super().__init__()  # Initialize the parent class
        if embed_dim <= 1:
            # If the embedding dimension is less than or equal to 1, perform simple unflattening operation
            self.reshape = nn.Unflatten(1, (-1, 1))
        else:
            assert hidden_size % embed_dim == 0, "hidden_size must be divisible by embed_dim."
            # Define a reshaping operation that first linearly transforms the input features to the hidden size,
            # then reshapes them to the specified embedding dimension
            self.reshape = nn.Sequential(
                nn.Linear(in_features, hidden_size), 
                nn.Unflatten(1, (-1, embed_dim))
            )
        self.model = None  # Initialize the model as None, to be defined in subclasses

    def forward(self, inputs: torch.Tensor):
        """
        Defines the forward pass of the base 2D model.
        
        Parameters:
        - inputs: Input tensor of shape (batch_size, in_features).
        
        Returns:
        - Output tensor after processing through the model, of shape (batch_size, out_features).
        """
        output = self.reshape(inputs)  # Reshape the input tensor
        return self.model(output)  # Pass the reshaped tensor through the model and return the output


class RNN2D(Base2DModel):
    """
    Model类继承自Base2DModel，主要用于构建和操作二维模型。
    它提供了加载模型数据、保存模型状态以及执行模型转换的功能。
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        hidden_size: int = 128,
        num_layers: int = 2,
        bidirectional=True,
        rnn=nn.GRU,
        dropout: float = 0.0,
        **kwargs,
    ):
        """
        初始化函数，用于设置神经网络的输入特征数、输出特征数、嵌入维度、RNN隐藏层大小、
        RNN层数、是否双向RNN、以及dropout比例。

        参数:
        in_features (int): 输入特征的数量。
        out_features (int): 输出特征的数量。
        embed_dim (int): 嵌入层的维度，默认为1。
        hidden_size (int): RNN隐藏层的大小，默认为128。
        num_layers (int): RNN的层数，默认为2。
        bidirectional (bool): 是否使用双向RNN，默认为True。
        rnn (nn.Module): RNN模型，默认为nn.GRU
        dropout (float): Dropout的比例，默认为0.0，表示不使用dropout。
        """
        # 调用父类的初始化方法，完成基础设置
        super().__init__(in_features, embed_dim, hidden_size)

        # 这里设置了RNN的输入维度、隐藏层大小、层数，是否双向，以及dropout比例
        self.model = rnn(
            input_size=embed_dim,
            hidden_size=hidden_size,
            num_layers=num_layers,
            bidirectional=bidirectional,
            batch_first=True,
            dropout=dropout,
            **kwargs
        )

        if embed_dim == 1:
            seq_len = in_features
        else:
            seq_len = hidden_size // embed_dim

        fc_dim = seq_len * hidden_size
        if bidirectional:
            fc_dim *= 2

        self.linear = nn.Linear(fc_dim, out_features)

    def forward(self, x: torch.Tensor):
        """
        实现前向传播过程

        参数:
        x (torch.Tensor): 输入的张量

        返回:
        torch.Tensor: 经过模型处理后的输出张量
        """
        # 对输入张量进行reshape操作，以符合模型输入要求
        x = self.reshape(x)
        # 通过self.model进行前向传播，此处模型的具体实现和功能未详细说明
        x, _ = self.model(x)
        # 将模型输出的张量展平，从第一个维度开始，以便进行全连接层处理
        x = x.flatten(start_dim=1)
        # 使用全连接层处理展平后的张量，并返回最终输出
        return self.linear(x)


class TextCNN2D(Base2DModel):
    """
    Examples
    --------
    >>> model = TextCNN2D(in_features=8, out_features=len(classes), embed_dim=16)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 16,
        hidden_size: int = 128,
        kernel_sizes=(2, 3, 4),
        cnn_channels: int = 64,
        activation=None,
        num_hidden_layer: int = 0,
        layer_norm=False,
        batch_norm=False,
        residual=False,
        dropout: float = 0.0,
        bias=False,
        **kwargs,
    ):
        super().__init__(in_features, embed_dim, hidden_size)
        self.model = TextCNN(
            embed_dim,
            kernel_sizes,
            cnn_channels,
            out_features,
            activation,
            num_hidden_layer,
            layer_norm,
            batch_norm,
            residual,
            dropout,
            bias,
            **kwargs,
        )


class RNNAttention2D(Base2DModel):
    """forward()方法有inputs和sequence_lengths两个参数, 不能直接作为模型用moddel-wrapper训练，
    否则会把y作为sequence_lengths参数传入

    Examples
    --------
    >>> model = RNNAttention2D(embed_dim, out_features=len(classes))
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        hidden_size: int = 128,
        num_heads: int = 1,
        num_layers: int = 2,
        rnn=nn.GRU,
        bidirectional=True,
        layer_norm=False,
        residual=False,
        dropout: float = 0.0,
        **kwargs,
    ):
        super().__init__(in_features, embed_dim, hidden_size)
        self.model = RNNAttention(
            embed_dim,
            out_features,
            hidden_size,
            num_layers,
            num_heads,
            rnn,
            bidirectional,
            layer_norm,
            residual,
            dropout,
            **kwargs,
        )


class CNNRNNAttention2D(Base2DModel):
    """
    Examples
    --------
    >>> model = CNNRNNAttention2D(embed_dim, out_features=2)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        seq_length: int = 16,
        cnn_channels: int = 64,
        kernel_sizes=(2, 3, 4),
        activation=None,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_heads: int = 1,
        rnn=nn.GRU,
        bidirectional=True,
        layer_norm=False,
        batch_norm=False,
        residual=False,
        dropout: float = 0.0,
        bias=False,
    ):
        super().__init__(in_features, embed_dim, hidden_size)
        self.model = CNNRNNAttention(
            embed_dim,
            out_features,
            seq_length,
            cnn_channels,
            kernel_sizes,
            activation,
            hidden_size,
            num_layers,
            num_heads,
            rnn,
            bidirectional,
            layer_norm,
            batch_norm,
            residual,
            dropout,
            bias,
        )


class RNNCNNAttention2D(Base2DModel):
    """
    Examples
    --------
    >>> model = RNNCNNAttention2D(embed_dim, out_features=2)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        seq_length: int = 16,
        cnn_channels: int = 64,
        kernel_sizes=(2, 3, 4),
        activation=None,
        hidden_size: int = 128,
        num_layers: int = 1,
        num_heads: int = 1,
        rnn=nn.GRU,
        bidirectional=True,
        layer_norm=False,
        batch_norm=False,
        dropout: float = 0.0,
        bias=False,
    ):
        super().__init__(in_features, embed_dim, hidden_size)
        self.model = RNNCNNAttention(
            embed_dim,
            out_features,
            seq_length,
            cnn_channels,
            kernel_sizes,
            activation,
            hidden_size,
            num_layers,
            num_heads,
            rnn,
            bidirectional,
            layer_norm,
            batch_norm,
            dropout,
            bias,
        )


class ResRNNCNNAttention2D(Base2DModel):
    """
    Examples
    --------
    >>> model = ResRNNCNNAttention2D(embed_dim, out_features=2)
    """

    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        eq_length: int = 16,
        cnn_channels: int = 64,
        kernel_sizes=(2, 3, 4),
        activation=None,
        hidden_size: int = 128,
        num_layers: int = 2,
        num_heads: int = 1,
        rnn=nn.GRU,
        bidirectional=True,
        layer_norm=False,
        batch_norm=False,
        dropout: float = 0.0,
        bias=False,
    ):
        super().__init__(in_features, embed_dim, hidden_size)
        self.model = ResRNNCNNAttention(
            embed_dim,
            out_features,
            eq_length,
            cnn_channels,
            kernel_sizes,
            activation,
            hidden_size,
            num_layers,
            num_heads,
            rnn,
            bidirectional,
            layer_norm,
            batch_norm,
            dropout,
            bias,
        )


class MultiheadSelfAttention2D(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 1,
        hidden_size: int = 128,
        num_heads: int = 1,
        dropout=0.2,
        bias=True,
        **kwargs,
    ):
        super().__init__()
        self.head = nn.Linear(in_features, hidden_size)
        self.unflatten = nn.Unflatten(1, (-1, embed_dim))
        self.att = nn.MultiheadAttention(
            embed_dim, num_heads, dropout, bias=bias, batch_first=True, **kwargs
        )
        self.fc = nn.Linear(hidden_size, out_features)

    def forward(self, src: torch.Tensor):
        x = self.head(src)
        x = F.silu(x)
        x = self.unflatten(x)
        x, _ = self.att(x, x, x)
        x = F.silu(x)
        return self.fc(x.flatten(1))


class TransformerEncoder2D(nn.Module):
    def __init__(
        self,
        in_features: int,
        out_features: int,
        embed_dim: int = 8,
        nhead: int = 1,
        num_layers: int = 1,
        hidden_size: int = 128,
        dim_feedforward: int = 128,
        activation=F.relu,
        norm_first=False,
        dropout=0.2,
        bias=True,
        **kwargs,
    ):
        super().__init__()
        self.head = nn.Linear(in_features, hidden_size)
        self.unflatten = nn.Unflatten(1, (-1, embed_dim))
        self.encoder = TransformerEncoder(
            embed_dim,
            nhead,
            num_layers,
            dim_feedforward,
            activation,
            norm_first,
            dropout,
            bias,
            **kwargs,
        )
        self.fc = nn.Linear(hidden_size, out_features)

    def forward(self, src: torch.Tensor):
        x = self.head(src)
        x = F.silu(x)
        x = self.unflatten(x)
        x = self.encoder(x)
        return self.fc(x.flatten(1))


class TransformerDecoder2D(nn.Module):
    def __init__(
        self,
        src_in_features: int,
        out_features: int,
        embed_dim: int = 8,
        tgt_in_features: int = None,
        nhead: int = 2,
        num_layers: int = 1,
        hidden_size: int = 128,
        dim_feedforward: int = 128,
        activation=F.relu,
        norm_first=False,
        dropout=0.2,
        bias=True,
        **kwargs,
    ):
        super().__init__()
        tgt_in_features = tgt_in_features or src_in_features
        self.src_head = nn.Linear(src_in_features, hidden_size)
        self.tgt_head = nn.Linear(tgt_in_features, hidden_size)
        self.unflatten = nn.Unflatten(1, (-1, embed_dim))
        self.decoder = TransformerDecoder(
            embed_dim,
            nhead,
            num_layers,
            dim_feedforward,
            activation,
            norm_first,
            dropout,
            bias,
            **kwargs,
        )
        self.fc = nn.Linear(hidden_size, out_features)

    def forward(self, src: torch.Tensor, tgt: torch.Tensor = None):
        src_out = self.src_head(src)
        src_out = F.silu(src_out)
        src_out = self.unflatten(src_out)
        tgt = tgt if tgt is not None else src
        tgt = self.tgt_head(tgt)
        tgt = F.silu(tgt)
        tgt = self.unflatten(tgt)
        out = self.decoder(src_out, tgt)
        return self.fc(out.flatten(1))


class Transformer2D(nn.Module):
    def __init__(
        self,
        src_in_features: int,
        out_features: int,
        embed_dim: int = 8,
        tgt_in_features: int = None,
        nhead: int = 2,
        num_encoder_layers: int = 1,
        num_decoder_layers: int = 1,
        hidden_size: int = 128,
        dim_feedforward: int = 128,
        activation=F.relu,
        norm_first=False,
        dropout=0.2,
        bias=True,
        **kwargs,
    ):
        super().__init__()
        tgt_in_features = tgt_in_features or src_in_features
        self.src_head = nn.Linear(src_in_features, hidden_size)
        self.tgt_head = nn.Linear(tgt_in_features, hidden_size)
        self.unflatten = nn.Unflatten(1, (-1, embed_dim))
        self.transformer = nn.Transformer(
            d_model=embed_dim,
            nhead=nhead,
            num_encoder_layers=num_encoder_layers,
            num_decoder_layers=num_decoder_layers,
            batch_first=True,
            activation=activation,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            norm_first=norm_first,
            bias=bias,
            **kwargs,
        )
        self.fc = nn.Linear(hidden_size, out_features)

    def forward(self, src: torch.Tensor, tgt: torch.Tensor = None):
        src_out = self.src_head(src)
        src_out = F.silu(src_out)
        src_out = self.unflatten(src_out)
        tgt = tgt if tgt is not None else src
        tgt = self.tgt_head(tgt)
        tgt = F.silu(tgt)
        tgt = self.unflatten(tgt)
        out = self.transformer(src_out, tgt)
        return self.fc(out.flatten(1))
