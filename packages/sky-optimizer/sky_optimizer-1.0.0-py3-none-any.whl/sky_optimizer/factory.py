from __future__ import annotations

from torch import nn

from .optimizer import SkyOptimizer


def create_sky_optimizer(
    model: nn.Module,
    lr: float = 3e-4,
    weight_decay: float = 0.01,
    **kwargs,
) -> SkyOptimizer:
    """Create a Sky optimizer with sensible defaults."""
    sky_defaults = {
        "betas": (0.9, 0.95),
        "eps": 1e-8,
        "rho": 0.04,
        "riemannian_geometry": True,
        "natural_gradients": True,
        "quasi_newton_methods": True,
        "information_theory": True,
        "meta_learning": True,
        "bayesian_optimization": True,
        "matrix_factorization": True,
        "sde_optimization": True,
        "entropy_regularization": 1e-4,
        "uncertainty_quantification": True,
        "manifold_optimization": True,
        "fisher_information": True,
        "spectral_normalization": True,
        "low_rank_approximation": 50,
        "conjugate_gradients": True,
        "trust_region_methods": True,
        "line_search_optimization": True,
        "gradient_centralization": True,
        "parameter_scaling": True,
        "layer_adaptation": True,
        "curvature_adaptation": True,
        "gradient_surgery": True,
        "loss_landscape_aware": True,
        "adaptive_momentum": True,
        "robust_numerical": True,
        "warmup_steps": 2000,
        "max_grad_norm": 1.0,
        "cyclical_lr": False,
        "cycle_steps": 1000,
        "cycle_multiplier": 1.0,
        "gradient_variance_adaptation": True,
        "nesterov": True,
        "agc_clip_factor": 0.01,
        "agc_eps": 1e-3,
        "radam_rectify": True,
        "lamb_trust_ratio": True,
        "decoupled_weight_decay": True,
    }

    sky_defaults.update(kwargs)

    return SkyOptimizer(
        model.parameters(),
        lr=lr,
        weight_decay=weight_decay,
        **sky_defaults,
    )