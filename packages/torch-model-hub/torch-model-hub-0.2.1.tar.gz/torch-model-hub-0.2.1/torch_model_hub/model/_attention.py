import math
import torch
from torch import nn
from typing import Optional
import torch.nn.functional as F
from .layer import TextCNNLayer, RNNLayer
from .embedding import RotaryEmbedding, SelfRotaryEmbedding


class RotaryAttention(nn.Module):
	def __init__(self, embed_dim: int, num_heads: int = 1, max_length: int = 100000, theta: float = 10000.0,
	             dropout: float = 0., bias: bool = True):
		"""
		:param embed_dim: word embedding维度
		:param num_heads: Number of parallel attention heads.
		:param max_length: max length of sequences
		:param theta (float, optional): Scaling factor for frequency computation. Defaults to 10000.0.
		"""
		super().__init__()
		self.rotary_embedding = RotaryEmbedding(embed_dim, max_length, theta)
		self.attention = nn.MultiheadAttention(embed_dim, num_heads, dropout, bias)
	
	def forward(self, inputs: torch.Tensor, mask: Optional[torch.Tensor] = None, start_pos: int = 0):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:param mask: [(batch_size, sequence_length, embed_dim)]
		:param start_pos:
		:return: [(batch_size, sequence_length, embed_dim)]
		"""
		query, key = self.rotary_embedding(inputs, start_pos)
		return self.attention(query, key, inputs, attn_mask=mask)


def attention(query: torch.Tensor, key: torch.Tensor, value: torch.Tensor):
	batch_size, length, d_k = key.size()
	key = key.contiguous()
	scores = torch.matmul(query, key.view(batch_size, d_k, length)) / math.sqrt(d_k)
	scores = F.softmax(scores, dim=-1)
	return torch.matmul(scores, value).sum(dim=1)


class ClassSelfAttention(nn.Module):

	def __init__(self, embed_dim: int):
		super().__init__()
		self.w_omega = nn.Parameter(torch.empty(embed_dim, embed_dim))
		self.u_omega = nn.Parameter(torch.empty(embed_dim, 1))
		# self.w_omega = nn.Parameter(torch.Tensor(embed_dim, embed_dim))
		# self.u_omega = nn.Parameter(torch.Tensor(embed_dim, 1))
		nn.init.uniform_(self.w_omega, -0.1, 0.1)
		nn.init.uniform_(self.u_omega, -0.1, 0.1)

	def forward(self, inputs: torch.Tensor):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, embed_dim)]
		"""
		u = torch.tanh(torch.matmul(inputs, self.w_omega))
		att = torch.matmul(u, self.u_omega)
		att_score = F.softmax(att, dim=1)
		value = inputs * att_score
		return torch.sum(value, dim=1)


class RotaryClassSelfAttention(nn.Module):

	def __init__(self, embed_dim: int, max_length: int = 100000, theta: float = 10000.0):
		super().__init__()
		self.rotary_embedding = SelfRotaryEmbedding(embed_dim, max_length, theta)
		self.w_omega = nn.Parameter(torch.Tensor(embed_dim, embed_dim))
		self.u_omega = nn.Parameter(torch.Tensor(embed_dim, 1))
		nn.init.uniform_(self.w_omega, -0.1, 0.1)
		nn.init.uniform_(self.u_omega, -0.1, 0.1)

	def forward(self, inputs: torch.Tensor, start_pos: int = 0):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:param start_pos:
		:return: [(batch_size, embed_dim)]
		"""
		rotary = self.rotary_embedding(inputs, start_pos)
		u = torch.tanh(torch.matmul(rotary, self.w_omega))
		att = torch.matmul(u, self.u_omega)
		att_score = F.softmax(att, dim=1)
		value = inputs * att_score
		return torch.sum(value, dim=1)


class MultiHeadClassSelfAttention(nn.Module):

	def __init__(self, embed_dim: int, num_heads: int = 1):
		super().__init__()
		self.num_heads = num_heads
		self.attention = ClassSelfAttention(num_heads * embed_dim)

	def forward(self, inputs: torch.Tensor):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, num_heads * embed_dim)]
		"""
		if self.num_heads > 1:
			inputs = torch.concat([inputs for _ in range(self.num_heads)], dim=-1)
		return self.attention(inputs)


class RNNAttention(nn.Module):
	""" forward()方法有inputs和sequence_lengths两个参数, 不能直接作为模型用moddel-wrapper训练，
	否则会把y作为sequence_lengths参数传入

	Examples
	--------
	>>> model = RNNAttention(embed_dim, out_features=len(classes))
	"""

	def __init__(self, embed_dim: int, out_features: int, hidden_size: int = 64, num_layers: int = 2, 
				 num_heads: int = 1,rnn=nn.GRU, bidirectional=True, layer_norm=False, residual=False,
				 dropout: float = 0.0, **kwargs):
		"""
		如果是英文、分词, 不用residual 效果比较好
		
		:param embed_dim: RNN的input_size，word embedding维度
		:param out_features: 输出维度
		:param hidden_size: RNN的hidden_size, RNN隐藏层维度
		:param num_layers: RNN的num_layers, RNN层数
		:param num_layers: RNN的num_layers, RNN层数
		:param num_heads: 抽头数
		:param rnn: 所用的RNN模型：GRU和LSTM，默认是GRU
		:param bidirectional： 是否是双向RNN
		:param layer_norm：是否层正则化
		:param residual: 是否残差
		:param dropout：
		"""
	
		super().__init__()
		self.residual = residual
		rnn_output_size = hidden_size << 1 if bidirectional else hidden_size
		attn_embed_dim = rnn_output_size + embed_dim if residual else rnn_output_size
		self.rnn = RNNLayer(embed_dim, hidden_size, num_layers, rnn, bidirectional, layer_norm, dropout, **kwargs)
		if layer_norm:
			self.attention = nn.Sequential(
				MultiHeadClassSelfAttention(attn_embed_dim, num_heads),
				nn.LayerNorm(attn_embed_dim),
			)
		else:
			self.attention = MultiHeadClassSelfAttention(attn_embed_dim, num_heads)
	
		# 定义全连接层
		self.fc = nn.Linear(attn_embed_dim * num_heads, out_features)
		if 0.0 < dropout < 1.0:
			self.fc = nn.Sequential(
				nn.Dropout(dropout),
				self.fc
			)

	def forward(self, inputs: torch.Tensor, sequence_lengths: Optional[torch.IntTensor] = None):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:param sequence_lengths: [torch.IntTensor] 序列实际长度
		:return: [(batch_size, out_features)]
		"""
		output = self.rnn(inputs, sequence_lengths)  # [(batch_size, sequence_length, rnn_output_size)]
		if self.residual:
			output = torch.cat((output, inputs), dim=2)
		output = self.attention(output)  # [(batch_size, attn_embed_dim)]
		return self.fc(output)
	

class CNNRNNAttention(nn.Module):
	"""
	Examples
	--------
	>>> model = CNNRNNAttention(embed_dim, out_features=2)
	"""
	
	def __init__(self, embed_dim: int, out_features: int, seq_length: int = 16, cnn_channels: int = 64, 
			  	 kernel_sizes=(2, 3, 4), activation=None, hidden_size: int = 64, num_layers: int = 2, 
				 num_heads: int = 1, rnn=nn.GRU, bidirectional=True, layer_norm=False, batch_norm=False,
	             residual=False, dropout: float = 0.0, bias=False):
		"""
		:param embed_dim: RNN的input_size，word embedding维度
		:param cnn_channels: CNN out_channels
		:param kernel_sizes: size of each CNN kernel
		:param activation: CNN 激活函数
		:param hidden_size: RNN的hidden_size, RNN隐藏层维度
		:param num_layers: RNN的num_layers, RNN层数
		:param num_heads: 抽头数
		:param out_features:
		:param rnn: 所用的RNN模型：GRU和LSTM，默认是GRU
		:param bidirectional： 是否是双向RNN
		:param layer_norm：是否层正则化
		:param residual: 是否残差
		:param batch_norm: 是否层批则化
		:param dropout：
		:param bias：
		"""
		
		super().__init__()
		cnn_channels = cnn_channels or embed_dim
		self.cnn = TextCNNLayer(embed_dim, seq_length, cnn_channels, kernel_sizes, activation, layer_norm, batch_norm, bias)
		self.attn = RNNAttention(cnn_channels, out_features, hidden_size, num_layers, num_heads, rnn, bidirectional,
		                         layer_norm, residual, dropout)
		
	def forward(self, inputs: torch.Tensor):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, out_features)]
		"""
		output = self.cnn(inputs)
		return self.attn(output)


class RNNCNNAttention(nn.Module):
	"""forward()方法有inputs和sequence_lengths两个参数, 不能直接作为模型用moddel-wrapper训练，
	否则会把y作为sequence_lengths参数传入

	Examples
	--------
	>>> model = RNNCNNAttention(embed_dim, out_features=len(classes))
	"""
	
	def __init__(self, embed_dim: int, out_features: int, seq_length: int = 16, cnn_channels: int = 64,
			    kernel_sizes=(2, 3, 4), activation=None, hidden_size: int = 64, num_layers: int = 1, num_heads: int = 1,
	            rnn=nn.GRU, bidirectional=True, layer_norm=False, batch_norm=False,
	            dropout: float = 0.0, bias=False):
		"""
		:param embed_dim: RNN的input_size，word embedding维度
		:param out_features: 输出维度
		:param cnn_channels: CNN out_channels
		:param kernel_sizes: size of each CNN kernel
		:param activation: CNN 激活函数
		:param hidden_size: RNN的hidden_size, RNN隐藏层维度
		:param num_layers: RNN的num_layers, RNN层数
		:param num_heads: 抽头数
		:param rnn: 所用的RNN模型：GRU和LSTM，默认是GRU
		:param bidirectional： 是否是双向RNN
		:param layer_norm：是否层正则化
		:param batch_norm: 是否层批则化
		:param dropout：
		:param bias：
		"""
		super().__init__()
		cnn_channels = cnn_channels or embed_dim
		rnn_output_size = (hidden_size << 1) if bidirectional else hidden_size
		self.rnn = RNNLayer(embed_dim, hidden_size, num_layers, rnn, bidirectional, layer_norm, dropout)
		self.cnn = TextCNNLayer(rnn_output_size, seq_length, cnn_channels, kernel_sizes, activation, layer_norm, batch_norm, bias)
		self.attention = MultiHeadClassSelfAttention(cnn_channels, num_heads)
	
		# 定义全连接层
		self.fc = nn.Linear(cnn_channels * num_heads, out_features)
		if 0.0 < dropout < 1.0:
			self.fc = nn.Sequential(
				nn.Dropout(dropout),
				self.fc
			)

	def forward(self, inputs: torch.Tensor, sequence_lengths: Optional[torch.IntTensor] = None):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:param sequence_lengths: [torch.IntTensor] 序列实际长度
		:return: [(batch_size, out_features)]
		"""
		output = self.rnn(inputs, sequence_lengths)
		output = self.cnn(output)
		output = self.attention(output)
		return self.fc(output)


class ResRNNCNNAttention(nn.Module):
	"""forward()方法有inputs和sequence_lengths两个参数, 不能直接作为模型用moddel-wrapper训练，
	否则会把y作为sequence_lengths参数传入
	
	Examples
	--------
	>>> model = ResRNNCNNAttention(embed_dim, out_features=len(classes))
	"""
	
	def __init__(self, embed_dim: int, out_features: int, seq_length: int = 16, cnn_channels: int = 64, 
			  	 kernel_sizes=(2, 3, 4), activation=None, hidden_size: int = 64, num_layers: int = 2, 
				 num_heads: int = 1, rnn=nn.GRU, bidirectional=True, layer_norm=False, batch_norm=False,
	             dropout: float = 0.0, bias=False):
		"""
		:param embed_dim: RNN的input_size，word embedding维度
		:param out_features: 输出维度
		:param cnn_channels: CNN out_channels
		:param kernel_sizes: size of each CNN kernel
		:param activation: CNN 激活函数
		:param hidden_size: RNN的hidden_size, RNN隐藏层维度
		:param num_layers: RNN的num_layers, RNN层数
		:param num_heads: 抽头数
		:param rnn: 所用的RNN模型：GRU和LSTM，默认是GRU
		:param bidirectional： 是否是双向RNN
		:param layer_norm：是否层正则化
		:param batch_norm: 是否层批则化
		:param dropout：
		:param bias：
		"""
		super().__init__()
		cnn_channels = cnn_channels or embed_dim
		rnn_output_size = (hidden_size << 1) if bidirectional else hidden_size
		self.rnn = RNNLayer(embed_dim, hidden_size, num_layers, rnn, bidirectional, layer_norm, dropout)
		self.cnn = TextCNNLayer(rnn_output_size, seq_length, cnn_channels, kernel_sizes, activation, layer_norm, batch_norm, bias)
		self.attention = MultiHeadClassSelfAttention(cnn_channels, num_heads)
		self.res_attention = MultiHeadClassSelfAttention(embed_dim + rnn_output_size, num_heads)
	
		# 定义全连接层
		self.fc = nn.Linear((embed_dim + cnn_channels + rnn_output_size) * num_heads, out_features)
		if 0.0 < dropout < 1.0:
			self.fc = nn.Sequential(
				nn.Dropout(dropout),
				self.fc
			)
		# if batch_norm:
		# 	self.fc = nn.Sequential(
		# 		nn.BatchNorm1d((embed_dim + cnn_channels + rnn_output_hidden_size) * num_heads),
		# 		self.fc
		# 	)

	def forward(self, inputs: torch.Tensor, sequence_lengths: Optional[torch.IntTensor] = None):
		"""
		:param inputs: [(batch_size, sequence_length, embed_dim)]
		:param sequence_lengths: [torch.IntTensor] 序列实际长度
		:return: [(batch_size, out_features)]
		"""
		rnn_output = self.rnn(inputs, sequence_lengths)  # [(batch_size, sequence_length, 2 * hidden_size)]
		rnn_cnn_output = self.cnn(rnn_output)     # [(batch_size, seq_length * len(kernel_sizes), cnn_channels)]
		rnn_cnn_attn_output = self.attention(rnn_cnn_output)   # [(batch_size, num_heads * out_channels)]
		
		# [(batch_size, num_heads * (embed_dim + 2 * hidden_size))]
		res_output = self.res_attention(torch.cat((inputs, rnn_output), dim=2))
		
		output = torch.cat([res_output, rnn_cnn_attn_output], dim=1)
		return self.fc(output)


class TransformerEncoder(nn.Module):

	def __init__(self, embed_dim: int, num_heads: int = 2, num_layers: int = 1, dim_feedforward: int = 128, activation=F.relu, 
			  norm_first= False, dropout=0.2, bias=True):
		super().__init__()
		encoder_layer = nn.TransformerEncoderLayer(embed_dim, num_heads, dim_feedforward=dim_feedforward, batch_first=True, 
											activation= activation, dropout=dropout, norm_first=norm_first, bias=bias)
		self.encoder = nn.TransformerEncoder(encoder_layer, num_layers, enable_nested_tensor=(num_heads & 1 == 0))

	def forward(self, src: torch.Tensor, 
			mask: Optional[torch.Tensor] = None,
            src_key_padding_mask: Optional[torch.Tensor] = None,
            is_causal: Optional[bool] = None) -> torch.Tensor:
		"""
		:param src: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, sequence_length, embed_dim)]
		"""
		return self.encoder(src, mask, src_key_padding_mask, is_causal)
	

class TransformerDecoder(nn.Module):

	def __init__(self, embed_dim: int, num_heads: int = 1, num_layers: int = 1, dim_feedforward: int = 128, activation=F.relu, 
			  norm_first= False, dropout=0.2, bias=True):
		super().__init__()
		decoder_layer = nn.TransformerDecoderLayer(embed_dim, num_heads, dim_feedforward=dim_feedforward, batch_first=True,
											activation= activation, dropout=dropout, norm_first=norm_first, bias=bias)
		self.decoder = nn.TransformerDecoder(decoder_layer, num_layers)

	def forward(self, src: torch.Tensor, tgt: torch.Tensor, src_mask: Optional[torch.Tensor] = None, 
			tgt_mask: Optional[torch.Tensor] = None, tgt_key_padding_mask: Optional[torch.Tensor] = None,
            memory_key_padding_mask: Optional[torch.Tensor] = None, tgt_is_causal: Optional[bool] = None,
            memory_is_causal: bool = False) -> torch.Tensor:
		"""
		:param src: [(batch_size, sequence_length, embed_dim)]
		:return: [(batch_size, sequence_length, embed_dim)]
		"""
		return self.decoder(tgt, src, tgt_mask, src_mask, tgt_key_padding_mask, memory_key_padding_mask, tgt_is_causal, memory_is_causal)
  