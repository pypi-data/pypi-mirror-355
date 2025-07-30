from typing import Union, Tuple, Optional
import torch
from torch import nn
from torch_model_hub.model import TextCNN, RNNAttention
from transformers import AutoModel, BertConfig, BertModel, ErnieConfig, ErnieModel, AutoTokenizer, AutoConfig
from transformers.utils.generic import PaddingStrategy


class TokenClassifier(nn.Module):

    def __init__(self, backbone, classifier, num_train_layers=0):
        """
        初始化模型。

        参数:
        - backbone: 模型的主干网络，用于特征提取。
        - classifier: 分类器，用于对提取的特征进行分类。
        - num_train_layers: 模型中需要训练的层数，默认为0，表示全部冻结。
        """
        super().__init__()  # 调用父类的构造方法进行初始化
        self.backbone = backbone  # 保存主干网络作为模型的一部分
        self.classifier = classifier  # 保存分类器作为模型的一部分
        # 根据num_train_layers参数决定是否冻结预训练模型的权重
        if num_train_layers <= 0:
            # 如果num_train_layers小于等于0，冻结所有预训练模型的权重
            for param in backbone.parameters():
                param.requires_grad_(False)
        else:
            # 否则，只冻结指定数量的层
            parameters = list(backbone.parameters())
            if num_train_layers < len(parameters):
                for param in parameters[:num_train_layers]:
                    param.requires_grad_(False)
                for param in parameters[num_train_layers:]:
                    param.requires_grad_(True)
            else:
                for param in parameters:
                    param.requires_grad_(True)

    def forward(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> torch.Tensor:
        outputs = self.backbone(
            input_ids=input_ids,
            attention_mask=attention_mask,
            token_type_ids=token_type_ids,
            output_hidden_states=True,
        )
        return self.classifier(
            outputs.last_hidden_state
        )  # 除去[cls]: outputs.last_hidden_state[:, 1:]

    def fit(
        self,
        input_ids: torch.Tensor,
        attention_mask: torch.Tensor,
        labels: torch.Tensor,
        token_type_ids: Optional[torch.Tensor] = None,
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        logits = self.forward(input_ids, attention_mask, token_type_ids)
        return nn.functional.cross_entropy(logits, labels), logits


class AutoCNNTokenClassifier(TokenClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes: int,
        num_train_layers: int = 0,
        config=None,
        model: Optional[nn.Module] = None,
        **kwargs
    ):
        """
        初始化模型。

        参数:
        pretrained_path (str): 预训练模型的路径。
        num_classes (int): 分类的类别数量。
        num_train_layers (int): 需要训练的模型层数量，默认为0，表示不训练任何层。
        config: 模型的配置信息，默认为None，如果未提供，则从预训练路径中加载配置。
        model (Optional[nn.Module]): 模型，默认为None，如果提供了模型，则使用提供的模型作为主干。
        **kwargs: 其他可变关键字参数，传递给TextCNN分类器。
        """
        # 加载或创建模型配置
        config = config or AutoConfig.from_pretrained(pretrained_path)
        # 加载预训练模型作为模型的主干部分
        backbone = model or AutoModel.from_pretrained(pretrained_path)
        # 创建TextCNN分类器，用于最终的分类任务
        classifier = TextCNN(
            embed_dim=config.hidden_size, out_features=num_classes, **kwargs
        )
        # 调用父类的初始化方法，初始化模型
        super().__init__(backbone, classifier, num_train_layers)


class BertCNNTokenClassifier(AutoCNNTokenClassifier):

    def __init__(self, pretrained_path, num_classes, num_train_layers=0, **kwargs):
        config = BertConfig.from_pretrained(pretrained_path)
        model = BertModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path, num_classes, num_train_layers, config, model, **kwargs
        )


class ErnieCNNTokenClassifier(AutoCNNTokenClassifier):

    def __init__(self, pretrained_path, num_classes, num_train_layers=0, **kwargs):
        config = ErnieConfig.from_pretrained(pretrained_path)
        model = ErnieModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path, num_classes, num_train_layers, config, model, **kwargs
        )


class AutoRNNAttentionTokenClassifier(TokenClassifier):

    def __init__(
        self, pretrained_path, num_classes, num_train_layers=0, config=None, model: Optional[nn.Module] = None, **kwargs
    ):
        """
        初始化模型。

        参数:
        pretrained_path (str): 预训练模型的路径。
        num_classes (int): 分类任务的类别数量。
        num_train_layers (int): 需要训练的模型层数量，默认为0，表示冻结所有层。
        config (optional): 模型的配置，默认为None，如果未提供，则从预训练路径中加载配置。
        model (Optional[nn.Module]): 模型，默认为None，如果提供了模型，则使用提供的模型作为主干。
        **kwargs: 其他传递给分类器的参数。
        """
        # 加载或创建模型配置
        config = config or AutoConfig.from_pretrained(pretrained_path)
        # 加载预训练模型作为模型的主干（backbone）
        backbone = model or AutoModel.from_pretrained(pretrained_path)
        # 创建分类器，使用RNNAttention，其中embed_dim是从配置中获取的隐藏层大小
        classifier = RNNAttention(
            embed_dim=config.hidden_size, out_features=num_classes, **kwargs
        )
        # 调用父类的初始化方法，传递主干和分类器
        super().__init__(backbone, classifier, num_train_layers)


class BertRNNAttentionTokenClassifier(AutoRNNAttentionTokenClassifier):

    def __init__(self, pretrained_path, num_classes, num_train_layers=0, **kwargs):
        config = BertConfig.from_pretrained(pretrained_path)
        model = BertModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path, num_classes, num_train_layers, config, model, **kwargs
        )


class ErnieRNNAttentionTokenClassifier(AutoRNNAttentionTokenClassifier):

    def __init__(self, pretrained_path, num_classes: int, num_train_layers=0, **kwargs):
        config = ErnieConfig.from_pretrained(pretrained_path)
        model = ErnieModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path, num_classes, num_train_layers, config, model, **kwargs
        )


# class ModernBertCNNTokenClassifier(AutoCNNTokenClassifier):

#     def __init__(self, pretrained_path, num_classes,  max_length: int = 512, **kwargs):
#         config = ModernBertConfig.from_pretrained(pretrained_path)
#         super().__init__(pretrained_path, num_classes, max_length, config, **kwargs)


# class ModernBertRNNAttentionTokenClassifier(AutoRNNAttentionTokenClassifier):

#     def __init__(self, pretrained_path, num_classes,  max_length: int = 512, **kwargs):
#         config = ModernBertConfig.from_pretrained(pretrained_path)
#         super().__init__(pretrained_path, num_classes, max_length, config, **kwargs)


class TextClassifier(TokenClassifier):
    """一般配合text_collate方法使用"""

    def __init__(
        self,
        pretrained_path,
        backbone,
        classifier,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
    ):
        """
        初始化模型及其参数。

        Args:
            pretrained_path (str): 预训练模型的路径。
            backbone (torch.nn.Module): 模型的主干网络。
            classifier (torch.nn.Module): 分类器头部。
            num_train_layers (int, optional): 需要训练的模型层数量，默认为0，表示冻结所有层。
            max_length (int, optional): 输入序列的最大长度，默认为512。
            padding (Union[bool, str, PaddingStrategy], optional): 填充策略，默认为True。
            truncation (bool, optional): 是否进行截断，默认为True。
            return_tensors (str, optional): 返回的张量类型，默认为'pt'（PyTorch）。
            return_token_type_ids (bool, optional): 是否返回token类型ID，默认为False。
            is_split_into_words (bool, optional): 输入文本是否已经被分割为单词，默认为False。
        """
        # 调用父类的初始化方法进行模型主干和分类器的初始化
        super().__init__(backbone, classifier, num_train_layers)
        # 初始化输入序列的最大长度
        self.max_length = max_length
        # 初始化填充策略
        self.padding = padding
        # 初始化截断策略
        self.truncation = truncation
        # 初始化返回的张量类型
        self.return_tensors = return_tensors
        # 初始化是否返回token类型ID的标志
        self.return_token_type_ids = return_token_type_ids
        # 初始化输入文本是否已被分割为单词的标志
        self.is_split_into_words = is_split_into_words
        # 使用预训练模型路径初始化tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(pretrained_path)
        self.device = None

    def forward(self, texts) -> torch.Tensor:
        if self.device:
            return self._forward(texts)
        
        self.device = next(self.parameters()).device
        return self._forward(texts)

    def _forward(self, texts) -> torch.Tensor:
        tokenizies = self.tokenizer.batch_encode_plus(
            texts,
            max_length=self.max_length,
            padding=self.padding,
            truncation=self.truncation,
            return_tensors=self.return_tensors,
            return_token_type_ids=self.return_token_type_ids,
            is_split_into_words=self.is_split_into_words,
        )
        tokenizies = {k: v.to(self.device) for k, v in tokenizies.items()}
        return super().forward(**tokenizies)

    def fit(self, texts, labels: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        logits = self.forward(texts)
        return nn.functional.cross_entropy(logits, labels), logits


class AutoCNNTextClassifier(TextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        config=None,
        model: Optional[nn.Module] = None,
        **kwargs
    ):
        """
        初始化模型参数。

        参数:
        pretrained_path (str): 预训练模型的路径。
        num_classes (int): 分类的类别数量。
        num_train_layers (int): 需要训练的模型层的数量，<=0表示冻结所有层。
        max_length (int): 输入序列的最大长度，默认为512。
        padding (Union[bool, str, PaddingStrategy]): 是否对序列进行填充，默认为True。
        truncation (bool): 是否对序列进行截断，默认为True。
        return_tensors (str): 返回的张量类型，默认为'pt'（PyTorch）。
        return_token_type_ids (bool): 是否返回token类型ID，默认为False。
        is_split_into_words (bool): 输入是否已经被分割为单词，默认为False。
        config (Optional[Config]): 模型的配置，如果为None，则从预训练路径加载。
        model (Optional[nn.Module]): 模型，如果为None，则从预训练路径加载。
        **kwargs: 其他传递给分类器TextCNN的参数。
        """
        # 加载或创建模型配置
        config = config or AutoConfig.from_pretrained(pretrained_path)
        # 加载预训练模型作为模型的主干
        backbone = model or AutoModel.from_pretrained(pretrained_path)
        # 初始化文本分类器，使用TextCNN作为分类头
        classifier = TextCNN(
            embed_dim=config.hidden_size, out_features=num_classes, **kwargs
        )
        # 调用父类的初始化方法，初始化整个模型
        super().__init__(
            pretrained_path,
            backbone,
            classifier,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
        )


class BertCNNTextClassifier(AutoCNNTextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        **kwargs
    ):
        config = BertConfig.from_pretrained(pretrained_path)
        model = BertModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path,
            num_classes,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
            config,
            model,
            **kwargs
        )


class ErnieCNNTextClassifier(AutoCNNTextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        **kwargs
    ):
        config = ErnieConfig.from_pretrained(pretrained_path)
        model = ErnieModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path,
            num_classes,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
            config,
            model,
            **kwargs
        )


class AutoRNNAttentionTextClassifier(TextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        config=None,
        model: Optional[nn.Module] = None,
        **kwargs
    ):
        config = config or AutoConfig.from_pretrained(pretrained_path)
        backbone = model or AutoModel.from_pretrained(pretrained_path)
        classifier = RNNAttention(
            embed_dim=config.hidden_size, out_features=num_classes, **kwargs
        )
        super().__init__(
            pretrained_path,
            backbone,
            classifier,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
        )


class BertRNNAttentionTextClassifier(AutoRNNAttentionTextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        **kwargs
    ):
        config = BertConfig.from_pretrained(pretrained_path)
        model = BertModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path,
            num_classes,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
            config,
            **kwargs
        )


class ErnieRNNAttentionTextClassifier(AutoRNNAttentionTextClassifier):

    def __init__(
        self,
        pretrained_path,
        num_classes,
        num_train_layers=0,
        max_length: int = 512,
        padding: Union[bool, str, PaddingStrategy] = True,
        truncation=True,
        return_tensors="pt",
        return_token_type_ids=False,
        is_split_into_words=False,
        **kwargs
    ):
        config = ErnieConfig.from_pretrained(pretrained_path)
        model = ErnieModel.from_pretrained(pretrained_path)
        super().__init__(
            pretrained_path,
            num_classes,
            num_train_layers,
            max_length,
            padding,
            truncation,
            return_tensors,
            return_token_type_ids,
            is_split_into_words,
            config,
            **kwargs
        )


# 需要 transformers>=4.48.3
# class ModernBertCNNTextClassifier(AutoCNNTextClassifier):

#     def __init__(self, pretrained_path, num_classes,  max_length: int = 512, **kwargs):
#         config = ModernBertConfig.from_pretrained(pretrained_path)
#         super().__init__(pretrained_path, num_classes, max_length, config, **kwargs)


# class ModernBertRNNAttentionTextClassifier(AutoRNNAttentionTextClassifier):

#     def __init__(self, pretrained_path, num_classes,  max_length: int = 512, **kwargs):
#         config = ModernBertConfig.from_pretrained(pretrained_path)
#         super().__init__(pretrained_path, num_classes, max_length, config, **kwargs)
