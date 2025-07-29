"""Convergence criteria for optimization algorithms."""
import numpy as np
import matplotlib.pyplot as plt
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Union, Tuple
import seaborn as sns


def plot_convergence(
    loss_history: Union[List[float], np.ndarray],
    title: str = "Convergence Plot",
    xlabel: str = "Iteration", 
    ylabel: str = "Loss",
    log_scale: bool = True,
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """Plot convergence history of optimization."""
    fig, ax = plt.subplots(figsize=figsize)
    
    ax.plot(loss_history, linewidth=2)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    
    if log_scale:
        ax.set_yscale('log')
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_convergence_comparison(
    loss_histories: Dict[str, Union[List[float], np.ndarray]],
    title: str = "Convergence Comparison",
    xlabel: str = "Iteration",
    ylabel: str = "Loss",
    log_scale: bool = True,
    figsize: Tuple[int, int] = (12, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """Plot convergence comparison for multiple optimizers."""
    fig, ax = plt.subplots(figsize=figsize)
    
    colors = plt.cm.Set1(np.linspace(0, 1, len(loss_histories)))
    
    for i, (name, history) in enumerate(loss_histories.items()):
        iterations = range(len(history))
        ax.plot(iterations, history, color=colors[i], 
                linewidth=2, alpha=0.8, label=name)
    
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    if log_scale:
        ax.set_yscale('log')
    
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


def plot_learning_curves(
    train_scores: Union[List[float], np.ndarray],
    val_scores: Union[List[float], np.ndarray],
    train_sizes: Optional[Union[List[int], np.ndarray]] = None,
    title: str = "Learning Curves",
    xlabel: str = "Training Set Size",
    ylabel: str = "Score",
    figsize: Tuple[int, int] = (10, 6),
    save_path: Optional[str] = None
) -> plt.Figure:
    """Plot learning curves showing training and validation scores."""
    fig, ax = plt.subplots(figsize=figsize)
    
    if train_sizes is None:
        train_sizes = range(len(train_scores))
    
    ax.plot(train_sizes, train_scores, 'o-', color='blue', 
            linewidth=2, alpha=0.8, label='Training Score')
    ax.plot(train_sizes, val_scores, 'o-', color='red', 
            linewidth=2, alpha=0.8, label='Validation Score')
    
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=14, fontweight='bold')
    
    ax.grid(True, alpha=0.3)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(fontsize=10)
    
    plt.tight_layout()
    
    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
    
    return fig


class ConvergenceCriterion(ABC):
    """Abstract base class for convergence criteria."""
    
    def __init__(self, tol: float = 1e-6, patience: int = 5):  # Fixed: __init__ not **init**
        self.tol = tol
        self.patience = patience
        self.wait_count = 0
    
    @abstractmethod
    def __call__(self, current_loss: float, loss_history: List[float]) -> bool:  # Fixed: __call__ not **call**
        """Check if convergence criteria is met."""
        pass


class RelativeChangeCriterion(ConvergenceCriterion):
    """Convergence based on relative change in loss."""
    
    def __call__(self, current_loss: float, loss_history: List[float]) -> bool:  # Fixed: __call__ not **call**
        """Check convergence based on relative change."""
        if len(loss_history) < 2:
            return False
            
        prev_loss = loss_history[-2]
        rel_change = abs(current_loss - prev_loss) / (abs(prev_loss) + 1e-8)
        
        if rel_change < self.tol:
            self.wait_count += 1
        else:
            self.wait_count = 0
            
        return self.wait_count >= self.patience


class AbsoluteChangeCriterion(ConvergenceCriterion):
    """Convergence based on absolute change in loss."""
    
    def __call__(self, current_loss: float, loss_history: List[float]) -> bool:  # Fixed: __call__ not **call**
        """Check convergence based on absolute change."""
        if len(loss_history) < 2:
            return False
            
        prev_loss = loss_history[-2]
        abs_change = abs(current_loss - prev_loss)
        
        if abs_change < self.tol:
            self.wait_count += 1
        else:
            self.wait_count = 0
            
        return self.wait_count >= self.patience
