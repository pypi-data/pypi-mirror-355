import math
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from utils.loader import load_data


# Define how to destructure the scores csv file
# [1:numberofchannels] - scores
# [numberofchannels+1 : 2*numberofchannels] - zscores
# [2*numberofchannels +1 : 3*numberofchannels] - pvalues
# [3*numberofchannel + 1] - normalized propability
# [3*numberofchannel + 2] - time hold ms
# [3*numberofchannel + 3] - class selection
# list of 30 colors
colors = [
    '#ff7f0e', '#1f77b4', '#2ca02c', '#d62728', '#c5b0d5',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#9467bd',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#17becf',
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#c5b0d5',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#9467bd',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#17becf'
]


def plot_scores(path, N_classes=5, score='zscore', xlim=0, skiprows=5, fs=250, header=None):
    scores = pd.read_csv(path, header=header, skiprows=skiprows)
    if score == 'default':
        scores = scores.iloc[:, 0:N_classes - 1]
    if score == 'zscore':
        scores = scores.iloc[:, N_classes: 2 * N_classes]
        z_threshold80 = 0.674489
        z_threshold85 = 1.036433
        z_threshold90 = 1.281552
        z_threshold95 = 1.644854
        z_threshold99 = 2.326348

        plt.plot(scores.index, np.ones(len(scores.index)) * z_threshold80, color='blue', label="Confidence 80",
                 linestyle='--')
        plt.plot(scores.index, np.ones(len(scores.index)) * z_threshold85, color='green', label="Confidence 85",
                 linestyle='--')
        plt.plot(scores.index, np.ones(len(scores.index)) * z_threshold90, color='black', label="Confidence 90",
                 linestyle='--')
        # plt.plot(scores.index, np.ones(len(scores.index)) * z_threshold95, color='black', label="Confidence 95", linestyle='--')
        # plt.plot(scores.index, np.ones(len(scores.index)) * z_threshold99, color='red', label="Confidence 99", linestyle='--')
        plt.yticks([-2, -1, 0, 1, z_threshold90, 2, 3], [-2, -1, 0, 1, f'{z_threshold90}', 2, 3])

        # plt.yticks([-2, -1, 0, 1, z_threshold85, z_threshold90, z_threshold95, z_threshold99, 2, 3], [-2, -1, 0, 1, f'{z_threshold85}',f'{z_threshold90}', f'{z_threshold95}', f'{z_threshold99}', 2, 3])

    if score == 'pvalue':
        scores = scores.iloc[:, 2 * N_classes: 3 * N_classes]
    if score == 'normalized':
        scores = scores.iloc[:, 3 * N_classes: 3 * N_classes + 1]
    if score == 'time':
        scores = scores.iloc[:, 3 * N_classes + 1: 3 * N_classes + 2]
    if score == 'class':
        scores = scores.iloc[:, 3 * N_classes + 2: 3 * N_classes + 3]

    for i, col in enumerate(scores.columns):
        plt.plot(scores.index, scores[col], color=colors[i], label="Class " + str(i + 1))

    # plot a highlight square starting at point 100 until point 200 for the selected class
    # plt.axvspan(715, 730, facecolor='red', alpha=0.5, label="Misclassified")

    # Compute the xticks
    limit = math.ceil(scores.index[-1] / 1000) * 1000
    print(limit)
    xticks = np.arange(xlim / N_classes, limit / N_classes, limit / N_classes / 8)
    indexes = np.arange(xlim, limit, limit / 8)
    print(indexes, xticks)

    plt.xlim(xlim)
    plt.ylim(-2, 2)
    plt.legend(loc='lower right')
    plt.xlabel("Time(s)", fontsize=18)
    plt.xticks(indexes, xticks)
    # plt.title(score.upper() + " probability scores with " + str(N_classes) + " classes for subject " + path.split('/')[-3])
    plt.ylabel(score, fontsize=18)
    plt.tight_layout()
    plt.show()


def plot_trigger(path, fs, xlim=None, skiprows=5, header=True):
    eeg, trigger, dataframe = load_data(path, header=header, fs=fs, skiprows=skiprows)
    plt.plot(dataframe.id, color='blue')
    plt.plot(dataframe.islast, color='red')
    if xlim:
        plt.xlim(xlim[0], xlim[1])
    plt.show()


## Run from command line
if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Plot scores from a file')
    parser.add_argument('path', type=str, help='Path to the file')
    parser.add_argument('--xlim', type=int, default=0, help='Limit the x-axis')
    args = parser.parse_args()
    plot_scores(args.path, args.xlim)
