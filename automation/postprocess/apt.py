import subprocess

from .commons import input_output_parser

def decode_apt(input_path: str, output_path: str):
    subprocess.check_call([
        "noaa-apt",
        "-o", output_path,
        input_path
    ])

if __name__ == '__main__':
    input_, output = input_output_parser("Decode APT",
        "Input WAV file", "Output imagery file")
    decode_apt(input_, output)
