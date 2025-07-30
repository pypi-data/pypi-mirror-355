# interfusion/config.py

def get_default_config():
    config = {
        'random_seed': 1689,
        'max_length': 256,
        'use_sparse': False,
        'start_rank': 128,
        'use_wandb': True,
        'use_mlflow': False,           # from default config
        'bi_encoder_model_name': 'BERT-Tiny_L-2_H-128_A-2-ft',
        'cross_encoder_model_name': 'cross-encoder/ms-marco-MiniLM-L-4-v2',
        'use_tqdm': True,              # from default config
        'tqdm_type': 'standard',
        'learning_rate': 2e-6,
        'initial_learning_rate': 2e-6,
        'num_epochs': 100,
        'train_batch_size': 8,
        'accumulation_steps': 64,
        'bi_encoder_batch_size': 256,
        'negative_batch_size': 256,
        'random_user_sample_amount': 0.3,
        'M': 100,
        'N': 20,
        'bi-encode_relevance_thresh': 0.75,
        'apply_count_threshold': 0,
        'eval_Ns': [1, 5, 10, 20, 50, 100],
        'save_dir': 'saved_models',
        'num_workers': 6,
        'eval_K': 250,
        'eval_epoch': 1,
        'eval_batch_size': 32,
        'eval_apply_count_threshold': 0,
        'hard_negative_sampling_frequency': 2,
        'temperature': 0.05,
        'wandb_project': 'interfusion_project2',
        'wandb_run_name': 'interfusion_runxM250',
        'continue_training': True,
        'saved_model_path': 'interfusion_best_p5_0.0916.pt',
        'train_on_item_to_user': False,
        'ranking_loss_mode': "listwise",
        # Add these new configurations
        'optimisation': True,             # Master switch for all optimizations
        'gradient_checkpointing': True,    # For memory efficiency
        'mixed_precision': True,           # Enable mixed precision training
        'gradient_clip_norm': 1.0,         # Clip gradients to this norm
        'lightweight_sparse': True,        # New option for lightweight sparse feature handling
        # DataParallel options
        'use_data_parallel': True,            # Enable DataParallel for training
        'use_data_parallel_inference': False, # Enable DataParallel for inference (typically not needed)
    }
    return config

