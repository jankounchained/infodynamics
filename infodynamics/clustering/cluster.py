"""
Clusters time series signals via DTW distance and agglomerative clustering,
with per-cluster DBA/soft-DTW archetypes.
"""
from typing import Literal, Optional, Sequence

import numpy as np
from sklearn.base import BaseEstimator, ClusterMixin
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import silhouette_score
from typing_extensions import Self

from infodynamics.clustering.barycenter import average as barycenter_average
from infodynamics.clustering.dtw import pairwise_distance


class SignalClusterer(BaseEstimator, ClusterMixin):
    """
    Clusters a set of (possibly differently lengthed) time series signals
    using DTW distance and agglomerative clustering, following the approach
    in Wevers, Kostkan & Nielbo (2021), "Event Flow".
    """

    def __init__(
        self,
        n_clusters: Optional[int] = None,
        k_range: Sequence[int] = range(2, 10),
        linkage: str = "average",
        z_normalize: bool = True,
        barycenter_method: Literal["dba", "soft_dtw"] = "dba",
    ):
        """

        Parameters
        ----------
        n_clusters : int or None, default=None
            number of clusters. If None, searches 'k_range' for the number of
            clusters with the highest silhouette score.

        k_range : Sequence[int], default=range(2, 10)
            candidate numbers of clusters to search over when 'n_clusters' is None.

        linkage : str, default='average'
            linkage criterion for agglomerative clustering. See sklearn's AgglomerativeClustering.

        z_normalize : bool, default=True
            z-normalize each time series before comparison.

        barycenter_method : {'dba', 'soft_dtw'}, default='dba'
            method used to compute the per-cluster archetypical time series.
        """
        self.n_clusters = n_clusters
        self.k_range = k_range
        self.linkage = linkage
        self.z_normalize = z_normalize
        self.barycenter_method = barycenter_method

    def _select_k(self, distance_matrix: np.ndarray) -> int:
        best_k, best_score = None, -np.inf
        for k in self.k_range:
            if k >= distance_matrix.shape[0]:
                break
            labels = AgglomerativeClustering(
                n_clusters=k, metric="precomputed", linkage=self.linkage
            ).fit_predict(distance_matrix)
            score = silhouette_score(distance_matrix, labels, metric="precomputed")
            if score > best_score:
                best_k, best_score = k, score

        if best_k is None:
            raise ValueError(
                "Could not find a valid number of clusters for the given 'k_range' and input size."
            )
        return best_k

    def fit(self, series: Sequence[np.ndarray], y=None) -> Self:
        """Fit the clusterer: compute DTW distances, cluster, and average each cluster.

        Parameters
        ----------
        series : Sequence[np.ndarray]
            the time series to cluster.

        y : Ignored
            not used, present here for API consistency by convention.
        """
        series = list(series)
        distance_matrix = pairwise_distance(series, z_normalize=self.z_normalize)

        n_clusters = self.n_clusters
        if n_clusters is None:
            n_clusters = self._select_k(distance_matrix)

        model = AgglomerativeClustering(
            n_clusters=n_clusters,
            metric="precomputed",
            linkage=self.linkage,
            compute_distances=True,
        )
        labels = model.fit_predict(distance_matrix)

        barycenters = {
            int(label): barycenter_average(
                [s for s, s_label in zip(series, labels) if s_label == label],
                method=self.barycenter_method,
            )
            for label in np.unique(labels)
        }

        self.model_ = model
        self.distance_matrix_ = distance_matrix
        self.labels_ = labels
        self.barycenters_ = barycenters
        self.n_clusters_ = n_clusters
        return self

    def fit_predict(self, series: Sequence[np.ndarray], y=None) -> np.ndarray:
        self.fit(series)
        return self.labels_
