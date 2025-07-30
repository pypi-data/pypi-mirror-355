import torch
import numpy as np
from typing import Tuple, Mapping
from torch.utils.data import Dataset

class BertDataset(Dataset):
	""" 
	当数据不大时，使用tokenizer.batch_encode_plus()将数据全部tokenize后，直接使用该类
	配合BertCollator使用 

	Example:
		>>> from transformers import BertTokenizer
		>>> tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
		>>> texts = ["Hello, world!", "Bert is great."]
		>>> labels = [0, 1]
		>>> tokenizies = tokenizer.batch_encode_plus(
				texts,
				max_length=66,
				padding="max_length",
				truncation=True,
				return_token_type_ids=True,
				return_attention_mask=True,
				return_tensors="pt",
			)
		>>> dataset = BertDataset(tokenizies, labels)
		>>> for item in dataset:
				print(item)
				# Output: ({'input_ids': tensor(...), 'attention_mask': tensor(...), 'token_type_ids': tensor(...)}, 0)
	"""

	def __init__(self, tokenizies: Mapping[str, torch.Tensor], labels: np.ndarray):
		super().__init__()
		self.tokenizies = tokenizies
		self.labels = labels

	def __getitem__(self, index: int) -> Tuple[Mapping[str, torch.Tensor], int]:
		return {k: v[index] for k, v in self.tokenizies.items()}, self.labels[index]

	def __len__(self):
		return len(self.labels)
		