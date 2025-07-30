import pytest

from hipster import HiPSGenerator, ImagePlotter, Inference, Range, SpectrumPlotter


@pytest.mark.parametrize("hierarchy", [1, 2])
def test_hips_generator_image(tmp_path, hierarchy):
    HiPSGenerator(
        decoder=Inference("tests/models/illustris_decoder.onnx"),
        image_maker=ImagePlotter(),
        hips_path=tmp_path,
        max_order=0,
        hierarchy=hierarchy,
    ).execute()


@pytest.mark.parametrize("hierarchy", [1, 2])
def test_hips_generator_spectra(tmp_path, hierarchy):
    HiPSGenerator(
        decoder=Inference("tests/models/gaia_decoder.onnx", input_name="l_x_"),
        image_maker=SpectrumPlotter(
            Range(336, 1023, 2),
            ylim=(0, 1),
            figsize_in_pixel=64,
        ),
        hips_path=tmp_path,
        max_order=0,
        hierarchy=hierarchy,
    ).execute()
