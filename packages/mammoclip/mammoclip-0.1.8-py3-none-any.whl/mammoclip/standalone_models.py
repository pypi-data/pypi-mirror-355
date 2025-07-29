#!/usr/bin/env python3
"""
Standalone models for mammoclip package to avoid dependency issues
"""

import timm
import torch
import torch.nn.functional as F
from torch import nn
from torch.nn import Parameter
from transformers import AutoConfig, AutoModel, BertModel, SwinModel, ViTModel


def gem(x, p=3, eps=1e-6):
    return F.avg_pool2d(x.clamp(min=eps).pow(p), (x.size(-2), x.size(-1))).pow(1.0 / p)


class GeM(nn.Module):
    def __init__(self, p=3, eps=1e-6, p_trainable=False):
        super(GeM, self).__init__()
        if p_trainable:
            self.p = Parameter(torch.ones(1) * p)
        else:
            self.p = p
        self.eps = eps

    def forward(self, x):
        ret = gem(x, p=self.p, eps=self.eps)
        return ret

    def __repr__(self):
        if isinstance(self.p, int):
            return (
                    self.__class__.__name__
                    + "("
                    + "p="
                    + "{:.4f}".format(self.p)
                    + ", "
                    + "eps="
                    + str(self.eps)
                    + ")"
            )
        else:
            return (
                    self.__class__.__name__
                    + "("
                    + "p="
                    + "{:.4f}".format(self.p.data.tolist()[0])
                    + ", "
                    + "eps="
                    + str(self.eps)
                    + ")"
            )


class EfficientNet_Mammo(nn.Module):
    def __init__(self, name: str = "tf_efficientnet_b5_ns", pretrained=False, in_chans=1, p=3, p_trainable=False,
                 eps=1e-6, get_features=False):
        super().__init__()
        # Clean the model name - remove suffixes that timm doesn't recognize
        clean_name = name.replace("-detect", "").replace("-cls", "")
        model = timm.create_model(clean_name, pretrained=pretrained, in_chans=in_chans)
        clsf = model.default_cfg['classifier']
        n_features = model._modules[clsf].in_features
        model._modules[clsf] = nn.Identity()
        self.out_dim = n_features

        self.fc = nn.Linear(n_features, 1)
        self.model = model
        self.get_features = get_features
        self.pool = nn.Sequential(
            GeM(p=p, eps=eps, p_trainable=p_trainable),
            nn.Flatten()
        )

    def forward(self, x):
        x = self.model.forward_features(x)
        x = self.pool(x)
        return x


class HuggingfaceTextEncoder(nn.Module):
    def __init__(
        self,
        name: str = "bert-base-uncased",
        vocab_size: int = None,
        pretrained: bool = True,
        gradient_checkpointing: bool = False,
        cache_dir: str = "~/.cache/huggingface/hub",
        local_files_only: bool = False,
        trust_remote_code: bool = False,
    ):
        super().__init__()
        cache_dir = None
        if pretrained:
            self.text_encoder = AutoModel.from_pretrained(
                name,
                ignore_mismatched_sizes=True,
                local_files_only=local_files_only,
                trust_remote_code=trust_remote_code,
            )
        else:
            # initializing with a config file does not load the weights associated with the model
            model_config = AutoConfig.from_pretrained(
                name,
                # vocab_size=vocab_size,
                ignore_mismatched_sizes=True,
                local_files_only=local_files_only,
                trust_remote_code=trust_remote_code,
            )
            if type(model_config).__name__ == "BertConfig":
                self.text_encoder = BertModel(model_config)
            else:
                # TODO: add text models if needed
                raise NotImplementedError(f"Not support training from scratch : {type(model_config).__name__}")

        if gradient_checkpointing and self.text_encoder.supports_gradient_checkpointing:
            self.text_encoder.gradient_checkpointing_enable()

        self.out_dim = self.text_encoder.config.hidden_size

    def forward(self, x):
        output = self.text_encoder(**x)
        return output["last_hidden_state"]  # (batch, seq_len, hidden_size)


class MLPProjectionHead(nn.Module):
    def __init__(self, embedding_dim, projection_dim, dropout):
        super().__init__()
        self.projection = nn.Linear(embedding_dim, projection_dim)
        self.gelu = nn.GELU()
        self.fc = nn.Linear(projection_dim, projection_dim)
        self.dropout = nn.Dropout(dropout)
        self.layer_norm = nn.LayerNorm(projection_dim)

    def forward(self, x):
        projected = self.projection(x)
        x = self.gelu(projected)
        x = self.fc(x)
        x = self.dropout(x)
        x = x + projected
        x = self.layer_norm(x)
        return x


class LinearProjectionHead(nn.Module):
    def __init__(self, embedding_dim, projection_dim):
        super().__init__()
        self.projection = nn.Linear(embedding_dim, projection_dim)
        
    def forward(self, x):
        return self.projection(x)


class HuggingfaceImageEncoder(nn.Module):
    def __init__(
            self,
            name: str = "google/vit-base-patch16-224",
            pretrained: bool = True,
            gradient_checkpointing: bool = False,
            cache_dir: str = "~/.cache/huggingface/hub",
            model_type: str = "vit",
            local_files_only: bool = False,
    ):
        super().__init__()
        self.model_type = model_type
        if pretrained:
            if self.model_type == "swin":
                self.image_encoder = SwinModel.from_pretrained(name)
            else:
                self.image_encoder = AutoModel.from_pretrained(
                    name, add_pooling_layer=False, cache_dir=cache_dir, local_files_only=local_files_only
                )
        else:
            # initializing with a config file does not load the weights associated with the model
            model_config = AutoConfig.from_pretrained(name, cache_dir=cache_dir, local_files_only=local_files_only)
            if type(model_config).__name__ == "ViTConfig":
                self.image_encoder = ViTModel(model_config, add_pooling_layer=False)
            else:
                # TODO: add vision models if needed
                raise NotImplementedError(f"Not support training from scratch : {type(model_config).__name__}")

        if gradient_checkpointing and self.image_encoder.supports_gradient_checkpointing:
            self.image_encoder.gradient_checkpointing_enable()

        self.out_dim = self.image_encoder.config.hidden_size

    def forward(self, image):
        if self.model_type == "vit":
            output = self.image_encoder(pixel_values=image, interpolate_pos_encoding=True)
        elif self.model_type == "swin":
            output = self.image_encoder(pixel_values=image)
        return output["last_hidden_state"]  # (batch, seq_len, hidden_size) 