# interfusion/inference.py

import torch
import torch.nn as nn
from transformers import AutoTokenizer
from .models import CrossEncoderModel
from .config import get_default_config
from .data_utils import CrossEncoderDataset

class InterFusionInference:
    def __init__(self, config=None, model_path=None):
        if config is None:
            config = get_default_config()
        self.config = config
        if model_path is None:
            model_path = config['saved_model_path']
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(config['cross_encoder_model_name'])
        
        # Store feature sizes from config for use in predict method
        self.user_feature_size = config.get('user_feature_size', 0)
        self.item_feature_size = config.get('item_feature_size', 0)
        
        # Create the model
        self.model = CrossEncoderModel(config, self.user_feature_size, self.item_feature_size).to(self.device)
        
        # Apply DataParallel if multiple GPUs available and enabled in config
        if torch.cuda.device_count() > 1 and config.get('use_data_parallel_inference', False):
            print(f"Using {torch.cuda.device_count()} GPUs for inference")
            self.model = nn.DataParallel(self.model)
        
        # Load state dict
        state_dict = torch.load(model_path, map_location=self.device)
        
        # Handle loading model state dict based on DataParallel
        if 'model_state_dict' in state_dict:
            if isinstance(self.model, nn.DataParallel):
                self.model.module.load_state_dict(state_dict['model_state_dict'])
            else:
                self.model.load_state_dict(state_dict['model_state_dict'])
        else:
            if isinstance(self.model, nn.DataParallel):
                self.model.module.load_state_dict(state_dict)
            else:
                self.model.load_state_dict(state_dict)
        
        self.model.eval()

    def predict(self, user_texts, item_texts, user_features_list=None, item_features_list=None, batch_size=32):
        predictions = []
        if user_features_list is None:
            user_features_list = [None] * len(user_texts)
        if item_features_list is None:
            item_features_list = [None] * len(item_texts)
        
        # Check if mixed precision is enabled in config
        use_mixed_precision = self.config.get('mixed_precision', True) and self.config.get('optimisation', True)
        
        # Get use_sparse attribute correctly with DataParallel
        use_sparse = self.config['use_sparse']
        
        # Use the stored feature sizes from __init__ instead of trying to access from model
        user_feature_size = self.user_feature_size
        item_feature_size = self.item_feature_size
        
        with torch.no_grad():
            for i in range(0, len(user_texts), batch_size):
                batch_user_texts = user_texts[i:i+batch_size]
                batch_item_texts = item_texts[i:i+batch_size]
                inputs = self.tokenizer(batch_user_texts, batch_item_texts, max_length=self.config['max_length'],
                                        truncation=True, padding=True, return_tensors='pt')
                input_ids = inputs['input_ids'].to(self.device)
                attention_mask = inputs['attention_mask'].to(self.device)
                
                if use_sparse:
                    batch_user_features = user_features_list[i:i+batch_size]
                    batch_item_features = item_features_list[i:i+batch_size]
                    features_list = []
                    for cf, jf in zip(batch_user_features, batch_item_features):
                        features = {
                            'user_features': torch.tensor(cf, dtype=torch.float) if cf is not None else torch.zeros(user_feature_size),
                            'item_features': torch.tensor(jf, dtype=torch.float) if jf is not None else torch.zeros(item_feature_size)
                        }
                        features_list.append(features)
                    
                    # Prepare features
                    features_padded = CrossEncoderDataset.pad_features_static(features_list, user_feature_size, item_feature_size)
                    features_tensor = features_padded.to(self.device)
                    
                    # Use mixed precision if enabled
                    if use_mixed_precision:
                        with torch.cuda.amp.autocast():
                            logits = self.model(input_ids=input_ids, attention_mask=attention_mask, features=features_tensor)
                    else:
                        logits = self.model(input_ids=input_ids, attention_mask=attention_mask, features=features_tensor)
                else:
                    # Use mixed precision if enabled
                    if use_mixed_precision:
                        with torch.cuda.amp.autocast():
                            logits = self.model(input_ids=input_ids, attention_mask=attention_mask)
                    else:
                        logits = self.model(input_ids=input_ids, attention_mask=attention_mask)
                
                raw_scores = logits.cpu().tolist()
                predictions.extend(raw_scores)
        
        return predictions
