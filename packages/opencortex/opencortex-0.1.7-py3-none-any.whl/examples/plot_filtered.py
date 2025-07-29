import matplotlib
import matplotlib.pyplot as plt
from brainflow import BoardIds, BoardShim

import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.layouts import layouts
from utils.loader import load_data, convert_to_mne
matplotlib.use("Qt5Agg")

board_id = BoardIds.UNICORN_BOARD
fs = BoardShim.get_sampling_rate(board_id)
chs = layouts[board_id]["channels"]

if __name__ == "__main__":
    eeg, trigger, _ = load_data("../data/aep/auditory_erp_eyes_open_S1.csv", header=False, fs=fs, skiprows=5)
    print("Loaded data with shape:" + str(eeg.shape) + " and trigger shape: " + str(trigger.shape))
    print("That means we have " + str(eeg.shape[0]) + " samples and " + str(eeg.shape[1]) + " channels.")

    # Convert to MNE format
    raw = convert_to_mne(eeg, trigger, fs=fs, chs=chs)

    # the method filters the signal in-place, so this time I
    # want to preserve the original signal and filter just a
    # temporary copy of it
    filtered = raw.copy()

    # Apply notch filter
    filtered = filtered.copy().notch_filter(freqs=50)  # notch filter at 50 Hz and 60 Hz

    # Apply band-pass filtering
    filtered = filtered.copy().filter(l_freq=1, h_freq=30)  # band-pass filter between 1 and 30 Hz

    # Compute PSD
    # fmax = Nyquist frequency, i.e. half of the sampling frequency
    # fmin = 0, i.e. the lowest frequency
    # This time we filtered the signal to include only frequencies of interest: Theta, Alpha, Beta
    pxx_filt = filtered.compute_psd(fmin=1, fmax=50)
    pxx_filt.plot()
    plt.show()
