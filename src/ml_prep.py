"""Waveform preparation for the CNN (Bab 5.1-5.2): cut to a fixed length, z-score, crop.

Pure numpy, so the same code runs inside Spark (mapInPandas) and in the PyTorch training loop.
"""
import numpy as np

FS = 100                     # samples per second
N = 150 * FS                 # every trace is cut to its first 150 s
CROP = 120 * FS              # CNN input: 120 s crop (random while training, centre otherwise)
CONTEXT_FEATURES = ['hour_sin', 'hour_cos', 'dow_sin', 'dow_cos', 'doy_sin', 'doy_cos',
                    'sensor_EH', 'sensor_BH', 'sensor_HH']


def standardize(z):
    """Raw Z trace -> first N samples as z-score float32: (x - mean) / std. None if too short or flat."""
    x = np.asarray(z[:N], dtype=np.float64)
    if len(x) < N or x.std() == 0:
        return None
    return ((x - x.mean()) / x.std()).astype(np.float32)


def crop(x, train, rng=None):
    """N samples -> CROP samples. Train: random start (shift of up to +-15 s); eval: centre (15-135 s)."""
    start = int(rng.integers(0, N - CROP + 1)) if train else (N - CROP) // 2
    return x[start:start + CROP]


if __name__ == '__main__':
    rng = np.random.default_rng(0)
    w = standardize(rng.normal(500, 80, 18001))
    assert w.shape == (N,) and w.dtype == np.float32 and abs(w.mean()) < 1e-4 and abs(w.std() - 1) < 1e-4
    assert standardize(np.zeros(15001)) is None and standardize(np.ones(1000)) is None
    assert crop(w, False).shape == crop(w, True, rng).shape == (CROP,)
    assert np.array_equal(crop(w, False), w[1500:13500])
    print('ok')
