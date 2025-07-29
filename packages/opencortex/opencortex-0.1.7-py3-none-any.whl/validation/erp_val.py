"""
This script plots the average ERP of each channel for Target and Non-Target stimuli.
If you need to change default parameters, you can do it by changing the values of the variables below.

Usage: python erp_val.py --data <path_to_data>

Author: Michele Romani
Email: michele.romani.zaltieri@gmail.com
Copyright 2024 Michele Romani
"""
import argparse
import matplotlib
import matplotlib.pyplot as plt
from brainflow import BoardShim, BrainFlowInputParams, BoardIds
from mne import Epochs, find_events
from utils.loader import convert_to_mne, load_erp_data

matplotlib.use("Qt5Agg")

manual_path = "../data/cortex/validation/Unicorn_2024-12-27_16-05-33_5classes.csv"
#Get filepath from command line
parser = argparse.ArgumentParser(description='ERP Validation')
parser.add_argument('--data', type=str, help='Path to the data file')
filepath = parser.parse_args().data
if not parser.parse_args().data:
    filepath = manual_path

# Parameters
start_train_id = 98
end_train_id = 99
start_app_id = 100
end_app_id = 101
training_length = 60
training_trigger = 1
application_target = 1
board_id = BoardIds.UNICORN_BOARD
delimiter = '\t'
header = 'header'
rescale = 1e6
notch_freqs = (50, 60)
band_freqs = (1, 10)
tmin = -0.1
tmax = 0.7
plot_application = False


def plot_erp(epochs, chs, title='ERP'):
    t_epochs = epochs['T'].average(picks=chs)
    nt_epochs = epochs['NT'].average(picks=chs)

    plt.plot(t_epochs.times, t_epochs.data.T, color='red', label='Target')
    plt.plot(nt_epochs.times, nt_epochs.data.T, color='blue', label='Non-target')
    plt.axvspan(0.25, 0.4, color='red', label="P300", alpha=0.3)
    plt.axvline(0, color='black', linewidth=0.5, linestyle='--', label='Event Onset')
    plt.xlabel('Time (s)')
    plt.ylabel('Amplitude (uV)')
    # remove redundant entries in the legend
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys())
    plt.title(title)
    plt.show()


def filter_extract_epochs(raw_data, stim_channel='STI', training_trigger=1, initial_event=True, shortest_event=1,
                          notch_freqs=(50, 60),
                          band_freqs=(1, 15), tmin=-0.1, tmax=0.7):
    # Apply band-pass filtering
    filtered = raw_data.copy()
    filtered.notch_filter(notch_freqs)
    filtered.filter(band_freqs[0], band_freqs[1])
    events = find_events(filtered, stim_channel=stim_channel, initial_event=initial_event,
                         shortest_event=shortest_event)

    # Remove events bigger than 90
    events = events[events[:, 2] <= 90]

    # Replace non-target event codes with a placeholder code (e.g., 999)
    events[:, 2][events[:, 2] != training_trigger] = 3
    baseline = (tmin, 0.0)
    eps = Epochs(filtered, events, event_id={'T': 1, 'NT': 3},
                 tmin=tmin, tmax=tmax, baseline=baseline)
    return eps





board = BoardShim(board_id, BrainFlowInputParams())
fs = board.get_sampling_rate(board_id)
chs = board.get_eeg_names(board_id)
training_eeg, training_triggers = load_erp_data(filepath, board_id, fs, chs, header, delimiter=delimiter,
                                                start_id=start_train_id, end_id=end_train_id, training=True)
raw_data = convert_to_mne(training_eeg, training_triggers, fs, chs, rescale=rescale, recompute=False, transpose=True)
if board_id == BoardIds.ENOPHONE_BOARD:
    raw_data.set_eeg_reference(ref_channels=['A1', 'A2'])
eps = filter_extract_epochs(raw_data, stim_channel='STI', training_trigger=training_trigger, initial_event=True,
                            shortest_event=1, notch_freqs=notch_freqs, band_freqs=band_freqs, tmin=tmin, tmax=tmax)
plot_erp(eps, chs, title='Training ERP Validation')

if plot_application:
    application_eeg, application_triggers = load_erp_data(filepath, board_id, fs, chs, header, delimiter=delimiter,
                                                          start_id=start_app_id, end_id=end_app_id, training=False)
    raw_data_app = convert_to_mne(application_eeg, application_triggers, fs, chs, rescale=rescale, recompute=False,
                                  transpose=True)
    if board_id == BoardIds.ENOPHONE_BOARD:
        raw_data_app.set_eeg_reference(ref_channels=['A1', 'A2'])
    eps_app = filter_extract_epochs(raw_data_app, stim_channel='STI', training_trigger=application_target,
                                    initial_event=True,
                                    shortest_event=1, notch_freqs=notch_freqs, band_freqs=band_freqs, tmin=tmin,
                                    tmax=tmax)
    plot_erp(eps_app, chs, title='Application ERP Validation')
