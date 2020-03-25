import argparse
import os.path
from typing import Tuple

def exist_file(x: str) -> str:
    """
    'Type' for argparse - checks that file exists but does not open.
    """
    if not os.path.exists(x):
        # Argparse uses the ArgumentTypeError to give a rejection message like:
        # error: argument input: x does not exist
        raise argparse.ArgumentTypeError("{0} does not exist".format(x))
    if not os.path.isfile(x):
        raise argparse.ArgumentTypeError("%s isn't a file" % (x,))
    return x

def input_output_parser(program: str, input_description: str, output_description: str) -> Tuple[str, str]:
    parser = argparse.ArgumentParser(program)
    parser.add_argument("input", type=exist_file, help=input_description)
    parser.add_argument("-o", "--output", type=str, default="output.png", help="Path to output file")
    args = parser.parse_args()
    return args.input, args.output