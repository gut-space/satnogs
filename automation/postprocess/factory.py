import os.path

from apt import decode_apt
from spectrogram import create_spectogram

def create_output_path(input_path: str, method: str, extension: str) -> str:
    directory, base = os.path.split(input_path)
    filename, _ = os.path.splitext(base)
    output_filename = filename + "_" + method + extension
    return os.path.join(directory, output_filename)

def get_postprocess_result(sat_name: str, input_path: str) -> str:
    get_output_path = lambda method, ext: create_output_path(input_path, method, ext)
    if sat_name.startswith("NOAA"):
        output_path = get_output_path("apt", ".png")
        decode_apt(input_path, output_path)
    else:
        output_path = get_output_path("spectrogram", ".png")
        create_spectogram(input_path, output_path)
    return output_path
