# interfusion/data_utils.py

import random
import torch
from torch.utils.data import Dataset
import numpy as np

def set_seed(seed):
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    np.random.seed(seed)
    random.seed(seed)

# Dataset class for the cross-encoder
class CrossEncoderDataset(Dataset):
    def __init__(self, data_samples, tokenizer, config, negatives=None, hard_negatives=None, random_negatives=None):
        """
        data_samples: list of dicts, each dict contains 'user_text', 'positive_item_text', 'user_id', etc.
        tokenizer: tokenizer to use
        config: configuration dictionary
        negatives: dict mapping user_id to list of M negative item_texts and ids (from bi-encoder)
        hard_negatives: dict mapping user_id to list of N hard negative item_texts and ids (from cross-encoder)
        random_negatives: dict mapping user_id to list of N random negative item_texts and ids
        """
        self.data_samples = data_samples
        self.tokenizer = tokenizer
        self.max_length = config['max_length']
        self.negatives = negatives  # M negatives per user
        self.hard_negatives = hard_negatives  # N hard negatives per user
        self.random_negatives = random_negatives  # N random negatives per user
        self.use_sparse = config['use_sparse']

    def __len__(self):
        return len(self.data_samples)

    def __getitem__(self, idx):
        sample = self.data_samples[idx]
        user_text = sample['user_text']
        positive_item_text = sample['positive_item_text']
        user_id = sample['user_id']
        user_features = sample.get('user_features', None)
        positive_item_features = sample.get('positive_item_features', None)
        items = []

        # Positive sample
        inputs = self.tokenizer(user_text, positive_item_text, max_length=self.max_length, truncation=True,
                                padding='max_length', return_tensors='pt')
        label = 1  # Positive class
        if self.use_sparse:
            features = self._prepare_features(user_features, positive_item_features)
        else:
            features = None
        items.append((inputs, features, label, user_id))

        # Negative samples (N hard negatives per user)
        if self.hard_negatives and user_id in self.hard_negatives:
            negative_item_texts = self.hard_negatives[user_id]['item_texts']
            negative_item_ids = self.hard_negatives[user_id]['item_ids']
            if self.use_sparse:
                negative_item_features_list = self.hard_negatives[user_id]['item_features']
            else:
                negative_item_features_list = [None] * len(negative_item_texts)

            for idx_neg, neg_item_text in enumerate(negative_item_texts):
                inputs_neg = self.tokenizer(user_text, neg_item_text, max_length=self.max_length, truncation=True,
                                            padding='max_length', return_tensors='pt')
                label_neg = 0  # Negative class
                if self.use_sparse:
                    neg_item_features = negative_item_features_list[idx_neg]
                    features_neg = self._prepare_features(user_features, neg_item_features)
                else:
                    features_neg = None
                items.append((inputs_neg, features_neg, label_neg, user_id))

        # Negative samples (N random negatives per user)
        if self.random_negatives and user_id in self.random_negatives:
            rand_neg_item_texts = self.random_negatives[user_id]['item_texts']
            rand_neg_item_ids = self.random_negatives[user_id]['item_ids']
            if self.use_sparse:
                rand_neg_features_list = self.random_negatives[user_id]['item_features']
            else:
                rand_neg_features_list = [None] * len(rand_neg_item_texts)
            for idx_neg, neg_item_text in enumerate(rand_neg_item_texts):
                inputs_neg = self.tokenizer(user_text, neg_item_text, max_length=self.max_length, truncation=True,
                                            padding='max_length', return_tensors='pt')
                label_neg = 0  # Negative class
                if self.use_sparse:
                    neg_item_features = rand_neg_features_list[idx_neg]
                    features_neg = self._prepare_features(user_features, neg_item_features)
                else:
                    features_neg = None
                items.append((inputs_neg, features_neg, label_neg, user_id))

        return items  # Return list of (inputs, features, label, user_id) tuples
        
    def collate_fn(self, batch):
        # batch is a list of lists of (inputs, features, label, user_id) tuples
        input_ids = []
        attention_masks = []
        labels = []
        features_list = []
        user_ids = []
        user_to_indices = {}
        idx = 0
        for items in batch:
            for inputs, features, label, user_id in items:
                input_ids.append(inputs['input_ids'].squeeze(0))
                attention_masks.append(inputs['attention_mask'].squeeze(0))
                labels.append(label)
                user_ids.append(user_id)
                if user_id not in user_to_indices:
                    user_to_indices[user_id] = []
                user_to_indices[user_id].append(idx)
                idx += 1
                if self.use_sparse:
                    features_list.append(features)
        input_ids = torch.stack(input_ids)
        attention_masks = torch.stack(attention_masks)
        labels = torch.tensor(labels)
        batch_data = {
            'input_ids': input_ids,
            'attention_mask': attention_masks,
            'labels': labels,
            'user_ids': user_ids,
            'user_to_indices': user_to_indices,
        }
        if self.use_sparse:
            features_padded = self._pad_features(features_list)
            batch_data['features'] = features_padded
        return batch_data

    def _prepare_features(self, user_features, item_features):
        if user_features is not None and item_features is not None:
            features = {
                'user_features': torch.tensor(user_features, dtype=torch.float),
                'item_features': torch.tensor(item_features, dtype=torch.float)
            }
        else:
            features = None
        return features

    def _pad_features(self, features_list):
        # Features_list is a list of dicts with 'user_features' and 'item_features'
        user_feature_lengths = [f['user_features'].size(0) for f in features_list if f is not None]
        item_feature_lengths = [f['item_features'].size(0) for f in features_list if f is not None]

        max_user_length = max(user_feature_lengths) if user_feature_lengths else 0
        max_item_length = max(item_feature_lengths) if item_feature_lengths else 0

        padded_user_features = []
        padded_item_features = []

        for features in features_list:
            if features is not None:
                user_feat = features['user_features']
                item_feat = features['item_features']

                # Pad user features
                pad_size_user = max_user_length - user_feat.size(0)
                if pad_size_user > 0:
                    user_feat = torch.cat([user_feat, torch.zeros(pad_size_user)], dim=0)

                # Pad item features
                pad_size_item = max_item_length - item_feat.size(0)
                if pad_size_item > 0:
                    item_feat = torch.cat([item_feat, torch.zeros(pad_size_item)], dim=0)
            else:
                user_feat = torch.zeros(max_user_length)
                item_feat = torch.zeros(max_item_length)

            padded_user_features.append(user_feat)
            padded_item_features.append(item_feat)

        # Stack features
        user_features_tensor = torch.stack(padded_user_features)
        item_features_tensor = torch.stack(padded_item_features)

        # Concatenate user and item features
        features_tensor = torch.cat([user_features_tensor, item_features_tensor], dim=1)  # Shape: [batch_size, total_feature_size]
        return features_tensor

    @staticmethod
    def pad_features_static(features_list, user_feature_size, item_feature_size):
        # Static method to pad features when feature sizes are known
        padded_user_features = []
        padded_item_features = []

        for features in features_list:
            if features is not None:
                user_feat = features['user_features']
                item_feat = features['item_features']

                # Pad user features
                pad_size_user = user_feature_size - user_feat.size(0)
                if pad_size_user > 0:
                    user_feat = torch.cat([user_feat, torch.zeros(pad_size_user)], dim=0)

                # Pad item features
                pad_size_item = item_feature_size - item_feat.size(0)
                if pad_size_item > 0:
                    item_feat = torch.cat([item_feat, torch.zeros(pad_size_item)], dim=0)
            else:
                user_feat = torch.zeros(user_feature_size)
                item_feat = torch.zeros(item_feature_size)

            padded_user_features.append(user_feat)
            padded_item_features.append(item_feat)

        # Stack features
        user_features_tensor = torch.stack(padded_user_features)
        item_features_tensor = torch.stack(padded_item_features)

        # Concatenate user and item features
        features_tensor = torch.cat([user_features_tensor, item_features_tensor], dim=1)  # Shape: [batch_size, total_feature_size]
        return features_tensor

    def update_hard_negatives(self, hard_negatives):
        self.hard_negatives = hard_negatives

    def update_random_negatives(self, random_negatives):
        self.random_negatives = random_negatives

