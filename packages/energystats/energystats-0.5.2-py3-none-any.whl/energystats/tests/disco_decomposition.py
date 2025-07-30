import numpy as np
from scipy.spatial.distance import pdist, squareform

def within_sample_dispersion(X, alpha=1):
    """
    Compute within-sample dispersion (W_alpha) for a single sample.
    Parameters:
        X (np.ndarray): Array of sample data.
        alpha (float): Exponent for distance weighting, default is 1.
    Returns:
        float: The within-sample dispersion W_alpha.
    """
    n = X.shape[0]
    if n < 2:
        return 0
    distances = pdist(X, 'euclidean')
    weighted_distances = distances**alpha
    return np.sum(weighted_distances) / (n * (n - 1))

def total_dispersion(X, alpha=1):
    """
    Compute the total dispersion (T_alpha) for all samples pooled together.
    Parameters:
        X (np.ndarray): Pooled array of data from all samples.
        alpha (float): Exponent for distance weighting, default is 1.
    Returns:
        float: The total dispersion T_alpha.
    """
    n = X.shape[0]
    distances = pdist(X, 'euclidean')
    weighted_distances = distances**alpha
    return np.sum(weighted_distances) / (n * (n - 1))

def disco_decomposition(groups, alpha=1, R=1000):
    """Partition total dispersion into within-sample and between-sample components via DISCO.

    This performs the DISCO decomposition on a list of samples, computing
    the total dispersion (Tₐ), the within-sample dispersion (Wₐ), and the
    between-sample dispersion (Sₐ).  It also runs a permutation test
    (R permutations) to compute a p-value for the between-sample component.

    Args:
        groups (list[np.ndarray]):
            A list where each element is a 1D or 2D sample array.
        alpha (float, optional):
            Exponent for distance weighting. Defaults to 1.0.
        R (int, optional):
            Number of permutations for the between-sample test. Defaults to 1000.

    Returns:
        dict:
            A dictionary with the following keys:
            
            - **'T_alpha'** (*float*): Total dispersion.
            - **'W_alpha'** (*float*): Within-sample dispersion.
            - **'S_alpha'** (*float*): Between-sample dispersion.
            - **'p_value'** (*float*): P-value from the permutation test.

    Raises:
        ValueError:
            If `groups` is empty or contains arrays of inconsistent dimension.
    """
    W_alpha = sum(within_sample_dispersion(X, alpha) * len(X) for X in groups) / sum(len(X) for X in groups)

    # Combine all samples for total dispersion
    pooled_data = np.vstack(groups)
    T_alpha = total_dispersion(pooled_data, alpha)

    # Compute between-sample component
    n = sum(len(X) for X in groups)
    S_alpha = T_alpha - W_alpha

    # Permutation test for the between-sample component
    observed_statistic = S_alpha
    perm_stats = []
    for _ in range(R):
        # Permute labels
        permuted_data = np.random.permutation(pooled_data)
        perm_groups = np.split(permuted_data, np.cumsum([len(X) for X in groups])[:-1])
        perm_W_alpha = sum(within_sample_dispersion(X, alpha) * len(X) for X in perm_groups) / n
        perm_T_alpha = total_dispersion(permuted_data, alpha)
        perm_stats.append(perm_T_alpha - perm_W_alpha)

    # Calculate p-value
    p_value = np.mean([stat >= observed_statistic for stat in perm_stats])

    return {
        "T_alpha": T_alpha,
        "W_alpha": W_alpha,
        "S_alpha": S_alpha,
        "p-value": p_value
    }
