"""
Poisson regression with AMGD optimization.
"""

import numpy as np
from scipy import special
from typing import Optional, Union

from amgd.models.base import BaseGLM
from amgd.utils.validation import check_array, check_is_fitted


class PoissonRegressor(BaseGLM):
    """
    Poisson regression with various optimization algorithms.
    
    This model assumes the target variable follows a Poisson distribution
    and uses a log link function.
    
    Parameters
    ----------
    optimizer : str or OptimizerBase, default='amgd'
        Optimization algorithm.
    penalty : str, default='none'
        Regularization penalty: 'l1', 'l2', 'elasticnet', or 'none'.
    lambda1 : float, default=0.0
        L1 regularization strength.
    lambda2 : float, default=0.0
        L2 regularization strength.
    fit_intercept : bool, default=True
        Whether to fit an intercept term.
    max_iter : int, default=1000
        Maximum number of optimization iterations.
    tol : float, default=1e-6
        Tolerance for convergence.
    warm_start : bool, default=False
        Whether to reuse previous solution as initialization.
    verbose : bool, default=False
        Whether to print progress.
    random_state : int or None, default=None
        Random seed for reproducibility.
    
    Attributes
    ----------
    coef_ : ndarray of shape (n_features,)
        Fitted coefficients.
    intercept_ : float
        Fitted intercept term.
    n_iter_ : int
        Number of iterations performed.
    loss_history_ : ndarray
        History of loss values during optimization.
    """
    
    def _compute_loss(self, X: np.ndarray, y: np.ndarray, coef: np.ndarray) -> float:
        """Compute negative Poisson log-likelihood."""
        linear_pred = X @ coef
        # Clip for numerical stability
        linear_pred = np.clip(linear_pred, -20, 20)
        mu = np.exp(linear_pred)
        
        # Negative log-likelihood
        log_likelihood = np.sum(y * linear_pred - mu - special.gammaln(y + 1))
        return -log_likelihood
        
    def _compute_gradient(self, X: np.ndarray, y: np.ndarray, coef: np.ndarray) -> np.ndarray:
        """Compute gradient of negative log-likelihood."""
        linear_pred = X @ coef
        linear_pred = np.clip(linear_pred, -20, 20)
        mu = np.exp(linear_pred)
        
        # Gradient
        residuals = mu - y
        gradient = X.T @ residuals
        return gradient
        
    def fit(self, X, y):
        """
        Fit Poisson regression model using simple gradient descent.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Training data.
        y : array-like of shape (n_samples,)
            Target counts.
            
        Returns
        -------
        self : object
            Returns self.
        """
        X = check_array(X)
        y = check_array(y, ensure_2d=False)

        n_samples, n_features = X.shape

        if self.fit_intercept:
            # Add intercept column
            X = np.hstack([np.ones((n_samples, 1)), X])
            n_features += 1

        # Initialize coefficients (including intercept if any)
        if self.warm_start and hasattr(self, "coef_"):
            coef = np.hstack(([self.intercept_] if self.fit_intercept else [] , self.coef_)) 
        else:
            coef = np.zeros(n_features)

        prev_loss = np.inf
        learning_rate = 0.01  # fixed step size for demonstration
        self.loss_history_ = []

        for iteration in range(self.max_iter):
            linear_pred = X @ coef
            linear_pred = np.clip(linear_pred, -20, 20)
            mu = np.exp(linear_pred)

            gradient = X.T @ (mu - y) / n_samples

            # Add regularization gradients
            if self.penalty in ['l2', 'elasticnet']:
                gradient += self.lambda2 * coef
            if self.penalty in ['l1', 'elasticnet']:
                gradient += self.lambda1 * np.sign(coef)

            # Update coefficients
            coef -= learning_rate * gradient

            # Compute loss
            loss = -np.sum(y * linear_pred - mu - special.gammaln(y + 1)) / n_samples
            self.loss_history_.append(loss)

            if self.verbose:
                print(f"Iteration {iteration+1}, Loss: {loss}")

            # Check convergence
            if abs(prev_loss - loss) < self.tol:
                break
            prev_loss = loss

        # Set attributes
        if self.fit_intercept:
            self.intercept_ = coef[0]
            self.coef_ = coef[1:]
        else:
            self.intercept_ = 0.0
            self.coef_ = coef

        self.n_iter_ = iteration + 1

        return self
        
    def predict(self, X):
        """
        Predict expected counts for samples in X.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Samples.
            
        Returns
        -------
        y_pred : ndarray of shape (n_samples,)
            Predicted expected counts.
        """
        check_is_fitted(self)
        X = check_array(X, accept_sparse=True)
        
        linear_pred = X @ self.coef_
        if self.fit_intercept:
            linear_pred += self.intercept_
            
        # Clip for numerical stability
        linear_pred = np.clip(linear_pred, -20, 20)
        return np.exp(linear_pred)
        
    def score(self, X, y):
        """
        Compute the mean Poisson deviance on the given test data.
        
        Parameters
        ----------
        X : array-like of shape (n_samples, n_features)
            Test samples.
        y : array-like of shape (n_samples,)
            True values for X.
            
        Returns
        -------
        score : float
            Mean Poisson deviance (negative is better).
        """
        from amgd.utils.metrics import poisson_deviance
        y_pred = self.predict(X)
        return -poisson_deviance(y, y_pred)
