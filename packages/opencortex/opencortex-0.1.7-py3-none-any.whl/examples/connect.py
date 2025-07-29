import re
import winreg
import bluetooth
import argparse
import time
import mne
import matplotlib.pyplot as plt
import matplotlib
from brainflow.board_shim import BoardShim, BrainFlowInputParams, BoardIds, BrainFlowPresets
matplotlib.use("Qt5Agg")


def retrieve_unicorn_devices():
    saved_devices = bluetooth.discover_devices(duration=1, lookup_names=True, lookup_class=True)
    unicorn_devices = filter(lambda x: re.search(r'UN-\d{4}.\d{2}.\d{2}', x[1]), saved_devices)
    return list(unicorn_devices)


def get_com_port_from_bluetooth_address(bluetooth_address):
    key_path = r"SYSTEM\CurrentControlSet\Services\BTHPORT\Parameters\Devices"
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path)
        subkey_name = None

        # Iterate through subkeys to find the one with the matching Bluetooth address
        while True:
            subkey_index = 0
            try:
                subkey_name = winreg.EnumKey(key, subkey_index)
                subkey = winreg.OpenKey(key, subkey_name)
                address = winreg.QueryValueEx(subkey, "DevClass")[0]
                if address.lower() == bluetooth_address.lower():
                    # Found the matching Bluetooth device
                    com_port = winreg.QueryValueEx(subkey, "COM")[0]
                    return com_port
                subkey_index += 1
            except OSError:
                break
    except OSError as e:
        print(f"Error: {e}")
    finally:
        if key:
            winreg.CloseKey(key)

    return None


def main():
    BoardShim.enable_dev_board_logger()
    # use synthetic board for demo
    params = BrainFlowInputParams()

    # Get bluetooth devices that match the UN-XXXX.XX.XX pattern
    print(retrieve_unicorn_devices())
    params.serial_number = retrieve_unicorn_devices()[0][1]

    # Create a board object and prepare the session
    board = BoardShim(BoardIds.UNICORN_BOARD.value, params)
    board.prepare_session()
    board.start_stream()

    # Get data from the board, 10 seconds in this example, then close the session
    time.sleep(10)
    data = board.get_board_data()
    board.stop_stream()
    board.release_session()
    eeg_channels = BoardShim.get_eeg_channels(BoardIds.UNICORN_BOARD.value)
    eeg_data = data[eeg_channels, :]
    eeg_data = eeg_data / 1e6 # BrainFlow returns uV, convert to V for MNE

    # Creating MNE objects from brainflow data arrays
    ch_types = ['eeg'] * len(eeg_channels)
    ch_names = BoardShim.get_eeg_names(BoardIds.UNICORN_BOARD.value)
    sfreq = BoardShim.get_sampling_rate(BoardIds.UNICORN_BOARD.value)
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(eeg_data, info)

    # Plot the data using MNE
    raw.plot()
    raw.compute_psd().plot(average=True)
    plt.show()
    plt.savefig('psd.png')


if __name__ == '__main__':
    main()
