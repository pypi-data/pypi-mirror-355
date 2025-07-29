"""
This script receive power bands data from LSL stream and plot the power bands distribution in real-time.

Author: Michele Romani
Email: michele.romani.zaltieri@gmail.com
Copyright 2024 Michele Romani
"""

import numpy as np
import matplotlib
from brainflow import BoardIds, BoardShim
from mne import set_eeg_reference
from pylsl import StreamInlet, resolve_stream

from utils.loader import convert_to_mne

matplotlib.use("Qt5Agg")

freq_bands = {
    'delta': (1, 4),
    'theta': (4, 8),
    'alpha': (8, 12),
    'beta': (12, 30),
    'gamma': (30, 50)
}

# Get the stream
print("Looking for an EEG stream...")
streams = resolve_stream('name', 'CortexEEG')
inlet = StreamInlet(streams[0])

# Get data in a separate thread
print("Start receiving data...")
# Power band labels (assume 5 bands: delta, theta, alpha, beta, gamma)
power_bands = ['Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']
num_bands = len(power_bands)

# Init 4 plots, one for each index
indexes = ['Alpha Asymmetry', 'Theta Asymmetry', 'Theta/Beta Ratio', 'Global Gamma Power']


board_id = BoardIds.ENOPHONE_BOARD
chs = BoardShim.get_eeg_names(board_id)
fs = BoardShim.get_sampling_rate(board_id)

time_window = 5
sample = []
# get the data
while True:
    data, timestamp = inlet.pull_sample()
    sample.append(data)
    if len(sample) == fs * time_window:
        sample = np.array(sample)
        eeg_data = sample[:, :-1]
        trigger = sample[:, -1]
        raw = convert_to_mne(eeg_data, trigger, fs, chs, rescale=1e6,recompute=False)
        raw, _ = set_eeg_reference(raw, ref_channels=['A1', 'A2'])
        selected_chs = ['C3', 'C4']
        raw = raw.pick_channels(selected_chs, ordered=True)
        theta_power = raw.copy().compute_psd(fmin=freq_bands['theta'][0], fmax=freq_bands['theta'][1], n_fft=fs).get_data()
        alpha_power = raw.copy().compute_psd(fmin=freq_bands['alpha'][0], fmax=freq_bands['alpha'][1], n_fft=fs).get_data()
        beta_power = raw.copy().compute_psd(fmin=freq_bands['beta'][0], fmax=freq_bands['beta'][1], n_fft=fs).get_data()
        gamma_power = raw.copy().compute_psd(fmin=freq_bands['gamma'][0], fmax=freq_bands['gamma'][1], n_fft=fs).get_data()

        # Index of alpha asymmetry (C3 - C4)
        alpha_asymmetry = np.mean(alpha_power[0] - alpha_power[1])
        # Index of theta asymmetry (C3 - C4)
        theta_asymmetry = np.mean(theta_power[0] - theta_power[1])
        # Index of theta/beta ratio averaged over C3 and C4
        theta_beta_ratio = np.mean(theta_power) / np.mean(beta_power)
        # Index of global gamma power
        gamma_power = np.mean(gamma_power)

        print(f'Index of alpha asymmetry: {alpha_asymmetry}' )
        print(f'Index of theta asymmetry: {theta_asymmetry}' )
        print(f'Index of theta/beta ratio: {theta_beta_ratio}' )
        print(f'Index of global gamma power: {gamma_power}' )


        sample = []





