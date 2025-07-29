import math
import torch


class SkyStepMixin:
    def _compute_revolutionary_adaptive_params(self, param, grad, state, group, step):
        base_lr = group['lr']
        base_beta1 = group['betas'][0]
        base_beta2 = group['betas'][1]
        base_rho = group['rho']
        lr_scale = self.meta_learning_state.get('lr_adaptation', 1.0)
        momentum_scale = self.meta_learning_state.get('momentum_adaptation', 1.0)
        if step < group['warmup_steps']:
            warmup_factor = step / group['warmup_steps']
            warmup_factor = 0.5 * (1 + math.cos(math.pi * (1 - warmup_factor)))
            lr_scale *= 0.1 + 0.9 * warmup_factor
        if group['information_theory'] and 'entropy_estimate' in state:
            entropy = state['entropy_estimate']
            entropy_factor = 1.0 + 0.1 * math.tanh(entropy - 1.0)
            lr_scale *= entropy_factor
        if group['uncertainty_quantification'] and 'parameter_uncertainty' in state:
            uncertainty = state['parameter_uncertainty'].mean().item()
            uncertainty_factor = 1.0 / (1.0 + uncertainty)
            lr_scale *= uncertainty_factor
        curvature_ema = state.get('curvature_ema', 0.0)
        if group['riemannian_geometry'] and curvature_ema > 0:
            curvature_factor = 1.0 / (1.0 + curvature_ema * 0.1)
            lr_scale *= curvature_factor
        if group['trust_region_methods']:
            trust_ratio = state.get('trust_ratio', 1.0)
            if trust_ratio > 0.75:
                lr_scale *= 1.1
            elif trust_ratio < 0.25:
                lr_scale *= 0.9
        if group.get('gradient_variance_adaptation', False):
            grad_var = state.get('grad_var_ema', 0.0)
            var_factor = 1.0 / (1.0 + grad_var)
            lr_scale *= var_factor
            momentum_scale *= var_factor ** 0.5
        correlation_factor = 1.0
        if 'prev_grad' in state and state['prev_grad'] is not None:
            grad_flat = grad.flatten()
            prev_grad_flat = state['prev_grad'].flatten()
            if grad_flat.numel() == prev_grad_flat.numel():
                correlation = torch.nn.functional.cosine_similarity(
                    grad_flat.unsqueeze(0), prev_grad_flat.unsqueeze(0), dim=1
                ).item()
                if correlation > 0.7:
                    correlation_factor = 1.1
                elif correlation < 0.3:
                    correlation_factor = 0.9
        cooldown_steps = max(0, step - group['warmup_steps'])
        cooldown_scale = group['cooldown_factor'] ** (cooldown_steps / 1000)
        if group.get('cyclical_lr', False):
            cycle_steps = max(1, group.get('cycle_steps', 1))
            cycle_mult = group.get('cycle_multiplier', 1.0)
            cycle_pos = (self.global_step % cycle_steps) / cycle_steps
            cyc_factor = 0.5 * (1 - math.cos(2 * math.pi * cycle_pos))
            lr_scale *= 0.5 + cyc_factor * cycle_mult
        if group.get('loss_landscape_aware', False) and self.landscape_metrics:
            if 'loss_variance' in self.landscape_metrics:
                loss_var = self.landscape_metrics['loss_variance']
                lr_scale *= 1.0 / (1.0 + loss_var)
            if 'loss_trend' in self.landscape_metrics:
                trend = self.landscape_metrics['loss_trend']
                lr_scale *= 1.0 - 0.5 * max(-1.0, min(1.0, trend))
        adaptive_lr = base_lr * lr_scale * cooldown_scale
        adaptive_beta1 = min(0.99, max(0.8, base_beta1 * momentum_scale * correlation_factor))
        adaptive_beta2 = base_beta2
        adaptive_rho = base_rho
        if group['spectral_normalization'] and 'spectral_norm' in state:
            spectral_norm = state['spectral_norm']
            if spectral_norm > 2.0:
                adaptive_rho *= 0.8
            elif spectral_norm < 0.5:
                adaptive_rho *= 1.2
        return adaptive_lr, adaptive_beta1, adaptive_beta2, adaptive_rho

    def _compute_adaptive_curvature_weight(self, state, group):
        base_weight = 0.4
        curvature_ema = state.get('curvature_ema', 0.0)
        if curvature_ema > 0.1:
            curvature_adjustment = min(0.3, curvature_ema * 0.5)
        else:
            curvature_adjustment = -0.1
        step_factor = max(0, 0.2 - self.global_step / 20000)
        condition_number = state.get('condition_number', 1.0)
        if condition_number > 100:
            condition_adjustment = -0.1
        else:
            condition_adjustment = 0.05
        weight = base_weight + curvature_adjustment + step_factor + condition_adjustment
        return max(0.0, min(0.8, weight))

    def _compute_revolutionary_step_direction(self, param, grad, exp_avg, denom, hessian_diag, state, group, bias_correction1, adaptive_beta1, adaptive_rho, step):
        # Improved numerical stability and GPU efficiency
        eps = group['eps']
        
        # Compute base AdamW step with better numerical stability
        if group['nesterov']:
            nesterov_grad = adaptive_beta1 * exp_avg + (1 - adaptive_beta1) * grad
            adamw_step = nesterov_grad / (bias_correction1 * torch.clamp(denom, min=eps))
        else:
            adamw_step = exp_avg / (bias_correction1 * torch.clamp(denom, min=eps))
        
        # Enhanced curvature adaptation with better conditioning
        if group['curvature_adaptation']:
            # More robust Hessian conditioning
            hessian_safe = torch.clamp(hessian_diag, min=eps, max=1e4)  # Reduced upper bound for stability
            
            # Improved natural gradient computation
            if 'natural_grad' in state:
                natural_component = state['natural_grad'] / bias_correction1
            else:
                # Better conditioned natural gradient approximation
                hessian_inv = 1.0 / (hessian_safe + eps)
                natural_component = exp_avg * hessian_inv / bias_correction1
            
            # Enhanced Fisher information component
            if 'fisher_diag' in state:
                fisher_safe = torch.clamp(state['fisher_diag'], min=eps, max=1e4)
                fisher_sqrt = torch.sqrt(fisher_safe)
                fisher_component = exp_avg / (bias_correction1 * fisher_sqrt)
            else:
                fisher_component = natural_component
            # Adaptive weight computation with improved stability
            curvature_weight = self._compute_adaptive_curvature_weight(state, group)
            cond_num = state.get('condition_number', 1.0)
            
            # More stable condition number scaling
            weight_scale = 1.0 / (1.0 + 0.1 * math.log1p(max(1.0, cond_num)))
            curvature_weight = torch.clamp(torch.tensor(curvature_weight * weight_scale), min=0.0, max=0.8).item()
            
            # Dynamic weight allocation based on optimization progress
            natural_weight = 0.3 if group['natural_gradients'] else 0.0
            fisher_weight = 0.2 if group['fisher_information'] else 0.0
            
            # Adjust weights based on gradient properties
            grad_norm = torch.clamp(grad.norm(), min=1e-8).item()
            if grad_norm > 1.0:  # Large gradients - favor robust methods
                natural_weight *= 1.2
                fisher_weight *= 0.8
            elif grad_norm < 0.1:  # Small gradients - favor precise methods
                fisher_weight *= 1.2
                natural_weight *= 0.8
            
            # Normalize weights for stability
            total_weight = curvature_weight + natural_weight + fisher_weight
            if total_weight > 1e-8:
                curvature_weight /= total_weight
                natural_weight /= total_weight
                fisher_weight /= total_weight
            
            # Compute second-order step with improved numerical stability
            second_order_step = (
                curvature_weight * natural_component
                + natural_weight * natural_component
                + fisher_weight * fisher_component
            )
            
            # More conservative clamping for stability
            clamp_value = min(adaptive_rho, 1.0)
            second_order_step = torch.clamp(second_order_step, min=-clamp_value, max=clamp_value)
            
            # Balanced combination of first and second order information
            adamw_weight = max(0.2, 1.0 - curvature_weight)  # Ensure minimum first-order contribution
            combined_step = adamw_weight * adamw_step + curvature_weight * second_order_step
        else:
            combined_step = adamw_step
        if group['orthogonal_regularization'] > 0:
            combined_step = self._apply_orthogonal_regularization(
                param, combined_step, group['orthogonal_regularization']
            )
        if group['spectral_normalization']:
            combined_step = self._apply_spectral_normalization(param, combined_step, state)
        if group['matrix_factorization'] and 'low_rank_s' in state:
            singular_values = state['low_rank_s']
            if len(singular_values) > 1:
                max_sv = torch.clamp(singular_values[0], min=1e-8).item()
                min_sv = torch.clamp(singular_values[-1], min=1e-8).item()
                condition_approx = max_sv / min_sv
                condition_factor = 1.0 / (1.0 + 0.1 * math.log(min(condition_approx, 1e6) + 1))
                combined_step *= condition_factor

        # LAMB-style trust ratio for better layer-wise scaling
        if group.get('lamb_trust_ratio', True):
            param_norm = param.detach().norm()
            step_norm = combined_step.norm()
            if param_norm > 0 and step_norm > 0:
                trust_ratio = param_norm / (step_norm + group['eps'])
                state['trust_ratio'] = trust_ratio.item()
                combined_step = combined_step * trust_ratio

        # RAdam rectification for adaptive variance
        if group.get('radam_rectify', True):
            beta2 = group['betas'][1]
            rho_inf = 2.0 / (1.0 - beta2) - 1.0
            rho_t = rho_inf - 2.0 * step * (beta2 ** step) / (1.0 - beta2 ** step)
            if rho_t > 4:
                rect = math.sqrt(
                    (rho_t - 4.0)
                    * (rho_t - 2.0)
                    * rho_inf
                    / ((rho_inf - 4.0) * (rho_inf - 2.0) * rho_t)
                )
                combined_step = combined_step * rect

        return combined_step

    def _apply_trust_region_constraint(self, param, step_direction, state, group):
        trust_radius = state.get('trust_radius', 1.0)
        step_norm = step_direction.norm().item()
        
        # More sophisticated trust region management
        if step_norm > trust_radius:
            scaling_factor = trust_radius / (step_norm + 1e-8)
            constrained_step = step_direction * scaling_factor
            
            # Adaptive trust radius adjustment based on optimization history
            grad_norm = state.get('recent_grad_norm', 1.0)
            loss_trend = getattr(self, 'landscape_metrics', {}).get('loss_trend', 0.0)
            
            # More conservative reduction if loss is increasing
            if loss_trend > 0:  # Loss increasing
                reduction_factor = 0.7
            elif scaling_factor < 0.3:  # Very large step required
                reduction_factor = 0.6
            else:
                reduction_factor = 0.8
            
            state['trust_radius'] = max(0.05, trust_radius * reduction_factor)
            return constrained_step
        else:
            # Adaptive trust radius expansion
            expansion_factor = 1.05
            
            # More aggressive expansion if optimization is going well
            loss_trend = getattr(self, 'landscape_metrics', {}).get('loss_trend', 0.0)
            if loss_trend < -0.01:  # Loss decreasing significantly
                expansion_factor = 1.15
            elif step_norm < 0.5 * trust_radius:  # Step much smaller than trust radius
                expansion_factor = 1.1
            
            state['trust_radius'] = min(3.0, trust_radius * expansion_factor)
            return step_direction

    def _perform_line_search(self, param, step_direction, state, group):
        alpha = state.get('line_search_alpha', 1.0)
        if 'prev_grad' in state and state['prev_grad'] is not None:
            current_grad_norm = step_direction.norm().item()
            prev_grad_norm = state['prev_grad'].norm().item()
            if prev_grad_norm > 0:
                grad_ratio = current_grad_norm / prev_grad_norm
                if grad_ratio > 1.5:
                    alpha *= 0.8
                elif grad_ratio < 0.5:
                    alpha *= 1.2
        alpha = max(0.1, min(2.0, alpha))
        state['line_search_alpha'] = alpha
        return alpha

    def _apply_sde_noise_and_drift(self, param, step_direction, state, group):
        noise_scale = state.get('noise_scale', 0.01)
        param_scale = param.norm().item()
        adaptive_noise_scale = noise_scale * min(1.0, 1.0 / (param_scale + 1e-8))
        noise = torch.randn_like(step_direction) * adaptive_noise_scale
        drift_term = state.get('drift_term', torch.zeros_like(param))
        drift_momentum = 0.9
        state['drift_term'] = drift_momentum * drift_term + (1 - drift_momentum) * step_direction
        sde_step = step_direction + 0.1 * state['drift_term'] + noise
        noise_decay = 0.9999
        state['noise_scale'] = max(1e-6, noise_scale * noise_decay)
        return sde_step

    def _apply_orthogonal_regularization(self, param, step, reg_strength):
        if param.dim() < 2:
            return step
        original_shape = param.shape
        param_2d = param.view(original_shape[0], -1)
        step_2d = step.view(original_shape[0], -1)
        try:
            u, s, v = torch.svd(param_2d)
            if param_2d.shape[0] <= param_2d.shape[1]:
                param_orth = param_2d @ param_2d.t()
                identity = torch.eye(param_2d.shape[0], device=param.device, dtype=param.dtype)
                orth_penalty = param_orth - identity
                orth_gradient = orth_penalty @ param_2d
            else:
                param_orth = param_2d.t() @ param_2d
                identity = torch.eye(param_2d.shape[1], device=param.device, dtype=param.dtype)
                orth_penalty = param_orth - identity
                orth_gradient = param_2d @ orth_penalty
            regularized_step = step_2d - reg_strength * orth_gradient
            return regularized_step.view(original_shape)
        except Exception:
            return step

    def _apply_spectral_normalization(self, param, step, state):
        if param.dim() < 2 or param.numel() > 10000:  # Skip for very large parameters
            return step
            
        param_2d = param.view(param.shape[0], -1)
        
        try:
            # Use more efficient SVD computation
            if min(param_2d.shape) <= 100:  # Full SVD for small matrices
                u, s, vh = torch.linalg.svd(param_2d, full_matrices=False)
                spectral_norm = s[0].item()
                
                if len(s) > 1:
                    condition_number = s[0] / (s[-1] + 1e-8)
                    # Clamp condition number for numerical stability
                    condition_number = min(condition_number.item(), 1e6)
                    state['condition_number'] = condition_number
                else:
                    state['condition_number'] = 1.0
            else:  # Power iteration for large matrices
                spectral_norm = self._estimate_spectral_norm_power_iteration(param_2d, state)
                state['condition_number'] = state.get('condition_number', 1.0)
            
            state['spectral_norm'] = spectral_norm
            
            # More conservative spectral normalization
            if spectral_norm > 3.0:
                scale_factor = 2.0 / spectral_norm
                return step * scale_factor
            elif spectral_norm < 0.3:
                scale_factor = min(1.5, 1.0 + 0.1 * (0.3 - spectral_norm))
                return step * scale_factor
            else:
                # Gentle normalization in the normal range
                scale_factor = 1.0 + 0.05 * (1.0 - spectral_norm)
                return step * scale_factor
                
        except Exception:
            # Fallback to simple norm-based scaling
            param_norm = param.norm().item()
            if param_norm > 10.0:
                return step * (5.0 / param_norm)
            return step
    
    def _estimate_spectral_norm_power_iteration(self, matrix, state, num_iterations=5):
        """Estimate spectral norm using power iteration for large matrices."""
        # Use cached vector if available
        if 'power_iteration_vector' in state:
            v = state['power_iteration_vector']
        else:
            v = torch.randn(matrix.shape[1], device=matrix.device, dtype=matrix.dtype)
            v = v / v.norm()
            state['power_iteration_vector'] = v
        
        for _ in range(num_iterations):
            v = matrix.t() @ (matrix @ v)
            norm = v.norm()
            if norm > 1e-8:
                v = v / norm
            else:
                break
        
        # Update cached vector
        state['power_iteration_vector'] = v.detach()
        
        # Estimate spectral norm
        Av = matrix @ v
        spectral_norm = Av.norm().item()
        return spectral_norm