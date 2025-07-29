import numpy as np
from sklearn.decomposition import PCA as skPCA


class PCA:
    VERSION = 'Kantris.PCA: 0.1.0'
    def PCA(Data: np.ndarray, Config: dict=None):
        if Config is None:
            Config = {}
        n_features = Data.shape[1]
        pca = skPCA(n_components=n_features)
        pca.fit(Data)
        return {
            "principal_components": pca.components_,
            "explained_variance": pca.explained_variance_,
            "explained_variance_ratio": pca.explained_variance_ratio_,
            "singular_values": pca.singular_values_,
            "mean_vector": pca.mean_
        }
