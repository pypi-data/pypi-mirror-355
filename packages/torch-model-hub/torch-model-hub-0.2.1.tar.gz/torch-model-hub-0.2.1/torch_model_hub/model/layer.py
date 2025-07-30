import torch
from torch import nn
from torch.nn.utils.rnn import pack_padded_sequence, pad_packed_sequence
from torch_model_hub.norm import RMSNorm

__all__ = [
	'TextCNNLayer',
	'RNNLayer',
]


class TextCNNLayer(nn.Module):
	
	def __init__(self, embed_dim: int, seq_length: int = 16, out_channels: int = None, kernel_sizes=(2, 3, 4),
	             activation=None, layer_norm=False, batch_norm=False, dropout: float = 0.0, bias=False, **kwargs):
		"""
		:param embed_dim: word embedding维度
		:param seq_length: 句子序列长度
		:param out_channels: CNN out_channels, default embed_dim
		:param kernel_sizes: size of each CNN kernel
		:param activation: 激活函数, 如 nn.ReLU(inplace=True)
		:param layer_norm: 是否层正则化
		:param batch_norm: 是否层批则化
		:param dropout: dropout
		:param bias:
		
		Examples::

        >>> input = torch.randn(2, 10, 100)
        >>> m = TextCNNLayer(embed_dim=100, seq_length=16)
        >>> output = m(input)
        >>> print(output.size())
        torch.Size([2, 48, 100])  # (batch_size, len(kernel_sizes) * seq_length, embed_dim)
		"""
		super().__init__()
		self.layer_norm = layer_norm
		out_channels = out_channels or embed_dim
		activation = activation or nn.SiLU(inplace=True)
		if batch_norm:
			self.convs = nn.ModuleList([
				nn.Sequential(
					nn.Conv1d(in_channels=embed_dim, out_channels=out_channels, kernel_size=kernel_size, bias=bias, **kwargs),
					nn.BatchNorm1d(num_features=out_channels),
					activation,
					nn.AdaptiveMaxPool1d(seq_length)
				) for kernel_size in kernel_sizes
			])
		else:
			self.convs = nn.ModuleList([
				nn.Sequential(
					nn.Conv1d(in_channels=embed_dim, out_channels=out_channels, kernel_size=kernel_size, bias=bias, **kwargs),
					activation,
					nn.AdaptiveMaxPool1d(seq_length)
				) for kernel_size in kernel_sizes
			])
		if layer_norm:
			self.norm = nn.LayerNorm(out_channels)

		if 0.0 < dropout < 1.0:
			self.dropout = nn.Dropout(dropout)
		else:
			self.dropout = None
	
	def forward(self, inputs: torch.Tensor):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, seq_length * len(kernel_sizes), out_channels)]
		"""
		inputs = inputs.transpose(2, 1).contiguous()
		output = torch.cat([conv(inputs) for conv in self.convs], dim=-1)
		output = output.transpose(2, 1).contiguous()
		if self.layer_norm:
			output = self.norm(output)
		if self.dropout:
			output = self.dropout(output)
		return output


class RNNLayer(nn.Module):
	"""
	Examples
	--------
	>>> from nlpx.text_token import Tokenizer
	>>> from nlpx.model import RNNAttention
	>>> tokenizer = Tokenizer(corpus)
	>>> rnn = RNNLayer(embed_dim)
	"""
	
	def __init__(self, embed_dim: int, hidden_size: int = 64, num_layers: int = 1, rnn=nn.GRU,
	             bidirectional=True, layer_norm=False, dropout: float = 0.0, **kwargs):
		"""
		:param embed_dim: RNN的input_size，word embedding维度
		:param hidden_size: RNN的hidden_size, RNN隐藏层维度
		:param num_layers: RNN的num_layers, RNN层数
		:param num_layers: RNN的num_layers, RNN层数
		:param rnn: 所用的RNN模型：GRU和LSTM，默认是GRU
		:param layer_norm：是否层正则化
		:param dropout：
		
		Examples::

        >>> input = torch.randn(2, 10, 100)
        >>> m = RNNLayer(embed_dim=100, hidden_size=16)
        >>> output = m(input)
        >>> print(output.size())
        torch.Size([2, 10, 32])  # (batch_size, sequence_length, 2 * hidden_size), bidirectional=True
		"""
		
		super().__init__()
		self.layer_norm = layer_norm
		self.rnn = rnn(input_size=embed_dim, hidden_size=hidden_size, num_layers=num_layers,
		               bidirectional=bidirectional, batch_first=True, dropout=dropout, **kwargs)
		if layer_norm:
			self.norm = nn.LayerNorm((hidden_size << 1) if bidirectional else hidden_size)
	
	def forward(self, inputs: torch.Tensor, sequence_lengths: torch.IntTensor = None):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)], sequence_length是不确定的
		:param sequence_lengths: [torch.IntTensor] 序列实际长度
		:return: [(batch_size, sequence_length, 2 * hidden_size)] when bidirectional is True
		:return: [(batch_size, sequence_length, hidden_size)] when bidirectional is False
		"""
		self.rnn.flatten_parameters()  # RNN module weights are not part of single contiguous chunk of memory.
		if sequence_lengths is not None and torch.all(sequence_lengths):
			# 在GPU上会报错:'lengths' argument should be a 1D CPU int64 tensor, but got 1D cuda:0 Long tensor
			output = pack_padded_sequence(inputs, sequence_lengths.cpu(), batch_first=True, enforce_sorted=False)
			output, _ = self.rnn(output)
			output, _ = pad_packed_sequence(output, batch_first=True)
		else:
			output, _ = self.rnn(inputs)  # [(batch_size, sequence_length, 2 * hidden_size)]
		
		if self.layer_norm:
			output = self.norm(output)
		return output

