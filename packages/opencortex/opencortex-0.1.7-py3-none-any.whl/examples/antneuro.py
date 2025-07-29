# Read a .eeg file using python MNE library:

import mne
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Qt5Agg')

# Read the .eeg file
raw = mne.io.read_raw_brainvision('../data/evaluation/BrainVision/CA-212_EC_2024-05-24_16-14-41.vhdr', preload=True)

# Print information about the raw data
print(raw.info)

# Plot the raw data
channels = raw.ch_names
raw.plot()
plt.show()

# Plot the power spectral density
raw.compute_psd().plot()
plt.show()


# Filter the data
filtered = raw.copy().notch_filter(freqs=[50, 60])
filtered = filtered.filter(1, 30)
filtered.plot()
plt.show()
