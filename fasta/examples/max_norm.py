"""Solve the max-norm problem, min_X <S, X X^T>, ||X||_{2,inf}^2 <= 1 using the FASTA solver.

The NP-complete max-cut problem can be relaxed into this form. The inequality constrains the maximum L2-norm of any row
of X.
"""

import numpy as np
from numpy import linalg as la
from scipy.spatial.distance import pdist, squareform
from matplotlib import pyplot as plt
from typing import Tuple

from fasta import fasta, plots, Convergence
from fasta.examples import ExampleProblem, test_modes
from fasta.linalg import LinearOperator, Matrix

__author__ = "Noah Singer"

__all__ = ["MaxNormProblem"]


class MaxNormProblem(ExampleProblem):
    def __init__(self, points: Matrix, mu: float, sigma: float=0.1, delta: float=0.01):
        """Create an instance of the max-norm problem.

        :param points: The points to cluster
        :param mu: The regularization parameter
        :param sigma: The standard deviation of the similarity metric (default: 0.1)
        :param delta: The balance parameter for the segmentation (default: 0.01)
        """
        super(ExampleProblem, self).__init__()

        self.points = points
        self.mu = mu

        # Build the similarity matrix from the distances between points
        distances = squareform(pdist(points))

        # Build the edge weight matrix
        self.S = delta - np.exp(-distances**2 / sigma**2 / 2)

    def solve(self, X0: Matrix, fasta_options: dict=None) -> Tuple[Matrix, Convergence]:
        """Solve the max-norm problem.

        :param X0: An initial guess for the solution
        :param fasta_options: Options for the FASTA algorithm (default: None)
        :return: The problem's computed solution and information on FASTA's convergence
        """
        f = lambda X: np.sum(self.S * (X @ X.T))
        gradf = lambda X: (self.S + self.S.T) @ X
        g = lambda X: 0

        def proxg(X, t):
            norms = la.norm(X, axis=1)

            # Shrink the norms that are too big, and ensure we don't divide by zero
            scale = np.maximum(norms, self.mu) + (norms == 0)

            return self.mu * X / scale[:,np.newaxis]

        X = fasta(None, None, f, gradf, g, proxg, X0, **(fasta_options or {}))

        return X.solution, X

    @staticmethod
    def construct(N: int=2000, D: int=2, noise: float=0.15, dx: Tuple[float, float]=(1, 0.5), K: int=10,
                  mu: int=1.0) -> Tuple["MaxNormProblem", Matrix]:
        """Construct a sample max-norm problem by creating a two-moons segmentation dataset, converting it to a weighted graph, and then performing max-norm regularization on its adjacency matrix.

        :param N: The number of observations in the two-moons dataset (default: 2000)
        :param D: The dimensionality of the observation vectors (default: 2)
        :param noise: The noise level in the two-moons points (default: 0.15)
        :param dx: The separation between the two moons in the x and y directions (default: (1, 0.5))
        :param K: The maximum allowed rank of the factorization (default: 10)
        :param mu: The regularization parameter (default: 1.0)
        :return: An example of this type of problem and a good initial guess for its solution
        """
        # Points on a circle
        theta = np.arange(0, N) / N * 2 * np.pi

        # Embed circle in D dimensions
        points = np.zeros((N, D))
        points[:,0] = np.cos(theta)
        points[:,1] = np.sin(theta)

        # Separate out the top moon
        points[:N//2,:2] -= dx

        # Add noise
        points += noise * np.random.randn(N, D)

        # An initial guess for the iterate
        X0 = np.random.randn(N, K) / np.sqrt(K) / 10

        return MaxNormProblem(points, mu), X0

    def plot(self, solution: Matrix) -> None:
        """Plot the results of the computed classifier on the two-moons dataset.

        :param solution: The problem's computed solution
        """
        labels = np.sign(adaptive[0] @ np.random.randn(solution.shape[1]))

        figure, axes = plt.subplots()
        figure.suptitle("Max-Norm Optimization")

        axes.set_xlabel("Predicted value")
        axes.set_ylabel("Frequency")

        axes.plot(self.points[labels < 0, 0], self.points[labels < 0, 1], 'b.')
        axes.plot(self.points[labels > 0, 0], self.points[labels > 0, 1], 'r.')


if __name__ == "__main__":
    problem, X0 = MaxNormProblem.construct()
    print("Constructed max-norm problem.")

    adaptive, accelerated, plain = test_modes(problem, X0)

    plots.plot_convergence("Max-Norm Problem", [adaptive[1], accelerated[1], plain[1]], ["Adaptive", "Accelerated", "Plain"])
    problem.plot(adaptive[0])
    plt.show()
