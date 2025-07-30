Usage Sample
''''''''''''

.. code:: python

        from sklearn.model_selection import train_test_split
        import torch
        from transformers import BertTokenizer
        from nlpx.dataset import TextDataset, text_collate
        from nlpx.model.wrapper import ClassifyModelWrapper
        from transformers_model import AutoCNNTextClassifier, AutoCNNTokenClassifier, \
                BertDataset, BertCollator, BertTokenizeCollator

        texts = [[str],]
        labels = [0, 0, 1, 2, 1...]
        pretrained_path = "clue/albert_chinese_tiny"
        classes = ['class1', 'class2', 'class3'...]
        train_texts, test_texts, y_train, y_test = train_test_split(texts, labels, test_size=0.2)
        
        train_set = TextDataset(train_texts, y_train)
        test_set = TextDataset(test_texts, y_test)

        ################################### TextClassifier ##################################
        model = AutoCNNTextClassifier(pretrained_path, len(classes))
        wrapper = ClassifyModelWrapper(model, classes)
        _ = wrapper.train(train_set, test_set, collate_fn=text_collate)

        ################################### TokenClassifier #################################
        tokenizer = BertTokenizer.from_pretrained(pretrained_path)

        ##################### BertTokenizeCollator #########################
        model = AutoCNNTokenClassifier(pretrained_path, len(classes))
        wrapper = ClassifyModelWrapper(model, classes)
        _ = wrapper.train(train_set, test_set, collate_fn=BertTokenizeCollator(tokenizer, 256))

        ##################### BertCollator ##################################
        train_tokens = tokenizer.batch_encode_plus(
                train_texts,
                max_length=256,
                padding="max_length",
                truncation=True,
                return_attention_mask=True,
                return_token_type_ids=False,
                return_tensors="pt",
        )

        test_tokens = tokenizer.batch_encode_plus(
                test_texts,
                max_length=256,
                padding="max_length",
                truncation=True,
                return_attention_mask=True,
                return_token_type_ids=False,
                return_tensors="pt",
        )

        train_set = BertDataset(train_tokens, y_train)
        test_set = BertDataset(test_tokens, y_test)

        model = AutoCNNTokenClassifier(pretrained_path, len(classes))
        wrapper = ClassifyModelWrapper(model, classes)
        _ = wrapper.train(train_set, test_set, collate_fn=BertCollator())
