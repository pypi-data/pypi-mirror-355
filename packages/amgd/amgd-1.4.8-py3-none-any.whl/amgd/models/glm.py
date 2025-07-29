"""General Linear Models implementation."""

import numpy as np
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Union, Tuple, List
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator, RegressorMixin

from amgd.core.optimizer import OptimizerBase, AMGDOptimizer
from amgd.core.penalties import PenaltyBase, create_penalty
from amgd.utils.validation import check_array, check_consistent_length, check_is_fitted


class ExponentialFamily(ABC):
    """Base class for exponential family distributions."""
    
    @abstractmethod
    def link_function(self, eta: np.ndarray) -> np.ndarray:
        """Link function: maps linear predictor to parameter space."""
        pass
    
    @abstractmethod
    def inverse_link(self, mu: np.ndarray) -> np.ndarray:
        """Inverse link function: maps mean to linear predictor."""
        pass
    
    @abstractmethod
    def variance(self, mu: np.ndarray) -> np.ndarray:
        """Variance function."""
        pass
    
    @abstractmethod
    def deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Deviance function."""
        pass
    
    @abstractmethod
    def log_likelihood(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Log-likelihood function."""
        pass


class PoissonFamily(ExponentialFamily):
    """Poisson family with log link."""
    
    def link_function(self, mu: np.ndarray) -> np.ndarray:
        """Log link function."""
        return np.log(np.maximum(mu, 1e-8))
    
    def inverse_link(self, eta: np.ndarray) -> np.ndarray:
        """Exponential inverse link function."""
        eta_clipped = np.clip(eta, -20, 20)
        return np.exp(eta_clipped)
    
    def variance(self, mu: np.ndarray) -> np.ndarray:
        """Poisson variance function: V(μ) = μ."""
        return np.maximum(mu, 1e-8)
    
    def deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Poisson deviance."""
        y_safe = np.maximum(y, 1e-8)
        mu_safe = np.maximum(mu, 1e-8)
        return 2 * np.sum(y * np.log(y_safe / mu_safe) - (y - mu))
    
    def log_likelihood(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Poisson log-likelihood."""
        from scipy import special
        mu_safe = np.maximum(mu, 1e-8)
        return np.sum(y * np.log(mu_safe) - mu - special.gammaln(y + 1))


class GaussianFamily(ExponentialFamily):
    """Gaussian family with identity link."""
    
    def link_function(self, mu: np.ndarray) -> np.ndarray:
        """Identity link function."""
        return mu
    
    def inverse_link(self, eta: np.ndarray) -> np.ndarray:
        """Identity inverse link function."""
        return eta
    
    def variance(self, mu: np.ndarray) -> np.ndarray:
        """Gaussian variance function: V(μ) = 1."""
        return np.ones_like(mu)
    
    def deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Gaussian deviance."""
        return np.sum((y - mu) ** 2)
    
    def log_likelihood(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Gaussian log-likelihood (without constant terms)."""
        return -0.5 * np.sum((y - mu) ** 2)


class BinomialFamily(ExponentialFamily):
    """Binomial family with logit link."""
    
    def link_function(self, mu: np.ndarray) -> np.ndarray:
        """Logit link function."""
        mu_clipped = np.clip(mu, 1e-8, 1 - 1e-8)
        return np.log(mu_clipped / (1 - mu_clipped))
    
    def inverse_link(self, eta: np.ndarray) -> np.ndarray:
        """Logistic inverse link function."""
        eta_clipped = np.clip(eta, -20, 20)
        return 1 / (1 + np.exp(-eta_clipped))
    
    def variance(self, mu: np.ndarray) -> np.ndarray:
        """Binomial variance function: V(μ) = μ(1-μ)."""
        mu_clipped = np.clip(mu, 1e-8, 1 - 1e-8)
        return mu_clipped * (1 - mu_clipped)
    
    def deviance(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Binomial deviance."""
        mu_safe = np.clip(mu, 1e-8, 1 - 1e-8)
        y_safe = np.clip(y, 1e-8, 1 - 1e-8)
        
        term1 = y * np.log(y_safe / mu_safe)
        term2 = (1 - y) * np.log((1 - y_safe) / (1 - mu_safe))
        
        return 2 * np.sum(term1 + term2)
    
    def log_likelihood(self, y: np.ndarray, mu: np.ndarray) -> float:
        """Binomial log-likelihood."""
        mu_safe = np.clip(mu, 1e-8, 1 - 1e-8)
        return np.sum(y * np.log(mu_safe) + (1 - y) * np.log(1 - mu_safe))


class GLM(BaseEstimator, RegressorMixin):
    """
    Generalized Linear Model with AMGD optimization.
    
    Parameters
    ----------
    family : str or ExponentialFamily, default='gaussian'
        The exponential family distribution. Options: 'gaussian', 'poisson', 'binomial'
        or an instance of ExponentialFamily.
    optimizer : str or OptimizerBase, default='amgd'
        The optimization algorithm to use.
    penalty : str or PenaltyBase, default=None
        Regularization penalty. Options: 'l1', 'l2', 'elasticnet', or PenaltyBase instance.
    lambda1 : float, default=0.0
        L1 regularization strength.
    lambda2 : float, default=0.0
        L2 regularization strength.
    alpha : float, default=0.01
        Learning rate for optimization.
    max_iter : int, default=1000
        Maximum number of iterations.
    tol : float, default=1e-6
        Convergence tolerance.
    fit_intercept : bool, default=True
        Whether to fit an intercept term.
    standardize : bool, default=True
        Whether to standardize features.
    verbose : bool, default=False
        Whether to print progress information.
    """
    
    def __init__(self, 
                 family: Union[str, ExponentialFamily] = 'gaussian',
                 optimizer: Union[str, OptimizerBase] = 'amgd',
                 penalty: Union[str, PenaltyBase, None] = None,
                 lambda1: float = 0.0,
                 lambda2: float = 0.0,
                 alpha: float = 0.01,
                 max_iter: int = 1000,
                 tol: float = 1e-6,
                 fit_intercept: bool = True,
                 standardize: bool = True,
                 verbose: bool = False):
        
        self.family = family
        self.optimizer = optimizer
        self.penalty = penalty
        self.lambda1 = lambda1
        self.lambda2 = lambda2
        self.alpha = alpha
        self.max_iter = max_iter
        self.tol = tol
        self.fit_intercept = fit_intercept
        self.standardize = standardize
        self.verbose = verbose
        
        # Initialize family
        self._setup_family()
        
        # Initialize optimizer
        self._setup_optimizer()
        
        # Initialize penalty
        self._setup_penalty()
    
    def _setup_family(self):
        """Setup the exponential family distribution."""
        if isinstance(self.family, str):
            if self.family.lower() == 'gaussian':
                self.family_ = GaussianFamily()
            elif self.family.lower() == 'poisson':
                self.family_ = PoissonFamily()
            elif self.family.lower() == 'binomial':
                self.family_ = BinomialFamily()
            else:
                raise ValueError(f"Unknown family: {self.family}")
        elif isinstance(self.family, ExponentialFamily):
            self.family_ = self.family
        else:
            raise ValueError("Family must be a string or ExponentialFamily instance")
    
    def _setup_optimizer(self):
        """Setup the optimizer."""
        if isinstance(self.optimizer, str):
            if self.optimizer.lower() == 'amgd':
                self.optimizer_ = AMGDOptimizer(
                    alpha=self.alpha,
                    max_iter=self.max_iter,
                    tol=self.tol
                )
            else:
                raise ValueError(f"Unknown optimizer: {self.optimizer}")
        elif isinstance(self.optimizer, OptimizerBase):
            self.optimizer_ = self.optimizer
        else:
            raise ValueError("Optimizer must be a string or OptimizerBase instance")
    
    def _setup_penalty(self):
        """Setup the regularization penalty."""
        if self.penalty is None:
            self.penalty_ = None
        elif isinstance(self.penalty, str):
            self.penalty_ = create_penalty(
                self.penalty, 
                lambda1=self.lambda1, 
                lambda2=self.lambda2
            )
        elif isinstance(self.penalty, PenaltyBase):
            self.penalty_ = self.penalty
        else:
            raise ValueError("Penalty must be None, string, or PenaltyBase instance")
    
    def _add_intercept(self, X: np.ndarray) -> np.ndarray:
        """Add intercept column to feature matrix."""
        return np.column_stack([np.ones(X.shape[0]), X])
    
    def _standardize_features(self, X: np.ndarray, fit: bool = True) -> np.ndarray:
        """Standardize features."""
        if fit:
            self.scaler_ = StandardScaler()
            return self.scaler_.fit_transform(X)
        else:
            return self.scaler_.transform(X)
    
    def _compute_gradient(self, X: np.ndarray, y: np.ndarray, coef: np.ndarray) -> np.ndarray:
        """Compute gradient of the negative log-likelihood."""
        # Linear predictor
        eta = X @ coef
        
        # Mean prediction
        mu = self.family_.inverse_link(eta)
        
        # Gradient of negative log-likelihood
        residuals = y - mu
        gradient = -X.T @ residuals
        
        return gradient
    
    def _compute_loss(self, X: np.ndarray, y: np.ndarray, coef: np.ndarray) -> float:
        """Compute total loss (negative log-likelihood + penalty)."""
        # Linear predictor
        eta = X @ coef
        
        # Mean prediction
        mu = self.family_.inverse_link(eta)
        
        # Negative log-likelihood
        nll = -self.family_.log_likelihood(y, mu)
        
        # Add penalty
        if self.penalty_ is not None:
            # Don't penalize intercept
            coef_without_intercept = coef[1:] if self.fit_intercept else coef
            penalty = self.penalty_(coef_without_intercept)
        else:
            penalty = 0.0
        
        return nll + penalty
    
    def fit(self, X: np.ndarray, y: np.ndarray) -> 'GLM':
        """
        Fit the GLM model.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target values.
            
        Returns
        -------
        self : object
            Returns self.
        """
        # Validate input
        X = check_array(X)
        y = check_array(y, ensure_2d=False)
        check_consistent_length(X, y)
        
        # Store original shapes
        self.n_features_in_ = X.shape[1]
        
        # Standardize features
        if self.standardize:
            X = self._standardize_features(X, fit=True)
        
        # Add intercept
        if self.fit_intercept:
            X = self._add_intercept(X)
        
        # Initialize coefficients
        n_features = X.shape[1]
        coef_init = np.random.normal(0, 0.1, n_features)
        
        # Define objective function for optimizer
        def objective(coef):
            return self._compute_loss(X, y, coef)
        
        def gradient(coef):
            grad = self._compute_gradient(X, y, coef)
            
            # Add penalty gradient
            if self.penalty_ is not None:
                # Don't penalize intercept
                if self.fit_intercept:
                    penalty_grad = np.zeros_like(grad)
                    penalty_grad[1:] = self.penalty_.gradient(coef[1:])
                else:
                    penalty_grad = self.penalty_.gradient(coef)
                grad += penalty_grad
            
            return grad
        
        # Optimize
        self.coef_, self.loss_history_ = self.optimizer_.optimize(
            objective=objective,
            gradient=gradient,
            x0=coef_init,
            verbose=self.verbose
        )
        
        # Store intercept and coefficients separately
        if self.fit_intercept:
            self.intercept_ = self.coef_[0]
            self.coef_ = self.coef_[1:]
        else:
            self.intercept_ = 0.0
        
        return self
    
    def predict(self, X: np.ndarray) -> np.ndarray:
        """
        Predict using the GLM model.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.
            
        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted values.
        """
        check_is_fitted(self)
        X = check_array(X)
        
        # Standardize features
        if self.standardize:
            X = self._standardize_features(X, fit=False)
        
        # Compute linear predictor
        eta = X @ self.coef_ + self.intercept_
        
        # Apply inverse link function
        return self.family_.inverse_link(eta)
    
    def score(self, X: np.ndarray, y: np.ndarray) -> float:
        """
        Return the coefficient of determination R^2 of the prediction.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test samples.
        y : array-like of shape (n_samples,)
            True values.
            
        Returns
        -------
        score : float
            R^2 score.
        """
        y_pred = self.predict(X)
        
        # Compute deviance-based score
        deviance = self.family_.deviance(y, y_pred)
        null_deviance = self.family_.deviance(y, np.full_like(y, np.mean(y)))
        
        # Pseudo R-squared
        if null_deviance == 0:
            return 1.0
        
        return 1 - (deviance / null_deviance)


# Convenience functions for creating specific GLM models
def PoissonGLM(**kwargs) -> GLM:
    """Create a Poisson GLM with log link."""
    return GLM(family='poisson', **kwargs)


def GaussianGLM(**kwargs) -> GLM:
    """Create a Gaussian GLM with identity link."""
    return GLM(family='gaussian', **kwargs)


def BinomialGLM(**kwargs) -> GLM:
    """Create a Binomial GLM with logit link."""
    return GLM(family='binomial', **kwargs)