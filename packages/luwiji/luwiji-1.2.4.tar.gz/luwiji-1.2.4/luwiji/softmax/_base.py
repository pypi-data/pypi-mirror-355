import warnings
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ipywidgets import interact


class BaseDemoSoftmax:
    def __init__(self):
        pass

    @staticmethod
    def softmax_temperature():
        def _simul(temp=1):
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                
                fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
                sns.barplot(x=vocab, y=proba, ax=ax1, palette="bright", width=0.6)
                ax1.set(title="Softmax", ylim=(0, 1))
                
                sns.barplot(x=vocab, y=proba_t[round(temp, 1)], ax=ax2, palette="bright", width=0.6)
                ax2.set(title=f"Softmax (with Temp = {temp:.1f})", ylim=(0, 1))

        logits = np.log([0.1, 0.2, 0.55, 0.15])
        vocab = ["vocab_1", "vocab_2", "vocab_3", "vocab_4"]
        proba = softmax(logits)
    
        proba_t = {round(temp, 1): softmax(logits, temp) for temp in np.arange(0.1, 3.1, 0.1)}
        interact(_simul, temp=(0.1, 3, 0.1))


def softmax(logits, temp=1):
    e_x = np.exp(logits / temp)
    return e_x / e_x.sum()