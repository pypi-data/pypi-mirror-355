# interfusion/trainer.py

import torch
from torch.utils.data import DataLoader
from transformers import AutoTokenizer, AutoModel
import torch.optim as optim
import torch.nn as nn
from torch.cuda.amp import GradScaler
import os
import csv
import random
import numpy as np
from collections import defaultdict

from .models import CrossEncoderModel, compute_bi_encoder_embeddings
from .inference import InterFusionInference
from .data_utils import CrossEncoderDataset, set_seed
from .config import get_default_config


import logging
import time

'''
# Set environment variables and multiprocessing start method at the very beginning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

import torch.multiprocessing as mp
try:
    mp.set_start_method('spawn', force=True)
except RuntimeError:
    # The start method has already been set
    pass
'''

class DummyTqdm:
    def __init__(self, iterable=None, **kwargs):
        self.iterable = iterable if iterable is not None else []
        self.iterator = iter(self.iterable)
        self.desc = kwargs.get('desc', '')
        self.start_time = None
        self.end_time = None

    def __iter__(self):
        self.start_time = time.time()
        return self

    def __next__(self):
        try:
            return next(self.iterator)
        except StopIteration:
            self.end_time = time.time()
            total_time = self.end_time - self.start_time
            if self.desc:
                print(f"{self.desc} completed in {total_time:.2f} seconds")
            else:
                print(f"Iteration completed in {total_time:.2f} seconds")
            raise

    def __getattr__(self, attr):
        # Return a dummy function for any other attributes
        return lambda *args, **kwargs: None

    def update(self, n=1):
        pass

    def set_description(self, desc=None, refresh=True):
        pass

    def close(self):
        pass


def get_tqdm(config):
    if not config.get('use_tqdm', True):
        return DummyTqdm
    else:
        tqdm_type = config.get('tqdm_type', 'standard')
        try:
            if tqdm_type == 'notebook':
                from tqdm.notebook import tqdm
            else:
                from tqdm import tqdm
        except ImportError:
            print("tqdm is not installed. Progress bars will be disabled.")
            return DummyTqdm
        return tqdm



def train_model(users, items, positive_matches, users_eval=None, items_eval=None, positive_matches_eval=None, user_config=None):
    """
    Train the InterFusion Encoder model.

    Parameters:
    - users: list of dictionaries representing users.
    - items: list of dictionaries representing items.
    - positive_matches: list of dictionaries representing positive matches.
    - users_eval: (optional) list of dictionaries representing evaluation users.
    - items_eval: (optional) list of dictionaries representing evaluation items.
    - positive_matches_eval: (optional) list of dictionaries representing evaluation positive matches.
    - user_config: (optional) dictionary to override default configurations.
    """
    
    # Merge user configuration with default configuration
    config = get_default_config()
    if user_config:
        config.update(user_config)
        
    # Check if optimisations are enabled
    optimisation_enabled = config.get('optimisation', True)
    
    # Enable TF32 for A10G GPU if optimisation is enabled
    if optimisation_enabled:
        torch.backends.cuda.matmul.allow_tf32 = True
        torch.backends.cudnn.allow_tf32 = True
        print("TF32 enabled for matmul and cudnn operations")
    else:
        torch.backends.cuda.matmul.allow_tf32 = False
        torch.backends.cudnn.allow_tf32 = False
        print("TF32 disabled (using full FP32 precision)")
    
    start_epoch_bool = True
    
    if config.get('use_wandb', False):
        import wandb
        wandb.init(project=config.get('wandb_project', 'InterFusion'), config=config)
    elif config.get('use_mlflow', False):
        import mlflow
        mlflow.start_run()
        mlflow.log_params(config)

    set_seed(config['random_seed'])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # Create directory to save models
    os.makedirs(config['save_dir'], exist_ok=True)

    # Build mappings
    user_id_to_text = {user['user_id']: user['user_text'] for user in users}
    user_id_to_features = {user['user_id']: user.get('user_features', None) for user in users}
    item_id_to_text = {item['item_id']: item['item_text'] for item in items}
    item_id_to_features = {item['item_id']: item.get('item_features', None) for item in items}

    if users_eval is None:
        # If evaluation data is not provided, use the training data
        users_eval = users
        items_eval = items
        positive_matches_eval = positive_matches

    # Initialize tokenizer
    tokenizer = AutoTokenizer.from_pretrained(config['cross_encoder_model_name'])

    # Initialize bi-encoder
    bi_encoder = AutoModel.from_pretrained(config['bi_encoder_model_name']).to(device)

    # Implement triangular learning rate scheduler with non-zero starting LR
    lr_start = config['initial_learning_rate']
    lr_max = config['learning_rate']
    num_epochs = config['num_epochs']
    start_mult = lr_start / lr_max  # Multiplier at epoch 0

    def lr_lambda(epoch):
        if epoch <= num_epochs / 2:
            return start_mult + (1.0 - start_mult) * (epoch / (num_epochs / 2))
        else:
            return start_mult + (1.0 - start_mult) * ((num_epochs - epoch) / (num_epochs / 2))

    # If using sparse features, set feature sizes
    user_feature_size = 0
    item_feature_size = 0
    if config['use_sparse']:
        # Verify that all users and items have 'user_features' and 'item_features'
        if all('user_features' in user for user in users) and all('item_features' in item for item in items):
            user_feature_lengths = [len(user['user_features']) for user in users]
            item_feature_lengths = [len(item['item_features']) for item in items]
            user_feature_size = max(user_feature_lengths)
            item_feature_size = max(item_feature_lengths)
            print(f"User feature size detected and set to: {user_feature_size}")
            print(f"Item feature size detected and set to: {item_feature_size}")
        else:
            raise ValueError("All users and items must have 'user_features' and 'item_features' when 'use_sparse' is True.")

    # Initialize scaler for mixed precision training if optimisation is enabled
    use_mixed_precision = config.get('mixed_precision', True) and config.get('optimisation', True)
    scaler = None
    if use_mixed_precision:
        scaler = torch.cuda.amp.GradScaler()
        print("Mixed precision training enabled with GradScaler")
    
    # Load saved model if continue_training is True
    if config.get('continue_training', False):
        saved_model_path = os.path.join(config.get('save_dir', None), config.get('saved_model_path', None))
        print("saved_model_path: ", saved_model_path)
        if saved_model_path and os.path.exists(saved_model_path):
            print(f"Loading saved model from {saved_model_path} for continued training...")
            checkpoint = torch.load(saved_model_path, map_location=device)

            # Initialize model
            model = CrossEncoderModel(config, user_feature_size, item_feature_size).to(device)
            
            # Apply DataParallel if multiple GPUs available and enabled in config
            if torch.cuda.device_count() > 1 and config.get('use_data_parallel', True):
                print(f"Using {torch.cuda.device_count()} GPUs for training")
                model = nn.DataParallel(model)

            # Load model state dict
            if 'model_state_dict' in checkpoint:
                if isinstance(model, nn.DataParallel):
                    model.module.load_state_dict(checkpoint['model_state_dict'])
                else:
                    model.load_state_dict(checkpoint['model_state_dict'])
                print("Model state dict loaded.")
            else:
                if isinstance(model, nn.DataParallel):
                    model.module.load_state_dict(checkpoint)
                else:
                    model.load_state_dict(checkpoint)
                print("Loaded model directly from checkpoint (no 'model_state_dict' key).")

            # Initialize optimizer, scheduler, and scaler
            optimizer = optim.AdamW(model.parameters(), lr=config['learning_rate'])
            scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

            # Load optimizer and scheduler states if available
            if 'optimizer_state_dict' in checkpoint:
                optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
                print("Optimizer state dict loaded.")
            else:
                print("Optimizer state dict not found in checkpoint.")

            if 'scheduler_state_dict' in checkpoint:
                scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
                print("Scheduler state dict loaded.")
            else:
                print("Scheduler state dict not found in checkpoint.")

            # Load scaler state if available and if mixed precision is enabled
            if use_mixed_precision and 'scaler_state_dict' in checkpoint:
                scaler.load_state_dict(checkpoint['scaler_state_dict'])
                print("Scaler state dict loaded.")
            elif use_mixed_precision:
                print("Scaler state dict not found in checkpoint, using new scaler.")

            start_epoch = checkpoint.get('epoch', 1) + 1
            print(f"Resuming training from epoch {start_epoch}")
        else:
            print("Saved model path does not exist. Starting training from scratch.")
            start_epoch = 1
            # Initialize model, optimizer, scheduler
            model = CrossEncoderModel(config, user_feature_size, item_feature_size).to(device)
            
            # Apply DataParallel if multiple GPUs available and enabled in config
            if torch.cuda.device_count() > 1 and config.get('use_data_parallel', True):
                print(f"Using {torch.cuda.device_count()} GPUs for training")
                model = nn.DataParallel(model)
                
            optimizer = optim.AdamW(model.parameters(), lr=config['learning_rate'])
            scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)
    else:
        print("Starting training from scratch.")
        start_epoch = 1
        # Initialize model, optimizer, scheduler
        model = CrossEncoderModel(config, user_feature_size, item_feature_size).to(device)
        
        # Apply DataParallel if multiple GPUs available and enabled in config
        if torch.cuda.device_count() > 1 and config.get('use_data_parallel', True):
            print(f"Using {torch.cuda.device_count()} GPUs for training")
            model = nn.DataParallel(model)
            
        optimizer = optim.AdamW(model.parameters(), lr=config['learning_rate'])
        scheduler = torch.optim.lr_scheduler.LambdaLR(optimizer, lr_lambda)

    # Build a list of all user IDs
    all_user_ids = list(user_id_to_text.keys())

    best_metric = 0.0  # Initialize best metric (e.g., Precision@5)
    
    evaluate(model, tokenizer, users_eval, items_eval, positive_matches_eval, config, bi_encoder, 0)
    
    for epoch in range(start_epoch, num_epochs):
    
        if (start_epoch_bool) or (epoch % config["hard_negative_sampling_frequency"] == 0):
            
            if (start_epoch_bool):
                start_epoch_bool = False
                
            sample_amount = config["random_user_sample_amount"]
            # Sample of users
            sampled_user_ids = random.sample(all_user_ids, k=int(len(all_user_ids)*sample_amount))
            sampled_user_set = set(sampled_user_ids)

            # Build data_samples for sampled users
            data_samples_epoch = []
            for match in positive_matches:
                user_id = match['user_id']
                if user_id in sampled_user_set:
                    item_id = match['item_id']
                    data_samples_epoch.append({
                        'user_id': user_id,
                        'user_text': user_id_to_text[user_id],
                        'positive_item_id': item_id,
                        'positive_item_text': item_id_to_text[item_id],
                        'user_features': user_id_to_features.get(user_id, None),
                        'positive_item_features': item_id_to_features.get(item_id, None)
                    })

            # Build positive_matches_epoch
            positive_matches_epoch = [match for match in positive_matches if match['user_id'] in sampled_user_set]

            # Build sampled_users
            sampled_users = [user for user in users if user['user_id'] in sampled_user_set]

            
            # Precompute negatives using bi-encoder
            print("Precomputing negatives using bi-encoder...")
            negatives = precompute_bi_encoder_negatives(bi_encoder, tokenizer, sampled_users, items, positive_matches_epoch, config)
            # Generate initial hard negatives
            print("Generating initial hard negatives...")
            hard_negatives = generate_hard_negatives(model, data_samples_epoch, tokenizer, negatives, config, user_feature_size, item_feature_size)

            # Precompute N random negatives per user
            print("Precomputing random negatives...")
            random_negatives = precompute_random_negatives(sampled_users, items, positive_matches_epoch, config)
            

        # Initialize dataset with initial hard negatives and random negatives
        train_dataset = CrossEncoderDataset(
            data_samples_epoch, tokenizer, config, negatives=negatives,
            hard_negatives=hard_negatives, random_negatives=random_negatives
        )
        train_dataset.update_hard_negatives(hard_negatives)
        train_dataset.update_random_negatives(random_negatives)

        # Train for one epoch and update scaler if using mixed precision
        updated_scaler = train(model, train_dataset, optimizer, device, config, epoch, scheduler, scaler)
        if use_mixed_precision:
            scaler = updated_scaler

        # Evaluate the model
        if (epoch + 1) % config.get('eval_epoch', 1) == 0:
            # Run standard evaluation (for logging purposes)
            avg_precisions = evaluate(model, tokenizer, users_eval, items_eval, positive_matches_eval, config, bi_encoder, epoch)
            
            path_tmp = os.path.join(config['save_dir'], "interfusion_tmp.pt")
            
            # Save checkpoint with scaler if using mixed precision
            checkpoint_dict = {
                'epoch': epoch,
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
            }
            
            # Save model state dict handling DataParallel
            if isinstance(model, nn.DataParallel):
                checkpoint_dict['model_state_dict'] = model.module.state_dict()
            else:
                checkpoint_dict['model_state_dict'] = model.state_dict()
            
            if use_mixed_precision:
                checkpoint_dict['scaler_state_dict'] = scaler.state_dict()

            max_retries = 5
            retry_delay = 600  # 10 minutes in seconds

            for attempt in range(1, max_retries + 1):
                try:
                    torch.save(checkpoint_dict, path_tmp)
                    logging.info(f"Checkpoint successfully saved to {path_tmp}")
                    break  # Exit loop if successful
                except Exception as e:
                    logging.error(f"Attempt {attempt} failed: {e}")
                    if attempt < max_retries:
                        logging.info(f"Retrying after {retry_delay // 60} minutes...")
                        time.sleep(retry_delay)
                    else:
                        logging.error("All retry attempts failed.")
                        raise
            
            # Check if custom evaluation function is specified
            custom_function = config.get('custom_function', None)
            
            if custom_function is not None:
                try:
                    # Call the custom function and get the precision at 5
                    custom_p5 = custom_function()
                    print(f"Custom evaluation metric (Precision@5): {custom_p5:.4f}")
                    
                    # Use the custom metric for model saving decisions
                    current_metric = custom_p5
                except Exception as e:
                    print(f"Error executing custom function: {e}")
                    # Fall back to standard evaluation if custom function fails
                    current_metric = avg_precisions.get(5, 0.0)
                    print(f"Using standard Precision@5: {current_metric:.4f}")
            else:
                # Use standard evaluation if no custom function is provided
                current_metric = avg_precisions.get(5, 0.0)
                print(f"Standard Precision@5: {current_metric:.4f}")
            
            # Check if metric improved
            if current_metric > best_metric:
                best_metric = current_metric
            
                # Save the model
                model_save_path = os.path.join(config['save_dir'], f"interfusion_best_p5_{best_metric:.4f}.pt")
                
                # Update checkpoint dictionary
                best_checkpoint_dict = {
                    'epoch': epoch,
                    'optimizer_state_dict': optimizer.state_dict(),
                    'scheduler_state_dict': scheduler.state_dict(),
                }
                
                # Save model state dict handling DataParallel
                if isinstance(model, nn.DataParallel):
                    best_checkpoint_dict['model_state_dict'] = model.module.state_dict()
                else:
                    best_checkpoint_dict['model_state_dict'] = model.state_dict()
                
                if use_mixed_precision:
                    best_checkpoint_dict['scaler_state_dict'] = scaler.state_dict()
                    
                torch.save(best_checkpoint_dict, model_save_path)
                print(f"New best Precision@5: {best_metric:.4f}. Model saved to {model_save_path}")

    # Optionally, save the final model
    final_model_save_path = os.path.join(config['save_dir'], "interfusion_final.pt")
    
    # Create final checkpoint dictionary
    final_checkpoint_dict = {
        'epoch': num_epochs - 1,
        'optimizer_state_dict': optimizer.state_dict(),
        'scheduler_state_dict': scheduler.state_dict(),
    }
    
    # Save model state dict handling DataParallel
    if isinstance(model, nn.DataParallel):
        final_checkpoint_dict['model_state_dict'] = model.module.state_dict()
    else:
        final_checkpoint_dict['model_state_dict'] = model.state_dict()
    
    if use_mixed_precision:
        final_checkpoint_dict['scaler_state_dict'] = scaler.state_dict()
        
    torch.save(final_checkpoint_dict, final_model_save_path)
    print(f"Final model saved to {final_model_save_path}")



import torch
from torch.utils.data import Dataset, DataLoader
import numpy as np
from tqdm import tqdm
import torch.nn as nn

class UsersDataset(Dataset):
    def __init__(self, users):
        self.users = users

    def __len__(self):
        return len(self.users)

    def __getitem__(self, idx):
        return self.users[idx]

def custom_collate_fn(batch):
    collated_batch = {}
    for key in batch[0]:
        collated_batch[key] = [item[key] for item in batch]
    return collated_batch



def precompute_bi_encoder_negatives(
    bi_encoder, tokenizer, users, items, positive_matches, config,
    batch_size=512, num_workers=12, debug=False
):
    """
    Precompute negative item samples for each user using DataLoader for efficient batching.

    Args:
        bi_encoder: The bi-encoder model used for computing embeddings.
        tokenizer: The tokenizer corresponding to the bi-encoder.
        users: List of user dictionaries with 'user_text' and 'user_id'.
        items: List of item dictionaries with 'item_text' and 'item_id'.
        positive_matches: List of dictionaries with 'user_id' and 'item_id' indicating positive matches.
        config: Dictionary containing configuration parameters like 'M', 'use_sparse', 'start_rank',
                and 'bi-encode_relevance_thresh' (the similarity threshold).
        batch_size: Batch size for processing users.
        num_workers: Number of worker processes for DataLoader.
        debug: If True, print timing and debug information.

    Returns:
        negatives: Dictionary mapping user IDs to negative item samples.
    """
    import time
    import numpy as np
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader

    # Assumed to be defined elsewhere:
    # - get_tqdm
    # - compute_bi_encoder_embeddings
    # - UsersDataset
    # - custom_collate_fn
    tqdm_fn = get_tqdm(config)

    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    bi_encoder.to(device)

    # Extract user and item texts and IDs
    user_texts = [user['user_text'] for user in users]
    user_ids = [user['user_id'] for user in users]
    item_texts = [item['item_text'] for item in items]
    item_ids = [item['item_id'] for item in items]

    # Compute embeddings for users
    if debug:
        print("Computing user embeddings...")
        start_time = time.time()
    user_embeddings = compute_bi_encoder_embeddings(
        bi_encoder, tokenizer, user_texts, config
    )
    if debug:
        elapsed_time = time.time() - start_time
        print(f"Time taken to compute user embeddings: {elapsed_time:.2f} seconds")

    # Compute embeddings for items
    if debug:
        print("Computing item embeddings...")
        start_time = time.time()
    item_embeddings = compute_bi_encoder_embeddings(
        bi_encoder, tokenizer, item_texts, config
    )
    if debug:
        elapsed_time = time.time() - start_time
        print(f"Time taken to compute item embeddings: {elapsed_time:.2f} seconds")

    # Normalize embeddings
    user_embeddings = nn.functional.normalize(user_embeddings, p=2, dim=1).to(device)
    item_embeddings = nn.functional.normalize(item_embeddings, p=2, dim=1).to(device)

    # Build mappings from user/item IDs to their indices
    user_id_to_idx = {cid: idx for idx, cid in enumerate(user_ids)}
    item_id_to_idx = {jid: idx for idx, jid in enumerate(item_ids)}

    # Build a list of positive item indices per user
    positive_item_indices_per_user = [[] for _ in range(len(users))]
    for match in positive_matches:
        c_idx = user_id_to_idx.get(match['user_id'])
        j_idx = item_id_to_idx.get(match['item_id'])
        if c_idx is not None and j_idx is not None:
            positive_item_indices_per_user[c_idx].append(j_idx)

    # Retrieve configuration parameters
    M = config.get('M', 10)  # Number of negatives to sample per user
    use_sparse = config.get('use_sparse', False)
    start_rank = config.get('start_rank', 1000)  # Starting rank offset
    relevance_thresh = config.get('bi-encode_relevance_thresh', 0.7)  # Similarity threshold

    negatives = {}
    if use_sparse:
        negatives['negative_item_features'] = {}

    num_users = len(users)
    num_items = len(items)
    if num_items < start_rank + M:
        raise ValueError(f"Number of items ({num_items}) is less than start_rank ({start_rank}) + M ({M}).")

    # Ensure item embeddings are contiguous for efficient GPU operations
    item_embeddings = item_embeddings.contiguous()

    # Create Dataset and DataLoader for users
    dataset = UsersDataset(users)
    dataloader = DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
        pin_memory=True,
        collate_fn=custom_collate_fn
    )
    total_batches = len(dataloader)
    if debug:
        print(f"Total number of batches: {total_batches}")

    # Process user batches
    for batch_idx, batch_users in enumerate(tqdm_fn(dataloader, desc="Precomputing negatives in batches")):
        if debug:
            batch_start_time = time.time()

        # Get user IDs from the batch
        batch_user_ids = batch_users['user_id']
        batch_user_ids = [cid.item() if isinstance(cid, torch.Tensor) else cid for cid in batch_user_ids]

        try:
            batch_indices = [user_id_to_idx[cid] for cid in batch_user_ids]
        except KeyError as e:
            print(f"KeyError for user_id: {e}")
            raise

        # Retrieve embeddings for the current batch of users
        batch_embeddings = user_embeddings[batch_indices]  # Shape: [batch_size, embedding_dim]

        with torch.no_grad():
            # Compute similarities between batch users and all items
            similarities = torch.matmul(batch_embeddings, item_embeddings.t())  # Shape: [batch_size, num_items]

            # Exclude positive items by setting their similarities to -inf
            for i, c_idx in enumerate(batch_indices):
                pos_indices = positive_item_indices_per_user[c_idx]
                if pos_indices:
                    similarities[i, pos_indices] = -float('inf')

            # Sort similarities in descending order for each user
            sorted_similarities, sorted_indices = torch.sort(similarities, descending=True, dim=1)

        # Move sorted arrays to CPU for vectorized processing
        sorted_similarities_np = sorted_similarities.cpu().numpy()  # shape: [batch_size, num_items]
        sorted_indices_np = sorted_indices.cpu().numpy()  # shape: [batch_size, num_items]

        # Process negatives for each user using vectorized filtering
        for i, user_id in enumerate(batch_user_ids):
            # Consider items starting at start_rank onward
            sims_slice = sorted_similarities_np[i, start_rank:]
            indices_slice = sorted_indices_np[i, start_rank:]
            # Find positions where similarity is below the threshold
            valid_positions = np.where(sims_slice < relevance_thresh)[0]
            # Select up to M negatives
            if valid_positions.size > 0:
                selected_positions = valid_positions[:M]
                user_negatives = indices_slice[selected_positions]
            else:
                user_negatives = np.array([], dtype=np.int64)
            # Retrieve negative item IDs and texts
            negative_item_ids = [item_ids[j] for j in user_negatives]
            negative_item_texts = [item_texts[j] for j in user_negatives]
            negatives[user_id] = {
                'item_ids': negative_item_ids,
                'item_texts': negative_item_texts
            }
            if use_sparse:
                negative_item_features = [items[j].get('item_features', None) for j in user_negatives]
                negatives['negative_item_features'][user_id] = negative_item_features

        if debug:
            batch_elapsed_time = time.time() - batch_start_time
            print(f"Processed batch {batch_idx+1}/{total_batches} in {batch_elapsed_time:.2f} seconds")

        # Free memory for the batch variables
        del similarities, sorted_similarities, sorted_indices, sorted_similarities_np, sorted_indices_np
        torch.cuda.empty_cache()

    return negatives




def generate_hard_negatives(
    model, data_samples, tokenizer, negatives, config,
    user_feature_size, item_feature_size, debug=False
):
    """
    Generate hard negatives from precomputed negatives using a cross-encoder model.

    Key changes
    ------------
    • *mixed_precision* in the config **now means pure FP16** (model.half()).
    • The previous AMP-based mixed-precision code is left in place but **commented out**.
    • Feature tensors are created in FP16 when half precision is active.
    """
    
    import time
    import numpy as np
    import torch
    import torch.nn as nn
    from collections import defaultdict
    from torch.utils.data import DataLoader

    # Assume the following helper functions and classes are defined elsewhere:
    # - get_tqdm
    # - CrossEncoderDataset

    tqdm_fn = get_tqdm(config)

    # --------------------------------------------------
    # 1. Prep model / mode / precision
    # --------------------------------------------------
    model.eval()
    device = next(model.parameters()).device

    # Safely access use_sparse attribute with DataParallel
    use_sparse = model.module.use_sparse if isinstance(model, nn.DataParallel) else model.use_sparse

    # Half-precision flag (repurposed mixed_precision)
    use_half_precision = config.get('mixed_precision', False)  # True -> model.half()

    if use_half_precision:
        print("Using pure FP16 (model.half()) for hard negative generation")
        if isinstance(model, nn.DataParallel):
            model.module.half()
        else:
            model.half()
        torch.set_grad_enabled(False)  # redundant inside no_grad but explicit

    # ---------------------------------------------------------------------
    # 2. Read configuration parameters
    # ---------------------------------------------------------------------
    N = config['N']                                     # Number of hard negatives per user
    batch_size = config.get('negative_batch_size', 128) # Default batch size
    max_length = config.get('max_length', 512)          # Tokeniser max length
    apply_count_threshold = config.get('apply_count_threshold', 10)

    if debug:
        print("Preparing data for processing...")
        data_prep_start_time = time.time()

    # ---------------------------------------------------------------------
    # 3. Compute apply counts & build per-user data
    # ---------------------------------------------------------------------
    user_apply_counts = defaultdict(int)
    for sample in data_samples:
        user_id = sample['user_id']
        user_apply_counts[user_id] += 1

    user_data = []
    processed_users = set()
    for sample in data_samples:
        user_id = sample['user_id']
        if (
            user_apply_counts[user_id] > apply_count_threshold
            and user_id not in processed_users
        ):
            processed_users.add(user_id)
            user_text = sample['user_text']
            user_features = sample.get('user_features', None)

            # Use precomputed negatives
            neg_item_texts = negatives[user_id]['item_texts']  # List of negative item texts
            neg_item_ids   = negatives[user_id]['item_ids']    # List of negative item IDs
            if use_sparse:
                neg_features_list = negatives['negative_item_features'][user_id]
            else:
                neg_features_list = [None] * len(neg_item_texts)

            user_data.append({
                'user_id': user_id,
                'user_text': user_text,
                'user_features': user_features,
                'negative_item_texts': neg_item_texts,
                'negative_item_ids': neg_item_ids,
                'negative_item_features': neg_features_list
            })

    if debug:
        data_prep_elapsed_time = time.time() - data_prep_start_time
        print(f"Data preparation completed in {data_prep_elapsed_time:.2f} seconds")
        print(f"Total number of users to process: {len(user_data)} (Users with applies > {apply_count_threshold})")

    # ---------------------------------------------------------------------
    # 4. DataLoader over users
    # ---------------------------------------------------------------------
    def collate_fn(batch):
        return batch  # batch is already a list of dicts

    dataloader = DataLoader(
        user_data,
        batch_size=batch_size,
        shuffle=False,
        num_workers=6,
        collate_fn=collate_fn
    )

    if debug:
        print(f"Total number of batches: {len(dataloader)}")

    # ---------------------------------------------------------------------
    # 5. Main loop (no_grad)
    # ---------------------------------------------------------------------
    hard_negatives = {}

    with torch.no_grad():
        for batch_idx, batch in enumerate(tqdm_fn(dataloader, desc="Generating hard negatives")):
            if debug:
                batch_start_time = time.time()

            # ----------------------------------------------------------
            # Per-user processing inside the batch
            # ----------------------------------------------------------
            for user in batch:
                if debug:
                    user_start_time = time.time()

                user_id                 = user['user_id']
                user_text               = user['user_text']
                user_features           = user['user_features']
                neg_item_texts          = user['negative_item_texts']
                neg_item_ids            = user['negative_item_ids']
                neg_item_features_list  = user['negative_item_features']

                # ---- Tokenise user text once ----
                if debug:
                    tokenization_user_start_time = time.time()

                inputs_user = tokenizer(
                    user_text,
                    max_length=max_length,
                    truncation=True,
                    padding='max_length',
                    return_tensors='pt'
                )

                if debug:
                    tokenization_user_elapsed = time.time() - tokenization_user_start_time
                    print(f"User {user_id}: Tokenized user text in {tokenization_user_elapsed:.2f} seconds")

                # ---- Tokenise negative item texts ----
                if debug:
                    tokenization_negatives_start_time = time.time()

                inputs_negatives = tokenizer(
                    neg_item_texts,
                    max_length=max_length,
                    truncation=True,
                    padding='max_length',
                    return_tensors='pt'
                )

                if debug:
                    tokenization_negatives_elapsed = time.time() - tokenization_negatives_start_time
                    print(f"User {user_id}: Tokenized negative item texts in {tokenization_negatives_elapsed:.2f} seconds")

                # ---- Build concatenated [user, item] inputs ----
                input_ids = torch.cat(
                    [inputs_user['input_ids'].repeat(len(neg_item_texts), 1),
                     inputs_negatives['input_ids']],
                    dim=1
                )
                attention_mask = torch.cat(
                    [inputs_user['attention_mask'].repeat(len(neg_item_texts), 1),
                     inputs_negatives['attention_mask']],
                    dim=1
                )

                input_ids      = input_ids.to(device)
                attention_mask = attention_mask.to(device)

                # ---- Optional sparse features ----
                features_tensor = None
                if use_sparse:
                    if debug:
                        feature_prep_start_time = time.time()

                    dtype_ = torch.float16 if use_half_precision else torch.float32
                    user_features_tensor = torch.tensor(user_features, dtype=dtype_, device=device).unsqueeze(0)
                    neg_item_features_tensor = torch.tensor(neg_item_features_list, dtype=dtype_, device=device)
                    features_tensor = torch.cat(
                        [user_features_tensor.repeat(len(neg_item_texts), 1),
                         neg_item_features_tensor],
                        dim=1
                    )

                    if debug:
                        feature_prep_elapsed_time = time.time() - feature_prep_start_time
                        print(f"User {user_id}: Prepared features in {feature_prep_elapsed_time:.2f} seconds")

                # --------------------------------------------------
                # 6. Forward pass
                # --------------------------------------------------
                if debug:
                    inference_start_time = time.time()

                if use_half_precision:
                    # ---- Pure FP16 inference ----
                    if use_sparse and features_tensor is not None:
                        logits = model(input_ids=input_ids,
                                       attention_mask=attention_mask,
                                       features=features_tensor)
                    else:
                        logits = model(input_ids=input_ids,
                                       attention_mask=attention_mask)
                else:
                    # =========================================================
                    # Old AMP mixed-precision path (kept for reference)
                    # =========================================================
                    # use_mixed_precision = config.get('mixed_precision', True)
                    # if use_mixed_precision:
                    #     with torch.cuda.amp.autocast():
                    #         if use_sparse and features_tensor is not None:
                    #             logits = model(input_ids=input_ids,
                    #                            attention_mask=attention_mask,
                    #                            features=features_tensor)
                    #         else:
                    #             logits = model(input_ids=input_ids,
                    #                            attention_mask=attention_mask)
                    # else:
                    #     if use_sparse and features_tensor is not None:
                    #         logits = model(input_ids=input_ids,
                    #                        attention_mask=attention_mask,
                    #                        features=features_tensor)
                    #     else:
                    #         logits = model(input_ids=input_ids,
                    #                        attention_mask=attention_mask)
                    # ---------------------------------------------------------
                    # Fallback to full FP32 when half precision is off
                    if use_sparse and features_tensor is not None:
                        logits = model(input_ids=input_ids,
                                       attention_mask=attention_mask,
                                       features=features_tensor)
                    else:
                        logits = model(input_ids=input_ids,
                                       attention_mask=attention_mask)

                if debug:
                    inference_elapsed_time = time.time() - inference_start_time
                    print(f"User {user_id}: Model inference completed in {inference_elapsed_time:.2f} seconds")

                # ---- Keep scores on GPU ----
                scores = logits.squeeze(-1)  # shape [K]

                # --------------------------------------------------
                # 7. Select hard negatives (skip 10 hardest, keep N)
                # --------------------------------------------------
                if debug:
                    selection_start_time = time.time()

                num_to_skip = 10
                num_total   = N + num_to_skip
                if scores.shape[0] < num_total:
                    num_total = scores.shape[0]

                top_scores, top_indices = torch.topk(scores, num_total, largest=True, sorted=False)
                top_indices = top_indices.cpu().numpy()

                selected_indices = top_indices[num_to_skip:]
                if len(selected_indices) > N:
                    selected_indices = selected_indices[:N]

                hard_neg_ids     = [neg_item_ids[i]            for i in selected_indices]
                hard_neg_texts   = [neg_item_texts[i]          for i in selected_indices]
                if use_sparse:
                    hard_neg_features = [neg_item_features_list[i] for i in selected_indices]

                hard_negatives[user_id] = {
                    'item_ids'  : hard_neg_ids,
                    'item_texts': hard_neg_texts
                }
                if use_sparse:
                    hard_negatives[user_id]['item_features'] = hard_neg_features

                if debug:
                    selection_elapsed_time = time.time() - selection_start_time
                    user_elapsed_time      = time.time() - user_start_time
                    print(f"User {user_id}: Selected top negatives in {selection_elapsed_time:.2f} seconds")
                    print(f"User {user_id}: Processed in {user_elapsed_time:.2f} seconds")

            # ---- Batch timer ----
            if debug:
                batch_elapsed_time = time.time() - batch_start_time
                print(f"Batch {batch_idx+1}/{len(dataloader)}: Processed in {batch_elapsed_time:.2f} seconds")

    # ---------------------------------------------------------------------
    # 8. Return
    # ---------------------------------------------------------------------
    return hard_negatives




def precompute_random_negatives(users, items, positive_matches, config, debug=False):
    """
    Function to precompute N random negatives per user.
    Optimized using NumPy for efficient sampling and includes bug fixes.
    """
    import time
    import numpy as np
    from collections import defaultdict

    tqdm_fn = get_tqdm(config)

    if debug:
        total_start_time = time.time()
        print("Starting precompute_random_negatives...")

    # Extract item IDs, texts, and features
    if debug:
        item_prep_start_time = time.time()

    item_ids = [item['item_id'] for item in items]
    item_texts = [item['item_text'] for item in items]
    item_id_to_text = {item['item_id']: item['item_text'] for item in items}
    item_id_to_features = {item['item_id']: item.get('item_features', None) for item in items}

    # Convert item IDs to a NumPy array for efficient operations
    np_item_ids = np.array(item_ids)
    
    # Convert item_ids (assumed to be a list or similar) to a NumPy array
    np_item_ids = np.array(item_ids)

    # Determine the number of samples that correspond to 10% of the array
    sample_size = max(1, int(0.1 * len(np_item_ids)))  # Ensures at least 1 element is selected

    # Randomly select 10% of the item IDs without replacement
    np_item_ids = np.random.choice(np_item_ids, size=sample_size, replace=False)

    if debug:
        item_prep_elapsed_time = time.time() - item_prep_start_time
        print(f"Prepared item IDs, texts, and features in {item_prep_elapsed_time:.2f} seconds")

    # Build positive item IDs per user
    if debug:
        positive_prep_start_time = time.time()

    positive_item_ids_per_user = defaultdict(set)
    for match in positive_matches:
        cid = match['user_id']
        jid = match['item_id']
        positive_item_ids_per_user[cid].add(jid)

    if debug:
        positive_prep_elapsed_time = time.time() - positive_prep_start_time
        print(f"Built positive item IDs per user in {positive_prep_elapsed_time:.2f} seconds")

    N = config['N']
    use_sparse = config['use_sparse']
    random_negatives = {}
    total_users = len(users)

    if debug:
        user_loop_start_time = time.time()
        print(f"Processing {total_users} users...")

    for idx, user in enumerate(tqdm_fn(users, desc="Random Sampling")):
    
        #if True:
        #    continue
    
        if debug and idx % 1000 == 0 and idx > 0:
            user_loop_elapsed = time.time() - user_loop_start_time
            print(f"Processed {idx}/{total_users} users in {user_loop_elapsed:.2f} seconds")

        cid = user['user_id']
        positive_jids = positive_item_ids_per_user.get(cid, set())
        
        
        if len(set(list(positive_jids))) <= config.get('apply_count_threshold', 10):
            continue
            
        #print("user applies: ", len(set(list(positive_jids))))
            
        # Use NumPy set difference to efficiently compute negative item IDs
        negative_jids = np.setdiff1d(np_item_ids, list(positive_jids), assume_unique=True)
        
        #negative_jids = np_item_ids
        

        if len(negative_jids) >= N:
            sampled_neg_jids = np.random.choice(negative_jids, N, replace=False)
        else:
            sampled_neg_jids = np.random.choice(negative_jids, N, replace=True)

        sampled_neg_jids = sampled_neg_jids.tolist()
        neg_item_texts = [item_id_to_text[jid] for jid in sampled_neg_jids]

        if use_sparse:
            neg_features_list = [item_id_to_features[jid] for jid in sampled_neg_jids]
        else:
            neg_features_list = [None] * len(sampled_neg_jids)

        random_negatives[cid] = {
            'item_ids': sampled_neg_jids,
            'item_texts': neg_item_texts,
            'item_features': neg_features_list  # Store features here under user_id
        }

    if debug:
        user_loop_elapsed_time = time.time() - user_loop_start_time
        total_elapsed_time = time.time() - total_start_time
        print(f"Processed all users in {user_loop_elapsed_time:.2f} seconds")
        print(f"Total time for precompute_random_negatives: {total_elapsed_time:.2f} seconds")

    return random_negatives


import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader

def train(model, train_dataset, optimizer, device, config, epoch, scheduler, scaler=None):
    """
    Train the CrossEncoderModel for one epoch with a listwise or pairwise ranking loss.
    Option to use mixed precision training with GradScaler.
    
    Args:
        model: The model to train
        train_dataset: The training dataset
        optimizer: The optimizer
        device: The device to train on
        config: Configuration dictionary
        epoch: Current epoch number
        scheduler: Learning rate scheduler
        scaler: Optional GradScaler for mixed precision training
    """
    tqdm = get_tqdm(config)

    # Initialize optimizer and accumulation steps
    optimizer.zero_grad()
    accumulation_steps = config['accumulation_steps']  # Update weights every N batches
    
    # Check if optimizations are enabled
    optimisation_enabled = config.get('optimisation', True)
    use_mixed_precision = config.get('mixed_precision', True) and optimisation_enabled
    use_gradient_clipping = optimisation_enabled
    gradient_clip_norm = config.get('gradient_clip_norm', 1.0) if use_gradient_clipping else None
    
    # Get use_sparse attribute safely with DataParallel
    use_sparse = model.module.use_sparse if isinstance(model, nn.DataParallel) else model.use_sparse
    
    if use_mixed_precision:
        if scaler is None:
            print("Warning: Mixed precision enabled but no scaler provided. Using default scaler.")
            scaler = torch.cuda.amp.GradScaler()
        print(f"Mixed precision training enabled (Epoch {epoch+1})")
    else:
        print(f"Mixed precision training disabled (Epoch {epoch+1})")
    
    if use_gradient_clipping:
        print(f"Gradient clipping enabled with norm {gradient_clip_norm} (Epoch {epoch+1})")

    # Training function with listwise ranking loss
    model.train()
    train_dataloader = DataLoader(
        train_dataset,
        batch_size=config['train_batch_size'],
        shuffle=True,
        collate_fn=train_dataset.collate_fn,
        num_workers=config['num_workers'],
        pin_memory=True,
        persistent_workers=True if config['num_workers'] > 0 else False  # Keep workers alive between iterations
    )
    total_loss = 0

    # This is still defined here (not used in the final loss)
    criterion = nn.CrossEntropyLoss()

    for batch_idx, batch in enumerate(tqdm(train_dataloader, desc=f"Training Epoch {epoch+1}")):
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels']
        user_to_indices = batch['user_to_indices']

        # Use autocast for mixed precision training if enabled
        if use_mixed_precision:
            with torch.cuda.amp.autocast():
                if use_sparse:
                    features = batch['features'].to(device)
                    logits = model(input_ids=input_ids, attention_mask=attention_mask, features=features)
                else:
                    logits = model(input_ids=input_ids, attention_mask=attention_mask)

                # Calculate loss - this part remains the same regardless of mixed precision
                loss = calculate_loss(logits, labels, user_to_indices, device, config)
                # Normalize loss for gradient accumulation
                loss = loss / accumulation_steps
        else:
            # Standard full-precision training
            if use_sparse:
                features = batch['features'].to(device)
                logits = model(input_ids=input_ids, attention_mask=attention_mask, features=features)
            else:
                logits = model(input_ids=input_ids, attention_mask=attention_mask)

            # Calculate loss
            loss = calculate_loss(logits, labels, user_to_indices, device, config)
            # Normalize loss for gradient accumulation
            loss = loss / accumulation_steps

        # Use scaler for backward pass in mixed precision if enabled
        if use_mixed_precision and scaler is not None:
            scaler.scale(loss).backward()
        else:
            # Standard backward pass
            loss.backward()

        # Perform optimizer step every 'accumulation_steps' batches
        if (batch_idx + 1) % accumulation_steps == 0 or (batch_idx + 1 == len(train_dataloader)):
            if use_mixed_precision and scaler is not None:
                # Unscale before gradient clipping
                scaler.unscale_(optimizer)
                
                # Apply gradient clipping for stability if enabled
                if use_gradient_clipping and gradient_clip_norm is not None:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=gradient_clip_norm)
                
                # Step with scaler
                scaler.step(optimizer)
                scaler.update()
            else:
                # Apply gradient clipping for stability if enabled
                if use_gradient_clipping and gradient_clip_norm is not None:
                    torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=gradient_clip_norm)
                
                # Standard optimizer step
                optimizer.step()
            
            # Zero gradients
            optimizer.zero_grad()

        # Accumulate total loss (multiply back to original scale)
        total_loss += loss.item() * accumulation_steps

    avg_loss = total_loss / len(train_dataloader)
    print(f"Average training loss: {avg_loss:.4f}")

    # Update learning rate
    scheduler.step()
    current_lr = scheduler.get_last_lr()[0]
    print(f"Current learning rate: {current_lr:.6f}")

    return scaler  # Return the scaler to preserve its state between epochs


# Helper function for calculating loss
def calculate_loss(logits, labels, user_to_indices, device, config):
    """
    Calculate loss using either listwise or pairwise ranking approach.
    Extracted to a separate function for clarity.
    """
    # Make sure to start with a Tensor for loss
    loss = torch.zeros((), device=device, requires_grad=True)

    # If you'd like to configure margin for pairwise approach, you can keep it in config as well
    margin = 1.0  

    # Loop over each user group
    for user_id, indices in user_to_indices.items():
        user_logits = logits[indices]    # shape: (k,)
        user_labels = labels[indices]    # shape: (k,)

        positive_indices = (user_labels == 1).nonzero(as_tuple=True)[0]
        negative_indices = (user_labels == 0).nonzero(as_tuple=True)[0]

        # If no positives, skip
        if positive_indices.numel() == 0:
            continue
            
        # -------------------------
        # SAMPLING POSITIVES (NEW)
        # -------------------------
        max_positives = 30
        if positive_indices.numel() > max_positives:
            perm = torch.randperm(positive_indices.numel())
            positive_indices = positive_indices[perm[:max_positives]]

        # ---------------------------------------------------------
        # Check config for "ranking_loss_mode" to decide the approach
        # ---------------------------------------------------------
        if config.get("ranking_loss_mode", "listwise") == "listwise":
            # MULTI-POSITIVE LISTWISE CROSS-ENTROPY
            # -------------------------------------
            # 1. Compute log-softmax across user_logits
            # 2. Sum or average the log-prob for all positive items

            # user_logits shape: (k,)
            log_softmaxed = F.log_softmax(user_logits, dim=0)  # also shape: (k,)

            # Gather log-softmax values of the positives
            pos_log_probs = log_softmaxed[positive_indices]  # shape: (#positives,)

            # Option 1: sum of positives
            loss_user = -pos_log_probs.sum()

            # Optionally normalize by #positives if you prefer an average:
            num_positives = len(positive_indices)
            loss_user /= num_positives

        else:
            # PAIRWISE HINGE-STYLE RANKING
            # -------------------------------------------
            # We want logit[pos] - logit[neg] >= margin
            # => hinge loss = max(0, margin - (pos - neg))
            loss_user = torch.zeros((), device=device, requires_grad=True)
            for p in positive_indices:
                for n in negative_indices:
                    diff = user_logits[p] - user_logits[n]
                    loss_pair = F.relu(margin - diff)  # shape: ()
                    loss_user = loss_user + loss_pair

            # Normalize by number of pairs
            num_pairs = len(negative_indices)
            
            if num_pairs > 0:
                loss_user = loss_user / num_pairs

        # Accumulate into total loss
        loss = loss + loss_user

    # Original code for per-user averaging:
    if len(user_to_indices) > 0:
        loss = loss / len(user_to_indices)
    else:
        # Keep it a Tensor
        loss = torch.zeros((), device=device, requires_grad=True)
        
    return loss
    
eval_visual_fixed_user_ids = []



def evaluate(model, tokenizer, users_eval, items_eval, positive_matches_eval, config, bi_encoder, epoch):
    """
    Evaluate the model by computing Precision at N using both the bi-encoder and cross-encoder.
    Only evaluates users who have more than a specified number of applications.
    """
    import torch
    import numpy as np
    from collections import defaultdict

    # Use tqdm for progress bars
    tqdm_fn = get_tqdm(config)

    # Set model to evaluation mode and get device
    model.eval()
    device = next(model.parameters()).device

    # Get use_sparse attribute safely with DataParallel
    use_sparse = model.module.use_sparse if isinstance(model, nn.DataParallel) else model.use_sparse

    # Retrieve evaluation parameters from config
    Ns = config['eval_Ns']
    K = config.get('eval_K', 50)  # Number of top items to retrieve using bi-encoder

    # Retrieve apply count threshold from config
    eval_apply_count_threshold = config.get('eval_apply_count_threshold', 10)

    # Build user and item texts and IDs
    user_texts_all = [user['user_text'] for user in users_eval]
    user_ids_all = [user['user_id'] for user in users_eval]
    item_texts = [item['item_text'] for item in items_eval]
    item_ids = [item['item_id'] for item in items_eval]

    # Create mappings from IDs to features
    user_id_to_features_all = {
        user['user_id']: user.get('user_features', None)
        for user in users_eval
    }
    item_id_to_features = {
        item['item_id']: item.get('item_features', None)
        for item in items_eval
    }

    # Create a mapping from user_id to ground truth item_ids
    user_to_items = defaultdict(set)
    for match in positive_matches_eval:
        cid = match['user_id']
        jid = match['item_id']
        user_to_items[cid].add(jid)

    # Compute application counts per user
    user_apply_counts = {cid: len(items) for cid, items in user_to_items.items()}

    # Filter users based on apply count threshold
    filtered_user_ids = [cid for cid in user_ids_all if user_apply_counts.get(cid, 0) > eval_apply_count_threshold]
    if not filtered_user_ids:
        print(f"No users have more than {eval_apply_count_threshold} applications.")
        return {}

    # Update user_texts, user_ids, user_id_to_features to only include filtered users
    user_ids = filtered_user_ids
    user_texts = [user_texts_all[user_ids_all.index(cid)] for cid in user_ids]
    user_id_to_features = {cid: user_id_to_features_all[cid] for cid in user_ids}

    # If using sparse features, set feature sizes
    if config['use_sparse']:
        # Verify that all evaluation users and items have 'user_features' and 'item_features'
        if all('user_features' in user for user in users_eval) and all('item_features' in item for item in items_eval):
            user_feature_lengths = [len(user['user_features']) for user in users_eval]
            item_feature_lengths = [len(item['item_features']) for item in items_eval]
            user_feature_size = max(user_feature_lengths)
            item_feature_size = max(item_feature_lengths)
            print(f"User feature size detected and set to: {user_feature_size}")
            print(f"Item feature size detected and set to: {item_feature_size}")
        else:
            raise ValueError("All evaluation users and items must have 'user_features' and 'item_features' when 'use_sparse' is True.")
    else:
        user_feature_size = 0
        item_feature_size = 0

    # Compute embeddings using bi-encoder
    print("Computing user embeddings for evaluation...")
    user_embeddings = compute_bi_encoder_embeddings(
        bi_encoder, tokenizer, user_texts, config
    )
    print("Computing item embeddings for evaluation...")
    item_embeddings = compute_bi_encoder_embeddings(
        bi_encoder, tokenizer, item_texts, config
    )

    # Normalize embeddings
    user_embeddings = torch.nn.functional.normalize(user_embeddings, p=2, dim=1)
    item_embeddings = torch.nn.functional.normalize(item_embeddings, p=2, dim=1)

    # Move item_embeddings to the same device as batch_user_embeddings
    item_embeddings = item_embeddings.to(device)

    # Initialize per-user data structures
    num_users = len(user_ids)
    num_items = len(item_ids)

    # For storing top K item indices and similarities per user
    topk_similarities = np.zeros((num_users, K), dtype=np.float32)
    topk_indices = np.zeros((num_users, K), dtype=int)

    # Compute similarities in batches to handle memory constraints
    print("Computing top K similarities in batches...")
    eval_batch_size = config.get('eval_batch_size', 512)
    item_batch_size = config.get('eval_item_batch_size', 5000)  # New parameter to control item batch size

    for i in tqdm_fn(range(0, num_users, eval_batch_size), desc="Users"):
        batch_user_embeddings = user_embeddings[i:i+eval_batch_size].to(device)

        # Initialize per-batch top K similarities and indices
        batch_size = batch_user_embeddings.shape[0]
        batch_topk_similarities = np.full((batch_size, K), -np.inf, dtype=np.float32)
        batch_topk_indices = np.zeros((batch_size, K), dtype=int)

        for j in range(0, num_items, item_batch_size):
            item_embeddings_chunk = item_embeddings[j:j+item_batch_size].to(device)
            item_indices_chunk = np.arange(j, min(j+item_batch_size, num_items))

            # Compute similarities between batch users and item chunk
            with torch.no_grad():
                sim_chunk = torch.matmul(batch_user_embeddings, item_embeddings_chunk.t())  # [batch_size, item_chunk_size]
            sim_chunk = sim_chunk.cpu().numpy()  # [batch_size, item_chunk_size]

            # For each user in the batch, update top K similarities
            for bi in range(batch_size):
                # Combine current top K with new similarities
                user_similarities = np.concatenate([batch_topk_similarities[bi], sim_chunk[bi]])
                user_indices = np.concatenate([batch_topk_indices[bi], item_indices_chunk])
                # Get indices of top K similarities
                topk = np.argpartition(-user_similarities, K-1)[:K]
                # Update top K similarities and indices
                batch_topk_similarities[bi] = user_similarities[topk]
                batch_topk_indices[bi] = user_indices[topk]

        # After processing all item chunks, store the top K similarities and indices for this batch
        topk_similarities[i:i+batch_size] = batch_topk_similarities
        topk_indices[i:i+batch_size] = batch_topk_indices

    # Now, we have top K similarities and indices for all users
    # Proceed with evaluation

    ### Evaluation using bi-encoder similarities ###
    print("\nEvaluating using bi-encoder similarities...")
    precisions_at_N_bi = {N: [] for N in Ns}
    for idx, user_id in enumerate(user_ids):
        user_topk_indices = topk_indices[idx]
        user_topk_similarities = topk_similarities[idx]
        # Sort the top K similarities and indices
        sorted_order = np.argsort(-user_topk_similarities)
        sorted_indices = user_topk_indices[sorted_order]
        sorted_item_ids = [item_ids[i] for i in sorted_indices]
        ground_truth_item_ids = user_to_items.get(user_id, set())
        for N in Ns:
            top_N_item_ids = sorted_item_ids[:N]
            hits = ground_truth_item_ids.intersection(top_N_item_ids)
            precision = len(hits) / N
            precisions_at_N_bi[N].append(precision)

    # Compute average precision at each N for bi-encoder
    avg_precisions_bi = {}
    print("\nAverage Precision at N using bi-encoder:")
    for N in Ns:
        avg_precision = np.mean(precisions_at_N_bi[N]) if precisions_at_N_bi[N] else 0.0
        avg_precisions_bi[N] = avg_precision
        print(f"Precision at {N}: {avg_precision:.4f}")

    ### Proceed with cross-encoder evaluation ###
    # Prepare cross-encoder inputs
    print("\nEvaluating with cross-encoder...")
    all_user_texts = []
    all_item_texts = []
    all_user_ids = []
    all_item_ids_list = []  # Collect item_ids
    all_user_features = []
    all_item_features = []

    for idx, user_id in enumerate(user_ids):
        user_topk_indices = topk_indices[idx]
        user_topk_similarities = topk_similarities[idx]
        # Sort the top K similarities and indices
        sorted_order = np.argsort(-user_topk_similarities)
        sorted_indices = user_topk_indices[sorted_order]
        sorted_item_ids = [item_ids[i] for i in sorted_indices]
        sorted_item_texts = [item_texts[i] for i in sorted_indices]
        user_text = user_texts[idx]
        user_feature = user_id_to_features.get(user_id, None)
        num_items = len(sorted_item_texts)
        all_user_texts.extend([user_text] * num_items)
        all_user_features.extend([user_feature] * num_items)
        all_item_texts.extend(sorted_item_texts)
        all_item_ids_list.extend(sorted_item_ids)
        item_features = [
            item_id_to_features.get(item_id, None) for item_id in sorted_item_ids
        ]
        all_item_features.extend(item_features)
        all_user_ids.extend([user_id] * num_items)

    # Proceed with cross-encoder evaluation
    total_pairs = len(all_user_texts)
    scores = []
    negative_batch_size = config.get('negative_batch_size', 512)
    with torch.no_grad():
        for i in tqdm_fn(
            range(0, total_pairs, negative_batch_size), desc="Evaluating"
        ):
            batch_user_texts = all_user_texts[i:i+negative_batch_size]
            batch_item_texts = all_item_texts[i:i+negative_batch_size]
            batch_user_features = all_user_features[i:i+negative_batch_size]
            batch_item_features = all_item_features[i:i+negative_batch_size]
            inputs = tokenizer(
                batch_user_texts,
                batch_item_texts,
                max_length=config['max_length'],
                truncation=True,
                padding=True,
                return_tensors='pt'
            )
            input_ids = inputs['input_ids'].to(device)
            attention_mask = inputs['attention_mask'].to(device)
            if use_sparse:
                # Prepare features
                features_list = []
                for cf, jf in zip(batch_user_features, batch_item_features):
                    if cf is not None and jf is not None:
                        features = np.concatenate([cf, jf])
                        features = torch.tensor(features, dtype=torch.float)
                    else:
                        # Use the calculated feature sizes
                        features = torch.zeros(user_feature_size + item_feature_size, dtype=torch.float)
                    features_list.append(features)
                features_tensor = torch.stack(features_list).to(device)
                logits = model(
                    input_ids=input_ids, attention_mask=attention_mask, features=features_tensor
                )
            else:
                logits = model(input_ids=input_ids, attention_mask=attention_mask)
            # Since logits is already the output, and it's a tensor of shape [batch_size], we can directly use it
            batch_scores = logits.cpu().tolist()
            scores.extend(batch_scores)

    # Collect scores per user
    user_item_scores = defaultdict(list)
    user_item_ids = defaultdict(list)
    idx = 0
    for cid, item_id in zip(all_user_ids, all_item_ids_list):
        user_item_scores[cid].append(scores[idx])
        user_item_ids[cid].append(item_id)
        idx += 1

    # Compute precision at N using cross-encoder
    precisions_at_N_cross = {N: [] for N in Ns}
    for user_id in user_ids:
        item_scores = user_item_scores[user_id]
        item_ids_list = user_item_ids[user_id]
        sorted_indices = np.argsort(-np.array(item_scores))
        sorted_item_ids = [item_ids_list[i] for i in sorted_indices]
        ground_truth_item_ids = user_to_items.get(user_id, set())
        for N in Ns:
            top_N_item_ids = sorted_item_ids[:N]
            hits = ground_truth_item_ids.intersection(top_N_item_ids)
            precision = len(hits) / N
            precisions_at_N_cross[N].append(precision)

    # Compute average precision at each N for cross-encoder
    avg_precisions = {}
    print("\nAverage Precision at N using cross-encoder:")
    for N in Ns:
        avg_precision = (
            np.mean(precisions_at_N_cross[N]) if precisions_at_N_cross[N] else 0.0
        )
        avg_precisions[N] = avg_precision
        print(f"Precision at {N}: {avg_precision:.4f}")

    # Log evaluation metrics to W&B or MLflow
    metrics = {f"Precision@{N}": avg_precisions[N] for N in Ns}
    metrics.update({f"BiEncoder Precision@{N}": avg_precisions_bi[N] for N in Ns})
    metrics["Epoch"] = epoch + 1

    if config.get('use_wandb', False):
        import wandb
        wandb.log(metrics)
    elif config.get('use_mlflow', False):
        import mlflow
        for key, value in metrics.items():
            mlflow.log_metric(key, value, step=epoch+1)
            
        
    #---------------------------------------
    # 5) SANITY CHECK: Print Top 10 and Bottom 10 Recommendations for 5 Users
    #---------------------------------------
    print("\n--- SANITY CHECK: Top 10 and Bottom 10 Recommendations for 5 Users ---\n")

    # Create mappings for user id -> user text and item id -> item text
    user_id_to_text = {cid: text for cid, text in zip(user_ids, user_texts)}
    item_id_to_text = {jid: text for jid, text in zip(item_ids, item_texts)}


    global eval_visual_fixed_user_ids
    
    if len(eval_visual_fixed_user_ids) == 0:
        # Choose 5 user IDs at random from user_ids
        eval_visual_fixed_user_ids = random.sample(user_ids, 5)

    for cid in eval_visual_fixed_user_ids:
        print(f"User ID: {cid}")
        print(f"User Text: {user_id_to_text[cid]}\n")
    
        scores_list = user_item_scores[cid]
        item_ids_list = user_item_ids[cid]
        scores_arr = np.array(scores_list)
    
        # === Sort indices in descending order by score ===
        sorted_indices = np.argsort(-scores_arr)

        # === Top 10 Unique Recommendations ===
        top10_unique_indices = []
        seen_texts = set()

        # Iterate over all sorted indices and pick items with unique text until we have 10.
        for idx in sorted_indices:
            jid = item_ids_list[idx]
            item_text = item_id_to_text.get(jid, "N/A")
            if item_text in seen_texts:
                continue  # Skip duplicates
            seen_texts.add(item_text)
            top10_unique_indices.append(idx)
            if len(top10_unique_indices) >= 10:
                break

        print("Top 10 Unique Recommendations:")
        for idx in top10_unique_indices:
            jid = item_ids_list[idx]
            score_val = scores_arr[idx]
            item_text = item_id_to_text.get(jid, "N/A")
            print(f"  Item ID: {jid}, Score: {score_val:.4f}")
            print(f"  Item Text: {item_text}\n")

        # === Mid 10 Recommendations ===
        # Calculate starting index for the middle 10 recommendations.
        total = len(sorted_indices)
        mid_start = total // 2 - 5  # Adjust if total is small
        mid10_indices = sorted_indices[mid_start:mid_start+10]

        print("Mid 10 Recommendations:")
        for idx in mid10_indices:
            jid = item_ids_list[idx]
            score_val = scores_arr[idx]
            item_text = item_id_to_text.get(jid, "N/A")
            print(f"  Item ID: {jid}, Score: {score_val:.4f}")
            print(f"  Item Text: {item_text}\n")

        # === Bottom 10 Recommendations ===
        bottom10_indices = np.argsort(scores_arr)[:10]

        print("Bottom 10 Recommendations:")
        for idx in bottom10_indices:
            jid = item_ids_list[idx]
            score_val = scores_arr[idx]
            item_text = item_id_to_text.get(jid, "N/A")
            print(f"  Item ID: {jid}, Score: {score_val:.4f}")
            print(f"  Item Text: {item_text}\n")

        print("=" * 10 + "\n")

    return avg_precisions
    
    

