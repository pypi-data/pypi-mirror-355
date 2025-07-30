# FOX/diagnostics.py
import numpy as np
from scipy.stats import kendalltau
from sklearn.neighbors import KDTree as KDTree_whole
from scipy.spatial import KDTree as KDTree_layer
from sklearn.decomposition import NMF
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from scipy import stats

def calculate_r2_and_coefficients(condx, condy):
    """
    Perform linear regression on the provided data (condx, condy),
    and return the R², RSS (Residual Sum of Squares), TSS (Total Sum of Squares),
    and the regression coefficients.
    """
    regr = LinearRegression()  # Initialize a LinearRegression model
    regr.fit(condx, condy)  # Fit the model to the data (condx, condy)

    y_pred = regr.predict(condx)  # Predict the values for condx using the trained model

    # Calculate the residual sum of squares (RSS)
    rss = np.sum((condy - y_pred) ** 2)

    # Calculate the total sum of squares (TSS)
    tss = np.sum((condy - np.mean(condy)) ** 2)

    # Calculate R² using the r2_score function from sklearn
    r2 = r2_score(condy, y_pred)

    return r2, rss, tss, regr.coef_  # Return the R², RSS, TSS, and coefficients (coef)


def check_r2_consistency(r2, rss, tss):
    """
    Check if the calculated R² is consistent with the given RSS and TSS.
    This should hold: R² = 1 - (RSS / TSS)
    """
    return r2 == 1 - (rss / tss)  # Return True if the formula holds, False otherwise


def calculate_metrics(r2, rss, tss, coef):
    """
    Calculate final metrics:
    - The correlation coefficient (r) as the square root of R², adjusted for the sign of the coefficient.
    - The rounded R², TSS, and RSS values for reporting.
    """
    r = math.sqrt(r2) * np.sign(
        coef
    )  # Calculate the correlation coefficient (r), adjusted for sign of the coefficients
    # Return the rounded metrics: r, r², TSS, RSS
    return round(r.item(), 2), round(r2, 2), round(tss, 2), round(rss, 2)


def process_data_for_labels(labels, NMF_embedd):
    """
    Process data for each label and calculate R², RSS, TSS, and the correlation coefficient.
    Returns a dictionary where the key is the label, and the value is a tuple of calculated metrics.
    """
    func_sep = {}  # Initialize an empty dictionary to store results for each label

    for i in labels:  # Iterate over each label
        # Get the data for this label and reshape it to be 2D (as required for sklearn)
        condx = NMF_embedd[i][0].reshape(-1, 1)
        condy = NMF_embedd[i][1].reshape(-1, 1)

        # Call the function to calculate R², RSS, TSS, and coefficients
        r2, rss, tss, coef = calculate_r2_and_coefficients(condx, condy)

        # Check if the calculated R² is consistent with RSS and TSS
        if check_r2_consistency(r2, rss, tss):
            print(i, " works")  # Print a success message if consistent

        # Calculate the final metrics: correlation coefficient, R², TSS, and RSS
        r_metric, r2_metric, tss_metric, rss_metric = calculate_metrics(
            r2, rss, tss, coef
        )

        # Store the metrics in the dictionary for this label
        func_sep[i] = (r_metric, r2_metric, tss_metric, rss_metric)

    return func_sep  # Return the dictionary of results for each label
