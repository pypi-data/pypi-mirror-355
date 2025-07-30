import torch
from torch import nn


class RMSNorm(nn.Module):
	def __init__(self, dim, eps=1e-6):
		super().__init__()
		self.weight = nn.Parameter(torch.ones(dim))
		self.eps = eps
	
	def forward(self, hidden_states):
		input_dtype = hidden_states.dtype
		hidden_states = hidden_states.to(torch.float32)
		variance = hidden_states.pow(2).mean(-1, keepdim=True)  # 计算隐状态的均方根
		hidden_states = hidden_states * torch.rsqrt(variance + self.eps)
		# 将隐状态除以其均方根后重新缩放
		return self.weight * hidden_states.to(input_dtype)


if __name__ == '__main__':
	batch_size = 4
	sent_length = 10
	word_dim = 16
	X = torch.randn(batch_size, sent_length, word_dim)
	output = RMSNorm(word_dim)(X)
	print(output.size())
