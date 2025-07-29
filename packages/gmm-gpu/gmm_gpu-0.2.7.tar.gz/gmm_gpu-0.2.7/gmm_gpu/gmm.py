"""
Provides a GMM class for fitting multiple instances of `Gaussian Mixture Models <https://en.wikipedia.org/wiki/Mixture_model#Gaussian_mixture_model>`_.

This may be useful if you have a large number of independent small problems and you want to fit a GMM on each one.
You can create a single large 3D tensor (three dimensional matrix) with the data for all your instances (i.e. a batch) and then
send the tensor to the GPU and process the whole batch in parallel. This would work best if all the instances have roughly the same number of points.

If you have a single big problem (one GMM instance with many points) that you want to fit using the GPU, maybe `Pomegranate <https://github.com/jmschrei/pomegranate>`_ would be a better option.

### Example usage:
Import pytorch and the GMM class
>>> from gmm_gpu.gmm import GMM
>>> import torch

Generate some test data:
We create a batch of 1000 instances, each
with 200 random points. Half of the points
are sampled from distribution centered at
the origin (0, 0) and the other half from
a distribution centered at (1.5, 1.5).
>>> X1 = torch.randn(1000, 100, 2)
>>> X2 = torch.randn(1000, 100, 2) + torch.tensor([1.5, 1.5])
>>> X = torch.cat([X1, X2], dim=1)

Fit the model
>>> gmm = GMM(n_components=2, device='cuda')
>>> gmm.fit(X)

Predict the components:
This will return a matrix with shape (1000, 200) where
each value is the predicted component for the point.
>>> gmm.predict(X)
"""

import torch
import numpy as np


class GMM:
    def __init__(self,
                 n_components,
                 max_iter=100,
                 device='cuda',
                 tol=0.001,
                 reg_covar=1e-6,
                 means_init=None,
                 weights_init=None,
                 precisions_init=None,
                 dtype=torch.float32,
                 random_seed=None):
        """
        Initialize a Gaussian Mixture Models instance to fit.

        Parameters
        ----------
        n_components : int
            Number of components (gaussians) in the model.
        max_iter : int
            Maximum number of EM iterations to perform.
        device : torch.device
            Which device to be used for the computations
            during the fitting (e.g `'cpu'`, `'cuda'`, `'cuda:0'`).
        tol : float
            The convergence threshold.
        reg_covar : float
            Non-negative regularization added to the diagonal of covariance.
            Allows to assure that the covariance matrices are all positive.
        means_init : torch.tensor
            User provided initialization means for all instances. The
            tensor should have shape (Batch, Components, Dimensions).
            If None (default) the means are going to be initialized
            with modified kmeans++ and then refined with kmeans.
        weights_init : torch.tensor
            The user-provided initial weights. The tensor should have shape
            (Batch, Components). If it is None, weights are initialized
            depending on the kmeans++ & kmeans initialization.
        precisions_init : torch.tensor
            The user-provided initial precisions (inverse of the covariance matrices).
            The tensor should have shape (Batch, Components, Dimension, Dimension).
            If it is None, precisions are initialized depending on the kmeans++ & kmeans
            initialization.
        dtype : torch.dtype
            Data type that will be used in the GMM instance.
        random_seed : int
            Controls the random seed that will be used
            when initializing the model parameters.
        """
        self._n_components = n_components
        self._max_iter = max_iter
        self._device = device
        self._tol = tol
        self._reg_covar = reg_covar
        self._means_init = means_init
        self._weights_init = weights_init
        self._precisions_init = precisions_init
        self._dtype = dtype
        self._rand_generator = torch.Generator(device=device)
        if random_seed:
            self._rand_seed = random_seed
            self._rand_generator.manual_seed(random_seed)
        else:
            self._rand_seed = None


    def fit(self, X):
        """
        Fit the GMM on the given tensor data.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        """
        X = X.to(device=self._device, dtype=self._dtype)

        B, N, D = X.shape

        self._init_parameters(X)
        component_mask = self._init_clusters(X)

        r = torch.zeros(B, N, self._n_components, device=X.device, dtype=self._dtype)
        for k in range(self._n_components):
            r[:, :, k][component_mask == k] = 1

        # This gives us the amount of points per component
        # for each instance in the batch. It's necessary
        # in order to handle missing points (with nan values).
        N_actual = r.nansum(1)
        N_actual_total = N_actual.sum(1)

        converged = torch.full((B,), False, device=self._device)

        # If at least one of the parameters is missing
        # we calculate all parameters with the M-step.
        if (self._means_init is None or
            self._weights_init is None or
            self._precisions_init is None):
            self._m_step(X, r, N_actual, N_actual_total, converged)

        # If any of the parameters have been provided by the
        # user, we overwrite it with the provided value.
        if self._means_init is not None:
            self.means = [self._means_init[:, c, :]
                          for c in range(self._n_components)]
        if self._weights_init is not None:
            self._pi = [self._weights_init[:, c]
                        for c in range(self._n_components)]
        if self._precisions_init is not None:
            self._precisions_cholesky = [torch.linalg.cholesky(self._precisions_init[:, c, :, :])
                                         for c in range(self._n_components)]

        self.convergence_iters = torch.full((B,), -1, dtype=int, device=self._device)
        mean_log_prob_norm = torch.full((B,), -np.inf, dtype=self._dtype, device=self._device)

        iteration = 1
        while iteration <= self._max_iter and not converged.all():
            prev_mean_log_prob_norm = mean_log_prob_norm.clone()

            # === E-STEP ===

            for k in range(self._n_components):
                r[~converged, :, k] = torch.add(
                        _estimate_gaussian_prob(
                            X[~converged],
                            self.means[k][~converged],
                            self._precisions_cholesky[k][~converged],
                            self._dtype).log(),
                        self._pi[k][~converged].unsqueeze(1).log()
                    )
            log_prob_norm = r[~converged].logsumexp(2)
            r[~converged] = (r[~converged] - log_prob_norm.unsqueeze(2)).exp()
            mean_log_prob_norm[~converged] = log_prob_norm.nanmean(1)
            N_actual = r.nansum(1)

            # If we have less than 2 points in a component it produces
            # bad covariance matrices. Hence, we stop the iterations
            # for the affected instances and continue with the rest.
            unprocessable_instances = (N_actual < 2).any(1)
            converged[unprocessable_instances] = True

            # === M-STEP ===

            self._m_step(X, r, N_actual, N_actual_total, converged)

            change = mean_log_prob_norm - prev_mean_log_prob_norm

            # If the change for some instances in the batch
            # are small enough, we mark those instances as
            # converged and do not process them anymore.
            small_change = change.abs() < self._tol
            newly_converged = small_change & ~converged
            converged[newly_converged] = True
            self.convergence_iters[newly_converged] = iteration

            iteration += 1


    def predict_proba(self, X, force_cpu_result=True):
        """
        Estimate the components' density for all samples
        in all instances.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        force_cpu_result : bool
            Make sure that the resulting tensor is loaded on
            the CPU regardless of the device used for the
            computations (default: True).

        Returns
        ----------
        torch.tensor
            tensor of shape (B, N, n_clusters) with probabilities.
            The values at positions [I, S, :] will be the probabilities
            of sample S in instance I to be assigned to each component.
        """
        X = X.to(device=self._device, dtype=self._dtype)
        B, N, D = X.shape
        log_probs = torch.zeros(B, N, self._n_components, device=X.device)
        for k in range(self._n_components):
            # Calculate weighted log probabilities
            log_probs[:, :, k] = torch.add(
                    self._pi[k].log().unsqueeze(1),
                    _estimate_gaussian_prob(X,
                                            self.means[k],
                                            self._precisions_cholesky[k],
                                            self._dtype).log())
        log_prob_norm = log_probs.logsumexp(2)
        log_resp = log_probs - log_prob_norm.unsqueeze(2)

        if force_cpu_result:
            return log_resp.exp().cpu()
        return log_resp.exp()


    def predict(self, X, force_cpu_result=True):
        """
        Predict the component assignment for the given tensor data.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        force_cpu_result : bool
            Make sure that the resulting tensor is loaded on
            the CPU regardless of the device used for the
            computations (default: True).

        Returns
        ----------
        torch.tensor
            tensor of shape (B, N) with component ids as values.
        """
        X = X.to(device=self._device, dtype=self._dtype)
        B, N, D = X.shape
        probs = torch.zeros(B, N, self._n_components, device=X.device)
        for k in range(self._n_components):
            probs[:, :, k] = _estimate_gaussian_prob(X,
                                                     self.means[k],
                                                     self._precisions_cholesky[k],
                                                     self._dtype)
        if force_cpu_result:
            torch.where(probs.isnan().any(2), np.nan, probs.argmax(2)).cpu()
        return torch.where(probs.isnan().any(2), np.nan, probs.argmax(2))


    def score_samples(self, X, force_cpu_result=True):
        """
        Compute the log-likelihood of each point across all instances in the batch.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        force_cpu_result : bool
            Make sure that the resulting tensor is loaded on
            the CPU regardless of the device used for the
            computations (default: True).

        Returns
        ----------
        torch.tensor
            tensor of shape (B, N) with the score for each point in the batch.
        """
        X = X.to(device=self._device, dtype=self._dtype)
        B, N, D = X.shape
        log_probs = torch.zeros(B, N, self._n_components, device=X.device)
        for k in range(self._n_components):
            # Calculate weighted log probabilities
            log_probs[:, :, k] = torch.add(
                    self._pi[k].log().unsqueeze(1),
                    _estimate_gaussian_prob(X,
                                            self.means[k],
                                            self._precisions_cholesky[k],
                                            self._dtype).log())
        if force_cpu_result:
            return log_probs.logsumexp(2).cpu()
        return log_probs.logsumexp(2)


    def score(self, X, force_cpu_result=True):
        """
        Compute the per-sample average log-likelihood of each instance in the batch.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        force_cpu_result : bool
            Make sure that the resulting tensor is loaded on
            the CPU regardless of the device used for the
            computations (default: True).

        Returns
        ----------
        torch.tensor
            tensor of shape (B,) with the log-likelihood for each instance in the batch.
        """
        X = X.to(device=self._device, dtype=self._dtype)
        if force_cpu_result:
            return self.score_samples(X).nanmean(1).cpu()
        return self.score_samples(X, force_cpu_result=False).nanmean(1)


    def bic(self, X, force_cpu_result=True):
        """
        Calculates the BIC (Bayesian Information Criterion) for the model on the dataset X.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        force_cpu_result : bool
            Make sure that the resulting tensor is loaded on
            the CPU regardless of the device used for the
            computations (default: True).

        Returns
        ----------
        torch.tensor
            tensor of shape (B,) with the BIC value for each instance in the Batch.
        """
        X = X.to(device=self._device, dtype=self._dtype)
        scores = self.score(X, force_cpu_result=False)
        valid_points = (~X.isnan()).all(2).sum(1)
        result = -2 * scores * valid_points + self.n_parameters() * valid_points.log()
        if force_cpu_result:
            return result.cpu()
        return result


    def n_parameters(self):
        """
        Returns the number of free parameters in the model for a single instance of the batch.

        Returns
        ----------
        int
            number of parameters in the model
        """
        n_features = self.means[0].shape[1]
        cov_params = self._n_components * n_features * (n_features + 1) / 2.0
        mean_params = n_features * self._n_components
        return int(cov_params + mean_params + self._n_components - 1)


    def _init_clusters(self, X):
        """
        Init the assignment component (cluster) assignment for B sets of N D-dimensional points.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        """
        # If the assignment produced by kmeans has a component
        # with less than two points, we rerun it to get a different
        # assignment (up to 3 times). Having less than 2 points leads
        # to bad covariance matrices that produce errors when trying
        # to decompose/invert them.
        retries = 0
        while retries < 3:
            _, assignment = self._kmeans(X, self._n_components)
            _, counts = assignment.unique(return_counts=True)
            if not torch.any(counts <= 2):
                return assignment
            retries += 1
        return assignment


    def _init_parameters(self, X):
        B, N, D = X.shape
        self.means = [torch.empty(B, D, dtype=self._dtype, device=self._device)
                      for _ in range(self._n_components)]
        self.covs = [torch.empty(B, D, D, dtype=self._dtype, device=self._device)
                     for _ in range(self._n_components)]
        self._precisions_cholesky = [torch.empty(B, D, D,
                                                 dtype=self._dtype,
                                                 device=self._device)
                                     for _ in range(self._n_components)]
        self._pi = [torch.empty(B, dtype=self._dtype, device=self._device)
                    for _ in range(self._n_components)]


    def _m_step(self, X, r, N_actual, N_actual_total, converged):
        B, N, D = X.shape
        # We update the means, covariances and weights
        # for all instances in the batch that still
        # have not converged.
        for k in range(self._n_components):
            self.means[k][~converged] = torch.div(
                    # the nominator is sum(r*X)
                    (r[~converged, :, k].unsqueeze(2) * X[~converged]).nansum(1),
                    # the denominator is normalizing by the number of valid points
                    N_actual[~converged, k].unsqueeze(1))

            self.covs[k][~converged] = self._get_covs(X[~converged],
                                                      self.means[k][~converged],
                                                      r[~converged, :, k],
                                                      N_actual[~converged, k])

            # We need to calculate the Cholesky decompositions of
            # the precision matrices (the precision is the inverse
            # of the covariance). However, due to numerical errors
            # the covariance may lose its positive-definite property
            # (which mathematically is guarenteed to have). Whenever
            # that happens, we can no longer calculate the Cholesky
            # decomposition. As a workaround, we substitute the cov
            # matrix with a near covariance matrix that is positive
            # definite.
            covs_cholesky, errors = torch.linalg.cholesky_ex(self.covs[k][~converged])
            bad_covs = errors > 0
            if bad_covs.any():
                eigvals, eigvecs = torch.linalg.eigh(self.covs[k][~converged][bad_covs])
                # Theoretically, we should be able to use much smaller
                # min value here, but for some reason smaller ones sometimes
                # fail to force the covariance matrix to be positive-definite.
                new_eigvals = torch.clamp(eigvals, min=1e-5)
                new_covs = eigvecs @ torch.diag_embed(new_eigvals) @ eigvecs.transpose(-1, -2)
                self.covs[k][~converged][bad_covs] = new_covs
                covs_cholesky[bad_covs] = torch.linalg.cholesky(new_covs)
            self._precisions_cholesky[k][~converged] = self._get_precisions_cholesky(covs_cholesky)

            self._pi[k][~converged] = N_actual[~converged, k]/N_actual_total[~converged]


    def _kmeans(self, X, n_clusters=2, max_iter=10, tol=0.001):
        """
        Clusters the points in each instance of the batch using k-means.
        Points with nan values are assigned with value -1.

        Parameters
        ----------
        X : torch.tensor
            A tensor with shape (Batch, N-points, Dimensions)
        n_clusters : int
            Number of clusters to find.
        max_iter : int
            Maximum number of iterations to perform.
        tol : float
            The convergence threshold.
        """
        B, N, D = X.shape
        C = n_clusters
        valid_points = ~X.isnan().any(dim=2)
        invalid_points_count = (~valid_points).sum(1)
        centers = self._kmeans_pp(X, C, valid_points)

        i = 0
        diff = np.inf
        while i < max_iter and diff > tol:
            # Calculate the squared distance between each point and cluster centers
            distances = (X[:, :, None, :] - centers[:, None, :, :]).square().sum(dim=-1)
            assignment = distances.argmin(dim=2)

            # Compute the new cluster center
            cluster_sums = torch.zeros_like(centers)
            cluster_counts = torch.zeros((B, C), dtype=torch.float32, device=X.device)
            # The nans are assigned to the first cluster. We want to ignore them.
            # Hence, we use nat_to_num() to replace them with 0s and then we subtract
            # the number of invalid points from the counts for the first cluster.
            cluster_sums.scatter_add_(1, assignment.unsqueeze(-1).expand(-1, -1, D), X.nan_to_num())
            cluster_counts.scatter_add_(1, assignment, torch.ones((B, N)))
            cluster_counts[:, 0] -= invalid_points_count
            new_centers = cluster_sums / cluster_counts.unsqueeze(2).clamp_min(1e-8)

            # Estimate how much change we get in the centers
            diff = torch.norm(new_centers - centers, dim=(1, 2)).max()

            centers = new_centers.nan_to_num()
            i += 1

        # Final assignment with updated centers
        distances = (X[:, :, None, :] - centers[:, None, :, :]).square().sum(dim=-1)
        assignment = torch.where(valid_points, distances.argmin(dim=2), -1)

        return centers, assignment


    def _select_random_valid_points(self, X, valid_mask):
        B, N, D = X.shape

        _, point_idx = valid_mask.nonzero(as_tuple=True)
        counts = valid_mask.sum(1)

        # Select random valid index.
        # This is efficient, but quite tricky:
        # nonzero(as_tuple=True) returns a list of the batch indices and corresponding
        # point indices of valid points. For each instance in the batch, we get a
        # random integer between 0 and the maximum possible number of valid points.
        # To make sure that the selected integer is not larger than the number of
        # valid points for each instance we mod that integer by counts.
        # This basically gives us a random offset to select a point from a list
        # of valid points for a given batch index.
        rand_offsets = torch.randint(0, counts.max(), (B,),
                                     generator=self._rand_generator,
                                     device=X.device) % counts

        # Here, cumsum(counts)-counts gives us the starting position of each instance in the batch
        # in point_idx. E.g. if we have a batch of 3 instances with [5, 7, 3] valid points respectively,
        # we would get batch starts = [0, 5, 12].
        batch_starts = torch.cumsum(counts, dim=0) - counts
        chosen_indices = point_idx[batch_starts + rand_offsets]

        selected_points = X[torch.arange(B, device=X.device), chosen_indices]
        return selected_points


    def _kmeans_pp(self, X, C, valid_points):
        B, N, D = X.shape
        device = X.device
        std = self._nanstd(X)
        centers = torch.empty(B, C, D, device=device)

        # Randomly select the first center for each batch
        rand_points = self._select_random_valid_points(X, valid_points)
        centers[:, 0, :] = std * rand_points / rand_points.norm(dim=-1, keepdim=True)

        # Each subsequent center would be calculated to be distant
        # from the previous one
        for k in range(1, C):
            prev_centers = centers[:, k - 1, :].unsqueeze(1)
            distances = (X - prev_centers).norm(dim=-1)

            # By default kmeans++ takes as the next center the
            # point that is furthest away. However, if there are
            # outliers, they're likely to be selected, so here we
            # ignore the top 10% of the most distant points.
            threshold_idx = int(0.9 * N)
            sorted_distances, sorted_indices = distances.sort(1)

            # The standard kmeans++ algorithm selects an initial
            # point at random for the first centroid and then for
            # each cluster selects the point that is furthest away
            # from the previous one. This is prone to selecting
            # outliers that are very far away from all other points,
            # leading to clusters with a single point. In the GMM
            # fitting these clusters are problematic, because variance
            # covariance metrics do not make sense anymore.
            # To ameliorate this, we position the centroid at a point
            # that is in the direction of the furthest point,
            # but the length of the vector is equal to the 150% the
            # standard deviation in the dataset.
            # First, we get the most distant valid positions (after ignoring
            # the top 10%).
            max_valid_idx = _nanmax(sorted_distances[:, :threshold_idx], 1)[1]
            # Those are indices that point to the sorting and not the original dataset.
            # We need to map them through sorted_indices to obtain the indices for those points
            # in the dataset X.
            orig_indices = sorted_indices[torch.arange(B, device=device), max_valid_idx]
            selected_points = X[torch.arange(B, device=device), orig_indices]
            # Once we have the actual points, we calculate the new centers.
            centers[:, k, :] = 1.5 * std * selected_points / selected_points.norm(dim=-1, keepdim=True)
        return centers


    def _get_covs(self, X, means, r, nums):
        B, N, D = X.shape
        # C_k = (1/N_k) * sum(r_nk * (x - mu_k)(x - mu_k)^T)
        diffs = X - means.unsqueeze(1)
        summands = r.view(B, N, 1, 1) * torch.matmul(diffs.unsqueeze(3), diffs.unsqueeze(2))
        covs = summands.nansum(1) / nums.view(B, 1, 1).add(torch.finfo(self._dtype).eps)
        return covs


    def _get_precisions_cholesky(self, covs_cholesky):
        B, D, D = covs_cholesky.shape
        precisions_cholesky = torch.linalg.solve_triangular(
                covs_cholesky,
                torch.eye(D, device=self._device).unsqueeze(0).repeat(B, 1, 1),
                upper=False,
                left=True).permute(0, 2, 1)
        return precisions_cholesky.to(self._dtype)


    def _nanstd(self, X):
        valid = torch.sum(~X.isnan().any(2), 1)
        return (((X - X.nanmean(1).unsqueeze(1)) ** 2).nansum(1) / valid.unsqueeze(1)) ** 0.5


def _nanmax(T, dim):
    """
    Compute the max along a given axis while ignoring NaNs.
    """
    nan_mask = T.isnan()
    T = torch.where(nan_mask, float('-inf'), T)
    max_values, indices = T.max(dim=dim)
    return max_values, indices


def _estimate_gaussian_prob(X, mean, precisions_chol, dtype):
    """
    Compute the probability of a batch of points X under
    a batch of multivariate normal distributions.

    Parameters
    ----------
    X : torch.tensor
        A tensor with shape (Batch, N-points, Dimensions).
        Represents a batch of points.
    mean : torch.tensor
        The means of the distributions. Shape: (B, D)
    precisions_chol : torch.tensor
        Cholesky decompositions of the precisions matrices. Shape: (B, D, D)
    dtype : torch.dtype
        Data type of the result

    Returns
    ----------
    torch.tensor
        tensor of shape (B, N) with probabilities
    """
    B, N, D = X.shape
    y = torch.bmm(X, precisions_chol) - torch.bmm(mean.unsqueeze(1), precisions_chol)
    log_prob = y.pow(2).sum(2)
    log_det = torch.diagonal(precisions_chol, dim1=1, dim2=2).log().sum(1)
    return torch.exp(
            -0.5 * (D * np.log(2 * np.pi) + log_prob) + log_det.unsqueeze(1))

