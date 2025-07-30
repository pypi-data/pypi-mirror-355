import torch
import numpy as np
from typing import List, Union
from sklearn.model_selection import train_test_split
from torch.utils.data import TensorDataset


def train_test_set(tokenize_vec, train_texts: List[str], test_texts: List[str],
                   y_train: Union[torch.LongTensor, List, np.ndarray], y_test: Union[torch.LongTensor, List, np.ndarray],
                         max_length: int = 0, n_jobs=-1):
    X_train = tokenize_vec.parallel_encode_plus(train_texts, max_length=max_length, padding='max_length',
                                        truncation=True, add_special_tokens=True,
                                        return_token_type_ids=True,return_attention_mask=True,
                                        return_tensors='pt', n_jobs=n_jobs)
    if isinstance(y_train, List) or isinstance(y_train, np.ndarray):
        y_train = torch.tensor(y_train, dtype=torch.long)

    X_test = tokenize_vec.parallel_encode_plus(test_texts, max_length=max_length, padding='max_length',
                                                truncation=True, add_special_tokens=True,
                                                return_token_type_ids=True, return_attention_mask=True,
                                                return_tensors='pt', n_jobs=n_jobs)
    if isinstance(y_test, List) or isinstance(y_test, np.ndarray):
        y_test = torch.tensor(y_test, dtype=torch.long)
    return TensorDataset(X_train, y_train), TensorDataset(X_test, y_test)


def train_test_split_set(tokenize_vec, texts: List[str], y: Union[torch.LongTensor, List, np.ndarray],
                         max_length: int = 0, test_size=0.2, n_jobs=-1, random_state=None):
    X = tokenize_vec.parallel_encode_plus(texts, max_length=max_length, padding='max_length',
                                        truncation=True, add_special_tokens=True,
                                        return_token_type_ids=True,return_attention_mask=True,
                                        return_tensors='pt', n_jobs=n_jobs)
    if isinstance(y, List) or isinstance(y, np.ndarray):
        y = torch.tensor(y, dtype=torch.long)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state)
    return TensorDataset(X_train, y_train), TensorDataset(X_test, y_test)
