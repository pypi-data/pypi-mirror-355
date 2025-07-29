"""
Core optimization algorithms including AMGD, Adam, and AdaGrad.
"""

import numpy as np
from typing import Optional, Tuple, Dict, Any, Callable
from abc import ABC, abstractmethod
import time

from amgd.core.penalties import PenaltyBase, L1Penalty, ElasticNetPenalty
from amgd.core.convergence import ConvergenceCriterion, RelativeChangeCriterion
from amgd.utils.validation import check_array, check_consistent_length

class OptimizerBase(ABC):
    """Base class for all optimizers."""

    def __init__(
        self,
        alpha: float = 0.01,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
        random_state: Optional[int] = None
    ):
        self.alpha = alpha
        self.max_iter = max_iter
        self.tol = tol
        self.verbose = verbose
        self.random_state = random_state

        # Track optimization history
        self.loss_history_ = []
        self.gradient_norm_history_ = []
        self.n_iter_ = 0
        self.converged_ = False

    @abstractmethod
    def minimize(
        self,
        objective: Callable,
        gradient: Callable,
        x0: np.ndarray,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        """Minimize the objective function."""
        pass

    def _initialize_state(self, n_features: int) -> None:
        if self.random_state is not None:
            np.random.seed(self.random_state)

    def optimize(
        self,
        objective: Callable,
        gradient: Callable,
        x0: np.ndarray,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        return self.minimize(objective, gradient, x0, **kwargs)


class AMGDOptimizer(OptimizerBase):
    """Adaptive Momentum Gradient Descent optimizer."""

    def __init__(
        self,
        alpha: float = 0.01,
        beta1: float = 0.9,
        beta2: float = 0.999,
        T: float = 20.0,
        eta: float = 0.0001,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
        random_state: Optional[int] = None
    ):
        super().__init__(alpha, max_iter, tol, verbose, random_state)
        self.beta1 = beta1
        self.beta2 = beta2
        self.T = T
        self.eta = eta
        self.epsilon = epsilon

    def minimize(
        self,
        objective: Callable,
        gradient: Callable,
        x0: np.ndarray,
        penalty: Optional[PenaltyBase] = None,
        convergence_criterion: Optional[ConvergenceCriterion] = None,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        n_features = len(x0)
        x = x0.copy()
        m = np.zeros(n_features)
        v = np.zeros(n_features)

        if convergence_criterion is None:
            convergence_criterion = RelativeChangeCriterion(tol=self.tol)

        self.loss_history_ = []
        self.gradient_norm_history_ = []
        nonzero_history = []
        start_time = time.time()

        for t in range(1, self.max_iter + 1):
            alpha_t = self.alpha / (1 + self.eta * t)
            grad = gradient(x)
            grad = np.clip(grad, -self.T, self.T)

            m = self.beta1 * m + (1 - self.beta1) * grad
            v = self.beta2 * v + (1 - self.beta2) * (grad ** 2)
            m_hat = m / (1 - self.beta1 ** t)
            v_hat = v / (1 - self.beta2 ** t)

            x = x - alpha_t * m_hat / (np.sqrt(v_hat) + self.epsilon)

            if penalty is not None and isinstance(penalty, (L1Penalty, ElasticNetPenalty)):
                denom = np.abs(x) + 0.1
                threshold = alpha_t * penalty.lambda1 / denom
                x = np.sign(x) * np.maximum(np.abs(x) - threshold, 0)

            loss = objective(x)
            if penalty is not None:
                loss += penalty(x)

            self.loss_history_.append(loss)
            self.gradient_norm_history_.append(np.linalg.norm(grad))
            nonzero_history.append(np.sum(np.abs(x) > 1e-6))

            if callback is not None:
                callback(x, t, loss)

            if self.verbose and t % 100 == 0:
                print(f"Iteration {t}: Loss = {loss:.6f}, "
                      f"||grad|| = {np.linalg.norm(grad):.6f}, "
                      f"Non-zero = {nonzero_history[-1]}")

            if convergence_criterion(loss, self.loss_history_):
                self.converged_ = True
                self.n_iter_ = t
                if self.verbose:
                    print(f"Converged at iteration {t}")
                break

        runtime = time.time() - start_time
        info = {
            'converged': self.converged_,
            'n_iter': self.n_iter_ if self.converged_ else self.max_iter,
            'loss_history': np.array(self.loss_history_),
            'gradient_norm_history': np.array(self.gradient_norm_history_),
            'nonzero_history': np.array(nonzero_history),
            'runtime': runtime,
            'final_loss': self.loss_history_[-1],
        }

        return x, info


class AdamOptimizer(OptimizerBase):
    """Adam optimizer implementation."""

    def __init__(
        self,
        alpha: float = 0.001,
        beta1: float = 0.9,
        beta2: float = 0.999,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
        random_state: Optional[int] = None
    ):
        super().__init__(alpha, max_iter, tol, verbose, random_state)
        self.beta1 = beta1
        self.beta2 = beta2
        self.epsilon = epsilon

    def minimize(
        self,
        objective: Callable,
        gradient: Callable,
        x0: np.ndarray,
        penalty: Optional[PenaltyBase] = None,
        convergence_criterion: Optional[ConvergenceCriterion] = None,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        n_features = len(x0)
        x = x0.copy()
        m = np.zeros(n_features)
        v = np.zeros(n_features)

        if convergence_criterion is None:
            convergence_criterion = RelativeChangeCriterion(tol=self.tol)

        self.loss_history_ = []
        self.gradient_norm_history_ = []
        nonzero_history = []
        start_time = time.time()

        for t in range(1, self.max_iter + 1):
            grad = gradient(x)
            m = self.beta1 * m + (1 - self.beta1) * grad
            v = self.beta2 * v + (1 - self.beta2) * (grad ** 2)

            m_hat = m / (1 - self.beta1 ** t)
            v_hat = v / (1 - self.beta2 ** t)

            x = x - self.alpha * m_hat / (np.sqrt(v_hat) + self.epsilon)

            if penalty is not None and isinstance(penalty, (L1Penalty, ElasticNetPenalty)):
                x = np.sign(x) * np.maximum(np.abs(x) - penalty.lambda1 * self.alpha, 0)

            loss = objective(x)
            if penalty is not None:
                loss += penalty(x)

            self.loss_history_.append(loss)
            self.gradient_norm_history_.append(np.linalg.norm(grad))
            nonzero_history.append(np.sum(np.abs(x) > 1e-6))

            if callback is not None:
                callback(x, t, loss)

            if self.verbose and t % 100 == 0:
                print(f"Iteration {t}: Loss = {loss:.6f}, "
                      f"||grad|| = {np.linalg.norm(grad):.6f}")

            if convergence_criterion(loss, self.loss_history_):
                self.converged_ = True
                self.n_iter_ = t
                if self.verbose:
                    print(f"Converged at iteration {t}")
                break

        runtime = time.time() - start_time
        info = {
            'converged': self.converged_,
            'n_iter': self.n_iter_ if self.converged_ else self.max_iter,
            'loss_history': np.array(self.loss_history_),
            'gradient_norm_history': np.array(self.gradient_norm_history_),
            'nonzero_history': np.array(nonzero_history),
            'runtime': runtime,
            'final_loss': self.loss_history_[-1],
        }

        return x, info


class AdaGradOptimizer(OptimizerBase):
    """AdaGrad optimizer implementation."""

    def __init__(
        self,
        alpha: float = 0.01,
        epsilon: float = 1e-8,
        max_iter: int = 1000,
        tol: float = 1e-6,
        verbose: bool = False,
        random_state: Optional[int] = None
    ):
        super().__init__(alpha, max_iter, tol, verbose, random_state)
        self.epsilon = epsilon

    def minimize(
        self,
        objective: Callable,
        gradient: Callable,
        x0: np.ndarray,
        penalty: Optional[PenaltyBase] = None,
        convergence_criterion: Optional[ConvergenceCriterion] = None,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> Tuple[np.ndarray, Dict[str, Any]]:
        n_features = len(x0)
        x = x0.copy()
        G = np.zeros(n_features)

        if convergence_criterion is None:
            convergence_criterion = RelativeChangeCriterion(tol=self.tol)

        self.loss_history_ = []
        self.gradient_norm_history_ = []
        nonzero_history = []
        start_time = time.time()

        for t in range(1, self.max_iter + 1):
            grad = gradient(x)
            G += grad ** 2

            x = x - self.alpha * grad / (np.sqrt(G) + self.epsilon)

            if penalty is not None and isinstance(penalty, (L1Penalty, ElasticNetPenalty)):
                x = np.sign(x) * np.maximum(
                    np.abs(x) - penalty.lambda1 * self.alpha / (np.sqrt(G) + self.epsilon),
                    0
                )

            loss = objective(x)
            if penalty is not None:
                loss += penalty(x)

            self.loss_history_.append(loss)
            self.gradient_norm_history_.append(np.linalg.norm(grad))
            nonzero_history.append(np.sum(np.abs(x) > 1e-6))

            if callback is not None:
                callback(x, t, loss)

            if self.verbose and t % 100 == 0:
                print(f"Iteration {t}: Loss = {loss:.6f}, "
                      f"||grad|| = {np.linalg.norm(grad):.6f}")

            if convergence_criterion(loss, self.loss_history_):
                self.converged_ = True
                self.n_iter_ = t
                if self.verbose:
                    print(f"Converged at iteration {t}")
                break

        runtime = time.time() - start_time
        info = {
            'converged': self.converged_,
            'n_iter': self.n_iter_ if self.converged_ else self.max_iter,
            'loss_history': np.array(self.loss_history_),
            'gradient_norm_history': np.array(self.gradient_norm_history_),
            'nonzero_history': np.array(nonzero_history),
            'runtime': runtime,
            'final_loss': self.loss_history_[-1],
        }

        return x, info
