"""
Adaptive Gradient Clipping (AGC)
Clips gradients adaptively relative to parameter magnitudes rather than globally.

Based on "High-Performance Large-Scale Image Recognition Without Normalization" (NFNet paper)
Prevents exploding gradients without hindering learning when parameters are large.
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import math
from typing import Optional, Union
from collections import defaultdict


def adaptive_gradient_clipping(
    parameters,
    clip_factor: float = 0.01,
    eps: float = 1e-3,
    norm_type: float = 2.0,
    per_param_clipping: bool = True,
    adaptive_eps: bool = True,
    gradient_centralization: bool = False
) -> torch.Tensor:
    """
    Apply Adaptive Gradient Clipping to model parameters.
    
    AGC clips gradients based on the ratio of gradient norm to parameter norm,
    allowing larger gradients when parameters are larger.
    
    Args:
        parameters: Model parameters (can be iterator or list)
        clip_factor: Clipping factor (default: 0.01)
        eps: Small constant to avoid division by zero (default: 1e-3)
        norm_type: Type of norm to compute (default: 2.0 for L2 norm)
    
    Returns:
        Total norm of gradients after clipping
    """
    if isinstance(parameters, torch.Tensor):
        parameters = [parameters]
    
    # Convert to list if it's an iterator
    parameters = [p for p in parameters if p.grad is not None]
    
    if len(parameters) == 0:
        return torch.tensor(0.0)
    
    device = parameters[0].grad.device
    
    # Enhanced per-parameter clipping with intelligent adaptations
    total_norm = 0.0
    param_norms = []
    grad_norms = []
    
    # First pass: collect statistics for adaptive adjustments
    for p in parameters:
        if p.grad is None:
            continue
        param_norms.append(p.detach().norm(dtype=torch.float32).item())
        grad_norms.append(p.grad.detach().norm(dtype=torch.float32).item())
    
    # Adaptive epsilon based on parameter statistics
    if adaptive_eps and param_norms:
        median_param_norm = torch.tensor(param_norms).median().item()
        adaptive_epsilon = max(eps, median_param_norm * 1e-6)
    else:
        adaptive_epsilon = eps
    
    # Second pass: apply enhanced clipping
    for i, p in enumerate(parameters):
        if p.grad is None:
            continue
            
        # Apply gradient centralization if enabled
        if gradient_centralization and p.grad.dim() > 1:
            # Center gradients by subtracting their mean
            grad_mean = p.grad.mean(dim=tuple(range(1, p.grad.dim())), keepdim=True)
            p.grad.sub_(grad_mean)
        
        # Compute parameter and gradient norms
        param_norm = p.detach().norm(dtype=torch.float32)
        grad_norm = p.grad.detach().norm(dtype=torch.float32)
        
        if per_param_clipping:
            # Per-parameter adaptive clipping with layer-aware scaling
            # Adjust clip factor based on parameter size relative to others
            if param_norms:
                param_size_ratio = param_norm.item() / (sum(param_norms) / len(param_norms) + 1e-8)
                # Larger parameters can handle relatively larger gradients
                adaptive_clip_factor = clip_factor * (1.0 + 0.1 * math.log(max(1.0, param_size_ratio)))
            else:
                adaptive_clip_factor = clip_factor
            
            # Compute maximum allowed gradient norm
            max_norm = param_norm * adaptive_clip_factor
            
            # Dynamic epsilon adjustment
            dynamic_eps = max(adaptive_epsilon, param_norm * 1e-6)
            max_norm = torch.clamp(max_norm, min=dynamic_eps)
            
            # Smooth clipping with cosine transition
            if grad_norm > max_norm:
                # Smooth clipping factor using cosine transition
                excess_ratio = (grad_norm - max_norm) / (max_norm + 1e-8)
                smooth_factor = 0.5 * (1.0 + torch.cos(torch.pi * torch.clamp(excess_ratio, 0, 1)))
                clipping_factor = max_norm / (grad_norm + 1e-8) * (1.0 - smooth_factor) + smooth_factor
                
                # Apply smooth clipping
                p.grad.detach().mul_(clipping_factor)
        else:
            # Global clipping fallback
            max_norm = param_norm * clip_factor
            max_norm = torch.clamp(max_norm, min=adaptive_epsilon)
            
            if grad_norm > max_norm:
                clipping_factor = max_norm / (grad_norm + 1e-8)
                p.grad.detach().mul_(clipping_factor)
        
        # Accumulate total norm (after clipping)
        total_norm += p.grad.detach().norm(dtype=torch.float32) ** norm_type
    
    # Return total norm
    total_norm = total_norm ** (1.0 / norm_type)
    return total_norm


class AGCWrapper:
    """
    Enhanced wrapper class to integrate AGC with any optimizer.
    Includes layer-wise clipping, adaptive thresholds, and gradient centralization.
    
    Usage:
        optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)
        agc_optimizer = AGCWrapper(optimizer, clip_factor=0.01, layerwise_adaptation=True)
        
        # In training loop:
        agc_optimizer.step()
    """
    
    def __init__(
        self, 
        optimizer, 
        clip_factor: float = 0.01, 
        eps: float = 1e-3,
        norm_type: float = 2.0,
        layerwise_adaptation: bool = True,
        gradient_centralization: bool = True,
        adaptive_clipping: bool = True,
        warmup_steps: int = 1000
    ):
        """
        Initialize enhanced AGC wrapper.
        
        Args:
            optimizer: Base optimizer to wrap
            clip_factor: Base AGC clipping factor (default: 0.01)
            eps: Small constant to avoid division by zero (default: 1e-3)
            norm_type: Type of norm to compute (default: 2.0)
            layerwise_adaptation: Enable layer-specific clipping adaptation
            gradient_centralization: Enable gradient centralization
            adaptive_clipping: Enable adaptive clipping thresholds
            warmup_steps: Steps for clipping factor warmup
        """
        self.optimizer = optimizer
        self.clip_factor = clip_factor
        self.eps = eps
        self.norm_type = norm_type
        self.layerwise_adaptation = layerwise_adaptation
        self.gradient_centralization = gradient_centralization
        self.adaptive_clipping = adaptive_clipping
        self.warmup_steps = warmup_steps
        
        # Enhanced state tracking
        self.step_count = 0
        self.layer_clip_history = defaultdict(list)
        self.layer_gradient_scales = defaultdict(float)
        self.adaptive_clip_factors = {}
    
    def step(self, closure=None):
        """
        Perform optimizer step with enhanced AGC.
        
        Args:
            closure: Optional closure for optimizer
        """
        self.step_count += 1
        
        if self.layerwise_adaptation:
            # Apply layer-wise adaptive clipping
            self._apply_layerwise_agc()
        else:
            # Apply standard AGC to all parameters
            all_params = []
            for group in self.optimizer.param_groups:
                all_params.extend([p for p in group['params'] if p.grad is not None])
            
            # Get current clip factor with warmup
            current_clip_factor = self._get_adaptive_clip_factor()
            
            grad_norm = adaptive_gradient_clipping(
                all_params,
                clip_factor=current_clip_factor,
                eps=self.eps,
                norm_type=self.norm_type,
                gradient_centralization=self.gradient_centralization,
                adaptive_eps=self.adaptive_clipping
            )
        
        # Perform optimizer step
        return self.optimizer.step(closure)
    
    def _get_adaptive_clip_factor(self, layer_name=None):
        """Get adaptive clip factor with warmup and layer-specific adjustments."""
        base_factor = self.clip_factor
        
        # Apply warmup
        if self.step_count < self.warmup_steps:
            warmup_factor = self.step_count / self.warmup_steps
            base_factor = base_factor * (0.1 + 0.9 * warmup_factor)
        
        # Layer-specific adaptation
        if layer_name and layer_name in self.adaptive_clip_factors:
            base_factor *= self.adaptive_clip_factors[layer_name]
        
        return base_factor
    
    def _apply_layerwise_agc(self):
        """Apply layer-wise adaptive gradient clipping."""
        # Group parameters by layer
        layer_params = defaultdict(list)
        
        for group in self.optimizer.param_groups:
            for p in group['params']:
                if p.grad is not None:
                    # Simple layer identification by parameter shape
                    layer_key = f"layer_{len(p.shape)}_{p.numel()//1000}k"
                    layer_params[layer_key].append(p)
        
        # Apply AGC to each layer separately
        for layer_name, params in layer_params.items():
            if params:
                # Get layer-specific clip factor
                layer_clip_factor = self._get_adaptive_clip_factor(layer_name)
                
                # Update layer-specific adaptation
                self._update_layer_adaptation(layer_name, params)
                
                # Apply AGC to this layer
                grad_norm = adaptive_gradient_clipping(
                    params,
                    clip_factor=layer_clip_factor,
                    eps=self.eps,
                    norm_type=self.norm_type,
                    gradient_centralization=self.gradient_centralization,
                    adaptive_eps=self.adaptive_clipping
                )
    
    def _update_layer_adaptation(self, layer_name, params):
        """Update layer-specific clipping adaptation based on gradient history."""
        if not self.adaptive_clipping:
            return
            
        # Compute layer gradient statistics
        grad_norms = []
        param_norms = []
        
        for p in params:
            if p.grad is not None:
                grad_norms.append(p.grad.detach().norm().item())
                param_norms.append(p.detach().norm().item())
        
        if grad_norms and param_norms:
            avg_grad_norm = sum(grad_norms) / len(grad_norms)
            avg_param_norm = sum(param_norms) / len(param_norms)
            
            # Track gradient-to-parameter ratio
            ratio = avg_grad_norm / (avg_param_norm + 1e-8)
            self.layer_clip_history[layer_name].append(ratio)
            
            # Keep only recent history
            if len(self.layer_clip_history[layer_name]) > 100:
                self.layer_clip_history[layer_name] = self.layer_clip_history[layer_name][-50:]
            
            # Adapt clipping factor based on history
            if len(self.layer_clip_history[layer_name]) > 10:
                recent_ratios = self.layer_clip_history[layer_name][-10:]
                ratio_trend = sum(recent_ratios) / len(recent_ratios)
                
                # Adjust clip factor: high ratios need stronger clipping
                adaptation_factor = 1.0 / (1.0 + ratio_trend * 0.1)
                
                # Smooth update
                current_factor = self.adaptive_clip_factors.get(layer_name, 1.0)
                self.adaptive_clip_factors[layer_name] = 0.9 * current_factor + 0.1 * adaptation_factor
    
    def zero_grad(self, set_to_none=False):
        """Zero gradients."""
        return self.optimizer.zero_grad(set_to_none)
    
    def state_dict(self):
        """Get optimizer state dict."""
        return self.optimizer.state_dict()
    
    def load_state_dict(self, state_dict):
        """Load optimizer state dict."""
        return self.optimizer.load_state_dict(state_dict)
    
    @property
    def param_groups(self):
        """Access parameter groups."""
        return self.optimizer.param_groups
    
    @property
    def defaults(self):
        """Access defaults."""
        return self.optimizer.defaults
    
    def __getattr__(self, name):
        """Delegate unknown attributes to wrapped optimizer."""
        return getattr(self.optimizer, name)


def apply_agc_to_model(
    model: nn.Module,
    clip_factor: float = 0.01,
    eps: float = 1e-3,
    exclude_layers: Optional[list] = None
) -> torch.Tensor:
    """
    Apply AGC to specific model layers, with option to exclude certain layers.
    
    Args:
        model: PyTorch model
        clip_factor: AGC clipping factor
        eps: Small constant to avoid division by zero
        exclude_layers: List of layer names/types to exclude from AGC
    
    Returns:
        Total gradient norm after clipping
    """
    if exclude_layers is None:
        exclude_layers = []
    
    # Collect parameters to clip
    params_to_clip = []
    
    for name, param in model.named_parameters():
        if param.grad is None:
            continue
            
        # Check if this parameter should be excluded
        should_exclude = False
        for exclude_pattern in exclude_layers:
            if exclude_pattern in name:
                should_exclude = True
                break
        
        if not should_exclude:
            params_to_clip.append(param)
    
    # Apply AGC
    return adaptive_gradient_clipping(
        params_to_clip,
        clip_factor=clip_factor,
        eps=eps
    )


# Convenience function for common use cases
def create_agc_optimizer(base_optimizer, clip_factor: float = 0.01):
    """
    Create an AGC-wrapped optimizer with recommended settings.
    
    Args:
        base_optimizer: Base optimizer (e.g., AdamW, SGD)
        clip_factor: AGC clipping factor (0.01 is good for most cases)
    
    Returns:
        AGC-wrapped optimizer
    """
    return AGCWrapper(
        base_optimizer,
        clip_factor=clip_factor,
        eps=1e-3,
        norm_type=2.0
    )