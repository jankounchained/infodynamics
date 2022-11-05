'''
Driver
'''
import numpy as np

from infodynamics.entropies.factory import entropy_factory


class Novelty:
    def __init__(self, window, metric, custom_metric, weight=0) -> None:
        self.metric = entropy_factory(metric=metric, **params)

    def _calc_novelty(self, X):
        N_hat = np.zeros(self.m)
        N_sd = np.zeros(self.m)
        for i, x in enumerate(self.data):
            submat = self.data[
                (i - self.window) : i,
            ]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, xx in enumerate(submat):
                    tmp[ii] = self.metric(x, xx)
            else:
                tmp = np.zeros([self.window]) + self.weight

            N_hat[i] = np.mean(tmp)
            N_sd[i] = np.std(tmp)

        self.nsignal = N_hat
        self.nsigma = N_sd

    def _calc_transience(self, X):
        T_hat = np.zeros(self.m)
        T_sd = np.zeros(self.m)
        for i, x in enumerate(self.data):
            submat = self.data[
                i + 1 : (i + self.window + 1),
            ]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, xx in enumerate(submat):
                    tmp[ii] = self.metric(x, xx)
            else:
                tmp = np.zeros([self.window])

            T_hat[i] = np.mean(tmp)
            T_hat[-self.window :] = np.zeros([self.window]) + self.weight
            T_sd[i] = np.std(tmp)

        self.tsignal = T_hat
        self.tsigma = T_sd

    def _calc_resonance(self, X):
        # novelty and transience must be run beforehand
        self.novelty(X)
        self.transience(X)

        self.rsignal = self.nsignal - self.tsignal
        self.rsignal[: self.window] = np.zeros([self.window]) + self.weight
        self.rsignal[-self.window :] = np.zeros([self.window]) + self.weight
        self.rsigma = (self.nsigma + self.tsigma) / 2
        self.rsigma[: self.window] = np.zeros([self.window]) + self.weight
        self.rsigma[-self.window :] = np.zeros([self.window]) + self.weight

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

    def fit(self, X, slice_w=False):
        self._calc_novelty(X)
        self._calc_transience(X)
        self._calc_resonance(X)

        if slice_w:
            self.slice_zeros()
        
        return self

    def transform():
        pass

    def fit_transform():
        pass
