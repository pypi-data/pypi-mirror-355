import sys
import time
import serial
import struct
import mne
from brainflow import BoardShim, BrainFlowInputParams, BoardIds
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from mne.io import RawArray
from mne.viz import plot_raw
from matplotlib import pyplot as plt
from serial.tools import list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QListWidget, QLabel, QTextEdit, QMainWindow
from PyQt5.QtCore import QTimer, QThread, pyqtSignal
import numpy as np
from connect import retrieve_unicorn_devices


class DataAcquisitionThread(QThread):
    data_received = pyqtSignal(np.ndarray)
    stop_thread = pyqtSignal()

    def __init__(self, callback_func, board, parent=None):
        super(DataAcquisitionThread, self).__init__(parent)
        self.callback_func = callback_func
        self.board = board

    def run(self):
        while not self.isInterruptionRequested():
            data = self.board.get_board_data()
            self.data_received.emit(data)
            self.callback_func(data)
            self.msleep(1000)


class RealTimePlotWidget(FigureCanvasQTAgg):
    def __init__(self, parent=None):
        self.fig, self.ax = plt.subplots()
        super(RealTimePlotWidget, self).__init__(self.fig)
        self.data_buffer = []

    def update_plot(self, data):
        self.data_buffer.append(data[0])
        if len(self.data_buffer) > 250:
            self.data_buffer.pop(0)  # Keep a limited number of data points for better performance
        self.ax.clear()
        self.ax.plot(self.data_buffer, color='b', marker='o')
        self.draw()


class BiosignalStreamer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.serial_device = None
        self.board = None
        self.data_thread = None
        self.connected_device = None
        self.setWindowTitle("Unicorn EEG Data Acquisition")
        self.setGeometry(100, 100, 1200, 800)

        self.battery_level = 0

        self.battery_label = QLabel("Battery Level: " + str(self.battery_level) + "%", self)
        self.device_list_widget = QListWidget(self)
        self.connect_button = QPushButton("Connect", self)
        self.disconnect_button = QPushButton("Disconnect", self)
        self.refresh_button = QPushButton("Refresh Devices", self)
        self.acq_button = QPushButton("Start Acquisition", self)
        self.status_label = QLabel("Status: Not connected", self)
        self.log_box = QTextEdit(self)
        self.log_box.setReadOnly(True)

        layout = QVBoxLayout(self)
        layout.addWidget(self.battery_label)
        layout.addWidget(self.device_list_widget)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.acq_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.log_box)

        menu_widget = QWidget()
        menu_widget.setLayout(layout)
        self.setMenuWidget(menu_widget)

        self.connect_button.clicked.connect(self.connect_to_device)
        self.disconnect_button.clicked.connect(self.disconnect_from_device)
        self.refresh_button.clicked.connect(self.refresh_devices)
        self.acq_button.clicked.connect(self.start_acquisition)


    def list_devices(self):
        nearby_devices = retrieve_unicorn_devices()
        print(nearby_devices)
        self.device_list_widget.clear()
        if not nearby_devices:
            self.device_list_widget.addItem("No Bluetooth devices found.")
        else:
            for addr, name, port in nearby_devices:
                self.device_list_widget.addItem(name)

    def refresh_devices(self):
        self.list_devices()
        self.log("Refreshed Bluetooth devices.")

    def connect_to_device(self):
        selected_item = self.device_list_widget.currentItem()
        if selected_item:
            serial_number = selected_item.text()
            self.status_label.setText(f"Status: Connecting to {serial_number}")
            self.log(f"Connecting to ({serial_number})")
            try:
                BoardShim.enable_dev_board_logger()
                params = BrainFlowInputParams()
                params.serial_number = serial_number
                self.board = BoardShim(BoardIds.UNICORN_BOARD.value, params)
                self.board.prepare_session()
                self.status_label.setText(f"Status: Connected to {serial_number}")
                # Start receiving data (replace this with your actual data reception logic)
                self.log(f"Connected to ({serial_number})")

            except ConnectionError as e:
                self.status_label.setText(f"Status: Failed to connect to {serial_number}")
                self.log(f"Failed to connect to {serial_number}")
                self.log(f"Error: {e}")
        else:
            self.status_label.setText("Status: No device selected")

    def disconnect_from_device(self):
        self.status_label.setText("Status: Not connected")
        self.stop_data_thread()
        self.board.stop_stream()
        self.board.release_session()
        self.connected_device = None
        self.log_clear("Disconnected from Bluetooth device.")

    def start_acquisition(self):
        self.board.start_stream()
        time.sleep(1)
        self.log('Started acquisition')
        self.data_thread = DataAcquisitionThread(self.receive_sample, board=self.board)
        self.data_thread.setStackSize(1024 * 1024 * 4)  # 4MB stack size
        self.data_thread.stop_thread.connect(self.data_thread.requestInterruption)
        self.data_thread.start()

    def receive_sample(self, data):
        eeg_channels = BoardShim.get_eeg_channels(BoardIds.UNICORN_BOARD.value)
        eeg_data = data[eeg_channels, :]
        eeg_data = eeg_data / 1e6  # BrainFlow returns uV, convert to V for MNE

        # send the data to LSL
        # outlet.push_sample(dat)
        # self.battery_level = battery
        # self.battery_label.repaint()
        self.log(eeg_data)

    def update_plot(self, new_data):

        self.eeg_data = np.roll(self.eeg_data, -1, axis=1)
        self.eeg_data[:, -1] = new_data

        # Clear the previous plot and update with new data
        self.ax.clear()
        self.ax.plot(self.eeg_data.T)
        self.ax.set_title("EEG Data Visualization")
        self.ax.set_xlabel("Time")
        self.ax.set_ylabel("Amplitude")
        self.canvas.draw()

    def stop_data_thread(self):
        self.data_thread.stop_thread.emit()

    def log(self, message):
        self.log_box.append(f"> {message}")

    def log_clear(self, message):
        self.log_box.setText(f"> {message}")  # Clear the log box and add the message


if __name__ == "__main__":
    app = QApplication(sys.argv)
    bluetooth_app = BiosignalStreamer()
    bluetooth_app.list_devices()
    bluetooth_app.show()
    sys.exit(app.exec())
