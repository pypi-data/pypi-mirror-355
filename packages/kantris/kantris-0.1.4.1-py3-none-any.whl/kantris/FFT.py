import numpy as np
from .DataManipulation import DataManipulation

import logging
logger = logging.getLogger(__name__)



class FFT:
    VERSION = 'Kantris.FFT: 0.1.0'
    def FFT(data: np.ndarray, tol: float = 1e-6) -> np.ndarray:
        """
        Berechnet die FFT einer Signalreihe mit (möglicherweise) nicht gleichmäßigen Abszissen.

        Parameters
        ----------
        data : np.ndarray
            Eingabe-Array der Form (N, 2), wobei Spalte 0 die x-Werte (z.B. Zeitpunkte) und
            Spalte 1 die zugehörigen y-Werte (z.B. Signalamplituden) enthält.
        tol : float, optional
            Toleranz für die Prüfung auf Gleichmäßigkeit der x-Abstände (Default: 1e-6).

        Returns
        -------
        np.ndarray
            Array der Form (M, 2) mit Spalte 0 die Frequenzen und Spalte 1 die zugehörigen
            Amplituden (Betragswerte der Fourier-Koeffizienten). M = N//2 + 1 für reelle Signale.
        """
        x = data[:, 0]
        y = data[:, 1]

        # Prüfen auf gleichmäßige Abstände
        dx = np.diff(x)
        if not np.allclose(dx, dx[0], atol=tol):
            logger.info("Input x-values are not evenly spaced: interpolating to uniform grid")
            N = len(x)
            x_uniform = np.linspace(x.min(), x.max(), N)
            # Verwende die angegebene LinearInterpol-Funktion
            y_uniform = DataManipulation.LinearInterpol(x_uniform, x, y)
            sampling_interval = x_uniform[1] - x_uniform[0]
        else:
            y_uniform = y
            sampling_interval = dx[0]

        # FFT auf reellem Signal
        N = len(y_uniform)
        fft_vals = np.fft.rfft(y_uniform)
        freqs = np.fft.rfftfreq(N, d=sampling_interval)
        amplitudes = np.abs(fft_vals)

        # Ergebnis: Spaltenweise Frequenz und Amplitude
        return np.column_stack((freqs, amplitudes))
