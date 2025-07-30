import numpy as np
import pytest

from hipster import AbsorptionLinePlotter, Range, SpectrumPlotter


@pytest.mark.parametrize("plotter", ["spectrum", "absorption_line"])
def test_spectrum_plotter(plotter):
    wavelengths = Range(200, 1000, 1000)
    spectrum = (5 + np.sin(wavelengths.to_numpy() * 0.1) ** 2) * np.exp(-0.00002 * (wavelengths.to_numpy() - 600) ** 2)

    if plotter == "spectrum":
        spectrum_plotter = SpectrumPlotter(wavelengths)
    elif plotter == "absorption_line":
        spectrum_plotter = AbsorptionLinePlotter(wavelengths)
    else:
        raise ValueError(f"Unknown plotter: {plotter}")

    spectrum = spectrum_plotter(spectrum)

    assert spectrum.shape == (800, 800, 3)
