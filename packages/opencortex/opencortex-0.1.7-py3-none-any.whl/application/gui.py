import numpy as np
from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

from utils.layouts import layouts

# 16 Color ascii codes for the 16 EEG channels
colors = ["blue", "green", "yellow", "purple", "orange", "pink", "brown", "gray",
          "cyan", "magenta", "lime", "teal", "lavender", "turquoise", "maroon", "olive"]


class GUI:
    def __init__(self, streamer):
        self.streamer = streamer
        self.app = QtWidgets.QApplication([])
        self.win = pg.GraphicsLayoutWidget(title='Cortex Streamer', size=(1200, 800))
        self.win.setWindowTitle('Cortex Streamer')
        self.win.show()
        self.main_layout = QtWidgets.QGridLayout()
        self.plot = self.init_plot()
        self.panel = self.create_buttons()
        self.main_layout.addWidget(self.plot, 0, 0)
        self.main_layout.addWidget(self.panel, 1, 0)
        self.win.setLayout(self.main_layout)
        self.app.exec_()

    def create_buttons(self):
        """Create buttons to interact with the neuroengine"""
        self.input_box = QtWidgets.QLineEdit()
        self.input_box.setFixedWidth(100)
        self.input_box.setPlaceholderText('Trigger value')
        self.input_box.setText('1')

        self.trigger_button = QtWidgets.QPushButton('Send Trigger')
        self.trigger_button.setFixedWidth(100)
        self.trigger_button.clicked.connect(lambda: self.streamer.write_trigger(int(self.input_box.text())))

        self.start_button = QtWidgets.QPushButton('Stop')
        self.start_button.setFixedWidth(100)
        self.start_button.clicked.connect(lambda: self.streamer.toggle_stream())

        self.roc_button = QtWidgets.QPushButton('Plot ROC')
        self.roc_button.setFixedWidth(100)
        self.roc_button.clicked.connect(lambda: self.streamer.classifier.plot_roc_curve())

        self.confusion_button = QtWidgets.QPushButton('Plot CM')
        self.confusion_button.setFixedWidth(100)
        self.confusion_button.clicked.connect(lambda: self.streamer.classifier.plot_confusion_matrix())

        self.save_data_checkbox = QtWidgets.QCheckBox('Save data to file')
        self.save_data_checkbox.setStyleSheet('color: white')
        self.save_data_checkbox.setChecked(self.streamer.save_data)

        self.bandpass_checkbox = QtWidgets.QCheckBox('Bandpass filter frequencies (Hz)')
        self.bandpass_checkbox.setStyleSheet('color: white')
        self.bandpass_box_low = QtWidgets.QLineEdit()
        self.bandpass_box_low.setPlaceholderText('0')
        self.bandpass_box_low.setText('1')
        self.bandpass_box_low.setMaximumWidth(30)
        self.bandpass_box_high = QtWidgets.QLineEdit()
        self.bandpass_box_high.setPlaceholderText('0')
        self.bandpass_box_high.setText('40')
        self.bandpass_box_high.setMaximumWidth(30)

        self.notch_checkbox = QtWidgets.QCheckBox('Notch filter frequencies (Hz)')
        self.notch_checkbox.setStyleSheet('color: white')
        self.notch_box = QtWidgets.QLineEdit()
        self.notch_box.setMaximumWidth(60)
        self.notch_box.setPlaceholderText('0, 0')
        self.notch_box.setText('50, 60')

        self.lsl_chunk_checkbox = QtWidgets.QCheckBox('Chunk data')
        self.lsl_chunk_checkbox.setStyleSheet('color: white')
        self.lsl_chunk_checkbox.setChecked(True)

        start_save_layout = QtWidgets.QHBoxLayout()
        start_save_layout.addWidget(self.save_data_checkbox)
        start_save_layout.addWidget(self.start_button)

        bandpass_layout = QtWidgets.QHBoxLayout()
        bandpass_layout.addWidget(self.bandpass_checkbox)
        bandpass_layout.addWidget(self.bandpass_box_low)
        bandpass_layout.addWidget(self.bandpass_box_high)

        notch_layout = QtWidgets.QHBoxLayout()
        notch_layout.addWidget(self.notch_checkbox)
        notch_layout.addWidget(self.notch_box)

        lsl_layout_label = QtWidgets.QLabel("LSL Options")
        lsl_layout_label.setStyleSheet("color: white; font-size: 20px;")
        lsl_layout = QtWidgets.QVBoxLayout()
        lsl_layout.addWidget(lsl_layout_label)
        lsl_layout.addWidget(self.lsl_chunk_checkbox)

        left_side_label = QtWidgets.QLabel("Filters")
        left_side_label.setStyleSheet("color: white; font-size: 20px;")
        left_side_layout = QtWidgets.QVBoxLayout()
        left_side_layout.addWidget(left_side_label)
        left_side_layout.addLayout(bandpass_layout)
        left_side_layout.addLayout(notch_layout)
        left_side_layout.addLayout(start_save_layout)

        center_label = QtWidgets.QLabel("Markers")
        center_label.setStyleSheet("color: white; size: 20px;")
        center_layout = QtWidgets.QVBoxLayout()
        center_layout.addWidget(center_label)
        center_layout.addWidget(self.input_box)
        center_layout.addWidget(self.trigger_button)

        right_side_label = QtWidgets.QLabel("Classifier")
        right_side_label.setStyleSheet("color: white; font-size: 20px;")
        right_side_layout = QtWidgets.QVBoxLayout()
        right_side_layout.addWidget(right_side_label)
        right_side_layout.addWidget(self.roc_button)
        right_side_layout.addWidget(self.confusion_button)

        horizontal_container = QtWidgets.QHBoxLayout()
        horizontal_container.addLayout(lsl_layout)
        horizontal_container.addLayout(left_side_layout)
        horizontal_container.addLayout(center_layout)
        horizontal_container.addLayout(right_side_layout)

        button_widget = QtWidgets.QWidget()
        button_widget.setLayout(horizontal_container)

        return button_widget

    def init_plot(self):
        """Initialize the timeseries plot for the EEG channels and trigger channel."""
        self.eeg_plot = pg.PlotWidget()
        self.eeg_plot.showAxis('left', False)
        self.eeg_plot.setMenuEnabled('left', True)
        self.eeg_plot.showAxis('bottom', True)
        self.eeg_plot.setMenuEnabled('bottom', True)
        self.eeg_plot.setLabel('bottom', text='Time (s)')
        self.eeg_plot.getAxis('bottom').setTicks([[(i, str(i / self.streamer.sampling_rate)) for i in
                                                   range(0, self.streamer.num_points,
                                                         int(self.streamer.sampling_rate / 2))] + [(
            self.streamer.num_points,
            str(self.streamer.num_points / self.streamer.sampling_rate))]])
        self.eeg_plot.setTitle('EEG Channels with Trigger')

        self.offset_amplitude = 200
        self.trigger_offset = -self.offset_amplitude

        self.curves = []
        self.quality_indicators = []

        for i, channel in enumerate(self.streamer.eeg_channels):
            curve = self.eeg_plot.plot(pen=colors[i])
            self.curves.append(curve)

            scatter = pg.ScatterPlotItem(size=20, brush=pg.mkBrush('green'))
            scatter.setPos(-1, i * self.offset_amplitude)
            self.eeg_plot.addItem(scatter)
            self.quality_indicators.append(scatter)

            text_item = pg.TextItem(text=layouts[self.streamer.board_id]["channels"][i], anchor=(1, 0.5))
            text_item.setPos(-10, i * self.offset_amplitude)
            self.eeg_plot.addItem(text_item)

        trigger_curve = self.eeg_plot.plot(pen='red')
        self.curves.append(trigger_curve)

        trigger_label = pg.TextItem(text="Trigger", anchor=(1, 0.5))
        trigger_label.setPos(-10, self.trigger_offset)
        self.eeg_plot.addItem(trigger_label)
        return self.eeg_plot

    def update_plot(self):
        """Update the plot with new data."""
        filtered_eeg = np.zeros((len(self.streamer.eeg_channels) + 1, self.streamer.num_points))
        if self.streamer.is_streaming:
            if self.streamer.window_size == 0:
                raise ValueError("Window size cannot be zero")
            data = self.streamer.board.get_current_board_data(num_samples=self.streamer.num_points)
            self.streamer.filter_data_buffer(data)
            start_eeg = layouts[self.streamer.board_id]["eeg_start"]
            end_eeg = layouts[self.streamer.board_id]["eeg_end"]
            eeg = data[start_eeg:end_eeg]

            for count, channel in enumerate(self.streamer.eeg_channels):
                ch_data = eeg[count]
                filtered_eeg[count] = ch_data

                if self.streamer.plot:
                    ch_data_offset = ch_data + count * self.offset_amplitude
                    self.curves[count].setData(ch_data_offset)

            trigger = data[-1] * 100
            if self.streamer.plot:
                trigger_rescaled = (trigger * (self.offset_amplitude / 5.0) + self.trigger_offset)
                self.curves[-1].setData(trigger_rescaled.tolist())

            min_display = self.trigger_offset - self.offset_amplitude
            max_display = (len(self.streamer.eeg_channels) - 1) * self.offset_amplitude + np.max(eeg)
            self.eeg_plot.setYRange(min_display, max_display)

            self.streamer.update_quality_indicators(filtered_eeg, push=True)
            self.app.processEvents()
