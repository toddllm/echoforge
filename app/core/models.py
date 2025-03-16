"""
EchoForge - Neural Models

This module defines the neural network architecture for the text-to-speech models.
It provides model configurations and initialization functions.
"""

import math
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List, Any, Union

import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger("echoforge.core.models")


@dataclass
class ModelArgs:
    """Arguments for model configuration."""
    
    # Model architecture
    backbone_flavor: str = "llama-1B"    # Model size for the text encoder backbone
    decoder_flavor: str = "llama-100M"   # Model size for the audio decoder
    
    # Vocabulary sizes
    text_vocab_size: int = 128_256      # Size of text token vocabulary
    audio_vocab_size: int = 2051        # Size of audio token vocabulary per codebook
    audio_num_codebooks: int = 32       # Number of audio codebooks
    
    # Fixed model parameters
    max_seq_len: int = 1024             # Maximum sequence length
    device: str = "cuda"                # Device for model allocation
    
    def __post_init__(self):
        """Validate and initialize derived parameters."""
        # Map flavor names to configurations
        self.backbone_config = FLAVORS.get(self.backbone_flavor)
        self.decoder_config = FLAVORS.get(self.decoder_flavor)
        
        if not self.backbone_config:
            raise ValueError(f"Unknown backbone flavor: {self.backbone_flavor}")
        if not self.decoder_config:
            raise ValueError(f"Unknown decoder flavor: {self.decoder_flavor}")


class RMSNorm(nn.Module):
    """Root Mean Square Layer Normalization."""
    
    def __init__(self, dim: int, eps: float = 1e-5):
        super().__init__()
        self.eps = eps
        self.weight = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        norm = torch.sqrt(torch.mean(x * x, dim=-1, keepdim=True) + self.eps)
        return x / norm * self.weight


class RotaryEmbedding(nn.Module):
    """Rotary positional embedding for attention."""
    
    def __init__(self, dim: int, max_seq_len: int = 1024):
        super().__init__()
        self.dim = dim
        self.max_seq_len = max_seq_len
        # Initialize fixed rotary embeddings
        self.freqs = self._precompute_freqs_cis(dim, max_seq_len)
    
    def _precompute_freqs_cis(self, dim: int, max_seq_len: int) -> torch.Tensor:
        """Precompute the frequency tensor for complex exponentials."""
        freqs = torch.arange(0, dim, 2).float() / dim
        freqs = 1.0 / (10000 ** freqs)
        
        # Sequence positions
        t = torch.arange(max_seq_len, device=freqs.device)
        freqs = torch.outer(t, freqs)
        
        # Complex exponentials freqs.shape = (seq_len, dim/2)
        freqs_cos = torch.cos(freqs)
        freqs_sin = torch.sin(freqs)
        return torch.cat((freqs_cos, freqs_sin), dim=-1)
    
    def forward(self, x: torch.Tensor, seq_len: int) -> torch.Tensor:
        """Apply rotary embeddings to input tensor."""
        return self.freqs[:seq_len, :]


class Attention(nn.Module):
    """Multi-head attention with rotary embeddings."""
    
    def __init__(
        self,
        dim: int,
        num_heads: int,
        kv_heads: Optional[int] = None,
        dropout: float = 0.0
    ):
        super().__init__()
        self.dim = dim
        self.num_heads = num_heads
        self.kv_heads = kv_heads or num_heads
        self.head_dim = dim // num_heads
        
        # Projection matrices
        self.q_proj = nn.Linear(dim, num_heads * self.head_dim, bias=False)
        self.k_proj = nn.Linear(dim, self.kv_heads * self.head_dim, bias=False)
        self.v_proj = nn.Linear(dim, self.kv_heads * self.head_dim, bias=False)
        self.o_proj = nn.Linear(num_heads * self.head_dim, dim, bias=False)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        rotary_emb: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Forward pass through attention layer."""
        batch_size, seq_len, _ = x.shape
        
        # Project to query, key, values
        q = self.q_proj(x)
        k = self.k_proj(x)
        v = self.v_proj(x)
        
        # Reshape for multi-head attention
        q = q.view(batch_size, seq_len, self.num_heads, self.head_dim)
        k = k.view(batch_size, seq_len, self.kv_heads, self.head_dim)
        v = v.view(batch_size, seq_len, self.kv_heads, self.head_dim)
        
        # Apply rotary embeddings
        # TODO: Implement rotary embedding application logic
        
        # Reshape for attention computation
        q = q.transpose(1, 2)  # (batch, num_heads, seq_len, head_dim)
        k = k.transpose(1, 2)  # (batch, kv_heads, seq_len, head_dim)
        v = v.transpose(1, 2)  # (batch, kv_heads, seq_len, head_dim)
        
        # Attention computation
        attn_weights = torch.matmul(q, k.transpose(-2, -1)) / math.sqrt(self.head_dim)
        
        # Apply attention mask if provided
        if mask is not None:
            attn_weights = attn_weights + mask
        
        # Softmax and dropout
        attn_weights = F.softmax(attn_weights, dim=-1)
        attn_weights = self.dropout(attn_weights)
        
        # Apply attention to values
        attn_output = torch.matmul(attn_weights, v)
        
        # Reshape back
        attn_output = attn_output.transpose(1, 2).contiguous()
        attn_output = attn_output.view(batch_size, seq_len, -1)
        
        # Final projection
        return self.o_proj(attn_output)


class FeedForward(nn.Module):
    """Feed-forward network with SwiGLU activation."""
    
    def __init__(self, dim: int, hidden_dim: int, dropout: float = 0.0):
        super().__init__()
        self.w1 = nn.Linear(dim, hidden_dim, bias=False)
        self.w2 = nn.Linear(hidden_dim, dim, bias=False)
        self.w3 = nn.Linear(dim, hidden_dim, bias=False)
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # SwiGLU activation
        swiglu = F.silu(self.w1(x)) * self.w3(x)
        x = self.w2(swiglu)
        return self.dropout(x)


class TransformerBlock(nn.Module):
    """Transformer block with attention and feed-forward networks."""
    
    def __init__(
        self,
        dim: int,
        num_heads: int,
        kv_heads: Optional[int] = None,
        hidden_dim: Optional[int] = None,
        dropout: float = 0.0
    ):
        super().__init__()
        self.attn_norm = RMSNorm(dim)
        self.attention = Attention(dim, num_heads, kv_heads, dropout)
        
        self.ffn_norm = RMSNorm(dim)
        hidden_dim = hidden_dim or 4 * dim
        self.feed_forward = FeedForward(dim, hidden_dim, dropout)
    
    def forward(
        self,
        x: torch.Tensor,
        rotary_emb: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        # Attention block
        h = x + self.attention(self.attn_norm(x), rotary_emb, mask)
        
        # Feed-forward block
        out = h + self.feed_forward(self.ffn_norm(h))
        return out


class Model(nn.Module):
    """
    Main text-to-speech model architecture.
    Consists of a text backbone encoder and audio decoder.
    """
    
    def __init__(self, args: ModelArgs):
        super().__init__()
        self.args = args
        
        # Text backbone encoder
        self.backbone_embed = nn.Embedding(args.text_vocab_size, args.backbone_config["dim"])
        self.backbone_layers = nn.ModuleList([
            TransformerBlock(
                dim=args.backbone_config["dim"],
                num_heads=args.backbone_config["n_heads"],
                kv_heads=args.backbone_config["kv_heads"],
                hidden_dim=args.backbone_config["hidden_dim"],
                dropout=0.0  # No dropout for inference
            )
            for _ in range(args.backbone_config["n_layers"])
        ])
        self.backbone_norm = RMSNorm(args.backbone_config["dim"])
        
        # Audio decoder
        self.audio_embed = nn.Embedding(args.audio_vocab_size, args.decoder_config["dim"])
        self.decoder_layers = nn.ModuleList([
            TransformerBlock(
                dim=args.decoder_config["dim"],
                num_heads=args.decoder_config["n_heads"],
                kv_heads=args.decoder_config["kv_heads"],
                hidden_dim=args.decoder_config["hidden_dim"],
                dropout=0.0  # No dropout for inference
            )
            for _ in range(args.decoder_config["n_layers"])
        ])
        self.decoder_norm = RMSNorm(args.decoder_config["dim"])
        
        # Projection from backbone to decoder
        self.backbone_to_decoder = nn.Linear(
            args.backbone_config["dim"], 
            args.decoder_config["dim"],
            bias=False
        )
        
        # Audio head for each codebook
        self.audio_head = nn.Linear(
            args.decoder_config["dim"],
            args.audio_vocab_size * args.audio_num_codebooks,
            bias=False
        )
        
        # Rotary embeddings
        self.rotary_backbone = RotaryEmbedding(
            args.backbone_config["dim"] // args.backbone_config["n_heads"],
            args.max_seq_len
        )
        self.rotary_decoder = RotaryEmbedding(
            args.decoder_config["dim"] // args.decoder_config["n_heads"],
            args.max_seq_len
        )
        
        # Cache for inference
        self.reset_caches()
    
    def reset_caches(self):
        """Reset KV caches for inference."""
        self.backbone_cache = None
        self.decoder_cache = None
    
    def forward_backbone(
        self,
        text_tokens: torch.Tensor,
        rotary_emb: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Process text through the backbone encoder."""
        x = self.backbone_embed(text_tokens)
        
        for layer in self.backbone_layers:
            x = layer(x, rotary_emb, mask)
        
        x = self.backbone_norm(x)
        return x
    
    def forward_decoder(
        self,
        audio_tokens: torch.Tensor,
        backbone_features: torch.Tensor,
        rotary_emb: torch.Tensor,
        mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Process audio tokens through the decoder."""
        x = self.audio_embed(audio_tokens)
        
        # Add projected backbone features
        backbone_projection = self.backbone_to_decoder(backbone_features)
        x = x + backbone_projection
        
        for layer in self.decoder_layers:
            x = layer(x, rotary_emb, mask)
        
        x = self.decoder_norm(x)
        return x
    
    def forward(
        self,
        text_tokens: torch.Tensor,
        audio_tokens: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Full forward pass through the model."""
        batch_size, text_seq_len = text_tokens.shape
        
        # Get rotary embeddings
        backbone_rotary = self.rotary_backbone(text_tokens, text_seq_len)
        
        # Process through backbone
        backbone_features = self.forward_backbone(text_tokens, backbone_rotary)
        
        if audio_tokens is not None:
            # Training mode - full forward pass
            audio_seq_len = audio_tokens.shape[1]
            decoder_rotary = self.rotary_decoder(audio_tokens, audio_seq_len)
            
            # Process through decoder
            decoder_features = self.forward_decoder(
                audio_tokens,
                backbone_features,
                decoder_rotary
            )
            
            # Project to audio token predictions
            logits = self.audio_head(decoder_features)
            
            # Reshape logits for multiple codebooks
            logits = logits.view(
                batch_size,
                audio_seq_len,
                self.args.audio_num_codebooks,
                self.args.audio_vocab_size
            )
            
            return logits
        else:
            # Inference mode - just process backbone
            return backbone_features
    
    def generate(
        self,
        text_tokens: torch.Tensor,
        max_audio_len: int = 1024,
        temperature: float = 0.7,
        top_k: int = 50
    ) -> torch.Tensor:
        """Generate audio tokens auto-regressively."""
        batch_size = text_tokens.shape[0]
        
        # Process through backbone
        backbone_features = self.forward(text_tokens)
        
        # Initialize first audio token (special start token)
        audio_tokens = torch.zeros(
            (batch_size, 1),
            dtype=torch.long,
            device=text_tokens.device
        )
        
        # Generate tokens auto-regressively
        for i in range(max_audio_len - 1):
            # Get current audio sequence
            curr_audio_seq = audio_tokens
            
            # Process through decoder
            decoder_rotary = self.rotary_decoder(curr_audio_seq, i + 1)
            decoder_features = self.forward_decoder(
                curr_audio_seq,
                backbone_features,
                decoder_rotary
            )
            
            # Project to audio token predictions
            logits = self.audio_head(decoder_features[:, -1:])
            
            # Reshape logits for multiple codebooks
            logits = logits.view(
                batch_size,
                1,
                self.args.audio_num_codebooks,
                self.args.audio_vocab_size
            )
            
            # Apply temperature and top-k sampling
            next_token_probs = F.softmax(logits / temperature, dim=-1)
            
            # TODO: Implement actual top-k sampling for multiple codebooks
            # For now, just take most likely token
            next_token = torch.argmax(next_token_probs, dim=-1)
            
            # Append to generated sequence
            audio_tokens = torch.cat([audio_tokens, next_token[:, :, 0]], dim=1)
        
        return audio_tokens


# Define model flavor configurations
FLAVORS = {
    "llama-1B": {
        "n_layers": 16,
        "n_heads": 32,
        "kv_heads": 8,
        "dim": 2048,
        "hidden_dim": 8192
    },
    "llama-100M": {
        "n_layers": 4,
        "n_heads": 8,
        "kv_heads": 2,
        "dim": 1024,
        "hidden_dim": 4096
    }
}


def create_model(
    backbone_flavor: str = "llama-1B",
    decoder_flavor: str = "llama-100M",
    audio_vocab_size: int = 2051,
    audio_num_codebooks: int = 32,
    device: str = "cuda"
) -> Model:
    """
    Create a model with the specified configuration.
    
    Args:
        backbone_flavor: The size of the backbone model ("llama-1B" or "llama-100M")
        decoder_flavor: The size of the decoder model ("llama-1B" or "llama-100M")
        audio_vocab_size: Size of the audio vocabulary per codebook
        audio_num_codebooks: Number of audio codebooks
        device: Device to load the model onto
        
    Returns:
        Configured model instance
    """
    args = ModelArgs(
        backbone_flavor=backbone_flavor,
        decoder_flavor=decoder_flavor,
        audio_vocab_size=audio_vocab_size,
        audio_num_codebooks=audio_num_codebooks,
        device=device
    )
    
    model = Model(args)
    logger.info(f"Created model with backbone={backbone_flavor}, decoder={decoder_flavor}")
    logger.info(f"Audio config: vocab_size={audio_vocab_size}, codebooks={audio_num_codebooks}")
    
    return model 