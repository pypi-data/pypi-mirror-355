from hipster import ImageGenerator, Inference


def test_hips_generator(tmp_path):
    image_generator = ImageGenerator(
        encoder=Inference("tests/models/gaia_encoder.onnx"),
        decoder=Inference("tests/models/gaia_decoder.onnx"),
        data_directory="tests/data",
        output_folder=tmp_path,
    )

    image_generator()
