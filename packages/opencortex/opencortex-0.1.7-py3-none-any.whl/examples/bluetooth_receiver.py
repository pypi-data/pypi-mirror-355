import re

import bluetooth

start_acq = [0x61, 0x7C, 0x87]
stop_acq = [0x63, 0x5C, 0xC5]
start_response = [0x00, 0x00, 0x00]
stop_response = [0x00, 0x00, 0x00]
start_sequence = [0xC0, 0x00]
stop_sequence = [0x0D, 0x0A]

blocksize = 0.2
timeout = 5
nchan = 16
fsample = 250


def send_message(socket, message):
    try:
        socket.send(bytes(message))
        print(f"Sent message: {message}")
    except bluetooth.BluetoothError as e:
        print(f"Error sending message: {e}")


def receive_response(socket, buffer=3):
    try:
        response = socket.recv(buffer)  # Adjust the buffer size as needed
        print(f"Received response: {response}")
    except bluetooth.BluetoothError as e:
        print(f"Error receiving response: {e}")


def retrieve_unicorn_devices():
    saved_devices = bluetooth.discover_devices(duration=1, lookup_names=True, lookup_class=True)
    devices = filter(lambda x: re.search(r'UN-\d{4}.\d{2}.\d{2}', x[1]), saved_devices)
    return list(devices)


unicorn_devices = retrieve_unicorn_devices()
target_address = unicorn_devices[0][0]
port = 1  # RFCOMM port, usually 1 for most devices

sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)

try:
    sock.connect((target_address, port))
    print(f"Connected to {target_address}")

    # Example: sending start_acq message
    send_message(sock, start_acq)

    # Example: sending stop_acq message
    send_message(sock, stop_acq)

    # Receive and process responses
    for _ in range(5):  # Adjust the number of iterations as needed
        receive_response(sock)

finally:
    sock.close()
    print("Connection closed")