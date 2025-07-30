import math
import torch
from torch import nn
from typing import Optional
from .rotary_emb import precompute_freqs_cis, apply_rotary_emb, apply_rotary_emb_self


class RotaryEmbedding(nn.Module):
	def __init__(self, embed_dim: int, max_length: int = 100000, theta: float = 10000.0):
		"""
		:param embed_dim: word embedding维度
		:param max_length: max length of sequences
		:param theta (float, optional): Scaling factor for frequency computation. Defaults to 10000.0.
		"""
		super().__init__()
		self.freqs_cis = precompute_freqs_cis(embed_dim, max_length * 2, theta)
		self.qw = nn.Linear(in_features=embed_dim, out_features=embed_dim)
		self.kw = nn.Linear(in_features=embed_dim, out_features=embed_dim)
	
	def forward(self, token_embedding: torch.Tensor, start_pos: int = 0):
		"""
		:param token_embedding:
		:param start_pos:
		:return: query, key with position embedding
		"""
		seq_length = token_embedding.shape[1]
		self.freqs_cis = self.freqs_cis.to(token_embedding.device)
		freqs_cis = self.freqs_cis[start_pos: start_pos + seq_length]
		query = self.qw(token_embedding)
		key = self.kw(token_embedding)
		return apply_rotary_emb(query, key, freqs_cis=freqs_cis)


class SelfRotaryEmbedding(nn.Module):
	def __init__(self, embed_dim: int, max_length: int = 100000, theta: float = 10000.0):
		"""
		:param embed_dim: word embedding维度
		:param max_length: max length of sequences
		:param theta (float, optional): Scaling factor for frequency computation. Defaults to 10000.0.
		"""
		super().__init__()
		self.freqs_cis = precompute_freqs_cis(embed_dim, max_length * 2, theta)
	
	def forward(self, token_embedding: torch.Tensor, start_pos: int = 0):
		"""
		:param token_embedding:
		:param start_pos:
		:return: query, key with position embedding
		"""
		seq_length = token_embedding.shape[1]
		self.freqs_cis = self.freqs_cis.to(token_embedding.device)
		freqs_cis = self.freqs_cis[start_pos: start_pos + seq_length]
		return apply_rotary_emb_self(token_embedding, freqs_cis=freqs_cis)


class Position(nn.Module):
	
	def __init__(self, embed_dim: int, max_length: int = 5000, alpha: float = 0.2):
		super().__init__()
		den = torch.exp(- torch.arange(0, embed_dim, 2) * math.log(10000) / embed_dim)
		pos = torch.arange(0, max_length).view(max_length, 1)
		pos_embedding = torch.zeros((max_length, embed_dim))
		pos_embedding[:, 0::2] = torch.sin(pos * den)
		pos_embedding[:, 1::2] = torch.cos(pos * den)
		pos_embedding = pos_embedding.unsqueeze(-2)
		
		self.alpha = alpha
		self.register_buffer('pos_embedding', pos_embedding)
	
	def forward(self, token_embedding: torch.Tensor):
		return (1 - self.alpha) * token_embedding + self.alpha * self.pos_embedding[:token_embedding.size(0), :]


class PositionalEncoding(nn.Module):
	
	def __init__(self, embed_dim: int, vocab_size: Optional[int] = None, embedding=None,
	             padding_idx: Optional[int] = None, max_length: int = 5000, alpha: float = 0.2, dropout: float = 0.):
		super().__init__()
		if dropout:
			self.embedding = nn.Sequential(
				EmbeddingLayer(embed_dim, vocab_size, embedding, padding_idx),
			    Position(embed_dim, max_length, alpha),
				nn.Dropout(dropout)
			)
		else:
			self.embedding = nn.Sequential(
				EmbeddingLayer(embed_dim, vocab_size, embedding, padding_idx),
				Position(embed_dim, max_length, alpha)
			)
		
	def forward(self, input_ids: torch.Tensor):
		return self.embedding(input_ids)
