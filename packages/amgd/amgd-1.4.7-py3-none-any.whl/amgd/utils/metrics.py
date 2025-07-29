"""Evaluation metrics for Poisson regression and other models."""

import numpy as np
from typing import Union, Dict, Any
from scipy import special


def poisson_deviance(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Poisson deviance.
    
    Parameters
    ----------
    y_true : array-like
        True target values (counts).
    y_pred : array-like
        Predicted values (rates).
        
    Returns
    -------
    float
        Poisson deviance.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    # Avoid log(0) by adding small epsilon
    y_pred = np.maximum(y_pred, 1e-8)
    y_true_safe = np.maximum(y_true, 1e-8)
    
    # Poisson deviance formula
    deviance = 2 * np.sum(y_true * np.log(y_true_safe / y_pred) - (y_true - y_pred))
    
    return deviance


def mean_absolute_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Absolute Error.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
        
    Returns
    -------
    float
        Mean Absolute Error.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    return np.mean(np.abs(y_true - y_pred))


def mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Mean Squared Error.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
        
    Returns
    -------
    float
        Mean Squared Error.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    return np.mean((y_true - y_pred) ** 2)


def root_mean_squared_error(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate Root Mean Squared Error.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
        
    Returns
    -------
    float
        Root Mean Squared Error.
    """
    return np.sqrt(mean_squared_error(y_true, y_pred))


def poisson_log_likelihood(beta: np.ndarray, X: np.ndarray, y: np.ndarray) -> float:
    """
    Calculate negative Poisson log-likelihood.
    
    Parameters
    ----------
    beta : array-like
        Coefficient vector.
    X : array-like
        Feature matrix.
    y : array-like
        Target values (counts).
        
    Returns
    -------
    float
        Negative Poisson log-likelihood.
    """
    linear_pred = X @ beta
    linear_pred = np.clip(linear_pred, -20, 20)
    mu = np.exp(linear_pred)
    
    log_likelihood = np.sum(y * linear_pred - mu - special.gammaln(y + 1))
    
    return -log_likelihood  # Negative because we want to minimize


def evaluate_model(beta: np.ndarray, X: np.ndarray, y: np.ndarray, 
                  target_name: str = 'Target') -> Dict[str, Any]:
    """
    Evaluate model performance for a single target.
    
    Parameters
    ----------
    beta : array-like
        Coefficient vector.
    X : array-like
        Feature matrix.
    y : array-like
        Target values (counts).
    target_name : str
        Name of the target variable.
        
    Returns
    -------
    dict
        Dictionary containing evaluation metrics.
    """
    linear_pred = X @ beta
    linear_pred = np.clip(linear_pred, -20, 20)
    y_pred = np.exp(linear_pred)
    
    # Mean Absolute Error
    mae = mean_absolute_error(y, y_pred)
    
    # Root Mean Squared Error
    rmse = root_mean_squared_error(y, y_pred)
    
    # Mean Poisson Deviance
    eps = 1e-10  # To avoid log(0)
    deviance = 2 * np.sum(y * np.log((y + eps) / (y_pred + eps)) - (y - y_pred))
    mean_deviance = deviance / len(y)
    
    # Sparsity metrics
    non_zero_coeffs = np.sum(np.abs(beta) > 1e-6)
    sparsity = 1.0 - (non_zero_coeffs / len(beta))
    
    results = {
        'MAE': mae,
        'RMSE': rmse,
        'Mean Deviance': mean_deviance,
        'Non-zero coeffs': non_zero_coeffs,
        'Sparsity': sparsity
    }
    
    return results


def calculate_r_squared(y_true: np.ndarray, y_pred: np.ndarray) -> float:
    """
    Calculate R-squared (coefficient of determination).
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
        
    Returns
    -------
    float
        R-squared value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    ss_res = np.sum((y_true - y_pred) ** 2)
    ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
    
    # Avoid division by zero
    if ss_tot == 0:
        return 0.0
    
    r2 = 1 - (ss_res / ss_tot)
    return r2


def calculate_adjusted_r_squared(y_true: np.ndarray, y_pred: np.ndarray, 
                               n_features: int) -> float:
    """
    Calculate adjusted R-squared.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
    n_features : int
        Number of features in the model.
        
    Returns
    -------
    float
        Adjusted R-squared value.
    """
    r2 = calculate_r_squared(y_true, y_pred)
    n = len(y_true)
    
    if n - n_features - 1 <= 0:
        return r2
    
    adj_r2 = 1 - (1 - r2) * (n - 1) / (n - n_features - 1)
    return adj_r2


def calculate_aic(y_true: np.ndarray, y_pred: np.ndarray, n_params: int) -> float:
    """
    Calculate Akaike Information Criterion (AIC) for Poisson regression.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
    n_params : int
        Number of parameters in the model.
        
    Returns
    -------
    float
        AIC value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    
    # Calculate log-likelihood for Poisson
    y_pred = np.maximum(y_pred, 1e-8)  # Avoid log(0)
    log_likelihood = np.sum(y_true * np.log(y_pred) - y_pred - special.gammaln(y_true + 1))
    
    aic = 2 * n_params - 2 * log_likelihood
    return aic


def calculate_bic(y_true: np.ndarray, y_pred: np.ndarray, n_params: int) -> float:
    """
    Calculate Bayesian Information Criterion (BIC) for Poisson regression.
    
    Parameters
    ----------
    y_true : array-like
        True target values.
    y_pred : array-like
        Predicted values.
    n_params : int
        Number of parameters in the model.
        
    Returns
    -------
    float
        BIC value.
    """
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    n = len(y_true)
    
    # Calculate log-likelihood for Poisson
    y_pred = np.maximum(y_pred, 1e-8)  # Avoid log(0)
    log_likelihood = np.sum(y_true * np.log(y_pred) - y_pred - special.gammaln(y_true + 1))
    
    bic = np.log(n) * n_params - 2 * log_likelihood
    return bic


# Alias functions for consistency with sklearn
mae = mean_absolute_error
mse = mean_squared_error
rmse = root_mean_squared_error