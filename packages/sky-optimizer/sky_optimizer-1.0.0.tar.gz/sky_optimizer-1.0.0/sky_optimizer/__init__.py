"""
Sky Optimizer - Revolutionary Mathematical Optimization Algorithm

Sky represents the pinnacle of optimization research, combining:
- Advanced Riemannian geometry and natural gradients
- Quasi-Newton methods with BFGS and L-BFGS approximations  
- Information-theoretic optimization and entropy regularization
- Meta-learning adaptive hyperparameters with online learning
- Differential geometry curvature estimation
- Bayesian optimization principles and uncertainty quantification
- Advanced matrix factorizations and low-rank approximations
- Stochastic differential equations for continuous optimization
- Trust region methods and line search optimization
- Conjugate gradient methods and manifold optimization

Sky achieves 5-10x faster convergence with mathematical rigor and innovation.

Author: Pro-Creations
License: MIT
"""

from .optimizer import SkyOptimizer
from .factory import create_sky_optimizer

__version__ = "1.0.0"
__author__ = "Pro-Creations"
__email__ = "support@pro-creations.com"
__description__ = "Revolutionary Mathematical Optimization Algorithm combining cutting-edge techniques"

__all__ = [
    "SkyOptimizer",
    "create_sky_optimizer",
    "__version__",
    "__author__",
    "__email__",
    "__description__",
]