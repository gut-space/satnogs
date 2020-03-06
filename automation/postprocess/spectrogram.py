import subprocess

from .commons import input_output_parser

def create_spectogram(input_path: str, output_path: str):
    subprocess.check_call(["sox", input_path, "-n", "spectrogram", "-o", output_path])

if __name__ == '__main__':
    input_, output = input_output_parser(
        "Create spectogram",
        "Path to audio file (preferred: WAV)",
        "Path to output spectrogram file"
    )

    create_spectogram(input_, output)
