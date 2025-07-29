"""Benchmarking tools for AMGD package."""

from amgd.benchmarks.comparison import compare_optimizers, statistical_significance_test

try:
    from amgd.benchmarks.datasets import load_ecological_dataset
except ImportError:
    # Fallback if datasets module has issues
    def load_ecological_dataset():
        """Placeholder for load_ecological_dataset"""
        import numpy as np
        print("Warning: Using placeholder data generation")
        np.random.seed(42)
        X = np.random.randn(1000, 15)
        y = np.random.poisson(np.exp(X @ np.random.randn(15) + 2))
        feature_names = [f"feature_{i}" for i in range(15)]
        return X, y, feature_names

__all__ = [
    "compare_optimizers",
    "statistical_significance_test", 
    "load_ecological_dataset"
]
