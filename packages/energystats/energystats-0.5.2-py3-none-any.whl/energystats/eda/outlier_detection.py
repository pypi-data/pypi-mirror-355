import numpy as np
import pandas as pd
from scipy import stats
from energystats.tests.cor import dcor


def find_outliers(data, target, threshold = 3, row_names = None,):
    """ 
    Szekely and Rizzo [2023], Identitfying influential observations using distance correlation analysis. 
    Args:
        data (list[np.ndarray]):
            A matrix of independent variables
        target (float):
            A vector of dependent observation
        R (int, optional):
            Number of permutations for the between-sample test. Defaults to 1000.

    Returns:
        dict:
            A dictionary with the following keys:   
            - **'original_dcor'** (*float*): The distance correlation of the original data.
            - **'dcor_replicates'** (*np.ndarray*): A NumPy containing the distance correlation of each replicate.  
            - **'outliers'** (*np.ndarray*): A list of identified outliers.
    """

    numeric_data = data.to_numpy()
    n = len(numeric_data)
    dcor_replicates = []
    original_dcor = dcor(data, target)

    for i in range(0, n):
        sample_data = data.drop([i], axis=0)
        sample_target = target.drop([i], axis=0)
        dcor_replicates.append(dcor(sample_data, sample_target))
    
    dcor_replicates = pd.DataFrame({'replicates' : dcor_replicates, 'point_labels': row_names})
    z = np.abs(stats.zscore(dcor_replicates['replicates']))
    outliers = dcor_replicates[z > threshold]

    
    return {'original_dcor': original_dcor, 'dcor_replicates': dcor_replicates, 'outliers' : outliers }


