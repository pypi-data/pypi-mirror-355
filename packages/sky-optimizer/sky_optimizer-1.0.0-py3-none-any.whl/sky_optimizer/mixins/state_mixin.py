# Utility mixin for SkyOptimizer state management
import math
import torch
import numpy as np
from collections import deque, defaultdict


class SkyStateMixin:
    def _initialize_revolutionary_state(self, state, param, group):
        """Initialize parameter state with revolutionary mathematical tracking."""
        state['step'] = 0
        # Use memory-efficient tensor initialization
        state['exp_avg'] = torch.zeros_like(param, memory_format=torch.preserve_format)
        state['exp_avg_sq'] = torch.zeros_like(param, memory_format=torch.preserve_format)
        
        if group['amsgrad']:
            state['max_exp_avg_sq'] = torch.zeros_like(param, memory_format=torch.preserve_format)
        
        # Improved initialization for numerical stability
        state['hessian_diag'] = torch.full_like(param, 1e-4, memory_format=torch.preserve_format)
        state['prev_grad'] = None
        state['prev_param'] = param.detach().clone()
        
        # Adaptive metric tensor size based on parameter size
        metric_size = min(param.numel(), 100) if param.numel() > 1000 else min(param.numel(), 50)
        state['metric_tensor'] = torch.eye(metric_size, dtype=param.dtype, device=param.device)
        
        # Reduced Christoffel symbols for efficiency
        christoffel_size = min(param.numel(), 20) if param.numel() > 100 else min(param.numel(), 10)
        state['christoffel_symbols'] = torch.zeros(christoffel_size, dtype=param.dtype, device=param.device)
        
        # Better initialization for numerical stability
        state['fisher_diag'] = torch.full_like(param, 1e-4)
        state['natural_grad'] = torch.zeros_like(param)
        
        # Adaptive history sizes based on parameter count
        history_size = min(20, max(5, param.numel() // 1000))
        state['s_history'] = deque(maxlen=history_size)
        state['y_history'] = deque(maxlen=history_size)
        state['rho_history'] = deque(maxlen=history_size)
        
        state['gamma'] = 1.0
        state['entropy_estimate'] = 0.0
        state['mutual_information'] = 0.0
        state['kl_divergence'] = 0.0
        
        # Reduced precision for uncertainty estimates to save memory
        if group.get('uncertainty_quantification', True):
            state['parameter_uncertainty'] = torch.full_like(param, 0.1)
            state['gradient_uncertainty'] = torch.full_like(param, 0.1)
        
        state['predictive_variance'] = 0.0
        state['grad_var_ema'] = 0.0
        # Optimized matrix factorization initialization
        if group['matrix_factorization'] and param.dim() >= 2 and param.numel() <= 10000:
            try:
                # Use more efficient SVD for initialization
                param_2d = param.detach().view(param.shape[0], -1)
                if min(param_2d.shape) > 1:
                    u, s, vh = torch.linalg.svd(param_2d, full_matrices=False)
                    rank = min(group['low_rank_approximation'], min(param_2d.shape), 50)
                    state['low_rank_u'] = u[:, :rank].contiguous().clone()
                    state['low_rank_s'] = s[:rank].clone()
                    state['low_rank_v'] = vh[:rank, :].contiguous().clone()
            except Exception:
                # Fallback to identity initialization if SVD fails
                rank = min(group['low_rank_approximation'], min(param.shape), 20)
                state['low_rank_u'] = torch.eye(param.shape[0], rank, device=param.device, dtype=param.dtype)
                state['low_rank_s'] = torch.ones(rank, device=param.device, dtype=param.dtype)
                state['low_rank_v'] = torch.eye(rank, param.shape[-1], device=param.device, dtype=param.dtype)
        state['noise_scale'] = 0.01
        state['drift_term'] = torch.zeros_like(param)
        state['diffusion_term'] = torch.ones_like(param) * 0.01
        state['trust_radius'] = 1.0
        state['trust_ratio'] = 1.0
        state['line_search_alpha'] = 1.0
        state['conjugate_direction'] = torch.zeros_like(param)
        state['conjugate_beta'] = 0.0
        state['curvature_ema'] = 0.0
        state['condition_number'] = 1.0
        state['spectral_norm'] = 1.0

    def _update_revolutionary_state(self, param, grad, state, group):
        """Update revolutionary mathematical state tracking."""
        state['prev_grad'] = grad.clone()
        state['prev_param'] = param.detach().clone()
        if 'prev_grad' in state and len(state.get('y_history', [])) > 0:
            y_recent = state['y_history'][-1] if state['y_history'] else grad.flatten()
            curvature_estimate = torch.dot(y_recent, grad.flatten()).item() / (
                y_recent.norm().item() * grad.norm().item() + 1e-8
            )
            state['curvature_ema'] = 0.95 * state.get('curvature_ema', 0.0) + 0.05 * abs(curvature_estimate)
        if group['uncertainty_quantification']:
            if 'parameter_uncertainty' in state:
                grad_squared = grad ** 2
                uncertainty_update = 0.01 * grad_squared
                state['parameter_uncertainty'] = (
                    0.99 * state['parameter_uncertainty'] + 0.01 * uncertainty_update
                )
        if group['information_theory']:
            param_flat = param.flatten()
            grad_flat = grad.flatten()
            if param_flat.numel() == grad_flat.numel() and param_flat.numel() > 10:
                param_normalized = (param_flat - param_flat.mean()) / (param_flat.std() + 1e-8)
                grad_normalized = (grad_flat - grad_flat.mean()) / (grad_flat.std() + 1e-8)
                correlation = torch.dot(param_normalized, grad_normalized) / param_flat.numel()
                mutual_info_approx = -0.5 * torch.log(1 - correlation ** 2 + 1e-8).item()
                state['mutual_information'] = 0.9 * state.get('mutual_information', 0.0) + 0.1 * mutual_info_approx
        if group['matrix_factorization'] and param.dim() >= 2 and 'low_rank_u' in state:
            if self.global_step % 100 == 0:
                try:
                    u, s, v = torch.svd(param.detach())
                    rank = min(group['low_rank_approximation'], min(param.shape))
                    state['low_rank_u'] = u[:, :rank].clone()
                    state['low_rank_s'] = s[:rank].clone()
                    state['low_rank_v'] = v[:, :rank].clone()
                except Exception:
                    pass
        if group['sde_optimization']:
            grad_flat = grad.flatten()
            if grad_flat.numel() > 1:
                grad_var = torch.var(grad_flat, unbiased=False).item()
            else:
                grad_var = 0.0
            state['diffusion_term'] = (
                0.95 * state.get('diffusion_term', torch.ones_like(param) * 0.01)
                + 0.05 * grad_var * torch.ones_like(param)
            )
        
        # Compute gradient variance safely
        grad_flat = grad.detach().flatten()
        if grad_flat.numel() > 1:
            grad_var = torch.var(grad_flat, unbiased=False).item()
        else:
            grad_var = 0.0
        state['grad_var_ema'] = 0.95 * state.get('grad_var_ema', 0.0) + 0.05 * grad_var

    def _update_mathematical_approximations(self):
        """Update comprehensive mathematical approximations with improved efficiency."""
        for group in self.param_groups:
            for p in group['params']:
                if p.grad is None or len(self.state[p]) == 0:
                    continue
                    
                state = self.state[p]
                current_grad = p.grad.detach()
                
                if state['prev_grad'] is not None:
                    # More numerically stable approximations
                    grad_diff = current_grad - state['prev_grad']
                    param_diff = state.get('prev_param', p.detach()) - p.detach()
                    
                    # Improved numerical stability checks
                    param_norm = param_diff.norm().item()
                    grad_norm = grad_diff.norm().item()
                    
                    if param_norm > 1e-8 and grad_norm > 1e-8:
                        # Clamped BFGS approximation for stability
                        bfgs_approx = torch.clamp(grad_diff.abs() / (param_diff.abs() + 1e-6), min=1e-8, max=1e6)
                    else:
                        bfgs_approx = grad_diff.abs()
                    
                    # Improved Fisher approximation with regularization
                    fisher_approx = current_grad ** 2 + 1e-8
                    
                    # More stable Gauss-Newton approximation
                    gauss_newton_approx = grad_diff.abs() * torch.clamp(torch.sign(current_grad), min=-1, max=1)
                    
                    # Natural gradient scaling with improved conditioning
                    if 'fisher_diag' in state:
                        natural_scaling = torch.clamp(state['fisher_diag'], min=1e-8).sqrt()
                    else:
                        natural_scaling = torch.ones_like(grad_diff)
                    # Adaptive weighting based on problem characteristics
                    weights = [0.25, 0.25, 0.25, 0.25]
                    
                    # Dynamic weight adjustment based on gradient properties
                    grad_flat = current_grad.flatten()
                    if grad_flat.numel() > 1:
                        grad_var = torch.var(grad_flat, unbiased=False).item()
                    else:
                        grad_var = 0.0
                    
                    if grad_var > 1.0:  # High variance - favor robust methods
                        weights[0] *= 1.2  # BFGS
                        weights[1] *= 0.8  # Fisher
                    elif grad_var < 0.1:  # Low variance - favor precise methods
                        weights[1] *= 1.2  # Fisher
                        weights[0] *= 0.8  # BFGS
                    
                    if group['natural_gradients']:
                        weights[3] += 0.1
                        weights[0] -= 0.05
                        weights[1] -= 0.05
                    if group['fisher_information']:
                        weights[1] += 0.1
                        weights[0] -= 0.05
                        weights[2] -= 0.05
                    
                    # Normalize weights
                    weight_sum = sum(weights)
                    weights = [w / weight_sum for w in weights]
                    
                    # Improved combination with numerical stability
                    combined_hessian = (
                        weights[0] * bfgs_approx
                        + weights[1] * fisher_approx
                        + weights[2] * gauss_newton_approx
                        + weights[3] * natural_scaling * grad_diff.abs()
                    )
                    
                    # Clamp combined hessian for numerical stability
                    combined_hessian = torch.clamp(combined_hessian, min=1e-8, max=1e6)
                    
                    # Improved EMA update with adaptive rate
                    hessian_ema = group['hessian_ema']
                    condition_est = combined_hessian.max() / (combined_hessian.min() + 1e-8)
                    if condition_est > 1e6:  # Poor conditioning - use more conservative update
                        hessian_ema = min(0.99, hessian_ema * 1.1)
                    
                    state['hessian_diag'] = hessian_ema * state['hessian_diag'] + (1 - hessian_ema) * combined_hessian
                    if group['riemannian_geometry'] and 'metric_tensor' in state:
                        if self.global_step % 50 == 0:
                            self._update_riemannian_metric(p, state, group)
                    if group['fisher_information']:
                        fisher_update = current_grad ** 2
                        if 'fisher_diag' in state:
                            state['fisher_diag'] = 0.95 * state['fisher_diag'] + 0.05 * fisher_update

    def _update_riemannian_metric(self, param, state, group):
        """Update Riemannian metric tensor for manifold optimization."""
        if param.numel() > 10000:
            return
        grad_flat = param.grad.detach().flatten()
        metric_size = state['metric_tensor'].shape[0]
        if grad_flat.numel() >= metric_size:
            grad_sample = grad_flat[:metric_size]
            metric_update = torch.outer(grad_sample, grad_sample)
            metric_update = metric_update / (metric_update.trace() + 1e-8)
            state['metric_tensor'] = 0.95 * state['metric_tensor'] + 0.05 * metric_update
            eigenvals, eigenvecs = torch.linalg.eigh(state['metric_tensor'])
            eigenvals = torch.clamp(eigenvals, min=1e-6)
            state['metric_tensor'] = eigenvecs @ torch.diag(eigenvals) @ eigenvecs.t()