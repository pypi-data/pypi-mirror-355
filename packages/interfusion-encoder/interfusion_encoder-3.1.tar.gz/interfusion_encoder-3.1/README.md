# InterFusion Encoder

InterFusion Encoder is a Python package for training and inference of a cross-encoder model designed to match Users with movies using both textual data and optional sparse features. It utilizes state-of-the-art transformer models and incorporates an attention mechanism and interaction layers to enhance performance.

## **Table of Contents**

- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
  - [Training](#training)
  - [Inference](#inference)
- [Data Preparation](#data-preparation)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

## **Features**

- Supports user and movie features of different lengths.
- Incorporates both bi-encoder and cross-encoder architectures.
- Utilizes hard negative sampling and random negatives for robust training.
- Includes attention mechanisms and interaction layers for improved performance.
- Supports training continuation from saved checkpoints.
- Integrated with Weights & Biases (W&B) for experiment tracking.

## **Installation**

Install the package using pip:

```bash
pip install interfusion_encoder
```

## **Usage**

### **Training**

```python
from interfusion import train_model

# Prepare your data
users = [
    {
        "user_id": "user_001",
        "user_text": "Avid movie enthusiast with a passion for indie films...",
        "user_features": [0.8, 0.7, 0.9]
    },
    # Add more users
]

movies = [
    {
        "movie_id": "movie_001",
        "movie_text": "An engaging drama exploring human relationships...",
        "movie_features": [0.85, 0.75, 0.9, 0.95]
    },
    # Add more movies
]

positive_matches = [
    {
        "user_id": "user_001",
        "movie_id": "movie_001"
    },
    # Add more positive matches
]

# Define your configuration (optional)
user_config = {
    'use_sparse': True,
    'num_epochs': 5,
    'learning_rate': 3e-5,
    'cross_encoder_model_name': 'bert-base-uncased',
    'bi_encoder_model_name': 'bert-base-uncased',
    'wandb_project': 'interfusion_project',
    'wandb_run_name': 'experiment_1',
    # Add or override other configurations as needed
}

# Start training
train_model(users, movies, positive_matches, user_config=user_config)

```

### **Inference**

```python
from interfusion import InterFusionInference

# Initialize inference model
config = {
    'use_sparse': True,
    'cross_encoder_model_name': 'bert-base-uncased',
    'saved_model_path': 'saved_models/interfusion_final.pt',
    'user_feature_size': 3,  # Set according to your data
    'movie_feature_size': 4  # Set according to your data
}
inference_model = InterFusionInference(config=config)

# Prepare user and movie texts and features
user_texts = [
    "Avid movie enthusiast with a passion for indie films...",
    # Add more user texts
]

movie_texts = [
    "An engaging drama exploring human relationships...",
    # Add more movie texts
]

user_features_list = [
    [0.8, 0.7, 0.9],
    # Add more user features
]

movie_features_list = [
    [0.85, 0.75, 0.9, 0.95],
    # Add more movie features
]

# Predict match scores
scores = inference_model.predict(user_texts, movie_texts, user_features_list, movie_features_list)

# Print the results
for user, movie, score in zip(user_texts, movie_texts, scores):
    print(f"User: {user}")
    print(f"Movie: {movie}")
    print(f"Match Score: {score:.4f}\n")

```

## **Data Preparation**

Ensure your data is in the form of lists of dictionaries with the following structure:

**Users:**

```python
[
  {
    "user_id": "user_001",
    "user_text": "Avid movie enthusiast with a passion for indie films and a deep knowledge of film history.",
    "user_features": [0.8, 0.7, 0.9]
  },
  {
    "user_id": "user_002",
    "user_text": "Film critic with a focus on evaluating cinematic techniques and storytelling.",
    "user_features": [0.9, 0.6, 0.85]
  },
  {
    "user_id": "user_003",
    "user_text": "Casual viewer with a love for comedies and light-hearted movies.",
    "user_features": [0.7, 0.8, 0.75]
  }
]

```

**Movies:**

```python
[
  {
    "movie_id": "movie_001",
    "movie_text": "An engaging drama exploring complex human emotions and relationships.",
    "movie_features": [0.85, 0.75, 0.9]
  },
  {
    "movie_id": "movie_002",
    "movie_text": "A thought-provoking documentary that delves into social issues with nuance.",
    "movie_features": [0.9, 0.65, 0.8]
  },
  {
    "movie_id": "movie_003",
    "movie_text": "A light-hearted comedy perfect for a relaxed evening with friends.",
    "movie_features": [0.7, 0.85, 0.8]
  }
]

```

**Positive Matches:**

```python
[
  {
    "user_id": "user_001",
    "movie_id": "movie_001"
  },
  {
    "user_id": "user_002",
    "movie_id": "movie_002"
  },
  {
    "user_id": "user_003",
    "movie_id": "movie_003"
  }
]

```

## **Configuration**

You can customize the model and training parameters by passing a user_config dictionary to the train_model function. Here are some of the configurable parameters:

- random_seed: Random seed for reproducibility.
- max_length: Maximum sequence length for tokenization.
- use_sparse: Whether to use sparse features.
- bi_encoder_model_name: Pre-trained model name for the bi-encoder.
- cross_encoder_model_name: Pre-trained model name for the cross-encoder.
- learning_rate: Learning rate for the optimizer.
- num_epochs: Number of training epochs.
- train_batch_size: Batch size for training.
- wandb_project: W&B project name for logging.
- saved_model_path: Path to save or load the trained model.

## **Contributing**

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## **License**

This project is licensed under the MIT License - see the LICENSE file for details.
