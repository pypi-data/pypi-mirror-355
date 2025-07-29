import numpy as np


class SkyMetricsMixin:
    def get_sky_metrics(self):
        metrics = {
            'global_step': self.global_step,
            'gradient_conflicts': self.gradient_conflicts,
            'surgery_applications': self.surgery_applications,
            'numerical_rescues': self.numerical_rescues,
            'adaptation_events': self.adaptation_events,
            'landscape_metrics': self.landscape_metrics.copy(),
            'meta_learning_state': self.meta_learning_state.copy(),
        }
        for key, values in self.gradient_stats.items():
            if values:
                recent_vals = list(values)
                metrics[f'recent_{key}'] = recent_vals[-1] if recent_vals else None
                metrics[f'avg_{key}'] = (
                    np.mean(recent_vals[-10:]) if len(recent_vals) >= 10 else None
                )
                metrics[f'std_{key}'] = (
                    np.std(recent_vals[-10:]) if len(recent_vals) >= 10 else None
                )
        total_entropy = sum(self.entropy_estimates.values())
        avg_uncertainty = (
            np.mean(list(self.bayesian_uncertainty.values())) if self.bayesian_uncertainty else 0
        )
        metrics['total_entropy'] = total_entropy
        metrics['average_uncertainty'] = avg_uncertainty
        metrics['param_groups'] = len(self.param_groups)
        total_params = sum(sum(p.numel() for p in group['params']) for group in self.param_groups)
        metrics['total_parameters'] = total_params
        return metrics

    def print_sky_status(self):
        metrics = self.get_sky_metrics()
        print(f"\n🌌 Sky Revolutionary Optimizer Status (Step {metrics['global_step']:,}):")
        print("=" * 80)
        print("🚀 Mathematical Performance:")
        print(f"   • Gradient conflicts resolved: {metrics['gradient_conflicts']:,}")
        print(f"   • Surgical interventions: {metrics['surgery_applications']:,}")
        print(f"   • Numerical stability rescues: {metrics['numerical_rescues']:,}")
        print(f"   • Adaptive events: {metrics['adaptation_events']:,}")
        print("\n🧮 Mathematical Insights:")
        print(f"   • Total system entropy: {metrics.get('total_entropy', 0):.6f}")
        print(f"   • Average parameter uncertainty: {metrics.get('average_uncertainty', 0):.6f}")
        if metrics['meta_learning_state']:
            print(
                f"   • Learning rate adaptation: {metrics['meta_learning_state'].get('lr_adaptation', 1.0):.3f}"
            )
            print(
                f"   • Momentum adaptation: {metrics['meta_learning_state'].get('momentum_adaptation', 1.0):.3f}"
            )
        if metrics['landscape_metrics']:
            print("\n🗺️ Loss Landscape Analysis:")
            for key, value in metrics['landscape_metrics'].items():
                print(f"   • {key}: {value:.6f}")
        print(f"\n📊 Recent Mathematical Statistics:")
        stat_keys = ['grad_param_ratio', 'total_entropy', 'fisher_trace', 'avg_condition_number', 'grad_variance']
        for key in stat_keys:
            recent_key = f'recent_{key}'
            avg_key = f'avg_{key}'
            if recent_key in metrics and metrics[recent_key] is not None:
                avg_val = metrics.get(avg_key, metrics[recent_key])
                print(f"   • {key}: {metrics[recent_key]:.6e} (avg: {avg_val:.6e})")
        print("=" * 80)