import math
import torch
import torch.nn.functional as F
from collections import deque

from ..utils.agc import adaptive_gradient_clipping


class SkyGradientsMixin:
    def _apply_gradient_centralization(self, grads):
        centralized_grads = []
        for grad in grads:
            if grad.dim() > 1:
                grad_mean = grad.mean(dim=tuple(range(1, grad.dim())), keepdim=True)
                centralized_grad = grad - grad_mean
                centralized_grads.append(centralized_grad)
            else:
                centralized_grads.append(grad)
        return centralized_grads

    def _clip_gradients(self, params, grads, group):
        """Apply adaptive or norm-based gradient clipping."""
        clip_factor = group.get("agc_clip_factor", 0.0)
        if clip_factor > 0:
            adaptive_gradient_clipping(
                params,
                clip_factor=clip_factor,
                eps=group.get("agc_eps", 1e-3),
                gradient_centralization=False,
            )
            return [p.grad if p.grad is not None else g for p, g in zip(params, grads)]

        max_norm = group.get("max_grad_norm", 0.0)
        if max_norm > 0:
            total_norm = 0.0
            for g in grads:
                total_norm += g.norm().item() ** 2
            total_norm = math.sqrt(total_norm)
            if total_norm > max_norm:
                scale = max_norm / (total_norm + 1e-6)
                return [g * scale for g in grads]
        return grads

    def _apply_advanced_gradient_surgery(self, params, grads, group):
        if len(grads) < 2:
            return grads
        
        # Pre-compute all flattened gradients for efficiency
        grad_flats = [g.flatten() for g in grads if g.numel() > 0]
        if len(grad_flats) < 2:
            return grads
        
        # Vectorized conflict detection for efficiency
        surgered_grads = []
        conflict_threshold = 0.1
        
        # Stack gradients with same size for vectorized operations
        size_groups = {}
        for i, grad_flat in enumerate(grad_flats):
            size = grad_flat.numel()
            if size not in size_groups:
                size_groups[size] = []
            size_groups[size].append((i, grad_flat))
        
        for i, grad_i in enumerate(grads):
            grad_flat_i = grad_i.flatten()
            conflicts = []
            
            # Only check conflicts within same size group for efficiency
            size = grad_flat_i.numel()
            if size in size_groups and len(size_groups[size]) > 1:
                for j, grad_flat_j in size_groups[size]:
                    if i != j:
                        # Efficient cosine similarity computation
                        cosine_sim = F.cosine_similarity(
                            grad_flat_i.unsqueeze(0), grad_flat_j.unsqueeze(0), dim=1
                        ).item()
                        
                        # Efficient correlation computation
                        grad_i_centered = grad_flat_i - grad_flat_i.mean()
                        grad_j_centered = grad_flat_j - grad_flat_j.mean()
                        norm_product = grad_i_centered.norm() * grad_j_centered.norm()
                        
                        if norm_product > 1e-8:
                            correlation = torch.dot(grad_i_centered, grad_j_centered) / norm_product
                            if cosine_sim < -conflict_threshold or correlation < -conflict_threshold:
                                conflicts.append((j, cosine_sim, correlation.item()))
            if conflicts:
                surgered_grad = grad_i.clone()
                for j, cosine_sim, correlation in conflicts:
                    grad_j = grads[j]
                    if grad_i.shape == grad_j.shape:
                        grad_flat_j = grad_j.flatten()
                        if grad_flat_j.norm() > 1e-8:
                            conflict_weight = max(abs(cosine_sim), abs(correlation))
                            projection = torch.dot(grad_flat_i, grad_flat_j) / (
                                grad_flat_j.norm() ** 2 + 1e-8
                            )
                            projected_component = projection * grad_j
                            surgered_grad = surgered_grad - conflict_weight * 0.5 * projected_component
                surgered_grads.append(surgered_grad)
                self.gradient_conflicts += 1
                self.surgery_applications += 1
            else:
                surgered_grads.append(grad_i)
        return surgered_grads

    def _apply_riemannian_optimization(self, params, grads, group):
        riemannian_grads = []
        # Process only parameters that need Riemannian optimization
        for i, (param, grad) in enumerate(zip(params, grads)):
            state = self.state[param]
            
            # Skip expensive operations for large parameters or when metric not available
            if 'metric_tensor' not in state or param.numel() > 10000:
                riemannian_grads.append(grad)
                continue
                
            grad_flat = grad.flatten()
            
            # Use cached metric tensor updates for efficiency
            cache_key = f"riemannian_{id(param)}_{self.global_step // 10}"
            
            if state['prev_grad'] is not None:
                prev_grad_flat = state['prev_grad'].flatten()
                if prev_grad_flat.numel() == grad_flat.numel():
                    grad_diff = grad_flat - prev_grad_flat
                    
                    # Only update metric tensor if significant change
                    if grad_diff.norm() > 1e-6:
                        metric_size = min(grad_flat.numel(), 100)
                        if metric_size <= grad_flat.numel():
                            grad_sample = grad_flat[:metric_size]
                            
                            # More efficient outer product computation
                            metric_update = torch.outer(grad_sample, grad_sample)
                            metric_norm = torch.norm(metric_update, p='fro')
                            
                            if metric_norm > 1e-8:
                                metric_update = metric_update / metric_norm
                                if state['metric_tensor'].shape == metric_update.shape:
                                    # Use momentum for metric tensor updates
                                    state['metric_tensor'] = 0.95 * state['metric_tensor'] + 0.05 * metric_update
                metric_size = state['metric_tensor'].shape[0]
                if metric_size <= grad_flat.numel():
                    grad_sample = grad_flat[:metric_size]
                    try:
                        metric_tensor_reg = state['metric_tensor'] + 1e-6 * torch.eye(
                            metric_size, device=param.device, dtype=param.dtype
                        )
                        natural_grad_sample = torch.linalg.solve(metric_tensor_reg, grad_sample)
                        natural_grad_flat = grad_flat.clone()
                        natural_grad_flat[:metric_size] = natural_grad_sample
                        riemannian_grad = natural_grad_flat.view(grad.shape)
                        riemannian_grads.append(riemannian_grad)
                    except Exception:
                        riemannian_grads.append(grad)
                else:
                    riemannian_grads.append(grad)
            else:
                riemannian_grads.append(grad)
        return riemannian_grads

    def _apply_natural_gradients(self, params, grads, group):
        natural_grads = []
        for param, grad in zip(params, grads):
            state = self.state[param]
            if 'fisher_diag' in state:
                grad_squared = grad ** 2
                state['fisher_diag'] = 0.95 * state['fisher_diag'] + 0.05 * grad_squared
                fisher_reg = state['fisher_diag'] + group['eps']
                natural_grad = grad / (fisher_reg.sqrt() + group['eps'])
                state['natural_grad'] = natural_grad
                natural_grads.append(natural_grad)
            else:
                natural_grads.append(grad)
        return natural_grads

    def _apply_information_regularization(self, params, grads, group):
        regularized_grads = []
        for param, grad in zip(params, grads):
            state = self.state[param]
            if group['entropy_regularization'] > 0:
                param_flat = param.flatten()
                if param_flat.numel() > 1 and torch.isfinite(param_flat).all():
                    # Safe histogram computation
                    param_min = param_flat.min().item()
                    param_max = param_flat.max().item()
                    
                    if abs(param_max - param_min) > 1e-8:  # Valid range
                        param_hist = torch.histc(param_flat, bins=50, min=param_min, max=param_max)
                        param_hist = param_hist + 1e-8
                        param_hist = param_hist / param_hist.sum()
                        entropy_est = -torch.sum(param_hist * torch.log(param_hist)).item()
                        state['entropy_estimate'] = 0.9 * state.get('entropy_estimate', 0.0) + 0.1 * entropy_est
                        
                        # Conservative entropy gradient
                        entropy_grad = torch.clamp(torch.sign(param) * group['entropy_regularization'], min=-1e-3, max=1e-3)
                        regularized_grad = grad + entropy_grad
                        regularized_grads.append(regularized_grad)
                    else:
                        regularized_grads.append(grad)
                else:
                    regularized_grads.append(grad)
            else:
                regularized_grads.append(grad)
        return regularized_grads

    def _apply_quasi_newton_update(self, param, grad, state, group):
        if state['prev_grad'] is None or state['prev_param'] is None:
            return grad
            
        # More efficient quasi-Newton update with better numerical stability
        s_k = param.detach() - state['prev_param']
        y_k = grad - state['prev_grad']
        s_k_flat = s_k.flatten()
        y_k_flat = y_k.flatten()
        
        # Improved numerical stability check
        sy_k = torch.dot(s_k_flat, y_k_flat).item()
        s_norm = s_k_flat.norm().item()
        y_norm = y_k_flat.norm().item()
        
        # Enhanced curvature condition for numerical stability
        if abs(sy_k) > 1e-8 and s_norm > 1e-8 and y_norm > 1e-8:
            # Memory-efficient history management
            max_history = min(20, param.numel() // 100 + 5)  # Adaptive history size
            
            state['s_history'].append(s_k_flat)
            state['y_history'].append(y_k_flat)
            state['rho_history'].append(1.0 / sy_k)
            
            # Trim history to maintain efficiency
            if len(state['s_history']) > max_history:
                state['s_history'].popleft()
                state['y_history'].popleft()
                state['rho_history'].popleft()
            
            if len(state['s_history']) > 0:
                q = grad.flatten()
                alphas = []
                
                # Optimized L-BFGS two-loop recursion
                for i in range(len(state['s_history']) - 1, -1, -1):
                    s_i = state['s_history'][i]
                    y_i = state['y_history'][i]
                    rho_i = state['rho_history'][i]
                    
                    if s_i.numel() == q.numel() and abs(rho_i) < 1e6:  # Numerical stability
                        alpha_i = rho_i * torch.dot(s_i, q).item()
                        q = q - alpha_i * y_i
                        alphas.append(alpha_i)
                    else:
                        alphas.append(0.0)
                if len(state['y_history']) > 0 and state['y_history'][-1].numel() == q.numel():
                    y_last = state['y_history'][-1]
                    gamma_k = sy_k / torch.dot(y_last, y_last).item()
                    state['gamma'] = max(0.1, min(10.0, gamma_k))
                r = state['gamma'] * q
                alphas.reverse()
                for i, alpha_i in enumerate(alphas):
                    if i < len(state['s_history']) and i < len(state['y_history']):
                        s_i = state['s_history'][i]
                        y_i = state['y_history'][i]
                        rho_i = state['rho_history'][i]
                        if s_i.numel() == r.numel():
                            beta_i = rho_i * torch.dot(y_i, r).item()
                            r = r + (alpha_i - beta_i) * s_i
                quasi_newton_grad = r.view(grad.shape)
                return quasi_newton_grad
        return grad

    def _apply_conjugate_gradient_acceleration(self, param, grad, state, group):
        if 'conjugate_direction' not in state or state['prev_grad'] is None:
            state['conjugate_direction'] = grad.clone()
            return grad
        grad_flat = grad.flatten()
        prev_grad_flat = state['prev_grad'].flatten()
        if grad_flat.numel() == prev_grad_flat.numel():
            grad_norm_sq = torch.dot(grad_flat, grad_flat)
            prev_grad_norm_sq = torch.dot(prev_grad_flat, prev_grad_flat)
            if prev_grad_norm_sq > 1e-8:
                beta_fr = grad_norm_sq / prev_grad_norm_sq
                grad_diff = grad_flat - prev_grad_flat
                beta_pr = torch.dot(grad_flat, grad_diff) / prev_grad_norm_sq
                beta = max(0.0, min(beta_fr.item(), beta_pr.item()))
                state['conjugate_beta'] = beta
                conjugate_dir = grad + beta * state['conjugate_direction']
                state['conjugate_direction'] = conjugate_dir
                return conjugate_dir
        return grad

    def _update_low_rank_second_moment(self, param, grad, exp_avg_sq, state, beta2):
        if 'low_rank_u' in state and param.dim() >= 2:
            grad_outer = torch.outer(
                grad.flatten()[: state['low_rank_u'].shape[0]],
                grad.flatten()[: state['low_rank_v'].shape[0]],
            )
            u, s, v = state['low_rank_u'], state['low_rank_s'], state['low_rank_v']
            state['low_rank_s'] = beta2 * s + (1 - beta2) * torch.diag(grad_outer)[: len(s)]
            low_rank_diag = torch.sum(u * s.unsqueeze(0), dim=1) ** 2
            param_flat = param.flatten()
            if low_rank_diag.numel() <= param_flat.numel():
                full_diag = torch.ones_like(param_flat) * low_rank_diag.mean()
                full_diag[: low_rank_diag.numel()] = low_rank_diag
            else:
                full_diag = low_rank_diag[: param_flat.numel()]
            exp_avg_sq.copy_(full_diag.view(param.shape))
        else:
            exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)