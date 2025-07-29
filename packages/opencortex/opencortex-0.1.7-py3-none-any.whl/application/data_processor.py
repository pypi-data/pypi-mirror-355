import numpy as np
from brainflow import DataFilter, FilterTypes, DetrendOperations
import pyqtgraph as pg
from PyQt5 import QtCore


class DataProcessor:
    def __init__(self, streamer):
        self.streamer = streamer


    def update_data_buffer(self):
        data = self.streamer.board.get_current_board_data(num_samples=self.streamer.num_points)
        self.filter_data_buffer(data)
        self.streamer.filtered_eeg = data

    def filter_data_buffer(self, data):
        start_eeg = self.streamer.layouts[self.streamer.board_id]["eeg_start"]
        end_eeg = self.streamer.layouts[self.streamer.board_id]["eeg_end"]
        eeg = data[start_eeg:end_eeg]
        for count, channel in enumerate(self.streamer.eeg_channels):
            ch_data = eeg[count]
            if self.streamer.gui.bandpass_checkbox.isChecked():
                start_freq = float(
                    self.streamer.gui.bandpass_box_low.text()) if self.streamer.gui.bandpass_box_low.text() != '' else 0
                stop_freq = float(
                    self.streamer.gui.bandpass_box_high.text()) if self.streamer.gui.bandpass_box_high.text() != '' else 0
                self.apply_bandpass_filter(ch_data, start_freq, stop_freq)
            if self.streamer.gui.notch_checkbox.isChecked():
                freqs = np.array(self.streamer.gui.notch_box.text().split(','))
                self.apply_notch_filter(ch_data, freqs)

    def apply_bandpass_filter(self, ch_data, start_freq, stop_freq, order=4,
                              filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE, ripple=0):
        DataFilter.detrend(ch_data, DetrendOperations.CONSTANT.value)
        if start_freq >= stop_freq:
            raise ValueError("Start frequency should be less than stop frequency")
        if start_freq < 0 or stop_freq < 0:
            raise ValueError("Frequency values should be positive")
        if start_freq > self.streamer.sampling_rate / 2 or stop_freq > self.streamer.sampling_rate / 2:
            raise ValueError(
                "Frequency values should be less than half of the sampling rate in respect of Nyquist theorem")
        DataFilter.perform_bandpass(ch_data, self.streamer.sampling_rate, start_freq, stop_freq, order, filter_type,
                                    ripple)

    def apply_notch_filter(self, ch_data, freqs, bandwidth=2.0, order=4, filter_type=FilterTypes.BUTTERWORTH_ZERO_PHASE,
                           ripple=0):
        for freq in freqs:
            if float(freq) < 0:
                raise ValueError("Frequency values should be positive")
            if float(freq) > self.streamer.sampling_rate / 2:
                raise ValueError(
                    "Frequency values should be less than half of the sampling rate in respect of Nyquist theorem")
        for freq in freqs:
            start_freq = float(freq) - bandwidth
            end_freq = float(freq) + bandwidth
            DataFilter.perform_bandstop(ch_data, self.streamer.sampling_rate, start_freq, end_freq, order, filter_type,
                                        ripple)

    def update_quality_indicators(self, sample, push=False):
        start_eeg = self.streamer.layouts[self.streamer.board_id]["eeg_start"]
        end_eeg = self.streamer.layouts[self.streamer.board_id]["eeg_end"]
        eeg = sample[start_eeg:end_eeg]
        amplitudes = []
        q_colors = []
        q_scores = []
        for i in range(len(eeg)):
            amplitude_data = eeg[i]
            color, amplitude, q_score = self.get_channel_quality(amplitude_data)
            q_colors.append(color)
            amplitudes.append(np.round(amplitude, 2))
            q_scores.append(q_score)
            self.streamer.gui.quality_indicators[i].setBrush(pg.mkBrush(color))
            self.streamer.gui.quality_indicators[i].setData([-1], [0])
        if push:
            self.push_lsl_quality(self.streamer.quality_outlet, q_scores)

    def get_channel_quality(self, eeg, threshold=75):
        amplitude = np.percentile(eeg, threshold)
        q_score = 0
        color = 'red'
        for low, high, color_name, score in self.streamer.quality_thresholds:
            if low <= amplitude <= high:
                color = color_name
                q_score = score
                break
        return color, amplitude, q_score

    def push_lsl_quality(self, outlet, q_scores):
        outlet.push_sample(q_scores)
