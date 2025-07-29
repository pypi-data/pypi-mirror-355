#!/usr/bin/env python3
"""
Setup script for Sky Optimizer
"""

import os
import re
from setuptools import setup, find_packages

# Read the version from __init__.py
def get_version():
    with open(os.path.join("sky_optimizer", "__init__.py"), "r") as f:
        content = f.read()
        match = re.search(r"__version__ = ['\"]([^'\"]*)['\"]", content)
        if match:
            return match.group(1)
        raise RuntimeError("Unable to find version string.")

# Read the long description from README.md
def get_long_description():
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as fh:
            return fh.read()
    return ""

# Core dependencies
install_requires = [
    "torch>=1.11.0",
    "numpy>=1.19.0",
]

# Optional dependencies for advanced features
extras_require = {
    "advanced": [
        "scipy>=1.7.0",  # For advanced mathematical functions
    ],
    "dev": [
        "pytest>=6.0.0",
        "pytest-cov>=2.10.0",
        "black>=21.0.0",
        "flake8>=3.8.0",
        "mypy>=0.800",
        "pre-commit>=2.10.0",
    ],
    "benchmark": [
        "psutil>=5.8.0",  # For memory monitoring in benchmarks
        "matplotlib>=3.3.0",  # For plotting benchmark results
    ],
}

# Include all extras in 'all'
extras_require["all"] = list(set(sum(extras_require.values(), [])))

setup(
    name="sky-optimizer",
    version=get_version(),
    author="Pro-Creations",
    author_email="support@pro-creations.com",
    description="Revolutionary Mathematical Optimization Algorithm combining cutting-edge techniques",
    long_description=get_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/pro-creations/sky-optimizer",
    project_urls={
        "Bug Tracker": "https://github.com/pro-creations/sky-optimizer/issues",
        "Documentation": "https://github.com/pro-creations/sky-optimizer/blob/main/README.md",
        "Source Code": "https://github.com/pro-creations/sky-optimizer",
    },
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Typing :: Typed",
    ],
    keywords=[
        "optimizer",
        "pytorch",
        "machine-learning",
        "deep-learning", 
        "optimization",
        "riemannian-geometry",
        "natural-gradients",
        "quasi-newton",
        "information-theory",
        "meta-learning",
        "bayesian-optimization",
        "matrix-factorization",
        "stochastic-differential-equations",
        "trust-region",
        "conjugate-gradients",
        "mathematical-optimization",
        "artificial-intelligence",
        "neural-networks",
    ],
    python_requires=">=3.8",
    install_requires=install_requires,
    extras_require=extras_require,
    zip_safe=False,
    include_package_data=True,
    package_data={
        "sky_optimizer": ["py.typed"],
    },
)