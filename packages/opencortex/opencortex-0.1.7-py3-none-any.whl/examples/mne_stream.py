import time

from matplotlib import pyplot as plt

from mne_lsl.datasets import sample
from mne_lsl.lsl import local_clock
from mne_lsl.player import PlayerLSL as Player
from mne_lsl.stream import StreamLSL as Stream

fname = sample.data_path() / "sample-ant-raw.fif"
player = Player(fname)
player.start()
stream = Stream(bufsize=5)  # 5 seconds of buffer
stream.connect(acquisition_delay=0.2)

stream.pick(["Fz", "Cz", "Oz"])

print(f"Number of new samples: {stream.n_new_samples}")
data, ts = stream.get_data()
time.sleep(0.5)
print(f"Number of new samples: {stream.n_new_samples}")

t0 = local_clock()
f, ax = plt.subplots(3, 1, sharex=True, constrained_layout=True)
for _ in range(3):
    # figure how many new samples are available, in seconds
    winsize = stream.n_new_samples / stream.info["sfreq"]
    # retrieve and plot data
    data, ts = stream.get_data(winsize)
    for k, data_channel in enumerate(data):
        ax[k].plot(ts - t0, data_channel)
    time.sleep(0.5)
for k, ch in enumerate(stream.ch_names):
    ax[k].set_title(f"EEG {ch}")
ax[-1].set_xlabel("Timestamp (LSL time)")
plt.show()

stream.disconnect()
player.stop()