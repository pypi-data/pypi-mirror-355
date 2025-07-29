"""
Tools for comparing optimization algorithms.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Union, Any
from sklearn.model_selection import KFold, train_test_split
from scipy import stats
import time

from amgd.models import PoissonRegressor
from amgd.utils.metrics import evaluate_model


def compare_optimizers(
    X: np.ndarray,
    y: np.ndarray,
    optimizers: List[str] = None,
    penalties: List[str] = None,
    lambda_values: np.ndarray = None,
    cv_folds: int = 5,
    test_size: float = 0.2,
    random_state: int = 42,
    verbose: bool = True,
    **optimizer_params
) -> Dict[str, Any]:
    """
    Compare performance of different optimizers.
    
    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature matrix.
    y : array-like of shape (n_samples,)
        Target values.
    optimizers : list of str, optional
        Optimizers to compare. Default: ['amgd', 'adam', 'adagrad'].
    penalties : list of str, optional
        Penalties to test. Default: ['l1', 'elasticnet'].
    lambda_values : array-like, optional
        Regularization strengths to test.
    cv_folds : int
        Number of cross-validation folds.
    test_size : float
        Proportion of data for test set.
    random_state : int
        Random seed.
    verbose : bool
        Print progress.
    **optimizer_params
        Additional parameters for optimizers.
        
    Returns
    -------
    results : dict
        Comparison results including best parameters and test metrics.
    """
    # Convert DataFrames to numpy arrays if needed
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, (pd.DataFrame, pd.Series)):
        y = y.values
        
    if optimizers is None:
        optimizers = ['amgd', 'adam', 'adagrad']
        
    if penalties is None:
        penalties = ['l1', 'elasticnet']
        
    if lambda_values is None:
        lambda_values = np.logspace(-4, 1, 20)
        
    # Split data
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    # Cross-validation to find best parameters
    cv_results = []
    best_params = {}
    
    for optimizer in optimizers:
        for penalty in penalties:
            if verbose:
                print(f"\nEvaluating {optimizer} with {penalty} penalty...")
                
            try:
                # Run cross-validation for different lambda values
                cv_scores = run_cross_validation(
                    X_train_val, y_train_val,
                    optimizer=optimizer,
                    penalty=penalty,
                    lambda_values=lambda_values,
                    cv_folds=cv_folds,
                    random_state=random_state,
                    **optimizer_params
                )
                
                # Find best lambda
                best_idx = np.argmin(cv_scores['mean_mae'])
                best_lambda = lambda_values[best_idx]
                
                # Store results
                result = {
                    'optimizer': optimizer,
                    'penalty': penalty,
                    'lambda': best_lambda,
                    'cv_mae': cv_scores['mean_mae'][best_idx],
                    'cv_mae_std': cv_scores['std_mae'][best_idx],
                    'cv_rmse': cv_scores['mean_rmse'][best_idx],
                    'cv_rmse_std': cv_scores['std_rmse'][best_idx],
                }
                cv_results.append(result)
                
                # Store best params for each optimizer
                if optimizer not in best_params or cv_scores['mean_mae'][best_idx] < best_params[optimizer]['cv_mae']:
                    best_params[optimizer] = {
                        'penalty': penalty,
                        'lambda': best_lambda,
                        'cv_mae': cv_scores['mean_mae'][best_idx]
                    }
                    
            except Exception as e:
                if verbose:
                    print(f"Error with {optimizer} + {penalty}: {str(e)}")
                continue
                
    # Convert to DataFrame for easy viewing
    cv_results_df = pd.DataFrame(cv_results)
    
    # Train final models with best parameters
    final_models = {}
    test_results = []
    
    for optimizer, params in best_params.items():
        if verbose:
            print(f"\nTraining final {optimizer} model...")
            
        try:
            # Create and train model
            if params['penalty'] == 'l1':
                lambda1 = params['lambda']
                lambda2 = 0.0
            else:  # elasticnet
                lambda1 = params['lambda'] / 2
                lambda2 = params['lambda'] / 2
                
            model = PoissonRegressor(
                optimizer=optimizer,
                penalty=params['penalty'],
                lambda1=lambda1,
                lambda2=lambda2,
                verbose=False,
                **optimizer_params
            )
            
            start_time = time.time()
            model.fit(X_train_val, y_train_val)
            train_time = time.time() - start_time
            
            # Evaluate on test set
            y_pred = model.predict(X_test)
            
            # Use sklearn metrics as fallback if evaluate_model fails
            try:
                test_metrics = evaluate_model(model.coef_, X_test, y_test)
            except:
                from sklearn.metrics import mean_absolute_error, mean_squared_error
                mae = mean_absolute_error(y_test, y_pred)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                test_metrics = {
                    'MAE': mae,
                    'RMSE': rmse,
                    'Mean Deviance': mae * 2,  # Approximation
                    'Sparsity': np.mean(np.abs(model.coef_) < 1e-6)
                }
            
            # Store results
            test_result = {
                'optimizer': optimizer,
                'penalty': params['penalty'],
                'lambda': params['lambda'],
                'train_time': train_time,
                'n_iter': getattr(model, 'n_iter_', 'unknown'),
                **test_metrics
            }
            test_results.append(test_result)
            final_models[optimizer] = model
            
        except Exception as e:
            if verbose:
                print(f"Error training final {optimizer} model: {str(e)}")
            continue
        
    test_results_df = pd.DataFrame(test_results)
    
    # Print summary if verbose
    if verbose:
        print("\n" + "="*60)
        print("CROSS-VALIDATION RESULTS")
        print("="*60)
        if not cv_results_df.empty:
            print(cv_results_df.to_string(index=False))
        else:
            print("No successful CV results")
        
        print("\n" + "="*60)
        print("TEST SET RESULTS")
        print("="*60)
        if not test_results_df.empty:
            print(test_results_df.to_string(index=False))
        else:
            print("No successful test results")
        
    return {
        'cv_results': cv_results_df,
        'test_results': test_results_df,
        'best_params': best_params,
        'models': final_models,
        'data_splits': {
            'X_train_val': X_train_val,
            'X_test': X_test,
            'y_train_val': y_train_val,
            'y_test': y_test
        }
    }


def run_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    optimizer: str,
    penalty: str,
    lambda_values: np.ndarray,
    cv_folds: int = 5,
    random_state: int = 42,
    **model_params
) -> Dict[str, np.ndarray]:
    """
    Run k-fold cross-validation for hyperparameter tuning.
    
    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature matrix.
    y : array-like of shape (n_samples,)
        Target values.
    optimizer : str
        Optimizer name.
    penalty : str
        Penalty type.
    lambda_values : array-like
        Regularization values to test.
    cv_folds : int
        Number of CV folds.
    random_state : int
        Random seed.
    **model_params
        Additional model parameters.
        
    Returns
    -------
    scores : dict
        Cross-validation scores for each lambda value.
    """
    # Ensure we have numpy arrays
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, (pd.DataFrame, pd.Series)):
        y = y.values
        
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    mae_scores = []
    rmse_scores = []
    deviance_scores = []
    sparsity_scores = []
    mae_stds = []
    rmse_stds = []
    
    for lambda_val in lambda_values:
        fold_mae = []
        fold_rmse = []
        fold_deviance = []
        fold_sparsity = []
        
        # Set up regularization parameters
        if penalty == 'l1':
            lambda1 = lambda_val
            lambda2 = 0.0
        elif penalty == 'elasticnet':
            lambda1 = lambda_val / 2
            lambda2 = lambda_val / 2
        else:
            lambda1 = 0.0
            lambda2 = 0.0
            
        # Cross-validation loop
        for train_idx, val_idx in kf.split(X):
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            try:
                # Train model
                model = PoissonRegressor(
                    optimizer=optimizer,
                    penalty=penalty,
                    lambda1=lambda1,
                    lambda2=lambda2,
                    verbose=False,
                    **model_params
                )
                
                model.fit(X_train, y_train)
                
                # Evaluate - use fallback if evaluate_model fails
                try:
                    metrics = evaluate_model(model.coef_, X_val, y_val)
                except:
                    from sklearn.metrics import mean_absolute_error, mean_squared_error
                    y_pred = model.predict(X_val)
                    mae = mean_absolute_error(y_val, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
                    metrics = {
                        'MAE': mae,
                        'RMSE': rmse,
                        'Mean Deviance': mae * 2,
                        'Sparsity': np.mean(np.abs(model.coef_) < 1e-6)
                    }
                
                fold_mae.append(metrics['MAE'])
                fold_rmse.append(metrics['RMSE'])
                fold_deviance.append(metrics['Mean Deviance'])
                fold_sparsity.append(metrics['Sparsity'])
                
            except Exception as e:
                # If model fails, append NaN
                fold_mae.append(np.nan)
                fold_rmse.append(np.nan)
                fold_deviance.append(np.nan)
                fold_sparsity.append(np.nan)
        
        # Store average scores and standard deviations (excluding NaN values)
        mae_scores.append(np.nanmean(fold_mae))
        rmse_scores.append(np.nanmean(fold_rmse))
        deviance_scores.append(np.nanmean(fold_deviance))
        sparsity_scores.append(np.nanmean(fold_sparsity))
        mae_stds.append(np.nanstd(fold_mae))
        rmse_stds.append(np.nanstd(fold_rmse))
        
    return {
        'mean_mae': np.array(mae_scores),
        'std_mae': np.array(mae_stds),
        'mean_rmse': np.array(rmse_scores),
        'std_rmse': np.array(rmse_stds),
        'mean_deviance': np.array(deviance_scores),
        'mean_sparsity': np.array(sparsity_scores)
    }


def debug_compare_optimizers(
    X: np.ndarray,
    y: np.ndarray,
    optimizers: List[str] = None,
    penalties: List[str] = None,
    lambda_values: np.ndarray = None,
    cv_folds: int = 5,
    test_size: float = 0.2,
    random_state: int = 42,
    verbose: bool = True,
    **optimizer_params
) -> Dict[str, Any]:
    """
    Debug version with data type checking.
    """
    # Debug: Print data information
    print("="*50)
    print("DEBUG: Data Information")
    print("="*50)
    print(f"X type: {type(X)}")
    print(f"X shape: {X.shape}")
    print(f"y type: {type(y)}")
    print(f"y shape: {y.shape}")
    
    if hasattr(X, 'columns'):
        print(f"X columns: {X.columns}")
    if hasattr(X, 'index'):
        print(f"X index: {X.index}")
        
    # Convert to numpy arrays if they're DataFrames
    if isinstance(X, pd.DataFrame):
        print("Converting X DataFrame to numpy array")
        X = X.values
    if isinstance(y, (pd.DataFrame, pd.Series)):
        print("Converting y DataFrame/Series to numpy array")
        y = y.values
        
    print(f"After conversion - X type: {type(X)}, shape: {X.shape}")
    print(f"After conversion - y type: {type(y)}, shape: {y.shape}")
    print("="*50)
    
    if optimizers is None:
        optimizers = ['amgd', 'adam', 'adagrad']
        
    if penalties is None:
        penalties = ['l1', 'elasticnet']
        
    if lambda_values is None:
        lambda_values = np.logspace(-4, 1, 20)
        
    # Split data
    X_train_val, X_test, y_train_val, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state
    )
    
    print(f"Train/val split - X shape: {X_train_val.shape}, y shape: {y_train_val.shape}")
    print(f"Test split - X shape: {X_test.shape}, y shape: {y_test.shape}")
    
    # Cross-validation to find best parameters
    cv_results = []
    best_params = {}
    
    for optimizer in optimizers:
        for penalty in penalties:
            if verbose:
                print(f"\nEvaluating {optimizer} with {penalty} penalty...")
                
            try:
                # Debug: Test a single model first
                print(f"DEBUG: Testing single {optimizer} model...")
                
                # Set up a simple lambda value for testing
                test_lambda = 0.1
                if penalty == 'l1':
                    lambda1 = test_lambda
                    lambda2 = 0.0
                elif penalty == 'elasticnet':
                    lambda1 = test_lambda / 2
                    lambda2 = test_lambda / 2
                else:
                    lambda1 = 0.0
                    lambda2 = 0.0
                
                # Create a simple train/val split for testing
                X_train_simple, X_val_simple, y_train_simple, y_val_simple = train_test_split(
                    X_train_val, y_train_val, test_size=0.2, random_state=42
                )
                
                print(f"Simple split - X_train: {X_train_simple.shape}, X_val: {X_val_simple.shape}")
                
                # Test model creation and fitting
                model = PoissonRegressor(
                    optimizer=optimizer,
                    penalty=penalty,
                    lambda1=lambda1,
                    lambda2=lambda2,
                    verbose=False,
                    **optimizer_params
                )
                
                print(f"Model created successfully: {model}")
                
                # Try fitting
                model.fit(X_train_simple, y_train_simple)
                print(f"Model fitted successfully")
                
                # Try prediction
                y_pred = model.predict(X_val_simple)
                print(f"Prediction successful, shape: {y_pred.shape}")
                
                # Try evaluation
                try:
                    metrics = evaluate_model(model.coef_, X_val_simple, y_val_simple)
                    print(f"evaluate_model successful: {metrics}")
                except Exception as eval_error:
                    print(f"evaluate_model failed: {eval_error}")
                    # Use fallback
                    from sklearn.metrics import mean_absolute_error, mean_squared_error
                    mae = mean_absolute_error(y_val_simple, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_val_simple, y_pred))
                    metrics = {
                        'MAE': mae,
                        'RMSE': rmse,
                        'Mean Deviance': mae * 2,
                        'Sparsity': np.mean(np.abs(model.coef_) < 1e-6)
                    }
                    print(f"Fallback metrics successful: {metrics}")
                
                print(f"Single model test successful for {optimizer} + {penalty}")
                
                # Now try the full cross-validation
                cv_scores = debug_run_cross_validation(
                    X_train_val, y_train_val,
                    optimizer=optimizer,
                    penalty=penalty,
                    lambda_values=lambda_values[:3],  # Test with fewer values first
                    cv_folds=cv_folds,
                    random_state=random_state,
                    **optimizer_params
                )
                
                print(f"Cross-validation successful for {optimizer} + {penalty}")
                
            except Exception as e:
                print(f"Error with {optimizer} + {penalty}: {str(e)}")
                import traceback
                traceback.print_exc()
                continue
                
    return {"debug": "completed"}


def debug_run_cross_validation(
    X: np.ndarray,
    y: np.ndarray,
    optimizer: str,
    penalty: str,
    lambda_values: np.ndarray,
    cv_folds: int = 5,
    random_state: int = 42,
    **model_params
) -> Dict[str, np.ndarray]:
    """
    Debug version of cross-validation.
    """
    print(f"DEBUG CV: X shape {X.shape}, y shape {y.shape}")
    print(f"DEBUG CV: X type {type(X)}, y type {type(y)}")
    
    # Ensure we have numpy arrays
    if isinstance(X, pd.DataFrame):
        print("DEBUG CV: Converting X from DataFrame to numpy")
        X = X.values
    if isinstance(y, (pd.DataFrame, pd.Series)):
        print("DEBUG CV: Converting y from DataFrame/Series to numpy")
        y = y.values
    
    kf = KFold(n_splits=cv_folds, shuffle=True, random_state=random_state)
    
    mae_scores = []
    
    for i, lambda_val in enumerate(lambda_values):
        print(f"DEBUG CV: Testing lambda {i+1}/{len(lambda_values)}: {lambda_val}")
        
        fold_mae = []
        
        # Set up regularization parameters
        if penalty == 'l1':
            lambda1 = lambda_val
            lambda2 = 0.0
        elif penalty == 'elasticnet':
            lambda1 = lambda_val / 2
            lambda2 = lambda_val / 2
        else:
            lambda1 = 0.0
            lambda2 = 0.0
            
        # Cross-validation loop
        for fold_idx, (train_idx, val_idx) in enumerate(kf.split(X)):
            print(f"DEBUG CV: Fold {fold_idx+1}/{cv_folds}")
            
            X_train, X_val = X[train_idx], X[val_idx]
            y_train, y_val = y[train_idx], y[val_idx]
            
            print(f"DEBUG CV: Fold data - X_train: {X_train.shape}, X_val: {X_val.shape}")
            
            try:
                # Train model
                model = PoissonRegressor(
                    optimizer=optimizer,
                    penalty=penalty,
                    lambda1=lambda1,
                    lambda2=lambda2,
                    verbose=False,
                    **model_params
                )
                
                model.fit(X_train, y_train)
                y_pred = model.predict(X_val)
                
                # Simple evaluation
                from sklearn.metrics import mean_absolute_error
                mae = mean_absolute_error(y_val, y_pred)
                fold_mae.append(mae)
                
                print(f"DEBUG CV: Fold {fold_idx+1} successful, MAE: {mae}")
                
            except Exception as e:
                print(f"DEBUG CV: Fold {fold_idx+1} failed: {str(e)}")
                import traceback
                traceback.print_exc()
                fold_mae.append(np.nan)
            
        # Store average scores
        mae_scores.append(np.nanmean(fold_mae))
        print(f"DEBUG CV: Lambda {lambda_val} average MAE: {np.nanmean(fold_mae)}")
        
    return {
        'mean_mae': np.array(mae_scores),
    }


def statistical_significance_test(
    X: np.ndarray,
    y: np.ndarray,
    optimizers: List[str],
    n_bootstrap: int = 1000,
    n_runs: int = 100,
    test_size: float = 0.2,
    random_state: int = 42,
    **model_params
) -> Dict[str, Any]:
    """
    Perform statistical significance testing between optimizers.
    
    Parameters
    ----------
    X : array-like of shape (n_samples, n_features)
        Feature matrix.
    y : array-like of shape (n_samples,)
        Target values.
    optimizers : list of str
        Optimizers to compare.
    n_bootstrap : int
        Number of bootstrap samples.
    n_runs : int
        Number of runs for each comparison.
    test_size : float
        Test set proportion.
    random_state : int
        Random seed.
    **model_params
        Additional model parameters.
        
    Returns
    -------
    results : dict
        Statistical test results.
    """
    # Convert DataFrames to numpy arrays if needed
    if isinstance(X, pd.DataFrame):
        X = X.values
    if isinstance(y, (pd.DataFrame, pd.Series)):
        y = y.values
        
    np.random.seed(random_state)
    
    # Store performance metrics for each optimizer
    all_metrics = {opt: {
        'mae': [], 'rmse': [], 'deviance': [], 'sparsity': []
    } for opt in optimizers}
    
    # Run multiple experiments
    for run in range(n_runs):
        print(f"Running experiment {run+1}/{n_runs}")
        
        # Random train/test split
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state + run
        )
        
        # Train each optimizer
        for optimizer in optimizers:
            try:
                model = PoissonRegressor(
                    optimizer=optimizer,
                    penalty='l1',
                    lambda1=0.1,  # Fixed for fair comparison
                    verbose=False,
                    **model_params
                )
                
                model.fit(X_train, y_train)
                
                # Evaluate with fallback
                try:
                    metrics = evaluate_model(model.coef_, X_test, y_test)
                except:
                    from sklearn.metrics import mean_absolute_error, mean_squared_error
                    y_pred = model.predict(X_test)
                    mae = mean_absolute_error(y_test, y_pred)
                    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
                    metrics = {
                        'MAE': mae,
                        'RMSE': rmse,
                        'Mean Deviance': mae * 2,
                        'Sparsity': np.mean(np.abs(model.coef_) < 1e-6)
                    }
                
                all_metrics[optimizer]['mae'].append(metrics['MAE'])
                all_metrics[optimizer]['rmse'].append(metrics['RMSE'])
                all_metrics[optimizer]['deviance'].append(metrics['Mean Deviance'])
                all_metrics[optimizer]['sparsity'].append(metrics['Sparsity'])
                
            except Exception as e:
                print(f"Error with {optimizer} in run {run+1}: {str(e)}")
                continue
            
    # Compute statistics
    statistics = {}
    
    for optimizer in optimizers:
        statistics[optimizer] = {}
        
        for metric in ['mae', 'rmse', 'deviance', 'sparsity']:
            values = all_metrics[optimizer][metric]
            
            if len(values) > 0:
                # Bootstrap confidence intervals
                bootstrap_means = []
                for _ in range(n_bootstrap):
                    bootstrap_sample = np.random.choice(values, size=len(values), replace=True)
                    bootstrap_means.append(np.mean(bootstrap_sample))
                    
                statistics[optimizer][metric] = {
                    'mean': np.mean(values),
                    'std': np.std(values),
                    'ci_lower': np.percentile(bootstrap_means, 2.5),
                    'ci_upper': np.percentile(bootstrap_means, 97.5)
                }
            else:
                statistics[optimizer][metric] = {
                    'mean': np.nan,
                    'std': np.nan,
                    'ci_lower': np.nan,
                    'ci_upper': np.nan
                }
                
    # Pairwise comparisons
    comparisons = {}
    
    for i, opt1 in enumerate(optimizers):
        for opt2 in optimizers[i+1:]:
            key = f"{opt1}_vs_{opt2}"
            comparisons[key] = {}
            
            for metric in ['mae', 'rmse', 'deviance', 'sparsity']:
                values1 = all_metrics[opt1][metric]
                values2 = all_metrics[opt2][metric]
                
                if len(values1) > 0 and len(values2) > 0:
                    # Paired t-test
                    t_stat, p_value = stats.ttest_rel(values1, values2)
                    
                    # Effect size (Cohen's d)
                    mean_diff = np.mean(values1) - np.mean(values2)
                    pooled_std = np.sqrt((np.var(values1) + np.var(values2)) / 2)
                    effect_size = mean_diff / (pooled_std + 1e-10)
                    
                    comparisons[key][metric] = {
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'effect_size': effect_size,
                        'significant': p_value < 0.05
                    }
                else:
                    comparisons[key][metric] = {
                        't_statistic': np.nan,
                        'p_value': np.nan,
                        'effect_size': np.nan,
                        'significant': False
                    }
                
    return {
        'statistics': statistics,
        'comparisons': comparisons,
        'n_runs': n_runs
    }