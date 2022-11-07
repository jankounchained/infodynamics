''' 
Melvin's jump entropy method
'''

import numpy as np

from infodynamics.measures.factory import metric_factory


class JumpEntropy:
    def __init__(self, window, jump_range, metric='jsd', custom_metric=None, placeholder_constant=0) -> None:
        self.window = window
        self.metric = metric_factory(metric_name=metric)

        if custom_metric:
            # check if custom_metric is a function
            assert hasattr(custom_metric, '__call__')
            self.metric = custom_metric

        self.placeholder_constant = placeholder_constant

    def _calc_jump(self, X, j):
        N_hat = np.zeros(X.shape[0])
        N_sd = np.zeros(X.shape[0])
        for i, x in enumerate(X):
            submat = X[(i - self.window):(i+self.window),]
            submat_jump = X[((i - self.window) + j):((i+self.window)+j),]
            tmp = np.zeros(submat.shape[0])
            if submat.any():
                for ii, (xx, xx_j) in enumerate(zip(submat, submat_jump)):
                    tmp[ii] = self.metric(xx, xx_j)
            else:
                tmp = np.zeros([self.window]) + self.placeholder_constant

            N_hat[i] = np.mean(tmp)
            N_sd[i] = np.std(tmp)

        return N_hat, N_sd

    # def make_jump_entropies(input_file, window, jump_range=range(-1500, 1500, 1)):

    #     theta, dates = load_model(input_file)

    #     jumps = dict()
    #     jumps2 = Parallel(n_jobs=40)(delayed(calc_jump)(theta, window, jump, jumps) for jump in tqdm(jump_range))
    #     jumps = dict()
    #     # take dictionary out of list output from parallel
    #     for _ in jumps2:
    #         for k, v in _.items():
    #             jumps[k] = v

    #     filename = os.path.basename(input_file) 
    #     df_kld = pd.DataFrame.from_dict(jumps, orient='columns')
    #     df_kld['dates'] = dates
    #     df_kld.to_pickle(f"../models/jumps/{filename[:-4]}_jump.pkl")