import torch
import numpy as np
from typing import Tuple, Mapping, Union, List
from transformers import PreTrainedTokenizer
from transformers.utils.generic import PaddingStrategy


class BertCollator:
	"""配合BertDataset使用
	传入({input_id, attention_mask, token_type_id}, labels), 
	返回({input_ids: [], attention_mask: [], token_type_ids: []}, labels),
	"""

	def __call__(self, examples: List[Tuple[Mapping, int]]) -> Mapping[str, torch.Tensor]:
		tokenizes, labels = zip(*examples)
		result = {k: [] for k in tokenizes[0].keys()}
		for d in tokenizes:
			for k, v in d.items():
				result[k].append(v)
		result = {k: torch.stack(v) for k, v in result.items()}
		# 分类用cross_entropy损失函数时，labels需要是np.int64类型（torch.long）
		result['labels'] = torch.from_numpy(np.asarray(labels, dtype=np.int64))

		return result


class BertTokenizeCollator:
	"""
	当数据量较大时，需要分批tokenize,此时就需要使用该类
	可以和TextDataset、TextDFDataset等配合使用
	传入的是(text, label), 返回的是({input_ids: [], attention_mask: [], token_type_ids: []}, labels)
	"""
	
	def __init__(self, tokenizer: PreTrainedTokenizer, max_length: int = 512,  
			  	padding: Union[bool, str, PaddingStrategy] = True, truncation=True, 
				return_tensors='pt', return_token_type_ids=False, **kwargs):
		"""
        初始化Collator。
        
        :param tokenizer: 用于将文本转换为token的tokenizer。
        :param max_length: 文本的最大长度，默认为512。
        :param padding: 是否进行padding，默认为True。
        :param truncation: 是否进行截断，默认为True。
        :param return_tensors: 返回张量类型，默认为'pt'。
        :param return_token_type_ids: 是否返回token type ids，默认为False。
        :param kwargs: 其他参数，将传递给tokenizer的batch_encode_plus方法。
        """
		self.tokenizer = tokenizer
		self.max_length = max_length
		self.padding = padding
		self.truncation = truncation
		self.return_tensors = return_tensors
		self.return_token_type_ids = return_token_type_ids
		self.kwargs = kwargs
	
	def __call__(self, examples: List[Tuple[str, int]]) -> Mapping[str, torch.Tensor]:
		texts, labels = zip(*examples)
		result = self.tokenizer.batch_encode_plus(texts,
                                                max_length=self.max_length,
												padding=self.padding,
                                                truncation=self.truncation,
                                                return_tensors=self.return_tensors,
												return_token_type_ids=self.return_token_type_ids,
												**self.kwargs)
		
		# 分类用cross_entropy损失函数时，labels需要是np.int64类型（torch.long）
		result['labels'] = torch.from_numpy(np.asarray(labels, dtype=np.int64))
		return result
		