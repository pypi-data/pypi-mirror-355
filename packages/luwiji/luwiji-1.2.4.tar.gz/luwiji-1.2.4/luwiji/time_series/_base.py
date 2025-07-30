import os
from IPython.display import Image

import numpy as np
import pandas as pd

import matplotlib.pyplot as plt
from ipywidgets import interact
from matplotlib.collections import PolyCollection
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.arima_process import ArmaProcess


class BaseDemoTimeSeries:
    def __init__(self):
        self._generate_data(seed=42, n_sample=45)

    def _generate_data(self, seed, n_sample):
        np.random.seed(seed)
        sample = ArmaProcess([1, -0.8, 0.75], None).generate_sample(n_sample)
        self.stationary_data = pd.Series(sample)

        sample = ArmaProcess([1, -0.8, 0.75], None).generate_sample(n_sample)
        self.trending_data = pd.Series(sample) + np.arange(len(sample))

    @staticmethod
    def AR_example(seed=42):
        np.random.seed(seed)
        plt.figure(figsize=(16, 7))

        sample = ArmaProcess([1, -0.6], None).generate_sample(12)
        plt.subplot(231)
        plt.plot(sample, "r-")
        plt.title("AR(1)")

        plt.subplot(232)
        sample = ArmaProcess([1, -0.8], None).generate_sample(20)
        plt.plot(sample, "r-")
        plt.title("AR(1)")

        plt.subplot(233)
        sample = ArmaProcess([1, 0.4], None).generate_sample(15)
        plt.plot(sample, "r-")
        plt.title("AR(1)")

        sample = ArmaProcess([1, -0.6, -0.3], None).generate_sample(12)
        plt.subplot(234)
        plt.plot(sample, "r-")
        plt.title("AR(2)")

        plt.subplot(235)
        sample = ArmaProcess([1, -0.8, 0.2], None).generate_sample(20)
        plt.plot(sample, "r-")
        plt.title("AR(2)")

        plt.subplot(236)
        sample = ArmaProcess([1, 0.4, -0.5], None).generate_sample(15)
        plt.plot(sample, "r-")
        plt.title("AR(2)")

    @staticmethod
    def MA_example(seed=42):
        np.random.seed(seed)
        plt.figure(figsize=(16, 7))

        sample = ArmaProcess(None, [1, 0.6]).generate_sample(12)
        plt.subplot(231)
        plt.plot(sample, "b-")
        plt.title("MA(1)")

        plt.subplot(232)
        sample = ArmaProcess(None, [1, 0.8]).generate_sample(20)
        plt.plot(sample, "b-")
        plt.title("MA(1)")

        plt.subplot(233)
        sample = ArmaProcess(None, [1, -0.4]).generate_sample(15)
        plt.plot(sample, "b-")
        plt.title("MA(1)")

        sample = ArmaProcess(None, [1, 0.6, 0.3]).generate_sample(12)
        plt.subplot(234)
        plt.plot(sample, "b-")
        plt.title("MA(2)")

        plt.subplot(235)
        sample = ArmaProcess(None, [1, 0.8, -0.2]).generate_sample(20)
        plt.plot(sample, "b-")
        plt.title("MA(2)")

        plt.subplot(236)
        sample = ArmaProcess(None, [1, 0.4, -0.5]).generate_sample(15)
        plt.plot(sample, "b-")
        plt.title("MA(2)")

    @staticmethod
    def _plot(process, ar, ma, diff=False, n_sample=15, show_acf=False):
        sample = process.generate_sample(n_sample)
        if diff:
            sample = pd.Series(sample).diff().dropna()

        if ar is not None:
            ar_eq = " + ".join([f"{-round(p, 2)}y_{{t-{i}}}" for i, p in enumerate(ar[1:], 1)])
        if ma is not None:
            ma_eq = " + ".join([fr"{round(q, 2)}\epsilon_{{t-{i}}}" for i, q in enumerate(ma[1:], 1)])
        if ar and ma:
            eq = fr"$y_t = {ar_eq} + {ma_eq} + \epsilon_t$"
        elif ar and not ma:
            eq = fr"$y_t = {ar_eq} + \epsilon_t$"
        elif not ar and ma:
            eq = fr"$y_t = {ma_eq} + \epsilon_t$"    
        
        if diff:
            eq = f"Difference of {eq} may be stationary"
        else:
            eq += f" | Stationarity: {process.isstationary}"

        plt.figure(figsize=(15, 8))
        plt.subplot(211)
        plt.plot(sample, "b-")
        plt.title(eq, fontsize=14)

        if show_acf:
            ax1 = plt.subplot(223)
            plot_pacf(sample, lags=min(n_sample, 30) // 2 - 1, ax=ax1, title="PACF (for AR)", color="r", vlines_kwargs={"colors": "r"}, alpha=0.05);
            for item in ax1.collections:
                if type(item) == PolyCollection:
                    item.set_facecolor('r')
                    item.set_alpha(0.15)

            ax2 = plt.subplot(224)
            plot_acf(sample, lags=min(n_sample, 30) - 1, ax=ax2, title="ACF (for MA)", color="b", vlines_kwargs={"colors": "b"}, alpha=0.05);
            for item in ax2.collections:
                if type(item) == PolyCollection:
                    item.set_facecolor('b')
                    item.set_alpha(0.15)



    def AR1_simulation(self, n_sample=36, show_acf=False):
        def _simul(alpha1=0.7):
            ar = [1, -alpha1]
            ma = None
            process = ArmaProcess(ar, ma)
            self._plot(process, ar, ma, n_sample=n_sample, show_acf=show_acf)

        interact(_simul, alpha1=(-0.9, 0.9, 0.05))

    def AR2_simulation(self, n_sample=36, show_acf=False):
        def _simul(alpha1=0.4, alpha2=0.5):
            ar = [1, -alpha1, -alpha2]
            ma = None            
            process = ArmaProcess(ar, ma)
            self._plot(process, ar, ma, n_sample=n_sample, show_acf=show_acf)

        interact(_simul, alpha1=(-0.9, 0.9, 0.05), alpha2=(-0.9, 0.9, 0.05))

    def MA1_simulation(self, n_sample=36, show_acf=False):
        def _simul(theta1=-0.7):
            ar = None
            ma = [1, theta1]
            process = ArmaProcess(ar, ma)
            self._plot(process, ar, ma, n_sample=n_sample, show_acf=show_acf)

        interact(_simul, theta1=(-0.9, 0.9, 0.05))

    def MA2_simulation(self, n_sample=36, show_acf=False):
        def _simul(theta1=0.8, theta2=-0.6):
            ar = None
            ma = [1, theta1, theta2]
            process = ArmaProcess(ar, ma)
            self._plot(process, ar, ma, n_sample=n_sample, show_acf=show_acf)

        interact(_simul, theta1=(-0.9, 0.9, 0.05), theta2=(-0.9, 0.9, 0.05))

    def AR2MA2_simulation(self, n_sample=36, show_acf=False):
        def _simul(alpha1=0.7, alpha2=-0.4, theta1=0.8, theta2=-0.5):
            ar = [1, -alpha1, -alpha2]
            ma = [1, theta1, theta2]
            process = ArmaProcess(ar, ma)
            self._plot(process, ar, ma, n_sample=n_sample, show_acf=show_acf)

        interact(_simul, alpha1=(-0.9, 0.9, 0.05), alpha2=(-0.9, 0.9, 0.05), theta1=(-0.9, 0.9, 0.05), theta2=(-0.9, 0.9, 0.05))

    def nonstationarity_simulation(self, diff=False, seed=100, n_sample=36, show_acf=False):
        np.random.seed(seed)
        ar = [1, -0.6, -0.45]
        ma = None
        process = ArmaProcess(ar, ma)
        self._plot(process, ar, ma, diff, n_sample=n_sample, show_acf=show_acf)

    def stationarity_simulation(self, diff=False, seed=39, n_sample=36, show_acf=False):
        np.random.seed(seed)
        ar = [1, -0.3]
        ma = None
        process = ArmaProcess(ar, ma)
        self._plot(process, ar, ma, diff, n_sample=n_sample, show_acf=show_acf)        


class BaseIllustrationTimeSeries:
    def __init__(self):
        here = os.path.dirname(__file__)
        self.ets_model = Image(f"{here}/assets/ets_model.png", width=800)
        self.stationarity_quiz = Image(f"{here}/assets/stationarity.png", width=850)
        self.autocorrelation = Image(f"{here}/assets/autocorrelation.png", width=850)
        self.direct_indirect = Image(f"{here}/assets/direct_indirect.png", width=750)
        self.arma = Image(f"{here}/assets/arma.png", width=800)
        self.arima = Image(f"{here}/assets/arima.png", width=850)        
