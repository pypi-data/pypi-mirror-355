import numpy as np
import pytest

from hipster import Inference


@pytest.mark.parametrize("batch_size", [1, 256])
def test_inference_decoder(batch_size):
    rg = Inference("tests/models/gaia_decoder.onnx", batch_size=batch_size, input_name="l_x_")
    point = np.array([[1, 0, 0]], dtype=np.float32)
    assert rg(point).shape == (1, 1, 344)
