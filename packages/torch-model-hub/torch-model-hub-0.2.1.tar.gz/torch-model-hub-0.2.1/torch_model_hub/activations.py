import torch
from torch import nn
from torch.nn import functional as F


class SwiGLU(nn.Module):
	
	def __init__(self, hidden_size) -> None:
		super().__init__()
		self.w1 = nn.Parameter(torch.Tensor(hidden_size, hidden_size))
		self.w2 = nn.Parameter(torch.Tensor(hidden_size, hidden_size))
		self.w3 = nn.Parameter(torch.Tensor(hidden_size, hidden_size))
	
	def forward(self, x):
		x1 = F.linear(x, self.w1)
		x2 = F.linear(x, self.w2)
		hidden = F.silu(x1) * x2
		return F.linear(hidden, self.w3)


if __name__ == '__main__':
	batch_size = 4
	sent_length = 10
	word_dim = 16
	X = torch.randn(batch_size, sent_length, word_dim)
	fc = nn.Sequential(
		nn.Linear(in_features=word_dim, out_features=word_dim),
		SwiGLU(word_dim)
	)
	print(fc(X).size())
