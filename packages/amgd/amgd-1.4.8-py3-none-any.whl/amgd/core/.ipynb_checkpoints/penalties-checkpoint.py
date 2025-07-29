"""
Regularization penalties for sparse optimization with adaptive soft-thresholding.
"""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional


class PenaltyBase(ABC):
    """Base class for regularization penalties."""
    
    @abstractmethod
    def __call__(self, x: np.ndarray) -> float:
        """Compute penalty value."""
        pass
        
    @abstractmethod
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Compute penalty gradient."""
        pass
        
    @abstractmethod
    def proximal_operator(self, x: np.ndarray, step_size: float) -> np.ndarray:
        """Apply proximal operator for the penalty."""
        pass


class L1Penalty(PenaltyBase):
    """L1 (Lasso) penalty with adaptive soft-thresholding option."""
    
    def __init__(self, lambda1: float = 1.0, adaptive: bool = False, 
                 adaptive_constant: float = 0.1):
        """
        Parameters
        ----------
        lambda1 : float
            L1 regularization strength.
        adaptive : bool
            Whether to use adaptive soft-thresholding.
        adaptive_constant : float
            Constant added to denominator in adaptive thresholding.
            Smaller values lead to more aggressive sparsity.
        """
        self.lambda1 = lambda1
        self.adaptive = adaptive
        self.adaptive_constant = adaptive_constant
        
    def __call__(self, x: np.ndarray) -> float:
        """Compute L1 penalty value."""
        return self.lambda1 * np.sum(np.abs(x))
        
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Compute L1 penalty subgradient."""
        return self.lambda1 * np.sign(x)
        
    def proximal_operator(self, x: np.ndarray, step_size: float) -> np.ndarray:
        """Soft-thresholding operator (standard or adaptive)."""
        if self.adaptive:
            # Adaptive soft-thresholding as in your AMGD algorithm
            denom = np.abs(x) + self.adaptive_constant
            threshold = step_size * self.lambda1 / denom
            return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)
        else:
            # Standard soft-thresholding
            threshold = self.lambda1 * step_size
            return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)
    
    def adaptive_proximal_operator(self, x: np.ndarray, step_size: float, 
                                  adaptive_constant: Optional[float] = None) -> np.ndarray:
        """
        Explicit adaptive soft-thresholding operator.
        
        Parameters
        ----------
        x : np.ndarray
            Input coefficients.
        step_size : float
            Step size (alpha_t in your algorithm).
        adaptive_constant : float, optional
            Override the default adaptive constant.
            
        Returns
        -------
        np.ndarray
            Thresholded coefficients.
        """
        if adaptive_constant is None:
            adaptive_constant = self.adaptive_constant
            
        denom = np.abs(x) + adaptive_constant
        threshold = step_size * self.lambda1 / denom
        return np.sign(x) * np.maximum(np.abs(x) - threshold, 0)


class AdaptiveL1Penalty(L1Penalty):
    """L1 penalty with adaptive soft-thresholding enabled by default."""
    
    def __init__(self, lambda1: float = 1.0, adaptive_constant: float = 0.1):
        """
        Parameters
        ----------
        lambda1 : float
            L1 regularization strength.
        adaptive_constant : float
            Constant added to denominator in adaptive thresholding.
            Recommended values:
            - 0.1: Default (moderate sparsity)
            - 0.01: More aggressive sparsity
            - 0.001: Very aggressive sparsity
        """
        super().__init__(lambda1=lambda1, adaptive=True, 
                        adaptive_constant=adaptive_constant)


class L2Penalty(PenaltyBase):
    """L2 (Ridge) penalty."""
    
    def __init__(self, lambda2: float = 1.0):
        """
        Parameters
        ----------
        lambda2 : float
            L2 regularization strength.
        """
        self.lambda2 = lambda2
        
    def __call__(self, x: np.ndarray) -> float:
        """Compute L2 penalty value."""
        return 0.5 * self.lambda2 * np.sum(x ** 2)
        
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Compute L2 penalty gradient."""
        return self.lambda2 * x
        
    def proximal_operator(self, x: np.ndarray, step_size: float) -> np.ndarray:
        """L2 proximal operator."""
        return x / (1 + self.lambda2 * step_size)


class ElasticNetPenalty(PenaltyBase):
    """Elastic Net penalty (combination of L1 and L2) with adaptive L1 option."""
    
    def __init__(self, lambda1: float = 1.0, lambda2: float = 1.0, 
                 adaptive_l1: bool = False, adaptive_constant: float = 0.1):
        """
        Parameters
        ----------
        lambda1 : float
            L1 regularization strength.
        lambda2 : float
            L2 regularization strength.
        adaptive_l1 : bool
            Whether to use adaptive soft-thresholding for L1 component.
        adaptive_constant : float
            Constant for adaptive L1 thresholding.
        """
        self.lambda1 = lambda1
        self.lambda2 = lambda2
        self.l1_penalty = L1Penalty(lambda1, adaptive=adaptive_l1, 
                                   adaptive_constant=adaptive_constant)
        self.l2_penalty = L2Penalty(lambda2)
        
    def __call__(self, x: np.ndarray) -> float:
        """Compute Elastic Net penalty value."""
        return self.l1_penalty(x) + self.l2_penalty(x)
        
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Compute Elastic Net penalty gradient."""
        return self.l1_penalty.gradient(x) + self.l2_penalty.gradient(x)
        
    def proximal_operator(self, x: np.ndarray, step_size: float) -> np.ndarray:
        """Elastic Net proximal operator with optional adaptive L1."""
        # First apply L2 proximal operator
        x_l2 = self.l2_penalty.proximal_operator(x, step_size)
        # Then apply L1 proximal operator (adaptive or standard)
        return self.l1_penalty.proximal_operator(x_l2, step_size)


class NonePenalty(PenaltyBase):
    """No penalty (unregularized)."""
    
    def __call__(self, x: np.ndarray) -> float:
        """No penalty."""
        return 0.0
        
    def gradient(self, x: np.ndarray) -> np.ndarray:
        """Zero gradient."""
        return np.zeros_like(x)
        
    def proximal_operator(self, x: np.ndarray, step_size: float) -> np.ndarray:
        """Identity operator."""
        return x


def create_penalty(penalty_type: str, lambda1: float = 0.0, lambda2: float = 0.0,
                  adaptive: bool = False, adaptive_constant: float = 0.1) -> PenaltyBase:
    """
    Create penalty object from string specification.
    
    Parameters
    ----------
    penalty_type : str
        Type of penalty: 'l1', 'l2', 'elasticnet', 'adaptive_l1', or 'none'.
    lambda1 : float
        L1 regularization strength.
    lambda2 : float
        L2 regularization strength.
    adaptive : bool
        Whether to use adaptive soft-thresholding for L1 penalties.
    adaptive_constant : float
        Constant for adaptive thresholding.
        
    Returns
    -------
    penalty : PenaltyBase
        Penalty object.
    """
    penalty_type = penalty_type.lower()
    
    if penalty_type == 'l1':
        return L1Penalty(lambda1, adaptive=adaptive, 
                        adaptive_constant=adaptive_constant)
    elif penalty_type == 'adaptive_l1':
        return AdaptiveL1Penalty(lambda1, adaptive_constant=adaptive_constant)
    elif penalty_type == 'l2':
        return L2Penalty(lambda2)
    elif penalty_type == 'elasticnet':
        return ElasticNetPenalty(lambda1, lambda2, adaptive_l1=adaptive,
                               adaptive_constant=adaptive_constant)
    elif penalty_type == 'none':
        return NonePenalty()
    else:
        raise ValueError(f"Unknown penalty type: {penalty_type}")


# Utility functions for testing and comparison
def compare_thresholding_methods(x: np.ndarray, step_size: float, lambda1: float,
                               adaptive_constant: float = 0.1) -> dict:
    """
    Compare standard vs adaptive soft-thresholding on given coefficients.
    
    Parameters
    ----------
    x : np.ndarray
        Input coefficients.
    step_size : float
        Step size for thresholding.
    lambda1 : float
        L1 penalty strength.
    adaptive_constant : float
        Adaptive thresholding constant.
        
    Returns
    -------
    dict
        Results from both methods.
    """
    # Standard soft-thresholding
    standard_penalty = L1Penalty(lambda1, adaptive=False)
    standard_result = standard_penalty.proximal_operator(x, step_size)
    
    # Adaptive soft-thresholding
    adaptive_penalty = L1Penalty(lambda1, adaptive=True, 
                                adaptive_constant=adaptive_constant)
    adaptive_result = adaptive_penalty.proximal_operator(x, step_size)
    
    return {
        'input': x,
        'standard': standard_result,
        'adaptive': adaptive_result,
        'standard_sparsity': np.mean(standard_result == 0),
        'adaptive_sparsity': np.mean(adaptive_result == 0),
        'standard_nonzero': np.sum(standard_result != 0),
        'adaptive_nonzero': np.sum(adaptive_result != 0)
    }


