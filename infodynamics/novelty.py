'''
Driver
'''
# %%
import sys
sys.path.append('../')

import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from infodynamics.entropies.factory import metric_factory


class Novelty:
    def __init__(self, window, metric, custom_metric=None, placeholder_constant=0) -> None:
        self.metric = metric_factory(metric_name=metric)
        self.window = window
        self.placeholder_constant = placeholder_constant

    def _calc_novelty(self, X):
        n_datapoints = X.shape[0]
        N_hat = np.zeros(n_datapoints)
        N_sd = np.zeros(n_datapoints)

        for i, x in enumerate(X):
            # current window data subset
            submat = X[
                (i - self.window) : i,
            ]
            # array of zeros to fill with results
            tmp = np.zeros(submat.shape[0])
            # are there datapoints? they appear at i >= window
            if submat.any():
                for ii, xx in enumerate(submat):
                    # calc pairwise entropy
                    tmp[ii] = self.metric(x, xx)
            else:
                # add constant for datapoints before i >= window
                tmp = np.zeros([self.window]) + self.placeholder_constant

            # summarize window
            N_hat[i] = np.mean(tmp)
            N_sd[i] = np.std(tmp)

        self.nsignal = N_hat
        self.nsigma = N_sd

    def _calc_transience(self, X):
        n_datapoints = X.shape[0]
        T_hat = np.zeros(n_datapoints)
        T_sd = np.zeros(n_datapoints)

        for i, x in enumerate(X):
            submat = X[
                i + 1 : (i + self.window + 1),
            ]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, xx in enumerate(submat):
                    tmp[ii] = self.metric(x, xx)
            else:
                tmp = np.zeros([self.window])

            T_hat[i] = np.mean(tmp)
            T_hat[-self.window :] = np.zeros([self.window]) + self.placeholder_constant
            T_sd[i] = np.std(tmp)

        self.tsignal = T_hat
        self.tsigma = T_sd

    def _calc_resonance(self, X):
        # novelty and transience must be run beforehand
        self._calc_novelty(X)
        self._calc_transience(X)

        self.rsignal = self.nsignal - self.tsignal
        self.rsignal[: self.window] = np.zeros([self.window]) + self.placeholder_constant
        self.rsignal[-self.window :] = np.zeros([self.window]) + self.placeholder_constant
        self.rsigma = (self.nsigma + self.tsigma) / 2
        self.rsigma[: self.window] = np.zeros([self.window]) + self.placeholder_constant
        self.rsigma[-self.window :] = np.zeros([self.window]) + self.placeholder_constant

    def _slice_zeros(self, complete=True):

        # cut values that are zero (incomplete data for calulation)
        self.rsignal = self.rsignal[self.window : -self.window]
        self.rsigma = self.rsigma[self.window : -self.window]

        if complete:
            # cut novelty and transience in the same way
            self.nsignal = self.nsignal[self.window : -self.window]
            self.nsigma = self.nsigma[self.window : -self.window]
            self.tsignal = self.tsignal[self.window : -self.window]
            self.tsigma = self.tsigma[self.window : -self.window]
        else:
            # cut first w from novelty and last w from tarnsience
            self.nsignal = self.nsignal[self.window ::]
            self.nsigma = self.nsigma[self.window ::]
            self.tsignal = self.tsignal[:: -self.window]
            self.tsigma = self.tsigma[:: -self.window]
    
    def _calc_novelty_effectiveness(self):
        # TODO check if fitted
        X_z = StandardScaler().fit_transform(self.nsignal.reshape(-1, 1))
        y_z = StandardScaler().fit_transform(self.rsignal.reshape(-1, 1))
        
        lm = LinearRegression(fit_intercept=False)
        lm.fit(X_z, y_z)
        return lm

    def fit(self, X, slice_w=False):
        self._calc_novelty(X)
        self._calc_transience(X)
        self._calc_resonance(X)

        if slice_w:
            self.slice_zeros()
        
        return self

    def transform(self, X):
        pass

    def fit_transform():
        pass

# # %%
# # test data

# px = np.array([0.2, 0.6, 0, 0.2])
# qx = np.array([0, 0.8, 0.1, 0.1])

# X = np.load('test_data.npy')

# # %%
# id = Novelty(window=2, metric="kld")
# id.fit(X)

# # %%
# a = id._calc_novelty_effectiveness()

# # %%
# kld = metric_factory('kld')
# # %%
# kld(X[0], X[1])

# # %%
# px_zero = np.array([0.2, 0.8, 0])
# qx_non_zero = np.array([1, 0, 0])

# kld(px_zero, qx_non_zero)
# # %%
