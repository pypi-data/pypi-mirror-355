#!/usr/bin/env python3
"""
Standalone model loader for Mammo-CLIP inference
Avoids importing the full breastclip package to prevent dependency issues
"""

import os
import sys
import torch
import torch.nn as nn
import numpy as np
from typing import Dict
from transformers.tokenization_utils import PreTrainedTokenizer

# Add codebase path for importing specific modules
codebase_path = os.path.join(os.path.dirname(__file__), '..', 'codebase')
if codebase_path not in sys.path:
    sys.path.insert(0, codebase_path)


class MammoClipModel(nn.Module):
    """Standalone MammoClip model for inference"""
    
    def __init__(self, model_config: Dict, loss_config: Dict, tokenizer: PreTrainedTokenizer = None):
        super().__init__()
        self.tokenizer = tokenizer
        self.model_config = model_config
        self.loss_config = loss_config
        
        # Import modules only when needed
        self._load_components()
        
        self.text_pooling = model_config["text_encoder"]["pooling"]
        self.projection = "projection_head" in model_config

        if self.projection:
            self.image_projection = self._load_projection_head(
                embedding_dim=self.image_encoder.out_dim, 
                config_projection_head=model_config["projection_head"]
            )
            self.text_projection = self._load_projection_head(
                embedding_dim=self.text_encoder.out_dim, 
                config_projection_head=model_config["projection_head"]
            )

        self.temperature = model_config["temperature"] if "temperature" in model_config else None
        if self.temperature:
            self.logit_scale = nn.Parameter(torch.ones([]) * np.log(1 / self.temperature))
        else:
            self.logit_scale = torch.tensor(1, dtype=torch.float32)

    def _load_components(self):
        """Load image and text encoders"""
        self.image_encoder = self._load_image_encoder(self.model_config["image_encoder"])
        self.text_encoder = self._load_text_encoder(
            self.model_config["text_encoder"], 
            vocab_size=self.tokenizer.vocab_size
        )

    def _load_image_encoder(self, config_image_encoder: Dict):
        """Load image encoder based on config"""
        if (config_image_encoder["source"].lower() == "cnn" and 
            "tf_efficientnet_b5_ns" in config_image_encoder["name"].lower()):
            from .standalone_models import EfficientNet_Mammo
            return EfficientNet_Mammo(name=config_image_encoder["name"])
        elif config_image_encoder["source"].lower() == "huggingface":
            from .standalone_models import HuggingfaceImageEncoder
            cache_dir = config_image_encoder.get("cache_dir", "~/.cache/huggingface/hub")
            gradient_checkpointing = config_image_encoder.get("gradient_checkpointing", False)
            model_type = config_image_encoder.get("model_type", "vit")
            
            return HuggingfaceImageEncoder(
                name=config_image_encoder["name"],
                pretrained=config_image_encoder["pretrained"],
                gradient_checkpointing=gradient_checkpointing,
                cache_dir=cache_dir,
                model_type=model_type,
                local_files_only=os.path.exists(
                    os.path.join(cache_dir, f'models--{config_image_encoder["name"].replace("/", "--")}')
                ),
            )
        else:
            raise KeyError(f"Not supported image encoder: {config_image_encoder}")

    def _load_text_encoder(self, config_text_encoder: Dict, vocab_size: int):
        """Load text encoder based on config"""
        if config_text_encoder["source"].lower() == "huggingface":
            from .standalone_models import HuggingfaceTextEncoder
            cache_dir = config_text_encoder["cache_dir"]
            gradient_checkpointing = config_text_encoder["gradient_checkpointing"]
            
            return HuggingfaceTextEncoder(
                name=config_text_encoder["name"],
                vocab_size=vocab_size,
                pretrained=config_text_encoder["pretrained"],
                gradient_checkpointing=gradient_checkpointing,
                cache_dir=cache_dir,
                local_files_only=os.path.exists(
                    os.path.join(cache_dir, f'models--{config_text_encoder["name"].replace("/", "--")}')
                ),
                trust_remote_code=config_text_encoder["trust_remote_code"],
            )
        else:
            raise KeyError(f"Not supported text encoder: {config_text_encoder}")

    def _load_projection_head(self, embedding_dim: int, config_projection_head: Dict):
        """Load projection head based on config"""
        if config_projection_head["name"].lower() == "mlp":
            from .standalone_models import MLPProjectionHead
            return MLPProjectionHead(
                embedding_dim=embedding_dim, 
                projection_dim=config_projection_head["proj_dim"],
                dropout=config_projection_head["dropout"]
            )
        elif config_projection_head["name"].lower() == "linear":
            from .standalone_models import LinearProjectionHead
            return LinearProjectionHead(
                embedding_dim=embedding_dim,
                projection_dim=config_projection_head["proj_dim"]
            )
        else:
            raise KeyError(f"Not supported projection head: {config_projection_head}")

    def encode_image(self, image):
        """Encode image to features"""
        image_features = self.image_encoder(image)

        if self.model_config["image_encoder"]["model_type"].lower() == "cnn":
            return image_features
        else:
            # get [CLS] token for global representation (only for vision transformer)
            global_features = image_features[:, 0]
            return global_features

    def encode_text(self, text_tokens):
        """Encode text tokens to features"""
        text_features = self.text_encoder(text_tokens)

        if self.text_pooling == "eos":
            # take features from the eot embedding (eos_token is the highest number in each sequence)
            eos_token_indices = text_tokens["attention_mask"].sum(dim=-1) - 1
            text_features = text_features[torch.arange(text_features.shape[0]), eos_token_indices]
        elif self.text_pooling == "bos":
            text_features = text_features[:, 0]
        elif self.text_pooling == "mean":
            input_mask_expanded = text_tokens["attention_mask"].unsqueeze(axis=-1).expand(text_features.size()).float()
            text_features = torch.sum(text_features * input_mask_expanded, axis=1) / torch.clamp(
                input_mask_expanded.sum(axis=1), min=1e-9)
        else:
            raise NotImplementedError("Not supported pooling method : %s", self.text_pooling)

        return text_features


def build_mammo_clip_model(model_config: Dict, loss_config: Dict, tokenizer: PreTrainedTokenizer = None):
    """Build MammoClip model"""
    if model_config["name"].lower() == "clip_custom":
        return MammoClipModel(model_config, loss_config, tokenizer)
    else:
        raise KeyError(f"Not supported model: {model_config['name']}") 