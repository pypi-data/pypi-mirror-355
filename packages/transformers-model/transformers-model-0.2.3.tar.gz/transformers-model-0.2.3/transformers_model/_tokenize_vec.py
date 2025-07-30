import os
import torch
from pathlib import Path
from typing import Union, List, Optional
from concurrent.futures import as_completed, ProcessPoolExecutor
from transformers import BertTokenizer, BertConfig, BertModel, AlbertConfig, AlbertModel, ErnieConfig, ErnieModel
from transformers.tokenization_utils import PaddingStrategy, TruncationStrategy, TensorType


class TokenizeVec:

	def __init__(self, pretrained_path: Union[str, Path], tokenizer=BertTokenizer):
		self.config = None
		self.pretrained = None
		self.tokenizer = tokenizer.from_pretrained(pretrained_path)

	@property
	def hidden_size(self):
		assert self.config is not None, "config must not be None"
		return self.config.hidden_size

	@staticmethod
	def get_max_length(texts: List[str], max_length: int = 0) -> int:
		if max_length and max_length > 0:
			return max_length
		return get_texts_max_length(texts, cut_type='char') + 2  # 开头结尾

	def encode_plus(self,
				texts: List[str],
				add_special_tokens: bool = True,
				padding: Union[bool, str, PaddingStrategy] = 'max_length',
				truncation: Union[bool, str, TruncationStrategy] = True,
				max_length: Optional[int] = None,
				stride: int = 0,
				is_split_into_words: bool = False,
				pad_to_multiple_of: Optional[int] = None,
				return_tensors: Optional[Union[str, TensorType]] = 'pt',
				return_token_type_ids: Optional[bool] = True,
				return_attention_mask: Optional[bool] = True,
				return_overflowing_tokens: bool = False,
				return_special_tokens_mask: bool = False,
				return_offsets_mapping: bool = False,
				return_length: bool = False,
				verbose: bool = True,
				cls: bool = False,
				**kwargs,
			) -> torch.FloatTensor:
		max_length = self.get_max_length(texts, max_length)
		return self._encode_plus(
								texts,
								add_special_tokens,
								padding,
								truncation,
								max_length,
								stride,
								is_split_into_words,
								pad_to_multiple_of,
								return_tensors,
								return_token_type_ids,
								return_attention_mask,
								return_overflowing_tokens,
								return_special_tokens_mask,
								return_offsets_mapping,
								return_length,
								verbose,
								cls,
								** kwargs
							)

	def batch_encode_plus(self,
						texts: List[str],
						add_special_tokens: bool = True,
						padding: Union[bool, str, PaddingStrategy] = 'max_length',
						truncation: Union[bool, str, TruncationStrategy] = True,
						max_length: Optional[int] = None,
						stride: int = 0,
						is_split_into_words: bool = False,
						pad_to_multiple_of: Optional[int] = None,
						return_tensors: Optional[Union[str, TensorType]] = 'pt',
						return_token_type_ids: Optional[bool] = True,
						return_attention_mask: Optional[bool] = True,
						return_overflowing_tokens: bool = False,
						return_special_tokens_mask: bool = False,
						return_offsets_mapping: bool = False,
						return_length: bool = False,
						verbose: bool = True,
						cls: bool = False,
						batch_size: int = 128,
						**kwargs,
					) -> torch.FloatTensor:
		length = len(texts)
		if length <= batch_size:
			return self.encode_plus(
									texts,
									add_special_tokens,
									padding,
									truncation,
									max_length,
									stride,
									is_split_into_words,
									pad_to_multiple_of,
									return_tensors,
									return_token_type_ids,
									return_attention_mask,
									return_overflowing_tokens,
									return_special_tokens_mask,
									return_offsets_mapping,
									return_length,
									verbose,
									cls,
									** kwargs
								)
		else:
			max_length = self.get_max_length(texts, max_length)
			text_list = self.split_texts(texts, batch_size)
			results = [self._encode_plus(
									text,
									add_special_tokens,
									padding,
									truncation,
									max_length,
									stride,
									is_split_into_words,
									pad_to_multiple_of,
									return_tensors,
									return_token_type_ids,
									return_attention_mask,
									return_overflowing_tokens,
									return_special_tokens_mask,
									return_offsets_mapping,
									return_length,
									verbose,
									cls,
									** kwargs
								) for text in text_list]
			return torch.concat(results, dim=0)

	def parallel_encode_plus(self,
						texts: List[str],
						add_special_tokens: bool = True,
						padding: Union[bool, str, PaddingStrategy] = 'max_length',
						truncation: Union[bool, str, TruncationStrategy] = True,
						max_length: Optional[int] = None,
						stride: int = 0,
						is_split_into_words: bool = False,
						pad_to_multiple_of: Optional[int] = None,
						return_tensors: Optional[Union[str, TensorType]] = 'pt',
						return_token_type_ids: Optional[bool] = True,
						return_attention_mask: Optional[bool] = True,
						return_overflowing_tokens: bool = False,
						return_special_tokens_mask: bool = False,
						return_offsets_mapping: bool = False,
						return_length: bool = False,
						verbose: bool = True,
						cls: bool = False,
						batch_size: int = 128,
						n_jobs: int = -1,
						**kwargs,
					) -> torch.FloatTensor:
		length = len(texts)
		if length <= batch_size:
			return self.encode_plus(
									texts,
									add_special_tokens,
									padding,
									truncation,
									max_length,
									stride,
									is_split_into_words,
									pad_to_multiple_of,
									return_tensors,
									return_token_type_ids,
									return_attention_mask,
									return_overflowing_tokens,
									return_special_tokens_mask,
									return_offsets_mapping,
									return_length,
									verbose,
									cls,
									** kwargs
								)
		else:
			max_length = self.get_max_length(texts, max_length)
			text_list = self.split_texts(texts, batch_size)
			if n_jobs <= 0:
				n_jobs = min(len(text_list), os.cpu_count() - 1)
			with ProcessPoolExecutor(n_jobs) as executor:
				results = [executor.submit(self._order_encode,
				                           i,
				                           text,
				                           add_special_tokens,
				                           padding,
				                           truncation,
				                           max_length,
				                           stride,
				                           is_split_into_words,
				                           pad_to_multiple_of,
				                           return_tensors,
				                           return_token_type_ids,
				                           return_attention_mask,
				                           return_overflowing_tokens,
				                           return_special_tokens_mask,
				                           return_offsets_mapping,
				                           return_length,
				                           verbose,
				                           cls,
				                           **kwargs
				                           ) for i, text in enumerate(text_list)]
				results = [r.result() for r in as_completed(results)]
			results.sort(key=lambda x: x[0], reverse=False)
			results = [r[1] for r in results]
			return torch.concat(results, dim=0)

	@staticmethod
	def split_texts(texts: List[str], batch_size: int):
		return [texts[i:i + batch_size] for i in range(0, len(texts), batch_size)]

	def _order_encode(self,
				order: int,
				texts: List[str],
				add_special_tokens: bool = True,
				padding: Union[bool, str, PaddingStrategy] = False,
				truncation: Union[bool, str, TruncationStrategy] = None,
				max_length: Optional[int] = None,
				stride: int = 0,
				is_split_into_words: bool = False,
				pad_to_multiple_of: Optional[int] = None,
				return_tensors: Optional[Union[str, TensorType]] = None,
				return_token_type_ids: Optional[bool] = None,
				return_attention_mask: Optional[bool] = None,
				return_overflowing_tokens: bool = False,
				return_special_tokens_mask: bool = False,
				return_offsets_mapping: bool = False,
				return_length: bool = False,
				verbose: bool = True,
				cls: bool = False,
				**kwargs,
			) -> torch.FloatTensor:
		return order, self._encode_plus(
								texts,
								add_special_tokens,
								padding,
								truncation,
								max_length,
								stride,
								is_split_into_words,
								pad_to_multiple_of,
								return_tensors,
								return_token_type_ids,
								return_attention_mask,
								return_overflowing_tokens,
								return_special_tokens_mask,
								return_offsets_mapping,
								return_length,
								verbose,
								cls,
								**kwargs
							)

	def _encode_plus(self,
				texts: List[str],
				add_special_tokens: bool = True,
				padding: Union[bool, str, PaddingStrategy] = False,
				truncation: Union[bool, str, TruncationStrategy] = None,
				max_length: Optional[int] = None,
				stride: int = 0,
				is_split_into_words: bool = False,
				pad_to_multiple_of: Optional[int] = None,
				return_tensors: Optional[Union[str, TensorType]] = None,
				return_token_type_ids: Optional[bool] = None,
				return_attention_mask: Optional[bool] = None,
				return_overflowing_tokens: bool = False,
				return_special_tokens_mask: bool = False,
				return_offsets_mapping: bool = False,
				return_length: bool = False,
				verbose: bool = True,
				cls: bool = False,
				**kwargs,
			) -> torch.FloatTensor:
		tokens = self.tokenizer.batch_encode_plus(
												texts,
												add_special_tokens,
												padding,
												truncation,
												max_length,
												stride,
												is_split_into_words,
												pad_to_multiple_of,
												return_tensors,
												return_token_type_ids,
												return_attention_mask,
												return_overflowing_tokens,
												return_special_tokens_mask,
												return_offsets_mapping,
												return_length,
												verbose,
												** kwargs
											)
		self.pretrained.eval()
		with torch.no_grad():
			output = self.pretrained(**tokens, output_hidden_states=True)
		return output.last_hidden_state[:, 0] if cls else output.last_hidden_state[:, 1:]

	def __call__(self,
				texts: List[str],
				add_special_tokens: bool = True,
				padding: Union[bool, str, PaddingStrategy] = 'max_length',
				truncation: Union[bool, str, TruncationStrategy] = True,
				max_length: Optional[int] = None,
				stride: int = 0,
				is_split_into_words: bool = False,
				pad_to_multiple_of: Optional[int] = None,
				return_tensors: Optional[Union[str, TensorType]] = 'pt',
				return_token_type_ids: Optional[bool] = True,
				return_attention_mask: Optional[bool] = True,
				return_overflowing_tokens: bool = False,
				return_special_tokens_mask: bool = False,
				return_offsets_mapping: bool = False,
				return_length: bool = False,
				verbose: bool = True,
				cls: bool = False,
				batch_size: int = 128,
				n_jobs: int = -1,
				**kwargs,
			) -> torch.FloatTensor:
		return self.parallel_encode_plus(
			texts,
			add_special_tokens,
			padding,
			truncation,
			max_length,
			stride,
			is_split_into_words,
			pad_to_multiple_of,
			return_tensors,
			return_token_type_ids,
			return_attention_mask,
			return_overflowing_tokens,
			return_special_tokens_mask,
			return_offsets_mapping,
			return_length,
			verbose,
			cls,
			batch_size,
			n_jobs,
			**kwargs)


class BertTokenizeVec(TokenizeVec):

	def __init__(self, pretrained_path: Union[str, Path]):
		super().__init__(pretrained_path)
		self.config = BertConfig.from_pretrained(pretrained_path)
		self.pretrained = BertModel.from_pretrained(pretrained_path, config=self.config)


class AlbertTokenizeVec(TokenizeVec):

	def __init__(self, pretrained_path: Union[str, Path]):
		super().__init__(pretrained_path)
		self.config = AlbertConfig.from_pretrained(pretrained_path)
		self.pretrained = AlbertModel.from_pretrained(pretrained_path, config=self.config)


class ErnieTokenizeVec(TokenizeVec):

	def __init__(self, pretrained_path: Union[str, Path]):
		super().__init__(pretrained_path)
		self.config = ErnieConfig.from_pretrained(pretrained_path)
		self.pretrained = ErnieModel.from_pretrained(pretrained_path, config=self.config)
